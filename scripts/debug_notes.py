"""List all ingested notes with their chunk and tag counts."""
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
    rows = conn.execute("""
        SELECT
            n.id,
            n.title,
            n.source_type,
            n.created_at,
            COUNT(DISTINCT c.id)  AS chunks,
            COUNT(DISTINCT nt.tag_id) AS tags
        FROM notes n
        LEFT JOIN chunks c  ON c.note_id = n.id
        LEFT JOIN note_tags nt ON nt.note_id = n.id
        GROUP BY n.id
        ORDER BY n.created_at DESC
    """).fetchall()

    if not rows:
        print("No notes ingested yet.")
    else:
        print(f"{'ID':<38} {'TITLE':<30} {'TYPE':<10} {'CHUNKS':>6} {'TAGS':>5}  CREATED")
        print("-" * 100)
        for r in rows:
            print(f"{r['id']:<38} {r['title'][:29]:<30} {r['source_type']:<10} {r['chunks']:>6} {r['tags']:>5}  {r['created_at'][:19]}")
        print(f"\nTotal notes: {len(rows)}")
