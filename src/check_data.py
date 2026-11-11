
from pathlib import Path
import pandas as pd

folder = Path("data/raw")

for file in folder.glob("*.csv"):
    try:
        df = pd.read_csv(file)
        print(f"\n{file.name}: {len(df)} rows")
        print("Columns:", list(df.columns))
        print(df.head(2).to_string(index=False))
    except Exception as e:
        print(f"Error reading {file.name}: {e}")
