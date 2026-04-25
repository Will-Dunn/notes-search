import httpx

from notes_search.core.models import Chunk
from notes_search.ports.synthesizer import ISynthesizer


class OllamaSynthesizer(ISynthesizer,):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model
    def summarize(self, relatedChunks: list[Chunk]) -> str:
        prompt = (
                "Summarize the following chunks into a concise summary, include a list of main points and key takeaways. Provide only this information and no other text" +
                "\n\n".join([chunk.content for chunk in relatedChunks])
        )
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        text = response.json()["response"]
        return text

    def answer(self, question: str, relatedChunks: list[Chunk]) -> str:
        prompt = (
                "Provide a detailed answer to the following question based on the provided context. " +
                "question: " + question +
                "\n\n".join([chunk.content for chunk in relatedChunks])
        )
        response = httpx.post(
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        response.raise_for_status()
        text = response.json()["response"]
        return text