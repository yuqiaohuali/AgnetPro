import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from pydantic import SecretStr


# llm.py 的上三级目录是项目根目录
ROOT_DIR: Path = Path(__file__).resolve().parents[2]

load_dotenv(ROOT_DIR / ".env")

# openai模型
def getOpenAIModel() -> ChatOpenAI:
    """创建模型openai"""
    # OpenAI 密钥，转换为 LangChain 类型定义要求的 SecretStr。
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("请在项目根目录 .env 中配置 OPENAI_API_KEY")

    return ChatOpenAI(
        api_key=SecretStr(openai_api_key),
        model=os.getenv("OPENAI_MODEL_NAME") or "gpt-5.6-sol",
        base_url=os.getenv("OPENAI_BASE_URL"),
        temperature=0,
        timeout=60,
        max_retries=5,
    )

# deepseek模型
def getDeepseekModel() -> ChatDeepSeek:
    """创建模型deepseek"""
    # DeepSeek 密钥，转换为 LangChain 类型定义要求的 SecretStr。
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        raise RuntimeError("请在项目根目录 .env 中配置 DEEPSEEK_API_KEY")

    return ChatDeepSeek(
        api_key=SecretStr(deepseek_api_key),
        model=os.getenv("DEEPSEEK_MODEL_NAME") or "deepseek-v4-flash",
        temperature=0,
        timeout=60,
        max_retries=5,
    )

