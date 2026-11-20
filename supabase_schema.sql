-- ============================================================================
-- CYBERTRACE AI — DIGITAL FORENSICS & CYBERCRIME INVESTIGATION PLATFORM
-- COMPLETE POSTGRESQL / SUPABASE RELATIONAL DATABASE DDL SCHEMA
-- ============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. ENUMS
-- ----------------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE userrole AS ENUM ('ADMIN', 'INVESTIGATOR', 'VIEWER');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE casestatus AS ENUM ('ACTIVE', 'UNDER_REVIEW', 'CLOSED', 'ARCHIVED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE casepriority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE casecategory AS ENUM (
        'AUTH_EXPLOIT', 'FIN_FRAUD', 'INTEL', 'MALWARE', 
        'PHISHING', 'DATA_EXFIL', 'NETWORK_INTRUSION', 'INSIDER_THREAT', 'OTHER'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE processingstatus AS ENUM ('UPLOADED', 'PROCESSING', 'EXTRACTED', 'INDEXED', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE integritystatus AS ENUM ('PENDING', 'VERIFIED', 'MISMATCH');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE eventseverity AS ENUM ('INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE threatseverity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE threatstatus AS ENUM ('OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE collectiontype AS ENUM ('cybertrace_case_evidence', 'cybertrace_knowledge');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE indexingstatus AS ENUM ('PENDING', 'INDEXING', 'INDEXED', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE reportstatus AS ENUM ('GENERATING', 'READY', 'FAILED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ----------------------------------------------------------------------------
-- 2. USERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role userrole NOT NULL DEFAULT 'INVESTIGATOR',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);


-- ----------------------------------------------------------------------------
-- 3. INVESTIGATION CASES TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS investigation_cases (
    id VARCHAR(36) PRIMARY KEY,
    case_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category casecategory NOT NULL DEFAULT 'OTHER',
    priority casepriority NOT NULL DEFAULT 'MEDIUM',
    status casestatus NOT NULL DEFAULT 'ACTIVE',
    investigator_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_cases_case_number ON investigation_cases(case_number);
CREATE INDEX IF NOT EXISTS ix_cases_status ON investigation_cases(status);
CREATE INDEX IF NOT EXISTS ix_cases_priority ON investigation_cases(priority);
CREATE INDEX IF NOT EXISTS ix_cases_investigator ON investigation_cases(investigator_id);


-- ----------------------------------------------------------------------------
-- 4. EVIDENCE FILES TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evidence_files (
    id VARCHAR(36) PRIMARY KEY,
    evidence_number VARCHAR(50) UNIQUE NOT NULL,
    case_id VARCHAR(36) NOT NULL REFERENCES investigation_cases(id) ON DELETE CASCADE,
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT,
    sha256_hash VARCHAR(64),
    storage_path VARCHAR(1000) NOT NULL,
    upload_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_status processingstatus NOT NULL DEFAULT 'UPLOADED',
    integrity_status integritystatus NOT NULL DEFAULT 'PENDING',
    uploaded_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS ix_evidence_number ON evidence_files(evidence_number);
CREATE INDEX IF NOT EXISTS ix_evidence_case_id ON evidence_files(case_id);
CREATE INDEX IF NOT EXISTS ix_evidence_status ON evidence_files(processing_status);
CREATE INDEX IF NOT EXISTS ix_evidence_sha256 ON evidence_files(sha256_hash);


-- ----------------------------------------------------------------------------
-- 5. CHAIN OF CUSTODY TABLE (Append-Only Cryptographic Audit Trail)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chain_of_custody (
    id VARCHAR(36) PRIMARY KEY,
    evidence_id VARCHAR(36) NOT NULL REFERENCES evidence_files(id) ON DELETE CASCADE,
    action VARCHAR(200) NOT NULL,
    performed_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    performed_by_name VARCHAR(255),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    previous_record_hash VARCHAR(64),
    record_hash VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS ix_custody_evidence_id ON chain_of_custody(evidence_id);


-- ----------------------------------------------------------------------------
-- 6. INVESTIGATION EVENTS TABLE (Chronological Reconstruction)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS investigation_events (
    id VARCHAR(36) PRIMARY KEY,
    case_id VARCHAR(36) NOT NULL REFERENCES investigation_cases(id) ON DELETE CASCADE,
    evidence_id VARCHAR(36) REFERENCES evidence_files(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    source_ip VARCHAR(45),
    destination_ip VARCHAR(45),
    username VARCHAR(255),
    hostname VARCHAR(255),
    severity eventseverity NOT NULL DEFAULT 'INFO',
    source_reference VARCHAR(500),
    raw_line TEXT
);

CREATE INDEX IF NOT EXISTS ix_events_timestamp ON investigation_events(timestamp);
CREATE INDEX IF NOT EXISTS ix_events_case_id ON investigation_events(case_id);
CREATE INDEX IF NOT EXISTS ix_events_source_ip ON investigation_events(source_ip);


-- ----------------------------------------------------------------------------
-- 7. THREAT DETECTIONS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS threat_detections (
    id VARCHAR(36) PRIMARY KEY,
    case_id VARCHAR(36) NOT NULL REFERENCES investigation_cases(id) ON DELETE CASCADE,
    event_id VARCHAR(36) REFERENCES investigation_events(id) ON DELETE SET NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    severity threatseverity NOT NULL DEFAULT 'MEDIUM',
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    detection_source VARCHAR(100) NOT NULL,
    supporting_evidence TEXT,
    status threatstatus NOT NULL DEFAULT 'OPEN',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_threats_case_id ON threat_detections(case_id);
CREATE INDEX IF NOT EXISTS ix_threats_severity ON threat_detections(severity);


-- ----------------------------------------------------------------------------
-- 8. RAG DOCUMENTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_documents (
    id VARCHAR(36) PRIMARY KEY,
    document_name VARCHAR(500) NOT NULL,
    document_type VARCHAR(50),
    case_id VARCHAR(36) REFERENCES investigation_cases(id) ON DELETE CASCADE,
    evidence_id VARCHAR(36) REFERENCES evidence_files(id) ON DELETE SET NULL,
    collection_type collectiontype NOT NULL,
    indexing_status indexingstatus NOT NULL DEFAULT 'PENDING',
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_ragdoc_case_id ON rag_documents(case_id);
CREATE INDEX IF NOT EXISTS ix_ragdoc_evidence_id ON rag_documents(evidence_id);


-- ----------------------------------------------------------------------------
-- 9. RAG CHUNKS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rag_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES rag_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    line_start INTEGER,
    line_end INTEGER,
    chroma_chunk_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS ix_ragchunk_document_id ON rag_chunks(document_id);


-- ----------------------------------------------------------------------------
-- 10. CHAT HISTORY TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    case_id VARCHAR(36) REFERENCES investigation_cases(id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources_json TEXT,
    findings_json TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_chat_case_id ON chat_history(case_id);
CREATE INDEX IF NOT EXISTS ix_chat_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS ix_chat_user_id ON chat_history(user_id);


-- ----------------------------------------------------------------------------
-- 11. INVESTIGATION REPORTS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS investigation_reports (
    id VARCHAR(36) PRIMARY KEY,
    report_number VARCHAR(50) UNIQUE NOT NULL,
    case_id VARCHAR(36) NOT NULL REFERENCES investigation_cases(id) ON DELETE CASCADE,
    report_title VARCHAR(500) NOT NULL,
    report_path VARCHAR(1000),
    generated_by VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    generated_by_name VARCHAR(255),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status reportstatus NOT NULL DEFAULT 'GENERATING'
);

CREATE INDEX IF NOT EXISTS ix_reports_number ON investigation_reports(report_number);
CREATE INDEX IF NOT EXISTS ix_reports_case_id ON investigation_reports(case_id);


-- ----------------------------------------------------------------------------
-- 12. AUDIT LOGS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    action VARCHAR(200) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(36),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    ip_address VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS ix_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_audit_resource ON audit_logs(resource_type, resource_id);


-- ----------------------------------------------------------------------------
-- 13. SEED INITIAL ADMIN USER
-- Default login: admin@cybertrace.ai / CyberTrace2026!
-- ----------------------------------------------------------------------------
INSERT INTO users (id, full_name, email, password_hash, role, is_active, created_at, updated_at)
VALUES (
    'u-admin-001',
    'Lead Examiner Chen',
    'admin@cybertrace.ai',
    '$2b$12$eWzU5G9P5.857jWlRov9iOsx96Vb/2qO6t33k0eH8YvGk5N3w857a', -- bcrypt hash of 'CyberTrace2026!'
    'ADMIN',
    TRUE,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO NOTHING;
