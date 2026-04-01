from typing import List, Optional

import aiosqlite

from alioth.configs import config
from alioth.utils import initialize, terminate

_db: Optional[aiosqlite.Connection] = None


def get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("Database not initialized. Call initialize first.")
    return _db


@initialize(priority=2)
async def _init_database():
    global _db
    db = await aiosqlite.connect(config.database_file_path)
    db.row_factory = aiosqlite.Row
    _db = db
    await _create_tables()


async def _create_tables():
    db = get_db()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS birthdays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_session TEXT NOT NULL,
            month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
            day INTEGER NOT NULL CHECK(day BETWEEN 1 AND 31),
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_sent_date TEXT
        )
    """)
    await db.commit()


# ── Birthdays CRUD ──────────────────────────────────────────────


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


async def list_birthdays() -> List[aiosqlite.Row]:
    db = get_db()
    cursor = await db.execute(
        """
        SELECT id, name, target_session, month, day, message, last_sent_date
        FROM birthdays
        ORDER BY month, day, id
        """
    )
    return list(await cursor.fetchall())


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


@terminate(priority=2)
async def _terminate_database():
    global _db
    if _db is None:
        return
    await _db.close()
