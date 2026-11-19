"""更新钉钉工作待办的工具。"""

from __future__ import annotations

from urllib.parse import quote

import requests
from langchain.tools import ToolRuntime
from langchain_core.tools import ToolException, tool
from pydantic import BaseModel, Field

from src.dingding_service.service import DingDingService
from src.tools.dingding.To_do import (
    _get_sender_user_id,
    _get_user_union_id,
    _json_response,
)


class TodoContentField(BaseModel):
    """待办内容区的自定义字段。"""

    # 自定义字段的唯一标识。
    fieldKey: str = Field(
        min_length=1,
        description="内容区自定义字段的唯一标识",
    )

    # 自定义字段的显示内容。
    fieldValue: str = Field(
        description="内容区自定义字段的值",
    )


class UpdateTodoInput(BaseModel):
    """更新钉钉待办所需的任务ID和可选字段。"""

    # 待更新的钉钉待办任务ID。
    taskId: str = Field(
        min_length=1,
        description="待更新的钉钉待办任务ID",
    )

    # 待办标题，钉钉接口限制最大长度为1024。
    subject: str | None = Field(
        default=None,
        min_length=1,
        max_length=1024,
        description="待办标题，最大长度1024",
    )

    # 待办描述，钉钉接口限制最大长度为4096。
    description: str | None = Field(
        default=None,
        max_length=4096,
        description="待办描述，最大长度4096",
    )

    # 截止时间，使用Unix时间戳，单位为毫秒。
    dueTime: int | None = Field(
        default=None,
        description="截止时间，Unix时间戳，单位毫秒",
    )

    # 待办完成状态。
    done: bool | None = Field(
        default=None,
        description="待办是否完成；true为完成，false为未完成",
    )

    # 执行人unionId列表，最多1000人。
    executorIds: list[str] | None = Field(
        default=None,
        max_length=1000,
        description="执行人的unionId列表，最多1000人",
    )

    # 参与人unionId列表，最多1000人。
    participantIds: list[str] | None = Field(
        default=None,
        max_length=1000,
        description="参与人的unionId列表，最多1000人",
    )

    # 内容区自定义字段列表。
    contentFieldList: list[TodoContentField] | None = Field(
        default=None,
        description="内容区自定义字段列表",
    )


@tool
def update_dingding_todo(
    todo: UpdateTodoInput,
    runtime: ToolRuntime,
) -> str:
    """更新当前钉钉用户拥有的待办信息或完成状态。

    只修改传入的字段；dueTime使用Unix毫秒时间戳。
    """

    try:
        # 去除模型可能附带的空白，并拒绝空任务ID。
        task_id = todo.taskId.strip()

        if not task_id:
            raise ToolException("更新钉钉待办失败：taskId不能为空")

        # 只发送用户明确提供的更新字段；False和空字符串仍会保留。
        update_payload = todo.model_dump(
            exclude={"taskId"},
            exclude_none=True,
        )

        if not update_payload:
            raise ToolException("更新钉钉待办失败：至少提供一个要更新的字段")

        # 通过服务端应用凭证获取当前有效的访问令牌。
        service_client = DingDingService.get_client()
        access_token = service_client.get_access_token()

        if not access_token:
            raise ToolException("获取钉钉access_token失败")

        # 将钉钉回调中的企业员工ID转换为待办接口要求的unionId。
        sender_user_id = _get_sender_user_id(runtime)
        union_id = _get_user_union_id(access_token, sender_user_id)

        # 当前消息发送者既是资源归属人也是操作者；路径ID需URL编码。
        encoded_union_id = quote(union_id, safe="")
        encoded_task_id = quote(task_id, safe="")

        # 向钉钉发送更新请求并读取接口确认结果。
        response = requests.put(
            "https://api.dingtalk.com/v1.0/todo/users/"
            f"{encoded_union_id}/tasks/{encoded_task_id}",
            headers={
                "x-acs-dingtalk-access-token": access_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            params={"operatorId": union_id},
            json=update_payload,
            timeout=(3, 8),
        )

        payload = _json_response(response, "更新钉钉待办")

        if payload.get("result") is not True:
            raise ToolException("更新钉钉待办失败：钉钉未确认更新成功")

        return f"钉钉待办更新成功，待办ID：{task_id}"

    except ToolException:
        raise
    except requests.RequestException as exc:
        raise ToolException("更新钉钉待办失败：网络请求异常") from exc
    except Exception as exc:
        raise ToolException(
            f"更新钉钉待办失败：{type(exc).__name__}"
        ) from exc


# 工具异常作为工具结果返回给Agent，让Agent可以向用户说明失败原因。
update_dingding_todo.handle_tool_error = True


__all__ = ["TodoContentField", "UpdateTodoInput", "update_dingding_todo"]
