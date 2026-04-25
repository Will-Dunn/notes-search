import json
from unittest.mock import MagicMock, patch

from notes_search.adapters.ollama_synthesizer import OllamaSynthesizer
from notes_search.core.models import Chunk


def _make_chunk(content: str = "some context") -> Chunk:
    return Chunk(id="c1", note_id="n1", content=content, chunk_index=0)


def _mock_stream(*payloads: dict) -> MagicMock:
    response = MagicMock()
    response.iter_lines.return_value = [json.dumps(p) for p in payloads]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=response)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


@patch("notes_search.adapters.ollama_synthesizer.httpx.stream")
def test_yields_tokens_in_order(mock_stream):
    mock_stream.return_value = _mock_stream(
        {"response": "Hello", "done": False},
        {"response": " world", "done": True},
    )
    tokens = list(OllamaSynthesizer("http://localhost:11434", "llama3.1:8b").synthesize("q", [_make_chunk()]))
    assert tokens == ["Hello", " world"]


@patch("notes_search.adapters.ollama_synthesizer.httpx.stream")
def test_stops_at_done(mock_stream):
    mock_stream.return_value = _mock_stream(
        {"response": "A", "done": False},
        {"response": "B", "done": True},
        {"response": "C", "done": False},
    )
    tokens = list(OllamaSynthesizer("http://localhost:11434", "llama3.1:8b").synthesize("q", [_make_chunk()]))
    assert tokens == ["A", "B"]


@patch("notes_search.adapters.ollama_synthesizer.httpx.stream")
def test_skips_malformed_json_lines(mock_stream):
    response = MagicMock()
    response.iter_lines.return_value = [
        "not valid json",
        json.dumps({"response": "ok", "done": True}),
    ]
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=response)
    ctx.__exit__ = MagicMock(return_value=False)
    mock_stream.return_value = ctx
    tokens = list(OllamaSynthesizer("http://localhost:11434", "llama3.1:8b").synthesize("q", [_make_chunk()]))
    assert tokens == ["ok"]
