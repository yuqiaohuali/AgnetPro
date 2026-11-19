from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage, ToolMessage


class ForceRAGMiddleware(AgentMiddleware):
    """每轮用户提问，要求先调用一次指定的 RAG 工具。"""

    def __init__(self, tool_name: str):
        # 必须是 @tool 注册后的实际名称
        self.tool_name = tool_name

    def _prepare_request(self, request):
        # 只检查最近一条用户消息之后的工具结果。
        # 不能检查整个历史，否则上一轮检索过，
        # 就会导致这一轮不再强制检索。
        rag_called = False

        for message in reversed(request.messages):
            if isinstance(message, HumanMessage):
                break

            if (
                isinstance(message, ToolMessage)
                and message.name == self.tool_name
            ):
                rag_called = True
                break

        if rag_called:
            # 本轮已收到 RAG 工具结果：
            # 允许模型直接回答，也允许它继续调用工具。
            return request.override(tool_choice="auto")

        # 本轮还没有 RAG 结果：
        # 指定模型必须请求调用这个工具。
        return request.override(
            tool_choice={
                "type": "function",
                "function": {"name": self.tool_name},
            }
        )

    def wrap_model_call(self, request, handler):
        """agent.invoke() 使用的同步入口。"""
        return handler(self._prepare_request(request))

    async def awrap_model_call(self, request, handler):
        """agent.ainvoke() 使用的异步入口。"""
        return await handler(self._prepare_request(request))