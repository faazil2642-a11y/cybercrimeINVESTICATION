def test_create_and_get_case(client, auth_headers):
    payload = {
        "title": "Suspected Ransomware Outbreak",
        "description": "Critical enterprise share lock observed.",
        "category": "MALWARE",
        "priority": "CRITICAL"
    }
    res = client.post("/api/cases", json=payload, headers=auth_headers)
    assert res.status_code == 201
    case_data = res.json()
    assert case_data["title"] == payload["title"]
    assert "CT-" in case_data["case_number"]

    # Retrieve by ID
    case_id = case_data["id"]
    get_res = client.get(f"/api/cases/{case_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["case_number"] == case_data["case_number"]


def test_list_cases_filter(client, auth_headers):
    client.post("/api/cases", json={"title": "Case Alpha", "category": "AUTH_EXPLOIT"}, headers=auth_headers)
    client.post("/api/cases", json={"title": "Case Beta", "category": "FIN_FRAUD"}, headers=auth_headers)

    res = client.get("/api/cases?category=AUTH_EXPLOIT", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert all(c["category"] == "AUTH_EXPLOIT" for c in items)


def test_update_case_status(client, auth_headers):
    create_res = client.post("/api/cases", json={"title": "Case To Update"}, headers=auth_headers)
    case_id = create_res.json()["id"]

    update_payload = {"status": "CLOSED", "priority": "LOW"}
    res = client.put(f"/api/cases/{case_id}", json=update_payload, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "CLOSED"
    assert res.json()["priority"] == "LOW"
