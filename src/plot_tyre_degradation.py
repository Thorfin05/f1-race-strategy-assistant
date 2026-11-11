
import os
import sqlite3
import matplotlib.pyplot as plt

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
            return float(parts[0]) * 60 + float(parts[1])
        return float(value)
    except (ValueError, TypeError):
        return None


conn = sqlite3.connect(DB)
cur = conn.cursor()

race = cur.execute("""
    SELECT round FROM races
    WHERE season = ? AND raceName = ?
""", (SEASON, RACE_NAME)).fetchone()

if not race:
    conn.close()
    raise SystemExit("Race not found in database.")

rnd = race[0]

fig, axes = plt.subplots(2, 2, figsize=(13, 9), sharey=True)
axes = axes.flatten()

for ax, (driver_id, driver_name) in zip(axes, DRIVERS.items()):

    rows = cur.execute("""
        SELECT lapNumber, time
        FROM lap_times
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lapNumber
    """, (SEASON, rnd, driver_id)).fetchall()

    pit_rows = cur.execute("""
        SELECT lap FROM pitstops
        WHERE season = ? AND round = ? AND driverId = ?
        ORDER BY lap
    """, (SEASON, rnd, driver_id)).fetchall()

    lap_times = {}
    for lap, time in rows:
        seconds = to_seconds(time)
        if seconds is not None and 70 < seconds < 100:
            lap_times[lap] = seconds

    if not rows:
        ax.set_title(f"{driver_name} — no data")
        continue

    pit_laps = sorted(set(row[0] for row in pit_rows))
    final_lap = max(row[0] for row in rows)

    ranges = []
    start = 1

    for pit_lap in pit_laps:
        if start <= pit_lap - 1:
            ranges.append((start, pit_lap - 1))
        start = pit_lap + 2

    if start <= final_lap:
        ranges.append((start, final_lap))

    for number, (first, last) in enumerate(ranges, start=1):
        points = [
            (lap - first + 1, lap_times[lap])
            for lap in range(first, last + 1)
            if lap in lap_times
        ]

        if not points:
            continue

        x = [point[0] for point in points]
        y = [point[1] for point in points]

        ax.scatter(x, y, s=18, label=f"Stint {number} laps")

        if len(points) >= 4:
            x_mean = sum(x) / len(x)
            y_mean = sum(y) / len(y)
            denominator = sum((v - x_mean) ** 2 for v in x)

            if denominator:
                slope = sum(
                    (a - x_mean) * (b - y_mean)
                    for a, b in points
                ) / denominator

                fitted = [
                    y_mean + slope * (v - x_mean)
                    for v in x
                ]

                ax.plot(
                    x, fitted,
                    label=f"Stint {number} trend ({slope:+.3f} s/lap)"
                )

    ax.set_title(driver_name)
    ax.set_xlabel("Lap age within stint")
    ax.set_ylabel("Lap time (seconds)")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

conn.close()

fig.suptitle(
    "2023 Italian GP — Lap-Time Trends by Stint",
    fontsize=15
)
fig.tight_layout()

os.makedirs("reports", exist_ok=True)
output = "reports/monza_tyre_degradation.png"
fig.savefig(output, dpi=160, bbox_inches="tight")

print(f"Chart saved to: {output}")
plt.show()
