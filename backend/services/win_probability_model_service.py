from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_METADATA_PATH = BASE_DIR / "models" / "production_model.json"

_model = None
_scaler = None
_metadata = None


def load_model_metadata() -> dict:
    with open(MODEL_METADATA_PATH, "r") as file:
        return json.load(file)


def get_model_bundle():
    global _model, _scaler, _metadata

    if _model is None or _scaler is None or _metadata is None:
        _metadata = load_model_metadata()

        model_path = BASE_DIR / _metadata["model_path"]
        scaler_path = BASE_DIR / _metadata["scaler_path"]

        _model = tf.keras.models.load_model(model_path)
        _scaler = joblib.load(scaler_path)

    return _model, _scaler, _metadata


def predict_home_win_probability(features: dict) -> float:
    model, scaler, metadata = get_model_bundle()

    feature_columns = metadata["feature_columns"]

    missing_features = [
        column for column in feature_columns if column not in features
    ]

    if missing_features:
        raise ValueError(f"Missing model features: {missing_features}")

    feature_row = {
        column: features[column]
        for column in feature_columns
    }

    df = pd.DataFrame([feature_row])

    for column in feature_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df[feature_columns].isna().any().any():
        invalid_columns = df[feature_columns].columns[
            df[feature_columns].isna().any()
        ].tolist()

        raise ValueError(f"Invalid numeric model features: {invalid_columns}")

    X = df[feature_columns].astype(float).values
    X_scaled = scaler.transform(X)

    prediction = model.predict(X_scaled, verbose=0).ravel()[0]

    return float(np.clip(prediction, 0.0, 1.0))