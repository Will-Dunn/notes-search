"""Show vector counts and check for chunks missing embeddings."""
import sqlite3

import sqlite_vec

from notes_search.config import get_config

config = get_config()
conn = sqlite3.connect(config.db_path)
conn.row_factory = sqlite3.Row
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
with conn:
    total_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    total_vectors = conn.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0]

    orphaned_vectors = conn.execute("""
        SELECT COUNT(*) FROM chunk_embeddings ce
        WHERE ce.rowid NOT IN (SELECT rowid FROM chunks)
    """).fetchone()[0]

    chunks_missing_embeddings = conn.execute("""
        SELECT c.id, c.note_id, c.chunk_index
        FROM chunks c
        WHERE c.rowid NOT IN (SELECT rowid FROM chunk_embeddings)
    """).fetchall()

    print(f"Total chunks:           {total_chunks}")
    print(f"Total vectors:          {total_vectors}")
    print(f"Orphaned vectors:       {orphaned_vectors}")
    print(f"Chunks missing vectors: {len(chunks_missing_embeddings)}")

    if chunks_missing_embeddings:
        print("\nChunks without embeddings:")
        for r in chunks_missing_embeddings:
            print(f"  chunk_id={r['id']}  note_id={r['note_id']}  index={r['chunk_index']}")
