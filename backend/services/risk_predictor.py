import joblib
import numpy as np
import os
import warnings
from dotenv import load_dotenv

load_dotenv()

# We prefer the Hugging Face model first.
HF_REPO_ID = os.environ.get("HF_REPO_ID")
HF_TOKEN = os.environ.get("HF_TOKEN")
MODEL_FILENAME = "supplier_risk_model.pkl"

model = None

def load_huggingface_model():
    if not HF_REPO_ID:
        return None
    try:
        from huggingface_hub import hf_hub_download
        
        # Download the model from the Hugging Face repo
        print(f"Downloading model from Hugging Face: {HF_REPO_ID}")
        downloaded_path = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=MODEL_FILENAME,
            token=HF_TOKEN
        )
        return joblib.load(downloaded_path)
    except Exception as e:
        warnings.warn(f"Failed to load model from HF Hub: {e}")
        return None

def load_local_model():
    model_path = os.path.join("models", MODEL_FILENAME)
    try:
        return joblib.load(model_path)
    except Exception as e:
        warnings.warn(f"Could not load local risk predictor model at {model_path}: {e}")
        return None

# Attempt HF Hub first, fallback to local
model = load_huggingface_model()
if model is None:
    model = load_local_model()

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