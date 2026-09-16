def verify_action(task, action):
    if not isinstance(action, dict):
        return False, "Action must be a JSON object."

    action_name = action.get("action")

    if not action_name:
        return False, "Missing action."

    if not task.can_do(action_name):
        return False, f"Action '{action_name}' is not allowed."

    if action_name == "finish":
        if "answer" not in action:
            return False, "finish requires an answer."

    return True, "ok"
