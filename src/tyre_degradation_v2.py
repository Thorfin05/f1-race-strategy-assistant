
import csv
import sqlite3
from pathlib import Path
from statistics import median

DB_PATH = "data/f1_history.db"
OUTPUT_PATH = "reports/tyre_degradation_robust.csv"

SEASON = 2023
RACE_NAME = "Italian Grand Prix"

MIN_LAP_SECONDS = 70.0
MAX_LAP_SECONDS = 100.0
MIN_STINT_LAPS = 6


def parse_lap_time(value):
    """Convert M:SS.mmm or seconds into seconds."""
    if value is None:
        return None

    try:
        value = str(value).strip()
        if not value:
            return None

        if ":" in value:
            minutes, seconds = value.split(":", 1)
            return int(minutes) * 60 + float(seconds)

        return float(value)
    except (ValueError, TypeError):
        return None


def theil_sen(x, y):
    """Return robust slope and intercept."""
    slopes = []

    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            dx = x[j] - x[i]
            if dx:
                slopes.append((y[j] - y[i]) / dx)

    if not slopes:
        return None, None

    slope = median(slopes)
    intercept = median([
        yi - slope * xi for xi, yi in zip(x, y)
    ])

    return slope, intercept


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    race = cur.execute(
        """
        SELECT season, round, raceName, circuitName
        FROM races
        WHERE season = ? AND raceName = ?
        """,
        (SEASON, RACE_NAME),
    ).fetchone()

    if race is None:
        print("Race not found in database.")
        conn.close()
        return

    season = race["season"]
    round_no = race["round"]

    drivers = cur.execute(
        """
        SELECT DISTINCT lt.driverId,
               COALESCE(d.code,
                        d.givenName || ' ' || d.familyName,
                        lt.driverId) AS driver_name
        FROM lap_times lt
        LEFT JOIN drivers d ON lt.driverId = d.driverId
        WHERE lt.season = ? AND lt.round = ?
        ORDER BY driver_name
        """,
        (season, round_no),
    ).fetchall()

    results = []

    print(f"\nTYRE DEGRADATION PROXY V2")
    print(f"{race['raceName']} {season} — {race['circuitName']}")
    print("=" * 65)

    for driver in drivers:
        driver_id = driver["driverId"]
        name = driver["driver_name"]

        rows = cur.execute(
            """
            SELECT lapNumber, time
            FROM lap_times
            WHERE season = ? AND round = ? AND driverId = ?
            ORDER BY lapNumber
            """,
            (season, round_no, driver_id),
        ).fetchall()

        pit_rows = cur.execute(
            """
            SELECT lap
            FROM pitstops
            WHERE season = ? AND round = ? AND driverId = ?
            ORDER BY lap
            """,
            (season, round_no, driver_id),
        ).fetchall()

        lap_times = {}
        for row in rows:
            lap_no = int(row["lapNumber"])
            seconds = parse_lap_time(row["time"])
            if seconds is not None:
                lap_times[lap_no] = seconds

        if not lap_times:
            continue

        pit_laps = sorted({
            int(row["lap"])
            for row in pit_rows
            if row["lap"] is not None
        })

        first_lap = min(lap_times)
        last_lap = max(lap_times)

        # Pit lap and immediate out-lap are excluded from fitting.
        stints = []
        start = first_lap

        for pit_lap in pit_laps:
            if start <= pit_lap - 1:
                stints.append((start, pit_lap - 1, pit_lap))

            start = pit_lap + 2

        if start <= last_lap:
            stints.append((start, last_lap, None))

        for stint_no, (start, end, pit_lap) in enumerate(
            stints, start=1
        ):
            expected_laps = list(range(start, end + 1))
            valid = []
            missing_laps = []
            timing_excluded = 0

            for lap_no in expected_laps:
                seconds = lap_times.get(lap_no)

                if seconds is None:
                    missing_laps.append(lap_no)
                    continue

                if not MIN_LAP_SECONDS <= seconds <= MAX_LAP_SECONDS:
                    timing_excluded += 1
                    continue

                valid.append((lap_no, seconds))

            if len(valid) < MIN_STINT_LAPS:
                quality = "TOO_SHORT"
                slope = None
                intercept = None
            else:
                # Stint age starts at zero for its first valid observation.
                first_valid_lap = valid[0][0]
                x = [lap - first_valid_lap for lap, _ in valid]
                y = [seconds for _, seconds in valid]

                slope, intercept = theil_sen(x, y)

                if missing_laps or timing_excluded:
                    quality = "CHECK_MISSING_OR_FILTERED_LAPS"
                else:
                    quality = "OK"

            avg = (
                sum(seconds for _, seconds in valid) / len(valid)
                if valid else None
            )

            result = {
                "season": season,
                "race": race["raceName"],
                "circuit": race["circuitName"],
                "driver": name,
                "driver_id": driver_id,
                "stint": stint_no,
                "start_lap": start,
                "end_lap": end,
                "pit_lap_boundary": pit_lap,
                "valid_laps": len(valid),
                "missing_laps": ",".join(map(str, missing_laps)),
                "timing_excluded": timing_excluded,
                "average_lap_seconds": round(avg, 3) if avg is not None else "",
                "robust_slope_seconds_per_lap": round(slope, 4) if slope is not None else "",
                "quality": quality,
            }
            results.append(result)

            print(f"\n{name} | Stint {stint_no}: {start}-{end}")
            print(f"  Valid laps: {len(valid)}")
            print(f"  Missing laps: {missing_laps or 'None'}")
            print(f"  Timing exclusions: {timing_excluded}")
            print(f"  Quality: {quality}")

            if avg is not None:
                print(f"  Average lap time: {avg:.3f} s")

            if slope is not None:
                print(f"  Robust trend: {slope:+.4f} s/lap")
                if slope > 0:
                    print("  Lap times generally increased")
                elif slope < 0:
                    print("  Lap times generally decreased")
                else:
                    print("  Approximately flat trend")

    conn.close()

    output = Path(OUTPUT_PATH)
    output.parent.mkdir(parents=True, exist_ok=True)

    if results:
        with output.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)

        print("\n" + "=" * 65)
        print(f"CSV report saved to: {output}")
        print(f"Total stint records: {len(results)}")
    else:
        print("No stint records were produced.")

    print("Reminder: lap-time trend is not direct tyre-wear measurement.")


if __name__ == "__main__":
    main()
