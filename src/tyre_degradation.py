
import sqlite3
from statistics import mean

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
    """Convert M:SS.mmm to seconds."""
    try:
        parts = str(value).strip().split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        return float(value)
    except (ValueError, TypeError):
        return None


def linear_regression(points):
    """Return slope and R-squared for (x, y) pairs."""
    xs = [x for x, y in points]
    ys = [y for x, y in points]

    x_mean = mean(xs)
    y_mean = mean(ys)

    denominator = sum((x - x_mean) ** 2 for x in xs)
    if denominator == 0:
        return None, None

    slope = sum(
        (x - x_mean) * (y - y_mean)
        for x, y in points
    ) / denominator

    predicted = [
        y_mean + slope * (x - x_mean)
        for x in xs
    ]

    total = sum((y - y_mean) ** 2 for y in ys)
    residual = sum(
        (y - prediction) ** 2
        for y, prediction in zip(ys, predicted)
    )

    r_squared = 1 - residual / total if total else None
    return slope, r_squared


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

race = cur.execute("""
    SELECT round
    FROM races
    WHERE season = ? AND raceName = ?
""", (SEASON, RACE_NAME)).fetchone()

if not race:
    conn.close()
    raise SystemExit(f"Race not found: {RACE_NAME} {SEASON}")

rnd = race["round"]

print(f"\nTYRE DEGRADATION PROXY: {RACE_NAME} {SEASON}")
print("=" * 68)

for driver_id, driver_name in DRIVERS.items():

    lap_rows = cur.execute("""
        SELECT lapNumber, time
        FROM lap_times
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lapNumber
    """, (SEASON, rnd, driver_id)).fetchall()

    pit_rows = cur.execute("""
        SELECT lap
        FROM pitstops
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lap
    """, (SEASON, rnd, driver_id)).fetchall()

    if not lap_rows:
        print(f"\n{driver_name}: No lap data found.")
        continue

    laps = {}
    for row in lap_rows:
        seconds = to_seconds(row["time"])

        # Basic quality filter for normal racing laps at Monza.
        # This removes unusually long or invalid recorded times.
        if seconds is not None and 70 < seconds < 100:
            laps[row["lapNumber"]] = seconds

    pit_laps = sorted(set(row["lap"] for row in pit_rows))
    final_lap = max(row["lapNumber"] for row in lap_rows)

    # Build stint ranges. Exclude pit-in laps and the
    # immediate out-lap after each stop.
    ranges = []
    start_lap = 1

    for pit_lap in pit_laps:
        end_lap = pit_lap - 1

        if start_lap <= end_lap:
            ranges.append((start_lap, end_lap))

        start_lap = pit_lap + 2

    if start_lap <= final_lap:
        ranges.append((start_lap, final_lap))

    print(f"\n{driver_name}")
    print("-" * 55)

    for stint_number, (start, end) in enumerate(ranges, start=1):

        points = []

        for lap_number in range(start, end + 1):
            if lap_number in laps:
                stint_age = lap_number - start + 1
                points.append((stint_age, laps[lap_number]))

        if len(points) < 4:
            print(
                f"Stint {stint_number} (laps {start}-{end}): "
                f"Not enough valid laps ({len(points)})"
            )
            continue

        slope, r_squared = linear_regression(points)

        if slope is None:
            print(f"Stint {stint_number}: Cannot fit model.")
            continue

        average_time = mean(y for x, y in points)

        print(
            f"Stint {stint_number} | laps {start}-{end} | "
            f"valid laps: {len(points)}"
        )
        print(f"  Average lap time: {average_time:.3f} s")
        print(f"  Lap-time trend:   {slope:+.3f} s per stint lap")

        if slope > 0:
            print("  Trend: Lap times increased")
        elif slope < 0:
            print("  Trend: Lap times decreased")
        else:
            print("  Trend: No linear change")

        if r_squared is not None:
            print(f"  R-squared:        {r_squared:.3f}")

print("\n" + "=" * 68)
print("Analysis complete.")
print("This estimates lap-time trends, not pure tyre degradation.")
print("Tyre compound, tyre age, fuel, traffic and weather are not controlled.")

conn.close()
