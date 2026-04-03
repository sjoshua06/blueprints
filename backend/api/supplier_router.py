from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Union
from services.mailing_agent import send_real_email, fetch_real_inbox_replies, analyze_supplier_replies

router = APIRouter()

class MailRequestPayload(BaseModel):
    component_id: Union[str, int]
    component_name: str
    required_quantity: Union[int, float]
    supplier_name: str
    supplier_email: str

@router.post("/mail-request")
async def send_mail_request(payload: MailRequestPayload):
    """
    Triggered by the frontend to send an RFQ email to the supplier via SMTP.
    """
    req_details = {
        "quantity": payload.required_quantity
    }
    success = send_real_email(
        payload.supplier_name, 
        payload.supplier_email, 
        payload.component_name, 
        req_details
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email. Check credentials or proxy.")
        
    return {"message": "Email sent successfully to supplier."}

@router.get("/insights/{component_id}")
async def get_supplier_insights(component_id: str, component_name: str):
    """
    Looks in the real inbox for replies mentioning this component, and returns AI insights.
    """
    real_replies = fetch_real_inbox_replies(component_name)
    
    if not real_replies:
        return {"insights": [], "recommended_supplier": None, "reason": "No replies found in email inbox."}
        
    insights = analyze_supplier_replies(component_name, real_replies)
    return insights
