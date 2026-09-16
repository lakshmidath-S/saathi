from playwright.sync_api import sync_playwright


class BrowserAdapter:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        return "Browser started"

    def navigate(self, url):
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        return f"Navigated to {self.page.url}"

    def find(self, text):
        locator = self.page.get_by_text(text, exact=False)
        count = locator.count()
        if count > 0:
            return f"Found ({count} matches): {locator.first.text_content().strip()[:200]}"
        return f"Text '{text}' not found on page."

    def scroll(self, amount=500, **kwargs):
        # Handle case where LLM hallucinates 'pixels' instead of 'amount'
        if 'pixels' in kwargs:
            amount = kwargs['pixels']
        self.page.evaluate(f"window.scrollBy(0, {amount})")
        return f"Scrolled by {amount}px"

    def extract(self, instruction=""):
        return self.page.inner_text("body")[:5000]

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        return "Browser stopped"
