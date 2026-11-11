import os
import csv
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas

REPORTS_DIR = Path(__file__).resolve().parent / "evidence" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class NumberedCanvas(canvas.Canvas):
    """Custom canvas to compute total page count and render professional footers."""
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header rule & title
        self.setLineWidth(0.5)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.line(40, 755, 572, 755)
        self.drawString(40, 760, "Industrial Safety AI Surveillance System — Audit Report")

        # Footer
        self.line(40, 45, 572, 45)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 32, page_str)
        self.drawString(40, 32, f"Confidential & Proprietary • Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.restoreState()


def generate_csv_report(
    incidents: List[Dict[str, Any]],
    report_type: str,
    title: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """Generate filtered CSV report file from actual incident records."""
    report_id = f"rpt_csv_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    filename = f"{report_id}.csv"
    filepath = REPORTS_DIR / filename

    with open(str(filepath), mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        
        # Meta header comments
        writer.writerow(["# Application:", "Industrial Safety AI Surveillance System"])
        writer.writerow(["# Report Title:", title])
        writer.writerow(["# Report Type:", report_type])
        writer.writerow(["# Date Range:", f"{start_date or 'Earliest'} to {end_date or 'Latest'}"])
        writer.writerow(["# Generated At:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["# Total Records:", len(incidents)])
        writer.writerow([])  # blank line separator

        # Header columns
        headers = [
            "Incident ID", "Timestamp", "Violation Category", "Severity",
            "Confidence", "Detection Source", "Status", "Resolution Date",
            "Resolution Notes", "Evidence File"
        ]
        writer.writerow(headers)

        # Data rows
        for inc in incidents:
            writer.writerow([
                inc.get("incident_id", ""),
                inc.get("timestamp", ""),
                inc.get("violation_category", ""),
                inc.get("severity", ""),
                f"{inc.get('confidence', 0.0):.2f}",
                inc.get("source", ""),
                inc.get("status", "NEW"),
                inc.get("resolved_at") or "—",
                inc.get("resolution_notes") or "—",
                inc.get("evidence_path", "")
            ])

    return str(filepath)


def generate_pdf_report(
    incidents: List[Dict[str, Any]],
    report_type: str,
    title: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    stats: Optional[Dict[str, Any]] = None
) -> str:
    """Generate a high-level industrial PDF audit report with tables, metrics, and styling."""
    report_id = f"rpt_pdf_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    filename = f"{report_id}.pdf"
    filepath = REPORTS_DIR / filename

    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=55,
        bottomMargin=55
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0e1322")
    )
    style_subtitle = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#64748b")
    )
    style_h2 = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6
    )
    style_cell = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b")
    )
    style_cell_bold = ParagraphStyle(
        'CellBold',
        parent=style_cell,
        fontName='Helvetica-Bold'
    )
    style_kpi_num = ParagraphStyle(
        'KpiNum',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=18,
        alignment=1,
        textColor=colors.HexColor("#4f46e5")
    )
    style_kpi_lbl = ParagraphStyle(
        'KpiLbl',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=9,
        alignment=1,
        textColor=colors.HexColor("#64748b")
    )

    story = []

    # Title & Subtitle banner
    story.append(Paragraph(title, style_title))
    story.append(Spacer(1, 4))
    date_range_str = f"Inspection Window: <b>{start_date or 'Earliest'}</b> to <b>{end_date or 'Present'}</b> • Report Type: <b>{report_type}</b>"
    story.append(Paragraph(date_range_str, style_subtitle))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=14))

    # Compute key KPIs for report
    total_inc = len(incidents)
    critical_count = sum(1 for i in incidents if i.get("severity") == "CRITICAL")
    high_count = sum(1 for i in incidents if i.get("severity") == "HIGH")
    resolved_count = sum(1 for i in incidents if i.get("status") == "RESOLVED")
    open_count = sum(1 for i in incidents if i.get("status") in ("NEW", "OPEN"))
    compliance_str = (stats.get("compliance_rate") if stats else None) or "Not enough data"

    # KPI Summary Cards Grid
    kpi_data = [
        [
            Paragraph(f"{total_inc}", style_kpi_num),
            Paragraph(f"{critical_count}", style_kpi_num),
            Paragraph(f"{resolved_count}", style_kpi_num),
            Paragraph(f"{compliance_str}", style_kpi_num)
        ],
        [
            Paragraph("TOTAL INCIDENTS", style_kpi_lbl),
            Paragraph("CRITICAL SEVERITY", style_kpi_lbl),
            Paragraph("RESOLVED STATUS", style_kpi_lbl),
            Paragraph("PPE COMPLIANCE", style_kpi_lbl)
        ]
    ]
    t_kpi = Table(kpi_data, colWidths=[133, 133, 133, 133])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 16))

    # Breakdown by Violation Category Table
    story.append(Paragraph("1. PPE Violation Category Breakdown", style_h2))
    cat_counts = {}
    for i in incidents:
        c = i.get("violation_category", "Unknown")
        cat_counts[c] = cat_counts.get(c, 0) + 1

    cat_rows = [[Paragraph("Violation Category", style_cell_bold), Paragraph("Incident Count", style_cell_bold), Paragraph("Share of Violations", style_cell_bold)]]
    for c, cnt in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (cnt / total_inc * 100) if total_inc > 0 else 0
        cat_rows.append([
            Paragraph(f"<b>{c}</b>", style_cell),
            Paragraph(str(cnt), style_cell),
            Paragraph(f"{pct:.1f}%", style_cell)
        ])
    if len(cat_rows) == 1:
        cat_rows.append([Paragraph("No violations recorded in selected window.", style_cell), Paragraph("0", style_cell), Paragraph("0.0%", style_cell)])

    t_cats = Table(cat_rows, colWidths=[240, 140, 152])
    t_cats.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor("#cbd5e1")),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_cats)
    story.append(Spacer(1, 16))

    # Detailed Incident Audit Table (Top 35 records to ensure clean PDF pagination)
    story.append(Paragraph(f"2. Incident Log Details ({min(len(incidents), 35)} of {len(incidents)} Records Shown)", style_h2))
    
    inc_table_data = [
        [
            Paragraph("Incident ID", style_cell_bold),
            Paragraph("Timestamp", style_cell_bold),
            Paragraph("Violation", style_cell_bold),
            Paragraph("Severity", style_cell_bold),
            Paragraph("Source", style_cell_bold),
            Paragraph("Status", style_cell_bold)
        ]
    ]

    for inc in incidents[:35]:
        sev = inc.get("severity", "MEDIUM")
        sev_color = "#b91c1c" if sev == "CRITICAL" else ("#c2410c" if sev == "HIGH" else "#b45309")
        stat = inc.get("status", "NEW")
        stat_color = "#15803d" if stat == "RESOLVED" else ("#1d4ed8" if stat == "ACKNOWLEDGED" else "#b91c1c")

        inc_table_data.append([
            Paragraph(f"<b>{inc.get('incident_id', '')}</b>", style_cell),
            Paragraph(inc.get("timestamp", "")[:19], style_cell),
            Paragraph(f"<font color='#be123c'><b>{inc.get('violation_category', '')}</b></font>", style_cell),
            Paragraph(f"<font color='{sev_color}'><b>{sev}</b></font>", style_cell),
            Paragraph(inc.get("source", "")[:16], style_cell),
            Paragraph(f"<font color='{stat_color}'><b>{stat}</b></font>", style_cell)
        ])

    if len(inc_table_data) == 1:
        inc_table_data.append([
            Paragraph("No incidents recorded matching the selected criteria.", style_cell),
            Paragraph("—", style_cell), Paragraph("—", style_cell),
            Paragraph("—", style_cell), Paragraph("—", style_cell), Paragraph("—", style_cell)
        ])

    t_incs = Table(inc_table_data, colWidths=[95, 105, 100, 70, 95, 67])
    t_incs.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0e1322")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_incs)

    # Build PDF with dynamic NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    return str(filepath)
