from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

# Support both running as package (backend.*) and as top-level (uvicorn api.main)
try:
    from backend.agents.graph import run_pipeline
    from backend.services.llm import get_llm
    from backend.models.schemas import (
        AnalyzeRequest,
        AnalyzeResponse,
        DraftRequest,
        DraftResponse,
        ProcessRequest,
        ProcessResponse,
    )
except ModuleNotFoundError:
    from agents.graph import run_pipeline
    from services.llm import get_llm
    from models.schemas import (
        AnalyzeRequest,
        AnalyzeResponse,
        DraftRequest,
        DraftResponse,
        ProcessRequest,
        ProcessResponse,
    )

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_email(payload: AnalyzeRequest):
    try:
        result = await run_pipeline(
            email_text=payload.email_text,
            contract_snippet=payload.contract_snippet,
            mode="analyze",
            debug=payload.debug or False,
        )
        return AnalyzeResponse(**result["analysis"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/draft", response_model=DraftResponse)
async def draft_reply(payload: DraftRequest):
    try:
        result = await run_pipeline(
            email_text=payload.email_text,
            contract_snippet=payload.contract_snippet,
            analysis=payload.analysis,
            variant=payload.variant,
            mode="draft",
            debug=payload.debug or False,
        )
        # Coerce draft to a non-empty string to satisfy response model
        draft_val = result.get("draft")
        if not isinstance(draft_val, str) or not draft_val.strip():
            draft_val = (
                "Subject: Re: Your email\n\n"
                "Thank you for your message. We are reviewing the points you raised. "
                "We will respond with more detail after internal consultation.\n\n"
                "Best regards,\nLegal Team"
            )
        return DraftResponse(draft=draft_val, risk_score=result.get("risk_score"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process", response_model=ProcessResponse)
async def process(payload: ProcessRequest):
    try:
        result = await run_pipeline(
            email_text=payload.email_text,
            contract_snippet=payload.contract_snippet,
            mode="process",
            debug=payload.debug or False,
        )
        draft_val = result.get("draft")
        if not isinstance(draft_val, str) or not draft_val.strip():
            draft_val = (
                "Subject: Re: Your email\n\n"
                "Thank you for your message. We are reviewing the points you raised. "
                "We will respond with more detail after internal consultation.\n\n"
                "Best regards,\nLegal Team"
            )
        return ProcessResponse(analysis=result["analysis"], draft=draft_val, risk_score=result.get("risk_score"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def models():
    """Return the current Gemini model candidates in use (for debugging)."""
    llm = get_llm()
    names = []
    try:
        # best-effort introspection
        names = getattr(llm, "_candidates", []) or []
        current = getattr(llm, "_candidates", [None])[getattr(llm, "_idx", 0)] if names else None
    except Exception:
        current = None
    return {"candidates": names, "current": current}
