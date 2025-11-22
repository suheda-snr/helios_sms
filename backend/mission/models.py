from dataclasses import dataclass
from typing import Optional


@dataclass
class Task:
    id: str
    title: str
    description: Optional[str] = None
    projected_seconds: Optional[int] = None
    completed: bool = False


@dataclass
class Mission:
    id: str
    name: str
    max_duration_seconds: Optional[int] = None
    tasks: list = None
    started: bool = False
    paused: bool = False
    elapsed_seconds: int = 0

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
