import io
import hashlib


def test_evidence_upload_and_hash(client, auth_headers):
    # Create case first
    case_res = client.post("/api/cases", json={"title": "Forensic Vault Case"}, headers=auth_headers)
    case_id = case_res.json()["id"]

    test_content = b"2026-11-18T22:14:01Z auth.warn sshd Failed password for root from 192.0.2.45"
    expected_hash = hashlib.sha256(test_content).hexdigest()

    file_tuple = ("auth.log", io.BytesIO(test_content), "text/plain")
    data = {"case_id": case_id}

    res = client.post("/api/evidence/upload", data=data, files={"file": file_tuple}, headers=auth_headers)
    assert res.status_code == 201
    ev_data = res.json()
    assert ev_data["sha256_hash"] == expected_hash
    assert ev_data["case_id"] == case_id

    # Verify hash endpoint
    ev_id = ev_data["id"]
    hash_res = client.get(f"/api/evidence/{ev_id}/hash", headers=auth_headers)
    assert hash_res.status_code == 200
    assert hash_res.json()["match"] is True

    # Verify chain of custody was created
    custody_res = client.get(f"/api/evidence/{ev_id}/custody", headers=auth_headers)
    assert custody_res.status_code == 200
    records = custody_res.json()
    assert len(records) >= 1
    assert "ACQUIRED" in records[0]["action"]
