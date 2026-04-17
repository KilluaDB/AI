# Used alongside prompt_generator_format.py to handle cases where the model output
# format is not fully controllable.

from collections import defaultdict

from prompt_generator_format import *
from data_utils import *
import json
from utils import (extract_functional_dependency_from_text, get_attribute_keys_by_arm_strong,
                   get_attribute_keys_by_arm_strong_each,get_common_element_list,
                   decompose_to_3NF, trans_relation_to_schema, predict_entity_schema, predict_relation_schema,
                   clear_analyses, trans_relation_to_schema_for_domain)



# Implements the multi-agent workflow and records the full interaction process.
def fully_decode(question, handler, args):
    data_info = {}
    if args.method == "base_direct":   # Generate the full schema in one step (zero-shot).
        if args.few_shot:
            direct_prompt = get_direct_few_shot_prompt(question)
        else:
            direct_prompt = get_direct_prompt(question)
        # handler.get_output_multiagent generates the model response from a prompt.
        output, output_json = handler.get_output_multiagent(user_input=direct_prompt, temperature=0, max_tokens=1000, system_role="")  # 没有system role

        # output is a string; parse it and store as JSON.
        print(f'output:\n {output}')
        data_info = {
            'question': question,
            'answer': output_json,
        }

    elif args.method == "base_cot":
        if args.few_shot:
            cot_prompt = get_cot_few_shot_prompt(question)
        else:
            cot_prompt = get_cot_prompt(question)
        output, output_json = handler.get_output_multiagent(user_input=cot_prompt, temperature=0, max_tokens=1000, system_role="")
        data_info = {
            'question': question,
            'answer': output_json,
            # 'gold_schema': gold_answer
        }

    # TODO: prompt formats for this method are not tuned yet.
    elif args.method == "expert_analyse":
        # Split into multiple subtasks; each subtask uses an agent.
        # This may be too granular (up to ~9 agents / ~9 LLM calls).
        print('### -------------------- Phase 1: Convert requirements to a conceptual model ---------------------- ###')

        do_requirement_analyse = False  # Controls whether to run requirement analysis.

        if do_requirement_analyse:
            # 1. Use an agent to analyze requirements.
            question_analyzer, prompt_get_question_analysis = get_question_analysis_prompt(question)
            # Requirement analysis result.
            question_analyses = handler.get_output_multiagent(user_input=prompt_get_question_analysis,
                                                                  temperature=0, max_tokens=3000,
                                                                  system_role=question_analyzer)
        else:
            question_analyses = question

        # 2. Identify entity sets. Returns: (role, prompt).
        # TODO: output format constraints are still loose.
        entity_analyzer, prompt_get_entity_analyses = get_entity_analysis_prompt(question_analyses)

        # Entity recognition result.
        entity_analyses = handler.get_output_multiagent(user_input=prompt_get_entity_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=entity_analyzer)

        # Keep only the final result, remove analysis steps.
        entity_analyses_result = clear_analyses(entity_analyses)

        # 3. Identify entity attributes based on the entity recognition result.
        entity_attribute_analyzer, prompt_get_entity_attribute_analyses = get_entity_attribute_analysis_prompt(question_analyses, entity_analyses_result)

        # Entity attribute recognition result.
        entity_attribute_analyses = handler.get_output_multiagent(user_input=prompt_get_entity_attribute_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=entity_attribute_analyzer)
        entity_attribute_analyses_result = clear_analyses(entity_attribute_analyses)


        # 4. Identify relationships between entities.
        # Usually binary/ternary; unary/quaternary are rare.
        # TODO: the model often infers relation types automatically; consider merging later.
        relation_analyzer, prompt_get_relation_analyses = get_relation_analysis_prompt(question_analyses, entity_analyses)
        relation_analyses = handler.get_output_multiagent(user_input=prompt_get_relation_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=relation_analyzer)
        relation_analyses_result = clear_analyses(relation_analyses)


    # 5. Determine relationship cardinality.
    # TODO: explicitly constrain to 1-1 / 1-N / N-N.
        relation_type_analyzer, prompt_get_relation_type_analyses = get_relation_analysis_type_prompt(question_analyses, relation_analyses_result)
        relation_type_analyses = handler.get_output_multiagent(user_input=prompt_get_relation_type_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=relation_type_analyzer)
        relation_type_analyses_result = clear_analyses(relation_type_analyses)



    # 6. Determine relationship attributes.
    # TODO: avoid including endpoint primary keys here (unknown at this stage).
        relation_attribute_analyzer, prompt_get_relation_attribute_analyses = get_relation_analysis_attribute_prompt(question_analyses, entity_attribute_analyses_result, relation_analyses_result)
        relation_attribute_analyses = handler.get_output_multiagent(user_input=prompt_get_relation_attribute_analyses,
                                                               temperature=0, max_tokens=800,
                                                               system_role=relation_attribute_analyzer)
        relation_attribute_analyses_result = clear_analyses(relation_attribute_analyses)


        # 7. Identify functional dependencies between entity attributes.
        entity_functional_dependency_analyzer, prompt_get_entity_functional_dependency_analyses = get_entity_functional_dependency_analysis_prompt(
            question_analyses, entity_attribute_analyses_result)
        entity_functional_dependency_analyses = handler.get_output_multiagent(user_input=prompt_get_entity_functional_dependency_analyses,
                                                               temperature=0, max_tokens=800,
                                                               system_role=entity_functional_dependency_analyzer)
        entity_functional_dependency_analyses_result = clear_analyses(entity_functional_dependency_analyses)



        print('### -------------------- Phase 2: Convert conceptual model to relational model ---------------------- ###')

        # 1) Entity conversion: each entity becomes a schema/table.

        # 2) Relationship conversion: enforce referential integrity.
        # Only N:N creates a new schema; 1:N and 1:1 typically add the key to the N-side.
        # 8. Get entity primary keys. Convert functional dependency text to JSON.
        entity_functional_dependency_json = extract_functional_dependency_from_text(entity_functional_dependency_analyses_result)
        print(f'entity_functional_dependency_json:\n {entity_functional_dependency_json}')

        # Use Armstrong's axioms to derive candidate keys and non-key attributes.
        # TODO: if results look wrong, consider adjusting earlier steps.
        entity_attributes_all, entity_keys_and_attribute_map = get_attribute_keys_by_arm_strong(entity_functional_dependency_json)
        print(f'entity_attributes_all:\n {entity_attributes_all}')
        print(f'entity_keys_and_attribute_map:\n {entity_keys_and_attribute_map}')

        # 9. Update entity attributes/schemas based on relationship types.
        # multi_relation matches the entity_attributes_all data shape.
        multi_relation = trans_relation_to_schema(relation_analyses_result, relation_attribute_analyses_result,
                                                                 relation_type_analyses_result, entity_attributes_all, entity_keys_and_attribute_map)
        print(f'multi_relation:\n {multi_relation}')

        # 3) Normalization

        # 10. Identify functional dependencies after adding relationship attributes.
        # This is for decomposition, not for primary key discovery.
        entity_functional_dependency_analyzer, prompt_get_entity_functional_dependency_analyses = get_entity_functional_dependency_analysis_prompt(
            question_analyses, json.dumps(entity_attributes_all, ensure_ascii=False))
        entity_add_relation_functional_dependency_analyses = handler.get_output_multiagent(
                                                    user_input=prompt_get_entity_functional_dependency_analyses,
                                                    temperature=0, max_tokens=800,
                                                    system_role=entity_functional_dependency_analyzer)
        entity_add_relation_functional_dependency_analyses_result = clear_analyses(entity_add_relation_functional_dependency_analyses)


        print(f'entity_add_relation_functional_dependency_analyses_result:\n {entity_add_relation_functional_dependency_analyses_result}')

        entity_add_relation_functional_dependency_json = extract_functional_dependency_from_text(
            entity_add_relation_functional_dependency_analyses_result)
        print(f'entity_add_relation_functional_dependency_json:\n {entity_add_relation_functional_dependency_json}')

    # Use Armstrong's axioms again to compute keys.
    # TODO: if results look wrong, consider adjusting earlier steps.
        entity_add_relation_attributes_all, entity_add_relation_keys_and_attribute_map = get_attribute_keys_by_arm_strong(
                                                                            entity_add_relation_functional_dependency_json)

        print(f'entity_add_relation_attributes_all:\n {entity_add_relation_attributes_all}')
        print(f'entity_add_relation_keys_and_attribute_map:\n {entity_add_relation_keys_and_attribute_map}')

    # 11. Check for partial/transitive dependencies to ensure 2NF/3NF.
        transitive_partial_dependencies = decompose_to_3NF(
                                                            entity_add_relation_functional_dependency_json,
                                                            entity_add_relation_attributes_all,
                                                            entity_add_relation_keys_and_attribute_map
                                                            )
        transitive_partial_dependencies = {key: value for key, value in transitive_partial_dependencies.items()}  #转为普通dict
    # In course-selection examples, these dependencies may not exist.
        print(f'transitive_partial_dependencies:\n {transitive_partial_dependencies}')

    # 12. Decompose entity tables (algorithmic implementation).
        new_entity_add_relation_attributes_all = {}
        new_entity_add_relation_keys_and_attribute_map = {}
        for entity_name in transitive_partial_dependencies:
            if len(transitive_partial_dependencies[entity_name]['分解关系']) == 1:  # No decomposition needed.
                new_entity_add_relation_attributes_all[entity_name] = entity_add_relation_attributes_all[entity_name]
                new_entity_add_relation_keys_and_attribute_map[entity_name] = entity_add_relation_keys_and_attribute_map[entity_name]
            else:  # Decomposition required.
                for sub_table_attributes in transitive_partial_dependencies[entity_name]['分解关系']:
                    candidate_keys = get_attribute_keys_by_arm_strong_each(sub_table_attributes,
                                                                           entity_add_relation_functional_dependency_json['dependencies'][entity_name])
                    new_entity_name = ''
                    for candidate_key in candidate_keys:
                        new_entity_name = ''.join(candidate_key)   # TODO: if new_entity_name already exists, handle collisions.
                    # if new_entity_name in new_entity_add_relation_attributes_all:
                    #     new_entity_name +=
                    new_entity_add_relation_attributes_all[new_entity_name] = sub_table_attributes
                    new_entity_add_relation_keys_and_attribute_map[new_entity_name] = candidate_keys

        print(f'new_entity_add_relation_attributes_all:\n {new_entity_add_relation_attributes_all}')
        print(f'new_entity_add_relation_keys_and_attribute_map:\n {new_entity_add_relation_keys_and_attribute_map}')

        entity_schemas = predict_entity_schema(new_entity_add_relation_attributes_all,
                                               new_entity_add_relation_keys_and_attribute_map)



        relation_all_attribute = {}
        for relation_item in multi_relation:
            for relation_name in relation_item:
                relation_all_attribute[relation_name] = relation_item[relation_name]['属性']
        print(f'relation_all_attribute:\n {relation_all_attribute}')

        relation_functional_dependency_analyzer, prompt_get_relation_functional_dependency_analyses = get_relation_functional_dependency_analysis_prompt(
            question_analyses, relation_all_attribute)

        relation_functional_dependency_analyses = handler.get_output_multiagent(
                                                            user_input=prompt_get_relation_functional_dependency_analyses,
                                                            temperature=0, max_tokens=800,
                                                            system_role=relation_functional_dependency_analyzer)
        relation_functional_dependency_analyses_result = clear_analyses(relation_functional_dependency_analyses)

        print(f'relation_functional_dependency_analyses:\n {relation_functional_dependency_analyses} \n')
        print(f'relation_functional_dependency_analyses_result:\n {relation_functional_dependency_analyses_result}')

   
        relation_functional_dependency_json = extract_functional_dependency_from_text(
                                                         relation_functional_dependency_analyses_result)
        print(f'relation_functional_dependency_json:\n {relation_functional_dependency_json}')
        relation_attributes_all, relation_keys_and_attribute_map = get_attribute_keys_by_arm_strong(relation_functional_dependency_json)
        print(f'relation_attributes_all:\n {relation_attributes_all}')
        print(f'relation_keys_and_attribute_map:\n {relation_keys_and_attribute_map}')



        multi_relation_schemas = predict_relation_schema(multi_relation, relation_keys_and_attribute_map)
        print(f'multi_relation_schemas:\n {multi_relation_schemas}')

        schema_predicted = {**entity_schemas, **multi_relation_schemas}
        print(f'schema_predicted:\n {schema_predicted}')



        data_info = {
            'question': question,
            'question_analyses': question_analyses,
            'entity_analyses': entity_analyses_result,
            'entity_attribute_analyses': entity_attribute_analyses_result,
            'relation_analyses': relation_analyses_result,
            'relation_attribute_analyses': relation_attribute_analyses_result,
            'relation_type_analyses': relation_type_analyses_result,
            'entity_functional_dependency_analyses': entity_functional_dependency_analyses_result,
            'relation_functional_dependency_analyses': relation_functional_dependency_analyses_result,
            'entity_functional_dependency_json':entity_functional_dependency_json,
            'entity_attributes_all':entity_attributes_all,
            'relation_functional_dependency_analyses_result': relation_functional_dependency_analyses_result,
            'relation_functional_dependency_json':relation_functional_dependency_json,
            'relation_attributes_all':relation_attributes_all,
            'multi_relation_schemas':multi_relation_schemas,
            'pred_schema': schema_predicted,
        }

        # 打印history
        if args.log_history:
            print('*********************** History *********************')
            print(data_info)



    elif args.method == "domain_analyse":
     

        do_requirement_analyse = False  

        if do_requirement_analyse:

            question_analyzer, prompt_get_question_analysis = get_question_analysis_prompt(question)

            question_analyses = handler.get_output_multiagent(user_input=prompt_get_question_analysis,
                                                              temperature=0, max_tokens=3000,
                                                              system_role=question_analyzer)
        else:
            question_analyses = question

      
        entity_analyzer, prompt_get_entity_analyses = get_entity_all_analysis_prompt(question_analyses)  # english
       
        entity_analyses, entity_analyses_result = handler.get_output_multiagent(user_input=prompt_get_entity_analyses,
                                                        temperature=0, max_tokens=800,
                                                        system_role=entity_analyzer)
        print(f'entity_analyses_result:\n {entity_analyses_result}')

        revision_history = {}
        
        if 'entity_verification' in args.verification:  

            new_entity_json_result = {}
            for entity_name in entity_analyses_result:
                quality_controller, quality_control_prompt = get_verification_entity_prompt(question_analyses, entity_analyses,
                                                                                  entity_name)
                quality_controller_opi, _ = handler.get_output_multiagent(user_input=quality_control_prompt,
                                                                       temperature=0, max_tokens=800,
                                                                       system_role=quality_controller)
                quality_controller_opinion = cleansing_voting(quality_controller_opi)  # "yes" / "no"

                print(f'quality_controller_opinion: {quality_controller_opinion}')
                revision_history[entity_name] = quality_controller_opinion

                if quality_controller_opinion == 'yes':
                    new_entity_json_result[entity_name] = entity_analyses_result[entity_name]

            entity_analyses_result = new_entity_json_result


        print(f'revision_history: \n {revision_history}')
        print(f'entity_analyses_result:\n {entity_analyses_result}')


        relation_analyzer, prompt_get_relation_analyses = get_relation_all_analysis_prompt(question_analyses,
                                                                                       entity_analyses_result)
        relation_analyses, relation_analyses_result = handler.get_output_multiagent(user_input=prompt_get_relation_analyses,
                                                          temperature=0, max_tokens=800,
                                                          system_role=relation_analyzer)

        print(f'relation_analyses_result:\n {relation_analyses_result}')



        entity_functional_dependency_analyzer, prompt_get_entity_functional_dependency_analyses = get_entity_functional_dependency_analysis_prompt(
            question_analyses, entity_analyses_result)
        entity_functional_dependency_analyses, entity_functional_dependency_analyses_result = handler.get_output_multiagent(
            user_input=prompt_get_entity_functional_dependency_analyses,
            temperature=0, max_tokens=800,
            system_role=entity_functional_dependency_analyzer)

        print(f'entity_functional_dependency_analyses_result:\n {entity_functional_dependency_analyses_result}')

        revision_entity_denpendency_history = defaultdict(list)
        if 'entity_denpendency_verification' in args.verification:  

            new_entity_functional_dependency_analyses_result = {}
            for entity_name, entity_value in entity_functional_dependency_analyses_result.items():
                entity_dependency = {entity_name:entity_value}
                ENTITY_REVISE_FLAG = True
                ENTITY_REVISE_NUM = 3
                tried_num = 0
                while tried_num<ENTITY_REVISE_NUM and ENTITY_REVISE_FLAG:
                    tried_num += 1

                    quality_controller, quality_control_prompt = get_dependency_consensus_prompt(question_analyses,
                                                                {entity_name:entity_analyses_result[entity_name]},
                                                    entity_dependency)
                    quality_controller_opi, _ = handler.get_output_multiagent(user_input=quality_control_prompt,
                                                                           temperature=0, max_tokens=800,
                                                                           system_role=quality_controller)
                    quality_controller_opinion = cleansing_voting(quality_controller_opi)  # "yes" / "no"

                    print(f'quality_controller_opinion: {quality_controller_opinion}')
                    revision_entity_denpendency_history[entity_name].append(quality_controller_opinion)

                    if quality_controller_opinion == 'yes':
                        new_entity_functional_dependency_analyses_result[entity_name] = entity_value
                        ENTITY_REVISE_FLAG = False
                    else: 
                        revise_control_prompt = get_dependency_consensus_opinion_prompt(question_analyses,
                                                            {entity_name: entity_analyses_result[entity_name]},
                                                                            entity_dependency,
                                                                             quality_controller_opi )
                        (revise_entity_functional_dependency_analyses,
                         revise_entity_functional_dependency_analyses_result) = handler.get_output_multiagent(user_input=revise_control_prompt,
                                                                              temperature=0, max_tokens=800,
                                                                              system_role=quality_controller)
                        entity_dependency = revise_entity_functional_dependency_analyses_result

                if tried_num==ENTITY_REVISE_NUM:
                    new_entity_functional_dependency_analyses_result[entity_name] = entity_dependency[entity_name]
            entity_functional_dependency_analyses_result = new_entity_functional_dependency_analyses_result
            print(f'revision_entity_denpendency_history:\n {revision_entity_denpendency_history}')

        print(f'new_entity_functional_dependency_analyses_result:\n {entity_functional_dependency_analyses_result}')

        entity_attributes_all, entity_keys_and_attribute_map = get_attribute_keys_by_arm_strong(
            entity_functional_dependency_analyses_result)
        print(f'entity_attributes_all:\n {entity_attributes_all}')
        print(f'entity_keys_and_attribute_map:\n {entity_keys_and_attribute_map}')

        multi_relation, entity_attributes_all_with_foreign_key = trans_relation_to_schema_for_domain(relation_analyses_result, entity_attributes_all,
                                                  entity_keys_and_attribute_map)
        print(f'entity_add_relation_attributes_all:\n {entity_attributes_all}')
        print(f'entity_attributes_all_with_foreign_key:\n {entity_attributes_all_with_foreign_key}')
        print(f'multi_relation:\n {multi_relation}')

        entity_functional_dependency_analyzer, prompt_get_entity_functional_dependency_analyses = get_entity_functional_dependency_analysis_prompt(
            question_analyses, json.dumps(entity_attributes_all, ensure_ascii=False))
        entity_add_relation_functional_dependency_analyses, entity_add_relation_functional_dependency_json = handler.get_output_multiagent(
            user_input=prompt_get_entity_functional_dependency_analyses,
            temperature=0, max_tokens=800,
            system_role=entity_functional_dependency_analyzer)

        print(f'entity_add_relation_functional_dependency_json:\n {entity_add_relation_functional_dependency_json}')

        entity_add_relation_attributes_all, entity_add_relation_keys_and_attribute_map = get_attribute_keys_by_arm_strong(
            entity_add_relation_functional_dependency_json)

        print(f'entity_add_relation_attributes_all:\n {entity_add_relation_attributes_all}')
        print(f'entity_add_relation_keys_and_attribute_map:\n {entity_add_relation_keys_and_attribute_map}')


        transitive_partial_dependencies = decompose_to_3NF(
            entity_add_relation_functional_dependency_json,
            entity_add_relation_keys_and_attribute_map
        )
        transitive_partial_dependencies = {key: value for key, value in
                                           transitive_partial_dependencies.items()}  

        print(f'transitive_partial_dependencies:\n {transitive_partial_dependencies}')

        new_entity_add_relation_attributes_all = defaultdict(dict)
        new_entity_add_relation_keys_and_attribute_map = {}
        for entity_name in transitive_partial_dependencies:
            if len(transitive_partial_dependencies[entity_name]['Decomposition relationship']) == 1: 
                new_entity_add_relation_attributes_all[entity_name]['property'] = entity_add_relation_attributes_all[entity_name]
                new_entity_add_relation_keys_and_attribute_map[entity_name] = entity_add_relation_keys_and_attribute_map[entity_name]
            else:
                for sub_table_attributes in transitive_partial_dependencies[entity_name]['Decomposition relationship']:
                    candidate_keys = get_attribute_keys_by_arm_strong_each(sub_table_attributes,
                                                                           entity_add_relation_functional_dependency_json[entity_name])
                    new_entity_name = ''
                    for candidate_key in candidate_keys:
                        new_entity_name = ''.join(candidate_key)
                    new_entity_add_relation_attributes_all[new_entity_name]['property'] = sub_table_attributes
                    new_entity_add_relation_attributes_all[new_entity_name]['foreign_key'] = {}


                    foreign_keys = list(entity_attributes_all_with_foreign_key[entity_name]['foreign_key'].keys())
                    common_keys = get_common_element_list(foreign_keys, sub_table_attributes)

                    for key in common_keys:
                        new_entity_add_relation_attributes_all[new_entity_name]['foreign_key'][key] = entity_attributes_all_with_foreign_key[entity_name]['外键'][key]
                    new_entity_add_relation_keys_and_attribute_map[new_entity_name] = candidate_keys

        print(f'new_entity_add_relation_attributes_all:\n {new_entity_add_relation_attributes_all}')
        print(f'new_entity_add_relation_keys_and_attribute_map:\n {new_entity_add_relation_keys_and_attribute_map}')

        entity_schemas = predict_entity_schema(new_entity_add_relation_attributes_all,
                                               new_entity_add_relation_keys_and_attribute_map)
        print(f'entity_schemas:\n {entity_schemas}')


        relation_all_attribute = {}
        for relation_name in multi_relation:
            relation_all_attribute[relation_name] = multi_relation[relation_name]['property']
        print(f'relation_all_attribute:\n {relation_all_attribute}')

        if relation_all_attribute:
    
            relation_functional_dependency_analyzer, prompt_get_relation_functional_dependency_analyses = get_relation_functional_dependency_analysis_prompt(
                question_analyses, relation_all_attribute)
            relation_functional_dependency_analyses, relation_functional_dependency_analyses_result = handler.get_output_multiagent(
                user_input=prompt_get_relation_functional_dependency_analyses,
                temperature=0, max_tokens=800,
                system_role=relation_functional_dependency_analyzer)
            # print(f'relation_functional_dependency_analyses:\n {relation_functional_dependency_analyses} \n')
            print(f'relation_functional_dependency_analyses_result:\n {relation_functional_dependency_analyses_result}')


            revision_relation_denpendency_history = defaultdict(list)
            if 'relation_denpendency_verification' in args.verification: 

                new_relation_functional_dependency_analyses_result = {}
                for relation_name, relation_value in relation_functional_dependency_analyses_result.items():
                    relation_dependency = {relation_name: relation_value}
                    RELATION_REVISE_FLAG = True
                    RELATION_REVISE_NUM = 3
                    tried_num = 0
                    while tried_num < RELATION_REVISE_NUM and RELATION_REVISE_FLAG:
                        tried_num += 1

                        quality_controller, quality_control_prompt = get_relation_dependency_consensus_prompt(question_analyses,
                                                                {relation_name:relation_all_attribute[relation_name]},
                                                                               relation_dependency)
                        quality_controller_opi, _ = handler.get_output_multiagent(user_input=quality_control_prompt,
                                                                                  temperature=0, max_tokens=800,
                                                                                  system_role=quality_controller)
                        quality_controller_opinion = cleansing_voting(quality_controller_opi)  # "yes" / "no"

                        print(f'quality_controller_opi: \n {quality_controller_opi}' )
                        print(f'quality_controller_opinion: {quality_controller_opinion}')
                        revision_relation_denpendency_history[relation_name].append(quality_controller_opinion)

                        if quality_controller_opinion == 'yes':
                            new_relation_functional_dependency_analyses_result[relation_name] = relation_value
                            RELATION_REVISE_FLAG = False
                        else:  
                            revise_control_prompt = get_relation_dependency_consensus_opinion_prompt(question_analyses,
                                                        {relation_name:relation_all_attribute[relation_name]},
                                                                                            relation_dependency,
                                                                                            quality_controller_opi)
                            (revise_relation_functional_dependency_analyses,
                             revise_relation_functional_dependency_analyses_result) = handler.get_output_multiagent(
                                user_input=revise_control_prompt,
                                temperature=0, max_tokens=800,
                                system_role=quality_controller)
                            print(f'revise_relation_functional_dependency_analyses: \n revise_relation_functional_dependency_analyses')
                            print(f'revise_relation_functional_dependency_analyses_result: \n revise_relation_functional_dependency_analyses_result')
                            relation_dependency = revise_relation_functional_dependency_analyses_result

                    if tried_num == RELATION_REVISE_NUM:
                        new_relation_functional_dependency_analyses_result[relation_name] = relation_dependency[relation_name]
                relation_functional_dependency_analyses_result = new_relation_functional_dependency_analyses_result
                print(f'revision_relation_denpendency_history:\n {revision_relation_denpendency_history}')


            print(f'new_relation_functional_dependency_analyses_result:\n {relation_functional_dependency_analyses_result}')


           
            relation_attributes_all, relation_keys_and_attribute_map = get_attribute_keys_by_arm_strong(
                relation_functional_dependency_analyses_result)
            print(f'relation_attributes_all:\n {relation_attributes_all}')
            print(f'relation_keys_and_attribute_map:\n {relation_keys_and_attribute_map}')

            
            new_multi_relation = {}
            new_relation_keys_and_attribute_map = {}
            for relation_name in relation_keys_and_attribute_map:
                if len(relation_keys_and_attribute_map[relation_name]) == 0: 
                    relation_item = {}
                    for item in relation_analyses_result:
                        if list(item.keys())[0] == relation_name:
                            relation_item = item
                    revised_relation_analyzer, prompt_get_relation_revised_analyses = get_relation_revised_analysis_prompt(
                        question_analyses, relation_item, entity_schemas)
                    revised_relation_analyses, revised_relation_analyses_result = handler.get_output_multiagent(
                        user_input=prompt_get_relation_revised_analyses,
                        temperature=0, max_tokens=800,
                        system_role=revised_relation_analyzer)
                    print(f'revised_relation_analyses_result:\n {revised_relation_analyses_result}')

                    for key in revised_relation_analyses_result:
                        new_multi_relation[key] = revised_relation_analyses_result[key]
                        new_relation_keys_and_attribute_map[key] = [set(revised_relation_analyses_result[key]['主键'])]
                else:
                    new_multi_relation[relation_name] = multi_relation[relation_name]
                    new_relation_keys_and_attribute_map[relation_name] = relation_keys_and_attribute_map[relation_name]

            print(f'new_multi_relation:\n {new_multi_relation}')
            print(f'new_relation_keys_and_attribute_map:\n {new_relation_keys_and_attribute_map}')

        
            multi_relation_schemas = predict_relation_schema(new_multi_relation, new_relation_keys_and_attribute_map)
            print(f'multi_relation_schemas:\n {multi_relation_schemas}')

            
            schema_predicted = {**entity_schemas, **multi_relation_schemas}
        else:
            schema_predicted = entity_schemas

        print(f'schema_predicted:\n {schema_predicted}')

        data_info = {
            'question': question,
            'question_analyses': question_analyses,
            'entity_analyses': entity_analyses_result,
            'revision_history':revision_history,
            'relation_analyses': relation_analyses_result,
            'entity_functional_dependency_analyses': entity_functional_dependency_analyses_result,
            'entity_attributes_all': entity_attributes_all,
            # 'relation_functional_dependency_analyses_result': relation_functional_dependency_analyses_result,
            # 'multi_relation_schemas': multi_relation_schemas,
            'pred_schema': schema_predicted,
        }


        if args.log_history:
            print('*********************** History *********************')
            print(data_info)


    elif args.method == "pseudo_code_analyse":
        schema_analyzer, prompt_get_schema_analyses = get_pseudo_code_prompt(question, './pseudo_code.md')

        print(f'prompt_get_schema_analyses: \n{prompt_get_schema_analyses}')
        relation_functional_dependency_analyses, output_json = handler.get_output_multiagent(
            user_input=schema_analyzer,
            temperature=0, max_tokens=800,
            system_role=prompt_get_schema_analyses)

        # print('**********************************')
        # print(relation_functional_dependency_analyses)

        data_info = {
            'question': question,
            'pred_schema': output_json,
        }

    return data_info






