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
    _is_valid_date,
    _reminder_state,
    _reset_state,
)


async def start_birthday_reminder(event: AstrMessageEvent) -> None:
    _reset_state()
    ctx = get_plugin_context_unsafe()
    timeout = ctx.config.get("session_timeout", 120)
    waiter = session_waiter(timeout=timeout, record_history_chains=False)
    wrapped_session = waiter(_add_birthday_reminder_session)
    try:
        await event.send(event.plain_result(_INITIAL_PROMPT))
        await wrapped_session(event)
    except Exception:
        _reset_state()
        raise


async def _add_birthday_reminder_session(
    controller: SessionController,
    event: AstrMessageEvent,
) -> None:
    ctx = get_plugin_context_unsafe()
    keep_timeout = ctx.config.get("session_timeout", 120)
    user_input = event.message_str.strip()

    if user_input == "退出":
        await event.send(event.plain_result("已退出生日提醒设置~"))
        controller.stop()
        return

    if _reminder_state["name"] is None:
        if not user_input:
            await event.send(event.plain_result(_INITIAL_PROMPT))
        else:
            _reminder_state["name"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录名字: {user_input}\n{_TARGET_SESSION_PROMPT}"
                )
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if _reminder_state["target_session"] is None:
        if not user_input:
            await event.send(event.plain_result(_TARGET_SESSION_PROMPT))
        else:
            _reminder_state["target_session"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录会话标识: {user_input}\n请提供生日月份（1-12）："
                )
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if _reminder_state["month"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供生日月份（1-12）："))
        else:
            _reminder_state["month"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录月份: {user_input}\n请提供生日日期（1-31）："
                )
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if _reminder_state["day"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供生日日期（1-31）："))
        else:
            _reminder_state["day"] = user_input
            await event.send(
                event.plain_result(f"已记录日期: {user_input}\n请提供生日祝福话语：")
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if _reminder_state["message"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供生日祝福话语："))
        else:
            month_str = _reminder_state["month"]
            day_str = _reminder_state["day"]

            name = _reminder_state["name"]
            target_session = _reminder_state["target_session"]

            if (
                name is None
                or target_session is None
                or month_str is None
                or day_str is None
            ):
                logger.error(
                    "生日提醒状态异常，保存时存在缺失字段: %s", _reminder_state
                )
                await event.send(event.plain_result("设置状态异常，请重新开始。"))
                _reset_state()
                controller.stop()
                return

            if not _is_valid_date(month_str, day_str):
                await event.send(
                    event.plain_result(
                        f"日期无效：{month_str}月{day_str}日不存在，请重新设置。"
                    )
                )
                _reset_state()
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
                _reset_state()
                controller.stop()
                return

            logger.info(
                "生日已保存: name=%s target=%s %s月%s日 (row_id=%d)",
                _reminder_state["name"],
                _reminder_state["target_session"],
                month_str,
                day_str,
                row_id,
            )

            confirm_msg = (
                f"生日提醒已设置完成！\n"
                f"名字: {_reminder_state['name']}\n"
                f"发送至: {_reminder_state['target_session']}\n"
                f"生日: {month_str}月{day_str}日\n"
                f"祝福: {user_input}"
            )
            await event.send(event.plain_result(confirm_msg))

            _reset_state()
            controller.stop()
