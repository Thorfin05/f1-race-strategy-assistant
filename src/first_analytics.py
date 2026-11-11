
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "f1_history.db"


def to_seconds(value):
    if not value or ":" not in value:
        return None
    try:
        minutes, seconds = value.split(":")
        return int(minutes) * 60 + float(seconds)
    except (ValueError, AttributeError):
        return None


with sqlite3.connect(DB) as conn:
    conn.row_factory = sqlite3.Row

    print("\n=== AVAILABLE SEASONS ===")
    query = """
        SELECT season, COUNT(*) AS races
        FROM races
        GROUP BY season
        ORDER BY season DESC
        LIMIT 10
    """
    for row in conn.execute(query):
        print(dict(row))

    race = conn.execute("""
        SELECT r.season, r.round, r.raceName,
               COUNT(l.lapNumber) AS recorded_laps
        FROM races r
        JOIN lap_times l
          ON r.season = l.season AND r.round = l.round
        GROUP BY r.season, r.round, r.raceName
        ORDER BY r.season DESC, r.round DESC
        LIMIT 1
    """).fetchone()

    if not race:
        print("No race with lap-time records found.")
        raise SystemExit(1)

    season, rnd = race["season"], race["round"]

    print("\n=== LATEST RACE WITH LAP DATA ===")
    print(dict(race))

    print("\n=== DRIVER LAP-TIME COMPARISON ===")
    rows = conn.execute("""
        SELECT d.givenName, d.familyName, l.time
        FROM lap_times l
        JOIN drivers d ON l.driverId = d.driverId
        WHERE l.season = ? AND l.round = ?
    """, (season, rnd)).fetchall()

    times = {}
    for row in rows:
        seconds = to_seconds(row["time"])
        if seconds is not None:
            name = f'{row["givenName"]} {row["familyName"]}'
            times.setdefault(name, []).append(seconds)

    for name, values in sorted(
        times.items(),
        key=lambda item: sum(item[1]) / len(item[1])
    ):
        if len(values) >= 5:
            avg = sum(values) / len(values)
            print(f"{name}: {len(values)} laps, {avg:.3f} seconds")

    print("\n=== PIT-STOP SUMMARY ===")
    stops = conn.execute("""
        SELECT d.givenName, d.familyName, p.duration
        FROM pitstops p
        JOIN drivers d ON p.driverId = d.driverId
        WHERE p.season = ? AND p.round = ?
    """, (season, rnd)).fetchall()

    summary = {}
    for stop in stops:
        name = f'{stop["givenName"]} {stop["familyName"]}'
        try:
            duration = float(stop["duration"])
        except (ValueError, TypeError):
            continue
        summary.setdefault(name, []).append(duration)

    for name, values in sorted(
        summary.items(),
        key=lambda item: len(item[1]),
        reverse=True
    ):
        avg = sum(values) / len(values)
        print(f"{name}: {len(values)} stops, average {avg:.2f} seconds")

print("\nAnalytics completed.")
