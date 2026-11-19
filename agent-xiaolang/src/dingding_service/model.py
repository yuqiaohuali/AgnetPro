import asyncio
from dataclasses import dataclass, field


@dataclass
class UserInfo:
    """保存一个用户的基本信息。"""

    # 程序内部生成的用户唯一标识。
    user_key: str

    # 钉钉消息中的 senderId。
    sender_id: str

    # 企业内部用户标识，部分消息场景可能没有。
    staff_id: str

    # 用户昵称，只用于展示，不能作为唯一标识。
    nickname: str

    # 用户所属企业标识。
    corp_id: str


@dataclass
class ChatSession:
    """保存一个用户在某个聊天窗口中的会话信息。"""

    session_id: str
    user_key: str
    conversation_id: str
    conversation_type: str

    # 当前会话成功回复的次数。
    reply_count: int = 0

    # 每个会话一把独立的异步锁。
    #
    # 同一会话的消息串行处理，避免计数或后续聊天状态互相覆盖。
    # 不同会话可以并发处理。
    lock: asyncio.Lock = field(
        default_factory=asyncio.Lock,
        repr=False,
    )


@dataclass(frozen=True)
class UserMessage:
    """
    传递给业务层的消息。

    后续 Agent、缓存等类可以使用这个对象，
    无需依赖钉钉 SDK 的 ChatbotMessage。
    """

    # 本次收到的文字。
    text: str

    # 当前发送者的资料。
    user: UserInfo

    # 用于后续隔离不同用户、不同聊天窗口的上下文。
    session_id: str

    # 钉钉聊天窗口标识。
    conversation_id: str

    # "1"：单聊；"2"：群聊。
    conversation_type: str