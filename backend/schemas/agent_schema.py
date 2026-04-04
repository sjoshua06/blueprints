from pydantic import BaseModel, Field
from typing import List, Optional

class AgentMessage(BaseModel):
    agent: str = Field(..., description="Agent name (Engineering, Procurement, Compliance, Supervisor)")
    message: str = Field(..., description="The message or decision from the agent")

class AgenticAuditTrail(BaseModel):
    status: str = Field("resolved", description="Status of the negotiation")
    messages: List[AgentMessage] = Field(default_factory=list, description="Transcript of the agent negotiation")

class ECOSchema(BaseModel):
    original_part: str = Field(..., description="The part that failed or is at risk")
    new_part: str = Field(..., description="The substitute part chosen")
    reasonCode: str = Field("SUPPLY_SHOCK", description="Reason for the ECO")
    approved_by_agents: bool = Field(True, description="Whether the multi-agent system approved it")

class FinalRiskResponse(BaseModel):
    component_id: str
    supplier_name: str
    risk_score: float
    risk_level: str
    dominant_signal: str
    internal_risk_score: float
    external_risk_score: float
    shipping_risk_score: float
    # If the score is high, it triggers the agent, and this field is populated
    healing_triggered: bool = False
    audit_trail: Optional[AgenticAuditTrail] = None
    final_eco: Optional[ECOSchema] = None
