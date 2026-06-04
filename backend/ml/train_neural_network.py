import argparse
import json
from pathlib import Path
from xml.parsers.expat import model

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import StandardScaler

from ml.features import MODEL_FEATURE_COLUMNS, TARGET_COLUMN

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def load_training_data(path: str) -> pd.DataFrame:
    input_path = Path(path)
    return pd.read_parquet(input_path)

def split_by_game(df: pd.DataFrame, test_size: float = .2, random_state: int = 42,):
    splitter = GroupShuffleSplit(
        test_size=test_size, 
        n_splits=1, 
        random_state=random_state
    )
    groups = df["game_id"]
    train_idx, test_idx = next(splitter.split(df[TARGET_COLUMN], groups=groups))
    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()
    return train_df, test_df

def build_model(input_dim: int) -> tf.keras.Model:
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(input_dim,)),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dropout(0.20),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dropout(0.10),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), 
        loss='binary_crossentropy', 
        metrics=[
            'accuracy',
            tf.keras.metrics.AUC(name='auc'),
            tf.keras.metrics.Precision(name='precision'),
        ]
    )
    return model

def evaluate_model(y_true: np.ndarray, y_pred_proba: np.ndarray) -> dict:
    y_pred = (y_pred_proba >= 0.5).astype(int)
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "brier_score": brier_score_loss(y_true, y_pred_proba),
        "log_loss": log_loss(y_true, y_pred_proba),
        "auc": roc_auc_score(y_true, y_pred_proba),
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="ml/data/training_features.parquet",
    )
    parser.add_argument(
        "--model-output",
        default="models/win_probability_nn_v1.keras",
    )
    parser.add_argument(
        "--scaler-output",
        default="models/win_probability_nn_scaler_v1.pkl",
    )
    parser.add_argument(
        "--metrics-output",
        default="models/win_probability_nn_metrics_v1.json",
    )
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=2048)
    args = parser.parse_args()

    print("Loading training data")
    df = load_training_data(args.input)

    print(f"Rows loaded: {len(df)}")
    print(f"Features: {MODEL_FEATURE_COLUMNS}")

    missing_columns = [
        column
        for column in MODEL_FEATURE_COLUMNS + [TARGET_COLUMN, "game_id"]
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    df = df.dropna(subset=MODEL_FEATURE_COLUMNS + [TARGET_COLUMN])

    print("Splitting by game_id to avoid leakage")
    train_df, test_df = split_by_game(df)

    print(f"Train rows: {len(train_df)}")
    print(f"Test rows: {len(test_df)}")
    print(f"Train games: {train_df['game_id'].nunique()}")
    print(f"Test games: {test_df['game_id'].nunique()}")

    X_train = train_df[MODEL_FEATURE_COLUMNS].astype(float).values
    y_train = train_df[TARGET_COLUMN].astype(int).values

    X_test = test_df[MODEL_FEATURE_COLUMNS].astype(float).values
    y_test = test_df[TARGET_COLUMN].astype(int).values

    print("Scaling features")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Training neural network")
    model = build_model(input_dim=X_train_scaled.shape[1])

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_auc",
            patience=4,
            mode="max",
            restore_best_weights=True,
        )
    ]

    history = model.fit(
        X_train_scaled,
        y_train,
        validation_split=0.15,
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    print("Evaluating")
    y_pred_proba = model.predict(X_test_scaled, batch_size=args.batch_size).ravel()

    metrics = evaluate_model(y_test, y_pred_proba)

    print("Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")

    print("Saving model artifacts")
    model.save(args.model_output)
    joblib.dump(scaler, args.scaler_output)

    output = {
        "model_type": "neural_network",
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "metrics": metrics,
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_games": int(train_df["game_id"].nunique()),
        "test_games": int(test_df["game_id"].nunique()),
        "epochs_ran": len(history.history["loss"]),
    }

    with open(args.metrics_output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved model to {args.model_output}")
    print(f"Saved scaler to {args.scaler_output}")
    print(f"Saved metrics to {args.metrics_output}")


if __name__ == "__main__":
    main()


    
