"""钉钉待办工具。"""

from __future__ import annotations

from typing import Any, Literal
from urllib.parse import quote
from uuid import uuid4

import requests
from langchain.tools import ToolRuntime
from langchain_core.tools import ToolException, tool
from pydantic import BaseModel, Field

from src.dingding_service.service import DingDingService


class TodoDetailUrl(BaseModel):
    """第三方待办在钉钉客户端中的详情页地址。"""

    # APP端详情页地址，必须是应用自己的页面。
    appUrl: str | None = Field(
        default=None,
        description="APP端详情页URL",
    )

    # PC端详情页地址，必须是应用自己的页面。
    pcUrl: str | None = Field(
        default=None,
        description="PC端详情页URL",
    )


class TodoInput(BaseModel):
    """创建钉钉待办所需的业务参数。"""

    # 待办标题，钉钉接口限制最大长度为1024字节。
    subject: str = Field(
        min_length=1,
        max_length=1024,
        description="待办事项标题，最大长度1024",
    )

    # 截止时间，使用Unix时间戳，单位为毫秒。
    dueTime: int | None = Field(
        default=None,
        description="截止时间，Unix时间戳，单位毫秒",
    )

    # 待办描述，钉钉接口限制最大长度为4096字节。
    description: str | None = Field(
        default=None,
        max_length=4096,
        description="待办备注描述，最大长度4096",
    )

    # 待办优先级，只允许钉钉接口规定的四个值。
    priority: Literal[10, 20, 30, 40] = Field(
        default=20,
        description="优先级：10较低，20普通，30较高，40紧急",
    )

    # 可选的参与人unionId列表，最多100人。
    participantIds: list[str] | None = Field(
        default=None,
        max_length=100,
        description="参与人的unionId列表，最多100人",
    )

    # 第三方待办详情页；当前接口创建工作待办时需要该字段。
    detailUrl: TodoDetailUrl | None = Field(
        default=None,
        description=(
            "第三方待办详情页，包含appUrl或pcUrl；"
            "当前接口创建工作待办时必须提供"
        ),
    )


def _runtime_context(runtime: ToolRuntime) -> dict[str, Any]:
    """读取Agent本次调用携带的运行时上下文。"""

    context = runtime.context

    if isinstance(context, dict):
        return context

    return {}


def _get_sender_user_id(runtime: ToolRuntime) -> str:
    """从当前会话上下文获取发送者的userId。"""

    context = _runtime_context(runtime)

    # senderStaffId是通讯录接口所需的企业用户ID；senderId仅作缺少该字段时的兜底。
    sender_id = (
        str(context.get("sender_staff_id") or "").strip()
        or str(context.get("sender_id") or "").strip()
    )

    if not sender_id:
        raise ToolException(
            "无法识别当前钉钉用户，请通过钉钉消息调用该工具。"
        )

    return sender_id


def _json_response(response: requests.Response, operation: str) -> dict[str, Any]:
    """读取钉钉JSON响应，并统一处理HTTP及JSON格式错误。"""

    try:
        payload = response.json()
    except ValueError as exc:
        raise ToolException(
            f"{operation}失败：钉钉返回了非JSON响应（HTTP {response.status_code}）"
        ) from exc

    if not isinstance(payload, dict):
        raise ToolException(f"{operation}失败：钉钉返回格式异常")

    if response.status_code >= 400:
        error_code = payload.get("code") or payload.get("errcode")
        error_message = payload.get("message") or payload.get("errmsg")
        raise ToolException(
            f"{operation}失败：HTTP {response.status_code}，"
            f"错误码={error_code or '未知'}，"
            f"错误信息={error_message or '未知'}"
        )

    return payload


def _get_user_union_id(
    access_token: str,
    sender_user_id: str,
) -> str:
    """通过钉钉userId查询创建待办所需的unionId。"""

    try:
        response = requests.post(
            "https://oapi.dingtalk.com/topapi/v2/user/get",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            params={"access_token": access_token},
            json={
                "userid": sender_user_id,
                "language": "zh_CN",
            },
            timeout=(3, 8),
        )
    except requests.RequestException as exc:
        raise ToolException("查询钉钉用户unionId失败：网络请求异常") from exc

    payload = _json_response(response, "查询钉钉用户unionId")

    # topapi接口使用errcode/errmsg表示业务结果，即使HTTP状态为200也要检查。
    if payload.get("errcode") not in (None, 0, "0"):
        raise ToolException(
            "查询钉钉用户unionId失败："
            f"错误码={payload.get('errcode')}，"
            f"错误信息={payload.get('errmsg', '未知')}"
        )

    result = payload.get("result")

    if not isinstance(result, dict):
        raise ToolException("查询钉钉用户unionId失败：缺少用户结果")

    union_id = str(
        result.get("unionid")
        or result.get("unionId")
        or ""
    ).strip()

    if not union_id:
        raise ToolException("查询钉钉用户unionId失败：响应中没有unionid")

    return union_id


def _build_todo_payload(
    todo: TodoInput,
    union_id: str,
) -> dict[str, Any]:
    """组装钉钉创建工作待办接口的请求体。"""

    payload: dict[str, Any] = {
        # sourceId保证同一个业务任务可以被钉钉幂等识别。
        "sourceId": f"xiaolang-{uuid4().hex}",
        "subject": todo.subject,
        # 当前消息用户作为创建者和默认执行者。
        "creatorId": union_id,
        "executorIds": [union_id],
        "priority": todo.priority,
        "notifyConfigs": {
            "dingNotify": 1,
            "sendAssistantChat": True
        },
        "detailUrl": {
            "appUrl": "",
            "pcUrl": "",
        }
    }

    if todo.dueTime is not None:
        payload["dueTime"] = todo.dueTime

    if todo.description:
        payload["description"] = todo.description

    if todo.participantIds:
        payload["participantIds"] = todo.participantIds

    if todo.detailUrl is None:
        raise ToolException(
            "当前钉钉接口创建工作待办必须提供detailUrl，"
            "请传入detailUrl.appUrl或detailUrl.pcUrl"
        )

    detail_url = todo.detailUrl.model_dump(exclude_none=True)

    if not detail_url:
        raise ToolException(
            "当前钉钉接口创建工作待办必须提供detailUrl.appUrl或detailUrl.pcUrl"
        )

    payload["detailUrl"] = detail_url

    return payload


@tool
def create_dingding_todo(
    todo: TodoInput,
    runtime: ToolRuntime,
) -> str:
    """创建一个钉钉工作待办，并分配给当前发消息的用户。

    当前钉钉接口要求detailUrl.appUrl或detailUrl.pcUrl至少填写一个。
    dueTime使用Unix毫秒时间戳；未提供时创建无截止时间的待办。
    """

    try:
        service_client = DingDingService.get_client()
        access_token = service_client.get_access_token()

        if not access_token:
            raise ToolException("获取钉钉access_token失败")

        sender_user_id = _get_sender_user_id(runtime)
        union_id = _get_user_union_id(access_token, sender_user_id)

        todo_payload = _build_todo_payload(todo, union_id)
        # unionId属于用户身份，不能从DingTalkStreamClient对象上直接读取。
        encoded_union_id = quote(union_id, safe="")

        response = requests.post(
            "https://api.dingtalk.com/v1.0/todo/users/"
            f"{encoded_union_id}/tasks",
            headers={
                "x-acs-dingtalk-access-token": access_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=todo_payload,
            timeout=(3, 8),
        )

        payload = _json_response(response, "创建钉钉待办")
        task_id = payload.get("id") or payload.get("taskId")

        if task_id:
            return f"钉钉待办创建成功，待办ID：{task_id}"

        return "钉钉待办创建成功"

    except ToolException:
        raise
    except requests.RequestException as exc:
        raise ToolException("创建钉钉待办失败：网络请求异常") from exc
    except Exception as exc:
        raise ToolException(
            f"创建钉钉待办失败：{type(exc).__name__}"
        ) from exc


# 工具异常作为工具结果返回给Agent，让Agent可以向用户说明失败原因。
create_dingding_todo.handle_tool_error = True


__all__ = ["TodoInput", "create_dingding_todo"]
