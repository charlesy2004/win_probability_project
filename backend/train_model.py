import os
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupShuffleSplit
from xgboost import XGBClassifier
from db.session import session_local
from db.models import HistoricalGameState


MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "win_probability_model.pkl")

FEATURE_COLUMNS = [
    "score_diff",
    "seconds_remaining",
    "game_progress",
    "period",
    "home_score",
    "away_score",
]

def load_training_data():
    db = session_local()
    try:
        rows = db.query(HistoricalGameState).all()
        data = [
            {
                "game_id": row.game_id,
                "score_diff": row.score_diff,
                "seconds_remaining": row.seconds_remaining,
                "game_progress": row.game_progress,
                "period": row.period,
                "home_score": row.home_score,
                "away_score": row.away_score,
                "home_team_won": row.home_team_won,
            }
            for row in rows
        ]
        df = pd.DataFrame(data)
        return df
    finally:        db.close()

def train_model():
    df = load_training_data()
    if df.empty:
        raise ValueError("No training data available")
    df = df.dropna(subset=FEATURE_COLUMNS + ["home_team_won"])
    X = df[FEATURE_COLUMNS]
    y = df["home_team_won"]
    groups = df["game_id"]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    # X_train, X_test, y_train, y_test = train_test_split(
    #     X,
    #     y,
    #     test_size=0.2,
    #     random_state=42,
    #     stratify=y,
    # )

    logistic_model = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000)),
    ])
    logistic_model.fit(X_train, y_train)
    y_pred = logistic_model.predict(X_test)
    y_proba = logistic_model.predict_proba(X_test)[:, 1]
    
    xgb_model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    xgb_model.fit(X_train, y_train)
    y_pred_xgb = xgb_model.predict(X_test)
    y_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)
    print(f"Model Accuracy: {accuracy:.4f}")
    print(f"Model ROC AUC: {roc_auc:.4f}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    accuracy_xgb = accuracy_score(y_test, y_pred_xgb)
    roc_auc_xgb = roc_auc_score(y_test, y_proba_xgb)
    print(f"XGBoost Model Accuracy: {accuracy_xgb:.4f}")
    print(f"XGBoost Model ROC AUC: {roc_auc_xgb:.4f}")
    print("XGBoost Classification Report:")
    print(classification_report(y_test, y_pred_xgb))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(
        {
            "model": logistic_model,
            "feature_columns": FEATURE_COLUMNS,
            "model_type": "logistic_regression",
        },
        "models/logistic_win_probability_model.pkl",
    )

    joblib.dump(
        {
            "model": xgb_model,
            "feature_columns": FEATURE_COLUMNS,
            "model_type": "xgboost",
        },
        "models/xgboost_win_probability_model.pkl",
    )
if __name__ == "__main__":    train_model()