import inspect
from collections.abc import Callable, Iterator
from typing import Optional, Protocol, TypeVar, cast


class TerminatorWithMetadata(Protocol):
    __name__: str
    _term_name: str
    _term_priority: int

    def __call__(self, *args: object) -> object: ...


class TerminationRegistry:
    def __init__(self):
        self._functions: list[TerminatorWithMetadata] = []

    def register(self, func: TerminatorWithMetadata) -> TerminatorWithMetadata:
        self._functions.append(func)
        return func

    def _sorted_functions(self) -> list[TerminatorWithMetadata]:
        return sorted(
            self._functions,
            key=lambda func: getattr(func, "_term_priority", 0),
            reverse=True,
        )

    def run_all(self) -> None:
        for func in self._sorted_functions():
            if inspect.iscoroutinefunction(func):
                raise RuntimeError(
                    "Async terminator registered in synchronous run_all(); "
                    "use run_all_async instead."
                )
            func()

    async def run_all_async(self) -> None:
        for func in self._sorted_functions():
            result = func()
            if inspect.isawaitable(result):
                await result

    def clear(self) -> None:
        self._functions.clear()

    def __iter__(self) -> Iterator[TerminatorWithMetadata]:
        return iter(self._sorted_functions())


_term_registry = TerminationRegistry()
F = TypeVar("F", bound=Callable[..., object])


def terminate(name: Optional[str] = None, priority: int = 0):
    def decorator(func: F) -> F:
        wrapped = cast(TerminatorWithMetadata, cast(object, func))
        wrapped._term_name = name or func.__name__
        wrapped._term_priority = priority
        _term_registry.register(wrapped)
        return cast(F, wrapped)

    return decorator


def get_term_registry() -> TerminationRegistry:
    return _term_registry


def run_terminations() -> None:
    _term_registry.run_all()


async def run_terminations_async() -> None:
    await _term_registry.run_all_async()
