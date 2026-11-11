
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "f1_history.db"
DRIVERS = ["max_verstappen", "perez", "sainz", "leclerc"]

def to_seconds(value):
    try:
        parts = value.split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        return float(value)
    except (ValueError, AttributeError):
        return None

with sqlite3.connect(DB) as conn:
    conn.row_factory = sqlite3.Row

    race = conn.execute("""
        SELECT season, round, raceName
        FROM races
        WHERE season = 2023 AND raceName = 'Italian Grand Prix'
    """).fetchone()

    if not race:
        raise SystemExit("Italian Grand Prix not found.")

    season, rnd = race["season"], race["round"]
    print(f"\n{race['raceName']} {season} — Round {rnd}")
    print("=" * 55)

    for driver_id in DRIVERS:
        driver = conn.execute("""
            SELECT driverName FROM race_results
            WHERE season = ? AND round = ? AND driverId = ?
        """, (season, rnd, driver_id)).fetchone()

        if not driver:
            print(f"\nDriver not found: {driver_id}")
            continue

        stop = conn.execute("""
            SELECT lap, duration FROM pitstops
            WHERE season = ? AND round = ? AND driverId = ?
            ORDER BY lap LIMIT 1
        """, (season, rnd, driver_id)).fetchone()

        if not stop:
            print(f"\n{driver['driverName']}: no pit stop found")
            continue

        stop_lap = stop["lap"]
        print(f"\n{driver['driverName']} — pit lap {stop_lap}")

        laps = conn.execute("""
            SELECT lapNumber, time, position
            FROM lap_times
            WHERE season = ? AND round = ? AND driverId = ?
              AND lapNumber BETWEEN ? AND ?
            ORDER BY lapNumber
        """, (season, rnd, driver_id, stop_lap - 3, stop_lap + 3)).fetchall()

        for lap in laps:
            seconds = to_seconds(lap["time"])
            pace = f"{seconds:.3f}s" if seconds is not None else lap["time"]
            flag = " [PIT-WINDOW LAP]" if lap["lapNumber"] == stop_lap else ""
            print(
                f"Lap {lap['lapNumber']:>2}: {pace}, "
                f"recorded position={lap['position']}{flag}"
            )

print("\nAnalysis complete.")
