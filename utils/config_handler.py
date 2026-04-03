"""
yaml
k: v
"""
import os
import re
import yaml
from dotenv import load_dotenv
from utils.path_tool import get_abs_path

# 加载 .env 文件
load_dotenv(get_abs_path(".env"))


def _resolve_env_vars(value):
    """递归解析配置值中的环境变量引用 ${VAR_NAME}"""
    if isinstance(value, str):
        # 匹配 ${VAR_NAME} 格式
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, value)
        for match in matches:
            env_value = os.getenv(match, '')
            value = value.replace(f'${{{match}}}', env_value)
        return value
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def load_agent_config(config_path: str=get_abs_path("config/agent.yml"), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return _resolve_env_vars(config)


def load_rag_config(config_path: str=get_abs_path("config/rag.yml"), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return _resolve_env_vars(config)


def load_chroma_config(config_path: str=get_abs_path("config/chroma.yml"), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return _resolve_env_vars(config)


def load_prompts_config(config_path: str=get_abs_path("config/prompts.yml"), encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        return _resolve_env_vars(config)


rag_conf = load_rag_config()
chroma_conf = load_chroma_config()
prompts_conf = load_prompts_config()
agent_conf = load_agent_config()


if __name__ == '__main__':
    # print(rag_conf["chat_model_name"])
    print(chroma_conf)
