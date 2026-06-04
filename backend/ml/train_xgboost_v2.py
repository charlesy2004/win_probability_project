from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from xgboost import XGBClassifier

from ml.features import MODEL_FEATURE_COLUMNS, TARGET_COLUMN


MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def load_training_data(path: str) -> pd.DataFrame:
    input_path = Path(path)

    if input_path.suffix == ".parquet":
        return pd.read_parquet(input_path)

    if input_path.suffix == ".csv":
        return pd.read_csv(input_path)

    raise ValueError(f"Unsupported file type: {input_path.suffix}")


def split_by_game(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
):
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=test_size,
        random_state=random_state,
    )

    groups = df["game_id"]

    train_idx, test_idx = next(
        splitter.split(df, df[TARGET_COLUMN], groups=groups)
    )

    train_df = df.iloc[train_idx].copy()
    test_df = df.iloc[test_idx].copy()

    return train_df, test_df


def build_model() -> XGBClassifier:
    return XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.85,
        colsample_bytree=0.85,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        random_state=42,
        n_jobs=-1,
    )


def evaluate_model(y_true, y_pred_proba) -> dict:
    y_pred = (y_pred_proba >= 0.5).astype(int)

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "roc_auc": float(roc_auc_score(y_true, y_pred_proba)),
        "log_loss": float(log_loss(y_true, y_pred_proba)),
        "brier_score": float(brier_score_loss(y_true, y_pred_proba)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="ml/data/training_features.parquet",
    )
    parser.add_argument(
        "--model-output",
        default="models/win_probability_xgboost_v2.pkl",
    )
    parser.add_argument(
        "--metrics-output",
        default="models/win_probability_xgboost_metrics_v2.json",
    )
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

    X_train = train_df[MODEL_FEATURE_COLUMNS].astype(float)
    y_train = train_df[TARGET_COLUMN].astype(int)

    X_test = test_df[MODEL_FEATURE_COLUMNS].astype(float)
    y_test = test_df[TARGET_COLUMN].astype(int)

    print("Training XGBoost")
    model = build_model()

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_test, y_test)],
        verbose=True,
    )

    print("Evaluating")
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    metrics = evaluate_model(y_test, y_pred_proba)

    print("Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")

    print("Saving model artifacts")
    joblib.dump(model, args.model_output)

    output = {
        "model_type": "xgboost",
        "feature_columns": MODEL_FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "metrics": metrics,
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "train_games": int(train_df["game_id"].nunique()),
        "test_games": int(test_df["game_id"].nunique()),
        "xgboost_params": model.get_params(),
    }

    with open(args.metrics_output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved model to {args.model_output}")
    print(f"Saved metrics to {args.metrics_output}")


if __name__ == "__main__":
    main()