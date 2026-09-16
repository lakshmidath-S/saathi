from agent_runtime.context.builder import build_context
from agent_runtime.core.task import Task
from agent_runtime.core.state import AgentState


def test_context_contains_task_and_constraints():
    task = Task(
        goal="Find the total CPU core count of Intel Core i7-14700.",
        url="https://en.wikipedia.org/wiki/Raptor_Lake",
        constraints=[
            "Do not search the web.",
            "Do not create or modify files.",
            "Return only the number.",
        ],
        allowed_actions=[
            "navigate",
            "find_text",
            "scroll",
            "finish",
        ],
    )

    state = AgentState(task)

    context = build_context(task, state)

    assert "Intel Core i7-14700" in context
    assert "Do not search the web." in context
    assert "Do not create or modify files." in context
    assert "find_text" in context
    assert "finish" in context
