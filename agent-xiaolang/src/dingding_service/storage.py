import json

from dingtalk_stream import ChatbotMessage

from .model import ChatSession, UserInfo


class UserStorage:
    """
    用户与会话的内存存储。

    当前只用于学习阶段：
    - 程序重启后清空。
    - 多个进程之间不共享。
    - 不包含聊天历史或模型记忆。
    """

    def __init__(self) -> None:
        self.users: dict[str, UserInfo] = {}
        self.sessions: dict[str, ChatSession] = {}

    def get_or_create(
        self,
        message: ChatbotMessage,
    ) -> tuple[UserInfo, ChatSession]:
        """从钉钉消息中获取或创建用户、会话。"""

        sender_id = str(message.sender_id or "")
        staff_id = str(message.sender_staff_id or "")

        conversation_id = str(message.conversation_id or "")
        conversation_type = str(message.conversation_type or "")

        corp_id = str(
            message.sender_corp_id
            or message.chatbot_corp_id
            or ""
        )

        robot_code = str(message.robot_code or "")

        if not sender_id and not staff_id:
            raise ValueError("消息缺少用户身份标识")

        if not conversation_id:
            raise ValueError("消息缺少 conversationId")

        # 优先使用 senderId，缺少时使用 senderStaffId。
        # 同时保留标识类型，避免不同字段的值意外混淆。
        identity = (
            ["senderId", sender_id]
            if sender_id
            else ["staffId", staff_id]
        )

        # 组合机器人、企业及用户身份，生成内部用户key。
        user_key = json.dumps(
            [robot_code, corp_id, *identity],
            ensure_ascii=False,
        )

        # 会话隔离策略：用户 + 会话类型 + 聊天窗口。
        #
        # 同一个用户在私聊和不同群里拥有不同的会话。
        # 同一个群里的不同用户也各自拥有独立会话。
        session_id = json.dumps(
            [user_key, conversation_type, conversation_id],
            ensure_ascii=False,
        )

        user = self.users.get(user_key)

        if user is None:
            user = UserInfo(
                user_key=user_key,
                sender_id=sender_id,
                staff_id=staff_id,
                nickname=str(message.sender_nick or "用户"),
                corp_id=corp_id,
            )

            self.users[user_key] = user
        else:
            # 昵称可能改变，所以收到消息时更新。
            user.nickname = str(
                message.sender_nick or user.nickname
            )
            user.staff_id = staff_id or user.staff_id

        session = self.sessions.get(session_id)

        if session is None:
            session = ChatSession(
                session_id=session_id,
                user_key=user_key,
                conversation_id=conversation_id,
                conversation_type=conversation_type,
            )

            self.sessions[session_id] = session

        return user, session

    def get_user(self, user_key: str) -> UserInfo | None:
        """按内部用户key查询用户。"""
        return self.users.get(user_key)

    def get_all_users(self) -> list[UserInfo]:
        """获取当前内存中的所有用户。"""
        return list(self.users.values())