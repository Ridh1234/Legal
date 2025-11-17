from typing import Dict, Any
import logging
import re

try:
    from backend.services.llm import get_llm, ANALYZE_PROMPT_VERSION
    from backend.services.cache import cache_get, cache_set
    from backend.agents.heuristics import (
        extract_due_date,
        extract_urgency,
        refine_intent,
        extract_parties,
        extract_questions,
        refine_topic,
    )
except ModuleNotFoundError:
    from services.llm import get_llm, ANALYZE_PROMPT_VERSION
    from services.cache import cache_get, cache_set
    from agents.heuristics import (
        extract_due_date,
        extract_urgency,
        refine_intent,
        extract_parties,
        extract_questions,
        refine_topic,
    )

logger = logging.getLogger(__name__)


async def analyze_email_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inputs: state with email_text
    Outputs: state with analysis (dict)
    """
    email_text = state["email_text"]
    debug = state.get("debug", False)

    cache_key = f"analysis:v{ANALYZE_PROMPT_VERSION}:{hash(email_text)}"
    cached = cache_get(cache_key)
    if cached:
        if debug:
            state.setdefault("trace", []).append({"node": "analyze_email", "cached": True})
        return {"analysis": cached}

    llm = get_llm()
    prompt = (
        "You are a legal email analysis engine. Extract structured information using ONLY the JSON schema below.\n\n"
        "STRICT RULES:\n"
        "1. Output ONLY valid JSON. No commentary, no markdown fences.\n"
        "2. Include ALL keys; missing values become empty strings.\n"
        "3. NEVER hallucinate parties, dates, or clauses not in the email.\n"
        "4. parties.client = sender (from signature or writing perspective). parties.counterparty = explicitly mentioned other party (e.g., in 'between X and Y'). If absent -> ''.\n"
        "5. questions: ONLY sentences ending with '?' from the email; remove duplicates/paraphrases. Ignore statements like 'Please revert'.\n"
        "6. intent: concise functional purpose (e.g., legal_advice_request, requesting_approval, termination_query, payment_withholding, clarification_request).\n"
        "7. primary_topic: main legal subject (e.g., termination_for_non-performance, msa_amendments, payment_withholding).\n"
        "8. agreement_reference: capture type (e.g., 'Statement of Work', 'MSA', 'NDA'); if date missing use ''. Do not fabricate.\n"
        "9. requested_due_date: explicit deadline phrases (e.g., 'tomorrow', 'end of week'); else ''.\n"
        "10. urgency_level: high -> urgent|asap|immediately|tomorrow; medium -> end of week|early next week|soon|follow up; low -> no deadline cues.\n"
        "11. NEVER duplicate semantically identical questions.\n"
        "Return JSON ONLY with keys: intent, primary_topic, parties{client,counterparty}, agreement_reference{type,date}, questions[], requested_due_date, urgency_level."
    )

    # We keep reasoning out of the final response. The LLM wrapper handles safe JSON extraction.
    result = await llm.structured_json(prompt=prompt, email_text=email_text)
    # Normalize to API schema (strings with empty defaults, objects for parties and agreement)
    normalized = _normalize_analysis(result, email_text=email_text)

    cache_set(cache_key, normalized, ttl_seconds=60 * 60)

    if debug:
        state.setdefault("trace", []).append({"node": "analyze_email", "output": normalized})

    return {"analysis": normalized}


def _normalize_analysis(data: Dict[str, Any], email_text: str | None = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    # Intent mapping to our preferred labels, but expose as free string
    raw_intent = str((data.get("intent") or "")).strip().lower()
    intent_map = {
        "request_for_approval": "approval_request",
        "approval": "approval_request",
        "approve_request": "approval_request",
        "approval_request": "approval_request",
        "information_request": "information_request",
        "info_request": "information_request",
        "information": "information_request",
        "info": "information_request",
        "termination_notice": "termination_notice",
        "termination": "termination_notice",
        "terminate": "termination_notice",
        "invoice": "invoice",
        "billing": "invoice",
        "payment": "invoice",
        "negotiate": "negotiation",
        "negotiation": "negotiation",
        "counter": "negotiation",
        "other": "other",
    }
    out["intent"] = intent_map.get(raw_intent, raw_intent or "")

    # Primary topic refined generically
    topic = data.get("primary_topic") or ""
    et = (email_text or "").lower()
    out["primary_topic"] = refine_topic(et, topic)

    # Parties: override with heuristic extraction (ignore LLM hallucinations)
    raw_client = ""
    raw_counterparty = ""
    if isinstance(data.get("parties"), dict):
        raw_client = str(data["parties"].get("client") or "")
        raw_counterparty = str(data["parties"].get("counterparty") or "")
    elif isinstance(data.get("parties"), list):
        lst = [str(p) for p in data["parties"] if p]
        if lst:
            raw_client = lst[0]
        if len(lst) > 1:
            raw_counterparty = lst[1]
    client, counterparty = extract_parties(email_text or "", raw_client, raw_counterparty)
    out["parties"] = {"client": client, "counterparty": counterparty}

    # Agreement reference -> object {type, date} generic cleanup
    agr = data.get("agreement_reference")
    atype = ""
    adate = ""
    if isinstance(agr, dict):
        atype = str(agr.get("type") or "")
        adate = str(agr.get("date") or "")
    elif isinstance(agr, str):
        # Try to parse a type token like MSA, NDA, SOW
        token = agr.strip()
        if re.match(r"^[A-Za-z]{2,5}$", token.upper()):
            atype = token
        else:
            atype = token
    # If email mentions MSA and atype empty, fill
    if not atype and "msa" in et:
        atype = "MSA"
    out["agreement_reference"] = {"type": atype, "date": adate}

    # Questions -> list[str] with generalized extraction
    questions = data.get("questions")
    if isinstance(questions, str):
        questions = [questions]
    if not isinstance(questions, list):
        questions = []
    qnorm = [str(q) for q in questions if q is not None]
    extracted = extract_questions(email_text or "", qnorm)
    # Fix accidental '.?' punctuation
    cleaned_qs = [re.sub(r"\.?\?$", "?", q.strip()) for q in extracted]
    out["questions"] = cleaned_qs

    # Requested due date -> string (generalized)
    rdd = str(data.get("requested_due_date") or "")
    out["requested_due_date"] = extract_due_date(email_text or "", rdd)

    # Urgency normalization -> low|medium|high else empty
    raw_urg = str((data.get("urgency_level") or "")).strip().lower()
    out["urgency_level"] = extract_urgency(email_text or "", raw_urg)

    # Intent refinement using email cues
    out["intent"] = refine_intent(email_text or "", out["intent"])

    return out
