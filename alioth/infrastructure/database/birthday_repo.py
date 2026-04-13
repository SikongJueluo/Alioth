from __future__ import annotations

from typing import List

from alioth.birthday_reminder.domain.models import Birthday

from .runtime import get_db


async def add_birthday(
    name: str,
    target_session: str,
    month: int,
    day: int,
    message: str,
) -> int:
    db = get_db()
    cursor = await db.execute(
        """
        INSERT INTO birthdays (name, target_session, month, day, message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, target_session, month, day, message),
    )
    await db.commit()
    if cursor.lastrowid is None:
        raise RuntimeError("Failed to insert birthday: no row ID returned")
    return cursor.lastrowid


async def list_birthdays() -> List[Birthday]:
    db = get_db()
    cursor = await db.execute(
        """
        SELECT id, name, target_session, month, day, message, last_sent_date
        FROM birthdays
        ORDER BY month, day, id
        """
    )
    rows = await cursor.fetchall()
    return [
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


async def mark_birthday_sent(birthday_id: int, date_str: str) -> None:
    db = get_db()
    await db.execute(
        "UPDATE birthdays SET last_sent_date = ? WHERE id = ?",
        (date_str, birthday_id),
    )
    await db.commit()


async def delete_birthday(birthday_id: int) -> bool:
    db = get_db()
    cursor = await db.execute("DELETE FROM birthdays WHERE id = ?", (birthday_id,))
    await db.commit()
    return cursor.rowcount > 0
