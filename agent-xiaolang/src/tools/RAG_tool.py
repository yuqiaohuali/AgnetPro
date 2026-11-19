"""RAG LangChain 工具适配层。"""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain.tools import ToolRuntime
from langchain_core.tools import ToolException, tool

from src.memory._Run import find_memory_result
from src.tools.rag.RAG_service import RAGService


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    """首次调用时初始化并复用 RAG 服务。"""

    return RAGService()


@tool(parse_docstring=True)
def rag_search(query: str, runtime: ToolRuntime) -> str:
    """检索本地知识库中的项目文档、制度、业务说明和表格资料。

    当用户询问与知识库相关的具体事实、规则、流程或数据时使用。
    返回候选资料及文件名、页码等来源信息。
    应根据资料回答，并使用 [1]、[2] 等编号引用来源。
    检索结果可能不相关或不充分，不得据此编造答案。

    Args:
        query: 要检索的问题，应包含明确的主题、对象和关键条件。
        runtime: LangGraph 自动注入的当前会话运行时，用于读取会话记忆。
    """

    try:
        # 优先复用当前会话中相同原始问题的检索结果。
        memory_result = find_memory_result(runtime)

        if memory_result is not None:
            logger.info("RAG 命中会话记忆，跳过向量库检索")
            return memory_result

        return get_rag_service().search_context(query)
    except Exception as exc:
        logger.exception("知识库检索失败")

        # 区分“检索失败”和“没有找到相关资料”，避免 Agent 编造答案。
        raise ToolException(
            "知识库检索失败，请稍后重试；不能视为知识库没有相关资料。"
        ) from exc


# 让 ToolException 作为工具结果返回给 Agent，避免异常终止整轮对话。
rag_search.handle_tool_error = True


__all__ = ["RAGService", "get_rag_service", "rag_search"]
