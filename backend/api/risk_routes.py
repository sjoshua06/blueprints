from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from db.database import engine
from auth.dependencies import get_current_user_id
from schemas.risk_schema import RiskPredictionRequest, RiskPredictionResponse
from services.risk_predictor import predict_risk

router = APIRouter(prefix="/api/supplier-risk", tags=["Risk Prediction"])

@router.post("/predict", response_model=RiskPredictionResponse)
def predict_supplier_risk(data: RiskPredictionRequest):
    features = [
        data.availability_score,
        data.reliability_score,
        data.defect_rate,
        data.on_time_delivery_rate,
        data.avg_lead_time_days
    ]
    risk = predict_risk(features)
    return {"risk_score": risk}


@router.post("/predict-all")
def predict_all_suppliers(user_id: str = Depends(get_current_user_id)):
    """
    Predict risk scores for all suppliers that belong to the current user.
    Updates the 'risk_score' column in the suppliers table and returns the results.
    """
    select_sql = """
        SELECT 
            s.supplier_id, 
            s.supplier_name, 
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
                features = [
                    float(row.avg_availability_score or 0.5),
                    float(row.reliability_score or 0.5),
                    float(row.defect_rate or 0.0),
                    float(row.on_time_delivery_rate or 0.5),
                    float(row.avg_lead_time_days or 30.0)
                ]
                
                # Predict risk (cached model)
                risk = predict_risk(features)
                
                # Collect for batch update
                update_data.append({"risk": risk, "sid": row.supplier_id})
                
                # Append to results for response
                results.append({
                    "supplier_id": row.supplier_id,
                    "supplier_name": row.supplier_name,
                    "availability_score": features[0],
                    "reliability_score": features[1],
                    "defect_rate": features[2],
                    "on_time_delivery_rate": features[3],
                    "avg_lead_time_days": features[4],
                    "risk_score": risk
                })
            
            # Batch Update
            if update_data:
                conn.execute(text(update_sql), update_data)
                
        return {"message": f"Successfully predicted risk for {len(results)} suppliers", "data": results}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))