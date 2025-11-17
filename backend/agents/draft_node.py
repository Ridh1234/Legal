from typing import Dict, Any
import json
import logging

try:
    from backend.services.llm import get_llm, DRAFT_PROMPT_VERSION
    from backend.services.cache import cache_get, cache_set
    from backend.services.vectorstore import retrieve_relevant_clauses
except ModuleNotFoundError:
    from services.llm import get_llm, DRAFT_PROMPT_VERSION
    from services.cache import cache_get, cache_set
    from services.vectorstore import retrieve_relevant_clauses

logger = logging.getLogger(__name__)


async def draft_reply_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs: state with email_text, analysis, contract_snippet
    Outputs: state with draft (string) and risk_score (int)
    """
    email_text = state["email_text"]
    analysis = state.get("analysis")
    # Normalize analysis to a plain dict (FastAPI may pass a Pydantic model instance)
    if analysis and not isinstance(analysis, dict):
        # Pydantic v1 uses .dict(), v2 uses .model_dump()
        if hasattr(analysis, "model_dump"):
            analysis = analysis.model_dump()
        elif hasattr(analysis, "dict"):
            analysis = analysis.dict()
    contract_snippet = state.get("contract_snippet")
    variant = (state.get("variant") or "").upper().strip() or None
    debug = state.get("debug", False)

    # Retrieval augmented: fetch relevant clauses
    retrieved = retrieve_relevant_clauses(contract_snippet or "")

    # Stable cache key: hash of email_text + normalized analysis JSON + contract snippet
    analysis_key_fragment = hash(json.dumps(analysis, sort_keys=True)) if analysis else 0
    cache_key = f"draft:v{DRAFT_PROMPT_VERSION}:{hash(email_text)}:{analysis_key_fragment}:{hash(contract_snippet or '')}:{variant or ''}"
    cached = cache_get(cache_key)
    if cached:
        draft_cached = cached.get("draft") if isinstance(cached, dict) else None
        if isinstance(draft_cached, str) and draft_cached.strip():
            if debug:
                state.setdefault("trace", []).append({"node": "draft_reply", "cached": True})
            return {"draft": draft_cached, "risk_score": cached.get("risk_score")}
        else:
            logger.warning("Ignoring invalid cached draft (None or empty); regenerating.")

    llm = get_llm()

    base_guidelines = (
        "You are a careful legal assistant. Draft a professional email reply.\n"
        "- Refer to clauses 9.1, 9.2, 10.2 when relevant.\n"
        "- Maintain cautious legal tone.\n"
        "- Avoid strong commitments.\n"
    )
    if variant == "B":
        system = (
            base_guidelines
            + "- Provide a slightly more detailed structure with short bullet points for key actions.\n"
            + "- Offer two alternative phrasings for the main position where helpful.\n"
            + "- Aim for 150-220 words.\n"
        )
    else:
        system = (
            base_guidelines
            + "- Keep it clear and concise in 80-140 words; paragraphs only (no bullets).\n"
        )

    try:
        draft = await llm.generate_draft(
            system_prompt=system,
            email_text=email_text,
            analysis=analysis,
            contract_snippet=contract_snippet,
            retrieved_clauses=retrieved,
        )
    except Exception as e:
        logger.error("LLM draft generation failed: %s", e)
        # Fallback minimal draft
        draft = None

    # Ensure non-empty string draft
    if not isinstance(draft, str) or not draft.strip():
        if variant == "B":
            draft = (
                "Subject: Re: Your email\n\n"
                "Thank you for your message.\n\n"
                "- We acknowledge the request and will review the relevant clauses (9.1, 9.2, 10.2) as applicable.\n"
                "- We will coordinate internally and revert with options.\n\n"
                "Best regards,\nLegal Team"
            )
        else:
            draft = (
                "Subject: Re: Your email\n\n"
                "Thank you for your message. We are reviewing the points you raised. "
                "We will respond with more detail after internal consultation.\n\n"
                "Best regards,\nLegal Team"
            )

    # Simple heuristic risk score (0-100)
    risk = 0
    if analysis:
        urgency = str((analysis.get("urgency_level") or "low")).lower()
        intent = str((analysis.get("intent") or "other")).lower()
        if urgency == "high":
            risk += 25
        if any(x in intent for x in ["termination", "terminate"]):
            risk += 35
        if "negotiation" in intent:
            risk += 20
        questions = analysis.get("questions") or []
        if any(isinstance(q, str) and "liability" in q.lower() for q in questions):
            risk += 20
    risk = max(0, min(100, risk))

    cache_set(cache_key, {"draft": draft, "risk_score": risk}, ttl_seconds=60 * 60)

    if debug:
        state.setdefault("trace", []).append({"node": "draft_reply", "risk_score": risk})

    return {"draft": draft, "risk_score": risk}
