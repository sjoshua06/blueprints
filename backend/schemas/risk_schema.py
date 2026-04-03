from pydantic import BaseModel, Field
from typing import Optional


# ── Request Models ───────────────────────────────────────────────────────────

class RiskPredictionRequest(BaseModel):
    """Request body for single-supplier risk prediction."""
    supplier_name: str = Field(..., description="Name of the supplier")
    country: str = Field("Global", description="Supplier's country of operation")
    availability_score: float = Field(0.5, ge=0.0, le=1.0)
    reliability_score: float = Field(50.0, ge=0.0, le=100.0)
    defect_rate: float = Field(0.0, ge=0.0, le=1.0)
    on_time_delivery_rate: float = Field(50.0, ge=0.0, le=100.0)
    avg_lead_time_days: float = Field(30.0, ge=0.0)


# ── Response Models ──────────────────────────────────────────────────────────

class RiskFactor(BaseModel):
    """A single contributing factor in the risk breakdown."""
    factor: str = Field(..., description="Human-readable factor name")
    category: str = Field(..., description="Category: Performance, Quality, Delivery, Supply, External")
    impact: float = Field(..., description="Impact weight on the final score (0–100)")
    detail: str = Field(..., description="Human-readable detail about this factor")
    risk_level: str = Field(..., description="LOW / MEDIUM / HIGH / CRITICAL")


class NewsArticle(BaseModel):
    """A news article with its sentiment analysis."""
    title: str = ""
    source: str = ""
    url: str = ""
    published_at: str = ""
    compound: float = Field(0.0, description="VADER compound sentiment score (-1 to +1)")
    sentiment: str = Field("NEUTRAL", description="POSITIVE / NEGATIVE / NEUTRAL")


class RiskPredictionResponse(BaseModel):
    """Enriched risk prediction response with factor breakdown and news."""
    risk_score: float = Field(..., description="Final risk score (0–100)")
    risk_level: str = Field(..., description="LOW / MEDIUM / HIGH / CRITICAL")
    internal_risk_score: float = Field(..., description="Internal formula score (0–100)")
    external_risk_score: float = Field(..., description="News sentiment score (0–100)")
    factors: list[RiskFactor] = Field(default_factory=list, description="Contributing factors, ranked by impact")
    adaptive_weights: dict = Field(default_factory=dict, description="The dynamic ML weights used")
    bom_summary: dict = Field(default_factory=dict, description="Summary of the BOM history for this supplier")
    news_articles: list[NewsArticle] = Field(default_factory=list, description="Relevant news articles with sentiment")


class SupplierRiskResult(BaseModel):
    """Result for a single supplier in the predict-all response."""
    supplier_id: int
    supplier_name: str
    country: Optional[str] = None
    availability_score: float
    reliability_score: float
    defect_rate: float
    on_time_delivery_rate: float
    avg_lead_time_days: float
    risk_score: float
    risk_level: str
    internal_risk_score: float
    external_risk_score: float
    factors: list[RiskFactor] = Field(default_factory=list)
    adaptive_weights: dict = Field(default_factory=dict)
    bom_summary: dict = Field(default_factory=dict)
    news_articles: list[NewsArticle] = Field(default_factory=list)


class PredictAllResponse(BaseModel):
    """Response for the predict-all endpoint."""
    message: str
    data: list[SupplierRiskResult]