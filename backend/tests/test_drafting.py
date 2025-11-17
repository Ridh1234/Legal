from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_draft_with_analysis():
    analysis = {
        "intent": "approval_request",
        "primary_topic": "contract",
        "parties": {"client": "Seller", "counterparty": "Buyer"},
        "agreement_reference": {"type": "MSA", "date": "2023-01-01"},
        "questions": ["timeline"],
        "requested_due_date": "",
        "urgency_level": "medium",
    }
    payload = {
        "email_text": "Please approve changes to the MSA.",
        "analysis": analysis,
        "contract_snippet": "See clause 9.1 and 10.2",
    }
    r = client.post("/api/draft", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "draft" in data
    assert isinstance(data["draft"], str)
    assert data.get("risk_score") is None or (0 <= data.get("risk_score") <= 100)


def test_process_pipeline():
    payload = {
        "email_text": "We intend to terminate the agreement soon due to liability concerns.",
        "contract_snippet": "Limitation of Liability per 10.2",
    }
    r = client.post("/api/process", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "analysis" in body and "draft" in body
