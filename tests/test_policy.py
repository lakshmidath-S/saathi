from agent_runtime.tools.registry import ToolRegistry


def test_blocked_search():
    registry = ToolRegistry()

    try:
        registry.execute(
            "browser.search",
            query="functional elements"
        )
        assert False, "Search should have been blocked"

    except PermissionError:
        assert True


def test_unknown_tool_blocked():
    registry = ToolRegistry()

    try:
        registry.execute("something.dangerous")
        assert False, "Unknown tool should be blocked"

    except PermissionError:
        assert True
