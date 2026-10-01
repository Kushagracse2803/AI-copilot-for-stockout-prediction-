# These numbers come directly from data/documents/supplier_terms.txt and
# safety_stock_policy.txt. Kept here as code (not re-retrieved via RAG every
# time) because they are fixed business rules, not narrative explanations -
# exact numbers should live in code, not be re-read from text each time.

PUBLISHER_MIN_ORDER_QTY = {
    "S Chand": 50,
    "Oxford": 30,
    "NCERT": 100,
    "Navneet": 40,
    "Full Circle": 20,
}
DEFAULT_MIN_ORDER_QTY = 20  # for notebooks/stationery (no publisher)

PUBLISHER_LEAD_TIME_DAYS = {
    "S Chand": 7,
    "Oxford": 9,
    "NCERT": 14,
    "Navneet": 6,
    "Full Circle": 10,
}
DEFAULT_LEAD_TIME_DAYS = 7


def get_safety_stock(category: str, is_admission_season: bool) -> int:
    if category == "Book":
        return 25 if is_admission_season else 10
    elif category == "Notebook":
        return 40 if is_admission_season else 20
    else:  # Stationery
        return 15


def get_min_order_qty(publisher) -> int:
    if publisher and publisher in PUBLISHER_MIN_ORDER_QTY:
        return PUBLISHER_MIN_ORDER_QTY[publisher]
    return DEFAULT_MIN_ORDER_QTY


def get_lead_time(publisher) -> int:
    if publisher and publisher in PUBLISHER_LEAD_TIME_DAYS:
        return PUBLISHER_LEAD_TIME_DAYS[publisher]
    return DEFAULT_LEAD_TIME_DAYS