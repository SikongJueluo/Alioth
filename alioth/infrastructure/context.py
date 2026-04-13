from dataclasses import dataclass
from typing import Optional

from astrbot.api import AstrBotConfig
from astrbot.api.star import Context
from returns.maybe import Maybe


@dataclass
class PluginContext:
    star_context: Context
    config: AstrBotConfig


_plugin_context: Optional[PluginContext] = None


def initialize_plugin_context(context: Context, config: AstrBotConfig) -> None:
    global _plugin_context
    _plugin_context = PluginContext(star_context=context, config=config)


def get_plugin_context() -> Maybe[PluginContext]:
    return Maybe.from_optional(_plugin_context)


def get_plugin_context_unsafe() -> PluginContext:
    if _plugin_context is None:
        raise ValueError("plugin context not initialized")
    return _plugin_context
