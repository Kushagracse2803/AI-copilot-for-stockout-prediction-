import sys, os
import pandas as pd
import xgboost as xgb

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_PATH, PROCESSED_DATA_PATH
from llm.explain import generate_explanation

FEATURE_COLUMNS = [
    "unit_price", "is_admission_season", "is_weekend",
    "sales_roll7_avg", "sales_roll14_avg", "sales_trend_ratio",
    "days_of_cover", "supplier_lead_time_days", "lead_time_roll14_avg",
    "lead_time_delay_flag", "admission_season_next_30d", "day_of_week",
]


def predict_and_explain(product_id: str, branch: str):
    # --- load model + latest data for this product ---
    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)

    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=["date"])
    row = df[(df["product_id"] == product_id) & (df["branch"] == branch)].sort_values("date").iloc[-1]

    # --- get real risk score ---
    X = pd.DataFrame([row[FEATURE_COLUMNS]])
    risk_score = float(model.predict_proba(X)[0, 1])

    # --- get real top drivers (importance AND actual value) ---
    importances = model.feature_importances_
    drivers = sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True)[:3]
    top_drivers = [
        {"feature": f, "importance": float(v), "actual_value": float(row[f])}
        for f, v in drivers
    ]

    print(f"Product: {product_id} | Branch: {branch}")
    print(f"Risk score: {risk_score:.2%}")
    print(f"Top drivers: {top_drivers}\n")

    # --- send to LLM ---
    explanation = generate_explanation(product_id, branch, risk_score, top_drivers)
    print("Explanation:\n", explanation)


if __name__ == "__main__":
    predict_and_explain(product_id="BOOK_SChand_5_Maths", branch="Main Market")