from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuntimeState:
    jobs_paused: bool = False
