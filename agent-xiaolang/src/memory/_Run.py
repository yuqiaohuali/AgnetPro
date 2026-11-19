from langchain.tools import ToolRuntime
import json

def _normalize_query(query: str) -> str:
    """规范化问题文本，便于在会话记忆中判断是否重复提问。"""

    return " ".join(query.casefold().split())


def _message_text(message: object) -> str:
    """提取消息文本，兼容字符串和多内容块消息。"""

    #getattr: 对象：要读取属性的对象。属性名：字符串，例如 "name"。默认值：可选，属性不存在时返回；如果不提供，属性不存在会抛出 AttributeError。
    content = getattr(message, "content", "")

    #isinstance: 判断一个对象是否属于某个类型，返回 True 或 False
    if isinstance(content, str):
        return content

    return json.dumps(content, ensure_ascii=False)


def find_memory_result(runtime: ToolRuntime) -> str | None:
    """根据用户原问题查找当前会话中已有的 RAG 工具结果。"""

    state = runtime.state
    messages = (
        state.get("messages", [])
        if isinstance(state, dict)
        else getattr(state, "messages", [])
    )
    human_indices = [
        index
        for index, message in enumerate(messages)
        if getattr(message, "type", "") == "human"
    ]

    if not human_indices:
        return None

    # 使用用户原问题作为缓存键，不使用模型可能改写后的工具 query。
    current_index = human_indices[-1]
    normalized_question = _normalize_query(
        _message_text(messages[current_index])
    )

    # 从当前问题之前的历史问题中倒序查找最近一次已完成的 RAG 结果。
    for index in reversed(human_indices[:-1]):
        if _normalize_query(_message_text(messages[index])) != normalized_question:
            continue

        for following in messages[index + 1:]:
            if getattr(following, "type", "") == "human":
                break

            if (
                getattr(following, "type", "") == "tool"
                and getattr(following, "name", "") == "rag_search"
            ):
                return _message_text(following)

    return None