from unittest.mock import MagicMock

from notes_search.core.services.ingest_service import IngestService
from notes_search.ports.chunker import IChunker
from notes_search.ports.embedder import IEmbedder
from notes_search.ports.note_repository import INotesRepository
from notes_search.ports.tagger import ITagger


def _make_mocks(note_exists=False):
    repo = MagicMock(spec=INotesRepository)
    repo.note_exists.return_value = note_exists
    embedder = MagicMock(spec=IEmbedder)
    embedder.embed.return_value = [[0.1] * 768]
    chunker = MagicMock(spec=IChunker)
    chunker.chunk.return_value = ["chunk one"]
    tagger = MagicMock(spec=ITagger)
    tagger.tag.return_value = ["tag1"]
    return repo, embedder, chunker, tagger


def test_single_file_ingested(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("hello world " * 10)
    repo, embedder, chunker, tagger = _make_mocks()
    service = IngestService(repo, embedder, chunker, tagger)
    ingested, skipped = service.ingest(note)
    assert ingested == 1
    assert skipped == 0
    repo.save_note.assert_called_once()
    repo.save_chunk.assert_called_once()
    repo.save_tags.assert_called_once()


def test_duplicate_file_is_skipped(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("hello world " * 10)
    repo, embedder, chunker, tagger = _make_mocks(note_exists=True)
    service = IngestService(repo, embedder, chunker, tagger)
    ingested, skipped = service.ingest(note)
    assert ingested == 0
    assert skipped == 1
    repo.save_note.assert_not_called()


def test_unsupported_extension_produces_zero_results(tmp_path):
    bad = tmp_path / "note.pdf"
    bad.write_text("content")
    repo, embedder, chunker, tagger = _make_mocks()
    service = IngestService(repo, embedder, chunker, tagger)
    ingested, skipped = service.ingest(bad)
    assert ingested == 0
    assert skipped == 0


def test_empty_directory_produces_zero_results(tmp_path):
    repo, embedder, chunker, tagger = _make_mocks()
    service = IngestService(repo, embedder, chunker, tagger)
    ingested, skipped = service.ingest(tmp_path)
    assert ingested == 0
    assert skipped == 0
