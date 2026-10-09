import pandas as pd
from pathlib import Path

for f in sorted(Path("data/raw").glob("*NO2*.csv")):
    df = pd.read_csv(f, skiprows=7, na_values=["no data"])
    print(f.name, "| rows:", len(df),
          "| missing:", round(df.iloc[:, 2].isna().mean() * 100, 1), "%",
          "| columns:", df.columns.tolist())
    