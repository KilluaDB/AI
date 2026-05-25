import os
import pdb
import sys
import json
import numpy as np
import argparse
import multiprocessing as mp
from func_timeout import func_timeout, FunctionTimedOut
import time
import math
from db_utils import get_pg_connection, normalize_pg_sql


def result_callback(result):
    exec_result.append(result)


def clean_abnormal(input):
    input = np.asarray(input)
    processed_list = []
    mean = np.mean(input, axis=0)
    std = np.std(input, axis=0)
    for x in input:
        if x < mean + 3 * std and x > mean - 3 * std:
            processed_list.append(x)
    return processed_list


def execute_sql(sql, db_place):
    conn = get_pg_connection(schema=db_place)
    cursor = conn.cursor()
    start_time = time.time()
    cursor.execute(normalize_pg_sql(sql))
    exec_time = time.time() - start_time
    cursor.close()
    conn.close()
    return exec_time


def is_numeric_match(pred_rows, gold_rows, tolerance=1e-6):
    if len(pred_rows) != len(gold_rows):
        return False
    if not pred_rows:
        return False
    if len(pred_rows[0]) != len(gold_rows[0]):
        return False
    try:
        pred_sorted = sorted(pred_rows, key=lambda r: [str(v) for v in r])
        gold_sorted = sorted(gold_rows, key=lambda r: [str(v) for v in r])
        for pred_row, gold_row in zip(pred_sorted, gold_sorted):
            for pred_val, gold_val in zip(pred_row, gold_row):
                try:
                    p, g = float(pred_val), float(gold_val)
                    if g == 0:
                        if abs(p) >= tolerance:
                            return False
                    else:
                        if abs(p - g) / abs(g) >= tolerance:
                            return False
                except (TypeError, ValueError):
                    if pred_val != gold_val:
                        return False
        return True
    except Exception:
        return False


def find_matching_column_indices(pred_rows, gold_rows):
    """
    For each gold column, find a pred column whose values match exactly.
    Works regardless of column count difference.
    Returns mapping {gold_idx: pred_idx} or None if no full mapping found.
    """
    if not pred_rows or not gold_rows:
        return None
    if len(pred_rows) != len(gold_rows):
        return None

    n_pred_cols = len(pred_rows[0])
    n_gold_cols = len(gold_rows[0])

    pred_sorted = sorted(pred_rows, key=lambda r: [str(v) for v in r])
    gold_sorted = sorted(gold_rows, key=lambda r: [str(v) for v in r])

    def cols_match_exactly(p_idx, g_idx):
        for pred_row, gold_row in zip(pred_sorted, gold_sorted):
            if pred_row[p_idx] != gold_row[g_idx]:
                return False
        return True

    mapping = {}
    used_pred = set()
    for g_idx in range(n_gold_cols):
        for p_idx in range(n_pred_cols):
            if p_idx in used_pred:
                continue
            if cols_match_exactly(p_idx, g_idx):
                mapping[g_idx] = p_idx
                used_pred.add(p_idx)
                break

    return mapping if len(mapping) == n_gold_cols else None


def iterated_execute_sql(predicted_sql, ground_truth, db_place, iterate_num, relaxed=True):
    predicted_sql = normalize_pg_sql(predicted_sql)
    ground_truth = normalize_pg_sql(ground_truth)
    conn = get_pg_connection(schema=db_place)
    diff_list = []
    cursor = conn.cursor()

    cursor.execute(predicted_sql)
    predicted_res = cursor.fetchall()
    pred_cols = [desc[0] for desc in cursor.description]

    cursor.execute(ground_truth)
    ground_truth_res = cursor.fetchall()
    gold_cols = [desc[0] for desc in cursor.description]

    cursor.close()
    conn.close()

    time_ratio = 0
    mismatch = True

    if set(predicted_res) == set(ground_truth_res):   
        mismatch = False

    else:
        # Case 1: column name match
        common_cols = [c for c in gold_cols if c in pred_cols]
        if common_cols:
            pred_idx = [pred_cols.index(c) for c in common_cols]
            gold_idx = [gold_cols.index(c) for c in common_cols]

            pred_projected = [tuple(row[i] for i in pred_idx) for row in predicted_res]
            gold_projected = [tuple(row[i] for i in gold_idx) for row in ground_truth_res]

            if set(pred_projected) == set(gold_projected):
                print(f"[RELAXED VES PASS] Matched on cols: {common_cols}, "
                      f"extra pred cols ignored: {[c for c in pred_cols if c not in gold_cols]}",
                      file=sys.stderr, flush=True)
                mismatch = False  # ← treat as match for VES timing
            
            elif is_numeric_match(pred_projected, gold_projected):
                print(f"[RELAXED VES PASS] Numeric tolerance match on cols: {common_cols}",
                    file=sys.stderr, flush=True)
                mismatch = False

        else:
            # Case 2: value-based column alignment (exact match, any col count)
            mapping = find_matching_column_indices(predicted_res, ground_truth_res)
            if mapping is not None:
                print(f"[RELAXED VES PASS] Value-based column alignment: {mapping}",
                      file=sys.stderr, flush=True)
                mismatch = False

            # Case 2: no common col names, same col count — try numeric tolerance
            elif len(pred_cols) == len(gold_cols):
                if is_numeric_match(predicted_res, ground_truth_res):
                    print(f"[RELAXED VES PASS] Numeric tolerance match",
                        file=sys.stderr, flush=True)
                    mismatch = False

            # Case 3: no common names, different col counts — can't relax
            else:
                print(f"[RELAXED VES SKIP] Cannot relax — no common col names and "
                    f"col count mismatch (pred={len(pred_cols)}, gold={len(gold_cols)})",
                    file=sys.stderr, flush=True)

    if not mismatch:
        for i in range(iterate_num):
            predicted_time = execute_sql(predicted_sql, db_place)
            ground_truth_time = execute_sql(ground_truth, db_place)
            if predicted_time > 1e-9:
                diff_list.append(ground_truth_time / predicted_time)
        processed_diff_list = clean_abnormal(diff_list)
        if len(processed_diff_list) > 0:
            time_ratio = sum(processed_diff_list) / len(processed_diff_list)
    return time_ratio, mismatch, len(predicted_res), len(ground_truth_res)


def execute_model(predicted_sql, ground_truth, db_place, idx, iterate_num, meta_time_out, relaxed=True):
    """
    Capture timeouts and execution errors instead of silently turning them into
    time_ratio=0. A time_ratio of 0 in VES now means *one of three* things
    that can be told apart via the extra fields: (a) result sets didn't match,
    (b) the query timed out, or (c) the query raised. Stderr is logged once
    per failing item so silent failures don't hide behind low VES.
    """
    timed_out = False
    error_msg = None
    time_ratio = 0
    mismatch = False
    pred_rc = None
    gold_rc = None
    try:
        # you can personalize the total timeout number
        # larger timeout leads to more stable ves
        # while it needs more your patience....
        if idx % 500 == 0:
            print(idx, file=sys.stdout, flush=True)
        time_ratio, mismatch, pred_rc, gold_rc = func_timeout(
            meta_time_out * iterate_num, iterated_execute_sql,
            args=(predicted_sql, ground_truth, db_place, iterate_num, relaxed))
    except KeyboardInterrupt:
        sys.exit(0)
    except FunctionTimedOut:
        timed_out = True
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}".strip()
        print(f"[VES] idx={idx} db_place={db_place} error: {error_msg}",
              file=sys.stderr, flush=True)

    return {
        'sql_idx': idx,
        'time_ratio': time_ratio,
        'timeout': timed_out,
        'error': error_msg,
        'mismatch': mismatch,
        'pred_row_count': pred_rc,
        'gold_row_count': gold_rc,
    }


def package_sqls(sql_path, db_root_path, mode='gpt', data_mode='dev'):
    clean_sqls = []
    db_path_list = []
    if mode == 'gpt':
        sql_data = json.load(open(sql_path, 'r', encoding='utf8'))
        for idx, sql_str in sql_data:
            if type(sql_str) == str:
                sql, db_name = sql_str.split('\t----- bird -----\t')
            else:
                sql, db_name = " ", "financial"
            clean_sqls.append(sql)
            db_path_list.append(db_name)

    elif mode == 'gt':
        sqls = open(sql_path, encoding='utf8')
        sql_txt = sqls.readlines()
        for idx, sql_str in enumerate(sql_txt):
            sql, db_name = sql_str.strip().split('\t')
            clean_sqls.append(sql)
            db_path_list.append(db_name)

    return clean_sqls, db_path_list


def run_sqls_parallel(sqls, db_places, num_cpus=1, iterate_num=100, meta_time_out=30.0, relaxed=True):
    pool = mp.Pool(processes=num_cpus)
    for i, sql_pair in enumerate(sqls):
        predicted_sql, ground_truth = sql_pair
        pool.apply_async(execute_model, args=(predicted_sql, ground_truth, db_places[i], i, iterate_num, meta_time_out, relaxed),
                         callback=result_callback)
    pool.close()
    pool.join()


def sort_results(list_of_dicts):
    return sorted(list_of_dicts, key=lambda x: x['sql_idx'])


def compute_ves(exec_results):
    num_queries = len(exec_results)
    if num_queries == 0:
        return 0
    total_ratio = 0
    count = 0

    for i, result in enumerate(exec_results):
        if result['time_ratio'] != 0:
            count += 1
        total_ratio += math.sqrt(result['time_ratio']) * 100
    ves = (total_ratio / num_queries)
    return ves


def load_json(dir):
    with open(dir, 'r', encoding='utf8') as j:
        contents = json.loads(j.read())
    return contents


def compute_ves_by_diff(exec_results, diff_json_path):
    num_queries = len(exec_results)
    contents = load_json(diff_json_path)
    # Support both list of items and dict with 'data'/'questions' or keyed by index
    if isinstance(contents, dict):
        contents = contents.get('data') or contents.get('questions') or list(contents.values())
    if not isinstance(contents, list):
        raise ValueError(f'diff_json_path must be a JSON list or dict; got {type(contents).__name__}')
    simple_results, moderate_results, challenging_results = [], [], []
    for i, content in enumerate(contents):
        if i >= num_queries:
            break
        if not isinstance(content, dict):
            continue
        difficulty = content.get('difficulty', 'simple')
        if difficulty == 'simple':
            simple_results.append(exec_results[i])
        elif difficulty == 'moderate':
            moderate_results.append(exec_results[i])
        elif difficulty == 'challenging':
            challenging_results.append(exec_results[i])
    simple_ves = compute_ves(simple_results)
    moderate_ves = compute_ves(moderate_results)
    challenging_ves = compute_ves(challenging_results)
    all_ves = compute_ves(exec_results)
    count_lists = [len(simple_results), len(moderate_results), len(challenging_results), num_queries]
    return simple_ves, moderate_ves, challenging_ves, all_ves, count_lists


def print_data(score_lists, count_lists):
    levels = ['simple', 'moderate', 'challenging', 'total']
    print("{:20} {:20} {:20} {:20} {:20}".format("", *levels))
    print("{:20} {:<20} {:<20} {:<20} {:<20}".format('count', *count_lists))

    print('=========================================    VES   ========================================')
    print("{:20} {:<20.2f} {:<20.2f} {:<20.2f} {:<20.2f}".format('ves', *score_lists))


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--predicted_sql_json_path', type=str, required=True, default='')
    args_parser.add_argument('--ground_truth_sql_path', type=str, required=True, default='')
    args_parser.add_argument('--data_mode', type=str, required=True, default='dev')
    args_parser.add_argument('--db_root_path', type=str, required=True, default='')
    args_parser.add_argument('--num_cpus', type=int, default=1)
    args_parser.add_argument('--meta_time_out', type=float, default=30.0)
    args_parser.add_argument('--mode_gt', type=str, default='gt')
    args_parser.add_argument('--mode_predict', type=str, default='gpt')
    args_parser.add_argument('--diff_json_path', type=str, required=True, default='')
    args = args_parser.parse_args()
    exec_result = []

    pred_queries, db_paths = package_sqls(args.predicted_sql_json_path, args.db_root_path, 
                                          mode=args.mode_predict, data_mode=args.data_mode)
    if len(pred_queries) == 0:
        raise ValueError(f'Empty data in {args.predicted_sql_json_path}')
    # generate gt sqls:
    gt_queries, db_paths_gt = package_sqls(args.ground_truth_sql_path, args.db_root_path, mode='gt',
                                           data_mode=args.data_mode)

    assert len(pred_queries) == len(gt_queries), "len(pred_queries) != len(gt_queries)"
    query_pairs = list(zip(pred_queries, gt_queries))
    run_sqls_parallel(query_pairs, iterate_num=100, db_places=db_paths, num_cpus=args.num_cpus, meta_time_out=args.meta_time_out, relaxed=True)
    exec_result = sort_results(exec_result)

    # Surface silent failures (mirrors evaluation_bird_ex.py): a 0 VES used to
    # cover "no row-set match", "timeout", and "raised an exception" all the
    # same way. Now we report each cause separately.
    total = len(exec_result)
    timeouts = sum(1 for r in exec_result if r.get('timeout'))
    errors = sum(1 for r in exec_result if r.get('error'))
    mismatches = sum(1 for r in exec_result if r.get('mismatch'))
    matched = sum(1 for r in exec_result if r.get('time_ratio', 0) != 0)

    # Per-failure dump: join worker results with diff_json so we can include
    # the original question/evidence next to the failing SQLs.
    try:
        raw_json_data = load_json(args.diff_json_path)
        if isinstance(raw_json_data, dict):
            raw_json_data = (raw_json_data.get('data')
                             or raw_json_data.get('questions')
                             or list(raw_json_data.values()))
        if not isinstance(raw_json_data, list):
            raw_json_data = []
    except Exception as e:
        print(f"[VES] could not load diff_json for failure dump: {e}",
              file=sys.stderr, flush=True)
        raw_json_data = []

    print('\n================================ VES FAILURES ================================')
    any_failed = False
    for r in exec_result:
        is_fail = r.get('timeout') or r.get('error') or r.get('mismatch')
        if not is_fail:
            continue
        any_failed = True
        i = r['sql_idx']
        item = raw_json_data[i] if i < len(raw_json_data) and isinstance(raw_json_data[i], dict) else {}
        db_id = item.get('db_id', db_paths[i] if i < len(db_paths) else '?')
        question = item.get('question', '')
        evidence = item.get('evidence', '')
        pred_sql = pred_queries[i] if i < len(pred_queries) else ''
        gold_sql = gt_queries[i] if i < len(gt_queries) else ''
        if r.get('timeout'):
            reason = 'timeout'
        elif r.get('error'):
            reason = 'exec_error'
        else:
            reason = 'mismatch'
        print(f"\033[1;31m[VES FAIL] idx={i} db_id={db_id} reason={reason}\033[0m")
        print(f"  \033[1;32m[question]\033[0m: {question}")
        if evidence:
            print(f"  \033[1;32m[evidence]\033[0m: {evidence}")
        print(f"  \033[1;32m[pred_sql]\033[0m: {pred_sql}")
        print(f"  \033[1;32m[gold_sql]\033[0m: {gold_sql}")
        if reason == 'mismatch':
            print(f"  \033[1;32m[rows_count]\033[0m: pred_row_count={r.get('pred_row_count')} gold_row_count={r.get('gold_row_count')}")
        elif reason == 'exec_error':
            print(f"  \033[1;32m[error]\033[0m: {r.get('error')}")
    if not any_failed:
        print('(no failures)')

    print(f"\n\033[1;33m[VES exec summary]\033[0m: total={total} matched={matched} "
          f"mismatches={mismatches} timeouts={timeouts} errors={errors}")

    print('start calculate')
    simple_ves, moderate_ves, challenging_ves, ves, count_lists = \
        compute_ves_by_diff(exec_result, args.diff_json_path)
    score_lists = [simple_ves, moderate_ves, challenging_ves, ves]
    print_data(score_lists, count_lists)
    print('===========================================================================================')
    print("Finished evaluation")
