import pytest
from agent_runtime.tools.browser import BrowserAdapter


@pytest.fixture
def browser():
    b = BrowserAdapter()
    b.start()
    yield b
    b.stop()


def test_navigate_reaches_real_page(browser):
    assert "example.com" in browser.navigate("https://example.com")


def test_extract_returns_nonempty_text(browser):
    browser.navigate("https://example.com")
    text = browser.extract()
    assert len(text) > 0 and "Example Domain" in text


def test_find_locates_known_text(browser):
    browser.navigate("https://example.com")
    assert "Found" in browser.find("Example Domain")


def test_find_reports_missing_text(browser):
    browser.navigate("https://example.com")
    assert "not found" in browser.find("zzz_nonexistent_xyz123")
