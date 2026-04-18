import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import sqlite_vec

from notes_search.logger import get_logger

logger = get_logger(__name__)


def _load_vec(conn: sqlite3.Connection) -> None:
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)


def init_db(db_path: Path, dimensions: int) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(db_path)
        _load_vec(conn)
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
            f"USING vec0(embedding float[{dimensions}])"
        )
        conn.commit()
    finally:
        conn.close()
    logger.info("DB initialised at %s", db_path)


@contextmanager
def get_conn(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _load_vec(conn)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
