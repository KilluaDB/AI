import argparse
import asyncio
import json
import os
import sys
import io
import logging
from typing import List
from typing_extensions import Self
from pydantic import BaseModel

from autogen_core.model_context import ChatCompletionContext
from autogen_core.models import LLMMessage
from autogen_core import Component

from autogen_agentchat.agents import AssistantAgent, SocietyOfMindAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import SelectorGroupChat, RoundRobinGroupChat
from autogen_agentchat.ui import Console

# Import centralized LLM configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_config import create_model_client, list_available_models, get_model_config

from user_prompt_english import (get_conceptual_design_agent_prompt, get_logical_design_agent_prompt, get_QA_agent_prompt,\
    get_selector_prompt, get_manager_prompt, selector_func, get_reviewer_prompt, get_execution_agent_prompt, get_society_of_mind_prompt)
from util import *
from context import RoleChatCompletionContext, RecipientChatCompletionContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main(args):

    logger.info(args)
    
    # Get available models from centralized config
    available_models = list_available_models()
    logger.info(f"Available models: {available_models}")

    # Create model client using configs
    try:
        model_client = create_model_client(args.model_name)
        logger.info(f'Finished loading model: {args.model_name}')
    except ValueError as e:
        logger.error(f"Model configuration error: {e}")
        raise

    conceptual_designer_agent = AssistantAgent(
        "ConceptualDesignerAgent",
        description="Concept designers design conceptual models based on requirements analysis.",
        model_client=model_client,
        system_message=get_conceptual_design_agent_prompt(),
        model_context=RecipientChatCompletionContext(name=["society_of_mind", "ConceptualDesignerAgent"])
    )

    logical_designer_agent = AssistantAgent(
        "LogicalDesignerAgent",
        description="The logic designer designs the logical model based on the conceptual model.",
        model_client=model_client,
        tools=[get_attribute_keys_by_arm_strong, confirm_to_third_normal_form],
        system_message=get_logical_design_agent_prompt(),
        reflect_on_tool_use=True
       
    )

    qa_agent = AssistantAgent(
        "QAAgent",
        description="QA engineers generate test cases based on requirement analysis.",
        model_client=model_client,
        system_message=get_QA_agent_prompt(),
        model_context=RecipientChatCompletionContext(name=['QAAgent']) #limited, can only see the requirement analysis
    )

    execution_agent = AssistantAgent(
        "ExecutionAgent",
        description="The execution agent evaluates whether the current database logic design schemas satisfies the test cases.",
        model_client=model_client,
        system_message=get_execution_agent_prompt(),
        model_context=RecipientChatCompletionContext(name=["ExecutionAgent"])
    )

    manager = AssistantAgent(
        "ManagerAgent",
        description="Managers have two jobs. One is to analyze user requirement, and the other is to decide the final acceptance.",
        model_client=model_client,
        system_message=get_manager_prompt(),
        model_context=RecipientChatCompletionContext(name=["ManagerAgent"])
    )

    conceptual_reviewer_agent = AssistantAgent(
        "ConceptualReviewerAgent",
        description="Determine whether the current conceptual model satisfies all constraints.",
        model_client=model_client,
        system_message=get_reviewer_prompt(),
    )


    text_mention_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=15)
    termination = text_mention_termination | max_messages_termination


    # for conceptual model design, nested group chat
    inner_termination = TextMentionTermination("Approve") | max_messages_termination
    inner_team = RoundRobinGroupChat([conceptual_designer_agent, conceptual_reviewer_agent], termination_condition=inner_termination)
    society_of_mind_agent = SocietyOfMindAgent("society_of_mind",
                                               description='A team that designs conceptual models based on requirements analysis.',
                                               team=inner_team,
                                               model_client=model_client,
                                               instruction='Earlier you were asked to designs conceptual models. You and your team worked diligently to address that request. Here is a transcript of that conversation:',
                                               response_prompt=get_society_of_mind_prompt()
                                            
                                              )

    team = SelectorGroupChat([manager, society_of_mind_agent, logical_designer_agent, qa_agent, execution_agent],
                                 model_client=model_client,
                                 termination_condition=termination,
                                 allow_repeated_speaker=True,
                                 selector_prompt=get_selector_prompt(),
                                 selector_func=selector_func
                             )
        
    save_file_path = f'{args.save_file_dir}/agent_chat_{args.model_name}_for_test.txt'
    save_file_error_path = f'{args.save_file_dir}/agent_chat_error_{args.model_name}.txt'
    save_file_json_path = save_file_path.replace('.txt', '.jsonl')
    with open(args.test_file_path, 'r', encoding='utf-8') as f:
        test_datas = [json.loads(line) for line in f][args.start_pos : args.end_pos]
    
    
    retry_ids = ['67552f0a13602ec03b41a87a']
    
    with open(save_file_path, 'a+') as f:
        for data in test_datas:
            if data['id'] not in retry_ids:
                continue
            
            i = 0
            for i in range(args.retry_times):
                try:
                    captured_output = io.StringIO()
                    original_stdout = sys.stdout
                    sys.stdout = captured_output

                    logger.info(f'---- id:{data["id"]} ----')
                    print(f'---- id:{data["id"]} ----')

                    text = data['question']
                    await Console(team.run_stream(task=text))
                    await team.reset()  
                    output_string = captured_output.getvalue()

                    # save the output to text file
                    f.write(output_string)
                    logger.info(f"Successfully saved to txt format.")
                    # convert the text format to json format
                    data_list = extract_answer_from_sample(output_string)
                    logger.info(f"Successfully converted to json format.")
                    logger.info(data_list)
                    with open(save_file_json_path, 'a+') as json_f:
                        for item in data_list:
                            json_f.write(json.dumps(item, ensure_ascii=False) + '\n')
                    break
                except Exception as e:
                    logger.error("Conversion failed")
                    logger.error(e)
                    continue
                finally:
                    sys.stdout = original_stdout

            if i == args.retry_times - 1:
                logger.error(f"Failed to convert to json format after {args.retry_times} times.")
                with open(save_file_error_path, 'a+') as error_f:
                    error_f.write(f'{data["id"]}\n')
    
    return save_file_path
    
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', default='deepseek')  
    parser.add_argument('--test_file_path', default='../dataset/RSchema/annotation.jsonl')
    parser.add_argument('--save_file_dir', default='../output/agent_txt')
    parser.add_argument('--start_pos', type=int, default=0, help='Start position in dataset')
    parser.add_argument('--end_pos', type=int, default=550, help='End position in dataset (-1 for all)')
    parser.add_argument('--retry_times', type=int, default=3, help='Retry times when failed')
    args = parser.parse_args()
    save_file_chat_path = asyncio.run(main(args))

    logger.info(f"Output has been saved to file: {save_file_chat_path}")



