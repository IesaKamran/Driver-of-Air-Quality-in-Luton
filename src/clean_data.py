"""Load, clean and merge NO2 (Luton A505) and weather data into one hourly table."""
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

MAX_INTERPOLATE_HOURS = 3  # only fill short gaps; leave long outages as missing


def load_no2() -> pd.DataFrame:
    """Combine the yearly DEFRA NO2 files into one clean hourly DataFrame."""
    files = sorted(RAW_DIR.glob("*NO2*.csv"))
    if not files:
        raise FileNotFoundError("No NO2 files found in data/raw/")

    frames = []
    for f in files:
        # First 7 lines are metadata (site name, notes, etc.), so skip them.
        # Missing readings are stored as the text "no data".
        df = pd.read_csv(f, skiprows=7, na_values=["no data"])
        frames.append(df)

    no2 = pd.concat(frames, ignore_index=True)
    no2["timestamp"] = pd.to_datetime(no2["Date"] + " " + no2["Time"])
    no2 = no2.rename(columns={"Nitrogen dioxide": "no2", "Status": "status"})
    no2["no2"] = pd.to_numeric(no2["no2"], errors="coerce")

    # Tiny negative values are sensor noise, so floor them at zero.
    no2["no2"] = no2["no2"].clip(lower=0)

    # P = provisional (not yet fully quality-checked). Keep a flag for the README.
    no2["provisional"] = no2["status"].eq("P")

    no2 = (no2[["timestamp", "no2", "provisional"]]
           .drop_duplicates("timestamp")
           .sort_values("timestamp")
           .set_index("timestamp"))

    # Make sure every hour exists as a row, so gaps are explicit.
    full_index = pd.date_range(no2.index.min(), no2.index.max(), freq="h")
    no2 = no2.reindex(full_index)
    no2.index.name = "timestamp"
    no2["provisional"] = no2["provisional"].fillna(False).astype(bool)

    # Fill short gaps only.
    no2["no2"] = no2["no2"].interpolate(limit=MAX_INTERPOLATE_HOURS,
                                        limit_area="inside")
    return no2


def load_weather() -> pd.DataFrame:
    weather = pd.read_csv(RAW_DIR / "weather_luton.csv", parse_dates=["time"])
    return weather.rename(columns={"time": "timestamp"}).set_index("timestamp")


def main():
    no2 = load_no2()
    print(f"NO2: {len(no2)} hourly rows, "
          f"{no2['no2'].isna().mean():.1%} still missing after short-gap fill")

    try:
        weather = load_weather()
        merged = no2.join(weather, how="inner")
    except FileNotFoundError:
        print("weather_luton.csv not found, saving NO2 only")
        merged = no2

    merged.to_csv(PROCESSED_DIR / "luton_hourly.csv")
    print(f"Saved {len(merged)} rows to data/processed/luton_hourly.csv")


if __name__ == "__main__":
    main()