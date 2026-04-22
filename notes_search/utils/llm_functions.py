import json

import httpx

from notes_search.logger import get_logger

logger = get_logger(__name__)


def auto_tag(base_url: str, model: str, content: str) -> list[str]:
    truncated = content[:2000]
    prompt = (
        "Return a JSON array of lowercase subject tags for this note. Return only a json array no other text. "
        'Example: ["python", "machine-learning"]. Note:\n\n' + truncated
    )
    response = httpx.post(
        f"{base_url}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
    )
    response.raise_for_status()
    text = response.json()["response"]
    try:
        tags = json.loads(text)
        return [t.lower() for t in tags]
    except (json.JSONDecodeError, TypeError):
        logger.warning("Tagger returned unparseable output; proceeding with no tags. Raw: %r", text)
        return []
