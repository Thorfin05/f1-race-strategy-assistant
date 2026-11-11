
import sqlite3
from pathlib import Path

db = Path(__file__).resolve().parent.parent / "data" / "f1_history.db"

with sqlite3.connect(db) as conn:
    conn.row_factory = sqlite3.Row

    print("RACES TABLE")
    for row in conn.execute("""
        SELECT season, round, raceName
        FROM races
        WHERE season = 2023 AND round BETWEEN 14 AND 17
        ORDER BY round
    """):
        print(dict(row))

    print("\nPIT STOP DRIVER IDS — ROUNDS 15 AND 16")
    for row in conn.execute("""
        SELECT round, driverId, lap, duration
        FROM pitstops
        WHERE season = 2023 AND round IN (15, 16)
          AND driverId IN ('max_verstappen', 'verstappen',
                           'perez', 'sainz', 'leclerc')
        ORDER BY round, lap
    """):
        print(dict(row))

    print("\nLAP-TIME DRIVER IDS")
    for row in conn.execute("""
        SELECT DISTINCT driverId
        FROM lap_times
        WHERE season = 2023 AND round = 15
        ORDER BY driverId
    """):
        print(row["driverId"])
