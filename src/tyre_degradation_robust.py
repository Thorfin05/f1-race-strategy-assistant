
import sqlite3
from statistics import median
from math import sqrt

DB_PATH = "data/f1_history.db"

SEASON = 2023
RACE_NAME = "Italian Grand Prix"

# Adjust these limits if your dataset uses a different timing format.
MIN_LAP_SECONDS = 70.0
MAX_LAP_SECONDS = 100.0

# Exclude the pit-entry lap and the first lap after the stop.
EXCLUDE_PIT_LAP = True
EXCLUDE_OUT_LAP = True


def parse_lap_time(value):
    """Convert '1:26.733' or '86.733' into seconds."""
    if value is None:
        return None

    try:
        value = str(value).strip()

        if not value:
            return None

        parts = value.split(":")

        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])

        return float(value)

    except (ValueError, TypeError):
        return None


def robust_regression(x_values, y_values):
    """
    Theil-Sen-style regression:
    slope = median of pairwise slopes
    intercept = median of residual-adjusted intercepts
    """
    slopes = []

    for i in range(len(x_values)):
        for j in range(i + 1, len(x_values)):
            dx = x_values[j] - x_values[i]

            if dx != 0:
                slopes.append(
                    (y_values[j] - y_values[i]) / dx
                )

    if not slopes:
        return None, None, None

    slope = median(slopes)
    intercept = median([
        y - slope * x
        for x, y in zip(x_values, y_values)
    ])

    predictions = [
        intercept + slope * x for x in x_values
    ]

    mean_y = sum(y_values) / len(y_values)
    total = sum((y - mean_y) ** 2 for y in y_values)
    residual = sum(
        (y - prediction) ** 2
        for y, prediction in zip(y_values, predictions)
    )

    # Descriptive R-squared for the robust fitted line.
    r_squared = (
        1 - residual / total if total > 0 else None
    )

    return slope, intercept, r_squared


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
        (SEASON, RACE_NAME)
    ).fetchone()

    if race is None:
        print("Race not found in the database.")
        conn.close()
        return

    season = race["season"]
    round_no = race["round"]

    print(
        f"\nROBUST LAP-TIME DEGRADATION PROXY: "
        f"{race['raceName']} {season}"
    )
    print(f"Circuit: {race['circuitName']}")
    print("=" * 68)

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
        (season, round_no)
    ).fetchall()

    for driver in drivers:
        driver_id = driver["driverId"]
        driver_name = driver["driver_name"]

        lap_rows = cur.execute(
            """
            SELECT lapNumber, time
            FROM lap_times
            WHERE season = ? AND round = ? AND driverId = ?
            ORDER BY lapNumber
            """,
            (season, round_no, driver_id)
        ).fetchall()

        pit_rows = cur.execute(
            """
            SELECT lap
            FROM pitstops
            WHERE season = ? AND round = ? AND driverId = ?
            ORDER BY lap
            """,
            (season, round_no, driver_id)
        ).fetchall()

        pit_laps = sorted({
            int(row["lap"])
            for row in pit_rows
            if row["lap"] is not None
        })

        if not lap_rows:
            continue

        lap_times = {}

        for row in lap_rows:
            lap_no = int(row["lapNumber"])
            seconds = parse_lap_time(row["time"])

            if seconds is not None:
                lap_times[lap_no] = seconds

        if not lap_times:
            continue

        first_lap = min(lap_times)
        last_lap = max(lap_times)

        # Build stint ranges using recorded pit-stop laps.
        stints = []
        start_lap = first_lap

        for pit_lap in pit_laps:
            if start_lap <= pit_lap - 1:
                stints.append(
                    (start_lap, pit_lap - 1, pit_lap)
                )

            # Skip the pit lap and immediate out-lap.
            start_lap = pit_lap + 1

            if EXCLUDE_PIT_LAP:
                start_lap = pit_lap + 1

            if EXCLUDE_OUT_LAP:
                start_lap = max(start_lap, pit_lap + 2)

        if start_lap <= last_lap:
            stints.append((start_lap, last_lap, None))

        # Count the race laps rejected by timing limits.
        invalid_times = sum(
            1 for seconds in lap_times.values()
            if not MIN_LAP_SECONDS <= seconds <= MAX_LAP_SECONDS
        )

        print(f"\n{driver_name}")
        print(f"Recorded pit-stop laps: {pit_laps or 'None'}")
        print(f"Timing-limit exclusions: {invalid_times}")

        for stint_number, (start, end, pit_lap) in enumerate(
            stints, start=1
        ):
            observations = []

            for lap_no in range(start, end + 1):
                seconds = lap_times.get(lap_no)

                if seconds is None:
                    continue

                if not MIN_LAP_SECONDS <= seconds <= MAX_LAP_SECONDS:
                    continue

                # Relative stint age starts at zero.
                stint_age = lap_no - start
                observations.append((stint_age, seconds, lap_no))

            if len(observations) < 4:
                print(
                    f"  Stint {stint_number} ({start}-{end}): "
                    "not enough valid laps"
                )
                continue

            x_values = [item[0] for item in observations]
            y_values = [item[1] for item in observations]

            slope, intercept, r_squared = robust_regression(
                x_values, y_values
            )

            average = sum(y_values) / len(y_values)

            print(
                f"\n  Stint {stint_number}: laps {start}-{end}"
            )
            print(f"    Valid laps: {len(observations)}")
            print(f"    Average lap time: {average:.3f} s")
            print(
                f"    Robust trend: {slope:+.3f} "
                "seconds per stint lap"
            )

            if slope > 0:
                print("    Interpretation: lap times generally increased")
            elif slope < 0:
                print("    Interpretation: lap times generally decreased")
            else:
                print("    Interpretation: approximately flat trend")

            if r_squared is not None:
                print(f"    Descriptive R-squared: {r_squared:.3f}")

            if pit_lap is not None:
                print(
                    f"    Excluded pit-entry lap: {pit_lap}"
                )
                if EXCLUDE_OUT_LAP:
                    print(
                        f"    Excluded immediate out-lap: {pit_lap + 1}"
                    )

    conn.close()

    print("\n" + "=" * 68)
    print("Analysis complete.")
    print(
        "Reminder: this measures lap-time trends, not tyre wear alone."
    )


if __name__ == "__main__":
    main()
