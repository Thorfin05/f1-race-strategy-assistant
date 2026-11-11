
import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parent.parent / "data" / "f1_history.db"

with sqlite3.connect(db) as conn:
    tables = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """).fetchall()

    print("Database tables:")
    for (table,) in tables:
        print("-", table)

    print("\nSample race records:")
    print(conn.execute("""
        SELECT * FROM races LIMIT 5
    """).fetchall())

    print("\nTotal lap-time records:")
    print(conn.execute("""
        SELECT COUNT(*) FROM lap_times
    """).fetchone()[0])
