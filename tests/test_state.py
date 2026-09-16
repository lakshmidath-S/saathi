from agent_runtime.core.task import Task
from agent_runtime.core.state import AgentState


def test_task_blocks_unknown_action():
    task = Task(
        goal="Find CPU cores",
        allowed_actions=[
            "browser.navigate",
            "browser.find_text",
            "browser.extract",
            "finish",
        ],
    )

    assert task.can_do("browser.find_text")
    assert not task.can_do("write_file")
    assert not task.can_do("search_web")


def test_state_records_actions():
    task = Task(
        goal="Find CPU cores",
        allowed_actions=["browser.find_text", "finish"],
    )

    state = AgentState(task)

    state.record(
        "browser.find_text",
        "Found Intel Core i7-14700",
    )

    assert len(state.history) == 1
    assert state.last_result == "Found Intel Core i7-14700"
