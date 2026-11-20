"""
Log Analysis Engine
Supports: Linux auth log (syslog), Windows Event CSV, JSON logs, generic text logs.
Uses rule-based detection + scikit-learn IsolationForest.
"""
import re
import json
import csv
import io
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple
import uuid


# ── Parsers ─────────────────────────────────────────────────────────────────

SYSLOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
    r".*?(?:sshd|sudo|auth|PAM|login)"
    r".*?(?P<message>.*)",
    re.IGNORECASE,
)

SYSLOG_LEGACY = re.compile(
    r"(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<process>\S+?)(?:\[\d+\])?:\s+(?P<message>.*)"
)

IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
USER_RE = re.compile(r"(?:for|user|from)\s+(\S+)", re.IGNORECASE)
FAILED_RE = re.compile(r"failed|invalid|failure|rejected|unauthorized|error", re.IGNORECASE)
SUCCESS_RE = re.compile(r"accepted|successful|logged in|session opened|authenticated", re.IGNORECASE)
SUDO_RE = re.compile(r"sudo|su\s|privilege|elevation|root", re.IGNORECASE)


def _parse_timestamp(ts_str: str) -> Optional[datetime]:
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(ts_str.rstrip("Z"), fmt.rstrip("Z"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def parse_log_file(content: str, log_format: str = "auto") -> List[Dict[str, Any]]:
    """Parse log content into structured event list."""
    if log_format == "auto":
        log_format = _detect_format(content)

    if log_format == "windows_csv":
        return _parse_windows_csv(content)
    elif log_format == "json":
        return _parse_json_log(content)
    elif log_format == "syslog":
        return _parse_syslog(content)
    else:
        return _parse_generic(content)


def _detect_format(content: str) -> str:
    first_lines = content[:2000]
    if first_lines.strip().startswith("{") or first_lines.strip().startswith("["):
        return "json"
    if re.search(r"TimeCreated|EventId|EventID|RecordId", first_lines, re.IGNORECASE):
        return "windows_csv"
    if re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*sshd|auth\.warn|auth\.info", first_lines):
        return "syslog"
    if re.search(r"\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\S+\s+sshd", first_lines):
        return "syslog"
    return "generic"


def _parse_syslog(content: str) -> List[Dict]:
    events = []
    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        m = SYSLOG_PATTERN.search(line)
        if m:
            ts = _parse_timestamp(m.group("timestamp"))
            msg = m.group("message").strip()
        else:
            m2 = SYSLOG_LEGACY.match(line)
            if m2:
                year = datetime.now(timezone.utc).year
                ts_str = f"{year} {m2.group('month')} {m2.group('day')} {m2.group('time')}"
                try:
                    ts = datetime.strptime(ts_str, "%Y %b %d %H:%M:%S").replace(tzinfo=timezone.utc)
                except ValueError:
                    ts = None
                msg = m2.group("message")
            else:
                ts = None
                msg = line

        ips = IP_RE.findall(line)
        users = USER_RE.findall(msg)
        events.append({
            "line_number": line_num,
            "timestamp": ts,
            "message": msg,
            "raw": line,
            "source_ip": ips[0] if ips else None,
            "username": users[0] if users else None,
            "is_failed": bool(FAILED_RE.search(msg)),
            "is_success": bool(SUCCESS_RE.search(msg)),
            "is_sudo": bool(SUDO_RE.search(msg)),
        })
    return events


def _parse_windows_csv(content: str) -> List[Dict]:
    events = []
    try:
        reader = csv.DictReader(io.StringIO(content))
        for line_num, row in enumerate(reader, 1):
            ts_str = row.get("TimeCreated") or row.get("Time") or ""
            ts = _parse_timestamp(ts_str) if ts_str else None
            msg = row.get("Message") or row.get("Description") or str(row)
            ips = IP_RE.findall(msg)
            users = USER_RE.findall(msg)
            events.append({
                "line_number": line_num,
                "timestamp": ts,
                "message": msg,
                "raw": str(row),
                "source_ip": ips[0] if ips else None,
                "username": users[0] if users else row.get("SubjectUserName", ""),
                "event_id": row.get("EventId") or row.get("EventID", ""),
                "is_failed": bool(FAILED_RE.search(msg)),
                "is_success": bool(SUCCESS_RE.search(msg)),
                "is_sudo": bool(SUDO_RE.search(msg)),
            })
    except Exception:
        pass
    return events


def _parse_json_log(content: str) -> List[Dict]:
    events = []
    try:
        data = json.loads(content)
        if not isinstance(data, list):
            data = [data]
        for line_num, entry in enumerate(data, 1):
            ts_str = (
                entry.get("timestamp") or entry.get("time") or
                entry.get("@timestamp") or entry.get("TimeCreated") or ""
            )
            ts = _parse_timestamp(str(ts_str)) if ts_str else None
            msg = entry.get("message") or entry.get("msg") or json.dumps(entry)
            ips = IP_RE.findall(msg)
            users = USER_RE.findall(msg)
            events.append({
                "line_number": line_num,
                "timestamp": ts,
                "message": str(msg),
                "raw": json.dumps(entry),
                "source_ip": ips[0] if ips else entry.get("src_ip"),
                "username": users[0] if users else entry.get("user") or entry.get("username", ""),
                "is_failed": bool(FAILED_RE.search(str(msg))),
                "is_success": bool(SUCCESS_RE.search(str(msg))),
                "is_sudo": bool(SUDO_RE.search(str(msg))),
            })
    except Exception:
        return _parse_generic(content)
    return events


def _parse_generic(content: str) -> List[Dict]:
    events = []
    ts_re = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
    for line_num, line in enumerate(content.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        ts_match = ts_re.search(line)
        ts = _parse_timestamp(ts_match.group()) if ts_match else None
        ips = IP_RE.findall(line)
        users = USER_RE.findall(line)
        events.append({
            "line_number": line_num,
            "timestamp": ts,
            "message": line,
            "raw": line,
            "source_ip": ips[0] if ips else None,
            "username": users[0] if users else None,
            "is_failed": bool(FAILED_RE.search(line)),
            "is_success": bool(SUCCESS_RE.search(line)),
            "is_sudo": bool(SUDO_RE.search(line)),
        })
    return events


# ── Detection Rules ──────────────────────────────────────────────────────────

def detect_threats(events: List[Dict]) -> List[Dict]:
    """
    Apply rule-based detection + IsolationForest anomaly detection.
    Returns list of finding dicts.
    """
    findings = []

    # Group by source IP
    ip_events: Dict[str, List[Dict]] = defaultdict(list)
    ip_users: Dict[str, set] = defaultdict(set)
    for ev in events:
        ip = ev.get("source_ip")
        if ip:
            ip_events[ip].append(ev)
            user = ev.get("username")
            if user:
                ip_users[ip].add(user)

    for ip, ip_evs in ip_events.items():
        failed = [e for e in ip_evs if e["is_failed"]]
        success = [e for e in ip_evs if e["is_success"]]
        sudo = [e for e in ip_evs if e["is_sudo"]]

        # Rule 1: Brute force (>5 failed within 10 minutes)
        if len(failed) >= 5:
            timestamps = [e["timestamp"] for e in failed if e["timestamp"]]
            if _within_window(timestamps, minutes=10):
                findings.append({
                    "finding_id": str(uuid.uuid4()),
                    "category": "BRUTE_FORCE",
                    "severity": "HIGH" if len(failed) >= 20 else "MEDIUM",
                    "description": f"Potential brute-force attack: {len(failed)} failed login attempts detected from IP {ip}.",
                    "source_ip": ip,
                    "username": list(ip_users[ip])[:3],
                    "timestamp": timestamps[0] if timestamps else None,
                    "event_count": len(failed),
                    "evidence_lines": [e["raw"] for e in failed[:5]],
                    "detection_method": "rule_based",
                })

        # Rule 2: Success after repeated failures
        if failed and success and len(failed) >= 3:
            findings.append({
                "finding_id": str(uuid.uuid4()),
                "category": "SUSPICIOUS_LOGIN",
                "severity": "HIGH",
                "description": f"Successful login from IP {ip} following {len(failed)} failed attempts — potential credential compromise.",
                "source_ip": ip,
                "username": list(ip_users[ip])[:3],
                "timestamp": success[0]["timestamp"] if success[0]["timestamp"] else None,
                "event_count": len(failed) + len(success),
                "evidence_lines": [e["raw"] for e in (failed[-3:] + success[:2])],
                "detection_method": "rule_based",
            })

        # Rule 3: Privilege escalation
        if sudo:
            findings.append({
                "finding_id": str(uuid.uuid4()),
                "category": "PRIVILEGE_ESCALATION",
                "severity": "MEDIUM",
                "description": f"Privilege escalation activity observed from IP {ip}.",
                "source_ip": ip,
                "username": list(ip_users[ip])[:3],
                "timestamp": sudo[0]["timestamp"],
                "event_count": len(sudo),
                "evidence_lines": [e["raw"] for e in sudo[:3]],
                "detection_method": "rule_based",
            })

        # Rule 4: Multiple accounts from one IP
        if len(ip_users[ip]) >= 3:
            findings.append({
                "finding_id": str(uuid.uuid4()),
                "category": "CREDENTIAL_STUFFING",
                "severity": "MEDIUM",
                "description": f"IP {ip} accessed {len(ip_users[ip])} different accounts: {', '.join(list(ip_users[ip])[:5])}.",
                "source_ip": ip,
                "username": list(ip_users[ip]),
                "timestamp": ip_evs[0]["timestamp"],
                "event_count": len(ip_evs),
                "evidence_lines": [e["raw"] for e in ip_evs[:3]],
                "detection_method": "rule_based",
            })

    # Rule 5: After-hours access
    after_hours = [
        e for e in events
        if e["is_success"] and e["timestamp"] and
        (e["timestamp"].hour < 7 or e["timestamp"].hour >= 20)
    ]
    if after_hours:
        for ev in after_hours[:5]:
            findings.append({
                "finding_id": str(uuid.uuid4()),
                "category": "AFTER_HOURS_ACCESS",
                "severity": "LOW",
                "description": f"Successful authentication at unusual hour ({ev['timestamp'].strftime('%H:%M UTC') if ev['timestamp'] else 'unknown'}) from {ev.get('source_ip','?')}.",
                "source_ip": ev.get("source_ip"),
                "username": [ev.get("username")] if ev.get("username") else [],
                "timestamp": ev["timestamp"],
                "event_count": 1,
                "evidence_lines": [ev["raw"]],
                "detection_method": "rule_based",
            })

    # Anomaly detection with IsolationForest
    findings.extend(_isolation_forest_detect(events, ip_events))

    return findings


def _within_window(timestamps: List, minutes: int = 10) -> bool:
    """Check if any burst of events occurs within the given time window."""
    valid = sorted([t for t in timestamps if t])
    if len(valid) < 2:
        return True  # Can't verify window; assume suspicious
    window = timedelta(minutes=minutes)
    for i in range(len(valid) - 1):
        if valid[-1] - valid[0] <= window:
            return True
        if valid[i + 1] - valid[i] <= window:
            return True
    return False


def _isolation_forest_detect(events: List[Dict], ip_events: Dict) -> List[Dict]:
    """Detect anomalous IPs by login frequency using IsolationForest."""
    findings = []
    if len(ip_events) < 5:
        return findings
    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np

        ips = list(ip_events.keys())
        X = np.array([[len(v)] for v in ip_events.values()], dtype=float)

        clf = IsolationForest(contamination=0.1, random_state=42)
        preds = clf.fit_predict(X)

        for i, (ip, pred) in enumerate(zip(ips, preds)):
            if pred == -1:  # anomaly
                count = len(ip_events[ip])
                findings.append({
                    "finding_id": str(uuid.uuid4()),
                    "category": "ANOMALOUS_FREQUENCY",
                    "severity": "MEDIUM",
                    "description": f"Statistically anomalous login frequency from IP {ip} ({count} events). Detected via IsolationForest.",
                    "source_ip": ip,
                    "username": [],
                    "timestamp": ip_events[ip][0]["timestamp"],
                    "event_count": count,
                    "evidence_lines": [ip_events[ip][0]["raw"]],
                    "detection_method": "isolation_forest",
                })
    except ImportError:
        pass
    except Exception:
        pass
    return findings
