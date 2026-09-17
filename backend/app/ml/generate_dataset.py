"""
Generates a synthetic but realistic cloud-metrics dataset for training the
carbon emission forecasting models. Correlations are built in deliberately:

- energy_consumption scales with cpu_usage, memory_usage, storage and network
- carbon_emission = energy_consumption * region_carbon_factor + noise
- includes daily / weekly seasonality so LSTM-style sequence models have a
  genuine temporal pattern to learn from

Run directly:  python -m app.ml.generate_dataset
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

from app.ml.carbon_engine import REGION_CARBON_FACTORS

np.random.seed(42)

REGIONS = list(REGION_CARBON_FACTORS.keys())
SERVERS = [f"AWS{str(i).zfill(3)}" for i in range(1, 13)]
N_DAYS = 400


def generate(n_days: int = N_DAYS) -> pd.DataFrame:
    rows = []
    start = datetime.utcnow() - timedelta(days=n_days)

    for server in SERVERS:
        region = np.random.choice(REGIONS)
        base_cpu = np.random.uniform(25, 65)
        base_mem = np.random.uniform(30, 70)
        base_storage = np.random.uniform(150, 900)
        factor = REGION_CARBON_FACTORS[region]

        for day in range(n_days):
            ts = start + timedelta(days=day)
            weekday_dip = 0.85 if ts.weekday() >= 5 else 1.0  # lower usage on weekends
            weekly_wave = 1 + 0.15 * np.sin(2 * np.pi * day / 7)
            trend = 1 + 0.0006 * day  # slow upward drift (data growth)

            cpu = np.clip(base_cpu * weekday_dip * weekly_wave * trend
                          + np.random.normal(0, 5), 1, 100)
            mem = np.clip(base_mem * weekday_dip * weekly_wave * trend
                          + np.random.normal(0, 4), 1, 100)
            storage = max(10, base_storage * trend + np.random.normal(0, 8))
            network = np.clip(np.random.gamma(2.0, 15) * weekday_dip, 0, 400)
            temperature = np.random.normal(24, 2)

            energy = (
                0.9 * cpu + 0.6 * mem + 0.02 * storage + 0.15 * network
                + np.random.normal(0, 6)
            )
            energy = max(5, energy)
            carbon = round(energy * factor + np.random.normal(0, energy * 0.03), 3)

            rows.append({
                "server_id": server,
                "region": region,
                "timestamp": ts.strftime("%Y-%m-%d"),
                "cpu_usage": round(cpu, 2),
                "memory_usage": round(mem, 2),
                "storage": round(storage, 2),
                "network_traffic": round(network, 2),
                "temperature": round(temperature, 2),
                "energy_consumption": round(energy, 2),
                "carbon_emission": max(0, carbon),
            })

    df = pd.DataFrame(rows)
    # previous day's emission as a lag feature (used by the model)
    df = df.sort_values(["server_id", "timestamp"])
    df["prev_carbon_emission"] = df.groupby("server_id")["carbon_emission"].shift(1)
    df["prev_carbon_emission"] = df["prev_carbon_emission"].fillna(df["carbon_emission"])
    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = generate()
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "dataset")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cloud_emissions_dataset.csv")
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} rows -> {out_path}")
