from dataclasses import dataclass
from typing import Optional

from astrbot.api.star import Star
from returns.maybe import Maybe


@dataclass
class PluginContext:
    star_context: Star._ContextLike


_plugin_context: Optional[PluginContext] = None


def initialize_utils_common(context: Star._ContextLike):
    global _plugin_context
    _plugin_context = PluginContext(star_context=context)


def get_plugin_context() -> Maybe[PluginContext]:
    """
    Get the plugin context.
    """
    return Maybe.from_optional(_plugin_context)


def get_plugin_context_unsafe() -> PluginContext:
    """
    Usually use in initialize function
    Raise ValueError when common utils are not initialized
    """
    if _plugin_context is None:
        raise ValueError("plugin context not initialized")
    return _plugin_context
