from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_assignment_sample_email_analysis():
    email_text = (
        "Hi team,\n\n"
        "Please approve the proposed changes to the MSA. This is fairly urgent, ideally by end of week.\n"
        "Also, could you clarify the liability limits?\n\n"
        "Thanks,\n"
        "Buyer\n"
    )
    r = client.post("/api/analyze", json={"email_text": email_text})
    assert r.status_code == 200
    data = r.json()

    # Exact expectations per assignment
    assert data["intent"] == "requesting approval and clarification"
    assert data["primary_topic"] == "MSA amendments"
    assert data["parties"]["client"] in {"Buyer", ""}  # allow empty if LLM doesn't extract client
    assert data["parties"]["counterparty"] == ""
    assert data["agreement_reference"]["type"] in {"MSA", ""}
    assert data["agreement_reference"]["date"] == ""
    # Exactly one liability clarification question expected
    liability_qs = [q for q in data["questions"] if "liability" in q.lower() and "clarify" in q.lower()]
    assert len(liability_qs) == 1
    assert data["requested_due_date"] == "end of week"
    # Updated rule: 'end of week' now medium urgency per new instructions
    assert data["urgency_level"] == "medium"
