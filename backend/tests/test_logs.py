import io


def test_log_analysis_failed_logins(client, auth_headers):
    sample_log = (
        "2026-11-18T22:14:01Z auth.warn sshd Failed password for root from 192.0.2.45\n"
        "2026-11-18T22:14:05Z auth.warn sshd Failed password for root from 192.0.2.45\n"
        "2026-11-18T22:14:09Z auth.warn sshd Failed password for admin from 192.0.2.45\n"
        "2026-11-18T22:14:14Z auth.warn sshd Failed password for admin from 192.0.2.45\n"
        "2026-11-18T22:14:18Z auth.warn sshd Failed password for deploy from 192.0.2.45\n"
        "2026-11-18T22:18:09Z auth.info sshd Accepted password for srv_backup from 192.0.2.45\n"
        "2026-11-18T22:18:10Z audit sudo srv_backup TTY=pts/2 COMMAND=/bin/bash\n"
    )

    file_tuple = ("syslog.log", io.BytesIO(sample_log.encode()), "text/plain")
    res = client.post("/api/logs/analyze", files={"file": file_tuple}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["parsed_events"] >= 6
    assert len(data["findings"]) > 0

    categories = [f["category"] for f in data["findings"]]
    assert "BRUTE_FORCE" in categories or "SUSPICIOUS_LOGIN" in categories
