import inspect
from typing import Callable, List, Optional, TypeVar, cast
from functools import wraps


class TerminationRegistry:
    def __init__(self):
        self._functions: List[Callable] = []

    def register(self, func: Callable) -> Callable:
        self._functions.append(func)
        return func

    def _sorted_functions(self) -> List[Callable]:
        return sorted(
            self._functions,
            key=lambda func: getattr(func, "_term_priority", 0),
            reverse=True,
        )

    def run_all(self):
        for func in self._sorted_functions():
            if inspect.iscoroutinefunction(func):
                raise RuntimeError(
                    "Async terminator registered in synchronous run_all(); "
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
