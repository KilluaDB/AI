# Used for reading data from the database
import copy
import json
import os
import re
import random
from collections import defaultdict
import ast
import math
from pymongo import MongoClient
from tqdm import tqdm
from datetime import datetime
#
# # Connect to MongoDB
# client = MongoClient('mongodb://localhost:27017/')
# client = MongoClient('mongodb://wangqin:123456@localhost:27017/?authSource=admin')
#
# # Try to get database list
# db_list = client.list_database_names()
#
# if db_list:
#     print("Connection successful")
#     print(db_list)
# else:
#     print("Connection failed")
#
# # Select database and collection
# db = client['database_design']
# anno_collection = db['annotation_round2']  #annotation_round3_test
#


def get_chinese_saved_data():
    current_time = datetime.now()
    # Format as hour_minute format
    formatted_time = current_time.strftime("%H_%M")
    # save_path = f'datasets/RSchema/annotation_0215_{formatted_time}.jsonl'
    save_path = f'datasets/RSchema/annotation_chinese_all.jsonl'
    saved_doc = anno_collection.find({"status": 'Second Round Saved'})
    finish_annotation_list = [doc for doc in saved_doc]
    # Format conversion, convert all to lowercase format
    for i, item in enumerate(finish_annotation_list):
        item['_id'] = str(item['_id'])

    save_datas = []
    for item in finish_annotation_list:
        try:
            # 处理一下schema的格式
            schemas = {}
            schema_id_name_pair = {}
            for schema_key in item['standard_schema']:
                schema_item = item['standard_schema'][schema_key]
                # print(schema_item)
                schema_name = schema_item['模式名']   # Schema Name (Chinese key)
                schema_id_name_pair[schema_key] = schema_name

            for schema_key in item['standard_schema']:
                schema_item = item['standard_schema'][schema_key]
                # print(schema_item)
                schema_name = schema_item['模式名']  # Schema Name (Chinese key)
                # Process foreign keys
                new_foreign_key = defaultdict(dict)
                foreign_key = schema_item['外键']  # Foreign key (Chinese key)
                for f_key in foreign_key:
                    f_item = foreign_key[f_key]
                    for f_item_con_key in f_item:
                        if f_item_con_key in schema_id_name_pair:
                            key = schema_id_name_pair[f_item_con_key]
                            new_foreign_key[f_key][key] = foreign_key[f_key][f_item_con_key]
                        else:
                            new_foreign_key[f_key][f_item_con_key] = foreign_key[f_key][f_item_con_key]

                schemas[schema_name] = {'属性':schema_item['属性'], '主键':schema_item['主键'], '外键':new_foreign_key}  # Chinese keys: Attributes, Primary key, Foreign key

            # if item['remarks'] != '' and item['remarks'] is not None and item['assign_to']!='tk':
            #     print('remarks')
            #     print(item)

            save_datas.append({'id':str(item['_id']), '业务场景': item['text'], 'answer':schemas, 'entities': item['entities'], 'relations': item['relations'], 'remarks':item['remarks']})  # Business scenario
        except Exception as e:
            print(e)
            print(item)

    print(len(save_datas))

    # Save
    with open(save_path, 'w', encoding='utf-8') as f:
        for data in save_datas:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')

    print(f'finish saving to file : {save_path}')





def get_saved_data():
    current_time = datetime.now()
    # Format as hour_minute format
    formatted_time = current_time.strftime("%H_%M")
    save_path = f'datasets/RSchema/annotation_0215_{formatted_time}.jsonl'
    saved_doc = anno_collection.find({"status": 'Third Round Saved'})
    finish_annotation_list = [doc for doc in saved_doc]
    # Format conversion, convert all to lowercase format
    for i, item in enumerate(finish_annotation_list):
        item['_id'] = str(item['_id'])
        item_str_ori = json.dumps(item, ensure_ascii=False)
        item_str = (item_str_ori.replace('Attribute', 'Attributes').
                    replace('attribute', 'Attributes').
                    replace('attributes', 'Attributes').
                    replace('Attributess', 'Attributes').
                    replace('Properties', 'Attributes').
                    replace('Primary keys', 'Primary key').
                    replace('primary keys', 'Primary key').
                    replace('primary key', 'Primary key').
                    replace('Primary Key', 'Primary key').
                    replace('Foreign keys', 'Foreign key').
                    replace('foreign keys', 'Foreign key').
                    replace('foreign key', 'Foreign key').
                    replace('Foreign Key', 'Foreign key').
                    replace('Scheme', 'Schema').
                    replace('schema name', 'Schema Name').
                    replace('Schema name', 'Schema Name').
                    replace('Mode Name', 'Schema Name').
                    replace('Mode name', 'Schema Name').
                    replace('Model Name', 'Schema Name'))

        finish_annotation_list[i] = json.loads(item_str)


    save_datas = []
    for item in finish_annotation_list:
        try:
            # Process the schema format
            schemas = {}
            schema_id_name_pair = {}
            for schema_key in item['standard_schema']:
                schema_item = item['standard_schema'][schema_key]
                # print(schema_item)
                schema_name = schema_item['Schema Name']   #
                schema_id_name_pair[schema_key] = schema_name

            for schema_key in item['standard_schema']:
                schema_item = item['standard_schema'][schema_key]
                # print(schema_item)
                schema_name = schema_item['Schema Name']  # Schema Name
                # Process foreign keys
                new_foreign_key = defaultdict(dict)
                foreign_key = schema_item['Foreign key']  #
                for f_key in foreign_key:
                    f_item = foreign_key[f_key]
                    for f_item_con_key in f_item:
                        if f_item_con_key in schema_id_name_pair:
                            key = schema_id_name_pair[f_item_con_key]
                            new_foreign_key[f_key][key] = foreign_key[f_key][f_item_con_key]
                        else:
                            new_foreign_key[f_key][f_item_con_key] = foreign_key[f_key][f_item_con_key]

                schemas[schema_name] = {'Attributes':schema_item['Attributes'], 'Primary key':schema_item['Primary key'], 'Foreign key':new_foreign_key}

            # if item['remarks'] != '' and item['remarks'] is not None and item['assign_to']!='tk':
            #     print('remarks')
            #     print(item)

            save_datas.append({'id':str(item['_id']), 'question': item['text'], 'answer':schemas, 'entities': item['entities'], 'relations': item['relations'], 'remarks':item['remarks']})  # 'assign_to':item['assign_to'],
        except Exception as e:
            print(e)
            print(item)

    print(len(save_datas))

    # Save
    with open(save_path, 'w', encoding='utf-8') as f:
        for data in save_datas:
            json.dump(data, f, ensure_ascii=False)
            f.write('\n')

    print(f'finish saving to file : {save_path}')

def extract_answer_from_text():
    # file_path = 'outputs/DBdesignText/DBdesignAgent_annotation_0203_21_34_deepseek.txt'
    # save_path = 'outputs/DBdesign/deepseek_chat_agent_0203_21_34.jsonl'
    file_path = 'outputs/DBdesign_domain/text/agent_chat_healthcare_domain_chatgpt.txt'
    save_path = 'outputs/DBdesign_domain/healthcare_domain_chatgpt_chat_agent_evaluation.jsonl'
    with open(file_path, 'r', encoding='utf-8') as f:
        # Open file and read contents
        content = f.read()

    entries = re.split(r'---- id:', content)[1:]  # First remove the empty string at the beginning
    data_list = []
    for entry in entries:
        # Extract id
        id_match = re.match(r'([a-f0-9]{24})', entry)
        if id_match:
            id_value = id_match.group(1)
            print(id_value)
            # Get trajectory (execution order) information
            trajectory = []
            agents = re.findall(r'---------- (\w+Agent) ----------', entry)
            trajectory.extend(agents)  # Collect all Agent names as execution order

            pattern = r'```json(.*?)```'
            matches = re.findall(pattern, entry, re.DOTALL)
            flag = 0
            # Print matched content
            for match in matches[::-1]:  # Reverse order
                try:
                    match_format = json.loads(match.strip())
                except:
                    try:
                        match_format = json.loads(match.strip().replace("'", '"'))
                    except Exception as e:
                        print(e)
                        match_format = match
                        if '"schema"' in match_format or "'schema'" in match_format:  #schema  #output
                            flag = 1
                if isinstance(match_format, dict) and 'schema' in match_format:
                    answer = match_format['schema']
                elif flag == 1:
                    answer = match_format
                else:
                    continue
                # 创建字典并加入到列表
                data_dict = {
                    "id": id_value,
                    "trajectory": trajectory,
                    "predict": answer
                }
                print(f'Successfully saved: {id_value}')
                data_list.append(data_dict)
                break

    # save
    with open(save_path, 'a+', encoding='utf-8') as f:
        for data in data_list:
            f.write(json.dumps(data) + '\n')

    print(f'finish saving to file : {save_path}')







def extract_answer_from_cot_text():
    file_path = 'temp.txt'
    save_path = 'outputs/DBdesign/deepseek-base_cot_0203_21_34_fewshot.jsonl'

    with open(file_path, 'r', encoding='utf-8') as f:
        # Open file and read contents
        content = f.read()

    entries = re.split(r'---- id : ', content)[1:]  # First remove the empty string at the beginning
    data_list = []
    for entry in entries:
        # Extract id
        id_match = re.match(r'([a-f0-9]{24})', entry)
        if id_match:
            id_value = id_match.group(1)
            print(id_value)

            pattern = r'```json(.*?)```'
            matches = re.findall(pattern, entry, re.DOTALL)
            flag = 0
            # Print matched content
            for match in matches[::-1]:  # Reverse order
                try:
                    match_format = json.loads(match.strip())
                except:
                    try:
                        match_format = json.loads(match.strip().replace("'", '"'))
                    except Exception as e:
                        print(e)
                        match_format = match
                        if '"schema"' in match_format or "'schema'" in match_format:  #schema  #output
                            flag = 1
                if isinstance(match_format, dict) and 'schema' in match_format:
                    answer = match_format
                elif flag == 1:
                    answer = match_format
                else:
                    continue
                # Create dictionary and add to list
                data_dict = {
                    "id": id_value,
                    "answer": answer,
                }
                data_list.append(data_dict)
                break

    # save
    with open(save_path, 'a+', encoding='utf-8') as f:
        for data in data_list:
            f.write(json.dumps(data) + '\n')

    print(f'finish saving to file : {save_path}')








# Check if all data is in proper format
def check_data():
    file_path = 'outputs/DBdesignExample/agent_group_chat_execution.jsonl'
    # file_path = 'datasets/DBexample/test_english.jsonl'
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        datas = [json.loads(line) for line in lines]

    for i, item in enumerate(datas):
        print(f'{i} -------------')
        if 'answer' in item:
            schemas = item['answer']
            for schema_name in schemas:
                if 'Primary key' not in schemas[schema_name]:
                    print('Primary key', schema_name)
                    assert 1==0
                if 'Attribute' not in schemas[schema_name]:
                    print('Attribute', schema_name)
                    assert 1==0
                if 'Primary key' not in schemas[schema_name]:
                    print('Primary key', schema_name)
                    assert 1==0
                # if 'Foreign key' not in schemas[schema_name]:
                #     schemas[schema_name]['Foreign key'] = {}


def get_ready_data():
    file_path = 'datasets/RSchema/annotation_0203_21_34.jsonl'
    without_file_path = ['datasets/RSchema/annotation_0125_21_59.jsonl', 'datasets/RSchema/annotation_0201_01_19.jsonl']
    save_path = f'datasets/RSchema/ready_data.jsonl'
    origin_data_id = []
    for path in without_file_path:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                line = json.loads(line)
                origin_data_id.append(line['id'])
    print(f'Number of already generated items: {len(origin_data_id)}')

    save_datas = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = json.loads(line)
            if line['id'] not in origin_data_id:
                save_datas.append(line)
    print(f'Number of items to be generated: {len(save_datas)}')
    # save
    with open(save_path, 'w', encoding='utf-8') as f:
        for data in save_datas:
            f.write(json.dumps(data) + '\n')

    print(f'finish saving to file : {save_path}')


# Remove duplicates
def remove_duplicates():
    path = 'outputs/DBdesign/deepseek-base_cot_0203_21_34.jsonl'
    datas = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            line = json.loads(line)
            if line['id'] not in datas:
                datas[line['id']] = line
            else:
                print(f'Duplicate id: {line["id"]}')

    print(len(datas.keys()))

    # # save
    # with open(path, 'w', encoding='utf-8') as f:
    #     for key in datas:
    #         f.write(json.dumps(datas[key]) + '\n')
    # print(f'finish saving to file : {path}')


# Determine if answer is string type
def determine_string_answer():
    path = 'outputs/DBdesign/gpt4_chat_pipeline_0203_21_34.jsonl'
    count = 0
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            print(i)
            line = json.loads(line)
            if isinstance(line['predict'], str):
                print(line['id'])
                count += 1

    print(count)





# get_saved_data()
# get_chinese_saved_data()
# get_ready_data()
extract_answer_from_text()
# extract_answer_from_cot_text()
# check_data()
# remove_duplicates()
# determine_string_answer()