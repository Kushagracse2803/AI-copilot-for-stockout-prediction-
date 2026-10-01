def calculate_order_quantity(avg_daily_demand: float, publisher_min_order_qty: int, coverage_days: int = 30) -> int:
    """
    Rule from replenishment_policy.txt:
    "Order quantity should cover 30 days of demand, rounded up to the
    nearest publisher minimum order quantity."
    """
    raw_qty = avg_daily_demand * coverage_days
    # round up to the nearest multiple of the publisher's minimum order quantity
    import math
    multiples_needed = math.ceil(raw_qty / publisher_min_order_qty)
    final_qty = multiples_needed * publisher_min_order_qty
    return int(final_qty)


def decide_source(
    current_branch_inventory: float,
    current_branch_safety_stock: float,
    other_branches: list[dict],  # [{"branch": "X", "inventory": 100, "safety_stock": 20}, ...]
) -> dict:
    """
    Rule from replenishment_policy.txt:
    "If another branch has surplus (more than 2x its own safety stock),
    recommend a transfer instead of a new supplier order."
    """
    for branch in other_branches:
        surplus_threshold = branch["safety_stock"] * 2
        if branch["inventory"] > surplus_threshold:
            transferable = branch["inventory"] - surplus_threshold
            return {
                "source_type": "transfer",
                "source_branch": branch["branch"],
                "max_transferable_qty": int(transferable),
            }

    return {"source_type": "supplier_order", "source_branch": None, "max_transferable_qty": 0}


def get_priority(risk_score: float) -> str:
    """Reuses the same thresholds as Piece 2's risk level, for consistency."""
    if risk_score < 0.20:
        return "Low"
    elif risk_score < 0.50:
        return "Medium"
    else:
        return "High"


def calculate_expected_arrival_days(source_type: str, lead_time_days: int) -> int:
    """
    Transfers arrive much faster than supplier orders, per policy
    (same-day to 2 days for transfers vs full supplier lead time).
    """
    if source_type == "transfer":
        return 2  # per replenishment_policy.txt: "same-day to 2 days"
    return lead_time_days


if __name__ == "__main__":
    # quick manual test with made-up example numbers
    qty = calculate_order_quantity(avg_daily_demand=8.5, publisher_min_order_qty=50)
    print(f"Recommended order quantity: {qty} units")

    source = decide_source(
        current_branch_inventory=5,
        current_branch_safety_stock=25,
        other_branches=[
            {"branch": "Station Road", "inventory": 80, "safety_stock": 25},
            {"branch": "College Chowk", "inventory": 30, "safety_stock": 25},
        ],
    )
    print(f"Source decision: {source}")

    priority = get_priority(risk_score=0.82)
    print(f"Priority: {priority}")

    arrival = calculate_expected_arrival_days(source["source_type"], lead_time_days=10)
    print(f"Expected arrival: {arrival} days")