import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_weather(lat=51.8787, lon=-0.4200,
                     start="2021-01-01", end="2026-10-01"):
    """Download hourly historical weather for Luton from Open-Meteo."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": ("temperature_2m,relative_humidity_2m,precipitation,"
                   "pressure_msl,wind_speed_10m,wind_direction_10m"),
        "timezone": "GMT",
    }
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    df = pd.DataFrame(response.json()["hourly"])
    df.to_csv(RAW_DIR / "weather_luton.csv", index=False)
    print(f"Saved {len(df)} rows to data/raw/weather_luton.csv")


if __name__ == "__main__":
    download_weather()