from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Birthday:
    id: int
    name: str
    target_session: str
    month: int
    day: int
    message: str
    last_sent_date: Optional[str] = None
