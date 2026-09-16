from typing import Callable, Any

from agent_runtime.policy.permissions import (
    TrustLevel,
    check_permission,
)


class ToolRegistry:

    def __init__(self):
        self.tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, function: Callable[..., Any]):
        self.tools[name] = function

    def execute(self, name: str, **kwargs):
        permission = check_permission(name)

        if permission == TrustLevel.BLOCK:
            raise PermissionError(
                f"Tool '{name}' is blocked by policy."
            )

        if permission == TrustLevel.CONFIRM:
            raise PermissionError(
                f"Tool '{name}' requires user confirmation."
            )

        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")

        return self.tools[name](**kwargs)
