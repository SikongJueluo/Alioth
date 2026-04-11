from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.core.utils.session_waiter import (
    SessionController,
    session_waiter,
)
from returns.result import Failure

from alioth.utils import (
    add_birthday,
    get_plugin_context_unsafe,
    initialize,
    list_birthdays,
    mark_birthday_sent,
    send_message,
    terminate,
)


@dataclass(frozen=True)
class Birthday:
    id: int
    name: str
    target_session: str
    month: int
    day: int
    message: str
    last_sent_date: Optional[str] = None


_scheduler: Optional[AsyncIOScheduler] = None

_INITIAL_PROMPT = "请提供寿星的名字："

_reminder_state = {
    "name": None,
    "target_session": None,
    "month": None,
    "day": None,
    "message": None,
}


def _reset_state() -> None:
    _reminder_state["name"] = None
    _reminder_state["target_session"] = None
    _reminder_state["month"] = None
    _reminder_state["day"] = None
    _reminder_state["message"] = None


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


@initialize(priority=3)
async def _initialize_birthday_reminder():
    global _scheduler
    ctx = get_plugin_context_unsafe()
    hour = ctx.config.get("check_hour", 8)
    minute = ctx.config.get("check_minute", 0)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_daily_check,
        CronTrigger(hour=hour, minute=minute),
        id="daily_birthday_check",
        replace_existing=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("生日提醒初始化成功...")


@terminate(priority=3)
async def _terminate_birthday_reminder():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None


def _is_valid_date(month_str: str, day_str: str) -> bool:
    try:
        month = int(month_str)
        day = int(day_str)
    except ValueError:
        return False
    if month < 1 or month > 12:
        return False
    max_day = calendar.monthrange(2000, month)[1]
    return 1 <= day <= max_day


def _is_birthday_today(month: int, day: int, today: datetime) -> bool:
    if month == 2 and day == 29 and not calendar.isleap(today.year):
        return today.month == 2 and today.day == 28
    return today.month == month and today.day == day


def _get_due_birthdays(
    birthdays: List[Birthday],
    today: datetime,
) -> List[Birthday]:
    return [b for b in birthdays if _is_birthday_today(b.month, b.day, today)]


async def _send_notification(birthday: Birthday) -> None:
    msg = MessageChain().message(birthday.message)
    ret = await send_message(birthday.target_session, msg)
    if isinstance(ret, Failure):
        logger.error("发送失败：%s", ret.failure())

    logger.info(
        "[占位] 发送至 %s：今天是 %s 的生日 — %s",
        birthday.target_session,
        birthday.name,
        birthday.message,
    )


async def run_daily_check(today: Optional[datetime] = None) -> None:
    today = today or datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    rows = await list_birthdays()
    birthdays = [
        Birthday(
            id=row["id"],
            name=row["name"],
            target_session=row["target_session"],
            month=row["month"],
            day=row["day"],
            message=row["message"],
            last_sent_date=row["last_sent_date"],
        )
        for row in rows
    ]
    due = _get_due_birthdays(birthdays, today)

    if not due:
        logger.info("今天没有生日提醒。")
        return

    for birthday in due:
        if birthday.last_sent_date == today_str:
            logger.info(
                "跳过已发送的生日提醒: %s (last_sent=%s)",
                birthday.name,
                birthday.last_sent_date,
            )
            continue

        await _send_notification(birthday)
        await mark_birthday_sent(birthday.id, today_str)


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
                    f"已记录名字: {user_input}\n请提供发送提醒的对话窗口ID："
                )
            )
        controller.keep(timeout=keep_timeout, reset_timeout=True)
        return

    if _reminder_state["target_session"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供发送提醒的对话窗口ID："))
        else:
            _reminder_state["target_session"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录对话窗口: {user_input}\n请提供生日月份（1-12）："
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
