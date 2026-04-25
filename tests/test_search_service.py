from unittest.mock import MagicMock

from notes_search.core.models import Chunk, RelatedNote, SearchResult, TaggedNote
from notes_search.core.services.search_service import SearchService
from notes_search.ports.embedder import IEmbedder
from notes_search.ports.note_repository import INotesRepository
from notes_search.ports.synthesizer import ISynthesizer


def _make_note(note_id: str = "note-1") -> TaggedNote:
    return TaggedNote(
        id=note_id, title="Test Note", content="some content",
        source_path="/tmp/note.md", source_type="markdown", tags=["tag1"],
    )


def _make_chunk(note_id: str = "note-1", chunk_id: str = "chunk-1") -> Chunk:
    return Chunk(id=chunk_id, note_id=note_id, content="chunk content", chunk_index=0)


def _make_mocks(chunks=None, note=None):
    repo = MagicMock(spec=INotesRepository)
    embedder = MagicMock(spec=IEmbedder)
    synthesizer = MagicMock(spec=ISynthesizer)

    chunk = _make_chunk() if chunks is None else chunks[0]
    repo.search_chunks.return_value = [(chunk, 0.25)]
    repo.get_note_by_id.return_value = _make_note() if note is None else note
    embedder.embed.return_value = [[0.1] * 768]
    synthesizer.synthesize.return_value = iter(["Hello", " world"])
    return repo, embedder, synthesizer


def test_returns_related_notes():
    repo, embedder, synthesizer = _make_mocks()
    result = SearchService(repo, embedder, synthesizer).search("query")
    assert len(result.related_notes) == 1
    assert result.related_notes[0].note.title == "Test Note"


def test_deduplicates_by_note_id():
    repo = MagicMock(spec=INotesRepository)
    embedder = MagicMock(spec=IEmbedder)
    synthesizer = MagicMock(spec=ISynthesizer)
    chunk_a = _make_chunk(note_id="note-1", chunk_id="c1")
    chunk_b = _make_chunk(note_id="note-1", chunk_id="c2")
    repo.search_chunks.return_value = [(chunk_a, 0.1), (chunk_b, 0.2)]
    repo.get_note_by_id.return_value = _make_note()
    embedder.embed.return_value = [[0.1] * 768]
    synthesizer.synthesize.return_value = iter([])
    result = SearchService(repo, embedder, synthesizer).search("query")
    assert len(result.related_notes) == 1


def test_raw_mode_skips_synthesis():
    repo, embedder, synthesizer = _make_mocks()
    result = SearchService(repo, embedder, synthesizer).search("query", raw=True)
    synthesizer.synthesize.assert_not_called()
    assert result.generated_response is None


def test_synthesis_called_when_not_raw():
    repo, embedder, synthesizer = _make_mocks()
    result = SearchService(repo, embedder, synthesizer).search("query", raw=False)
    synthesizer.synthesize.assert_called_once()
    assert result.generated_response is not None


def test_no_results_skips_synthesis():
    repo = MagicMock(spec=INotesRepository)
    embedder = MagicMock(spec=IEmbedder)
    synthesizer = MagicMock(spec=ISynthesizer)
    repo.search_chunks.return_value = []
    embedder.embed.return_value = [[0.1] * 768]
    result = SearchService(repo, embedder, synthesizer).search("query")
    synthesizer.synthesize.assert_not_called()
    assert result.related_notes == []
