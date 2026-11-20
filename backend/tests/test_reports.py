import os


def test_pdf_report_generation_and_download(client, auth_headers):
    # Create case
    case_res = client.post("/api/cases", json={"title": "Report Test Case", "description": "Testing PDF export"}, headers=auth_headers)
    case_id = case_res.json()["id"]

    # Generate Report
    gen_res = client.post("/api/reports/generate", json={"case_id": case_id, "report_title": "Official Test Report"}, headers=auth_headers)
    assert gen_res.status_code == 201
    report_data = gen_res.json()
    assert report_data["status"] == "READY"
    report_id = report_data["id"]

    # Download Report
    down_res = client.get(f"/api/reports/{report_id}/download", headers=auth_headers)
    assert down_res.status_code == 200
    assert down_res.headers["content-type"] == "application/pdf"
    assert len(down_res.content) > 1000  # valid PDF bytes
