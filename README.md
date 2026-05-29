# win_probability_project

## Model Performance

The win probability model was trained on historical NBA play-by-play data using a game-level grouped train/test split to avoid leakage between plays from the same game.

| Model | Accuracy | ROC AUC |
|---|---:|---:|
| Logistic Regression | 0.7320 | 0.8141 |
| XGBoost | 0.7328 | 0.8241 |

XGBoost was selected as the production model because it achieved the highest ROC AUC.