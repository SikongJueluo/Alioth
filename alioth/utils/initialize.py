import inspect
from functools import wraps
from typing import Callable, List, Optional, TypeVar, cast


class InitializationRegistry:
    def __init__(self):
        self._functions: List[Callable] = []

    def register(self, func: Callable) -> Callable:
        self._functions.append(func)
        return func

    def _sorted_functions(self) -> List[Callable]:
        return sorted(
            self._functions,
            key=lambda func: getattr(func, "_init_priority", 0),
        )

    def run_all(self):
        for func in self._sorted_functions():
            if inspect.iscoroutinefunction(func):
                raise RuntimeError(
                    "Async initializer registered in synchronous run_all(); "
                    "use run_all_async instead."
                )
            func()

    async def run_all_async(self):
        for func in self._sorted_functions():
            result = func()
            if inspect.isawaitable(result):
                await result

    def clear(self):
        self._functions.clear()

    def __iter__(self):
        return iter(self._sorted_functions())


_init_registry = InitializationRegistry()
F = TypeVar("F", bound=Callable)


def initialize(name: Optional[str] = None, priority: int = 0):
    def decorator(func: F) -> F:
        wrapped = cast(F, wraps(func)(func))
        wrapped._init_name = name or func.__name__  # type: ignore[reportFunctionMemberAccess]
        wrapped._init_priority = priority  # type: ignore[reportFunctionMemberAccess]
        _init_registry.register(wrapped)
        return wrapped

    return decorator


def get_init_registry() -> InitializationRegistry:
    return _init_registry


def run_initializations():
    _init_registry.run_all()


async def run_initializations_async():
    await _init_registry.run_all_async()
