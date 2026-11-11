
import sqlite3
from statistics import median

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

print(f"\nLAP-TIME VALIDATION: {RACE_NAME} {SEASON}")
print("=" * 65)

for driver_id, name in DRIVERS.items():
    rows = cur.execute("""
        SELECT lapNumber, time
        FROM lap_times
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lapNumber
    """, (SEASON, race["round"], driver_id)).fetchall()

    valid = []
    flagged = []

    for row in rows:
        seconds = to_seconds(row["time"])

        if seconds is None or seconds <= 0:
            flagged.append((row["lapNumber"], row["time"], "Invalid time"))
        elif seconds < 70 or seconds > 100:
            flagged.append((row["lapNumber"], row["time"], "Outside 70–100s"))
        else:
            valid.append((row["lapNumber"], seconds))

    # Identify unusual times relative to this driver's median.
    if valid:
        typical = median(seconds for _, seconds in valid)

        for lap, seconds in valid:
            if abs(seconds - typical) > 5:
                flagged.append((lap, f"{seconds:.3f}s",
                                f"{seconds - typical:+.3f}s from median"))

    print(f"\n{name}")
    print(f"Valid recorded laps: {len(valid)}")
    print(f"Flagged observations: {len(flagged)}")

    for lap, value, reason in sorted(flagged):
        print(f"  Lap {lap}: {value} — {reason}")

print("\nValidation complete.")
print("Flagged laps are for review, not automatic deletion.")

conn.close()
