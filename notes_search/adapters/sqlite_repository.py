import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import sqlite_vec

from notes_search.core.models import Chunk, Note, TaggedNote
from notes_search.logger import get_logger
from notes_search.ports.note_repository import INotesRepository

logger = get_logger(__name__)


class SqliteNotesRepository(INotesRepository):
    def __init__(self, db_path: Path, dimensions: int) -> None:
        self._db_path = db_path
        self._dimensions = dimensions
        self._init_db()

    def _load_vec(self, conn: sqlite3.Connection) -> None:
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        self._load_vec(conn)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        self._load_vec(conn)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS notes (
                id           TEXT PRIMARY KEY,
                title        TEXT NOT NULL,
                content      TEXT NOT NULL,
                source_path  TEXT,
                source_type  TEXT NOT NULL,
                is_ocr       INTEGER NOT NULL DEFAULT 0,
                is_generated INTEGER NOT NULL DEFAULT 0,
                created_at   TEXT NOT NULL,
                updated_at   TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id          TEXT PRIMARY KEY,
                note_id     TEXT NOT NULL REFERENCES notes(id),
                content     TEXT NOT NULL,
                chunk_index INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tags (
                id   TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS note_tags (
                note_id TEXT NOT NULL REFERENCES notes(id),
                tag_id  TEXT NOT NULL REFERENCES tags(id),
                PRIMARY KEY (note_id, tag_id)
            );
        """)
        conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS chunk_embeddings "
            f"USING vec0(embedding float[{self._dimensions}])"
        )
        conn.commit()
        conn.close()
        logger.info("DB initialised at %s", self._db_path)

    def save_note(self, note: Note) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO notes (id, title, content, source_path, source_type, "
                "is_ocr, is_generated, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    note.id, note.title, note.content, note.source_path,
                    note.source_type, int(note.is_ocr), int(note.is_generated),
                    note.created_at, note.updated_at,
                ),
            )

    def save_chunk(self, chunk: Chunk, embedding: list[float]) -> None:
        with self._get_conn() as conn:
            result = conn.execute(
                "INSERT INTO chunks (id, note_id, content, chunk_index) VALUES (?,?,?,?)",
                (chunk.id, chunk.note_id, chunk.content, chunk.chunk_index),
            )
            chunk_rowid = result.lastrowid
            serialized = sqlite_vec.serialize_float32(embedding)
            conn.execute(
                "INSERT INTO chunk_embeddings(rowid, embedding) VALUES (?,?)",
                (chunk_rowid, serialized),
            )

    def save_tags(self, note_id: str, tags: list[str]) -> None:
        with self._get_conn() as conn:
            for tag in tags:
                conn.execute(
                    "INSERT OR IGNORE INTO tags (id, name) VALUES (?,?)", (tag, tag)
                )
                conn.execute(
                    "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?,?)",
                    (note_id, tag),
                )

    def note_exists(self, source_path: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM notes WHERE source_path = ?", (source_path,)
            ).fetchone()
            return row is not None

    def search_chunks(
        self, embedding: list[float], top_k: int
    ) -> list[tuple[Chunk, float]]:
        serialized = sqlite_vec.serialize_float32(embedding)
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT c.id, c.note_id, c.content, c.chunk_index,
                       distance AS score
                FROM chunk_embeddings ce
                JOIN chunks c ON ce.rowid = c.rowid
                WHERE ce.embedding MATCH ? AND ce.k = ?
                ORDER BY distance
                """,
                (serialized, top_k),
            ).fetchall()
        return [
            (
                Chunk(
                    id=row["id"],
                    note_id=row["note_id"],
                    content=row["content"],
                    chunk_index=row["chunk_index"],
                ),
                row["score"],
            )
            for row in rows
        ]
    def get_note_by_id(self, note_id: str, include_tags: bool = False) -> Note | None:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            if row is None:
                return None
            if include_tags:
                tag_rows = conn.execute(
                    "SELECT t.name FROM tags t JOIN note_tags nt ON nt.tag_id = t.id WHERE nt.note_id = ?",
                    (note_id,),
                ).fetchall()
                return TaggedNote(
                    id=row["id"],
                    title=row["title"],
                    content=row["content"],
                    source_path=row["source_path"],
                    source_type=row["source_type"],
                    is_ocr=bool(row["is_ocr"]),
                    is_generated=bool(row["is_generated"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    tags=[r["name"] for r in tag_rows],
                )
            return Note(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                source_path=row["source_path"],
                source_type=row["source_type"],
                is_ocr=bool(row["is_ocr"]),
                is_generated=bool(row["is_generated"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
