from api.risk_routes import predict_supplier_risk
from schemas.risk_schema import RiskPredictionRequest

req = RiskPredictionRequest(
    supplier_name="Harmon-Yates",
    country="China",
    availability_score=0.5,
    reliability_score=40.57,
    defect_rate=0.62,
    on_time_delivery_rate=91.4,
    avg_lead_time_days=11
)

print(predict_supplier_risk(req))
