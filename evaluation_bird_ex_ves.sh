#!/bin/bash

# Run from script directory so relative paths work from anywhere
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

num_cpus=12
meta_time_out=30.0
time_out=60
mode_gt="gt"
mode_predict="gpt"

# =============================================================================
# Small evaluation: foo test (20 samples) - same as run.sh test, try before full dev
# =============================================================================
FOO_PRED="./outputs/foo/predict_test.json"
FOO_GOLD="./data/foo/test_gold.sql"
FOO_DB_ROOT="./data/foo/test_databases/"
FOO_DIFF_JSON="./data/foo/test.json"

if [ -f "$FOO_PRED" ] && [ -f "$FOO_GOLD" ]; then
    echo "=============================================="
    echo "Small evaluation (foo test, 20 samples)"
    echo "=============================================="
    echo "Evaluate EX on foo test..."
    python ./evaluation/evaluation_bird_ex.py --db_root_path "$FOO_DB_ROOT" \
        --predicted_sql_json_path "$FOO_PRED" \
        --data_mode "test" \
        --ground_truth_sql_path "$FOO_GOLD" \
        --num_cpus $num_cpus \
        --mode_predict $mode_predict \
        --diff_json_path "$FOO_DIFF_JSON" \
        --meta_time_out $meta_time_out
    echo "Evaluate VES on foo test..."
    python ./evaluation/evaluation_bird_ves.py \
        --db_root_path "$FOO_DB_ROOT" \
        --predicted_sql_json_path "$FOO_PRED" \
        --data_mode "test" \
        --ground_truth_sql_path "$FOO_GOLD" \
        --num_cpus $num_cpus --meta_time_out $time_out \
        --mode_gt $mode_gt --mode_predict $mode_predict \
        --diff_json_path "$FOO_DIFF_JSON"
    echo "Foo test evaluation done!"
    echo ""
else
    echo "Skipping foo test evaluation (missing $FOO_PRED or $FOO_GOLD). Run run.sh first to generate predict_test.json."
    echo ""
fi

# =============================================================================
# Full BIRD dev evaluation
# =============================================================================
# db_root_path="./data/bird/dev_databases/"
# data_mode="dev"
# diff_json_path="./data/bird/dev.json"
# predicted_sql_json_path="./outputs/bird/predict_dev.json"
# ground_truth_sql_path="./data/bird/dev_gold.sql"

# # Require prediction file (generate first with run.sh on BIRD dev)
# if [ ! -f "$predicted_sql_json_path" ]; then
#     echo "Error: Prediction file not found: $predicted_sql_json_path"
#     echo "Run the BIRD dev pipeline first, e.g. uncomment and run the BIRD dev block in run.sh"
#     exit 1
# fi
# if [ ! -f "$ground_truth_sql_path" ]; then
#     echo "Error: Ground truth not found: $ground_truth_sql_path"
#     exit 1
# fi

# # evaluate EX
# echo "Evaluate BIRD EX begin!"
# start_time=$(date +%s)
# python ./evaluation/evaluation_bird_ex.py --db_root_path $db_root_path \
#     --predicted_sql_json_path $predicted_sql_json_path \
#     --data_mode $data_mode \
#     --ground_truth_sql_path $ground_truth_sql_path \
#     --num_cpus $num_cpus \
#     --mode_predict $mode_predict \
#     --diff_json_path $diff_json_path \
#     --meta_time_out $meta_time_out
# echo "Evaluate EX done!"

# # evaluate VES
# echo "Evaluate BIRD VES begin!"
# python ./evaluation/evaluation_bird_ves.py \
#     --db_root_path $db_root_path \
#     --predicted_sql_json_path $predicted_sql_json_path \
#     --data_mode $data_mode \
#     --ground_truth_sql_path $ground_truth_sql_path \
#     --num_cpus $num_cpus --meta_time_out $time_out \
#     --mode_gt $mode_gt --mode_predict $mode_predict \
#     --diff_json_path $diff_json_path
# echo "Evaluate VES done!"
# end_time=$(date +%s)
# elapsed=$(( end_time - start_time ))
# elapsed_minutes=$(( elapsed / 60 ))
# elapsed_seconds=$(( elapsed % 60 ))
# echo "BIRD evaluation finished in ${elapsed_minutes} minutes and ${elapsed_seconds} seconds."