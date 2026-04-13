from __future__ import annotations

import calendar
from datetime import datetime
from typing import Iterable, List

from .models import Birthday


def is_valid_date(month_str: str, day_str: str) -> bool:
    try:
        month = int(month_str)
        day = int(day_str)
    except ValueError:
        return False

    if month < 1 or month > 12:
        return False

    max_day = calendar.monthrange(2000, month)[1]
    return 1 <= day <= max_day


def is_birthday_today(month: int, day: int, today: datetime) -> bool:
    if month == 2 and day == 29 and not calendar.isleap(today.year):
        return today.month == 2 and today.day == 28
    return today.month == month and today.day == day


def get_due_birthdays(
    birthdays: Iterable[Birthday],
    today: datetime,
) -> List[Birthday]:
    return [b for b in birthdays if is_birthday_today(b.month, b.day, today)]
