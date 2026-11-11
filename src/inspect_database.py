
import sqlite3

conn = sqlite3.connect("data/f1_history.db")
cur = conn.cursor()

tables = cur.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

print("DATABASE TABLES AND COLUMNS")
print("=" * 50)

for (table,) in tables:
    columns = cur.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    print(f"\n{table}")
    print("Columns:", ", ".join(column[1] for column in columns))

conn.close()
