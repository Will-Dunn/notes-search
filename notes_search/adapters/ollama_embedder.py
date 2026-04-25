import httpx

from notes_search.ports.embedder import IEmbedder


class OllamaEmbedder(IEmbedder):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            response = httpx.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self._model, "prompt": text},
                timeout=60,
            )
            response.raise_for_status()
            embeddings.append(response.json()["embedding"])
        return embeddings
