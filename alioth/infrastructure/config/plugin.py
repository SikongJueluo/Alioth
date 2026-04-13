from __future__ import annotations

# pyright: reportMissingImports=false
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, field_validator

_CONFIG_DEFAULTS = {
    "check_hour": 8,
    "check_minute": 0,
    "session_timeout": 120,
}


class PluginConfig(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    check_hour: int = 8
    check_minute: int = 0
    session_timeout: int = 120

    @field_validator("check_hour", "check_minute", "session_timeout", mode="before")
    @classmethod
    def validate_int_field(cls, value: object) -> int:
        if isinstance(value, bool):
            raise ValueError("必须是整数。")

        try:
            return int(str(value))
        except (TypeError, ValueError) as exc:
            raise ValueError("必须是整数。") from exc

    @field_validator("check_hour")
    @classmethod
    def validate_check_hour(cls, value: int) -> int:
        if not 0 <= value <= 23:
            raise ValueError("必须在 0 到 23 之间。")
        return value

    @field_validator("check_minute")
    @classmethod
    def validate_check_minute(cls, value: int) -> int:
        if not 0 <= value <= 59:
            raise ValueError("必须在 0 到 59 之间。")
        return value

    @field_validator("session_timeout")
    @classmethod
    def validate_session_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("必须大于 0。")
        return value


def parse_plugin_config(raw_config: object) -> PluginConfig:
    return PluginConfig.model_validate(raw_config)
