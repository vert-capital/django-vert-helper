from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RegisteredAction:
    slug: str
    name: str
    description: str
    services: tuple[str, ...]
    function_path: str
    function: Callable
    questions: list[dict] | None = None


_registered_actions: dict[str, RegisteredAction] = {}


def register_action(action: RegisteredAction) -> None:
    _registered_actions[action.slug] = action


def get_registered_actions() -> dict[str, RegisteredAction]:
    return dict(_registered_actions)


def clear_registered_actions() -> None:
    _registered_actions.clear()
