from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_between_clause_and_signature_extraction():
    email = (
        "Dear Counsel,\n\n"
        "Under the Statement of Work dated 12 February 2024 between Helios Labs and Quantum Systems Ltd., the vendor has failed to deliver Milestone 3 despite multiple reminders.\n\n"
        "We are evaluating whether we can terminate the SOW for non-performance. Additionally, please advise whether we can withhold the next payment scheduled for 5 March 2025.\n\n"
        "Please revert by tomorrow as we need to brief management.\n\n"
        "Regards,\n"
        "Aarav Mehta\n"
        "Legal, Helios Labs\n"
    )
    r = client.post("/api/analyze", json={"email_text": email})
    assert r.status_code == 200
    data = r.json()
    # Parties
    assert data["parties"]["client"].lower().startswith("helios labs")
    assert data["parties"]["counterparty"].lower().startswith("quantum systems")
    # Questions should not include non-question 'Please revert...' and should dedupe payment question
    qs = data["questions"]
    assert all(q.endswith("?") for q in qs)
    # Core phrases deduped
    payment_phrases = [q for q in qs if "withhold" in q.lower() and "payment" in q.lower()]
    assert len(payment_phrases) == 1
    termination_phrases = [q for q in qs if "terminate" in q.lower() and "sow" in q.lower()]
    assert len(termination_phrases) == 1
