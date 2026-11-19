
from typing import Any, TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

from src.middleware.force_rag import ForceRAGMiddleware
from src.common.llm import getDeepseekModel, getOpenAIModel
from src.prompt.basic import BasicPrompt
from src.tools.RAG_tool import rag_search
from src.tools.Serpapi import serpapi_search
from src.tools.dingding.To_do import create_dingding_todo
from src.tools.dingding.delete_todo import delete_dingding_todo
from src.tools.dingding.update_todo import update_dingding_todo
from src.emotion.Emotion_model import EmotionModel
from src.emotion.Feeling_model import FeelingModel
from src.langSmith import configure_langsmith_tracing
from functools import lru_cache
from src.memory.resdis_memory import RedisMemory


class AgentContext(TypedDict, total=False):
    """Agent本次调用的运行时上下文。"""

    # 钉钉回调中的senderId，仅在没有企业员工ID时用于用户查询兜底。
    sender_id: str

    # 钉钉回调中的senderStaffId，对应通讯录查询所需的企业员工ID。
    sender_staff_id: str

    # Redis 记忆按用户唯一标识和钉钉会话标识共同隔离。
    user_id: str
    session_id: str


class AgentModel:
    """
    小浪助手 Agent 核心类。
    """

    def __init__(self) -> None:
        """初始化 Agent 核心属性。"""

        # 创建 Agent 前加载 LangSmith 配置，使后续调用自动记录追踪。
        configure_langsmith_tracing()

        # 主语言模型：负责理解用户问题、推理和生成回复
        self.llm: ChatOpenAI = getOpenAIModel()

        # 备用语言模型：当主模型不可用时的备选方案
        self.fallback_llm: ChatDeepSeek = getDeepseekModel()

        # 小浪助手自身的回应基调。
        self.feeling: FeelingModel = FeelingModel()

        # 用户情绪分析模块。
        self.emotion: EmotionModel = EmotionModel()

        # Agent 系统提示词，负责生成基础规则、情绪提示和本轮 RAG 上下文。
        self.prompt: BasicPrompt = BasicPrompt(
            emotion_model=self.emotion,
            feeling_model=self.feeling,
        )

        # 每次调用模型前动态注入当前轮次的情绪分析和 RAG 检索结果。
        self.prompt_middleware: Any = self.prompt.middleware()

        # Agent 可调用的工具列表。
        self.tools: list[Any] = [
            serpapi_search,
            rag_search,
            create_dingding_todo,
            update_dingding_todo,
            delete_dingding_todo,
        ]

        # Agent 会话记忆由 Redis 持久化，并在上下文接近上限时生成摘要。
        self.memory: RedisMemory = RedisMemory(llm=self.llm)

        # LangChain / LangGraph Agent 实例
        # 负责协调 LLM、Prompt、Tools、Memory 等模块
        # 显式声明运行时上下文类型，避免默认的None上下文导致调用处类型错误。
        self.agent: CompiledStateGraph[Any, AgentContext, Any, Any] = create_agent(
            # 主模型
            model=self.llm,
            # Agent 可调用的工具
            tools=self.tools,
            # 系统提示词
            system_prompt=self.prompt.base_prompt,
            # 将当前钉钉用户身份传给需要用户上下文的工具。
            context_schema=AgentContext,
            middleware=[
                # 提示词
                self.prompt_middleware,
                # 模型调用失败时自动切换 DeepSeek
                ModelFallbackMiddleware(self.fallback_llm),
                # 从 Redis 恢复历史，超限时压缩，并在 Agent 完成后写回。
                self.memory.middleware(system_prompt=self.prompt.base_prompt),
                # 每轮用户提问先强制调用 RAG
                # ForceRAGMiddleware(tool_name=rag_search.name)
            ],
        )

# lru_cache: Least Recently Used（最近最少使用）：缓存满了，就淘汰最久没有使用的条目
# 同样的参数再次调用函数时，直接返回之前的结果，避免重复执行函数
# maxsize 最多缓存 1 组结果
@lru_cache(maxsize=1)
def get_agent_model() -> AgentModel:
    """创建并复用 Agent，保持不同消息之间的短期记忆。"""

    return AgentModel()
