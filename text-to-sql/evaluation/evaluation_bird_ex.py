import os
import re
import sys
import json
import argparse
import multiprocessing as mp
import logging
from func_timeout import func_timeout, FunctionTimedOut
from db_utils import get_pg_connection, normalize_pg_sql

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False  # Prevent duplicate logging to root logger

def replace_multiple_spaces(text):
    pattern = r'\s+'
    new_text = re.sub(pattern, ' ', text)
    return new_text


def load_json(dir):
    with open(dir, 'r', encoding='utf8') as j:
        contents = json.loads(j.read())
    return contents


def save_json_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"save json file to {path}")


def result_callback(result):
    exec_result.append(result)


def execute_sql(predicted_sql, ground_truth, db_place):
    conn = get_pg_connection(schema=db_place)
    cursor = conn.cursor()
    cursor.execute(normalize_pg_sql(predicted_sql))
    predicted_res = cursor.fetchall()
    cursor.execute(normalize_pg_sql(ground_truth))
    ground_truth_res = cursor.fetchall()
    cursor.close()
    conn.close()
    res = 0
    if set(predicted_res) == set(ground_truth_res):
        res = 1
    return res



def execute_model(predicted_sql, ground_truth, db_place, idx, meta_time_out):
    """
    Run pred vs gold and classify the outcome into pass / mismatch / timeout /
    exec_error. The legacy `res` (0/1) is kept for backward compatibility with
    scoring; the new fields surface *why* a 0 happened so the post-run
    summary can distinguish silent failures from real wrong answers.
    """
    error_type = 'pass'
    error_msg = None
    pred_rc = None
    gt_rc = None
    res = 0
    try:
        res, pred_rc, gt_rc = func_timeout(meta_time_out, execute_sql,
                                           args=(predicted_sql, ground_truth, db_place))
        if res == 0:
            error_type = 'mismatch'
    except KeyboardInterrupt:
        sys.exit(0)
    except FunctionTimedOut:
        error_type = 'timeout'
        print(f"[EX] idx={idx} db_place={db_place} timeout",
              file=sys.stderr, flush=True)
    except Exception as e:
        error_type = 'exec_error'
        error_msg = f"{type(e).__name__}: {e}".strip()
        print(f"[EX] idx={idx} db_place={db_place} error: {error_msg}",
              file=sys.stderr, flush=True)
    return {
        'sql_idx': idx,
        'res': res,
        'error_type': error_type,
        'error_msg': error_msg,
        'pred_row_count': pred_rc,
        'gold_row_count': gt_rc,
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


def run_sqls_parallel(sqls, db_places, num_cpus=1, meta_time_out=30.0):
    pool = mp.Pool(processes=num_cpus)
    for i, sql_pair in enumerate(sqls):

        predicted_sql, ground_truth = sql_pair
        pool.apply_async(execute_model, args=(predicted_sql, ground_truth, db_places[i], i, meta_time_out), callback=result_callback)
    pool.close()
    pool.join()


def sort_results(list_of_dicts):
  return sorted(list_of_dicts, key=lambda x: x['sql_idx'])


def compute_acc_by_diff(exec_results, diff_json_path):
    num_queries = len(exec_results)
    results = [res['res'] for res in exec_results]
    contents = load_json(diff_json_path)
    simple_results, moderate_results, challenging_results = [], [], []

    for i, content in enumerate(contents):
        difficulty = content.get('difficulty', 'simple')
        if difficulty == 'simple':
            try:
                simple_results.append(exec_results[i])
            except Exception as e:
                print(e)
                import pdb
                pdb.set_trace()

        if difficulty == 'moderate':
            moderate_results.append(exec_results[i])

        if difficulty == 'challenging':
            challenging_results.append(exec_results[i])

    if len(simple_results) == 0:
        simple_acc = 0.0
    else:
        simple_acc = sum([res['res'] for res in simple_results]) / len(simple_results)

    if len(moderate_results) == 0:
        moderate_acc = 0
    else:
        moderate_acc = sum([res['res'] for res in moderate_results])/len(moderate_results)
    
    if len(challenging_results) == 0:
        challenging_acc = 0
    else:
        challenging_acc = sum([res['res'] for res in challenging_results])/len(challenging_results)
    
    all_acc = sum(results)/num_queries
    count_lists = [len(simple_results), len(moderate_results), len(challenging_results), num_queries]
    return simple_acc * 100, moderate_acc * 100, challenging_acc * 100, all_acc * 100, count_lists


def print_data(score_lists,count_lists):
    levels = ['simple', 'moderate', 'challenging', 'total']
    print("{:20} {:20} {:20} {:20} {:20}".format("", *levels))
    print("{:20} {:<20} {:<20} {:<20} {:<20}".format('count', *count_lists))

    print('======================================    ACCURACY    =====================================')
    print("{:20} {:<20.2f} {:<20.2f} {:<20.2f} {:<20.2f}".format('accuracy', *score_lists))


if __name__ == '__main__':
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--predicted_sql_json_path', type=str, required=True)
    args_parser.add_argument('--ground_truth_sql_path', type=str, required=True)
    args_parser.add_argument('--data_mode', type=str, required=True, default='dev', choices=['train', 'dev', 'test'])
    args_parser.add_argument('--db_root_path', type=str, required=True)
    args_parser.add_argument('--num_cpus', type=int, default=1)
    args_parser.add_argument('--meta_time_out', type=float, default=30.0)
    args_parser.add_argument('--mode_predict', type=str, default='gpt')
    args_parser.add_argument('--difficulty',type=str, default='simple')
    args_parser.add_argument('--diff_json_path',type=str,default='./data/bird/dev.json')
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
    run_sqls_parallel(query_pairs, db_places=db_paths, num_cpus=args.num_cpus, meta_time_out=args.meta_time_out)
    exec_result = sort_results(exec_result)

    # save ex results
    out_dir = os.path.dirname(args.predicted_sql_json_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    result_json_path = os.path.join(out_dir, f'eval_result_{args.data_mode}.json')
    
    # relocate idx of exec_result (use actual gt_queries for gold, not diff_json which may have empty SQL)
    raw_json_data = load_json(args.diff_json_path)
    pred_sqls = [replace_multiple_spaces(s) for s in pred_queries]
    gt_sqls = [replace_multiple_spaces(s) for s in gt_queries]
    result_json_lst = []
    for i, item in enumerate(raw_json_data):
        item['pred'] = pred_sqls[i]
        item['gold'] = gt_sqls[i] if i < len(gt_sqls) else item.get('SQL', '')
        if 'SQL' in item:
            del item['SQL']
        item['res'] = exec_result[i]['res']
        result_json_lst.append(item)
    save_json_file(result_json_path, result_json_lst)

    # Per-failure dump: walk results in idx order and emit a human-readable
    # block for everything that didn't pass, joining worker output with the
    # original question/evidence from diff_json.
    total = len(exec_result)
    passed = sum(1 for r in exec_result if r.get('error_type') == 'pass')
    mismatches = sum(1 for r in exec_result if r.get('error_type') == 'mismatch')
    timeouts = sum(1 for r in exec_result if r.get('error_type') == 'timeout')
    exec_errors = sum(1 for r in exec_result if r.get('error_type') == 'exec_error')

    print('\n================================ EX FAILURES ================================')
    any_failed = False
    for r in exec_result:
        if r.get('error_type') == 'pass':
            continue
        any_failed = True
        i = r['sql_idx']
        item = raw_json_data[i] if i < len(raw_json_data) else {}
        db_id = item.get('db_id', db_paths[i] if i < len(db_paths) else '?')
        question = item.get('question', '')
        evidence = item.get('evidence', '')
        pred_sql = pred_sqls[i] if i < len(pred_sqls) else ''
        gold_sql = gt_sqls[i] if i < len(gt_sqls) else ''
        reason = r.get('error_type', 'unknown')
        print(f"[EX FAIL] idx={i} db_id={db_id} reason={reason}")
        print(f"  question: {question}")
        if evidence:
            print(f"  evidence: {evidence}")
        print(f"  pred_sql: {pred_sql}")
        print(f"  gold_sql: {gold_sql}")
        if reason == 'mismatch':
            print(f"  pred_row_count={r.get('pred_row_count')} gold_row_count={r.get('gold_row_count')}")
        elif reason == 'exec_error':
            print(f"  error: {r.get('error_msg')}")
    if not any_failed:
        print('(no failures)')

    print(f"\nEX exec summary: total={total} passed={passed} "
          f"mismatches={mismatches} timeouts={timeouts} exec_errors={exec_errors}")

    print('start calculate')
    simple_acc, moderate_acc, challenging_acc, acc, count_lists = \
        compute_acc_by_diff(exec_result, args.diff_json_path)
    score_lists = [simple_acc, moderate_acc, challenging_acc, acc]
    print_data(score_lists,count_lists)
    print('===========================================================================================')
    print("Finished evaluation")
