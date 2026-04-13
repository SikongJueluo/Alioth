import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar, cast

from astrbot.api import AstrBotConfig
from astrbot.api.star import Context


@dataclass(frozen=True)
class InitializationContext:
    star_context: Context
    config: AstrBotConfig


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

    def _build_initializer_args(
        self,
        func: Callable,
        init_ctx: Optional[InitializationContext],
    ) -> tuple[Any, ...]:
        signature = inspect.signature(func)
        parameters = list(signature.parameters.values())

        if len(parameters) == 0:
            return ()

        if len(parameters) == 1:
            if init_ctx is None:
                init_name = getattr(func, "_init_name", func.__name__)
                raise RuntimeError(
                    f"Initializer '{init_name}' requires InitializationContext, "
                    "but none was provided."
                )
            return (init_ctx,)

        init_name = getattr(func, "_init_name", func.__name__)
        raise RuntimeError(
            f"Initializer '{init_name}' must accept zero or one argument, "
            f"got {len(parameters)}."
        )

    def run_all(self, init_ctx: Optional[InitializationContext] = None) -> None:
        for func in self._sorted_functions():
            if inspect.iscoroutinefunction(func):
                raise RuntimeError(
                    "Async initializer registered in synchronous run_all(); "
                    "use run_all_async instead."
                )
            func(*self._build_initializer_args(func, init_ctx))

    async def run_all_async(
        self,
        init_ctx: Optional[InitializationContext] = None,
    ) -> None:
        for func in self._sorted_functions():
            result = func(*self._build_initializer_args(func, init_ctx))
            if inspect.isawaitable(result):
                await result

    def clear(self) -> None:
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


def run_initializations(init_ctx: Optional[InitializationContext] = None) -> None:
    _init_registry.run_all(init_ctx)


async def run_initializations_async(
    init_ctx: Optional[InitializationContext] = None,
) -> None:
    await _init_registry.run_all_async(init_ctx)
