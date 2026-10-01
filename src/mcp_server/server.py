import sys, os
import pandas as pd
import xgboost as xgb
from mcp.server.mcpserver import MCPServer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_PATH, MODEL_PATH
from rag.retriever import retrieve_relevant_chunks
from rules.policy_lookup import get_lead_time
from rules.recommend import generate_recommendation

mcp = MCPServer("om-traders-inventory")

FEATURE_COLUMNS = [
    "unit_price", "is_admission_season", "is_weekend",
    "sales_roll7_avg", "sales_roll14_avg", "sales_trend_ratio",
    "days_of_cover", "supplier_lead_time_days", "lead_time_roll14_avg",
    "lead_time_delay_flag", "admission_season_next_30d", "day_of_week",
]


@mcp.tool()
def get_inventory(product_id: str, branch: str) -> dict:
    """
    Get the current inventory level for a specific product at a specific branch.
    Use this when you need to know how much stock is currently available.

    Args:
        product_id: The product ID, e.g. 'BOOK_SChand_5_Maths'
        branch: The branch name, e.g. 'Main Market'
    """
    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=["date"])
    row = df[(df["product_id"] == product_id) & (df["branch"] == branch)].sort_values("date")

    if row.empty:
        return {"error": f"No data found for {product_id} at {branch}"}

    latest = row.iloc[-1]
    return {
        "product_id": product_id,
        "branch": branch,
        "current_inventory": float(latest["inventory_end_of_day"]),
        "days_of_cover": float(latest["days_of_cover"]),
        "as_of_date": str(latest["date"].date()),
    }


@mcp.tool()
def get_demand_forecast(product_id: str, branch: str) -> dict:
    """
    Get the predicted stockout risk score for a product at a branch, using
    the trained ML model. Use this when you need to know how likely a
    product is to stock out in the next 7 days.

    Args:
        product_id: The product ID, e.g. 'BOOK_SChand_5_Maths'
        branch: The branch name, e.g. 'Main Market'
    """
    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=["date"])
    row = df[(df["product_id"] == product_id) & (df["branch"] == branch)].sort_values("date")

    if row.empty:
        return {"error": f"No data found for {product_id} at {branch}"}

    latest = row.iloc[-1]
    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)

    X = pd.DataFrame([latest[FEATURE_COLUMNS]])
    risk_score = float(model.predict_proba(X)[0, 1])

    return {
        "product_id": product_id,
        "branch": branch,
        "stockout_risk_score": round(risk_score, 4),
        "risk_horizon_days": 7,
    }


@mcp.tool()
def check_supplier_lead_time(publisher: str) -> dict:
    """
    Get the standard delivery lead time (in days) for a given publisher.
    Use this when you need to know how long a supplier order will take to arrive.

    Args:
        publisher: The publisher name, e.g. 'S Chand', 'Oxford', 'NCERT'
    """
    lead_time = get_lead_time(publisher)
    return {"publisher": publisher, "lead_time_days": lead_time}


@mcp.tool()
def retrieve_policy(query: str) -> dict:
    """
    Search the company's policy documents (safety stock rules, supplier
    terms, replenishment policy) for text relevant to a question. Use this
    when you need to ground a recommendation in actual company policy.

    Args:
        query: A natural language question, e.g. 'safety stock for books during admission season'
    """
    chunks = retrieve_relevant_chunks(query, top_k=2)
    return {
        "query": query,
        "results": [{"source": c["source"], "text": c["text"]} for c in chunks],
    }


@mcp.tool()
def create_replenishment_draft(product_id: str, branch: str, risk_score: float) -> dict:
    """
    Create a DRAFT replenishment recommendation (order quantity, source,
    priority) based on company rules. This NEVER creates a confirmed order -
    it always returns status 'draft', requiring human planner approval before
    any real action is taken. Use this as the final step after assessing risk.

    Args:
        product_id: The product ID, e.g. 'BOOK_SChand_5_Maths'
        branch: The branch name, e.g. 'Main Market'
        risk_score: The stockout risk score (0.0 to 1.0), from get_demand_forecast
    """
    recommendation = generate_recommendation(product_id, branch, risk_score)
    recommendation["status"] = "draft"  # enforced here, cannot be overridden
    return recommendation


if __name__ == "__main__":
    mcp.run()