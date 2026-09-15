import sys, os
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RAW_DATA_PATH, PROCESSED_DATA_PATH, STOCKOUT_HORIZON_DAYS

BURN_IN_DAYS = 20  # shuru ke kuch din hata denge (cold-start issue ke wajah se)
ADMISSION_LOOKAHEAD_DAYS = 30  # "agle 30 din mein admission season aa raha hai kya"


def build_features_for_group(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values("date").reset_index(drop=True)

    # --- past-looking (safe) features ---
    g["sales_roll7_avg"] = g["units_sold"].rolling(7, min_periods=1).mean()
    g["sales_roll14_avg"] = g["units_sold"].rolling(14, min_periods=1).mean()

    g["sales_trend_ratio"] = (
        g["sales_roll7_avg"] / g["sales_roll14_avg"].replace(0, np.nan)
    ).fillna(1.0)

    g["days_of_cover"] = (
        g["inventory_end_of_day"] / g["sales_roll7_avg"].replace(0, np.nan)
    ).fillna(g["inventory_end_of_day"])
    g["days_of_cover"] = g["days_of_cover"].clip(upper=365)

    g["lead_time_roll14_avg"] = g["supplier_lead_time_days"].rolling(14, min_periods=1).mean()
    g["lead_time_delay_flag"] = (
        g["supplier_lead_time_days"] > g["lead_time_roll14_avg"] + 1
    ).astype(int)

    # is admission season starting within the next 30 days?
    g["admission_season_next_30d"] = (
        g["is_admission_season"].shift(-1).rolling(ADMISSION_LOOKAHEAD_DAYS, min_periods=1).max()
        .shift(-(ADMISSION_LOOKAHEAD_DAYS - 1))
    ).fillna(0).astype(int)

    g["day_of_week"] = pd.to_datetime(g["date"]).dt.dayofweek

    # --- forward-looking LABEL ---
    g["label_stockout_next_7d"] = (
        g["is_stockout_today"].shift(-1).rolling(STOCKOUT_HORIZON_DAYS, min_periods=1).max()
        .shift(-(STOCKOUT_HORIZON_DAYS - 1))
    ).fillna(0).astype(int)

    return g


def build_features() -> pd.DataFrame:
    df = pd.read_csv(RAW_DATA_PATH, parse_dates=["date"])

    processed_groups = []
    for (product_id, branch), g in df.groupby(["product_id", "branch"]):
        g_feat = build_features_for_group(g)
        g_feat = g_feat.iloc[BURN_IN_DAYS:]
        g_feat = g_feat.iloc[:-STOCKOUT_HORIZON_DAYS]
        processed_groups.append(g_feat)

    result = pd.concat(processed_groups, ignore_index=True)
    return result


if __name__ == "__main__":
    features_df = build_features()
    os.makedirs(os.path.dirname(PROCESSED_DATA_PATH), exist_ok=True)
    features_df.to_csv(PROCESSED_DATA_PATH, index=False)
    print(f"Built features for {len(features_df):,} rows -> {PROCESSED_DATA_PATH}")
    print(f"Positive label rate: {features_df['label_stockout_next_7d'].mean():.2%}")

    cols = ["date", "product_id", "branch", "sales_roll7_avg", "days_of_cover",
             "admission_season_next_30d", "label_stockout_next_7d"]
    print(features_df[cols].head(10).to_string(index=False))