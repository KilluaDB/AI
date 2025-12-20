
def get_question_analysis_prompt(question):
    question_analyzer = f"You are a requirements analysis expert in the database field. You will carefully examine and analyze user requirements based on your experience and relevant theories."
    prompt_get_question_analysis = f"Please carefully read the requirements in this problem: '''{question}''' Use your professional knowledge to analyze this requirement. Do not output any irrelevant content, and do not expand or reduce the requirements."

    return question_analyzer, prompt_get_question_analysis



def get_entity_analysis_prompt(question_analysis):
    subtask_analyzer = f"You are an expert in building database conceptual models. You are particularly good at identifying database entities from requirements analysis."
    prompt_get_requirement_analyses = f"We have obtained analysis from experts in the field of requirements analysis. \n"
    prompt_get_requirement_analyses += f"The analysis results of the requirements analysis expert are: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"You need to deeply understand the content of the requirements analysis and obtain the database entities in this requirement. Note that relationship entities or association entities are not database entities."
    prompt_get_requirement_analyses += f"Your output format should be '''After thinking step by step, [thinking content], I can finally conclude that the database entities in Python list format are: [Entity name 1, Entity name 2]'''. No need to explain each entity in detail. No need to display brackets."

    return subtask_analyzer, prompt_get_requirement_analyses


def get_entity_all_analysis_prompt(question_analysis):
    data_format = '''
                  {'Database entity 1':['Entity attribute 1', 'Entity attribute 2'],
                   'Database entity 2':['Entity attribute 3', 'Entity attribute 4']}
                  '''
    subtask_analyzer = f"You are an expert in building database conceptual models. You are particularly good at identifying database entities and entity attributes from requirements analysis."
    prompt_get_requirement_analyses = f"We have obtained analysis from experts in the field of requirements analysis. \n"
    prompt_get_requirement_analyses += f"The analysis results of the requirements analysis expert are: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"Review the analysis of the requirement description by the requirements analysis expert. You need to deeply understand the content of the requirements analysis and obtain the database entities and entity attributes in this requirement. You need to set the ID attribute."
    prompt_get_requirement_analyses += f"Your output format should be '''After thinking step by step, '''thinking content''', I can finally conclude that the JSON format of database entities and their attributes is: {data_format}''' Do not generate additional content."

    return subtask_analyzer, prompt_get_requirement_analyses


def get_entity_all_analysis_prompt_v1(question_analysis):
    data_format = '''
                  {'Database entity 1':['Entity attribute 1', 'Entity attribute 2'],
                   'Database entity 2':['Entity attribute 3', 'Entity attribute 4']}
                  '''
    subtask_analyzer = f"You are an expert in building database conceptual models. You are particularly good at identifying database entities and entity attributes from requirements analysis."
    prompt_get_requirement_analyses = f"We have obtained analysis from experts in the field of requirements analysis. \n"
    prompt_get_requirement_analyses += f"The analysis results of the requirements analysis expert are: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"Review the analysis of the requirement description by the requirements analysis expert. You need to deeply understand the content of the requirements analysis and obtain the database entities and entity attributes in this requirement. You need to set the ID attribute."
    prompt_get_requirement_analyses += f"Your output format should be '''After thinking step by step, '''thinking content''', I can finally conclude that the JSON format of database entities and their attributes is: {data_format}''' Do not generate additional content."

    return subtask_analyzer, prompt_get_requirement_analyses

def get_entity_all_analysis_english_prompt_v1(question_analysis):
    data_format = '''
                    {'Database entity 1':['Entity attribute 1', 'Entity attribute 2'],
                    'Database entity 2':['Entity attribute 3', 'Entity attribute 4']}
                  '''
    subtask_analyzer = f"You are an expert in building database conceptual models. You are particularly good at identifying database entities and entity attributes from requirement analysis."
    prompt_get_requirement_analyses = f"We have obtained analysis from experts in the field of requirement analysis. \n"
    prompt_get_requirement_analyses += f"The analysis results of experts in the field of requirement analysis are: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"Review the analysis of the requirement description by the requirement analysis expert. You need to deeply understand the content of the requirement analysis and obtain the database entities and entity attributes in this requirement. You need to set the number (ID) attribute."
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step,... I can finally conclude that the JSON format of the database entity and its attributes is: {data_format}''' Do not generate additional content."
    return subtask_analyzer, prompt_get_requirement_analyses

def get_entity_all_analysis_prompt(question_analysis):
    data_format = '''
                  {'Database entity 1':['Entity attribute 1', 'Entity attribute 2'],
                   'Database entity 2':['Entity attribute 3', 'Entity attribute 4']}
                  '''
    subtask_analyzer = f"You are an expert in building entity-relationship database models. You are particularly good at identifying database entity sets and entity set attributes from requirements analysis."
    prompt_get_requirement_analyses = f"The entity-relationship data model is a high-level data model。它将被称作entity's基本对象和这些对象之间's联系区分开来。This model is typically used as the first step in database schema design。 \n"
    prompt_get_requirement_analyses += (f"我向你解释数据库inentity集和entity集Attributes's定义。一个entityis现实世界in可区别于所有其他对象's一个“事物”or“对象”。例如，大学in's每个人都is一个entity。"
                                        f"Each entity has a set of properties, and the values of some property sets must uniquely identify an entity. For example, a person may have a person ID property whose value uniquely identifies that person."
                                        f"Thus, a person ID value of 677-89-9011 would uniquely identify a specific person in the university. Similarly, courses can also be considered entities,"
                                        f"and the course number uniquely identifies a particular course entity in the university. Entities can be tangible, such as a person or a book; entities can also be abstract,"
                                        f"such as a course, a course section, or a flight reservation.\n")
    prompt_get_requirement_analyses += (f"An entity set is a collection of entities of the same type that share the same properties or attributes. For example, the collection of all instructors at a given university"
                                        f"can be defined as the instructor entity set. Similarly, the student entity set can represent the collection of all students in the university.")
    prompt_get_requirement_analyses += (f"An entity is represented by a set of attributes. Attributes are descriptive properties possessed by each member of an entity set. Designing an attribute for an entity set indicates that the database stores"
                                        f"similar information about each entity in the entity set, but each entity may have its own value for each attribute. The instructor entity set may have attributes such as instructor ID, name, department, and salary.\n")
    prompt_get_requirement_analyses += f"Now we have obtained analysis results from experts in the requirements analysis field: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += f"You need to deeply understand the content of the requirements analysis以andentity集和entityAttributes's定义，and obtain the database entities in this requirement集andentity集Attributes。You need to set an ID attribute for each entity set。Do not generate additional content。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，**thinking content...** In the end, I can present the entity sets and their attributes in the database in JSON format as follows：{data_format}。''' "

    return subtask_analyzer, prompt_get_requirement_analyses




def get_entity_all_analysis_english_prompt(question_analysis):
    data_format = '''
                    {'Database entity 1':['Entity attribute 1', 'Entity attribute 2'],
                    'Database entity 2':['Entity attribute 3', 'Entity attribute 4']}
                  '''
    subtask_analyzer = (f"You are an expert in building database entity-relationship database models. "
                        f"You are particularly good at identifying database entity sets and entity set attributes from requirements analysis.")
    prompt_get_requirement_analyses = (f"The entity-relationship (E-R) model is a high-level data model. Instead of representing all data in tables, "
                                       f"it distinguishes between basic called entities, and relationships among these objects. "
                                       f"It is often used as a first step in database-schema design.\n")
    prompt_get_requirement_analyses += (f"I will explain to you the definitions of entity sets and entity set attributes in the database. \n"
                                        f"An entity is a “thing” or “object” in the real world that is distinguishable from all other objects. "
                                        f"For example, each person in a university is an entity. An entity has a set of properties, and the "
                                        f"values for some set of properties may uniquely identify an entity. For instance, a person may "
                                        f"have a person id property whose value uniquely identifies that person. Thus, the value 677-89-9011"
                                        f" for person id would uniquely identify one particular person in the university. Similarly, courses"
                                        f" can be thought of as entities, and course id uniquely identifies a course entity in the university. "
                                        f"An entity may be concrete, such as a person or a book, or it may be abstract, such as a course, "
                                        f"a course offering, or a flight reservation. ")
    prompt_get_requirement_analyses += (f"An entity set is a set of entities of the same type that share the same properties,"
                                        f"or attributes. The set of all people who are instructors at a given university, for"
                                        f"example, can be defined as the entity set instructor. Similarly, the entity set student"
                                        f"might represent the set of all students in the university")
    prompt_get_requirement_analyses += (f"An entity is represented by a set of attributes. Attributes are descriptive"
                                        f"properties possessed by each member of an entity set. The designation of an"
                                        f"attribute for an entity set expresses that the database stores similar information"
                                        f"concerning each entity in the entity set; however, each entity may have its own"
                                        f"value for each attribute. Possible attributes of the instructor entity set are ID, name,"
                                        f"dept name, and salary.")
    prompt_get_requirement_analyses += f"Now we have obtained the analysis results from experts in the field of requirement analysis: '''{question_analysis}''' \n"
    prompt_get_requirement_analyses += (f"You need to deeply understand the content of requirement analysis and the definition of entity sets and entity attributes, "
                                        f"and get the database entity sets and entity set attributes in this requirement. You need to set the number (ID) attribute for "
                                        f"each entity set. Do not generate additional content.")
    prompt_get_requirement_analyses += (f"Your output format should be'''After thinking step by step, **Thinking content...** "
                                        f"In the end, I can present the entity set and its attributes in the database in JSON format as follows: {data_format}.''' ")


    return subtask_analyzer, prompt_get_requirement_analyses



def get_verification_entity_prompt(question_analysis, entity_analyses, entity_name):
    subtask_analyzer = f"You are an expert in building database conceptual models"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analysis}''' \n The analysis content of the database entity recognition expert is：'''{entity_analyses}''' \n"
    prompt_get_requirement_analyses += f"The database entity recognition expert believes that'''{entity_name}'''is a database entity \n"
    prompt_get_requirement_analyses += f"As an expert in building database conceptual models, please carefully read the requirements analysis results and entity recognition results, and decide whether your opinion is consistent with that of the entity recognition expert。"
    prompt_get_requirement_analyses += f"These are the rules you must follow when making judgments：1. A database entity can correspond to a table in the database。 2. 【两】个entity之间产生'sRelationship entities or association entities are NOT database entities。3. Results that can be calculated do not need entities and entity tables"
    prompt_get_requirement_analyses += f"Your output format should be'''After carefully reading the requirements analysis results and entity recognition results，[analysis content]，my answer is：[yes or no]"

    return subtask_analyzer, prompt_get_requirement_analyses


def get_consensus_prompt(question_analysis, entity_analysis):
    subtask_analyzer = f"You are an expert in building database conceptual models"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analysis}''' We have obtained analysis from the database entity recognition expert。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity recognition expert is: '''{entity_analysis}''' \n"
    prompt_get_requirement_analyses += f"As an expert in building database conceptual models, please carefully read the requirements analysis results and entity recognition results, and decide whether your opinion is consistent with that of the entity recognition expert。"
    prompt_get_requirement_analyses += f"These are the rules you must follow when making judgments：1. Relationship entities or association entities are NOT database entities。2. Database entities generally do NOT contain foreign keys from other entities。"
    prompt_get_requirement_analyses += f"Your output format should be'''After carefully reading the requirements analysis results and entity recognition results，[analysis content]，my answer is：[yes or no]"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_consensus_opinion_prompt(question_analysis, entity_analyses, quality_controller_opi):
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analysis}''' We have obtained analysis from the database entity recognition expert。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity recognition expert is: '''{entity_analyses}''' \n"
    prompt_get_requirement_analyses += f"In addition, we have also obtained modification suggestions from another expert in building database conceptual models for this analysis result：'''{quality_controller_opi}''' \n Ensure that the analysis results of the entity recognition expert are modified according to the modification suggestions, including adding or deleting entities。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，[thinking content]，I can finally conclude thatthe modified database entities and their attributes are：[{{database entity1:entityAttributes1、entityAttributes2}}]'''。Display each entity on a separate line，No need to display brackets。Output in Chinese。"

    return prompt_get_requirement_analyses




def get_entity_attribute_analysis_prompt(question_analysis, entity_analysis):
    subtask_analyzer = f"You are an expert in building database conceptual models，You are particularly good at identifying database entity attributes from requirements analysis。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analysis}''' We have obtained analysis from the database entity recognition expert。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity recognition expert is: '''{entity_analysis}''' \n"
    prompt_get_requirement_analyses += f"Review the requirement description analysis by the requirements analysis expert，as well as the analysis of entities in this requirement by the database entity recognition expert，You need to deeply understand the content of the requirements analysis，精准and obtain the database entities in this requirementAttributes。"
    prompt_get_requirement_analyses += f"It is particularly important to note that，database entityAttributes在非必要scenario下not单独设置编号(ID)Attributes。只需要recognitionAttributes，not需要recognitionPrimary key。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，[thinking content]，I can finally conclude thatthe database entity attributes are：[database entity:其对应'sentityAttributes1、entityAttributes2]'''。Display each entity on a separate line，No need to display brackets。"

    return subtask_analyzer, prompt_get_requirement_analyses



# TODO This definitely needs to be modified to ask questions for each entity
def get_relation_analysis_prompt(question_analyses, entity_analysis):
    subtask_analyzer = f"You are an expert in building database conceptual models，You are particularly good at identifying relationships between database entities。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' We have obtained analysis from the database entity recognition expert。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity recognition expert is: '''{entity_analysis}''' \n"
    prompt_get_requirement_analyses += f"Review the requirement description analysis by the requirements analysis expert，as well as the analysis of entities in this requirement by the database entity recognition expert，You need to deeply understand the content of the requirements analysis，and obtain the relationships between database entities in this requirement。"
    prompt_get_requirement_analyses += f"It is particularly important to note that，You only need to identify entity pairs with relationships and their corresponding relationship names, without identifying relationship cardinality。Relationship names cannot be the same as entity names。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，'''thinking content'''，I can finally conclude thatthe database entity relationships are：[Relationship name1:Entity name1、Entity name2]'''。Separate each relationship with ','，No need to display brackets。"

    return subtask_analyzer, prompt_get_requirement_analyses


def get_relation_all_analysis_prompt(question_analyses, entity_analysis):
    subtask_analyzer = f"You are an expert in building database conceptual models，You are particularly good at identifying relationships between database entities以andrelationship'scardinality type和relationship'sAttributes。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' We have obtained analysis from the database entity recognition expert。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity recognition expert is: '''{entity_analysis}''' \n"
    prompt_get_requirement_analyses += f"You need to deeply understand the content of the requirements analysis，judgment'''{list(entity_analysis.keys())}'''in两两entity之间is否具有relationship。如果有relationship，generateRelationship name、relationship'scardinality type和属于relationship'sAttributes。"
    prompt_get_requirement_analyses += f"你must做到以下几点：1. Entity namemust包含在entityrecognitionexpert's'sanalysisresultin。2. Relationship names cannot be the same as entity names。3. relationship'scardinality type包括one-to-one，one-to-many，many-to-one还ismany-to-many。4. 如果没有值则填空字符串"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，'''thinking content'''，I can finally conclude thatthe database entity relationships in JSON format are：[{{'某Relationship name':['Entity name1','Entity name2'], 'Cardinality':'one-to-one', 'relationshipAttributes':['Attributes1','Attributes2']}}]'''"

    return subtask_analyzer, prompt_get_requirement_analyses



# There is an issue here: we also need to make entity cardinality correspond to entities, 1:n
def get_relation_analysis_type_prompt(question_analyses, relation_analyses):
    subtask_analyzer = f"You are an expert in building database conceptual models，You are particularly good at identifying relationship cardinality types, such as one-to-one, one-to-many, many-to-one, or many-to-many。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了来自database entity间relationshiprecognitionexpert'sanalysis。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity relationship recognition expert is: '''{relation_analyses}''' \n"
    prompt_get_requirement_analyses += f"Review the requirement description analysis by the requirements analysis expert，以anddatabase entity间relationshiprecognitionexpert对此Requirementinentityrelationship'sanalysis，recognitionrelationshipinentity之间'scardinality type，并将此cardinality type作for该relationship'scardinality type。"
    prompt_get_requirement_analyses += f"It is particularly important to note that，database entity间relationshiprecognitionexpert给出'sis形如'''[Relationship name1:Entity name1、Entity name2]''''srelationshipdescription。每个relationship只对应一种cardinality type。not要更改database entity间relationshiprecognitionexpert命名'sRelationship name。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，[thinking content]，\n I can finally conclude thatthe cardinality types between database entities are：[Relationship name1:relationshipcardinality type1]'''。Separate each relationship with ','，No need to display brackets。"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_relation_analysis_attribute_prompt(question_analyses, entity_attribute_analyses, relation_analyses):
    subtask_analyzer = f"You are an expert in building database conceptual models，You are particularly good at identifying relationship attributes。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了来自database entityAttributesrecognitionexpert和database entity间relationshiprecognitionexpert'sanalysis。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity attribute recognition expert is: '''{entity_attribute_analyses}''' \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity relationship recognition expert is: '''{relation_analyses}''' \n"
    prompt_get_requirement_analyses += f"Review the requirement description analysis by the requirements analysis expert，以anddatabase entity间relationshiprecognitionexpert对此Requirementinentityrelationship'sanalysis，You need to deeply understand the content of the requirements analysis，得到符合全局design'sresult。"
    prompt_get_requirement_analyses += f"It is particularly important to note that，relationshipAttributesis只属于relationship'sAttributes，它not属于任何entity。只需要recognitionAttributes，not需要recognitionPrimary key。Relationship name应该withdatabase entity间relationshiprecognitionexpert'sdescription一致。你's所有thinking content都应该在[thinking content]in体现，而not应该在finally结论in体现。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，[thinking content]，\n I can finally conclude thatthe database relationship attributes are：[Relationship name1:relationship'sAttributes1、relationship'sAttributes2]'''。Display each relationship on a separate line，No need to display brackets。当没有relationshipAttributes时只需outputRelationship name，not需要outputrelationshipAttributes。"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_entity_functional_dependency_analysis_prompt(question_analyses, entity_attribute_analyses):
    output_format = '''
                    {
                    "Entity name1": {"Attributes1": ["Attributes2"], "Attributes1, Attributes2": ["Attributes4"]}, 
                    "Entity name2": {"Attributes1": ["Attributes2"], "Attributes1": ["Attributes3"]}
                    }
                    '''
    subtask_analyzer = f"You are an expert in building database conceptual models，You are particularly good at identifying functional dependencies between database entity attributes。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了来自database entityAttributesrecognitionexpert'sanalysis。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database entity attribute recognition expert is: '''{entity_attribute_analyses}''' \n"
    prompt_get_requirement_analyses += f"Review the requirement description analysis by the requirements analysis expert，以anddatabase entityAttributesrecognitionexpert'sanalysis，You need to deeply understand the content of the requirements analysis，得到database entityAttributes之间'sfunctional dependencyrelationship。"
    prompt_get_requirement_analyses += f"It is particularly important to note that，functional dependency只存在于每个entity内部'sAttributes之间。Do not generate additional content。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，'''thinking content'''，\n I can finally conclude thatthe functional dependencies between database entity attributes are：{output_format}'''"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_relation_functional_dependency_analysis_prompt(question_analyses, relation_attribute_analyses):
    output_format = '''
                    {
                    "Relationship name1": {"Attributes1": ["Attributes2"], "Attributes1, Attributes2": ["Attributes4"]}, 
                    "Relationship name2": {"Attributes1": ["Attributes2"], "Attributes1": ["Attributes3"]}
                    }
                    '''
    subtask_analyzer = f"You are an expert in building database conceptual models，You are particularly good at identifying functional dependencies between relationship attributes。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了来自数据库relationshipAttributesrecognitionexpert'sanalysis。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database relationship attribute recognition expert is: '''{relation_attribute_analyses}''' \n 其inkey值表示Relationship name，value值表示relationship'sAttributes。"
    prompt_get_requirement_analyses += f"Review the requirement description analysis by the requirements analysis expert，以and数据库relationshipAttributesrecognitionexpert'sanalysis，你需要得到数据库relationshipAttributes{relation_attribute_analyses}in每个relationship'sfunctional dependencyrelationship。"
    prompt_get_requirement_analyses += f"It is particularly important to note that，functional dependency只存在于每个relationship内部'sAttributes之间。Do not generate additional content。如果没有提供relationshipAttributes则generate空'sjson。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，'''thinking content'''，I can finally conclude thatthe functional dependencies between relationship attributes are：{output_format}'''。"

    return subtask_analyzer, prompt_get_requirement_analyses




def get_dependency_consensus_prompt(question_analyses, entity_attributes, entity_dependency_analyses):
    subtask_analyzer = f"You are an expert in building database conceptual models。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了一个entity(relationship)and其Attributes：{entity_attributes}。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the attribute dependency recognition expert is: '''{entity_dependency_analyses}''' \n"
    prompt_get_requirement_analyses += f"You need to deeply understand the content of the requirements analysis，结合你自身丰富's经验知识，决定你's意见is否withAttributes依赖relationshiprecognitionexpert's意见一致"
    prompt_get_requirement_analyses += f"It is particularly important to note that，你's所有thinking content都应该在[thinking content]in体现，"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，[thinking content]，my answer is：[yes or no]"

    return subtask_analyzer, prompt_get_requirement_analyses



def get_relation_dependency_consensus_prompt(question_analyses, relation_attributes, relation_dependency_analyses):
    subtask_analyzer = f"You are an expert in building database conceptual models。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了一个entity(relationship)and其Attributes：{relation_attributes}。\n"
    prompt_get_requirement_analyses += f"The analysis result of the attribute dependency recognition expert is: '''{relation_dependency_analyses}''' \n"
    prompt_get_requirement_analyses += f"You need to deeply understand the content of the requirements analysis，结合你自身丰富's经验知识，你应该设想多个scenario对Attributes依赖relationshiprecognitionexpert'sanalysisresult进行judgment。"
    prompt_get_requirement_analyses += f"scenario包括但not限于：1. 决定Attributesis否能uniqueidentify依赖Attributes；2.  如果将一个依赖relationship转for一张表，决定Attributes's所有组合值is否只出现一次；..."
    prompt_get_requirement_analyses += f"It is particularly important to note that，你's所有thinking content都应该在[thinking content]in体现。如果not符合scenario，你's意见将withAttributes依赖relationshiprecognitionexpert's意见not一致，please问答no。如果符合scenario，please回答yes。 \n"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，[thinking content]，my answer is：[yes or no]"

    return subtask_analyzer, prompt_get_requirement_analyses

def get_dependency_consensus_opinion_prompt(question_analyses, entity_attributes, entity_dependency_analyses, quality_controller_opi):
    output_format = '''
                        {
                        "Entity name1or者Relationship name1": {"Attributes1": ["Attributes2"], "Attributes1, Attributes2": ["Attributes4"]}, 
                        }
                        '''
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了一个entityand其entityAttributes：{entity_attributes} \n"
    prompt_get_requirement_analyses += f"The analysis result of the attribute dependency recognition expert is:'''{entity_dependency_analyses}''' \n"
    prompt_get_requirement_analyses += f"In addition, we have also obtained modification suggestions from another expert in building database conceptual models for this analysis result：'''{quality_controller_opi}''' \n Ensure that the results of the database attribute dependency recognition expert are modified according to the modification suggestions。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，'''thinking content'''，I can finally conclude thatthe modified functional dependencies between attributes are：{output_format}'''"
    return prompt_get_requirement_analyses


def get_relation_dependency_consensus_opinion_prompt(question_analyses, relation_attributes, relation_dependency_analyses, quality_controller_opi):
    output_format = '''
                        {
                        "Relationship name1": {"Attributes1": ["Attributes2"], "Attributes1, Attributes2": ["Attributes4"]}, 
                        }
                        '''
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了一个relationshipand其Attributes：{relation_attributes} \n"
    prompt_get_requirement_analyses += f"The analysis result of the attribute dependency recognition expert is:'''{relation_dependency_analyses}''' \n"
    prompt_get_requirement_analyses += f"In addition, we have also obtained modification suggestions from another expert in building database conceptual models for this analysis result：'''{quality_controller_opi}''' \n Ensure that the results of the database attribute dependency recognition expert are modified according to the modification suggestions。如果没有functional dependencyrelationship则valuegenerate空'sjson。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，'''thinking content'''，I can finally conclude thatthe modified functional dependencies between attributes are：{output_format}'''"
    return prompt_get_requirement_analyses

def get_relation_revised_analysis_prompt(question_analyses, relation_item_analyses, entity_schemas):
    output_format = '''
                    {
                    "Entity name1": {"Attributes": ["Attributes1", "Attributes2"], "Primary key": ["Attributes1"], "Foreign key":[]}, 
                    "Relationship name2": {"Attributes": ["Attributes1", "Attributes2"], "Primary key": ["Attributes1"], "Foreign key":[{"Attributes2":{"Entity name1":"Attributes1"}}]}
                    }
                    '''
    subtask_analyzer = f"You are an expert in building database conceptual models。"
    prompt_get_requirement_analyses = f"Based on the requirement analysis results from the requirements analysis expert: '''{question_analyses}''' 我们获得了来自数据库relationshiprecognitionexpert'sanalysis。 \n"
    prompt_get_requirement_analyses += f"The analysis result of the database relationship recognition expert for a certain relationship is: '''{relation_item_analyses}''' \n"
    relation_name = list(relation_item_analyses.keys())[0]
    prompt_get_requirement_analyses += f"表示{relation_name}relationship连接两个entity：{relation_item_analyses[relation_name]}\n"
    prompt_get_requirement_analyses += f"但is这个relationshipinnot存在Primary key，这意味着这两个entity之间无法use一个relationship进行连接。需要创建一个新entity。"
    prompt_get_requirement_analyses += f"这is已有'sentity：{entity_schemas} \n"
    prompt_get_requirement_analyses += f"please你继续deeplyunderstandRequirementanalysis'scontent，得到新'sentity以andentityAttributes、Primary key、Foreign key，relationshipandrelationshipAttributes、Primary key、Foreign key。"
    prompt_get_requirement_analyses += f"你'sdesignprinciples包括：1. implementRequirementdescriptionin'sfunction。2. 遵循前文，该relationshipinnot存在Primary key，连接's两个entity无法uniqueidentify。2. 设想多个scenario，reduce数据redundancy。3. 已有'sentitynot要在resultingenerate。"
    prompt_get_requirement_analyses += f"Your output format should be'''After thinking step by step，'''thinking content'''，I can finally conclude thatthe database relational schema is：{output_format}'''"

    return subtask_analyzer, prompt_get_requirement_analyses



# def get_direct_prompt(question):
#     direct_format = '{"schema name1":{"Attributes": ["Attribute name1", "Attribute name2"],"Primary key": ["Attribute name1"]},"schema name2":{"Attributes": ["Attribute name3", "Attribute name4"],"Primary key": ["Attribute name3", "Attribute name1"],"Foreign key": {"schema name1": ["Attribute name1"]}}}'
#     prompt = f"业务Requirement: {question} \n please根据业务Requirement，generateDatabase schema。The content you generate should be in the same format as'''{direct_format}''''sformat相同。在必要's时候才forentity添加IDAttributes进行identify，not需要generate任何additional'scontent"
#     return prompt


def get_direct_prompt(question):
    direct_format = '''
                    {
                        'schema': 
                        {
                            "Relationship schema name 1":
                                {
                                "Attributes":["Attribute name 1", "Attribute name 2"],
                                "Primary key":["Attribute name 1"]
                                },
                            "Relationship schema name 2":
                                {
                                "Attributes":["Attribute name 3","Attribute name 4"],
                                "Primary key":["Attribute name 3","Attribute name 1"],
                                "Foreign key":{
                                        "Attribute name 4":{"Relationship schema name 1":"Attribute name 1"}
                                        }
                                }
                        }
                    }
                    '''
    example = '''
            requirement: A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, department, dormitory address. The addresses of student dormitories in the same department are the same. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            answer: {
                        'schema': {
                            "Student":
                                {
                                    "Attributes": ['ID', 'Name', 'Age', 'Department'],
                                    "Primary key": ['ID']
                                    "Foreign key": {
                                                "Department": {"Department": "ID"}
                                                }
                                },
                            "Department":
                            {
                                "Attributes": ['ID', 'Name', 'Dormitory Adress'],
                                "Primary key": ['ID']
                            },
                            "Course":
                            {
                                "Attributes": ['Number', 'Credits', 'Lecturer', 'Class Time'],
                                "Primary key": ['Number']
                            },
                            "Course Selection":
                            {
                                    "Attributes": ['ID', 'Number', 'Selection Time'],
                                    "Primary key": ['ID', 'Number']
                                    "Foreign key": {
                                                "ID": {"Student": "ID"},
                                                "Number": {"Course": "Number"},
                                                }
                            }
                        }
                    }
              '''
    prompt = f'''
                You are a database design expert. You need to come up with database schemas that meet the requirements provided.
                requirement:{question} 
                Please generate a database schema based on requirements and the knowledge provided. The content you generate should be in the same format as {direct_format}. 
                You should pay attention to these constraints when responding:
                1.  Add ID attributes to entities for identification only when necessary, without generating any additional content.
                2.  If the schema describes an entity, the schema name should be a noun. If the schema describes a relationship, the schema name be a verb.
                3.  All words are separated, e.g. ProductID should be Product ID.
                Here is a example:
                {example}
              '''
    return prompt



def get_direct_few_shot_prompt(question):
    direct_format = '''
                    {
                        'schema': 
                        {
                            "Relationship schema name 1":
                                {
                                "Attributes":["Attribute name 1", "Attribute name 2"],
                                "Primary key":["Attribute name 1"]
                                },
                            "Relationship schema name 2":
                                {
                                "Attributes":["Attribute name 3","Attribute name 4"],
                                "Primary key":["Attribute name 3","Attribute name 1"],
                                "Foreign key":{
                                        "Attribute name 4":{"Relationship schema name 1":"Attribute name 1"}
                                        }
                                }
                        }
                    }
                    '''
    example = '''
            example 1:
            requirement: A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, department, dormitory address. The addresses of student dormitories in the same department are the same. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            answer: {
                        'schema': {
                            "Student":
                                {
                                    "Attributes": ['ID', 'Name', 'Age', 'Department'],
                                    "Primary key": ['ID']
                                    "Foreign key": {
                                                "Department": {"Department": "ID"}
                                                }
                                },
                            "Department":
                            {
                                "Attributes": ['ID', 'Name', 'Dormitory Adress'],
                                "Primary key": ['ID']
                            },
                            "Course":
                            {
                                "Attributes": ['Number', 'Credits', 'Lecturer', 'Class Time'],
                                "Primary key": ['Number']
                            },
                            "Course Selection":
                            {
                                    "Attributes": ['ID', 'Number', 'Selection Time'],
                                    "Primary key": ['ID', 'Number']
                                    "Foreign key": {
                                                "ID": {"Student": "ID"},
                                                "Number": {"Course": "Number"},
                                                }
                            }
                        }
                    }
              example 2:
              requirement: The business requirements of a warehouse management system are described as follows: a warehousing company manages multiple warehouses, each of which has a warehouse number, address, and capacity. The company has multiple loaders, each of which has a number, name, and phone number. Cargo has ID and Name. Each inbound and outbound task needs to record the warehouse number, loader information, cargo information, quantity, and time. The system needs to support real-time monitoring and performance evaluation of warehouses and loading and unloading tasks.
              answer: {
                    "Warehouse":
                    {
                        "Attribute":
                        [
                            "Warehouse Number",
                            "Address",
                            "Capacity"
                        ],
                        "Primary key":
                        [
                            "Warehouse Number"
                        ],
                        "Foreign key":
                        {}
                    },
                    "Cargo":
                    {
                        "Attribute":
                        [
                            "Cargo ID",
                            "Cargo Name"
                        ],
                        "Primary key":
                        [
                            "Cargo ID"
                        ],
                        "Foreign key":
                        {}
                    },
                    "Loader":
                    {
                        "Attribute":
                        [
                            "Name",
                            "Phone",
                            "Loader ID"
                        ],
                        "Primary key":
                        [
                            "Loader ID"
                        ],
                        "Foreign key":
                        {}
                    },
                    "inbound outbound record":
                    {
                        "Attribute":
                        [
                            "Transaction ID",
                            "Time",
                            "Warehouse number",
                            "Transaction type"
                        ],
                        "Primary key":
                        [
                            "Transaction ID"
                        ],
                        "Foreign key":
                        {
                            "Warehouse number":
                            {
                                "Warehouse": "Warehouse number"
                            }
                        }
                    },
                    "goods inbound outbound record":
                    {
                        "Attribute":
                        [
                            "Goods ID",
                            "Transaction ID",
                            "Quantity"
                        ],
                        "Primary key":
                        [
                            "Goods ID",
                            "Transaction ID"
                        ],
                        "Foreign key":
                        {
                            "Transaction ID":
                            {
                                "inbound outbound record": "Transaction ID"
                            },
                            "Goods ID":
                            {
                                "Goods": "Goods ID"
                            }
                        }
                    },
                    "Stevedores Transaction record":
                    {
                        "Attribute":
                        [
                            "Stevedores ID",
                            "Transaction ID"
                        ],
                        "Primary key":
                        [
                            "Stevedores ID",
                            "Transaction ID"
                        ],
                        "Foreign key":
                        {
                            "Transaction ID":
                            {
                                "Transaction record": "Transaction ID"
                            },
                            "Stevedores ID":
                            {
                                "Stevedores": "Stevedores ID"
                            }
                        }
                    }
                }
              example 3:
              requirement: Business requirement description of grassroots organization election management system: A grassroots mass autonomous organization needs to manage the election process, including candidates, voters and voting records. Candidates have candidate numbers, names, genders, dates of birth and positions; voters have voter numbers, names, genders, dates of birth and contact information; a voter can only vote for one candidate, and voters also need to record voting time and voting location when voting. The system can count the number of votes for each candidate.,
              answer: {
                    "Candidate":
                    {
                        "Attribute":
                        [
                            "Candidate Number",
                            "Name",
                            "Gender",
                            "Date of Birth",
                            "Position"
                        ],
                        "Primary key":
                        [
                            "Candidate Number"
                        ],
                        "Foreign key":
                        {}
                    },
                    "Voter":
                    {
                        "Attribute":
                        [
                            "Voter Number",
                            "Name",
                            "Gender",
                            "Date of Birth",
                            "Contact Information",
                            "Candidate Number",
                            "Voting Time",
                            "Voting Location"
                        ],
                        "Primary key":
                        [
                            "Voter Number"
                        ],
                        "Foreign key":
                        {
                            "Candidate Number":
                            {
                                "Candidate": "Candidate Number"
                            }
                        }
                    }
                }
              '''
    prompt = f'''
                You are a database design expert. You need to come up with database schemas that meet the requirements provided.
                requirement:{question} 
                Please generate a database schema based on requirements and the knowledge provided. The content you generate should be in the same format as {direct_format}. 
                You should pay attention to these constraints when responding:
                1.  Add ID attributes to entities for identification only when necessary, without generating any additional content.
                2.  If the schema describes an entity, the schema name should be a noun. If the schema describes a relationship, the schema name be a verb.
                3.  All words are separated, e.g. ProductID should be Product ID.
                Here is a example:
                {example}
              '''
    return prompt




def get_cot_prompt_chinese(question):
    json_format = '{"schema name1":{"Attributes": ["Attribute name1", "Attribute name2"],"Primary key": ["Attribute name1"]},"schema name2":{"Attributes": ["Attribute name3", "Attribute name4"],"Primary key": ["Attribute name3", "Attribute name1"],"Foreign key": {"schema name1": ["Attribute name1"]}}}'
    cot_format = f"Thinking: [step by stepthinking content] \n" \
                f"Database schema: {json_format}"
    prompt = f"Requirement: {question} \n" \
        f"让我们step by step解决这个问题，以ensure我们得到正确's答案。pleaseOutput in Chinese。" \
        f"The content you generate should be in the same format as'''{cot_format}'''. Do not generate content that does not conform to the format.。"
    return prompt



def get_cot_prompt(question):
    direct_format = '''
                        {
                            "Thinking Step": <Your thinking steps>, 
                            "schema": 
                            {
                                "Relationship schema name 1":
                                    {
                                    "Attributes":["Attribute name 1", "Attribute name 2"],
                                    "Primary key":["Attribute name 1"]
                                    },
                                "Relationship schema name 2":
                                    {
                                    "Attributes":["Attribute name 3","Attribute name 4"],
                                    "Primary key":["Attribute name 3","Attribute name 1"],
                                    "Foreign key":{
                                            "Attribute name 4":{"Relationship schema name 1":"Attribute name 1"}
                                            }
                                    }
                            }
                        }
                        '''

    example = '''
            requirement: A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, department, dormitory address. The addresses of student dormitories in the same department are the same. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            answer: {
                        "Thinking Step": "Step 1: Identify key entities from the requirement. The entities are Student, Department, Course, and Course Selection.\n Step 2: Define attributes for each entity. For Student, include ID, Name, Age, and Department. For Department, include ID, Name, and Dormitory Address. For Course, include Number, Credits, Lecturer, and Class Time. For Course Selection, include Student ID, Course Number, and Selection Time.\n Step 3: Define primary keys for each table. For Student, the primary key is ID. For Department, the primary key is ID. For Course, the primary key is Number. For Course Selection, the composite primary key is Student ID and Course Number.\n Step 4: Establish foreign key relationships. The Student table has a foreign key to the Department table. The Course Selection table has foreign keys to both the Student and Course tables.\n Step 5: Normalize the database to avoid redundancy. Dormitory Address is stored in the Department table, as all students in the same department share the same address. The Course Selection table captures the many-to-many relationship between students and courses.\n Step 6: Consider how to handle course popularity prediction. Course popularity can be derived from the Course Selection table by counting the number of students enrolled in each course, although it's not explicitly stored in the schema. "
                        'schema': {
                            "Student":
                                {
                                    "Attributes": ['ID', 'Name', 'Age', 'Department'],
                                    "Primary key": ['ID']
                                    "Foreign key": {
                                                "Department": {"Department": "ID"}
                                                }
                                },
                            "Department":
                            {
                                "Attributes": ['ID', 'Name', 'Dormitory Address'],
                                "Primary key": ['ID']
                            },
                            "Course":
                            {
                                "Attributes": ['Number', 'Credits', 'Lecturer', 'Class Time'],
                                "Primary key": ['Number']
                            },
                            "Course Selection":
                            {
                                    "Attributes": ['ID', 'Number', 'Selection Time'],
                                    "Primary key": ['ID', 'Number']
                                    "Foreign key": {
                                                "ID": {"Student": "ID"},
                                                "Number": {"Course": "Number"},
                                                }
                            }
                        }
                    }
              '''

    prompt = f'''
                You are a database design expert. You need to come up with database schemas that meet the requirements provided.
                Requirement: {question} 
                Let's solve this problem step by step to ensure that we get the correct answer." 
                The content you generate should be in the same format as {direct_format}. Do not generate content that does not conform to the format.
                You should pay attention to these constraints when responding:
                1.  Add ID attributes to entities for identification only when necessary, without generating any additional content.
                2.  If the schema describes an entity, the schema name should be a noun. If the schema describes a relationship, the schema name be a verb.
                3.  All words are separated, e.g. ProductID should be Product ID.
                Here is a example:
                {example}
            '''

    return prompt







def get_cot_few_shot_prompt(question):
    direct_format = '''
                        {
                            "Thinking Step": <Your thinking steps>, 
                            "schema": 
                            {
                                "Relationship schema name 1":
                                    {
                                    "Attributes":["Attribute name 1", "Attribute name 2"],
                                    "Primary key":["Attribute name 1"]
                                    },
                                "Relationship schema name 2":
                                    {
                                    "Attributes":["Attribute name 3","Attribute name 4"],
                                    "Primary key":["Attribute name 3","Attribute name 1"],
                                    "Foreign key":{
                                            "Attribute name 4":{"Relationship schema name 1":"Attribute name 1"}
                                            }
                                    }
                            }
                        }
                        '''
    example = '''
            example 1:
            requirement: A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, department, dormitory address. The addresses of student dormitories in the same department are the same. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
            answer: {
                        "Thinking Step": "Step 1: Identify key entities from the requirement. The entities are Student, Department, Course, and Course Selection. \n Step 2: Define attributes for each entity. For Student, include ID, Name, Age, and Department. For Department, include ID, Name, and Dormitory Address. For Course, include Number, Credits, Lecturer, and Class Time. For Course Selection, include Student ID, Course Number, and Selection Time. \n Step 3: Define primary keys for each table. For Student, the primary key is ID. For Department, the primary key is ID. For Course, the primary key is Number. For Course Selection, the composite primary key is Student ID and Course Number. \nStep 4: Establish foreign key relationships. The Student table has a foreign key to the Department table. The Course Selection table has foreign keys to both the Student and Course tables.\n Step 5: Normalize the database to avoid redundancy. Dormitory Address is stored in the Department table, as all students in the same department share the same address. The Course Selection table captures the many-to-many relationship between students and courses.\n Step 6: Consider how to handle course popularity prediction. Course popularity can be derived from the Course Selection table by counting the number of students enrolled in each course, although it's not explicitly stored in the schema. "
                        'schema': {
                            "Student":
                                {
                                    "Attributes": ['ID', 'Name', 'Age', 'Department'],
                                    "Primary key": ['ID']
                                    "Foreign key": {
                                                "Department": {"Department": "ID"}
                                                }
                                },
                            "Department":
                            {
                                "Attributes": ['ID', 'Name', 'Dormitory Address'],
                                "Primary key": ['ID']
                            },
                            "Course":
                            {
                                "Attributes": ['Number', 'Credits', 'Lecturer', 'Class Time'],
                                "Primary key": ['Number']
                            },
                            "Course Selection":
                            {
                                    "Attributes": ['ID', 'Number', 'Selection Time'],
                                    "Primary key": ['ID', 'Number']
                                    "Foreign key": {
                                                "ID": {"Student": "ID"},
                                                "Number": {"Course": "Number"},
                                                }
                            }
                        }
                    }
            example 2:
            requirement: The business requirements of a warehouse management system are described as follows: a warehousing company manages multiple warehouses, each of which has a warehouse number, address, and capacity. The company has multiple loaders, each of which has a number, name, and phone number. Cargo has ID and Name. Each inbound and outbound task needs to record the warehouse number, loader information, cargo information, quantity, and time. The system needs to support real-time monitoring and performance evaluation of warehouses and loading and unloading tasks.
            answer: {
                    "Thinking Step": "Step 1: Identify key entities from the requirement. The entities are Warehouse, Cargo, Loader, Inbound/Outbound Record, Goods Inbound/Outbound Record, and Stevedores Transaction Record. \n Step 2: Define attributes for each entity. For Warehouse, include Warehouse Number, Address, and Capacity. For Cargo, include Cargo ID and Cargo Name. For Loader, include Loader ID, Name, and Phone Number. For Inbound/Outbound Record, include Transaction ID, Time, Warehouse Number, and Transaction Type. For Goods Inbound/Outbound Record, include Goods ID, Transaction ID, and Quantity. For Stevedores Transaction Record, include Stevedores ID and Transaction ID. \n  Step 3: Define primary keys for each table. For Warehouse, the primary key is Warehouse Number. For Cargo, the primary key is Cargo ID. For Loader, the primary key is Loader ID. For Inbound/Outbound Record, the primary key is Transaction ID. For Goods Inbound/Outbound Record, the composite primary key is Goods ID and Transaction ID. For Stevedores Transaction Record, the composite primary key is Stevedores ID and Transaction ID. \n Step 4: Establish foreign key relationships. The Inbound/Outbound Record table has a foreign key to the Warehouse table. The Goods Inbound/Outbound Record table has foreign keys to both the Inbound/Outbound Record and Cargo tables. The Stevedores Transaction Record table has foreign keys to the Inbound/Outbound Record and Loader tables. \n Step 5: Normalize the database to avoid redundancy. Information about warehouses, cargo, and loaders are stored in separate tables, and related records are connected via foreign keys. The Goods Inbound/Outbound Record and Stevedores Transaction Record tables help track the relationship between tasks, goods, and workers. \n Step 6: Consider how to handle performance evaluation and real-time monitoring. Performance data can be derived from the transaction logs and be used to evaluate the efficiency of warehouses and loaders.",
                    "schema":
                    {
                        "Warehouse":
                        {
                            "Attribute":
                            [
                                "Warehouse Number",
                                "Address",
                                "Capacity"
                            ],
                            "Primary key":
                            [
                                "Warehouse Number"
                            ],
                            "Foreign key":
                            {}
                        },
                        "Cargo":
                        {
                            "Attribute":
                            [
                                "Cargo ID",
                                "Cargo Name"
                            ],
                            "Primary key":
                            [
                                "Cargo ID"
                            ],
                            "Foreign key":
                            {}
                        },
                        "Loader":
                        {
                            "Attribute":
                            [
                                "Name",
                                "Phone",
                                "Loader ID"
                            ],
                            "Primary key":
                            [
                                "Loader ID"
                            ],
                            "Foreign key":
                            {}
                        },
                        "inbound outbound record":
                        {
                            "Attribute":
                            [
                                "Transaction ID",
                                "Time",
                                "Warehouse number",
                                "Transaction type"
                            ],
                            "Primary key":
                            [
                                "Transaction ID"
                            ],
                            "Foreign key":
                            {
                                "Warehouse number":
                                {
                                    "Warehouse": "Warehouse number"
                                }
                            }
                        },
                        "goods inbound outbound record":
                        {
                            "Attribute":
                            [
                                "Goods ID",
                                "Transaction ID",
                                "Quantity"
                            ],
                            "Primary key":
                            [
                                "Goods ID",
                                "Transaction ID"
                            ],
                            "Foreign key":
                            {
                                "Transaction ID":
                                {
                                    "inbound outbound record": "Transaction ID"
                                },
                                "Goods ID":
                                {
                                    "Goods": "Goods ID"
                                }
                            }
                        },
                        "Stevedores Transaction record":
                        {
                            "Attribute":
                            [
                                "Stevedores ID",
                                "Transaction ID"
                            ],
                            "Primary key":
                            [
                                "Stevedores ID",
                                "Transaction ID"
                            ],
                            "Foreign key":
                            {
                                "Transaction ID":
                                {
                                    "Transaction record": "Transaction ID"
                                },
                                "Stevedores ID":
                                {
                                    "Stevedores": "Stevedores ID"
                                }
                            }
                        }
                    }
                }
              example 3:
              requirement: Business requirement description of grassroots organization election management system: A grassroots mass autonomous organization needs to manage the election process, including candidates, voters and voting records. Candidates have candidate numbers, names, genders, dates of birth and positions; voters have voter numbers, names, genders, dates of birth and contact information; a voter can only vote for one candidate, and voters also need to record voting time and voting location when voting. The system can count the number of votes for each candidate.,
              answer: {
                    "Thinking Step": "Step 1: Identify key entities from the requirement. The entities are Candidate, Voter, and Voting Record. \n Step 2: Define attributes for each entity. For Candidate, include Candidate Number, Name, Gender, Date of Birth, and Position. For Voter, include Voter Number, Name, Gender, Date of Birth, and Contact Information. For Voting Record, include Voter Number, Candidate Number, Voting Time, and Voting Location. \n Step 3: Define primary keys for each table. For Candidate, the primary key is Candidate Number. For Voter, the primary key is Voter Number. For Voting Record, the composite primary key is Voter Number.\n Step 4: Establish foreign key relationships. The Voting Record table has foreign keys to both the Voter and Candidate tables. \n Step 5: Normalize the database to avoid redundancy. Candidate and Voter information are stored separately to ensure efficient data management. The Voting Record table captures the relationship between voters and candidates while also storing voting details. \n Step 6: Consider how to handle vote counting. The system can derive the number of votes for each candidate by aggregating records in the Voting Record table, rather than storing it explicitly in the schema.",
                    "schema":
                    {
                        "Candidate":
                        {
                            "Attribute":
                            [
                                "Candidate Number",
                                "Name",
                                "Gender",
                                "Date of Birth",
                                "Position"
                            ],
                            "Primary key":
                            [
                                "Candidate Number"
                            ],
                            "Foreign key":
                            {}
                        },
                        "Voter":
                        {
                            "Attribute":
                            [
                                "Voter Number",
                                "Name",
                                "Gender",
                                "Date of Birth",
                                "Contact Information",
                                "Candidate Number",
                                "Voting Time",
                                "Voting Location"
                            ],
                            "Primary key":
                            [
                                "Voter Number"
                            ],
                            "Foreign key":
                            {
                                "Candidate Number":
                                {
                                    "Candidate": "Candidate Number"
                                }
                            }
                        }
                    }
                }
              '''

    prompt = f'''
                You are a database design expert. You need to come up with database schemas that meet the requirements provided.
                Requirement: {question} 
                Let's solve this problem step by step to ensure that we get the correct answer." 
                The content you generate should be in the same format as {direct_format}. Do not generate content that does not conform to the format.
                You should pay attention to these constraints when responding:
                1.  Add ID attributes to entities for identification only when necessary, without generating any additional content.
                2.  If the schema describes an entity, the schema name should be a noun. If the schema describes a relationship, the schema name be a verb.
                3.  All words are separated, e.g. ProductID should be Product ID.
                Here is a example:
                {example}
            '''

    return prompt



def get_pseudo_code_prompt(question, code_path):
    role = f"You are an expert in building database relational models. You can continuously calculate based on code logic and eventually get the output."
    with open(code_path, 'r', encoding='utf-8') as f:
        code_prompt = f.read()
    code_prompt += f'\n >>>generate_schema_from_text({question})'
    return role, code_prompt
