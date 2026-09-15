import sys, os
import pandas as pd
import xgboost as xgb
from sklearn.metrics import precision_score, recall_score

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_PATH, MODEL_PATH

# columns the model is allowed to learn from
FEATURE_COLUMNS = [
    "unit_price",
    "is_admission_season",
    "is_weekend",
    "sales_roll7_avg",
    "sales_roll14_avg",
    "sales_trend_ratio",
    "days_of_cover",
    "supplier_lead_time_days",
    "lead_time_roll14_avg",
    "lead_time_delay_flag",
    "admission_season_next_30d",
    "day_of_week",
]
LABEL_COLUMN = "label_stockout_next_7d"


def time_based_split(df: pd.DataFrame, test_fraction: float = 0.2):
    df = df.sort_values("date")
    cutoff_idx = int(len(df) * (1 - test_fraction))
    cutoff_date = df.iloc[cutoff_idx]["date"]

    train_df = df[df["date"] < cutoff_date]
    test_df = df[df["date"] >= cutoff_date]
    print(f"Train: {len(train_df):,} rows (before {cutoff_date.date()})")
    print(f"Test:  {len(test_df):,} rows (on/after {cutoff_date.date()})")
    return train_df, test_df


def train_model():
    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=["date"])
    train_df, test_df = time_based_split(df)

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[LABEL_COLUMN]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[LABEL_COLUMN]

    n_pos = y_train.sum()
    n_neg = len(y_train) - n_pos
    scale_pos_weight = n_neg / max(n_pos, 1)
    print(f"\nscale_pos_weight = {scale_pos_weight:.2f} "
          f"(train set has {n_pos:,} positives / {n_neg:,} negatives)")

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",
        random_state=42,
    )

    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    print(f"\nQuick check @ 0.5 threshold:")
    print(f"  Precision: {precision_score(y_test, y_pred):.3f}")
    print(f"  Recall:    {recall_score(y_test, y_pred):.3f}")

    importances = pd.Series(model.feature_importances_, index=FEATURE_COLUMNS)
    importances = importances.sort_values(ascending=False)
    print("\nTop feature importances:")
    print(importances.head(8).to_string())

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save_model(MODEL_PATH)
    print(f"\nModel saved -> {MODEL_PATH}")


if __name__ == "__main__":
    train_model()
    