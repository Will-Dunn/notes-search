"""Inspect a single note by id or title substring — shows chunks and tags."""
import sqlite3
import sys

import sqlite_vec

from notes_search.config import get_config

if len(sys.argv) < 2:
    print("Usage: uv run python scripts/debug_note.py <note-id-or-title-substring>")
    sys.exit(1)

query = sys.argv[1]
config = get_config()
conn = sqlite3.connect(config.db_path)
conn.row_factory = sqlite3.Row
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
with conn:
    note = conn.execute(
        "SELECT * FROM notes WHERE id = ? OR title LIKE ?",
        (query, f"%{query}%"),
    ).fetchone()

    if not note:
        print(f"No note found matching '{query}'")
        sys.exit(1)

    tags = conn.execute(
        "SELECT t.name FROM tags t JOIN note_tags nt ON nt.tag_id = t.id WHERE nt.note_id = ?",
        (note["id"],),
    ).fetchall()

    chunks = conn.execute(
        """
        SELECT c.chunk_index, c.id AS chunk_id, c.content,
               CASE WHEN ce.rowid IS NOT NULL THEN 'yes' ELSE 'NO' END AS has_embedding
        FROM chunks c
        LEFT JOIN chunk_embeddings ce ON ce.rowid = c.rowid
        WHERE c.note_id = ?
        ORDER BY c.chunk_index
        """,
        (note["id"],),
    ).fetchall()

    print(f"ID:          {note['id']}")
    print(f"Title:       {note['title']}")
    print(f"Source:      {note['source_path']}")
    print(f"Type:        {note['source_type']}")
    print(f"OCR:         {bool(note['is_ocr'])}   Generated: {bool(note['is_generated'])}")
    print(f"Created:     {note['created_at'][:19]}")
    print(f"Updated:     {note['updated_at'][:19]}")
    print(f"Tags:        {', '.join(r['name'] for r in tags) or 'none'}")
    print(f"\nChunks ({len(chunks)}):")
    for c in chunks:
        preview = c["content"].replace("\n", " ")[:80]
        print(f"  [{c['chunk_index']}] embedding={c['has_embedding']}  {preview!r}")
