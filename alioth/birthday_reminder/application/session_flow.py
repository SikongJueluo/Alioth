from __future__ import annotations

# pyright: reportMissingImports=false
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.utils.session_waiter import SessionController, session_waiter
from pydantic import ValidationError

from alioth.birthday_reminder.domain.models import CreateBirthdayReminderInput
from alioth.birthday_reminder.domain.prompts import (
    INITIAL_PROMPT,
    TARGET_SESSION_PROMPT,
    build_creation_confirmation,
)
from alioth.birthday_reminder.domain.state import ReminderState, new_reminder_state
from alioth.infrastructure.context import get_plugin_context_unsafe

from .reminder_service import create_birthday_reminder

_reminder_states: dict[str, ReminderState] = {}


def _get_session_key(event: AstrMessageEvent) -> str:
    return event.unified_msg_origin


def _has_active_state(session_key: str) -> bool:
    state = _reminder_states.get(session_key)
    if state is None:
        return False
    return any(value is not None for value in state.values())


def _get_state(session_key: str) -> ReminderState:
    state = _reminder_states.get(session_key)
    if state is None:
        state = new_reminder_state()
        _reminder_states[session_key] = state
    return state


def _reset_state(session_key: str) -> None:
    _reminder_states.pop(session_key, None)


async def start_birthday_reminder(event: AstrMessageEvent) -> None:
    session_key = _get_session_key(event)
    if _has_active_state(session_key):
        await event.send(
            event.plain_result(
                "当前会话已有生日提醒设置进行中，请继续输入，或发送“退出”取消后再重新开始。"
            )
        )
        return

    _reset_state(session_key)
    ctx = get_plugin_context_unsafe()
    timeout = ctx.config.session_timeout
    waiter = session_waiter(timeout=timeout, record_history_chains=False)
    wrapped_session = waiter(_add_birthday_reminder_session)
    try:
        await event.send(event.plain_result(INITIAL_PROMPT))
        await wrapped_session(event)
    except Exception:
        _reset_state(session_key)
        raise


async def _add_birthday_reminder_session(
    controller: SessionController,
    event: AstrMessageEvent,
) -> None:
    ctx = get_plugin_context_unsafe()
    keep_timeout = ctx.config.session_timeout
    user_input = event.message_str.strip()
    session_key = _get_session_key(event)
    state = _get_state(session_key)

    if user_input == "退出":
        await event.send(event.plain_result("已退出生日提醒设置~"))
        _reset_state(session_key)
        controller.stop()
        return

    if state["name"] is None:
        if not user_input:
            await event.send(event.plain_result(INITIAL_PROMPT))
        else:
            state["name"] = user_input
            await event.send(
                event.plain_result(f"已记录名字: {user_input}\n{TARGET_SESSION_PROMPT}")
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if state["target_session"] is None:
        if not user_input:
            await event.send(event.plain_result(TARGET_SESSION_PROMPT))
        else:
            state["target_session"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录会话标识: {user_input}\n请提供生日月份（1-12）："
                )
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if state["month"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供生日月份（1-12）："))
        else:
            state["month"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录月份: {user_input}\n请提供生日日期（1-31）："
                )
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if state["day"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供生日日期（1-31）："))
        else:
            state["day"] = user_input
            await event.send(
                event.plain_result(f"已记录日期: {user_input}\n请提供生日祝福话语：")
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if state["message"] is not None:
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if not user_input:
        await event.send(event.plain_result("请提供生日祝福话语："))
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    state["message"] = user_input
    name = state["name"]
    target_session = state["target_session"]
    month_str = state["month"]
    day_str = state["day"]

    if name is None or target_session is None or month_str is None or day_str is None:
        logger.error("生日提醒状态异常，保存时存在缺失字段: %s", state)
        await event.send(event.plain_result("设置状态异常，请重新开始。"))
        _reset_state(session_key)
        controller.stop()
        return

    try:
        payload = CreateBirthdayReminderInput.model_validate(
            {
                "name": name,
                "target_session": target_session,
                "month": month_str,
                "day": day_str,
                "message": user_input,
            }
        )
        row_id = await create_birthday_reminder(
            name=payload.name,
            target_session=payload.target_session,
            month=payload.month,
            day=payload.day,
            message=payload.message,
        )
    except ValidationError as exc:
        await event.send(event.plain_result(_format_validation_error(exc)))
        _reset_state(session_key)
        controller.stop()
        return
    except ValueError as exc:
        await event.send(event.plain_result(str(exc)))
        _reset_state(session_key)
        controller.stop()
        return
    except Exception:
        logger.exception("保存生日到数据库失败")
        await event.send(event.plain_result("保存失败，请稍后重试。"))
        _reset_state(session_key)
        controller.stop()
        return

    logger.info(
        "生日已保存: name=%s target=%s %s月%s日 (row_id=%d)",
        payload.name,
        payload.target_session,
        payload.month,
        payload.day,
        row_id,
    )
    await event.send(
        event.plain_result(
            build_creation_confirmation(
                payload.name,
                payload.target_session,
                payload.month,
                payload.day,
                payload.message,
            )
        )
    )
    _reset_state(session_key)
    controller.stop()


def _format_validation_error(exc: ValidationError) -> str:
    error = exc.errors()[0]
    location = error.get("loc", ())
    field_name = str(location[0]) if location else "参数"
    error_type = error.get("type")

    if error_type == "missing":
        return f"参数 {field_name} 为必填项。"

    return f"参数 {field_name}{error['msg']}"
