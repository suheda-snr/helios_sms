from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class Task:
    id: str
    title: str
    description: Optional[str] = None
    projected_seconds: Optional[int] = None
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            description=data.get("description"),
            projected_seconds=data.get("projected_seconds"),
            completed=data.get("completed", False),
        )


@dataclass
class Mission:
    id: str
    name: str
    description: Optional[str] = "No description provided"  # Default value for description
    max_duration_seconds: Optional[int] = None
    tasks: List[Task] = field(default_factory=list)
    started: bool = False
    paused: bool = False
    elapsed_seconds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # replace task objects with dicts
        data["tasks"] = [t.to_dict() for t in self.tasks]
        # computed fields
        data["projected_seconds"] = self.projected_seconds()
        data["progress"] = self.progress()
        data["over_max"] = self.is_over_max()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Mission":
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return cls(
            id=data.get("id"),
            name=data.get("name") or data.get("title") or "",
            description=data.get("description"),  # Handle description field
            max_duration_seconds=data.get("max_duration_seconds"),
            tasks=tasks,
            started=data.get("started", False),
            paused=data.get("paused", False),
            elapsed_seconds=data.get("elapsed_seconds", 0),
        )

    def projected_seconds(self) -> int:
        total = 0
        for t in self.tasks:
            if t.projected_seconds:
                total += int(t.projected_seconds)
        return total

    def progress(self) -> float:
        proj = self.projected_seconds()
        if proj == 0:
            return 0.0
        completed = sum(1 for t in self.tasks if t.completed)
        return round((completed / len(self.tasks)) * 100.0, 2) if self.tasks else 0.0

    def is_over_max(self) -> bool:
        if self.max_duration_seconds is None:
            return False
        return self.projected_seconds() > int(self.max_duration_seconds)
