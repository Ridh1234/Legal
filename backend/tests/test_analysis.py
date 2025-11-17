import os
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_api_basic():
    payload = {"email_text": "Hello, please approve the change ASAP. This concerns the MSA."}
    r = client.post("/api/analyze", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Basic shape checks for new schema
    assert isinstance(data.get("intent", ""), str)
    assert isinstance(data.get("primary_topic", ""), str)
    assert data.get("urgency_level", "") in {"", "low", "medium", "high"}
    assert isinstance(data.get("requested_due_date", ""), str)
    assert isinstance(data.get("questions", []), list)
    # Parties object
    parties = data.get("parties", {})
    assert isinstance(parties, dict)
    assert isinstance(parties.get("client", ""), str)
    assert isinstance(parties.get("counterparty", ""), str)
    # Agreement reference object
    agr = data.get("agreement_reference", {})
    assert isinstance(agr, dict)
    assert isinstance(agr.get("type", ""), str)
    assert isinstance(agr.get("date", ""), str)

