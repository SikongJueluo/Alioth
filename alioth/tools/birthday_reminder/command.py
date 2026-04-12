from __future__ import annotations

# pyright: reportMissingImports=false

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.utils.session_waiter import (
    SessionController,
    session_waiter,
)

from alioth.utils import (
    add_birthday,
    get_plugin_context_unsafe,
)
from alioth.tools.birthday_reminder.common import (
    _INITIAL_PROMPT,
    _TARGET_SESSION_PROMPT,
    _get_state,
    _has_active_state,
    _is_valid_date,
    _reset_state,
)


def _get_session_key(event: AstrMessageEvent) -> str:
    return event.unified_msg_origin


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
    timeout = ctx.config.get("session_timeout", 120)
    waiter = session_waiter(timeout=timeout, record_history_chains=False)
    wrapped_session = waiter(_add_birthday_reminder_session)
    try:
        await event.send(event.plain_result(_INITIAL_PROMPT))
        await wrapped_session(event)
    except Exception:
        _reset_state(session_key)
        raise


async def _add_birthday_reminder_session(
    controller: SessionController,
    event: AstrMessageEvent,
) -> None:
    ctx = get_plugin_context_unsafe()
    keep_timeout = ctx.config.get("session_timeout", 120)
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
            await event.send(event.plain_result(_INITIAL_PROMPT))
        else:
            state["name"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录名字: {user_input}\n{_TARGET_SESSION_PROMPT}"
                )
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if state["target_session"] is None:
        if not user_input:
            await event.send(event.plain_result(_TARGET_SESSION_PROMPT))
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

    if state["message"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供生日祝福话语："))
        else:
            state["message"] = user_input
            month_str = state["month"]
            day_str = state["day"]

            name = state["name"]
            target_session = state["target_session"]

            if (
                name is None
                or target_session is None
                or month_str is None
                or day_str is None
            ):
                logger.error("生日提醒状态异常，保存时存在缺失字段: %s", state)
                await event.send(event.plain_result("设置状态异常，请重新开始。"))
                _reset_state(session_key)
                controller.stop()
                return

            if not _is_valid_date(month_str, day_str):
                await event.send(
                    event.plain_result(
                        f"日期无效：{month_str}月{day_str}日不存在，请重新设置。"
                    )
                )
                _reset_state(session_key)
                controller.stop()
                return

            try:
                row_id = await add_birthday(
                    name=name,
                    target_session=target_session,
                    month=int(month_str),
                    day=int(day_str),
                    message=user_input,
                )
            except Exception:
                logger.exception("保存生日到数据库失败")
                await event.send(event.plain_result("保存失败，请稍后重试。"))
                _reset_state(session_key)
                controller.stop()
                return

            logger.info(
                "生日已保存: name=%s target=%s %s月%s日 (row_id=%d)",
                state["name"],
                state["target_session"],
                month_str,
                day_str,
                row_id,
            )

            confirm_msg = (
                f"生日提醒已设置完成！\n"
                f"名字: {state['name']}\n"
                f"发送至: {state['target_session']}\n"
                f"生日: {month_str}月{day_str}日\n"
                f"祝福: {user_input}"
            )
            await event.send(event.plain_result(confirm_msg))

            _reset_state(session_key)
            controller.stop()
