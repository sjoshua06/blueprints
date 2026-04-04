"""
Final Risk API  —  Unified Softmax Attention Risk Score
=======================================================

Combines three data sources into one risk score per supplier:

1. Internal metrics  : reliability, defect, OTD, lead time, availability  (from suppliers + supplier_components tables)
2. News sentiment    : VADER-scored NewsData.io articles  (from news_service.py)
3. Shipping signals  : weather, earthquake, political, GDELT conflict, disaster, air (from shipping_risk_service.py)

A Softmax-Temperature attention mechanism weights all 7 signals so that
the worst signal **exponentially** dominates the final score.

The `dominant_signal` field identifies which of the 7 signals is most
responsible — this is the key input for the upcoming agent orchestration layer.

Endpoints
---------
POST /api/final-risk/             single supplier (pass supplier_id to auto-fetch from DB)
GET  /api/final-risk/{supplier_id} quick lookup by supplier_id (all data from DB)
POST /api/final-risk/predict-all  batch — scores all suppliers for a user_id
"""

from __future__ import annotations

import math
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from db.database import engine
from services.news_service import compute_external_risk
from services.shipping_risk_service import (
    fetch_destination_risks,
    fetch_origin_risks,
    geocode_location,
)

router = APIRouter(prefix="/api/final-risk", tags=["Agentic final risk"])

# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class FinalRiskRequest(BaseModel):
    supplier_id: Optional[int] = None
    user_id: Optional[str] = None          # used to look up destination_port from profiles
    supplier_name: str
    country: str
    # Optional metrics — if omitted and supplier_id given, fetched from DB
    availability_score: Optional[float] = None
    reliability_score: Optional[float] = None
    defect_rate: Optional[float] = None
    on_time_delivery_rate: Optional[float] = None
    avg_lead_time_days: Optional[float] = None


class FinalRiskResponse(BaseModel):
    supplier_name: str
    risk_score: float
    risk_level: str
    dominant_signal: str
    internal_scores: dict
    external_score: float
    shipping_score: float
    adaptive_weights: dict
    shipping_details: dict
    news_details: dict


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _softmax_weights(logits: dict[str, float], temperature: float = 1.5) -> dict[str, float]:
    """Softmax with temperature. Lower temp → worst metric dominates more aggressively."""
    scaled  = {k: v / temperature for k, v in logits.items()}
    max_val = max(scaled.values()) if scaled else 0.0          # numerical stability
    exps    = {k: math.exp(v - max_val) for k, v in scaled.items()}
    total   = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


def _get_destination_port(user_id: str | None) -> str:
    """
    Fetches the user's preferred destination port from the profiles table.
    Falls back to 'Los Angeles, USA' if not set or user_id not provided.
    """
    if not user_id:
        return "Los Angeles, USA"
    try:
        sql = text("SELECT destination_port FROM profiles WHERE user_id = :uid LIMIT 1")
        with engine.connect() as conn:
            row = conn.execute(sql, {"uid": user_id}).first()
        if row and row.destination_port:
            return row.destination_port
    except Exception as e:
        print(f"[DestPort] Could not fetch from profiles: {e}")
    return "Los Angeles, USA"


def _apply_defaults(features: dict) -> dict:
    """Ensure all 5 internal metrics are non-None floats."""
    return {
        "availability_score":    float(features.get("availability_score")    or 0.5),
        "reliability_score":     float(features.get("reliability_score")     or 50.0),
        "defect_rate":           float(features.get("defect_rate")           or 0.0),
        "on_time_delivery_rate": float(features.get("on_time_delivery_rate") or 50.0),
        "avg_lead_time_days":    float(features.get("avg_lead_time_days")    or 30.0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core computation  (all 3 endpoints share this)
# ─────────────────────────────────────────────────────────────────────────────

async def _compute_risk_for_supplier(
    supplier_name: str,
    country: str,
    destination_port: str,
    features: dict,
) -> dict:
    """
    Runs the full 3-source Softmax Attention pipeline and returns a
    FinalRiskResponse-shaped dict.

    Parameters
    ----------
    features : dict with 5 float keys (all defaults already applied)
    """

    # ── 1. News sentiment (sync; cached 24 h per country) ────────────────────
    try:
        news_result = compute_external_risk(supplier_name, country)
        news_score  = float(news_result.get("external_risk_score", 0.4))
    except Exception as e:
        print(f"[News] {supplier_name}: {e}")
        news_score  = 0.4
        news_result = {"sentiment_summary": {}, "news_articles": []}

    # ── 2. Shipping signals (async; cached 1 h per lat/lon) ──────────────────
    try:
        origin_geo   = await geocode_location(country)
        dest_geo     = await geocode_location(destination_port)
        origin_risks = await fetch_origin_risks(country, origin_geo)
        dest_risks   = await fetch_destination_risks(dest_geo, destination_port)

        origin_delay = (
            origin_risks["origin_weather"]["delay_days"]  +
            origin_risks["origin_quake"]["delay_days"]    +
            origin_risks["origin_politics"]["delay_days"] +
            origin_risks["origin_conflict"]["delay_days"]
        )
        dest_delay = (
            dest_risks["dest_weather"]["delay_days"]   +
            dest_risks["dest_disasters"]["delay_days"] +
            dest_risks["dest_air"]["delay_days"]
        )
        total_delay    = min(origin_delay + dest_delay, 14)
        shipping_score = total_delay / 14.0
        shipping_details = {
            "total_delay_days": total_delay,
            "destination_port": destination_port,
            "origin_risks":     origin_risks,
            "dest_risks":       dest_risks,
        }
    except Exception as e:
        print(f"[Shipping] {supplier_name}: {e}")
        shipping_score   = 0.3
        shipping_details = {"error": str(e), "total_delay_days": 0, "destination_port": destination_port}

    # ── 3. Normalize all 7 signals → 0-1 (higher = worse) ───────────────────
    raw_risks = {
        "reliability_risk":  1.0 - (features["reliability_score"] / 100.0),
        "defect_risk":       min(features["defect_rate"], 1.0),
        "otd_risk":          1.0 - (features["on_time_delivery_rate"] / 100.0),
        "lead_time_risk":    min(features["avg_lead_time_days"] / 60.0, 1.0),   # 60 days = full risk
        "availability_risk": 1.0 - features["availability_score"],
        "news_risk":         news_score,
        "shipping_risk":     shipping_score,
    }

    # ── 4. Softmax Attention — domain priors + exponential severity scaling ───
    DOMAIN_PRIORS = {
        "reliability_risk":  0.15,
        "defect_risk":       0.15,
        "otd_risk":          0.15,
        "lead_time_risk":    0.10,
        "availability_risk": 0.10,
        "news_risk":         0.15,
        "shipping_risk":     0.20,
    }

    # Logit = prior × (1 + risk² × 5)
    # A signal at 0.9 risk gets ~5× more logit than one at 0.1 → exponential emphasis
    logits = {
        key: DOMAIN_PRIORS[key] * (1.0 + (raw_risks[key] ** 2) * 5.0)
        for key in DOMAIN_PRIORS
    }
    adaptive_weights = _softmax_weights(logits, temperature=1.2)

    # ── 5. Weighted score + dominant signal ───────────────────────────────────
    final_score     = sum(adaptive_weights[k] * raw_risks[k] for k in raw_risks)
    dominant_signal = max(adaptive_weights, key=adaptive_weights.get)

    final_100 = round(final_score * 100, 2)
    if final_100 >= 75:
        risk_level = "CRITICAL"
    elif final_100 >= 50:
        risk_level = "HIGH"
    elif final_100 >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "supplier_name":    supplier_name,
        "risk_score":       final_100,
        "risk_level":       risk_level,
        "dominant_signal":  dominant_signal,
        "internal_scores":  {k: round(v, 4) for k, v in raw_risks.items()},
        "external_score":   round(news_score * 100, 2),
        "shipping_score":   round(shipping_score * 100, 2),
        "adaptive_weights": {k: round(v, 4) for k, v in adaptive_weights.items()},
        "shipping_details": shipping_details,
        "news_details": {
            "sentiment_summary": news_result.get("sentiment_summary", {}),
            "top_articles":      news_result.get("news_articles", [])[:3],
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# SQL helpers
# ─────────────────────────────────────────────────────────────────────────────

_SUPPLIER_BY_ID_SQL = text("""
    SELECT
        s.supplier_name,
        s.country,
        s.reliability_score,
        s.defect_rate,
        s.on_time_delivery_rate,
        s.avg_lead_time_days,
        COALESCE(
            (SELECT AVG(sc.availability_score)
             FROM supplier_components sc
             WHERE sc.supplier_id = s.supplier_id),
            0.5
        ) AS avg_availability
    FROM suppliers s
    WHERE s.supplier_id = :sid
""")

_ALL_SUPPLIERS_SQL = text("""
    SELECT
        s.supplier_id,
        s.supplier_name,
        s.country,
        s.reliability_score,
        s.defect_rate,
        s.on_time_delivery_rate,
        s.avg_lead_time_days,
        COALESCE(
            (SELECT AVG(sc.availability_score)
             FROM supplier_components sc
             WHERE sc.supplier_id = s.supplier_id),
            0.5
        ) AS avg_availability
    FROM suppliers s
    WHERE s.user_id = :uid
""")


def _row_to_features(row) -> dict:
    return {
        "availability_score":    float(getattr(row, "avg_availability", None)       or 0.5),
        "reliability_score":     float(getattr(row, "reliability_score", None)      or 50.0),
        "defect_rate":           float(getattr(row, "defect_rate", None)            or 0.0),
        "on_time_delivery_rate": float(getattr(row, "on_time_delivery_rate", None)  or 50.0),
        "avg_lead_time_days":    float(getattr(row, "avg_lead_time_days", None)     or 30.0),
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/final-risk/   — single supplier
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/", response_model=FinalRiskResponse)
async def predict_final_risk(data: FinalRiskRequest):
    """
    Unified risk score for one supplier.

    - Pass `supplier_id` + `user_id` to auto-fetch metrics and destination port from DB.
    - Alternatively pass all metric fields directly.
    """
    # Resolve destination port from profiles
    destination_port = _get_destination_port(data.user_id)

    # Build features dict
    features = {
        "availability_score":    data.availability_score,
        "reliability_score":     data.reliability_score,
        "defect_rate":           data.defect_rate,
        "on_time_delivery_rate": data.on_time_delivery_rate,
        "avg_lead_time_days":    data.avg_lead_time_days,
    }

    # Fill missing values from DB if supplier_id provided
    if data.supplier_id and any(v is None for v in features.values()):
        with engine.connect() as conn:
            row = conn.execute(_SUPPLIER_BY_ID_SQL, {"sid": data.supplier_id}).first()
        if row:
            if features["availability_score"]    is None: features["availability_score"]    = float(row.avg_availability or 0.5)
            if features["reliability_score"]     is None: features["reliability_score"]     = float(row.reliability_score or 50.0)
            if features["defect_rate"]           is None: features["defect_rate"]           = float(row.defect_rate or 0.0)
            if features["on_time_delivery_rate"] is None: features["on_time_delivery_rate"] = float(row.on_time_delivery_rate or 50.0)
            if features["avg_lead_time_days"]    is None: features["avg_lead_time_days"]    = float(row.avg_lead_time_days or 30.0)

    features = _apply_defaults(features)

    return await _compute_risk_for_supplier(
        supplier_name    = data.supplier_name,
        country          = data.country,
        destination_port = destination_port,
        features         = features,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/final-risk/{supplier_id}   — quick lookup by ID
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{supplier_id}", response_model=FinalRiskResponse)
async def predict_final_risk_by_id(supplier_id: int, user_id: Optional[str] = None):
    """
    Quick risk prediction by supplier_id.
    All metrics fetched from DB.  Pass user_id to resolve destination port from profiles.
    """
    with engine.connect() as conn:
        row = conn.execute(_SUPPLIER_BY_ID_SQL, {"sid": supplier_id}).first()

    if not row:
        raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")

    destination_port = _get_destination_port(user_id)
    features         = _row_to_features(row)

    return await _compute_risk_for_supplier(
        supplier_name    = row.supplier_name,
        country          = row.country or "Global",
        destination_port = destination_port,
        features         = features,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/final-risk/predict-all   — batch score all suppliers for a user
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/predict-all")
async def predict_all_final_risk(user_id: str):
    """
    Scores every supplier belonging to user_id.
    Destination port is resolved once from profiles and reused for all suppliers.
    """
    destination_port = _get_destination_port(user_id)

    with engine.connect() as conn:
        rows = conn.execute(_ALL_SUPPLIERS_SQL, {"uid": user_id}).fetchall()

    if not rows:
        return {"message": "No suppliers found for this user", "data": []}

    results = []
    for row in rows:
        try:
            features = _row_to_features(row)
            result   = await _compute_risk_for_supplier(
                supplier_name    = row.supplier_name,
                country          = row.country or "Global",
                destination_port = destination_port,
                features         = features,
            )
            result["supplier_id"] = row.supplier_id
            results.append(result)
        except Exception as e:
            results.append({
                "supplier_id":   row.supplier_id,
                "supplier_name": row.supplier_name,
                "error":         str(e),
            })

    return {
        "message":          f"Scored {len(results)} suppliers",
        "destination_port": destination_port,
        "data":             results,
    }
