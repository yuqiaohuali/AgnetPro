"""删除钉钉工作待办的工具。"""

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


class DeleteTodoInput(BaseModel):
    """删除钉钉待办所需的参数。"""

    # 待删除的钉钉待办任务ID。
    taskId: str = Field(
        min_length=1,
        description="待删除的钉钉待办任务ID",
    )


@tool
def delete_dingding_todo(
    todo: DeleteTodoInput,
    runtime: ToolRuntime,
) -> str:
    """删除当前钉钉用户拥有的待办。

    taskId必须是钉钉返回的待办任务ID。
    """

    try:
        # 去除模型可能附带的空白，并拒绝空任务ID。
        task_id = todo.taskId.strip()

        if not task_id:
            raise ToolException("删除钉钉待办失败：taskId不能为空")

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

        # 向钉钉发送删除请求并读取接口确认结果。
        response = requests.delete(
            "https://api.dingtalk.com/v1.0/todo/users/"
            f"{encoded_union_id}/tasks/{encoded_task_id}",
            headers={
                "x-acs-dingtalk-access-token": access_token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            params={"operatorId": union_id},
            timeout=(3, 8),
        )

        payload = _json_response(response, "删除钉钉待办")

        if payload.get("result") is not True:
            raise ToolException("删除钉钉待办失败：钉钉未确认删除成功")

        return f"钉钉待办删除成功，待办ID：{task_id}"

    except ToolException:
        raise
    except requests.RequestException as exc:
        raise ToolException("删除钉钉待办失败：网络请求异常") from exc
    except Exception as exc:
        raise ToolException(
            f"删除钉钉待办失败：{type(exc).__name__}"
        ) from exc


# 工具异常作为工具结果返回给Agent，让Agent可以向用户说明失败原因。
delete_dingding_todo.handle_tool_error = True


__all__ = ["DeleteTodoInput", "delete_dingding_todo"]
