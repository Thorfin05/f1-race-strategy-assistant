
import sqlite3

DB = "data/f1_history.db"
SEASON = 2023
RACE_NAME = "Italian Grand Prix"

DRIVERS = {
    "max_verstappen": "Max Verstappen",
    "perez": "Sergio Pérez",
    "sainz": "Carlos Sainz",
    "leclerc": "Charles Leclerc",
}


def to_seconds(value):
    """Convert M:SS.mmm or a numeric string to seconds."""
    try:
        parts = str(value).strip().split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        return float(value)
    except (ValueError, TypeError):
        return None


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

race = cur.execute("""
    SELECT round
    FROM races
    WHERE season = ? AND raceName = ?
""", (SEASON, RACE_NAME)).fetchone()

if not race:
    print(f"Race not found: {RACE_NAME} {SEASON}")
    conn.close()
    raise SystemExit

rnd = race["round"]

print(f"\nF1 STRATEGY REPORT: {RACE_NAME} {SEASON}")
print("=" * 65)

for driver_id, driver_name in DRIVERS.items():

    # 1. First pit stop
    pit = cur.execute("""
        SELECT lap, duration
        FROM pitstops
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lap
        LIMIT 1
    """, (SEASON, rnd, driver_id)).fetchone()

    # 2. Race result
    result = cur.execute("""
        SELECT grid, position, points
        FROM race_results
        WHERE season = ? AND round = ? AND driverId = ?
        LIMIT 1
    """, (SEASON, rnd, driver_id)).fetchone()

    # 3. Lap times around the first pit stop
    print(f"\n{driver_name}")
    print("-" * 45)

    if not pit:
        print("Pit stop: No record found")
        continue

    pit_lap = pit["lap"]
    duration = to_seconds(pit["duration"])

    print(f"First pit lap: {pit_lap}")
    if duration is not None:
        print(f"Recorded stop duration: {duration:.3f} seconds")
    else:
        print(f"Recorded stop duration: {pit['duration']}")

    rows = cur.execute("""
        SELECT lapNumber, time
        FROM lap_times
        WHERE season = ? AND round = ? AND driverId = ?
          AND lapNumber BETWEEN ? AND ?
        ORDER BY lapNumber
    """, (SEASON, rnd, driver_id, pit_lap - 4, pit_lap + 4)).fetchall()

    laps = {
        row["lapNumber"]: to_seconds(row["time"])
        for row in rows
    }

    # Three laps before pit
    before = [
        laps.get(lap) for lap in range(pit_lap - 3, pit_lap)
    ]

    # Exclude the pit lap and immediate out-lap
    after = [
        laps.get(lap) for lap in range(pit_lap + 2, pit_lap + 5)
    ]

    # Simple safeguard against unusually long recorded laps
    before = [x for x in before if x is not None and 0 < x < 100]
    after = [x for x in after if x is not None and 0 < x < 100]

    pre_avg = sum(before) / len(before) if before else None
    post_avg = sum(after) / len(after) if after else None

    if pre_avg is not None:
        print(f"Pre-pit average:  {pre_avg:.3f} s/lap")
    else:
        print("Pre-pit average:  Insufficient data")

    if post_avg is not None:
        print(f"Post-pit average: {post_avg:.3f} s/lap")
    else:
        print("Post-pit average: Insufficient data")

    if pre_avg is not None and post_avg is not None:
        change = post_avg - pre_avg
        print(f"Pace difference:  {change:+.3f} s/lap")
        print("Pace trend:       Faster" if change < 0
              else "Pace trend:       Slower" if change > 0
              else "Pace trend:       Unchanged")

    # 4. Grid position and final result
    if result:
        print(f"Starting grid:    P{result['grid']}")
        print(f"Finishing place:  P{result['position']}")
        print(f"Championship pts: {result['points']}")
    else:
        print("Race result: Not found")

print("\n" + "=" * 65)
print("Report complete.")
print("Caution: Pace changes alone do not establish undercut success.")
print("Traffic, tyre compound, fuel and track conditions are not controlled.")

conn.close()
