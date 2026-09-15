import numpy as np
import pandas as pd
from datetime import timedelta

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    BRANCHES, PUBLISHERS, CLASSES, SUBJECTS, NOTEBOOK_VARIANTS,
    STATIONERY_ITEMS, N_DAYS, RANDOM_SEED, RAW_DATA_PATH
)


def build_product_catalog():
    """Turns our config lists into one flat list of real products."""
    products = []

    for publisher in PUBLISHERS:
        for cls in CLASSES:
            for subject in SUBJECTS:
                products.append({
                    "product_id": f"BOOK_{publisher}_{cls}_{subject}".replace(" ", ""),
                    "category": "Book",
                    "publisher": publisher,
                    "class": cls,
                    "subject": subject,
                    "demand_profile": "spike_admission",  # big spike, admission season only
                })

    for notebook_type, pages in NOTEBOOK_VARIANTS:
        products.append({
            "product_id": f"NB_{notebook_type}_{pages}".replace(" ", ""),
            "category": "Notebook",
            "publisher": None,
            "class": None,
            "subject": f"{notebook_type} ({pages} pages)",
            "demand_profile": "steady_with_bump",  # steady, moderate admission bump
        })

    for item in STATIONERY_ITEMS:
        products.append({
            "product_id": f"STY_{item}".replace(" ", ""),
            "category": "Stationery",
            "publisher": None,
            "class": None,
            "subject": item,
            "demand_profile": "steady",  # steady, small admission bump
        })

    return products


def is_admission_season(date: pd.Timestamp) -> bool:
    """April 1 to June 15 - when parents buy the new class's full booklist."""
    return (date.month == 4) or (date.month == 5) or (date.month == 6 and date.day <= 15)


def generate_synthetic_data() -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    catalog = build_product_catalog()

    start_date = pd.Timestamp("2025-01-01")
    dates = [start_date + timedelta(days=d) for d in range(N_DAYS)]

    rows = []

    for product in catalog:
        base_demand = rng.uniform(3, 15)          # avg units sold/day (books/notebooks sell in smaller daily qty than a detergent SKU)
        unit_price = rng.uniform(40, 450)
        base_lead_time = rng.integers(4, 12)        # publishers/distributors can be slower than a local supplier

        # how strongly admission season boosts demand, based on product type
        if product["demand_profile"] == "spike_admission":
            admission_multiplier = 6.0
        elif product["demand_profile"] == "steady_with_bump":
            admission_multiplier = 2.5
        else:
            admission_multiplier = 1.4

        for branch in BRANCHES:
            branch_factor = rng.uniform(0.7, 1.3)

            inventory = rng.uniform(40, 120)
            reorder_point = base_demand * branch_factor * base_lead_time * 1.2
            order_qty = base_demand * branch_factor * 20

            pending_delivery_day = None
            pending_delivery_qty = 0

            for day_idx, date in enumerate(dates):
                admission = is_admission_season(date)
                is_weekend = date.dayofweek >= 5

                seasonality = 1.1 if is_weekend else 1.0
                admission_uplift = admission_multiplier if admission else 1.0
                noise = rng.normal(1.0, 0.2)
                demand = max(
                    0,
                    base_demand * branch_factor * seasonality * admission_uplift * noise
                )
                actual_sales = min(demand, inventory)

                lead_time_today = base_lead_time
                if rng.random() < 0.05:
                    lead_time_today += rng.integers(3, 8)

                if pending_delivery_day == day_idx:
                    inventory += pending_delivery_qty
                    pending_delivery_day = None
                    pending_delivery_qty = 0

                inventory -= actual_sales
                inventory = max(inventory, 0)

                if inventory <= reorder_point and pending_delivery_day is None:
                    pending_delivery_day = day_idx + lead_time_today
                    pending_delivery_qty = order_qty

                rows.append({
                    "date": date,
                    "product_id": product["product_id"],
                    "category": product["category"],
                    "publisher": product["publisher"],
                    "class": product["class"],
                    "subject": product["subject"],
                    "branch": branch,
                    "unit_price": round(unit_price, 2),
                    "is_admission_season": int(admission),
                    "is_weekend": int(is_weekend),
                    "units_sold": round(actual_sales, 1),
                    "demand_raw": round(demand, 1),
                    "inventory_end_of_day": round(inventory, 1),
                    "supplier_lead_time_days": lead_time_today,
                    "reorder_point": round(reorder_point, 1),
                    "is_stockout_today": int(inventory <= 0),
                })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_synthetic_data()
    os.makedirs(os.path.dirname(RAW_DATA_PATH), exist_ok=True)
    df.to_csv(RAW_DATA_PATH, index=False)
    print(f"Generated {len(df):,} rows -> {RAW_DATA_PATH}")
    print(f"Total products: {df['product_id'].nunique()}")
    print(f"Stockout rate: {df['is_stockout_today'].mean():.2%}")
    print(df.head())