import hashlib
import json
import logging
from collections.abc import Awaitable, Callable
from threading import Lock
from time import monotonic

from dingtalk_stream import (
    AckMessage,
    CallbackMessage,
    ChatbotHandler,
    ChatbotMessage,
)

from .model import UserMessage
from .replier import DingDingReplier
from .storage import UserStorage


# 定义业务回调的类型：
#
# 输入：UserMessage
# 返回：一个等待后得到 str 的异步对象
#
# 对应函数形式：
# async def handle_message(message: UserMessage) -> str:
#     ...
MessageCallback = Callable[[UserMessage], Awaitable[str]]


class DingDingHandler(ChatbotHandler):
    """连接钉钉回调与外部业务处理函数。"""

    # 钉钉重试窗口内保留已处理消息，避免同一消息重复回复。
    MESSAGE_DEDUP_TTL_SECONDS = 10 * 60

    def __init__(
        self,
        storage: UserStorage,
        replier: DingDingReplier,
        on_message: MessageCallback,
    ) -> None:
        super().__init__()

        self.storage = storage
        self.replier = replier

        # 保存函数引用，现在不执行。
        # 真正收到消息后才会调用这个函数。
        self.on_message = on_message

        self.logger = logging.getLogger("xiaolang.handler")

        # 保存正在处理或已经成功处理的消息 ID。
        self._message_dedup: dict[str, float] = {}
        self._message_dedup_lock = Lock()

    @staticmethod
    def _message_key(
        incoming: ChatbotMessage,
        callback_message: CallbackMessage,
    ) -> str:
        """获取钉钉消息的稳定幂等键。"""

        message_id = str(incoming.message_id or "").strip()

        if message_id:
            return f"msg:{message_id}"

        # 极少数回调没有 msgId 时，使用稳定字段生成备用键。
        fallback = json.dumps(
            {
                "sender_id": incoming.sender_id,
                "conversation_id": incoming.conversation_id,
                "create_at": incoming.create_at,
                "message_type": incoming.message_type,
                "text": incoming.text.content if incoming.text else "",
                "callback_id": callback_message.headers.message_id,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        digest = hashlib.sha256(fallback.encode("utf-8")).hexdigest()
        return f"payload:{digest}"

    def _claim_message(self, message_key: str) -> bool:
        """声明消息处理权，返回 False 表示这是重复回调。"""

        now = monotonic()

        with self._message_dedup_lock:
            expired = [
                key
                for key, timestamp in self._message_dedup.items()
                if now - timestamp >= self.MESSAGE_DEDUP_TTL_SECONDS
            ]

            for key in expired:
                del self._message_dedup[key]

            if message_key in self._message_dedup:
                return False

            # 处理开始时就登记，覆盖并发中的重复回调。
            self._message_dedup[message_key] = now
            return True

    def _finish_message(self, message_key: str, success: bool) -> None:
        """完成消息处理；失败时移除记录以允许钉钉重试。"""

        if success:
            with self._message_dedup_lock:
                self._message_dedup[message_key] = monotonic()
            return

        with self._message_dedup_lock:
            self._message_dedup.pop(message_key, None)

    async def process(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        message: CallbackMessage,
    ) -> tuple[int, str]:
        """SDK收到机器人消息后，自动调用这个方法。"""

        message_key: str | None = None

        try:
            incoming = ChatbotMessage.from_dict(message.data)
            message_key = self._message_key(incoming, message)

            if not self._claim_message(message_key):
                self.logger.info(
                    "忽略钉钉重复回调，消息ID=%s",
                    incoming.message_id or message.headers.message_id,
                )
                return AckMessage.STATUS_OK, "duplicate ignored"

            # 非文字消息没有 text.content，先判断类型。
            if incoming.message_type != "text":
                await self.replier.send_text(
                    "目前仅支持文字消息，请发送文字测试。",
                    incoming,
                )

                return AckMessage.STATUS_OK, "OK"

            text = (
                incoming.text.content
                if incoming.text
                else ""
            ) or ""

            text = text.strip()

            if not text:
                await self.replier.send_text(
                    "请输入一些文字。",
                    incoming,
                )

                return AckMessage.STATUS_OK, "OK"

            # 获取发送者及该发送者对应的聊天会话。
            user, session = self.storage.get_or_create(incoming)

            # 把SDK消息转换成业务层自己的消息对象。
            user_message = UserMessage(
                text=text,
                user=user,
                session_id=session.session_id,
                conversation_id=session.conversation_id,
                conversation_type=session.conversation_type,
            )

            # 同一会话串行处理，其他会话仍然可以并发。
            async with session.lock:
                # 调用main.py传入的业务函数。
                #
                # 钉钉模块不关心回复来自：
                # 固定文字、Agent、缓存还是其他服务。
                reply_text = await self.on_message(user_message)

                if not isinstance(reply_text, str):
                    raise TypeError("业务处理函数必须返回字符串")

                if not reply_text.strip():
                    raise ValueError("业务处理函数返回了空回复")

                await self.replier.send_text(
                    reply_text,
                    incoming,
                )

                # 回复接口确认成功后再更新计数。
                session.reply_count += 1

            self._finish_message(message_key, success=True)

            self.logger.info(
                "当前会话用户：%s；当前会话用户ID：%s；当前会话回复次数=%d",
                user_message.user.nickname,
                user_message.user.sender_id,
                session.reply_count,
            )

            # ACK仅表示回调处理完成。
            # 真正给用户发消息的是上面的send_text。
            return AckMessage.STATUS_OK, "OK"

        except Exception as exc:
            if message_key is not None:
                self._finish_message(message_key, success=False)

            # 不输出完整回调或Webhook，避免日志包含敏感信息。
            self.logger.error(
                "消息处理失败，异常类型=%s",
                type(exc).__name__,
            )

            return (
                AckMessage.STATUS_SYSTEM_EXCEPTION,
                "process failed",
            )
