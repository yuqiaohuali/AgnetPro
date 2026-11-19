import logging
from typing import ClassVar

from dingtalk_stream import (
    ChatbotMessage,
    Credential,
    DingTalkStreamClient,
)

from .config import configure_logging, load_config
from .handler import DingDingHandler, MessageCallback
from .replier import DingDingReplier
from .storage import UserStorage


class _SafeSDKLogger(logging.Logger):
    """
    内部使用的SDK日志器。

    核对的SDK版本会记录包含连接ticket的信息。
    这里不输出SDK原始日志，只保留连接异常提示。

    类名前的下划线表示：这是包内部实现。
    """

    # 与 logging.Logger 保持完整签名，避免 SDK 日志器覆盖方法时类型不兼容。
    def _log(
        self,
        level,
        msg,
        args,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
    ):
        if level >= logging.WARNING:
            logging.getLogger("xiaolang.connection").log(
                level,
                "钉钉SDK连接异常，请检查网络、凭证及Stream配置。",
            )


class DingDingService:
    """
    钉钉服务的对外入口。

    创建实例：
        组装客户端和消息处理器。

    调用start：
        开始建立连接并接收消息。

    仅import此模块不会自动连接钉钉。
    """

    _current_client: ClassVar[DingTalkStreamClient | None] = None

    def __init__(
        self,
        on_message: MessageCallback,
        client_id: str | None = None,
        client_secret: str | None = None,
        storage: UserStorage | None = None,
    ) -> None:
        # 服务内部统一初始化日志、环境变量和默认存储。
        configure_logging()

        configured_client_id, configured_client_secret = load_config()
        client_id = client_id or configured_client_id
        client_secret = client_secret or configured_client_secret

        if not client_id or not client_secret:
            raise ValueError("钉钉Client ID和Client Secret不能为空")

        self.logger = logging.getLogger("xiaolang.service")
        self.storage = storage or UserStorage()

        credential = Credential(
            client_id,
            client_secret,
        )

        self.client: DingTalkStreamClient = DingTalkStreamClient(
            credential,
            logger=_SafeSDKLogger(
                "xiaolang.sdk",
                logging.WARNING,
            ),
        )

        DingDingService._current_client = self.client

        # 回复器属于钉钉接入内部实现，在服务内创建。
        replier = DingDingReplier()

        handler = DingDingHandler(
            storage=self.storage,
            replier=replier,
            on_message=on_message,
        )

        # 注册机器人消息处理器。
        self.client.register_callback_handler(
            ChatbotMessage.TOPIC,
            handler,
        )

    @classmethod
    def get_client(cls) -> DingTalkStreamClient:
        """返回已经创建的钉钉Stream客户端。"""

        if cls._current_client is None:
            raise RuntimeError("DingDingService 尚未初始化")

        return cls._current_client

    def start(self) -> None:
        """
        启动服务并持续运行。

        这是阻塞式入口，程序会在这里保持运行。
        main.py应先创建其他依赖，再最后调用它。
        """

        self.logger.info(
            "正在连接钉钉Stream，请发送文字验证接入。"
        )

        # SDK内部管理事件循环，不要再套asyncio.run。
        self.client.start_forever()
