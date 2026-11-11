
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "f1_history.db"
SEASON = 2023

def to_seconds(value):
    if not value:
        return None
    try:
        if ":" in value:
            minutes, seconds = value.split(":")
            return int(minutes) * 60 + float(seconds)
        return float(value)
    except (ValueError, TypeError):
        return None

with sqlite3.connect(DB) as conn:
    conn.row_factory = sqlite3.Row

    race = conn.execute("""
        SELECT season, round, raceName
        FROM races
        WHERE season = ? AND raceName LIKE '%Italian Grand Prix%'
        LIMIT 1
    """, (SEASON,)).fetchone()

    if not race:
        print("Monza race not found in the database.")
        raise SystemExit

    season, rnd = race["season"], race["round"]

    print(f"\n🏁 {race['raceName']} — {season}")
    print("=" * 65)

    stops = conn.execute("""
        SELECT p.driverId, d.givenName, d.familyName,
               p.lap, p.stop, p.duration
        FROM pitstops p
        JOIN drivers d ON p.driverId = d.driverId
        WHERE p.season = ? AND p.round = ?
        ORDER BY p.lap, p.driverId
    """, (season, rnd)).fetchall()

    print("\nPIT-STOP TIMELINE")
    print("-" * 65)

    for s in stops:
        name = f"{s['givenName']} {s['familyName']}"
        print(
            f"Lap {s['lap']:>2} | {name:<22} "
            f"| Stop {s['stop']} | {s['duration']} sec"
        )

    print("\nMAX VERSTAPPEN — LAP WINDOW")
    print("-" * 65)

    max_driver = conn.execute("""
        SELECT driverId
        FROM drivers
        WHERE familyName = 'Verstappen'
          AND givenName = 'Max'
        LIMIT 1
    """).fetchone()

    if not max_driver:
        print("Max Verstappen not found.")
        raise SystemExit

    max_stops = conn.execute("""
        SELECT lap, stop, duration
        FROM pitstops
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lap
    """, (season, rnd, max_driver["driverId"])).fetchall()

    for stop in max_stops:
        pit_lap = stop["lap"]
        print(
            f"\nPit stop #{stop['stop']} at lap {pit_lap} "
            f"(duration: {stop['duration']} sec)"
        )

        laps = conn.execute("""
            SELECT lapNumber, time, position
            FROM lap_times
            WHERE season = ? AND round = ? AND driverId = ?
              AND lapNumber BETWEEN ? AND ?
            ORDER BY lapNumber
        """, (
            season, rnd, max_driver["driverId"],
            max(1, pit_lap - 3), pit_lap + 3
        )).fetchall()

        for lap in laps:
            seconds = to_seconds(lap["time"])
            pace = f"{seconds:.3f}s" if seconds is not None else "N/A"
            print(
                f"  Lap {lap['lapNumber']:>2}: {pace:>9} "
                f"| Position: {lap['position']}"
            )

    print("\nRIVAL PIT WINDOWS")
    print("-" * 65)

    # Focus on the main Ferrari rival and Sergio Perez.
    for family in ["Sainz", "Perez", "Leclerc"]:
        driver = conn.execute("""
            SELECT driverId, givenName, familyName
            FROM drivers
            WHERE familyName = ?
            LIMIT 1
        """, (family,)).fetchone()

        if not driver:
            continue

        rival_stops = conn.execute("""
            SELECT lap, stop, duration
            FROM pitstops
            WHERE season = ? AND round = ? AND driverId = ?
            ORDER BY lap
        """, (season, rnd, driver["driverId"])).fetchall()

        print(f"\n{driver['givenName']} {driver['familyName']}")

        if not rival_stops:
            print("  No recorded pit stops.")
            continue

        for stop in rival_stops:
            print(
                f"  Stop {stop['stop']} at lap {stop['lap']} "
                f"| Duration: {stop['duration']} sec"
            )

            laps = conn.execute("""
                SELECT lapNumber, time, position
                FROM lap_times
                WHERE season = ? AND round = ? AND driverId = ?
                  AND lapNumber BETWEEN ? AND ?
                ORDER BY lapNumber
            """, (
                season, rnd, driver["driverId"],
                max(1, stop["lap"] - 2), stop["lap"] + 2
            )).fetchall()

            for lap in laps:
                seconds = to_seconds(lap["time"])
                pace = f"{seconds:.3f}s" if seconds is not None else "N/A"
                print(
                    f"    Lap {lap['lapNumber']:>2}: {pace:>9} "
                    f"| Position: {lap['position']}"
                )

print("\nInvestigation complete.")
