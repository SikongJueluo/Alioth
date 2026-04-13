from .context import (
    PluginContext,
    get_plugin_context,
    get_plugin_context_unsafe,
    initialize_plugin_context,
)
from .config import PluginConfig, parse_plugin_config
from .database import add_birthday, delete_birthday, list_birthdays, mark_birthday_sent
from .initialization import (
    InitializationContext,
    get_init_registry,
    initialize,
    run_initializations,
    run_initializations_async,
)
from .messaging import send_message
from .metadata import PluginMetadata, plugin_metadata
from .termination import (
    get_term_registry,
    run_terminations,
    run_terminations_async,
    terminate,
)

__all__ = [
    "PluginContext",
    "PluginConfig",
    "PluginMetadata",
    "InitializationContext",
    "add_birthday",
    "delete_birthday",
    "get_init_registry",
    "get_plugin_context",
    "get_plugin_context_unsafe",
    "get_term_registry",
    "initialize",
    "initialize_plugin_context",
    "list_birthdays",
    "mark_birthday_sent",
    "plugin_metadata",
    "parse_plugin_config",
    "run_initializations",
    "run_initializations_async",
    "run_terminations",
    "run_terminations_async",
    "send_message",
    "terminate",
]
