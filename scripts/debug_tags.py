"""Show all tags and which notes they are applied to."""
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
            t.name AS tag,
            COUNT(nt.note_id) AS note_count,
            GROUP_CONCAT(n.title, ', ') AS titles
        FROM tags t
        LEFT JOIN note_tags nt ON nt.tag_id = t.id
        LEFT JOIN notes n ON n.id = nt.note_id
        GROUP BY t.id
        ORDER BY note_count DESC, t.name
    """).fetchall()

    if not rows:
        print("No tags found.")
    else:
        print(f"{'TAG':<30} {'NOTES':>5}  TITLES")
        print("-" * 80)
        for r in rows:
            titles = (r['titles'] or '')[:50]
            print(f"{r['tag'][:29]:<30} {r['note_count']:>5}  {titles}")
        print(f"\nTotal tags: {len(rows)}")
