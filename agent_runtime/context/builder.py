def build_context(task, state):
    constraints = "\n".join(
        f"- {item}" for item in task.constraints
    )

    allowed_actions = "\n".join(
        f"- {item}" for item in task.allowed_actions
    )

    history = "\n".join(
        f"Action: {item['action']}\nResult: {item['result']}"
        for item in state.history[-5:]
    )

    return f"""
TASK:
{task.goal}

URL:
{task.url or "None"}

CONSTRAINTS:
{constraints or "- None"}

ALLOWED ACTIONS:
{allowed_actions or "- None"}

PREVIOUS ACTIONS:
{history or "None"}

LAST RESULT:
{state.last_result or "None"}

You are a controlled agent.

Work ONLY on the task above.

Do not invent another task.
Do not create or modify files.
Do not search the web unless explicitly allowed.
Do not summarize unrelated information.

Choose exactly ONE allowed action.

If you know the answer, immediately use:
{{"action": "finish", "answer": "..."}}

Return ONLY JSON.
"""

