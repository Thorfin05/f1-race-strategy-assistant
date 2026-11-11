
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "f1_history.db"
SEASON, ROUND = 2024, 24


def seconds(value):
    if not value:
        return None
    try:
        if ":" in value:
            minutes, secs = value.split(":")
            return int(minutes) * 60 + float(secs)
        return float(value)
    except (ValueError, TypeError):
        return None


with sqlite3.connect(DB) as conn:
    conn.row_factory = sqlite3.Row

    stops = conn.execute("""
        SELECT p.driverId, d.givenName, d.familyName,
               p.lap, p.stop, p.duration
        FROM pitstops p
        JOIN drivers d ON p.driverId = d.driverId
        WHERE p.season = ? AND p.round = ?
        ORDER BY p.lap, p.driverId
    """, (SEASON, ROUND)).fetchall()

    print(f"\nPIT WINDOW ANALYSIS: Abu Dhabi {SEASON}")
    print("-" * 75)

    for stop in stops:
        name = f'{stop["givenName"]} {stop["familyName"]}'
        pit_lap = stop["lap"]

        print(
            f"\n{name} | Pit stop #{stop['stop']} "
            f"| Lap {pit_lap} | Duration: {stop['duration']} sec"
        )

        laps = conn.execute("""
            SELECT lapNumber, time, position
            FROM lap_times
            WHERE season = ? AND round = ?
              AND driverId = ?
              AND lapNumber BETWEEN ? AND ?
            ORDER BY lapNumber
        """, (
            SEASON, ROUND, stop["driverId"],
            max(1, pit_lap - 2), pit_lap + 2
        )).fetchall()

        for lap in laps:
            lap_seconds = seconds(lap["time"])
            formatted = (
                f"{lap_seconds:.3f}s"
                if lap_seconds is not None else "N/A"
            )
            print(
                f"  Lap {lap['lapNumber']:>2}: "
                f"{formatted:>10} | Position: {lap['position']}"
            )

print("\nAnalysis complete.")
