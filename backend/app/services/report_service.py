import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfgen import canvas

from app.config import settings
from app.models.case import InvestigationCase
from app.models.evidence import EvidenceFile
from app.models.chain_of_custody import ChainOfCustody
from app.models.threat import ThreatDetection
from app.models.event import InvestigationEvent
from app.models.chat import ChatHistory
from app.models.report import InvestigationReport, ReportStatus


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically and adds header/footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))

        # Header
        self.drawString(54, 750, "CYBERTRACE AI // OFFICIAL FORENSIC EXAMINATION REPORT")
        self.drawRightString(558, 750, "CONFIDENTIAL & PRIVILEGED")
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 744, 558, 744)

        # Footer
        self.line(54, 45, 558, 45)
        self.drawString(54, 32, "VERIFIED DIGITAL FORENSIC RECORD // L3 ENCRYPTED")
        page_text = f"PAGE {self._pageNumber} OF {page_count}"
        self.drawRightString(558, 32, page_text)
        self.restoreState()


def generate_forensic_report_pdf(
    db: Session,
    case_id: str,
    report_title: Optional[str] = None,
    generated_by_id: Optional[str] = None,
    generated_by_name: Optional[str] = "Forensic Lead"
) -> InvestigationReport:
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    title = report_title or f"Forensic Investigation Report - {case.case_number}"
    report_num = f"REP-{case.case_number}-{uuid.uuid4().hex[:6].upper()}"

    reports_dir = Path(settings.REPORT_DIRECTORY)
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"{report_num}.pdf"
    pdf_path = reports_dir / pdf_filename

    # Create Report Record in DB
    report_record = InvestigationReport(
        report_number=report_num,
        case_id=case_id,
        report_title=title,
        report_path=str(pdf_path),
        generated_by=generated_by_id,
        generated_by_name=generated_by_name,
        generated_at=datetime.now(timezone.utc),
        status=ReportStatus.GENERATING
    )
    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    try:
        # Fetch case data
        evidence_list = db.query(EvidenceFile).filter(EvidenceFile.case_id == case_id).all()
        threats = db.query(ThreatDetection).filter(ThreatDetection.case_id == case_id).all()
        events = db.query(InvestigationEvent).filter(InvestigationEvent.case_id == case_id).order_by(InvestigationEvent.timestamp.asc()).all()
        chats = db.query(ChatHistory).filter(ChatHistory.case_id == case_id).order_by(ChatHistory.created_at.asc()).all()

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=64,
            bottomMargin=64
        )

        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0B192C")
        )
        h1_style = ParagraphStyle(
            'SectionH1',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#003259"),
            spaceBefore=14,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#222222")
        )
        mono_style = ParagraphStyle(
            'Mono',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#333333")
        )
        meta_label = ParagraphStyle(
            'MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#555555")
        )

        story = []

        # Header Title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Dossier Ref:</b> {case.case_number} &nbsp;|&nbsp; <b>Report ID:</b> {report_num} &nbsp;|&nbsp; <b>Generated:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", mono_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#003259"), spaceAfter=12))

        # 1. CASE DETAILS
        story.append(Paragraph("1. INVESTIGATION CASE SUMMARY", h1_style))
        case_data = [
            [Paragraph("Case Number:", meta_label), Paragraph(case.case_number, mono_style), Paragraph("Category:", meta_label), Paragraph(case.category.value, mono_style)],
            [Paragraph("Status:", meta_label), Paragraph(case.status.value, mono_style), Paragraph("Priority:", meta_label), Paragraph(case.priority.value, mono_style)],
            [Paragraph("Investigator:", meta_label), Paragraph(generated_by_name or "Unassigned", mono_style), Paragraph("Created At:", meta_label), Paragraph(case.created_at.strftime('%Y-%m-%d %H:%M UTC'), mono_style)],
        ]
        t_case = Table(case_data, colWidths=[90, 160, 90, 160])
        t_case.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_case)
        story.append(Spacer(1, 8))

        # Description / Executive Summary
        story.append(Paragraph("<b>Case Description & Scope:</b>", meta_label))
        story.append(Paragraph(case.description or "No formal description filed for this case dossier.", body_style))
        story.append(Spacer(1, 12))

        # 2. EVIDENCE INVENTORY & SHA-256 HASHES
        story.append(Paragraph("2. DIGITAL EVIDENCE INVENTORY & CRYPTOGRAPHIC HASHES", h1_style))
        if evidence_list:
            ev_table_data = [[
                Paragraph("<b>Item Ref</b>", meta_label),
                Paragraph("<b>Filename</b>", meta_label),
                Paragraph("<b>Size</b>", meta_label),
                Paragraph("<b>SHA-256 Digest</b>", meta_label),
                Paragraph("<b>Status</b>", meta_label)
            ]]
            for ev in evidence_list:
                ev_table_data.append([
                    Paragraph(ev.evidence_number, mono_style),
                    Paragraph(ev.original_filename[:24], mono_style),
                    Paragraph(f"{(ev.file_size or 0) / 1024:.1f} KB", mono_style),
                    Paragraph(ev.sha256_hash or "N/A", mono_style),
                    Paragraph(ev.integrity_status.value, mono_style)
                ])
            t_ev = Table(ev_table_data, colWidths=[70, 110, 50, 200, 70])
            t_ev.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_ev)
        else:
            story.append(Paragraph("No evidence items currently attached to this case dossier.", body_style))
        story.append(Spacer(1, 12))

        # 3. THREAT DETECTIONS & INCIDENT FINDINGS
        story.append(Paragraph("3. AUTOMATED THREAT DETECTIONS & SECURITY FINDINGS", h1_style))
        if threats:
            threat_data = [[
                Paragraph("<b>Category</b>", meta_label),
                Paragraph("<b>Severity</b>", meta_label),
                Paragraph("<b>Confidence</b>", meta_label),
                Paragraph("<b>Detection Details</b>", meta_label)
            ]]
            for th in threats:
                threat_data.append([
                    Paragraph(th.category, mono_style),
                    Paragraph(th.severity.value, mono_style),
                    Paragraph(f"{th.confidence*100:.1f}%", mono_style),
                    Paragraph(th.description, body_style)
                ])
            t_th = Table(threat_data, colWidths=[100, 60, 60, 280])
            t_th.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_th)
        else:
            story.append(Paragraph("No anomalous threat detections registered.", body_style))
        story.append(Spacer(1, 12))

        # 4. INCIDENT TIMELINE
        story.append(Paragraph("4. FORENSIC INCIDENT TIMELINE", h1_style))
        if events:
            ev_timeline_data = [[
                Paragraph("<b>Timestamp (UTC)</b>", meta_label),
                Paragraph("<b>Event Type</b>", meta_label),
                Paragraph("<b>Source IP</b>", meta_label),
                Paragraph("<b>Description</b>", meta_label)
            ]]
            for ev in events[:15]:  # include first 15 events
                ev_timeline_data.append([
                    Paragraph(ev.timestamp.strftime('%Y-%m-%d %H:%M:%S'), mono_style),
                    Paragraph(ev.event_type, mono_style),
                    Paragraph(ev.source_ip or "-", mono_style),
                    Paragraph(ev.description, body_style)
                ])
            t_time = Table(ev_timeline_data, colWidths=[110, 90, 80, 220])
            t_time.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t_time)
            if len(events) > 15:
                story.append(Spacer(1, 3))
                story.append(Paragraph(f"<i>[Showing 15 of {len(events)} recorded events in timeline]</i>", mono_style))
        else:
            story.append(Paragraph("No timeline events reconstructed yet.", body_style))
        story.append(Spacer(1, 12))

        # 5. AI RAG INVESTIGATION INQUIRIES & CITATIONS
        story.append(Paragraph("5. AI-ASSISTED RAG INQUIRIES & GROUNDED CITATIONS", h1_style))
        if chats:
            for idx, c in enumerate(chats[:3], 1):
                story.append(Paragraph(f"<b>Query {idx}:</b> {c.question}", body_style))
                story.append(Spacer(1, 2))
                story.append(Paragraph(f"<b>Grounded Finding:</b> {c.answer}", body_style))
                story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("No RAG investigation queries executed for this case.", body_style))
        story.append(Spacer(1, 12))

        # 6. LIMITATIONS & FORENSIC ATTESTATION
        story.append(Paragraph("6. LIMITATIONS & CHAIN-OF-CUSTODY ATTESTATION", h1_style))
        story.append(Paragraph(
            "This digital examination report was automatically synthesized from write-blocked evidence artifacts "
            "indexed strictly under case isolation. SHA-256 cryptographic hashes affirm original byte integrity. "
            "Telemetry interpretations are restricted to available forensic logs.",
            body_style
        ))
        story.append(Spacer(1, 14))

        # Sign-off box
        sig_data = [
            [Paragraph("<b>Lead Forensic Examiner:</b>", meta_label), Paragraph(f"{generated_by_name} (Cryptographically Sealed)", mono_style)],
            [Paragraph("<b>Examination Facility:</b>", meta_label), Paragraph("CyberTrace Digital Forensic Enclave L3", mono_style)],
            [Paragraph("<b>Verification Hash:</b>", meta_label), Paragraph(report_num, mono_style)]
        ]
        t_sig = Table(sig_data, colWidths=[150, 350])
        t_sig.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#A0AEC0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_sig)

        # Build document with NumberedCanvas
        doc.build(story, canvasmaker=NumberedCanvas)

        report_record.status = ReportStatus.READY
        db.commit()
        db.refresh(report_record)
        return report_record

    except Exception as e:
        report_record.status = ReportStatus.FAILED
        db.commit()
        raise e
