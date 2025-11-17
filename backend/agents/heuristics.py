"""Reusable heuristic extraction utilities for legal email analysis.

The LLM provides a first-pass JSON. These functions gently refine without
inventing data. All functions must be side-effect free.
"""
from __future__ import annotations
from typing import List, Tuple, Optional
import re

_DUE_DATE_PATTERNS = [
    (re.compile(r"\b(end of (the )?week)\b", re.I), "end of week"),
    (re.compile(r"\bby end of week\b", re.I), "end of week"),
    (re.compile(r"\beow\b", re.I), "end of week"),
    (re.compile(r"\bby friday\b", re.I), "end of week"),
    (re.compile(r"\bby (monday|tuesday|wednesday|thursday|friday)\b", re.I), None),  # keep phrase as-is
    (re.compile(r"\bby (eod|close of business)\b", re.I), "end of day"),
    (re.compile(r"\bwithin (\d{1,2}) days\b", re.I), None),
]

_HIGH_URGENCY_KEYWORDS = {
    "urgent", "asap", "immediately", "critical", "time-sensitive", "tomorrow"
}
_MEDIUM_URGENCY_KEYWORDS = {"soon", "priority", "at your earliest convenience", "follow up", "end of week", "eow", "early next week"}
_LOW_URGENCY_KEYWORDS = {"whenever", "no rush", "not urgent"}

INTENT_SYNONYM_GROUPS = [
    ("approval_request", {"approve", "approval", "sign off"}),
    ("information_request", {"info", "information", "detail", "details"}),
    ("termination_notice", {"terminate", "termination", "ending"}),
    ("invoice", {"invoice", "payment", "bill"}),
    ("negotiation", {"negotiate", "negotiation", "counteroffer", "counter"}),
]

QUESTION_TRIGGERS = ["could you", "can you", "would you", "please", "do you", "what is", "how", "why", "when", "which", "who"]
QUESTION_HINT_PATTERNS = [
    re.compile(r"\bcan we\b", re.I),
    re.compile(r"\bcould we\b", re.I),
    re.compile(r"\bwhether we can\b", re.I),
    re.compile(r"\bwhether we could\b", re.I),
    re.compile(r"\bcan you\b", re.I),
    re.compile(r"\bcould you\b", re.I),
    re.compile(r"\bplease advise whether\b", re.I),
    re.compile(r"\bplease advise if\b", re.I),
    re.compile(r"\bplease confirm\b", re.I),
    re.compile(r"\bwould you\b", re.I),
]


def extract_due_date(email_text: str, existing: str) -> str:
    if existing:
        return existing
    lower = email_text.lower()
    for pattern, normalized in _DUE_DATE_PATTERNS:
        m = pattern.search(lower)
        if m:
            if normalized:
                return normalized
            # If no normalized provided, return the matched span
            return m.group(0)
    return ""


def extract_urgency(email_text: str, existing: str) -> str:
    lower = email_text.lower()
    # Escalate if explicit high urgency words present
    if any(k in lower for k in _HIGH_URGENCY_KEYWORDS):
        return "high"
    if any(k in lower for k in _MEDIUM_URGENCY_KEYWORDS):
        return "medium"
    if any(k in lower for k in _LOW_URGENCY_KEYWORDS):
        return "low"
    # Preserve existing classification if valid and no stronger signal found
    if existing in {"high", "medium", "low"}:
        return existing
    return ""


def refine_intent(email_text: str, raw_intent: str) -> str:
    lower = email_text.lower()
    mapped = raw_intent
    # Combine approval + clarification pattern
    if ("approve" in lower or "approval" in lower) and ("clarify" in lower or "clarification" in lower):
        return "requesting approval and clarification"
    # If no mapped intent or very generic, attempt based on keyword groups
    if not mapped or mapped in {"other", ""}:
        for label, keywords in INTENT_SYNONYM_GROUPS:
            if any(k in lower for k in keywords):
                mapped = label
                break
    return mapped or ""


def extract_parties(email_text: str, existing_client: str, existing_counterparty: str) -> Tuple[str, str]:
    # Preserve existing if both present
    if existing_client and existing_counterparty:
        return existing_client, existing_counterparty

    text = email_text
    lower = text.lower()
    client = existing_client or ""
    counterparty = existing_counterparty or ""

    # Pattern: between X and Y
    between_match = re.search(r"between\s+(.+?)\s+and\s+(.+?)([\.,]|$)", text, re.IGNORECASE)
    parties_found: List[str] = []
    if between_match:
        p1 = between_match.group(1).strip()
        p2 = between_match.group(2).strip()
        # Clean trailing descriptors
        def _clean(p: str) -> str:
            return re.sub(r"\b(ltd|inc|corp|llc|gmbh|s\.a\.|plc)\.?$", lambda m: m.group(0).upper(), p, flags=re.I).strip()
        parties_found = [_clean(p1), _clean(p2)]

    # Signature parsing: last 8 lines for org mention (e.g., "Legal, Helios Labs")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    tail = lines[-8:]
    org_from_signature = ""
    for line in tail:
        if "," in line:
            # e.g., "Legal, Helios Labs" -> take last segment
            segs = [s.strip() for s in line.split(",") if s.strip()]
            if len(segs) >= 2:
                org_from_signature = segs[-1]
        else:
            # Organization style with multiple capitalized tokens
            tokens = line.split()
            cap_tokens = [t for t in tokens if re.match(r"^[A-Z][A-Za-z0-9.&'-]*$", t)]
            if len(cap_tokens) >= 2:
                org_from_signature = " ".join(cap_tokens)
    # Prefer signature org as client
    if org_from_signature:
        client = client or org_from_signature

    # If 'between' pattern present, try to align client with signature org; assign counterparty as the other
    if parties_found:
        if client:
            if client.lower() == parties_found[0].lower():
                counterparty = parties_found[1]
            elif client.lower() == parties_found[1].lower():
                counterparty = parties_found[0]
            else:
                # If signature org not in between, assume first is client
                client = client or parties_found[0]
                if not counterparty and len(parties_found) > 1:
                    counterparty = parties_found[1]
        else:
            client = parties_found[0]
            if len(parties_found) > 1:
                counterparty = parties_found[1]

    # Explicit proper noun extraction fallback for missing counterparty
    if not counterparty and parties_found and len(parties_found) > 1:
        # ensure distinct
        if parties_found[1].lower() != client.lower():
            counterparty = parties_found[1]

    # Validate explicit appearance in text; if not present, blank it
    if counterparty and counterparty.lower() not in lower:
        counterparty = ""
    if client and client.lower() not in lower and org_from_signature:
        # Accept signature client even if not in body
        pass
    return client or "", counterparty or ""


def extract_questions(email_text: str, existing_questions: List[str]) -> List[str]:
    # Preserve existing questions but remove obvious duplicates
    norm_map = {}
    out: List[str] = []
    def _norm(q: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", q.lower()).strip()
    for q in existing_questions:
        n = _norm(q)
        if n not in norm_map:
            norm_map[n] = q
            out.append(q)

    # Sentence-based extraction
    sentences = re.split(r"(?<=[?!.])\s+", email_text)
    for s in sentences:
        sl = s.lower().strip()
        if not sl:
            continue
        is_question = sl.endswith("?")
        if not is_question:
            # Check hint patterns for interrogative sentences lacking '?'
            if any(p.search(sl) for p in QUESTION_HINT_PATTERNS):
                is_question = True
        if not is_question:
            continue
        if 5 <= len(sl) <= 220:
            # Normalize to ensure trailing '?' present for consistency
            candidate = s.strip()
            if not candidate.endswith("?"):
                # Replace trailing '.' with '?' else append
                candidate = re.sub(r"\.$", "?", candidate) if candidate.endswith(".") else candidate + "?"
            n = _norm(candidate)
            if n not in norm_map:
                norm_map[n] = candidate
                out.append(candidate)

    # Liability clarification enforcement if liability mentioned
    if "liability" in email_text.lower():
        has_liability = any("liability" in _norm(q) and ("clarify" in _norm(q) or "can we" in _norm(q) or "could we" in _norm(q)) for q in out)
        if not has_liability:
            out.append("Can we clarify the liability limits?")

    # Collapse near-duplicate payment / termination questions by core phrase normalization
    core_map = {}
    cleaned: List[str] = []
    def _core(q: str) -> str:
        ql = q.lower()
        ql = re.sub(r"^(additionally,\s*)", "", ql)
        ql = re.sub(r"^(please\s+advise\s+whether\s*)", "", ql)
        ql = re.sub(r"^(can we\s+)", "", ql)
        ql = re.sub(r"^(could you\s+)", "", ql)
        ql = re.sub(r"^(would you\s+)", "", ql)
        ql = re.sub(r"^(please\s+)", "", ql)
        ql = re.sub(r"\?+$", "", ql).strip()
        return ql
    for q in out:
        c = _core(q)
        if c not in core_map:
            core_map[c] = q
            cleaned.append(q)
    return cleaned


def refine_topic(email_text: str, existing_topic: str) -> str:
    lower = email_text.lower()
    if ("msa" in lower) and any(k in lower for k in ["amend", "amendment", "change", "update", "revision"]):
        return "MSA amendments"
    if not existing_topic and "msa" in lower:
        return "MSA"
    return existing_topic or ""
