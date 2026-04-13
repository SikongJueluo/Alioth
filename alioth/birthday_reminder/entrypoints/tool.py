from __future__ import annotations

from astrbot.api import logger
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext
from typing import Any

# pyright: reportMissingImports=false
from pydantic import Field
from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from alioth.birthday_reminder.application.reminder_service import (
    create_birthday_reminder,
    delete_birthday_reminder,
    list_birthday_reminders,
)
from alioth.birthday_reminder.domain.models import (
    CreateBirthdayReminderInput,
    DeleteBirthdayReminderInput,
    ListBirthdayRemindersInput,
)
from alioth.birthday_reminder.domain.prompts import (
    build_birthday_delete_confirmation,
    build_birthday_list_message,
    build_creation_confirmation,
)
from alioth.infrastructure import llm_tool


@llm_tool()
@dataclass
class CreateBirthdayReminderTool(FunctionTool[AstrAgentContext]):
    name: str = "alioth_add_birthday"
    description: str = "添加一个生日提醒记录。需要提供寿星姓名、目标会话标识、生日月份、生日日期和祝福语。"
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "寿星姓名。"},
                "target_session": {
                    "type": "string",
                    "description": (
                        "要发送生日祝福的 unified_msg_origin，会话标识格式例如 "
                        "aiocqhttp:GroupMessage:123456。"
                    ),
                },
                "month": {"type": "integer", "description": "生日月份，范围 1 到 12。"},
                "day": {
                    "type": "integer",
                    "description": "生日日期，范围 1 到 31，会按自然日期校验。",
                },
                "message": {"type": "string", "description": "生日当天发送的祝福语。"},
            },
            "required": ["name", "target_session", "month", "day", "message"],
        }
    )

    async def call(
        self,
        context: ContextWrapper[AstrAgentContext],
        **kwargs: object,
    ) -> ToolExecResult:
        del context

        try:
            payload = CreateBirthdayReminderInput.model_validate(kwargs)
            row_id = await create_birthday_reminder(
                name=payload.name,
                target_session=payload.target_session,
                month=payload.month,
                day=payload.day,
                message=payload.message,
            )
        except ValidationError as exc:
            return _format_validation_error(exc)
        except ValueError as exc:
            return str(exc)
        except Exception:
            logger.exception("LLM 工具保存生日提醒失败")
            return "保存生日提醒失败，请稍后重试。"

        logger.info(
            "LLM 工具已保存生日提醒: name=%s target=%s %s月%s日 (row_id=%d)",
            payload.name,
            payload.target_session,
            payload.month,
            payload.day,
            row_id,
        )
        return (
            f"记录 ID: {row_id}\n"
            f"{build_creation_confirmation(payload.name, payload.target_session, payload.month, payload.day, payload.message)}"
        )


def _format_validation_error(exc: ValidationError) -> str:
    error = exc.errors()[0]
    location = error.get("loc", ())
    field_name = str(location[0]) if location else "参数"
    error_type = error.get("type")

    if error_type == "missing":
        return f"参数 {field_name} 为必填项。"

    return f"参数 {field_name}{error['msg']}"


@llm_tool()
@dataclass
class ListBirthdayReminderTool(FunctionTool[AstrAgentContext]):
    name: str = "alioth_list_birthdays"
    description: str = "列出当前所有生日提醒记录。"
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {},
        }
    )

    async def call(
        self,
        context: ContextWrapper[AstrAgentContext],
        **kwargs: object,
    ) -> ToolExecResult:
        del context, kwargs

        try:
            _ = ListBirthdayRemindersInput.model_validate({})
            birthdays = await list_birthday_reminders()
        except Exception:
            logger.exception("LLM 工具查询生日提醒失败")
            return "查询生日提醒失败，请稍后重试。"

        return build_birthday_list_message(birthdays)


@llm_tool()
@dataclass
class DeleteBirthdayReminderTool(FunctionTool[AstrAgentContext]):
    name: str = "alioth_delete_birthday"
    description: str = "按 ID 删除一个生日提醒记录。"
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "birthday_id": {
                    "type": "integer",
                    "description": "要删除的生日提醒 ID。",
                }
            },
            "required": ["birthday_id"],
        }
    )

    async def call(
        self,
        context: ContextWrapper[AstrAgentContext],
        **kwargs: object,
    ) -> ToolExecResult:
        del context

        try:
            payload = DeleteBirthdayReminderInput.model_validate(kwargs)
            birthday = await delete_birthday_reminder(payload.birthday_id)
        except ValidationError as exc:
            return _format_validation_error(exc)
        except ValueError as exc:
            return str(exc)
        except Exception:
            logger.exception("LLM 工具删除生日提醒失败")
            return "删除生日提醒失败，请稍后重试。"

        return build_birthday_delete_confirmation(birthday)
