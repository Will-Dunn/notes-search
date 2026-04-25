import httpx

from notes_search.core.models import Chunk
from notes_search.ports.synthesizer import ISynthesizer


class OllamaSynthesizer(ISynthesizer):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model

    def synthesize(self, query: str, chunks: list[Chunk]) -> str:
        context = "\n\n".join(chunk.content for chunk in chunks)
        prompt = (
            "Answer the following question using only the context provided. "
            "Be concise and direct. If the context does not contain enough information, say so.\n\n"
            f"Question: {query}\n\n"
            f"Context:\n{context}"
        )
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        response.raise_for_status()
        return response.json()["response"]
