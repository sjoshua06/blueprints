import joblib
import numpy as np
import os

MODEL_PATH = os.path.join("models", "supplier_risk_model.pkl")

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    import warnings
    warnings.warn(f"Could not load risk predictor model at {MODEL_PATH}: {e}")
    model = None


def predict_risk(features):

    """
    features order:
    [
        
        availability_score,
        reliability_score,
        defect_rate,
        on_time_delivery_rate,
        avg_lead_time_days
    ]
    """

    if model is None:
        # Fallback dummy risk if model is not trained yet
        return 0.5

    vector = np.array(features).reshape(1, -1)

    prediction = model.predict(vector)[0]

    return float(prediction)