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
async def init_database():
    global _db
    db = await aiosqlite.connect(config.database_file_path)
    db.row_factory = aiosqlite.Row
    _db = db
    await _create_tables()


async def _create_tables():
    db = get_db()
    await db.executescript("""
        CREATE TABLE IF NOT EXISTS birthday_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remindee_id TEXT NOT NULL,
            group_id TEXT NOT NULL,
            send_time TEXT NOT NULL,
            message_content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    await db.commit()


# ── Birthday Reminder CRUD ──────────────────────────────────────


async def add_birthday_reminder(
    remindee_id: str,
    group_id: str,
    send_time: str,
    message_content: str,
) -> int:
    db = get_db()
    cursor = await db.execute(
        """
        INSERT INTO birthday_reminders (remindee_id, group_id, send_time, message_content)
        VALUES (?, ?, ?, ?)
        """,
        (remindee_id, group_id, send_time, message_content),
    )
    await db.commit()
    if cursor.lastrowid is None:
        raise RuntimeError("Failed to insert birthday reminder: no row ID returned")
    return cursor.lastrowid


async def get_birthday_reminders(
    remindee_id: Optional[str] = None,
) -> List[aiosqlite.Row]:
    db = get_db()
    if remindee_id is not None:
        cursor = await db.execute(
            "SELECT * FROM birthday_reminders WHERE remindee_id = ? ORDER BY send_time",
            (remindee_id,),
        )
    else:
        cursor = await db.execute("SELECT * FROM birthday_reminders ORDER BY send_time")
    return list(await cursor.fetchall())


async def delete_birthday_reminder(reminder_id: int) -> bool:
    db = get_db()
    cursor = await db.execute(
        "DELETE FROM birthday_reminders WHERE id = ?", (reminder_id,)
    )
    await db.commit()
    return cursor.rowcount > 0


@terminate(priority=2)
async def terminate_database():
    global _db
    if _db is None:
        return
    await _db.close()
