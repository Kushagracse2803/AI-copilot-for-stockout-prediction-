import sys, os
import pandas as pd
import xgboost as xgb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_PATH, PROCESSED_DATA_PATH
from rules.recommend import generate_recommendation
from pipeline import run_full_pipeline
from api.schemas import StockoutRiskResponse, RecommendationResponse, ExplanationResponse, ProductResponse

FEATURE_COLUMNS = [
    "unit_price", "is_admission_season", "is_weekend",
    "sales_roll7_avg", "sales_roll14_avg", "sales_trend_ratio",
    "days_of_cover", "supplier_lead_time_days", "lead_time_roll14_avg",
    "lead_time_delay_flag", "admission_season_next_30d", "day_of_week",
]

app = FastAPI(title="Om Traders Stockout Copilot API")

# allow the Vite dev server (and other local dev ports) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# load the model once, when the server starts - not on every request
model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)


def get_risk_level(risk_score: float) -> str:
    if risk_score < 0.20:
        return "Low"
    elif risk_score < 0.50:
        return "Medium"
    else:
        return "High"


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/products", response_model=list[ProductResponse])
def list_products():
    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=["date"])
    latest = df.sort_values("date").groupby(["product_id", "branch"], as_index=False).last()
    return [
        ProductResponse(
            product_id=row["product_id"],
            branch=row["branch"],
            category=row["category"],
            publisher=None if pd.isna(row["publisher"]) else row["publisher"],
            subject=None if pd.isna(row["subject"]) else row["subject"],
        )
        for _, row in latest.iterrows()
    ]


@app.get("/predict/{product_id}/{branch}", response_model=StockoutRiskResponse)
def predict_risk(product_id: str, branch: str):
    df = pd.read_csv(PROCESSED_DATA_PATH, parse_dates=["date"])
    row = df[(df["product_id"] == product_id) & (df["branch"] == branch)].sort_values("date")

    if row.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {product_id} at {branch}")

    latest = row.iloc[-1]
    X = pd.DataFrame([latest[FEATURE_COLUMNS]])
    risk_score = float(model.predict_proba(X)[0, 1])

    return StockoutRiskResponse(
        product_id=product_id,
        branch=branch,
        risk_score=round(risk_score, 4),
        risk_level=get_risk_level(risk_score),
        days_of_cover=float(latest["days_of_cover"]),
        as_of_date=str(latest["date"].date()),
    )


@app.get("/recommend/{product_id}/{branch}", response_model=RecommendationResponse)
def recommend(product_id: str, branch: str):
    # first get the real risk score (reuse the same logic as /predict)
    risk_result = predict_risk(product_id, branch)
    recommendation = generate_recommendation(product_id, branch, risk_result.risk_score)
    return RecommendationResponse(**recommendation)


@app.get("/explain/{product_id}/{branch}", response_model=ExplanationResponse)
def explain(product_id: str, branch: str):
    result = run_full_pipeline(product_id, branch)
    return ExplanationResponse(
        product_id=result["product_id"],
        branch=result["branch"],
        risk_score=result["risk_score"],
        explanation=result["explanation"],
        evidence_sources=result["evidence_sources"],
        recommendation=RecommendationResponse(**result["recommendation"]),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)