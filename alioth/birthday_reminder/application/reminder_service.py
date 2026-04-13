from __future__ import annotations

# pyright: reportMissingImports=false

from datetime import datetime
from typing import Optional

from astrbot.api import logger
from astrbot.api.event import MessageChain
from returns.result import Failure

from alioth.birthday_reminder.domain.models import Birthday
from alioth.birthday_reminder.domain.rules import get_due_birthdays, is_valid_date
from alioth.infrastructure.database import (
    add_birthday,
    delete_birthday,
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


async def list_birthday_reminders() -> list[Birthday]:
    return await list_birthdays()


async def delete_birthday_reminder(birthday_id: int) -> Birthday:
    if birthday_id <= 0:
        raise ValueError("birthday_id 必须大于 0。")

    birthdays = await list_birthdays()
    birthday = next((item for item in birthdays if item.id == birthday_id), None)
    if birthday is None:
        raise ValueError(f"未找到 ID 为 {birthday_id} 的生日提醒。")

    deleted = await delete_birthday(birthday_id)
    if not deleted:
        raise RuntimeError("删除生日提醒失败，请稍后重试。")

    return birthday


async def send_birthday_notification(birthday: Birthday) -> bool:
    msg = MessageChain().message(birthday.message)
    ret = await send_message(birthday.target_session, msg)
    if isinstance(ret, Failure):
        logger.error("发送失败：%s", ret.failure())
        return False

    logger.info(
        "发送生日提醒成功: target=%s name=%s",
        birthday.target_session,
        birthday.name,
    )
    return True


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

        sent = await send_birthday_notification(birthday)
        if not sent:
            logger.warning(
                "生日提醒发送失败，保留未发送状态以便后续重试: %s (id=%s)",
                birthday.name,
                birthday.id,
            )
            continue

        await mark_birthday_sent(birthday.id, today_str)
