import os
import json
import logging
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv

try:
    import google.generativeai as genai  # SDK for Gemini
    HAVE_GENAI = True
except Exception:
    HAVE_GENAI = False

load_dotenv()
logger = logging.getLogger(__name__)

ANALYZE_PROMPT_VERSION = "1.0.2"
DRAFT_PROMPT_VERSION = "1.0.2"

_GEMINI_KEY = os.getenv("GEMINI_API_KEY")


class _MockLLM:
    """Fallback deterministic LLM for local testing without API key."""

    async def structured_json(self, *, prompt: str, email_text: str) -> Dict[str, Any]:
        lower = email_text.lower()
        intent = "information_request"
        if "terminate" in lower or "termination" in lower:
            intent = "termination_notice"
        elif "approve" in lower or "approval" in lower:
            intent = "approval_request"
        elif "invoice" in lower or "payment" in lower:
            intent = "invoice"
        elif "negotiate" in lower or "counter" in lower:
            intent = "negotiation"
        urgency = "high" if ("asap" in lower or "urgent" in lower) else "medium" if "soon" in lower else "low"
        questions = []
        for q in ["liability", "timeline", "fees", "termination"]:
            if q in lower:
                questions.append(f"Question regarding {q}")
        return {
            "intent": intent,
            "primary_topic": "contract",
            "parties": [p for p in ["Seller", "Buyer"] if p.lower() in lower] or ["Counterparty"],
            "agreement_reference": "MSA-2023" if ("msa" in lower or "agreement" in lower) else None,
            "questions": questions,
            "requested_due_date": None,
            "urgency_level": urgency,
        }

    async def generate_draft(
        self,
        *,
        system_prompt: str,
        email_text: str,
        analysis: Optional[Dict[str, Any]],
        contract_snippet: Optional[str],
        retrieved_clauses: Optional[str],
    ) -> str:
        ref = "Referencing clauses 9.1, 9.2, 10.2 where applicable."
        tone = "We acknowledge receipt and will review the matter with care."
        return (
            f"Subject: Re: Your email\n\n"
            f"Thank you for your message. {tone} "
            f"Based on our review, we will proceed cautiously and avoid firm commitments at this stage. "
            f"{ref}\n\n"
            f"Best regards,\nLegal Team"
        )


USER_CHAT_CANDIDATES = os.getenv("GEMINI_CHAT_CANDIDATES")  # comma separated friendly names

def _normalize_user_models(raw: str) -> List[str]:
    cleaned = []
    for part in raw.split(','):
        name = part.strip()
        if not name:
            continue
        # Allow friendly names like "Gemini 2.5 Pro" -> gemini-2.5-pro
        low = name.lower().replace(' ', '-')
        if not low.startswith('gemini-'):
            low = 'gemini-' + low
        cleaned.append(low)
    return cleaned

DEFAULT_CHAT_MODEL_CANDIDATES = (
    _normalize_user_models(USER_CHAT_CANDIDATES)
    if USER_CHAT_CANDIDATES else [
        # Prefer newest generation first; include 2.5 series user requested
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite',
        'gemini-2.5-pro',
        os.getenv("GEMINI_CHAT_MODEL") or "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-8b",
    ]
)


def _discover_models() -> List[str]:
    if not HAVE_GENAI or not _GEMINI_KEY:
        return []
    try:
        genai.configure(api_key=_GEMINI_KEY)
        models = list(genai.list_models())
        # Filter for generateContent capability
        chat_models = []
        for m in models:
            try:
                methods = set(getattr(m, "supported_generation_methods", []) or [])
                name = getattr(m, "name", "")
                # Normalize: API returns names like "models/gemini-1.5-flash-latest"
                if not name:
                    continue
                if "generateContent" in methods or "generateText" in methods or "createContent" in methods:
                    # strip leading "models/"
                    if name.startswith("models/"):
                        name = name.split("/", 1)[1]
                    chat_models.append(name)
            except Exception:
                continue
        # Scoring prefers 2.5 > 1.5, flash-lite < flash < pro for reply quality
        def score(n: str):
            s = 0
            if "2.5" in n:
                s += 30
            if "1.5" in n:
                s += 20
            if "flash-lite" in n:
                s += 5
            if "flash" in n and "flash-lite" not in n:
                s += 10
            if "pro" in n:
                s += 15
            if "latest" in n:
                s += 4
            if "8b" in n:
                s += 2
            return -s
        chat_models = sorted(set(chat_models), key=score)
        return chat_models
    except Exception as e:
        logger.warning(f"Model discovery failed: {e}")
        return []


class _GeminiLLM:
    def __init__(self):
        # Try dynamic discovery; fall back to defaults
        discovered = _discover_models()
        self._candidates = discovered or [m for m in DEFAULT_CHAT_MODEL_CANDIDATES if m]
        self._idx = 0
        self._model = self._build_model(self._candidates[self._idx])

    def _build_model(self, name: str):
        if not HAVE_GENAI:
            raise RuntimeError("google-generativeai SDK not installed")
        logger.info(f"Using Gemini chat model: {name}")
        genai.configure(api_key=_GEMINI_KEY)
        # Handle SDK variants: some expect 'model', others 'model_name', and some accept positional
        try:
            return genai.GenerativeModel(model=name, generation_config={"temperature": 0.2})
        except TypeError:
            try:
                return genai.GenerativeModel(model_name=name, generation_config={"temperature": 0.2})
            except TypeError:
                return genai.GenerativeModel(name)

    def _rotate(self):
        self._idx = (self._idx + 1) % len(self._candidates)
        self._model = self._build_model(self._candidates[self._idx])

    async def _call_chat(self, messages: List[str]):
        last_exc = None
        for _ in range(len(self._candidates)):
            try:
                # SDK is sync; wrap in thread if needed. We'll call it in a thread via asyncio.to_thread.
                import asyncio
                def _gen():
                    return self._model.generate_content(messages)
                resp = await asyncio.to_thread(_gen)
                return resp
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                # Rotate on 404 model not found or 429 rate limit or unsupported method errors
                if any(x in msg for x in ["404", "not found", "unsupported", "rate", "quota", "429", "exceeded"]):
                    logger.warning(f"Model error '{e}'. Rotating to next candidate.")
                    self._rotate()
                else:
                    break
        attempts = ", ".join(self._candidates)
        raise RuntimeError(f"Gemini call failed after trying models: [{attempts}] | last_error={last_exc}")

    async def structured_json(self, *, prompt: str, email_text: str) -> Dict[str, Any]:
        messages = [
            prompt + "\nReturn only valid JSON without markdown.",
            email_text,
        ]
        resp = await self._call_chat(messages)
        text = getattr(resp, "text", None) or str(resp)
        # Coerce to JSON
        try:
            if text.strip().startswith("```"):
                text = "\n".join([line for line in text.splitlines() if not line.strip().startswith("```")])
            data = json.loads(text)
        except Exception:
            import re
            m = re.search(r"\{[\s\S]*\}", text)
            if not m:
                raise
            data = json.loads(m.group(0))
        return data

    async def generate_draft(
        self,
        *,
        system_prompt: str,
        email_text: str,
        analysis: Optional[Dict[str, Any]],
        contract_snippet: Optional[str],
        retrieved_clauses: Optional[str],
    ) -> str:
        guidance = (
            system_prompt
            + "\nIncorporate any relevant references to clauses 9.1, 9.2, 10.2 as applicable."
            + "\nAvoid over-committing; maintain a cautious legal tone."
        )
        human = (
            "Email to reply to:\n" + email_text + "\n\n"
            + ("Analysis JSON:\n" + json.dumps(analysis, indent=2) + "\n\n" if analysis else "")
            + ("Contract Snippet:\n" + contract_snippet + "\n\n" if contract_snippet else "")
            + ("Retrieved Clauses:\n" + retrieved_clauses + "\n\n" if retrieved_clauses else "")
            + "Draft a reply email string only."
        )
        messages = [guidance, human]
        resp = await self._call_chat(messages)
        return getattr(resp, "text", None) or str(resp)


_llm_instance = None


def get_llm():
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
    if _GEMINI_KEY and len(_GEMINI_KEY) > 5 and HAVE_GENAI:
        logger.info("Using Gemini LLM via google-generativeai SDK")
        _llm_instance = _GeminiLLM()
    else:
        logger.warning("GEMINI_API_KEY not set; using Mock LLM for offline testing")
        _llm_instance = _MockLLM()
    return _llm_instance
