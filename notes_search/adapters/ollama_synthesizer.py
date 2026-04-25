import json
from typing import Iterator

import httpx

from notes_search.core.models import Chunk
from notes_search.ports.synthesizer import ISynthesizer


class OllamaSynthesizer(ISynthesizer):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model

    def synthesize(self, query: str, chunks: list[Chunk]) -> Iterator[str]:
        context = "\n\n".join(chunk.content for chunk in chunks)
        prompt = (
            "Answer the following question using only the context provided. "
            "Be concise and direct. If the context does not contain enough information, say so.\n\n"
            f"Question: {query}\n\n"
            f"Context:\n{context}"
        )
        with httpx.stream(
            "POST",
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": True},
            timeout=120,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                yield obj["response"]
                if obj.get("done"):
                    break
