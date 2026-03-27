from typing import Callable, List, Optional, TypeVar, cast
from functools import wraps


class InitializationRegistry:
    def __init__(self):
        self._functions: List[Callable] = []

    def register(self, func: Callable) -> Callable:
        self._functions.append(func)
        return func

    def run_all(self):
        for func in self._functions:
            func()

    async def run_all_async(self):
        for func in self._functions:
            if hasattr(func, "__await__"):
                await func()
            else:
                func()

    def clear(self):
        self._functions.clear()

    def __iter__(self):
        return iter(self._functions)


_registry = InitializationRegistry()
F = TypeVar("F", bound=Callable)


def initialize(name: Optional[str] = None, priority: int = 0):
    def decorator(func: F) -> F:
        wrapped = cast(F, wraps(func)(func))
        wrapped._init_name = name or func.__name__  # type: ignore[reportFunctionMemberAccess]
        wrapped._init_priority = priority  # type: ignore[reportFunctionMemberAccess]
        _registry.register(wrapped)
        return wrapped

    return decorator


def get_registry() -> InitializationRegistry:
    return _registry


def run_initializations():
    _registry.run_all()


async def run_initializations_async():
    await _registry.run_all_async()
