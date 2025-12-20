import json
import re
from collections import defaultdict


def extract_functional_dependency_from_text(dependency_text):
    description = ""
    dependencies = {}
    lines = dependency_text.strip().split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if '→' not in line: 
            description = line
        else:
            
            line = line.replace('- ', '').rstrip(',')
          
            entity, attrs = line.split(':')
            entity = entity.strip()
            attrs = attrs.strip().split('，')  
            entity_dependencies = {}
            for attr in attrs:
                left, right = attr.split(' → ')
                left = left.strip().replace('(','').replace(')', '')
                right = right.strip().replace('(','').replace(')', '')
                right = right.split(',')
                if left not in entity_dependencies:
                    entity_dependencies[left] = []
                entity_dependencies[left].extend(right)
            if entity not in dependencies:
                dependencies[entity] = entity_dependencies
            else:
                for key, value in entity_dependencies.items(): 
                    if key in dependencies[entity]:
                        dependencies[entity][key].extend(entity_dependencies[key])
                    else:
                        dependencies[entity][key] = entity_dependencies[key]

   
    json_output = {"description": description, "dependencies": dependencies}

    return json_output


def get_common_element_list(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    intersection = list(set1.intersection(set2))
    return intersection



def compute_closure(base_set, deps):
    closure = set(base_set)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in deps:
            if lhs <= closure and not rhs <= closure:
                closure.update(rhs)
                changed = True
    return closure


def find_candidate_keys(attrs, deps):
    
    def is_candidate_key(candidate, deps, all_attributes):
        return compute_closure(candidate, deps) == all_attributes

    from itertools import combinations
    all_attributes = set(attrs)
    candidates = []
    for i in range(1, len(attrs) + 1):
        for combo in combinations(attrs, i):
            candidate = set(combo)
            if is_candidate_key(candidate, deps, all_attributes):
               
                if any(all(sub in candidate for sub in c) for c in candidates):
                    continue
                candidates.append(candidate)
    return candidates

def get_attribute_keys_by_arm_strong(dependencies_json):

    attributes_all = {}
    dependencies_all = {}
    for entity_name in dependencies_json:
        entity = dependencies_json[entity_name]
        attributes = []
        dependencies = []
        for depend_key in entity:
            if '&' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split('&')]  
            elif ',' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split(',')]  
            else:
                depend_key_list = [depend_key]
            attributes.extend(list(set(depend_key_list) | set(entity[depend_key])))
            dependencies.append((set(depend_key_list), set(entity[depend_key])))
        attributes = list(set(attributes))

        attributes_all[entity_name] = attributes
        dependencies_all[entity_name] = dependencies



    candidate_keys_dict = {}
    for entity_name in attributes_all:
        candidate_keys = find_candidate_keys(attributes_all[entity_name], dependencies_all[entity_name])
        
        candidate_keys_dict[entity_name] = candidate_keys
    return attributes_all, candidate_keys_dict



def get_attribute_keys_by_arm_strong_each(attributes, dependencies):
    dependencies_all = []
    for depend_key in dependencies:
        if '&' in depend_key:
            depend_key_list = [it.strip() for it in depend_key.split('&')] 
        elif ',' in depend_key:
            depend_key_list = [it.strip() for it in depend_key.split(',')] 
        else:
            depend_key_list = [depend_key]
        dependencies_all.append((set(depend_key_list), set(dependencies[depend_key])))

    candidate_keys = find_candidate_keys(attributes, dependencies_all)
    return candidate_keys



def decompose_to_3NF(entity_fd_json, entity_primary_keys):

    def parse_dependencies(entity_fd_json):
        functional_dependencies = []
        for entity, dependencies in entity_fd_json.items():
            for determinant, dependents in dependencies.items():
                determinant_list = [attr.strip() for attr in determinant.split(",")]
                functional_dependencies.append((determinant_list, dependents, entity))
        return functional_dependencies

    def find_closure(dependencies, target_set):
        closure = set(target_set)
        changed = True
        while changed:
            changed = False
            for X, Y in dependencies:
                if set(X).issubset(closure) and not set(Y).issubset(closure):
                    closure.update(Y)
                    changed = True
        return closure

   
    functional_dependencies = parse_dependencies(entity_fd_json)


    results_by_entity = defaultdict(lambda: {"Decomposition relationship": []})

    dependencies_by_entity = defaultdict(list)
    for determinant, dependent, entity in functional_dependencies:
        dependencies_by_entity[entity].append((determinant, dependent))
    for entity, deps in dependencies_by_entity.items():
        primary_keys = entity_primary_keys[entity]  

       
        relations = []
        for X, Y in deps:
            closure = find_closure(dependencies_by_entity[entity], X)

            if any(set(X).issubset(pk) for pk in primary_keys):
               
                if not set(Y).issubset(closure):
                    partial_relation = set(X) | set(Y)
                    if partial_relation not in relations:
                        relations.append(partial_relation)

        for X, Y in deps:
            if set(Y).issubset(find_closure(dependencies_by_entity[entity], X)):
                relation = set(X) | set(Y)
                if relation not in relations:
                    relations.append(relation)

        print('---------------------')
        print(relations)
        print(primary_keys)
        for pk in primary_keys:
            if not any(set(pk).issubset(relation) for relation in relations):
                relations.append(set(pk))

        
        unique_relations = []
        for rel in relations:
            if rel not in unique_relations:
                unique_relations.append(rel)


        
        results_by_entity[entity]["Decomposition relationship"] = unique_relations

    return results_by_entity



def detect_transitive_and_partial_dependencies(entity_fd_json, keys_and_attribute_map, entity_attributes_all):
    
    def parse_dependencies(entity_fd_json):
        functional_dependencies = []
        for entity, dependencies in entity_fd_json['dependencies'].items():
            for determinant, dependents in dependencies.items():
                determinant_list = [attr.strip() for attr in determinant.split(",")]
                for dependent in dependents:
                    dependent_list = [attr.strip() for attr in dependent.split(",")]
                    functional_dependencies.append((determinant_list, dependent_list, entity))
        return functional_dependencies


    functional_dependencies = parse_dependencies(entity_fd_json)

    results_by_entity = defaultdict(lambda: {"Decomposition relationship": []})

    dependencies_by_entity = defaultdict(list)
    for determinant, dependent, entity in functional_dependencies:
        dependencies_by_entity[entity].append((determinant, dependent))

    for entity, deps in dependencies_by_entity.items():
        attributes = entity_attributes_all[entity]
        primary_keys = keys_and_attribute_map[entity]  


        relations = []

        for X, Y in deps:
            closure = compute_closure(X, dependencies_by_entity[entity])

            if any(set(X).issubset(pk) for pk in primary_keys):

                if not set(Y).issubset(closure):
                    partial_relation = set(X) | set(Y)
                    if partial_relation not in relations:
                        relations.append(partial_relation)

        for X, Y in deps:
            if set(Y).issubset(compute_closure(X, dependencies_by_entity[entity])):
                relation = set(X) | set(Y)
                if relation not in relations:
                    relations.append(relation)

        for pk in primary_keys:
            if not any(set(pk).issubset(relation) for relation in relations):
                relations.append(set(pk))

        unique_relations = []
        for rel in relations:
            if rel not in unique_relations:
                unique_relations.append(rel)


        results_by_entity[entity]["Decomposition relationship"] = unique_relations

    return results_by_entity


def trans_relation_to_schema(relation_analyses_result, relation_attribute_analyses_result,
                            relation_type_analyses_result, attributes_all, entity_keys_and_attribute_map):

    def extract_relation(text):

        pattern = r"(\w+):([\w、]+)"
        matches = re.findall(pattern, text)


        relationships = {}
        for match in matches:
            relationship, entities_str = match

            entities = [entity.strip() for entity in entities_str.split('、')]

            relationships[relationship] = entities
        return relationships

    relationship_dict = extract_relation(relation_analyses_result)
    relation_type_analyses_result = relation_type_analyses_result.replace(']','') 
    relation_type_dict = extract_relation(relation_type_analyses_result) 
    relation_attribute_dict = extract_relation(relation_attribute_analyses_result) 

    print('********************************')
    print(relationship_dict)
    print(relation_type_analyses_result)
    print(relation_type_dict)
    print(relation_attribute_dict)

    multi_relation = {}
    for relation_name in relationship_dict:
        if relation_type_dict[relation_name][0] == 'many to many':
            entity_name_n1 = relationship_dict[relation_name][0]
            entity_n1_key = list(entity_keys_and_attribute_map[entity_name_n1][0])
            entity_name_n2 = relationship_dict[relation_name][1]
            entity_n2_key = list(entity_keys_and_attribute_map[entity_name_n2][0])

            relation_attribute_list = relation_attribute_dict[relation_name]
            relation_attribute_list.extend(entity_n1_key)
            relation_attribute_list.extend(entity_n2_key)
            multi_relation[relation_name] = {'property':relation_attribute_list, 'foreign_key':{entity_n1_key:{entity_name_n1:entity_n1_key}, entity_n2_key:{entity_name_n2: entity_n2_key}}}  # 这个格式就跟实体的属性格式很像了

        elif relation_type_dict[relation_name][0] == 'many to one':
            entity_name_1 = relationship_dict[relation_name][1]
            entity_1_key = list(entity_keys_and_attribute_map[entity_name_1][1])
            entity_name_n = relationship_dict[relation_name][0]
            attributes_all[entity_name_n].extend(entity_1_key)

        else: 
            entity_name_1 = relationship_dict[relation_name][0]
            entity_1_key = list(entity_keys_and_attribute_map[entity_name_1][0])
            entity_name_n = relationship_dict[relation_name][1]
            attributes_all[entity_name_n].extend(entity_1_key)

    return multi_relation





def trans_relation_to_schema_for_domain(relation_analyses_result, attributes_all,
                                      entity_keys_and_attribute_map):

    multi_relation = {}
    attributes_all_with_foreign_key = {}
    for relationship in relation_analyses_result:
        relation_name = list(relationship.keys())[0]

        if relationship['proportional relationship'] == 'many to many':
            entity_name_n1 = relationship[relation_name][0]
            entity_n1_key = list(entity_keys_and_attribute_map[entity_name_n1][0])
            entity_name_n2 = relationship[relation_name][1]
            entity_n2_key = list(entity_keys_and_attribute_map[entity_name_n2][0])

            relation_attribute_list = relationship['relationship properties']
            relation_attribute_list.extend(entity_n1_key)
            relation_attribute_list.extend(entity_n2_key)
            multi_relation[relation_name] = {'property':relation_attribute_list, 'foreign_key':{entity_n1_key[0]:{entity_name_n1:entity_n1_key[0]}, entity_n2_key[0]:{entity_name_n2: entity_n2_key[0]}}}  # 这个格式就跟实体的属性格式很像了

        elif relationship['proportional relationship'] == 'many to one':
            entity_name_1 = relationship[relation_name][1]
            entity_1_key = list(entity_keys_and_attribute_map[entity_name_1][1])
            entity_name_n = relationship[relation_name][0]
            attributes_all[entity_name_n].extend(entity_1_key)
            attributes_all_with_foreign_key[entity_name_n] = {'property':attributes_all[entity_name_n], '外键':{entity_1_key[0]:{entity_name_1:entity_1_key[0]}}}


        else:
            entity_name_1 = relationship[relation_name][0]
            entity_1_key = list(entity_keys_and_attribute_map[entity_name_1][0]) 
            entity_name_n = relationship[relation_name][1]
            attributes_all[entity_name_n].extend(entity_1_key)
            attributes_all_with_foreign_key[entity_name_n] = {'property':attributes_all[entity_name_n], '外键':{entity_1_key[0]:{entity_name_1:entity_1_key[0]}}}


    return multi_relation, attributes_all_with_foreign_key





def predict_entity_schema(entity_add_relation_attributes_all, entity_add_relation_keys_and_attribute_map):
    entity_attributes_all_and_key = {}
    for entity_name in entity_add_relation_attributes_all:
        attributes = list(entity_add_relation_attributes_all[entity_name]['property'])
        if '外键' in entity_add_relation_attributes_all[entity_name]:
            foreign_key = entity_add_relation_attributes_all[entity_name]['foreign_key']
        else:
            foreign_key = {}
        keys = list(entity_add_relation_keys_and_attribute_map[entity_name][0])
        entity_attributes_all_and_key[entity_name] = {'property':attributes, 'primary_key':keys, 'foreign_key':foreign_key}

    return entity_attributes_all_and_key


def predict_relation_schema(multi_relation, relation_keys_and_attribute_map):
    relation_attributes_all_and_key = {}
    for relation_name in multi_relation: 
        attributes = list(multi_relation[relation_name]['property'])
        keys = list(relation_keys_and_attribute_map[relation_name][0])
        relation_attributes_all_and_key[relation_name] = {'property':attributes, 'primary_key':keys, 'foreign_key':multi_relation[relation_name]['foreign_key']}  

    return relation_attributes_all_and_key



def clear_analyses(analyses):
    match = re.search("Finally it can be concluded(.*)", analyses, re.DOTALL)
    if match:
        content_after = match.group(1)
        return content_after.strip() 
    else:
        return "No matching content found"



def extract_json_from_text(text):
    data = {}
    if 'yes' in text or 'no' in text:
        data = {}
    else:
        match_s = re.search(r'[{\[]', text)
        matches_e = re.findall(r'[}\]]', text)
        if match_s and matches_e:
            first_bracket_pos = match_s.start()
            end_bracket_pos = text.rfind(matches_e[-1])
            json_str = text[first_bracket_pos: end_bracket_pos+1].replace('`', '').replace("'", '"')
            # print(json_str)
            data = json.loads(json_str)
        else:
            print('No JSON match found')

    return data





