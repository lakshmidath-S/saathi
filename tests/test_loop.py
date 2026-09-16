from agent_runtime.core.task import Task
from agent_runtime.core.state import AgentState
from agent_runtime.core.loop import AgentLoop


class FakeModel:
    def generate_action(self, prompt):
        return {
            "action": "finish",
            "answer": "20",
        }


class FakeTools:
    def execute(self, name, **kwargs):
        raise AssertionError("Tool should not be called when finishing.")


def test_loop_finishes_with_model_answer():
    task = Task(
        goal="Find CPU core count.",
        allowed_actions=["finish"],
    )

    state = AgentState(task)

    loop = AgentLoop(
        task=task,
        model=FakeModel(),
        tools=FakeTools(),
    )

    answer = loop.run(state)

    assert answer == "20"
    assert task.status == "done"
    assert state.last_result == "20"
