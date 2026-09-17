"""
Optional LSTM sequence model for multi-day carbon emission forecasting.

This is provided as an advanced/extension module (per the project brief's
mention of LSTM) for forecasting emission trends over a rolling window,
which captures temporal patterns (weekly seasonality, trend) that the
per-record Random Forest / XGBoost models do not see.

Requires `tensorflow` which is NOT in requirements.txt by default (it is a
large dependency, and unnecessary for the core FastAPI service). Install it
separately if you want to use this module:

    pip install tensorflow==2.16.1

Run directly:  python -m app.ml.lstm_model
"""
import os
import numpy as np
import pandas as pd

from app.ml.generate_dataset import generate

SEQUENCE_LEN = 14  # look back 14 days to predict the next day


def _build_sequences(series: np.ndarray, seq_len: int = SEQUENCE_LEN):
    X, y = [], []
    for i in range(len(series) - seq_len):
        X.append(series[i:i + seq_len])
        y.append(series[i + seq_len])
    return np.array(X), np.array(y)


def train_lstm(server_id: str = "AWS001", epochs: int = 15):
    try:
        import tensorflow as tf
        from tensorflow.keras import layers, models
    except ImportError as exc:
        raise SystemExit(
            "tensorflow is not installed. Run: pip install tensorflow==2.16.1"
        ) from exc

    df = generate()
    df = df[df["server_id"] == server_id].sort_values("timestamp")
    series = df["carbon_emission"].values.astype("float32")

    # Normalize
    mean, std = series.mean(), series.std()
    norm_series = (series - mean) / std

    X, y = _build_sequences(norm_series)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    split = int(len(X) * 0.85)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    model = models.Sequential([
        layers.Input(shape=(SEQUENCE_LEN, 1)),
        layers.LSTM(64, return_sequences=True),
        layers.LSTM(32),
        layers.Dense(16, activation="relu"),
        layers.Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    model.fit(X_train, y_train, epochs=epochs, batch_size=16,
              validation_data=(X_test, y_test), verbose=1)

    out_path = os.path.join(os.path.dirname(__file__), "model_lstm.keras")
    model.save(out_path)
    print(f"LSTM model saved -> {out_path}")
    print(f"Normalization stats: mean={mean:.3f}, std={std:.3f}")
    return model


if __name__ == "__main__":
    train_lstm()
