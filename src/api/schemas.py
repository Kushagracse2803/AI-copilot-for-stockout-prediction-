from pydantic import BaseModel, Field
from typing import Optional


class ProductResponse(BaseModel):
    """Shape of one entry in the /products ledger listing."""
    product_id: str
    branch: str
    category: str
    publisher: Optional[str] = None
    subject: Optional[str] = None


class StockoutRiskResponse(BaseModel):
    """Shape of the response when someone asks for a risk prediction."""
    product_id: str
    branch: str
    risk_score: float = Field(..., ge=0.0, le=1.0, description="0 to 1, chance of stockout")
    risk_level: str
    days_of_cover: float
    as_of_date: str


class RecommendationResponse(BaseModel):
    """Shape of the response when someone asks for a replenishment recommendation."""
    product_id: str
    branch: str
    risk_score: float
    priority: str
    recommended_qty: int
    source_type: str
    source_branch: Optional[str] = None
    expected_arrival_days: int
    status: str = "draft"  # NEVER anything else - project safety rule


class ExplanationResponse(BaseModel):
    """Shape of the response for the full pipeline (Piece 1-4 combined)."""
    product_id: str
    branch: str
    risk_score: float
    explanation: str
    evidence_sources: list[str]
    recommendation: RecommendationResponse