from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthCheckResult:
    status: str
    message: str | None = None
