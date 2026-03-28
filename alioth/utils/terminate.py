from typing import Callable, List, Optional, TypeVar, cast
from functools import wraps


class TerminationRegistry:
    def __init__(self):
        self._functions: List[Callable] = []

    def register(self, func: Callable) -> Callable:
        self._functions.append(func)
        return func

    def run_all(self):
        for func in reversed(self._functions):
            func()

    async def run_all_async(self):
        for func in reversed(self._functions):
            if hasattr(func, "__await__"):
                await func()
            else:
                func()

    def clear(self):
        self._functions.clear()

    def __iter__(self):
        return iter(self._functions)


_term_registry = TerminationRegistry()
F = TypeVar("F", bound=Callable)


def terminate(name: Optional[str] = None, priority: int = 0):
    def decorator(func: F) -> F:
        wrapped = cast(F, wraps(func)(func))
        wrapped._term_name = name or func.__name__  # type: ignore[reportFunctionMemberAccess]
        wrapped._term_priority = priority  # type: ignore[reportFunctionMemberAccess]
        _term_registry.register(wrapped)
        return wrapped

    return decorator


def get_term_registry() -> TerminationRegistry:
    return _term_registry


def run_terminations():
    _term_registry.run_all()


async def run_terminations_async():
    await _term_registry.run_all_async()
