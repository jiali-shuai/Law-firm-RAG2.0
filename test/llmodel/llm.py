from langchain_openai import ChatOpenAI
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, setup_env

setup_env()

CHAT_LLM = ChatOpenAI(
    model="deepseek-chat",
    temperature=0.3,
    openai_api_key=DEEPSEEK_API_KEY,
    openai_api_base=DEEPSEEK_BASE_URL
)

REASONER_LLM = ChatOpenAI(
    model="deepseek-v4-pro",
    temperature=0.7,
    openai_api_key=DEEPSEEK_API_KEY,
    openai_api_base=DEEPSEEK_BASE_URL
)

