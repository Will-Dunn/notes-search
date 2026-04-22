from unittest.mock import MagicMock, patch

from notes_search.utils.llm_functions import auto_tag


def _mock_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {"response": text}
    return resp


@patch("notes_search.utils.llm_functions.httpx.post")
def test_valid_json_returns_lowercase_tags(mock_post):
    mock_post.return_value = _mock_response('["Python", "Machine-Learning"]')
    tags = auto_tag("http://localhost:11434", "llama3.1:8b", "some note content")
    assert tags == ["python", "machine-learning"]


@patch("notes_search.utils.llm_functions.httpx.post")
def test_invalid_json_returns_empty_list(mock_post):
    mock_post.return_value = _mock_response("not json at all")
    tags = auto_tag("http://localhost:11434", "llama3.1:8b", "some note content")
    assert tags == []


@patch("notes_search.utils.llm_functions.httpx.post")
def test_passes_timeout(mock_post):
    mock_post.return_value = _mock_response("[]")
    auto_tag("http://localhost:11434", "llama3.1:8b", "content")
    _, kwargs = mock_post.call_args
    assert kwargs["timeout"] == 60


@patch("notes_search.utils.llm_functions.httpx.post")
def test_empty_json_array_returns_empty_list(mock_post):
    mock_post.return_value = _mock_response("[]")
    assert auto_tag("http://localhost:11434", "llama3.1:8b", "content") == []
