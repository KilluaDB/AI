import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
import io
from typing import List
from typing_extensions import Self
from pydantic import BaseModel

from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import LLMMessage
from typing_extensions import Annotated
# from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from autogen_core import Component

from autogen_agentchat.agents import AssistantAgent, SocietyOfMindAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.ui import Console

# Import centralized LLM configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_config import create_model_client, list_available_models

# Import shared normalization utilities
from shared.normalization_utils import (
    compute_closure,
    find_candidate_keys,
    get_attribute_keys_by_armstrong_single as get_attribute_keys_by_arm_strong_each,
)

from user_prompt_english import (get_conceptual_design_agent_prompt, get_logical_design_agent_prompt, get_QA_agent_prompt, get_report_prompt,\
    get_selector_prompt, get_manager_prompt, selector_func, get_reviewer_prompt, get_execution_agent_prompt, get_physical_design_agent_prompt)

# Import PostgreSQL and Mermaid tools
from postgres_tools import (
    execute_sql_on_postgres,
    execute_ddl_statements,
    validate_ddl_syntax,
    infer_and_generate_ddl,
    test_postgres_connection,
    POSTGRES_TOOLS,
)
from mermaid_tools import (
    generate_mermaid_from_conceptual,
    generate_mermaid_from_logical,
    extract_conceptual_json,
    extract_logical_json,
    validate_mermaid_syntax,
    conceptual_to_mermaid,
    logical_to_mermaid,
)

# Import RAG tools for domain-specific knowledge
try:
    from rag import RAG_TOOLS, detect_domain_from_text, Domain
    RAG_AVAILABLE = True
except ImportError:
    RAG_TOOLS = []
    RAG_AVAILABLE = False
    print("Note: RAG module not available. Domain-specific knowledge disabled.")


# NOTE: compute_closure and find_candidate_keys are now imported from shared.normalization_utils


async def get_attribute_keys_by_arm_strong(dependencies_json: Annotated[
    str, "json in function dependencies {'entity set name or relationship set name': {'attribute 1': ['The attributes determined by the attribute 1']}}"]):
    '''Identify primary keys based on functional dependencies'''
    # Attribute sets
    attributes_all = {}
    dependencies_all = {}
    dependencies_json = json.loads(dependencies_json)
    for entity_name in dependencies_json:
        entity = dependencies_json[entity_name]
        attributes = []
        dependencies = []
        for depend_key in entity:
            if '&' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split('&')]  # Handle multiple left values
            elif ',' in depend_key:
                depend_key_list = [it.strip() for it in depend_key.split(',')]  # Handle multiple left values
            else:
                depend_key_list = [depend_key]
            attributes.extend(list(set(depend_key_list) | set(entity[depend_key])))
            dependencies.append((set(depend_key_list), set(entity[depend_key])))
        attributes = list(set(attributes))

        attributes_all[entity_name] = attributes
        dependencies_all[entity_name] = dependencies


    candidate_keys_dict = {}
    # Execute candidate key search
    for entity_name in attributes_all:
        candidate_keys = find_candidate_keys(attributes_all[entity_name], dependencies_all[entity_name])
        # print(f"The candidate keys of entity {entity_name} are:", candidate_keys)
        candidate_keys_dict[entity_name] = candidate_keys
    return {"attributes_all": attributes_all, "entity_primary_keys": candidate_keys_dict}


# NOTE: get_attribute_keys_by_arm_strong_each is now imported from shared.normalization_utils


async def confirm_to_third_normal_form(dependencies_json: Annotated[
    str, "json in function dependencies {'entity set name or relationship set name':{'attribute 1':['The attributes determined by the attribute 1']}}"],
                           entity_primary_keys: Annotated[
                               str, "json in {entity set name or relationship set name:[[primary key 1],[primary key 2]]}"],
                           attributes_all: Annotated[str, "json in {'entity set name or relationship set name':['attribute 1','attribute 2']}"]):
    """
    Automatically decompose current relations to 3NF.
    """

    def parse_dependencies(entity_fd_json):
        """
        Parse functional dependencies, supporting attributes separated by commas.
        """
        functional_dependencies = []
        for entity, dependencies in entity_fd_json.items():
            for determinant, dependents in dependencies.items():
                determinant_list = [attr.strip() for attr in determinant.split(",")]
                functional_dependencies.append((determinant_list, dependents, entity))
        return functional_dependencies

    def find_closure(dependencies, target_set):
        """
        Calculate the closure of attribute set target_set.
        """
        closure = set(target_set)
        changed = True
        while changed:
            changed = False
            for X, Y in dependencies:
                if set(X).issubset(closure) and not set(Y).issubset(closure):
                    closure.update(Y)
                    changed = True
        return closure

    dependencies_json = json.loads(dependencies_json)
    entity_primary_keys = json.loads(entity_primary_keys)
    attributes_all = json.loads(attributes_all)

    # Parse functional dependencies
    functional_dependencies = parse_dependencies(dependencies_json)

    # Save results
    transitive_partial_dependencies = defaultdict(lambda: {"decompose_relationships": []})

    # Classify dependencies by entity
    dependencies_by_entity = defaultdict(list)
    for determinant, dependent, entity in functional_dependencies:
        dependencies_by_entity[entity].append((determinant, dependent))

    # Functional dependency analysis
    for entity, deps in dependencies_by_entity.items():
        primary_keys = entity_primary_keys[entity]  # Get current entity's primary key

        # Decomposed relations
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

        for pk in primary_keys:
            if not any(set(pk).issubset(relation) for relation in relations):
                relations.append(set(pk))

        # Remove duplicate relations
        unique_relations = []
        for rel in relations:
            if len(rel) == 1:
                continue
            if rel not in unique_relations:
                unique_relations.append(rel)

        transitive_partial_dependencies[entity]["decompose_relationships"] = unique_relations

    transitive_partial_dependencies = {key: value for key, value in
                                       transitive_partial_dependencies.items()}  # Convert to regular dict

    new_entity_add_relation_attributes_all = defaultdict(dict)
    new_entity_add_relation_keys_and_attribute_map = {}
    for entity_name in transitive_partial_dependencies:
        if len(transitive_partial_dependencies[entity_name]['decompose_relationships']) == 1:  # No need to split table
            new_entity_add_relation_attributes_all[entity_name]['Attribute'] = attributes_all[
                entity_name]
            new_entity_add_relation_keys_and_attribute_map[entity_name] = entity_primary_keys[
                entity_name]
        else:  # Need to split table
            for sub_table_attributes in transitive_partial_dependencies[entity_name]['decompose_relationships']:
                candidate_keys = get_attribute_keys_by_arm_strong_each(sub_table_attributes,
                                                                            dependencies_json[entity_name])
                new_entity_name = ''
                for candidate_key in candidate_keys:
                    new_entity_name = ''.join(candidate_key)  
                new_entity_add_relation_attributes_all[new_entity_name]['Attribute'] = sub_table_attributes
                new_entity_add_relation_attributes_all[new_entity_name]['Foreign_key'] = {}
                new_entity_add_relation_keys_and_attribute_map[new_entity_name] = candidate_keys

    return {"entity_attributes_all": new_entity_add_relation_attributes_all,
            "entity_keys_and_attribute_map": new_entity_add_relation_keys_and_attribute_map}





class RoleChatCompletionContextConfig(BaseModel):
    name: str
    initial_messages: List[LLMMessage] | None = None


class RoleChatCompletionContext(ChatCompletionContext, Component[RoleChatCompletionContextConfig]):
    """A chat completion context that keeps a view of the specific assistant,
    Args:
        name (int): The name of the assistant.
        initial_messages (List[LLMMessage] | None): The initial messages.
    """

    component_config_schema = RoleChatCompletionContextConfig
    # component_provider_override = "autogen_core.model_context.HeadAndTailChatCompletionContext"

    def __init__(self, name: str, initial_messages: List[LLMMessage] | None = None) -> None:
        super().__init__(initial_messages)
        self._name = name

    async def get_messages(self) -> List[LLMMessage]:
        """Get messages from the specific assistant"""
        # Filter out thought field from AssistantMessage.
        messages_out: List[LLMMessage] = []
        for message in self._messages:
            if message.source == self._name:
                messages_out.append(message)
        return messages_out

    def _to_config(self) -> RoleChatCompletionContextConfig:
        return RoleChatCompletionContextConfig(
            name=self._name, initial_messages=self._initial_messages
        )

    @classmethod
    def _from_config(cls, config: RoleChatCompletionContextConfig) -> Self:
        return cls(name=config.name, initial_messages=config.initial_messages)



async def main(args):

    print('===================')
    print(args)
    # PostgreSQL connection parameters (optional - for database execution)
    # postgres_params = {
    #     "host": os.getenv("POSTGRES_HOST", "localhost"),
    #     "port": os.getenv("POSTGRES_PORT", "5432"),
    #     "user": os.getenv("POSTGRES_USER", "postgres"),
    #     "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
    #     "database": args.database_name,
    # }

    # # PostgreSQL MCP server params (if using MCP tools)
    # server_params = StdioServerParams(
    #     command="npx",
    #     args=["-y", "@anthropic-ai/mcp-server-postgres"],
    #     env={
    #         "POSTGRES_HOST": postgres_params["host"],
    #         "POSTGRES_PORT": postgres_params["port"],
    #         "POSTGRES_USER": postgres_params["user"],
    #         "POSTGRES_PASSWORD": postgres_params["password"],
    #         "POSTGRES_DATABASE": postgres_params["database"],
    #     },
    # )

    # # get PostgreSQL tools
    # tools = await mcp_server_tools(server_params)

    # Get available models from centralized config
    available_models = list_available_models()
    print(f"Available models: {available_models}")
    
    # Create model client using centralized configuration
    model_client = create_model_client(args.model_name)
    print(f'Finished loading model: {args.model_name}')
    
    # Prepare RAG tools based on availability
    conceptual_rag_tools = RAG_TOOLS[:4] if RAG_AVAILABLE else []  # detect, entity, relationship, query
    logical_rag_tools = [RAG_TOOLS[4], RAG_TOOLS[5], RAG_TOOLS[0]] if RAG_AVAILABLE and len(RAG_TOOLS) > 5 else []  # cardinality, normalization, query
    physical_rag_tools = [RAG_TOOLS[3], RAG_TOOLS[0]] if RAG_AVAILABLE and len(RAG_TOOLS) > 3 else []  # datatype, query
    reviewer_rag_tools = RAG_TOOLS[:4] if RAG_AVAILABLE else []  # detect, entity, relationship, query
    
    if RAG_AVAILABLE:
        print(f"RAG tools enabled: {len(RAG_TOOLS)} tools available")
    else:
        print("RAG tools disabled - running without domain-specific knowledge")

    conceptual_designer_agent = AssistantAgent(
        "ConceptualDesignerAgent",
        description="Concept designers design conceptual models based on requirements analysis. Can use RAG for domain-specific guidance.",
        model_client=model_client,
        tools=conceptual_rag_tools,
        system_message=get_conceptual_design_agent_prompt(),
        reflect_on_tool_use=True if conceptual_rag_tools else False,
    )

    logical_designer_agent = AssistantAgent(
        "LogicalDesignerAgent",
        description="The logic designer designs the logical model based on the conceptual model.",
        model_client=model_client,
        tools=[get_attribute_keys_by_arm_strong, confirm_to_third_normal_form] + logical_rag_tools,
        system_message=get_logical_design_agent_prompt(),
        reflect_on_tool_use=True
    )

    qa_agent = AssistantAgent(
        "QAAgent",
        description="QA engineers generate test cases based on requirement analysis.",
        model_client=model_client,
        system_message=get_QA_agent_prompt(),
        model_context=RoleChatCompletionContext(name='ManagerAgent'), #limited, can only see the requirement analysis
    )

    execution_agent = AssistantAgent(
        "ExecutionAgent",
        description="The execution agent evaluates whether the current database logic design schemas satisfies the test cases.",
        model_client=model_client,
        system_message=get_execution_agent_prompt(),
    )

    manager = AssistantAgent(
        "ManagerAgent",
        description="Managers have two jobs. One is to analyze user requirement, and the other is to decide the final acceptance.",
        model_client=model_client,
        system_message=get_manager_prompt(),
    )

    conceptual_reviewer_agent = AssistantAgent(
        "ConceptualReviewerAgent",
        description="Determine whether the current conceptual model satisfies all constraints. Can use RAG for domain validation.",
        model_client=model_client,
        tools=reviewer_rag_tools,
        system_message=get_reviewer_prompt(),
        reflect_on_tool_use=True if reviewer_rag_tools else False,
    )


    #Physical designers do not belong to this group because they cannot provide feedback on the design process and only follow the results of logical designers.  
    physical_designer_agent = AssistantAgent(
        "PhysicalDesignerAgent",
        description='The physical designer designs and executes the SQL statements based on the logical model. Has PostgreSQL tools for DDL execution and validation. Can use RAG for domain-specific type mappings.',
        model_client=model_client,
        tools=[
            execute_sql_on_postgres,
            execute_ddl_statements,
            validate_ddl_syntax,
            infer_and_generate_ddl,
            test_postgres_connection,
        ] + physical_rag_tools,
        system_message=get_physical_design_agent_prompt(),
        reflect_on_tool_use=True,
    )

    # agent to produce a report
    report_agent = AssistantAgent(
        'ReportAgent',
        description='The report agent compiles the current information into a standardized report format.',
        model_client=model_client,
        system_message=get_report_prompt(),
    )

    text_mention_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=15)
    termination = text_mention_termination | max_messages_termination


    # for conceptual model design, nested group chat
    inner_termination = TextMentionTermination("Approve") | max_messages_termination
    inner_team = RoundRobinGroupChat([conceptual_designer_agent, conceptual_reviewer_agent], termination_condition=inner_termination)
    society_of_mind_agent = SocietyOfMindAgent("ConceptualAgent",
                                               description='A team that designs conceptual models based on requirements analysis.',
                                               team=inner_team,
                                               model_client=model_client,
                                               instruction='Output the Final Answer formatted in json by ConceptualDesignerAgent. Do NOT change anything.')

    team = SelectorGroupChat([manager, society_of_mind_agent, logical_designer_agent, qa_agent, execution_agent],
                                 model_client=model_client,
                                 termination_condition=termination,
                                 allow_repeated_speaker=True,
                                 selector_prompt=get_selector_prompt(),
                                 selector_func=selector_func
                             )
    
    # -------------------- Test Examples -------------------
    # text = "A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, the name of the course chosen by the student, etc. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."
    # text = 'The business needs of a factory are as follows: the factory has multiple departments, some of which are production departments, called workshops. A department has multiple employees, and an employee belongs to only one department. Each employee has an employee number, name, date of birth, gender, telephone number and position; the factory produces a variety of products. Products have names, models, barcodes and prices. Departments need to collect parts from the warehouse and also put their products into the warehouse. Parts have names, models, barcodes and prices; each time they are collected, they need to record which parts have been collected, their quantity, the consignor, the recipient, and the collection time. When products are put into the warehouse, they also need to record which products have been put into the warehouse, their quantity, the consignor, the consignee, and the storage time. The production management information system should be able to evaluate the performance of the department.'
    # text = "The required functions of a certain tourism management system are described as follows: In the user management module, users can register by filling in their username, password, email address and phone number. The system will set the default user role to \"ordinary user\" and save the creation time and update time. In the team management module, administrators can create new team activities and fill in the event title, description, start and end date, event location and other information. After the event is created, the system will record the release time and update time. Users can sign up for team activities, and the system will record the user's registration time and status (such as registered, canceled). Users can cancel their registration before the event starts. In the attraction management module, administrators can manage the attraction list, including adding new attractions, deleting old attractions, or modifying the name, description, picture and location of the attraction. The system will record the creation time and update time. Users can comment on the attractions, including the content of the comment and the rating."
    # text = "The business requirements of a warehouse management system are described as follows: a warehousing company manages multiple warehouses, each of which has a warehouse number, address, and capacity. The company has multiple loaders, each of which has a number, name, and phone number. Each inbound and outbound task needs to record the warehouse number, loader information, cargo information, quantity, and time. The system needs to support real-time monitoring and performance evaluation of warehouses and loading and unloading tasks."

    text = args.requirement_text

    # backup markdown file - use absolute path
    saved_files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_files')
    os.makedirs(saved_files_dir, exist_ok=True)
    save_file_path = os.path.join(saved_files_dir, '_'.join(text[:15].split()) + '.md')
    
    # Create a StringIO object to capture the output
    captured_output = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured_output
    print('++++++++++ Begin to generate logical schemas +++++++++++')
    await Console(team.run_stream(task=text))
    # Reset the team for the next run. the next task is not related to the previous task
    await team.reset()  
    output_string = captured_output.getvalue()

    # Generate Mermaid diagram from conceptual design (by parsing, not LLM)
    print('++++++++++ Generating Mermaid ER diagram +++++++++++')
    try:
        mermaid_code, mermaid_file = conceptual_to_mermaid(output_string)
        if mermaid_code:
            is_valid, errors = validate_mermaid_syntax(mermaid_code)
            if is_valid:
                print(f'Mermaid diagram generated and validated: {mermaid_file}')
            else:
                print(f'Mermaid diagram generated with warnings: {errors}')
        else:
            print('Could not generate Mermaid diagram from conceptual design')
    except Exception as e:
        print(f'Error generating Mermaid diagram: {e}')

    print('++++++++++ Begin to generate physical DDL +++++++++++')
    # the team meassage will give to the physical model agent. workflow
    # Physical agent now has PostgreSQL tools for execution and self-refinement
    physical_result = await Console(physical_designer_agent.run_stream(task=output_string))
    output_string = captured_output.getvalue()
    
    # Self-refinement loop for physical design if execution failed
    max_refinement_attempts = 3
    refinement_attempt = 0
    while refinement_attempt < max_refinement_attempts:
        # Check if the last message indicates failure
        last_message = physical_result.messages[-1].content if physical_result.messages else ""
        if "Fail" in last_message or "Error" in last_message or "error" in last_message.lower():
            refinement_attempt += 1
            print(f'++++++++++ Self-refinement attempt {refinement_attempt} +++++++++++')
            refinement_prompt = f"""
            The previous DDL execution encountered errors. Please analyze the error and fix the issues:
            
            Previous output: {last_message}
            
            Steps to fix:
            1. Identify the specific error
            2. Fix the problematic SQL statement
            3. Re-execute using the PostgreSQL tools
            4. Verify success
            """
            physical_result = await Console(physical_designer_agent.run_stream(task=refinement_prompt))
            output_string = captured_output.getvalue()
        else:
            break

    print('++++++++++ Begin to generate report +++++++++++')
    # produce a report, change format, download. challenge.
    result = await Console(report_agent.run_stream(task=output_string))
    print('Success.')
    output_string = captured_output.getvalue()

    sys.stdout = original_stdout
    captured_output.close()

    with open(save_file_path, 'w') as f:
        f.write(output_string)
    
    print(f"finish saving file to {save_file_path}")

    note_message = f" \n\n### NOTE \n(1) Use the following statement to create a new database in PostgreSQL: \n```sql \nCREATE DATABASE {args.database_name}; \n``` \n(2) Copy the above DDL statements to PostgreSQL for execution. "

    return result.messages[1].content + note_message
    


async def stream_main(args):
    """
    Async generator that streams agent messages in real-time during schema generation.

    Yields dicts with these fields:
      - type: "phase" | "agent_message" | "tool_call" | "tool_result" | "thinking" | "error" | "done"
      - phase: "logical_design" | "physical_design" | "report"
      - status: "start" | "complete" | "refinement"  (only for type=="phase")
      - agent: agent name string  (for message/tool events)
      - content: text content     (for message/tool events)
      - attempt: int              (only for refinement phases)
    """
    model_client = create_model_client(args.model_name)

    conceptual_rag_tools = RAG_TOOLS[:4] if RAG_AVAILABLE else []
    logical_rag_tools = [RAG_TOOLS[4], RAG_TOOLS[5], RAG_TOOLS[0]] if RAG_AVAILABLE and len(RAG_TOOLS) > 5 else []
    physical_rag_tools = [RAG_TOOLS[3], RAG_TOOLS[0]] if RAG_AVAILABLE and len(RAG_TOOLS) > 3 else []
    reviewer_rag_tools = RAG_TOOLS[:4] if RAG_AVAILABLE else []

    conceptual_designer_agent = AssistantAgent(
        "ConceptualDesignerAgent",
        description="Concept designers design conceptual models based on requirements analysis. Can use RAG for domain-specific guidance.",
        model_client=model_client,
        tools=conceptual_rag_tools,
        system_message=get_conceptual_design_agent_prompt(),
        reflect_on_tool_use=True if conceptual_rag_tools else False,
    )

    logical_designer_agent = AssistantAgent(
        "LogicalDesignerAgent",
        description="The logic designer designs the logical model based on the conceptual model.",
        model_client=model_client,
        tools=[get_attribute_keys_by_arm_strong, confirm_to_third_normal_form] + logical_rag_tools,
        system_message=get_logical_design_agent_prompt(),
        reflect_on_tool_use=True,
    )

    qa_agent = AssistantAgent(
        "QAAgent",
        description="QA engineers generate test cases based on requirement analysis.",
        model_client=model_client,
        system_message=get_QA_agent_prompt(),
        model_context=RoleChatCompletionContext(name="ManagerAgent"),
    )

    execution_agent = AssistantAgent(
        "ExecutionAgent",
        description="The execution agent evaluates whether the current database logic design schemas satisfies the test cases.",
        model_client=model_client,
        system_message=get_execution_agent_prompt(),
    )

    manager = AssistantAgent(
        "ManagerAgent",
        description="Managers have two jobs. One is to analyze user requirement, and the other is to decide the final acceptance.",
        model_client=model_client,
        system_message=get_manager_prompt(),
    )

    conceptual_reviewer_agent = AssistantAgent(
        "ConceptualReviewerAgent",
        description="Determine whether the current conceptual model satisfies all constraints. Can use RAG for domain validation.",
        model_client=model_client,
        tools=reviewer_rag_tools,
        system_message=get_reviewer_prompt(),
        reflect_on_tool_use=True if reviewer_rag_tools else False,
    )

    physical_designer_agent = AssistantAgent(
        "PhysicalDesignerAgent",
        description="The physical designer designs and executes the SQL statements based on the logical model.",
        model_client=model_client,
        tools=[
            execute_sql_on_postgres,
            execute_ddl_statements,
            validate_ddl_syntax,
            infer_and_generate_ddl,
            test_postgres_connection,
        ] + physical_rag_tools,
        system_message=get_physical_design_agent_prompt(),
        reflect_on_tool_use=True,
    )

    report_agent = AssistantAgent(
        "ReportAgent",
        description="The report agent compiles the current information into a standardized report format.",
        model_client=model_client,
        system_message=get_report_prompt(),
    )

    text_mention_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=15)
    termination = text_mention_termination | max_messages_termination

    inner_termination = TextMentionTermination("Approve") | max_messages_termination
    inner_team = RoundRobinGroupChat(
        [conceptual_designer_agent, conceptual_reviewer_agent],
        termination_condition=inner_termination,
    )
    society_of_mind_agent = SocietyOfMindAgent(
        "ConceptualAgent",
        description="A team that designs conceptual models based on requirements analysis.",
        team=inner_team,
        model_client=model_client,
        instruction="Output the Final Answer formatted in json by ConceptualDesignerAgent. Do NOT change anything.",
    )

    team = SelectorGroupChat(
        [manager, society_of_mind_agent, logical_designer_agent, qa_agent, execution_agent],
        model_client=model_client,
        termination_condition=termination,
        allow_repeated_speaker=True,
        selector_prompt=get_selector_prompt(),
        selector_func=selector_func,
    )

    def _serialize_content(content):
        """Serialize message content to a plain string."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if hasattr(item, "name") and hasattr(item, "arguments"):
                    # FunctionCall (tool call request)
                    parts.append(f"[Tool: {item.name}] {item.arguments}")
                elif hasattr(item, "content") and hasattr(item, "call_id"):
                    # FunctionExecutionResult (tool result)
                    parts.append(f"[Result]: {item.content}")
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        return str(content)

    def _event_type(msg):
        name = type(msg).__name__
        if "ToolCallRequest" in name:
            return "tool_call"
        if "ToolCallExecution" in name:
            return "tool_result"
        if "Thought" in name:
            return "thinking"
        return "agent_message"

    text = args.requirement_text

    # ── Phase 1: Logical design ──────────────────────────────────────────────
    yield {"type": "phase", "phase": "logical_design", "status": "start",
           "message": "Starting logical schema design"}

    accumulated = []
    async for msg in team.run_stream(task=text):
        if not (hasattr(msg, "source") and hasattr(msg, "content")):
            continue  # TaskResult or internal control message
        source = msg.source
        content = _serialize_content(msg.content)
        accumulated.append(f"\n---------- {source} ----------\n{content}\n")
        yield {"type": _event_type(msg), "agent": source,
               "phase": "logical_design", "content": content}

    await team.reset()
    logical_output = "".join(accumulated)
    yield {"type": "phase", "phase": "logical_design", "status": "complete"}

    # Generate Mermaid ER diagram from the conceptual schema in the logical output
    try:
        mermaid_code, _ = conceptual_to_mermaid(logical_output)
        if mermaid_code:
            is_valid, errors = validate_mermaid_syntax(mermaid_code)
            yield {"type": "mermaid", "content": mermaid_code, "valid": is_valid}
    except Exception:
        pass  # Mermaid generation is best-effort; don't abort the stream

    # ── Phase 2: Physical design ─────────────────────────────────────────────
    yield {"type": "phase", "phase": "physical_design", "status": "start",
           "message": "Starting physical DDL generation"}

    physical_acc = []
    last_physical_content = ""

    async def _run_physical(task_text):
        nonlocal last_physical_content
        async for msg in physical_designer_agent.run_stream(task=task_text):
            if not (hasattr(msg, "source") and hasattr(msg, "content")):
                continue
            source = msg.source
            content = _serialize_content(msg.content)
            physical_acc.append(f"\n---------- {source} ----------\n{content}\n")
            last_physical_content = content
            yield {"type": _event_type(msg), "agent": source,
                   "phase": "physical_design", "content": content}

    async for event in _run_physical(logical_output):
        yield event

    # Self-refinement loop
    for attempt in range(1, 4):
        if not ("Fail" in last_physical_content or "error" in last_physical_content.lower()):
            break
        yield {"type": "phase", "phase": "physical_design",
               "status": "refinement", "attempt": attempt}
        refinement_prompt = (
            "The previous DDL execution encountered errors. "
            "Analyze the error, fix the problematic statement, re-execute, and verify success.\n\n"
            f"Previous output:\n{last_physical_content}"
        )
        async for event in _run_physical(refinement_prompt):
            yield event

    full_output = logical_output + "".join(physical_acc)
    yield {"type": "phase", "phase": "physical_design", "status": "complete"}

    # ── Phase 3: Report ──────────────────────────────────────────────────────
    yield {"type": "phase", "phase": "report", "status": "start",
           "message": "Generating final report"}

    async for msg in report_agent.run_stream(task=full_output):
        if not (hasattr(msg, "source") and hasattr(msg, "content")):
            continue
        source = msg.source
        content = _serialize_content(msg.content)
        yield {"type": _event_type(msg), "agent": source,
               "phase": "report", "content": content}

    yield {"type": "phase", "phase": "report", "status": "complete"}
    yield {"type": "done", "message": "Schema generation complete"}


# ----------- for test -----------
if __name__ == "__main__":
    requirement_text = "A university needs a student course selection management system to maintain and track students' course selection information. Students have information such as student ID, name, age, the name of the course chosen by the student, etc. Each student can take multiple courses and can drop or change courses within the specified time. Each course has information such as course number, course name, credits, lecturer and class time. The popularity of a course depends on the number of students who take the course. The system can predict the popularity of the course and provide support for academic decision-making."

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', default='gpt4')
    parser.add_argument('--database_name', default='relation_mcp_test')
    parser.add_argument('--database_user', default='root')
    parser.add_argument('--database_password', default='123456')
    parser.add_argument('--database_port', default='3306')
    parser.add_argument('--requirement_text', default=requirement_text)

    args = parser.parse_args()
    asyncio.run(main(args))
