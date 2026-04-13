from typing import Optional

import aiosqlite

from alioth.infrastructure.initialization import initialize
from alioth.infrastructure.paths import get_database_file_path
from alioth.infrastructure.termination import terminate

_db: Optional[aiosqlite.Connection] = None


def get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("Database not initialized. Call initialize first.")
    return _db


@initialize(priority=2)
async def _init_database() -> None:
    global _db
    database_file_path = get_database_file_path()
    database_file_path.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(database_file_path))
    db.row_factory = aiosqlite.Row
    _db = db
    await _create_tables()


async def _create_tables() -> None:
    db = get_db()
    await db.execute(
        """
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
        """
    )
    await db.commit()


@terminate(priority=2)
async def _terminate_database() -> None:
    global _db
    if _db is None:
        return
    await _db.close()
    _db = None
