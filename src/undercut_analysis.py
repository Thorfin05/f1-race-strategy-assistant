
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "f1_history.db"
SEASON = 2023
DRIVERS = [
    ("Max", "Verstappen"),
    ("Carlos", "Sainz"),
    ("Charles", "Leclerc"),
    ("Sergio", None),
]

with sqlite3.connect(DB) as conn:
    conn.row_factory = sqlite3.Row

    race = conn.execute("""
        SELECT season, round, raceName
        FROM races
        WHERE season = ? AND raceName LIKE '%Italian Grand Prix%'
        LIMIT 1
    """, (SEASON,)).fetchone()

    if not race:
        raise SystemExit("Race not found.")

    season, rnd = race["season"], race["round"]
    print(f"\nRACE STRATEGY REPORT: {race['raceName']} {season}")
    print("=" * 65)

    for given, family in DRIVERS:
        if given == "Sergio":
            driver = conn.execute("""
                SELECT driverId, givenName, familyName
                FROM drivers
                WHERE familyName = 'Pérez'
            """).fetchone()
        else:
            driver = conn.execute("""
                SELECT driverId, givenName, familyName
                FROM drivers
                WHERE givenName = ? AND familyName = ?
            """, (given, family)).fetchone()

        if not driver:
            print(f"\nDriver not found: {given} {family or ''}")
            continue

        stops = conn.execute("""
            SELECT lap, stop, duration
            FROM pitstops
            WHERE season = ? AND round = ? AND driverId = ?
            ORDER BY lap
        """, (season, rnd, driver["driverId"])).fetchall()

        result = conn.execute("""
            SELECT position, grid, points, status
            FROM race_results
            WHERE season = ? AND round = ? AND driverId = ?
        """, (season, rnd, driver["driverId"])).fetchone()

        print(f"\n{driver['givenName']} {driver['familyName']}")

        if stops:
            for stop in stops:
                print(
                    f"  Pit stop {stop['stop']}: lap {stop['lap']}, "
                    f"duration {stop['duration']} sec"
                )
        else:
            print("  No recorded pit stops.")

        if result:
            print(
                f"  Grid: P{result['grid']} | "
                f"Finish: P{result['position']} | "
                f"Points: {result['points']}"
            )
        else:
            print("  Race classification not found.")

print("\nReport complete.")
