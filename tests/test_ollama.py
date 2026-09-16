import pytest

from agent_runtime.models.ollama import OllamaModel


@pytest.mark.integration
def test_qwen_returns_action():
    model = OllamaModel()

    prompt = """
You are an agent controller.

The task is:
Find the total CPU core count of Intel Core i7-14700.

Allowed actions:
- browser.find_text
- browser.scroll
- browser.extract
- finish

Forbidden actions:
- write_file
- search_web
- navigate_to_other_site

Return ONLY valid JSON.

Example:
{"action": "browser.find_text", "target": "Intel Core i7-14700"}
"""

    result = model.generate_action(prompt)

    assert isinstance(result, dict)
    assert "action" in result
    assert result["action"] in {
        "browser.find_text",
        "browser.scroll",
        "browser.extract",
        "finish",
    }
