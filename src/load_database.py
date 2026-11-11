
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "f1_history.db"

if not DATA_DIR.exists():
    raise FileNotFoundError(f"Missing data directory: {DATA_DIR}")

csv_files = sorted(DATA_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError("No CSV files found in data/raw")

with sqlite3.connect(DB_PATH) as conn:
    for file in csv_files:
        table = file.stem

        print(f"\nLoading {file.name}...")

        df = pd.read_csv(
            file,
            na_values=[r"\N"],
            low_memory=False
        )

        df.columns = [
            col.strip().replace(" ", "_")
            for col in df.columns
        ]

        df.to_sql(
            table,
            conn,
            if_exists="replace",
            index=False,
            chunksize=10000
        )

        count = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]

        print(f"Table: {table} | Rows: {count}")
        print(f"Columns: {', '.join(df.columns)}")

print(f"\nDatabase created: {DB_PATH}")
print("Offline F1 data import completed!")
