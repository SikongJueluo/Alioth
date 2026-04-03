from .common import get_plugin_context, get_plugin_context_unsafe
from .database import add_birthday, list_birthdays, mark_birthday_sent
from .initialize import (
    get_init_registry,
    initialize,
    run_initializations,
    run_initializations_async,
)
from .message import send_message
from .terminate import (
    get_term_registry,
    run_terminations,
    run_terminations_async,
    terminate,
)

__all__ = [
    "initialize",
    "terminate",
    "get_init_registry",
    "get_term_registry",
    "run_initializations",
    "run_initializations_async",
    "run_terminations",
    "run_terminations_async",
    "send_message",
    "add_birthday",
    "list_birthdays",
    "mark_birthday_sent",
    "get_plugin_context",
    "get_plugin_context_unsafe",
]
