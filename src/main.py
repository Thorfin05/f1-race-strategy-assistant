
import fastf1
from pathlib import Path

# Store downloaded data inside the project
cache_dir = Path(__file__).resolve().parent.parent / "data" / "cache"
cache_dir.mkdir(parents=True, exist_ok=True)

fastf1.Cache.enable_cache(str(cache_dir))

print("FastF1 version:", fastf1.__version__)

session = fastf1.get_session(2023, "Bahrain", "R")

try:
    session.load(
        laps=True,
        telemetry=False,
        weather=True
    )

    print("Race:", session.event["EventName"])
    print("Drivers:", len(session.drivers))

    laps = session.laps
    print("Total laps:", len(laps))

    print(
        laps[
            ["Driver", "LapNumber", "LapTime", "Compound", "TyreLife"]
        ].head(10)
    )

except Exception as error:
    print("Unable to load race lap data.")
    print(type(error).__name__, ":", error)
    print("Check the FastF1 warnings above for the underlying cause.")
