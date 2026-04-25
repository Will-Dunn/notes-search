from unittest.mock import MagicMock, patch

from notes_search.adapters.ollama_embedder import OllamaEmbedder


def _mock_response(embedding: list[float]) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {"embedding": embedding}
    return resp


@patch("notes_search.adapters.ollama_embedder.httpx.post")
def test_returns_one_embedding_per_text(mock_post):
    mock_post.return_value = _mock_response([0.1, 0.2, 0.3])
    embedder = OllamaEmbedder("http://localhost:11434", "nomic-embed-text")
    result = embedder.embed(["hello", "world"])
    assert result == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    assert mock_post.call_count == 2


@patch("notes_search.adapters.ollama_embedder.httpx.post")
def test_passes_timeout(mock_post):
    mock_post.return_value = _mock_response([0.0])
    OllamaEmbedder("http://localhost:11434", "nomic-embed-text").embed(["text"])
    _, kwargs = mock_post.call_args
    assert kwargs["timeout"] == 60


@patch("notes_search.adapters.ollama_embedder.httpx.post")
def test_raises_on_http_error(mock_post):
    mock_post.return_value.raise_for_status.side_effect = Exception("500")
    import pytest
    with pytest.raises(Exception, match="500"):
        OllamaEmbedder("http://localhost:11434", "nomic-embed-text").embed(["text"])
