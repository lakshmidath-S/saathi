import json
import re
import requests


class OllamaModel:
    def __init__(
        self,
        model: str = "qwen3:14b",
        host: str = "http://localhost:11434",
    ):
        self.model = model
        self.host = host.rstrip("/")

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.host}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 500},
            },
            timeout=300,
        )

        response.raise_for_status()
        data = response.json()

        text = data.get("response", "")

        # Qwen3 models use a thinking mode. If the response field
        # is empty, check the thinking field for useful content.
        if not text.strip() and "thinking" in data:
            thinking = data["thinking"]
            # Try to extract JSON from the thinking content
            json_match = re.search(r'\{[^{}]*\}', thinking)
            if json_match:
                text = json_match.group(0)

        return text

    def generate_action(self, prompt: str) -> dict:
        text = self.generate(prompt)

        # Handle models occasionally wrapping JSON in markdown.
        text = text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "", 1)
            text = text.replace("```", "")
            text = text.strip()

        # Handle <think>...</think> tags that some models produce
        if "<think>" in text:
            # Remove thinking block, keep only the content after it
            parts = text.split("</think>")
            if len(parts) > 1:
                text = parts[-1].strip()
            else:
                # No closing tag, try to find JSON anywhere
                pass

        # Try to find JSON object in the text
        if not text.startswith("{"):
            json_match = re.search(r'\{[^{}]*\}', text)
            if json_match:
                text = json_match.group(0)

        return json.loads(text)
