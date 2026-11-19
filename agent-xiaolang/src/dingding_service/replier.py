import asyncio

import requests
from dingtalk_stream import ChatbotMessage


class DingDingReplier:
    """通过本次消息携带的 sessionWebhook 回复当前会话。"""

    async def send_text(
        self,
        text: str,
        message: ChatbotMessage,
    ) -> None:
        """
        对外提供异步方法。

        requests.post 是同步网络请求，
        用 to_thread 放到工作线程执行，
        避免网络等待阻塞事件循环。
        """

        await asyncio.to_thread(
            self._send_text_sync,
            text,
            message,
        )

    def _send_text_sync(
        self,
        text: str,
        message: ChatbotMessage,
    ) -> None:
        """执行实际的 HTTP 请求。"""

        if not message.session_webhook:
            raise ValueError("回调缺少 sessionWebhook")

        payload = {
            "msgtype": "text",
            "text": {
                "content": text,
            },
        }

        # 群聊时 @ 当前发消息的用户。
        # 如果没有企业内部用户标识，就只回复普通文字。
        if (
            str(message.conversation_type) == "2"
            and message.sender_staff_id
        ):
            payload["at"] = {
                "atUserIds": [message.sender_staff_id],
                "isAtAll": False,
            }

        with requests.post(
            message.session_webhook,
            json=payload,
            # 分别设置连接超时、读取响应超时。
            timeout=(3, 8),
            allow_redirects=False,
        ) as response:
            if response.status_code != 200:
                raise RuntimeError(
                    f"钉钉回复HTTP异常：{response.status_code}"
                )

            result = response.json()

        # HTTP成功不等于业务成功，还需要检查errcode。
        if not isinstance(result, dict):
            raise RuntimeError("钉钉响应格式异常")

        if result.get("errcode") != 0:
            raise RuntimeError(
                f"钉钉回复失败，errcode={result.get('errcode')}"
            )