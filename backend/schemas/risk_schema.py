from pydantic import BaseModel


class RiskPredictionRequest(BaseModel):

    
    availability_score: float
    reliability_score: float
    defect_rate: float
    on_time_delivery_rate: float
    avg_lead_time_days: float


class RiskPredictionResponse(BaseModel):

    risk_score: float