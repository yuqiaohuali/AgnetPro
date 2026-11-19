
from src.common.filter_answer import filterAnswer
from src.agent.Agent_model import AgentContext, get_agent_model
from src.dingding_service import DingDingService, UserMessage
from src.langSmith import get_langsmith_thread_id


async def handle_message(message: UserMessage) -> str:
    """处理钉钉消息"""

    # 用户输入的问题，最多只取 500 个字符，防止输入过长
    question = message.text[:500]

    try:
        agent_model = get_agent_model()
        # 当前消息发送者身份会由ToolRuntime传递给钉钉待办工具。
        agent_context: AgentContext = {
            "sender_id": message.user.sender_id,
            "sender_staff_id": message.user.staff_id,
            "user_id": message.user.user_key,
            "session_id": message.session_id,
        }
        response = agent_model.agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            # 使用匿名化线程 ID，避免把钉钉用户与会话标识发送到 LangSmith。
            config={
                "configurable": {
                    "thread_id": get_langsmith_thread_id(message.session_id),
                },
                "run_name": "xiaolang-agent",
                "tags": ["agent-xiaolang", "dingtalk"],
            },
            # 将消息发送者身份传给创建钉钉待办的工具。
            context=agent_context,
        )
        answer = filterAnswer(response["messages"][-1].content)
    except Exception as e:
        raise RuntimeError(f"Agent 处理失败: {e}") from e

    return (
        f"你好，{message.user.nickname}！我是小浪助手。\n"
        f"{answer}"
    )


def main() -> None:
    """启动钉钉服务。"""

    dingding = DingDingService(
        on_message=handle_message,
    )

    try:
        dingding.start()
    except KeyboardInterrupt:
        dingding.logger.info("小浪助手已停止。")


if __name__ == "__main__":
    main()
