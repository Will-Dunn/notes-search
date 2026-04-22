from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import typer

from notes_search.commands.ingest_command import ingest_command
from notes_search.config import Config


@pytest.fixture
def config():
    return Config(
        ollama_base_url="http://localhost:11434",
        llm_model="llama3.1:8b",
        embed_model="nomic-embed-text",
        dimensions=768,
        chunk_size=512,
        chunk_overlap=50,
        top_k_chunks=10,
        related_notes_count=5,
        db_path=Path("/tmp/test.db"),
    )


@pytest.fixture
def ctx(config):
    c = MagicMock(spec=typer.Context)
    c.obj = {"config": config}
    return c


def _make_conn(existing_id: str | None = None):
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (
        {"id": existing_id} if existing_id else None
    )
    conn.execute.return_value.lastrowid = 1
    return conn


@contextmanager
def _conn_ctx(conn):
    yield conn


@patch("notes_search.commands.ingest_command.auto_tag", return_value=["tag1"])
@patch("notes_search.commands.ingest_command.embed", return_value=[[0.1] * 768])
@patch("notes_search.commands.ingest_command.sqlite_vec.serialize_float32", return_value=b"vec")
@patch("notes_search.commands.ingest_command.get_conn")
def test_single_file_ingested(mock_get_conn, _ser, _embed, _tag, ctx, tmp_path):
    note = tmp_path / "note.md"
    note.write_text("hello world " * 10)
    conn = _make_conn()
    mock_get_conn.return_value = _conn_ctx(conn)

    ingest_command(ctx, tmp_path / "note.md")

    insert_calls = [str(c) for c in conn.execute.call_args_list]
    assert any("INSERT INTO notes" in s for s in insert_calls)
    assert any("INSERT INTO chunks" in s for s in insert_calls)
    assert any("INSERT INTO chunk_embeddings" in s for s in insert_calls)


@patch("notes_search.commands.ingest_command.auto_tag", return_value=[])
@patch("notes_search.commands.ingest_command.embed", return_value=[[0.1] * 768])
@patch("notes_search.commands.ingest_command.sqlite_vec.serialize_float32", return_value=b"vec")
@patch("notes_search.commands.ingest_command.get_conn")
def test_duplicate_file_is_skipped_not_aborted(mock_get_conn, _ser, _embed, _tag, ctx, tmp_path, capsys):
    note1 = tmp_path / "a.md"
    note2 = tmp_path / "b.md"
    note1.write_text("content a " * 10)
    note2.write_text("content b " * 10)

    conn = MagicMock()
    conn.execute.return_value.lastrowid = 1

    # note1 is a duplicate; note2 is new
    def fetchone_side_effect(*args, **kwargs):
        m = MagicMock()
        if "a.md" in str(args):
            m.fetchone.return_value = {"id": "existing-id"}
        else:
            m.fetchone.return_value = None
        return m

    conn.execute.side_effect = fetchone_side_effect
    mock_get_conn.return_value = _conn_ctx(conn)

    ingest_command(ctx, tmp_path)

    captured = capsys.readouterr()
    assert "Skipping" in captured.err
    assert "a.md" in captured.err
    # note2 should have been ingested — check stdout
    assert "b.md" in captured.out or "Ingested" in captured.out


@patch("notes_search.commands.ingest_command.get_conn")
def test_unsupported_extension_exits(mock_get_conn, ctx, tmp_path):
    bad_file = tmp_path / "note.pdf"
    bad_file.write_text("content")

    with pytest.raises(typer.Exit):
        ingest_command(ctx, bad_file)

    mock_get_conn.assert_not_called()


@patch("notes_search.commands.ingest_command.get_conn")
def test_empty_directory_exits(mock_get_conn, ctx, tmp_path):
    with pytest.raises(typer.Exit):
        ingest_command(ctx, tmp_path)

    mock_get_conn.assert_not_called()
