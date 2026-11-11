
import sqlite3
import pandas as pd

DB_PATH = "data/f1_history.db"
SEASON = 2023
ROUND = 15  # Italian Grand Prix

conn = sqlite3.connect(DB_PATH)

pitstops = pd.read_sql_query("""
    SELECT driverId, lap, stop, time, duration
    FROM pitstops
    WHERE season = ? AND round = ?
    ORDER BY lap, driverId
""", conn, params=(SEASON, ROUND))

lap_times = pd.read_sql_query("""
    SELECT driverId, lapNumber, position, time
    FROM lap_times
    WHERE season = ? AND round = ?
    ORDER BY driverId, lapNumber
""", conn, params=(SEASON, ROUND))

print("\nPIT-STOP LAP BOUNDARY AUDIT")
print("=" * 75)

if pitstops.empty:
    print("No pit-stop records found. Check the season and round.")
else:
    for _, pit in pitstops.iterrows():
        driver = pit["driverId"]
        pit_lap = int(pit["lap"])

        print(
            f"\nDriver: {driver} | Pit lap: {pit_lap} | "
            f"Stop: {pit['stop']} | Duration: {pit['duration']}s"
        )
        print("-" * 75)

        nearby = lap_times[
            (lap_times["driverId"] == driver)
            & (lap_times["lapNumber"].between(pit_lap - 2, pit_lap + 3))
        ]

        if nearby.empty:
            print("No nearby lap-time records found.")
        else:
            print(nearby.to_string(index=False))

conn.close()
