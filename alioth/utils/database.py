from typing import Optional

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


@terminate(priority=2)
async def terminate_database():
    global _db
    if _db is None:
        return
    await _db.close()
