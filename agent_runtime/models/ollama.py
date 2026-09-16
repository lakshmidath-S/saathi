import json
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
            },
            timeout=120,
        )

        response.raise_for_status()
        return response.json()["response"]

    def generate_action(self, prompt: str) -> dict:
        text = self.generate(prompt)

        # Handle models occasionally wrapping JSON in markdown.
        text = text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "", 1)
            text = text.replace("```", "")
            text = text.strip()

        return json.loads(text)
