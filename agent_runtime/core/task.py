from dataclasses import dataclass, field


@dataclass
class Task:
    goal: str
    url: str | None = None
    constraints: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    status: str = "running"

    def can_do(self, action: str) -> bool:
        return action in self.allowed_actions

    def finish(self):
        self.status = "done"
