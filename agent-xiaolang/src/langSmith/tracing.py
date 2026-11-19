"""LangSmith 追踪配置。"""

import os
from hashlib import sha256
from pathlib import Path

from dotenv import load_dotenv


# 从当前模块位置计算项目根目录，用于加载项目配置。
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def configure_langsmith_tracing() -> bool:
    """加载 LangSmith 环境配置；启用追踪时校验 API Key。"""

    load_dotenv(PROJECT_ROOT / ".env")

    # 兼容常见布尔写法，默认关闭追踪。
    tracing_value = os.getenv("LANGSMITH_TRACING", "false").strip().lower()
    tracing_enabled = tracing_value in {"1", "true", "yes", "on"}
    if not tracing_enabled:
        return False

    # 启用远端追踪必须配置 LangSmith API Key。
    if not os.getenv("LANGSMITH_API_KEY"):
        raise RuntimeError(
            "已启用 LangSmith 追踪，请在项目根目录 .env 中配置 LANGSMITH_API_KEY"
        )

    # 使用稳定项目路由，避免误走仍处于测试阶段的 Agent Address 路由。
    project_name = os.getenv("LANGSMITH_PROJECT", "agent-xiaolang-local").strip()
    if not project_name:
        project_name = "agent-xiaolang-local"
    os.environ["LANGSMITH_PROJECT"] = project_name
    os.environ.pop("LANGSMITH_AGENT_ID", None)
    os.environ.pop("LANGSMITH_AGENT_ENVIRONMENT", None)

    # LangChain 根据标准环境变量自动将 Agent 运行记录发送到 LangSmith。
    os.environ["LANGSMITH_TRACING"] = "true"
    return True


def get_langsmith_thread_id(session_id: str) -> str:
    """将业务会话标识转换为稳定且不含原始身份信息的线程 ID。"""

    # 原始钉钉会话标识包含身份与会话字段，不直接发送到 LangSmith。
    return sha256(session_id.encode("utf-8")).hexdigest()
