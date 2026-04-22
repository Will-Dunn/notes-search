import httpx


def embed(base_url: str, model: str, texts: list[str]) -> list[list[float]]:
    embeddings = []
    for text in texts:
        response = httpx.post(
            f"{base_url}/api/embeddings",
            json={"model": model, "prompt": text},
        )
        response.raise_for_status()
        embeddings.append(response.json()["embedding"])
    return embeddings
