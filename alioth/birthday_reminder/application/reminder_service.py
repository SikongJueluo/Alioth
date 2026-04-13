from __future__ import annotations

from datetime import datetime
from typing import Optional

from astrbot.api import logger
from astrbot.api.event import MessageChain
from returns.result import Failure

from alioth.birthday_reminder.domain.models import Birthday
from alioth.birthday_reminder.domain.rules import get_due_birthdays, is_valid_date
from alioth.infrastructure.database import (
    add_birthday,
    list_birthdays,
    mark_birthday_sent,
)
from alioth.infrastructure.messaging import send_message


async def create_birthday_reminder(
    name: str,
    target_session: str,
    month: int,
    day: int,
    message: str,
) -> int:
    if not is_valid_date(str(month), str(day)):
        raise ValueError(f"日期无效：{month}月{day}日不存在。")

    return await add_birthday(
        name=name,
        target_session=target_session,
        month=month,
        day=day,
        message=message,
    )


async def send_birthday_notification(birthday: Birthday) -> None:
    msg = MessageChain().message(birthday.message)
    ret = await send_message(birthday.target_session, msg)
    if isinstance(ret, Failure):
        logger.error("发送失败：%s", ret.failure())
        return

    logger.info(
        "发送生日提醒成功: target=%s name=%s",
        birthday.target_session,
        birthday.name,
    )


async def run_daily_check(today: Optional[datetime] = None) -> None:
    today = today or datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    due = get_due_birthdays(await list_birthdays(), today)
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

        await send_birthday_notification(birthday)
        await mark_birthday_sent(birthday.id, today_str)
