from __future__ import annotations

from typing import TypedDict


class ReminderState(TypedDict):
    name: str | None
    target_session: str | None
    month: str | None
    day: str | None
    message: str | None


def new_reminder_state() -> ReminderState:
    return {
        "name": None,
        "target_session": None,
        "month": None,
        "day": None,
        "message": None,
    }
