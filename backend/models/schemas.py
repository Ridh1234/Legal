from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class Parties(BaseModel):
    client: str = ""
    counterparty: str = ""


class AgreementRef(BaseModel):
    type: str = ""
    date: str = ""


class AnalysisJSON(BaseModel):
    # Use free-form strings for resilience; we normalize in code but don't block API
    intent: str = Field(default="", description="Primary intent of the email")
    primary_topic: str = Field(default="", description="Main legal topic or clause area")
    parties: Parties = Field(default_factory=Parties, description="Identified parties")
    agreement_reference: AgreementRef = Field(default_factory=AgreementRef, description="Agreement reference")
    questions: List[str] = Field(default_factory=list, description="List of questions asked")
    requested_due_date: str = Field(default="", description="Requested due date if any")
    urgency_level: str = Field(default="", description="Urgency level (low|medium|high or empty)")

class AnalyzeRequest(BaseModel):
    email_text: str
    contract_snippet: Optional[str] = None
    debug: Optional[bool] = False

class AnalyzeResponse(AnalysisJSON):
    pass

class DraftRequest(BaseModel):
    email_text: str
    analysis: Optional[AnalysisJSON] = None
    contract_snippet: Optional[str] = None
    debug: Optional[bool] = False
    variant: Optional[str] = Field(default=None, description="Optional draft variant label, e.g., 'A' or 'B'")

class DraftResponse(BaseModel):
    draft: str
    risk_score: Optional[int] = Field(default=None, ge=0, le=100)

class ProcessRequest(BaseModel):
    email_text: str
    contract_snippet: Optional[str] = None
    debug: Optional[bool] = False

class ProcessResponse(BaseModel):
    analysis: AnalysisJSON
    draft: str
    risk_score: Optional[int] = Field(default=None, ge=0, le=100)

# Internal engine state
class PipelineState(BaseModel):
    email_text: str
    contract_snippet: Optional[str] = None
    analysis: Optional[AnalysisJSON] = None
    draft: Optional[str] = None
    risk_score: Optional[int] = None
    debug: bool = False
    trace: List[Dict[str, Any]] = Field(default_factory=list, description="Internal trace (not exposed)")
