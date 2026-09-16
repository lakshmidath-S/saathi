from agent_runtime.core.task import Task
from agent_runtime.planning.verifier import verify_action


def test_verifier_allows_finish():
    task = Task(
        goal="Find CPU core count.",
        allowed_actions=[
            "finish",
        ],
    )

    ok, reason = verify_action(
        task,
        {
            "action": "finish",
            "answer": "20",
        },
    )

    assert ok is True
    assert reason == "ok"


def test_verifier_blocks_unknown_action():
    task = Task(
        goal="Find CPU core count.",
        allowed_actions=[
            "finish",
            "find_text",
        ],
    )

    ok, reason = verify_action(
        task,
        {
            "action": "write_file",
            "file_name": "bad.txt",
        },
    )

    assert ok is False


def test_verifier_blocks_search():
    task = Task(
        goal="Find CPU core count.",
        allowed_actions=[
            "finish",
            "find_text",
            "scroll",
        ],
    )

    ok, reason = verify_action(
        task,
        {
            "action": "search",
            "query": "Raptor Lake",
        },
    )

    assert ok is False
