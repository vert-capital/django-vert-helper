from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from .registry import RegisteredAction, register_action


def helper_action(
    *,
    slug: str,
    name: str,
    description: str = "",
    services: list[str] | tuple[str, ...] | None = None,
    questions: list[dict] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    services = tuple(services or ())

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        function_path = f"{func.__module__}.{func.__name__}"
        register_action(
            RegisteredAction(
                slug=slug,
                name=name,
                description=description,
                services=services,
                function_path=function_path,
                function=func,
                questions=questions,
            )
        )

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator
