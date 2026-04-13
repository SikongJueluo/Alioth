from __future__ import annotations

# pyright: reportMissingImports=false
import calendar
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class CreateBirthdayReminderInput(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )

    name: str
    target_session: str
    month: int
    day: int
    message: str

    @field_validator("name", "target_session", "message")
    @classmethod
    def validate_non_empty_string(cls, value: str) -> str:
        if not value:
            raise ValueError("必须是非空字符串。")
        return value

    @field_validator("month", "day", mode="before")
    @classmethod
    def validate_int_field(cls, value: object) -> int:
        if isinstance(value, bool):
            raise ValueError("必须是整数。")

        try:
            return int(str(value))
        except (TypeError, ValueError) as exc:
            raise ValueError("必须是整数。") from exc

    @model_validator(mode="after")
    def validate_date(self) -> CreateBirthdayReminderInput:
        max_day = (
            calendar.monthrange(2000, self.month)[1] if 1 <= self.month <= 12 else 0
        )
        if not 1 <= self.month <= 12:
            raise ValueError("月份必须在 1 到 12 之间。")
        if not 1 <= self.day <= max_day:
            raise ValueError(f"日期无效：{self.month}月{self.day}日不存在。")
        return self


class Birthday(CreateBirthdayReminderInput):
    id: int
    last_sent_date: str | None = None


class ListBirthdayRemindersInput(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        frozen=True,
        extra="forbid",
    )


class DeleteBirthdayReminderInput(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    birthday_id: int

    @field_validator("birthday_id", mode="before")
    @classmethod
    def validate_birthday_id(cls, value: object) -> int:
        if isinstance(value, bool):
            raise ValueError("必须是整数。")

        try:
            birthday_id = int(str(value))
        except (TypeError, ValueError) as exc:
            raise ValueError("必须是整数。") from exc

        if birthday_id <= 0:
            raise ValueError("必须大于 0。")
        return birthday_id
