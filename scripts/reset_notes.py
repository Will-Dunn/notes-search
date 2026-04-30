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
    conn.execute("DELETE FROM note_embeddings WHERE 1=1")
    conn.execute("DELETE FROM note_embedding_map WHERE 1=1")
    conn.execute("DELETE FROM chunk_embeddings WHERE 1=1")
    conn.execute("DELETE FROM note_tags WHERE 1=1")
    conn.execute("DELETE FROM chunks WHERE 1=1")
    conn.execute("DELETE FROM notes WHERE 1=1")
    conn.execute("DELETE FROM tags WHERE 1=1")

print("All notes cleared.")
