
import sqlite3
from statistics import median, mean

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
    try:
        parts = str(value).strip().split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(value)
    except (ValueError, TypeError):
        return None


def slope(points):
    if len(points) < 4:
        return None

    x = [p[0] for p in points]
    y = [p[1] for p in points]
    xm, ym = mean(x), mean(y)
    denom = sum((v - xm) ** 2 for v in x)

    if not denom:
        return None

    return sum((a - xm) * (b - ym)
               for a, b in points) / denom


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

race = cur.execute("""
    SELECT round FROM races
    WHERE season = ? AND raceName = ?
""", (SEASON, RACE_NAME)).fetchone()

if not race:
    conn.close()
    raise SystemExit("Race not found.")

rnd = race["round"]

print(f"\nCLEANED STINT TREND: {RACE_NAME} {SEASON}")
print("=" * 65)

for driver_id, name in DRIVERS.items():
    rows = cur.execute("""
        SELECT lapNumber, time FROM lap_times
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lapNumber
    """, (SEASON, rnd, driver_id)).fetchall()

    pit_rows = cur.execute("""
        SELECT lap FROM pitstops
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lap
    """, (SEASON, rnd, driver_id)).fetchall()

    raw = {}
    for row in rows:
        seconds = to_seconds(row["time"])
        if seconds is not None and 70 < seconds < 100:
            raw[row["lapNumber"]] = seconds

    if not raw:
        print(f"\n{name}: no valid lap times")
        continue

    typical = median(raw.values())
    cleaned = {
        lap: seconds for lap, seconds in raw.items()
        if abs(seconds - typical) <= 5
    }

    pit_laps = sorted(set(row["lap"] for row in pit_rows))
    final_lap = max(row["lapNumber"] for row in rows)

    ranges = []
    start = 1
    for pit_lap in pit_laps:
        if start <= pit_lap - 1:
            ranges.append((start, pit_lap - 1))
        start = pit_lap + 2
    if start <= final_lap:
        ranges.append((start, final_lap))

    print(f"\n{name}")
    print(f"Valid laps before median filter: {len(raw)}")
    print(f"Valid laps after median filter:  {len(cleaned)}")

    for number, (first, last) in enumerate(ranges, 1):
        points = [
            (lap - first + 1, cleaned[lap])
            for lap in range(first, last + 1)
            if lap in cleaned
        ]

        m = slope(points)
        if m is None:
            print(f"  Stint {number}: insufficient valid laps")
        else:
            print(
                f"  Stint {number} (laps {first}-{last}): "
                f"{m:+.3f} seconds per stint lap "
                f"({len(points)} valid observations)"
            )

print("\nNote: Filtering is a sensitivity check, not proof of tyre wear.")
conn.close()
