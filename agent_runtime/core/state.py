from dataclasses import dataclass, field
from .task import Task


@dataclass
class AgentState:
    task: Task
    history: list[dict] = field(default_factory=list)
    last_result: str | None = None

    def record(self, action: str, result: str):
        self.history.append({
            "action": action,
            "result": result,
        })
        self.last_result = result

