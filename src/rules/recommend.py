import sys, os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_PATH
from rules.inventory_rules import (
    calculate_order_quantity, decide_source, get_priority, calculate_expected_arrival_days
)
from rules.policy_lookup import get_safety_stock, get_min_order_qty, get_lead_time


def generate_recommendation(product_id: str, branch: str, risk_score: float) -> dict:
    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=["date"])

    # --- this product's latest row at this branch ---
    product_rows = df[df["product_id"] == product_id]
    row = product_rows[product_rows["branch"] == branch].sort_values("date").iloc[-1]

    category = row["category"]
    publisher = row["publisher"] if pd.notna(row["publisher"]) else None
    is_admission = bool(row["is_admission_season"])

    # --- policy lookups (fixed business rules) ---
    safety_stock = get_safety_stock(category, is_admission)
    min_order_qty = get_min_order_qty(publisher)
    lead_time = get_lead_time(publisher)

    # --- other branches' latest data, for transfer decision ---
    other_branches = []
    for other_branch in product_rows["branch"].unique():
        if other_branch == branch:
            continue
        other_row = product_rows[product_rows["branch"] == other_branch].sort_values("date").iloc[-1]
        other_branches.append({
            "branch": other_branch,
            "inventory": float(other_row["inventory_end_of_day"]),
            "safety_stock": safety_stock,  # same category = same safety stock rule
        })

    # --- run the deterministic calculations (Python, not LLM) ---
    source = decide_source(
        current_branch_inventory=float(row["inventory_end_of_day"]),
        current_branch_safety_stock=safety_stock,
        other_branches=other_branches,
    )

    order_qty = calculate_order_quantity(
        avg_daily_demand=float(row["sales_roll7_avg"]),
        publisher_min_order_qty=min_order_qty,
    )

    priority = get_priority(risk_score)
    arrival_days = calculate_expected_arrival_days(source["source_type"], lead_time)

    return {
        "product_id": product_id,
        "branch": branch,
        "risk_score": risk_score,
        "priority": priority,
        "recommended_qty": order_qty if source["source_type"] == "supplier_order" else source["max_transferable_qty"],
        "source_type": source["source_type"],
        "source_branch": source["source_branch"],
        "expected_arrival_days": arrival_days,
        "safety_stock_threshold": safety_stock,
        "status": "draft",  # NEVER auto-approved - project safety requirement
    }


if __name__ == "__main__":
    result = generate_recommendation(
        product_id="BOOK_SChand_5_Maths",
        branch="Main Market",
        risk_score=0.82,
    )
    for k, v in result.items():
        print(f"{k}: {v}")