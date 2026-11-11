
import sqlite3

DB = "data/f1_history.db"
SEASON = 2023
RACE_NAME = "Italian Grand Prix"

DRIVERS = {
    "max_verstappen": "Max Verstappen",
    "perez": "Sergio Pérez",
    "sainz": "Carlos Sainz",
    "leclerc": "Charles Leclerc"
}

def to_seconds(value):
    try:
        parts = value.split(":")
        return float(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(value)
    except (ValueError, AttributeError):
        return None

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

race = cur.execute("""
    SELECT round FROM races
    WHERE season = ? AND raceName = ?
""", (SEASON, RACE_NAME)).fetchone()

if not race:
    print("Race not found.")
    conn.close()
    raise SystemExit

rnd = race["round"]
print(f"\nPACE COMPARISON: {RACE_NAME} {SEASON}")
print("=" * 55)

for driver_id, name in DRIVERS.items():
    stop = cur.execute("""
        SELECT MIN(lap) AS pit_lap
        FROM pitstops
        WHERE season = ? AND round = ? AND driverId = ?
    """, (SEASON, rnd, driver_id)).fetchone()["pit_lap"]

    if stop is None:
        print(f"\n{name}: No pit stop recorded.")
        continue

    rows = cur.execute("""
        SELECT lapNumber, time
        FROM lap_times
        WHERE season = ? AND round = ? AND driverId = ?
          AND lapNumber BETWEEN ? AND ?
        ORDER BY lapNumber
    """, (SEASON, rnd, driver_id, stop - 4, stop + 4)).fetchall()

    laps = {
        row["lapNumber"]: to_seconds(row["time"])
        for row in rows
    }

    # Three laps before the pit lap
    before = [
        laps.get(lap) for lap in range(stop - 3, stop)
    ]

    # Out-lap is stop lap + 1; exclude it from post-pit pace
    after = [
        laps.get(lap) for lap in range(stop + 2, stop + 5)
    ]

    before = [x for x in before if x is not None and x < 100]
    after = [x for x in after if x is not None and x < 100]

    print(f"\n{name} — pit lap {stop}")

    if before:
        pre_avg = sum(before) / len(before)
        print(f"Pre-pit average:  {pre_avg:.3f}s")
    else:
        pre_avg = None
        print("Pre-pit average:  Insufficient data")

    if after:
        post_avg = sum(after) / len(after)
        print(f"Post-pit average: {post_avg:.3f}s")
    else:
        post_avg = None
        print("Post-pit average: Insufficient data")

    if pre_avg is not None and post_avg is not None:
        difference = post_avg - pre_avg
        print(f"Pace difference:  {difference:+.3f}s/lap")
        print("Interpretation:   Faster" if difference < 0
              else "Interpretation:   Slower" if difference > 0
              else "Interpretation:   Equal average pace")

print("\nNote: This is a basic pace comparison, not proof of an undercut.")
print("Traffic, tyre compound, fuel, and track conditions are not controlled.")
conn.close()
