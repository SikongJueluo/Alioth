from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.utils.session_waiter import (
    SessionController,
    session_waiter,
)

from alioth.utils.database import (
    add_birthday,
    list_birthdays,
)
from alioth.utils.initialize import initialize


@dataclass(frozen=True)
class Birthday:
    id: int
    name: str
    target_session: str
    month: int
    day: int
    message: str


_reminder_state = {
    "name": None,
    "target_session": None,
    "month": None,
    "day": None,
    "message": None,
}


@initialize()
async def _initialize_birthday_reminder():
    logger.info("生日提醒初始化成功...")


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
    # TODO: 实际发送通知的占位
    logger.info(
        "[占位] 发送至 %s：今天是 %s 的生日 — %s",
        birthday.target_session,
        birthday.name,
        birthday.message,
    )


async def run_daily_check(today: Optional[datetime] = None) -> None:
    today = today or datetime.now()

    rows = await list_birthdays()
    birthdays = [
        Birthday(
            id=row["id"],
            name=row["name"],
            target_session=row["target_session"],
            month=row["month"],
            day=row["day"],
            message=row["message"],
        )
        for row in rows
    ]
    due = _get_due_birthdays(birthdays, today)

    if not due:
        logger.info("今天没有生日提醒。")
        return

    for birthday in due:
        try:
            await _send_notification(birthday)
        except Exception:
            logger.exception("发送失败：%s", birthday.name)


@session_waiter(timeout=120, record_history_chains=False)
async def add_birthday_reminder(controller: SessionController, event: AstrMessageEvent):
    user_input = event.message_str.strip()

    if user_input == "退出":
        await event.send(event.plain_result("已退出生日提醒设置~"))
        controller.stop()
        return

    if _reminder_state["name"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供寿星的名字："))
        else:
            _reminder_state["name"] = user_input
            await event.send(
                event.plain_result(
                    f"已记录名字: {user_input}\n请提供发送提醒的对话窗口ID："
                )
            )
        controller.keep(timeout=120, reset_timeout=True)
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
        controller.keep(timeout=120, reset_timeout=True)
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
        controller.keep(timeout=120, reset_timeout=True)
        return

    if _reminder_state["day"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供生日日期（1-31）："))
        else:
            _reminder_state["day"] = user_input
            await event.send(
                event.plain_result(f"已记录日期: {user_input}\n请提供生日祝福话语：")
            )
        controller.keep(timeout=120, reset_timeout=True)
        return

    if _reminder_state["message"] is None:
        if not user_input:
            await event.send(event.plain_result("请提供生日祝福话语："))
        else:
            month_str = _reminder_state["month"]
            day_str = _reminder_state["day"]

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
                    name=_reminder_state["name"],  # type: ignore[arg-type]
                    target_session=_reminder_state["target_session"],  # type: ignore[arg-type]
                    month=int(month_str),  # type: ignore[arg-type]
                    day=int(day_str),  # type: ignore[arg-type]
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


def _reset_state():
    _reminder_state["name"] = None
    _reminder_state["target_session"] = None
    _reminder_state["month"] = None
    _reminder_state["day"] = None
    _reminder_state["message"] = None
