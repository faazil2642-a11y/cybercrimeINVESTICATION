from unittest.mock import patch
from app.rag.chunking import chunk_text


def test_chunking_with_line_metadata():
    sample_text = (
        "Line 1: System initialization\n"
        "Line 2: Network interface eth0 up\n"
        "Line 3: Daemon listening on port 22\n"
        "Line 4: Connection from 192.0.2.45\n"
        "Line 5: Authentication failure\n"
    )

    chunks = chunk_text(
        text=sample_text,
        chunk_size=50,
        chunk_overlap=10,
        document_id="doc-123",
        evidence_id="ev-456",
        case_id="case-789",
        filename="test.log"
    )

    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert "metadata" in first_chunk
    assert first_chunk["metadata"]["case_id"] == "case-789"
    assert first_chunk["metadata"]["filename"] == "test.log"
    assert first_chunk["metadata"]["line_start"] == 1


def test_rag_chat_ai_not_configured_when_no_key(client, auth_headers):
    # Create case
    case_res = client.post("/api/cases", json={"title": "RAG Case"}, headers=auth_headers)
    case_id = case_res.json()["id"]

    # When GEMINI_API_KEY is unset, should return 503 AINotConfiguredError gracefully
    chat_payload = {
        "case_id": case_id,
        "session_id": "sess-01",
        "question": "What happened?"
    }
    with patch("app.config.settings.GEMINI_API_KEY", ""):
        res = client.post("/api/investigation/chat", json=chat_payload, headers=auth_headers)
        assert res.status_code == 503
        assert "AI provider not configured" in res.json()["detail"]
