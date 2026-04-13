from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Birthday


INITIAL_PROMPT = "请提供寿星的名字："
TARGET_SESSION_PROMPT = "请提供发送提醒的会话标识（unified_msg_origin，例如 aiocqhttp:GroupMessage:123456）："


def build_creation_confirmation(
    name: str,
    target_session: str,
    month: int,
    day: int,
    message: str,
) -> str:
    return (
        "生日提醒已设置完成！\n"
        f"名字: {name}\n"
        f"发送至: {target_session}\n"
        f"生日: {month}月{day}日\n"
        f"祝福: {message}"
    )


def build_birthday_list_message(birthdays: Sequence[Birthday]) -> str:
    if not birthdays:
        return "当前没有已设置的生日提醒。"

    parts = [f"当前共有 {len(birthdays)} 条生日提醒："]
    for birthday in birthdays:
        last_sent = birthday.last_sent_date or "未发送"
        parts.append(
            "\n".join(
                [
                    "",
                    f"ID: {birthday.id}",
                    f"名字: {birthday.name}",
                    f"发送至: {birthday.target_session}",
                    f"生日: {birthday.month}月{birthday.day}日",
                    f"祝福: {birthday.message}",
                    f"最近发送: {last_sent}",
                ]
            )
        )
    return "\n".join(parts)


def build_birthday_delete_confirmation(birthday: Birthday) -> str:
    return (
        "生日提醒已删除。\n"
        f"ID: {birthday.id}\n"
        f"名字: {birthday.name}\n"
        f"发送至: {birthday.target_session}\n"
        f"生日: {birthday.month}月{birthday.day}日\n"
        f"祝福: {birthday.message}"
    )
