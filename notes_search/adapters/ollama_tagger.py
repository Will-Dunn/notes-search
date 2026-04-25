import json

import httpx

from notes_search.logger import get_logger
from notes_search.ports.tagger import ITagger

logger = get_logger(__name__)


class OllamaTagger(ITagger):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model

    def tag(self, content: str) -> list[str]:
        truncated = content[:2000]
        prompt = (
            "Return a JSON array of lowercase subject tags for this note. Return only a json array no other text. "
            'Example: ["python", "machine-learning"]. Note:\n\n' + truncated
        )
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        text = response.json()["response"]
        try:
            tags = json.loads(text)
            return [t.lower() for t in tags]
        except (json.JSONDecodeError, TypeError):
            logger.warning("Tagger returned unparseable output; proceeding with no tags. Raw: %r", text)
            return []
