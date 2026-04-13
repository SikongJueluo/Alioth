from __future__ import annotations

# pyright: reportMissingImports=false

import calendar
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TypedDict

from astrbot.api import logger
from astrbot.api.event import MessageChain
from returns.result import Failure

from alioth.utils import (
    list_birthdays,
    mark_birthday_sent,
    send_message,
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


_INITIAL_PROMPT = "请提供寿星的名字："
_TARGET_SESSION_PROMPT = "请提供发送提醒的会话标识（unified_msg_origin，例如 aiocqhttp:GroupMessage:123456）："


class ReminderState(TypedDict):
    name: str | None
    target_session: str | None
    month: str | None
    day: str | None
    message: str | None


def _new_state() -> ReminderState:
    return {
        "name": None,
        "target_session": None,
        "month": None,
        "day": None,
        "message": None,
    }


_reminder_states: dict[str, ReminderState] = {}


def _has_active_state(session_key: str) -> bool:
    state = _reminder_states.get(session_key)
    if state is None:
        return False
    return any(value is not None for value in state.values())


def _get_state(session_key: str) -> ReminderState:
    state = _reminder_states.get(session_key)
    if state is None:
        state = _new_state()
        _reminder_states[session_key] = state
    return state


def _reset_state(session_key: str) -> None:
    _reminder_states.pop(session_key, None)


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
