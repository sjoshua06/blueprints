from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from db.database import engine
from auth.dependencies import get_current_user_id
from schemas.risk_schema import (
    RiskPredictionRequest,
    RiskPredictionResponse,
    PredictAllResponse,
)
from services.risk_predictor import compute_final_risk, predict_risk

router = APIRouter(prefix="/api/supplier-risk", tags=["Risk Prediction"])


# ─────────────────────────────────────────────────────────────────────────────
# POST /predict  —  single supplier (manual input)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/predict", response_model=RiskPredictionResponse)
def predict_supplier_risk(data: RiskPredictionRequest):
    """
    Predict risk for a single supplier using the hybrid engine.
    Combines internal metrics formula + News API sentiment.
    Returns the score, factor breakdown, and relevant news articles.
    """
    features = {
        "availability_score":    data.availability_score,
        "reliability_score":     data.reliability_score,
        "defect_rate":           data.defect_rate,
        "on_time_delivery_rate": data.on_time_delivery_rate,
        "avg_lead_time_days":    data.avg_lead_time_days,
    }

    result = compute_final_risk(
        supplier_name=data.supplier_name,
        country=data.country,
        features=features,
    )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# POST /predict-all  —  all suppliers for the logged-in user
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/predict-all")
def predict_all_suppliers(user_id: str = Depends(get_current_user_id)):
    """
    Predict risk scores for ALL suppliers belonging to the current user.

    For each supplier:
    1. Compute internal risk from DB metrics
    2. Fetch news sentiment (cached per 24h)
    3. Fuse into a final risk score with factor breakdown
    4. Update the risk_score column in the suppliers table
    """
    select_sql = """
        SELECT 
            s.supplier_id, 
            s.supplier_name,
            s.country,
            s.reliability_score, 
            s.defect_rate, 
            s.on_time_delivery_rate, 
            s.avg_lead_time_days,
            (SELECT COALESCE(AVG(sc.availability_score), 0.5) 
             FROM supplier_components sc 
             WHERE sc.supplier_id = s.supplier_id) as avg_availability_score
        FROM suppliers s
        WHERE s.user_id = :uid
    """

    update_sql = "UPDATE suppliers SET risk_score = :risk WHERE supplier_id = :sid"

    results = []

    try:
        with engine.begin() as conn:
            rows = conn.execute(text(select_sql), {"uid": user_id}).fetchall()

            update_data = []
            for row in rows:
                features = {
                    "availability_score":    float(row.avg_availability_score or 0.5),
                    "reliability_score":     float(row.reliability_score or 50.0),
                    "defect_rate":           float(row.defect_rate or 0.0),
                    "on_time_delivery_rate": float(row.on_time_delivery_rate or 50.0),
                    "avg_lead_time_days":    float(row.avg_lead_time_days or 30.0),
                }

                supplier_name = str(row.supplier_name or "Unknown")
                country = str(row.country or "Global")

                # Full hybrid prediction
                risk_result = compute_final_risk(
                    supplier_name=supplier_name,
                    country=country,
                    features=features,
                )

                # The DB column stores 0–1 scale
                risk_for_db = risk_result["risk_score"] / 100.0
                update_data.append({"risk": risk_for_db, "sid": row.supplier_id})

                results.append({
                    "supplier_id":        row.supplier_id,
                    "supplier_name":      supplier_name,
                    "country":            country,
                    "availability_score": features["availability_score"],
                    "reliability_score":  features["reliability_score"],
                    "defect_rate":        features["defect_rate"],
                    "on_time_delivery_rate": features["on_time_delivery_rate"],
                    "avg_lead_time_days": features["avg_lead_time_days"],
                    **risk_result,
                })

            # Batch update DB
            if update_data:
                conn.execute(text(update_sql), update_data)

        return {
            "message": f"Successfully predicted risk for {len(results)} suppliers",
            "data": results,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))