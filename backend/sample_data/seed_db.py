"""
Seed database with demonstration forensic data.
All records are marked as DEMONSTRATION DATA.
Never represent demonstration findings as real cybercrime investigations.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, create_tables
from app.models.user import User, UserRole
from app.models.case import InvestigationCase, CaseStatus, CasePriority, CaseCategory
from app.models.evidence import EvidenceFile, ProcessingStatus, IntegrityStatus
from app.models.chain_of_custody import ChainOfCustody
from app.models.event import InvestigationEvent, EventSeverity
from app.models.threat import ThreatDetection, ThreatSeverity, ThreatStatus
from app.models.rag_document import RAGDocument, CollectionType, IndexingStatus
from app.core.security import hash_password
from app.services.hash_service import compute_sha256, compute_record_hash
from app.config import settings


def seed():
    print("[*] Initializing database tables...")
    create_tables()

    db = SessionLocal()
    try:
        # 1. Users
        admin = db.query(User).filter(User.email == "admin@cybertrace.ai").first()
        if not admin:
            print("[*] Creating Admin user (admin@cybertrace.ai)...")
            admin = User(
                full_name="Lead Examiner Chen",
                email="admin@cybertrace.ai",
                password_hash=hash_password("CyberTrace2026!"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        investigator = db.query(User).filter(User.email == "chen@cybertrace.ai").first()
        if not investigator:
            print("[*] Creating Investigator user (chen@cybertrace.ai)...")
            investigator = User(
                full_name="Inv. Alex Chen",
                email="chen@cybertrace.ai",
                password_hash=hash_password("Forensics2026!"),
                role=UserRole.INVESTIGATOR,
                is_active=True
            )
            db.add(investigator)
            db.commit()
            db.refresh(investigator)

        # 2. Demonstration Cases
        case1 = db.query(InvestigationCase).filter(InvestigationCase.case_number == "CT-2026-001").first()
        if not case1:
            print("[*] Creating Case CT-2026-001...")
            case1 = InvestigationCase(
                case_number="CT-2026-001",
                title="Unauthorized System Access & Privilege Elevation",
                description="[DEMONSTRATION DATA] Telemetry indicates repeated failed authentication bursts originating from external IP 192.0.2.45 targeting the auth endpoint, followed by successful srv_backup session and sudo elevation.",
                category=CaseCategory.AUTH_EXPLOIT,
                priority=CasePriority.CRITICAL,
                status=CaseStatus.ACTIVE,
                investigator_id=admin.id
            )
            db.add(case1)
            db.commit()
            db.refresh(case1)

        case2 = db.query(InvestigationCase).filter(InvestigationCase.case_number == "CT-2026-002").first()
        if not case2:
            print("[*] Creating Case CT-2026-002...")
            case2 = InvestigationCase(
                case_number="CT-2026-002",
                title="Suspicious Financial Wire Anomaly",
                description="[DEMONSTRATION DATA] Ledger transaction anomaly routed through proxy relays with altered executive signature headers.",
                category=CaseCategory.FIN_FRAUD,
                priority=CasePriority.HIGH,
                status=CaseStatus.UNDER_REVIEW,
                investigator_id=investigator.id
            )
            db.add(case2)
            db.commit()
            db.refresh(case2)

        case3 = db.query(InvestigationCase).filter(InvestigationCase.case_number == "CT-2026-003").first()
        if not case3:
            print("[*] Creating Case CT-2026-003...")
            case3 = InvestigationCase(
                case_number="CT-2026-003",
                title="Spear Phishing Credential Interception",
                description="[DEMONSTRATION DATA] Cloned authentication portal quarantined after deceptive outbound email distribution.",
                category=CaseCategory.PHISHING,
                priority=CasePriority.MEDIUM,
                status=CaseStatus.CLOSED,
                investigator_id=investigator.id
            )
            db.add(case3)
            db.commit()
            db.refresh(case3)

        # 3. Evidence Artifacts for Case 1
        ev1 = db.query(EvidenceFile).filter(EvidenceFile.case_id == case1.id).first()
        if not ev1:
            print("[*] Seeding evidence file records...")
            sample_log_path = Path(__file__).resolve().parent / "auth_server.log"
            log_sha256 = compute_sha256(str(sample_log_path)) if sample_log_path.exists() else "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

            ev1 = EvidenceFile(
                evidence_number="EV-8910-LOG",
                case_id=case1.id,
                original_filename="auth_server.log",
                stored_filename="auth_server_demonstration.log",
                file_type="log",
                file_size=sample_log_path.stat().st_size if sample_log_path.exists() else 26004,
                sha256_hash=log_sha256,
                storage_path=str(sample_log_path),
                processing_status=ProcessingStatus.INDEXED,
                integrity_status=IntegrityStatus.VERIFIED,
                uploaded_by=admin.id,
                chunk_count=14
            )
            db.add(ev1)
            db.commit()
            db.refresh(ev1)

            # Custody records
            c1 = ChainOfCustody(
                evidence_id=ev1.id,
                action="ACQUISITION_AND_HASHING",
                performed_by=admin.id,
                performed_by_name=admin.full_name,
                details="Acquired from compromised auth cluster node US-EAST-04. Write-blocked and SHA-256 generated.",
                record_hash=compute_record_hash("EV-8910-LOG:ACQUIRED")
            )
            db.add(c1)
            db.commit()

        # 4. Investigation Events for Timeline
        events_count = db.query(InvestigationEvent).filter(InvestigationEvent.case_id == case1.id).count()
        if events_count == 0:
            print("[*] Seeding timeline events...")
            base_time = datetime.now(timezone.utc) - timedelta(hours=3)
            demo_events = [
                ("FAILED_LOGIN", "Failed SSH login for root from 192.0.2.45 [Attempt 1/50]", "192.0.2.45", "root", EventSeverity.MEDIUM, base_time),
                ("FAILED_LOGIN", "Failed SSH login for root from 192.0.2.45 [Attempt 2/50]", "192.0.2.45", "root", EventSeverity.MEDIUM, base_time + timedelta(seconds=4)),
                ("FAILED_LOGIN", "Failed SSH login for admin from 192.0.2.45 [Attempt 3/50]", "192.0.2.45", "admin", EventSeverity.MEDIUM, base_time + timedelta(seconds=8)),
                ("FAILED_LOGIN", "Failed SSH login for deploy from 192.0.2.45 [Attempt 4/50]", "192.0.2.45", "deploy", EventSeverity.MEDIUM, base_time + timedelta(seconds=12)),
                ("FAILED_LOGIN", "Failed SSH login for srv_backup from 192.0.2.45 [Attempt 5/50]", "192.0.2.45", "srv_backup", EventSeverity.MEDIUM, base_time + timedelta(seconds=16)),
                ("ACCEPTED_LOGIN", "Accepted password for srv_backup from 192.0.2.45 port 54890", "192.0.2.45", "srv_backup", EventSeverity.INFO, base_time + timedelta(minutes=4)),
                ("SUDO_ELEVATION", "sudo su admin executed by srv_backup (pts/2)", "192.0.2.45", "srv_backup", EventSeverity.HIGH, base_time + timedelta(minutes=4, seconds=1)),
                ("SUSPICIOUS_ACCESS", "Read attempt on /etc/shadow by admin", "192.0.2.45", "admin", EventSeverity.CRITICAL, base_time + timedelta(minutes=5))
            ]
            for etype, desc, ip, user, sev, ts in demo_events:
                ev = InvestigationEvent(
                    case_id=case1.id,
                    evidence_id=ev1.id,
                    timestamp=ts,
                    event_type=etype,
                    description=desc,
                    source_ip=ip,
                    username=user,
                    severity=sev,
                    source_reference="auth_server.log"
                )
                db.add(ev)
            db.commit()

        # 5. Threats
        threat_count = db.query(ThreatDetection).filter(ThreatDetection.case_id == case1.id).count()
        if threat_count == 0:
            print("[*] Seeding threat indicators...")
            t1 = ThreatDetection(
                case_id=case1.id,
                category="BRUTE_FORCE",
                description="Repeated failed authentications (8 attempts within 32s) originating from 192.0.2.45 targeting multiple privileged accounts.",
                severity=ThreatSeverity.HIGH,
                confidence=0.96,
                detection_source="rule_based",
                status=ThreatStatus.OPEN
            )
            t2 = ThreatDetection(
                case_id=case1.id,
                category="PRIVILEGE_ESCALATION",
                description="Successful login for srv_backup followed immediately by sudo elevation command to root.",
                severity=ThreatSeverity.CRITICAL,
                confidence=0.94,
                detection_source="rule_based",
                status=ThreatStatus.OPEN
            )
            db.add_all([t1, t2])
            db.commit()

        print("[+] Database seeding complete! Demonstration records ready.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
