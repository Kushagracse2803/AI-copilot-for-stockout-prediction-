import sys, os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import precision_recall_curve, auc, precision_score, recall_score
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_PATH, MODEL_PATH

FEATURE_COLUMNS = [
    "unit_price", "is_admission_season", "is_weekend",
    "sales_roll7_avg", "sales_roll14_avg", "sales_trend_ratio",
    "days_of_cover", "supplier_lead_time_days", "lead_time_roll14_avg",
    "lead_time_delay_flag", "admission_season_next_30d", "day_of_week",
]
LABEL_COLUMN = "label_stockout_next_7d"


def evaluate_model():
    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=["date"])
    df = df.sort_values("date")

    # same time-based split as training, so we test on the same held-out data
    cutoff_idx = int(len(df) * 0.8)
    cutoff_date = df.iloc[cutoff_idx]["date"]
    test_df = df[df["date"] >= cutoff_date]

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[LABEL_COLUMN]

    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)

    y_proba = model.predict_proba(X_test)[:, 1]

    # --- PR-AUC: overall headline number ---
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
    pr_auc = auc(recalls, precisions)
    print(f"PR-AUC: {pr_auc:.3f}")

    # --- try a few different thresholds, see the trade-off ---
    print("\nThreshold vs Precision vs Recall:")
    print(f"{'Threshold':>10} {'Precision':>10} {'Recall':>10}")
    for t in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
        y_pred = (y_proba >= t).astype(int)
        p = precision_score(y_test, y_pred, zero_division=0)
        r = recall_score(y_test, y_pred, zero_division=0)
        print(f"{t:>10} {p:>10.3f} {r:>10.3f}")

    # --- plot the curve ---
    plt.figure(figsize=(6, 5))
    plt.plot(recalls, precisions)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"Precision-Recall Curve (PR-AUC = {pr_auc:.3f})")
    plt.savefig(os.path.join(os.path.dirname(MODEL_PATH), "pr_curve.png"))
    print(f"\nCurve saved -> {os.path.join(os.path.dirname(MODEL_PATH), 'pr_curve.png')}")


if __name__ == "__main__":
    evaluate_model()