from fastapi import APIRouter
from schemas.risk_schema import RiskPredictionRequest, RiskPredictionResponse
from services.risk_predictor import predict_risk

router = APIRouter(prefix="/risk", tags=["Risk Prediction"])


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