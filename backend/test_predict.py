import requests
import json

payload = {
    'supplier_name': 'Harmon-Yates',
    'country': 'China',
    'availability_score': 0.5,
    'reliability_score': 40.57,
    'defect_rate': 0.62,
    'on_time_delivery_rate': 91.4,
    'avg_lead_time_days': 11
}

r = requests.post('http://127.0.0.1:8000/api/supplier-risk/predict', json=payload)
print(json.dumps(r.json(), indent=2))
