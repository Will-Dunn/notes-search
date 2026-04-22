import uuid
from datetime import datetime, timezone
from pathlib import Path

import sqlite_vec
import typer

from notes_search.db import get_conn
from notes_search.logger import get_logger
from notes_search.utils.chunker import chunk_text
from notes_search.utils.embedder import embed
from notes_search.utils.llm_functions import auto_tag

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = (".md", ".txt")


def ingest_command(ctx: typer.Context, path: Path) -> None:
    if not path.is_dir() and path.suffix not in SUPPORTED_EXTENSIONS:
        typer.echo(
            f"Error: unsupported file type '{path.suffix}'. Supported types: {', '.join(SUPPORTED_EXTENSIONS)}",
            err=True,
        )
        raise typer.Exit(1)

    config = ctx.obj["config"]
    files = list(path.rglob("*.md")) + list(path.rglob("*.txt")) if path.is_dir() else [path]

    if not files:
        typer.echo("No eligible files found.", err=True)
        raise typer.Exit(1)

    with get_conn(config.db_path) as conn:
        for file in files:
            if file.suffix not in SUPPORTED_EXTENSIONS:
                continue
            source_path = str(file.resolve())
            existing = conn.execute(
                "SELECT id FROM notes WHERE source_path = ?", (source_path,)
            ).fetchone()
            if existing:
                typer.echo(
                    f"Skipping {file}: already ingested (id={existing['id']}). Use `notes update {file}` to re-process.",
                    err=True,
                )
                continue

            content = file.read_text()
            if content.strip() == "":
                typer.echo(f"Skipping empty file: {file}", err=True)
                continue
            source_type = "markdown" if file.suffix == ".md" else "text"
            now = datetime.now(timezone.utc).isoformat()
            note_id = str(uuid.uuid4())

            conn.execute(
                "INSERT INTO notes (id, title, content, source_path, source_type, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (note_id, file.stem, content, source_path, source_type, now, now),
            )
            logger.info("Ingest started: note_id=%s path=%s", note_id, source_path)

            chunks = chunk_text(content, config.chunk_size, config.chunk_overlap)
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                result = conn.execute(
                    "INSERT INTO chunks (id, note_id, content, chunk_index) VALUES (?, ?, ?, ?)",
                    (chunk_id, note_id, chunk, i),
                )
                chunk_rowid = result.lastrowid
                vectors = embed(config.ollama_base_url, config.embed_model, [chunk])
                serialized = sqlite_vec.serialize_float32(vectors[0])
                conn.execute(
                    "INSERT INTO chunk_embeddings(rowid, embedding) VALUES (?, ?)",
                    (chunk_rowid, serialized),
                )

            tags = auto_tag(config.ollama_base_url, config.llm_model, content)
            for tag in tags:
                conn.execute("INSERT OR IGNORE INTO tags (id, name) VALUES (?, ?)", (tag, tag))
                conn.execute("INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag))

            logger.info(
                "Ingest complete: note_id=%s chunks=%d tags=%s", note_id, len(chunks), tags
            )
            typer.echo(f"Ingested: id={note_id}  title={file.stem}  chunks={len(chunks)}  tags={tags}")
