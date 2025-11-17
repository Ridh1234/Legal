from backend.services.vectorstore import retrieve_relevant_clauses

def test_retrieve_default():
    text = retrieve_relevant_clauses("")
    assert isinstance(text, str)
    assert len(text) > 0


def test_retrieve_with_query():
    text = retrieve_relevant_clauses("confidentiality and limitation")
    assert isinstance(text, str)
    assert len(text) > 0
