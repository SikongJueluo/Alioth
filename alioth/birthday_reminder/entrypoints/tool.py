from __future__ import annotations

from astrbot.api import logger
from astrbot.api.star import Context
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.astr_agent_context import AstrAgentContext

# pyright: reportMissingImports=false
from pydantic import Field
from pydantic.dataclasses import dataclass

from alioth.birthday_reminder.application.reminder_service import (
    create_birthday_reminder,
)
from alioth.birthday_reminder.domain.prompts import build_creation_confirmation


@dataclass
class AddBirthdayReminderTool(FunctionTool[AstrAgentContext]):
    name: str = "alioth_add_birthday"
    description: str = "添加一个生日提醒记录。需要提供寿星姓名、目标会话标识、生日月份、生日日期和祝福语。"
    parameters: dict = Field(
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
            name = _require_non_empty_string(kwargs, "name")
            target_session = _require_non_empty_string(kwargs, "target_session")
            message = _require_non_empty_string(kwargs, "message")
            month = _parse_int(kwargs, "month")
            day = _parse_int(kwargs, "day")
            row_id = await create_birthday_reminder(
                name=name,
                target_session=target_session,
                month=month,
                day=day,
                message=message,
            )
        except ValueError as exc:
            return str(exc)
        except Exception:
            logger.exception("LLM 工具保存生日提醒失败")
            return "保存生日提醒失败，请稍后重试。"

        logger.info(
            "LLM 工具已保存生日提醒: name=%s target=%s %s月%s日 (row_id=%d)",
            name,
            target_session,
            month,
            day,
            row_id,
        )
        return f"记录 ID: {row_id}\n{build_creation_confirmation(name, target_session, month, day, message)}"


def register_llm_tools(context: Context) -> None:
    context.add_llm_tools(AddBirthdayReminderTool())


def _require_non_empty_string(kwargs: dict[str, object], key: str) -> str:
    value = kwargs.get(key)
    if not isinstance(value, str):
        raise ValueError(f"参数 {key} 必须是非空字符串。")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"参数 {key} 必须是非空字符串。")
    return normalized


def _parse_int(kwargs: dict[str, object], key: str) -> int:
    value = kwargs.get(key)
    if isinstance(value, bool):
        raise ValueError(f"参数 {key} 必须是整数。")

    try:
        return int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"参数 {key} 必须是整数。") from exc
