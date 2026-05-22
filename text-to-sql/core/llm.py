import sys
import json
import time
import os
import openai
MAX_TRY = 5

# 用来传递外面的字典进来
world_dict = {}

log_path = None
api_trace_json_path = None
total_prompt_tokens = 0
total_response_tokens = 0

# ensure we only print the model banner once per process
_model_banner_printed = False

# ensure we only configure openai (api_key / api_base) once per process
_openai_configured = False


def _configure_openai_from_env():
    """
    Configure the openai client from LLM_* env vars on first use.

    The FastAPI entry point (main.py -> agent_service.py) already calls
    openai.api_key / api_base directly at startup. Standalone entry points
    (e.g. evaluation/run.py) do not, so we lazily configure here using the
    same env vars (LLM_API_KEY, LLM_API_BASE) loaded by start.sh / run.sh.
    Falls back to OPENAI_API_KEY / OPENAI_API_BASE if LLM_* are not set.
    """
    global _openai_configured
    if _openai_configured:
        return

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("LLM_API_BASE") or os.getenv("OPENAI_API_BASE")

    if api_key:
        openai.api_key = api_key
    if api_base:
        openai.api_base = api_base
    openai.api_type = "open_ai"
    openai.api_version = None

    _openai_configured = True


def init_log_path(my_log_path):
    global total_prompt_tokens
    global total_response_tokens
    global log_path
    global api_trace_json_path
    log_path = my_log_path
    total_prompt_tokens = 0
    total_response_tokens = 0
    dir_name = os.path.dirname(log_path)
    os.makedirs(dir_name, exist_ok=True)

    # 另外一个记录api调用的文件
    api_trace_json_path = os.path.join(dir_name, 'api_trace.json')


def api_func(prompt:str, model_name: str = "gpt-4o"):
    global _model_banner_printed

    # Ensure openai.api_key / api_base are set (no-op if already configured by AgentService)
    _configure_openai_from_env()

    # Allow LLM_MODEL from .env to override the caller-supplied model_name
    # (keeps evaluation/run.py consistent with the FastAPI service)
    env_model = os.getenv("LLM_MODEL")
    if env_model:
        model_name = env_model

    if not _model_banner_printed:
        print(f"\nUse OpenAI model: {model_name} (api_base={openai.api_base})\n")
        _model_banner_printed = True

    # max_tokens caps output to avoid unbounded or looping completions (e.g. SQLCoder on chatty prompts)
    # request_timeout fails fast if the backend hangs
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2048,
        request_timeout=120,
    )
    text = response['choices'][0]['message']['content'].strip()
    prompt_token = response['usage']['prompt_tokens']
    response_token = response['usage']['completion_tokens']
    return text, prompt_token, response_token


def safe_call_llm(input_prompt, model_name: str = "gpt-4o", **kwargs) -> str:
    """
    函数功能描述：输入 input_prompt ，返回 模型生成的内容（内部自动错误重试5次，5次错误抛异常）
    """
    global log_path
    global api_trace_json_path
    global total_prompt_tokens
    global total_response_tokens
    global world_dict

    for i in range(5):
        try:
            if log_path is None:
                # print(input_prompt)
                sys_response, prompt_token, response_token = api_func(input_prompt)
                source = kwargs.get('send_to', 'UnknownAgent')
                idx = kwargs.get('idx', 'N/A')
                db_id = kwargs.get('db_id', 'N/A')
                print(f"\n[{source}] idx={idx}, db_id={db_id}\n")
                print(f"sys_response: \n{sys_response}")
                print(f'\nprompt_token,response_token: {prompt_token} {response_token}\n')
            else:
                # check log_path and api_trace_json_path is not None
                if (log_path is None) or (api_trace_json_path is None):
                    raise FileExistsError('log_path or api_trace_json_path is None, init_log_path first!')
                with open(log_path, 'a+', encoding='utf8') as log_fp, open(api_trace_json_path, 'a+', encoding='utf8') as trace_json_fp:
                    print('\n' + f'*'*20 +'\n', file=log_fp)
                    print(input_prompt, file=log_fp)
                    print('\n' + f'='*20 +'\n', file=log_fp)
                    sys_response, prompt_token, response_token = api_func(input_prompt)
                    source = kwargs.get('send_to', 'UnknownAgent')
                    idx = kwargs.get('idx', 'N/A')
                    db_id = kwargs.get('db_id', 'N/A')
                    print(f"[{source}] idx={idx}, db_id={db_id}\n", file=log_fp)
                    print(f"[{source}] idx={idx}, db_id={db_id}")
                    print(sys_response, file=log_fp)
                    print(f'\n prompt_token,response_token: {prompt_token} {response_token}\n', file=log_fp)
                    print(f'prompt_token,response_token: {prompt_token} {response_token}')

                    if len(world_dict) > 0:
                        world_dict = {}
                    
                    if len(kwargs) > 0:
                        world_dict = {}
                        for k, v in kwargs.items():
                            world_dict[k] = v
                    # prompt response to world_dict
                    world_dict['response'] = '\n' + sys_response.strip() + '\n'
                    world_dict['input_prompt'] = input_prompt.strip() + '\n'

                    world_dict['prompt_token'] = prompt_token
                    world_dict['response_token'] = response_token
                    

                    total_prompt_tokens += prompt_token
                    total_response_tokens += response_token

                    world_dict['cur_total_prompt_tokens'] = total_prompt_tokens
                    world_dict['cur_total_response_tokens'] = total_response_tokens

                    # world_dict to json str
                    world_json_str = json.dumps(world_dict, ensure_ascii=False)
                    print(world_json_str, file=trace_json_fp)

                    world_dict = {}
                    world_json_str = ''

                    print(f'\n total_prompt_tokens,total_response_tokens: {total_prompt_tokens} {total_response_tokens}\n', file=log_fp)
                    print(f'total_prompt_tokens,total_response_tokens: {total_prompt_tokens} {total_response_tokens}\n')
            return sys_response
        except Exception as ex:
            print(ex)
            print(f'Request {model_name} failed. try {i} times. Sleep 20 secs.')
            time.sleep(20)

    raise ValueError('safe_call_llm error!')


if __name__ == "__main__":
    res = safe_call_llm('我爸妈结婚为什么不邀请我？')
    print(res)
