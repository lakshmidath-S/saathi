from agent_runtime.context.builder import build_context
from agent_runtime.planning.verifier import verify_action


class AgentLoop:
    def __init__(self, task, model, tools, max_steps=10):
        self.task = task
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def run(self, state):
        for _ in range(self.max_steps):
            prompt = build_context(self.task, state)

            action = self.model.generate_action(prompt)

            valid, reason = verify_action(
                self.task,
                action,
            )

            if not valid:
                state.record(
                    "rejected",
                    reason,
                )
                continue

            action_name = action["action"]

            if action_name == "finish":
                answer = action["answer"]

                state.record(
                    "finish",
                    str(answer),
                )

                self.task.finish()

                return str(answer)

            if action_name == "find_text":
                tool_name = "browser.find"
            else:
                tool_name = f"browser.{action_name}"

            kwargs = {
                key: value
                for key, value in action.items()
                if key != "action"
            }

            result = self.tools.execute(
                tool_name,
                **kwargs,
            )

            state.record(
                action_name,
                str(result),
            )

        raise RuntimeError(
            "Maximum agent steps reached."
        )
