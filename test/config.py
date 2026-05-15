"""RAG 系统的配置文件"""
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


def get_env(key: str) -> str:
    """从 .env 获取配置，缺失则抛出错误"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"缺少必需配置项: {key}，请在 .env 文件中设置")
    return value


# 模型路径配置
BGE_MODEL_PATH = get_env("BGE_MODEL_PATH")
RERANKER_MODEL_PATH = get_env("RERANKER_MODEL_PATH")

# Milvus 配置
MILVUS_HOST = get_env("MILVUS_HOST")
MILVUS_PORT = get_env("MILVUS_PORT")
MILVUS_URI = f"http://{MILVUS_HOST}:{MILVUS_PORT}"
COLLECTION_NAME = get_env("COLLECTION_NAME")#默认集合

# LLM 配置
DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = get_env("DEEPSEEK_BASE_URL")

# HuggingFace 配置
HF_HOME = get_env("HF_HOME")
HUGGINGFACE_HUB_CACHE = get_env("HUGGINGFACE_HUB_CACHE")
HF_ENDPOINT = get_env("HF_ENDPOINT")
TRANSFORMERS_CACHE = get_env("TRANSFORMERS_CACHE")


def setup_env():
    """设置环境变量"""
    os.environ["HF_HOME"] = HF_HOME
    os.environ["HUGGINGFACE_HUB_CACHE"] = HUGGINGFACE_HUB_CACHE
    os.environ["HF_ENDPOINT"] = HF_ENDPOINT
    os.environ["TRANSFORMERS_CACHE"] = TRANSFORMERS_CACHE
