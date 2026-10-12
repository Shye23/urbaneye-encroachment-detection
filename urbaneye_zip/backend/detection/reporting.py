from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import DetectionArtifact, DetectionJob


def ensure_pdf_report(job: DetectionJob) -> DetectionArtifact:
    """Create and return the PDF report artifact for a completed job."""
    existing = job.artifacts.filter(
        kind=DetectionArtifact.Kind.REPORT,
        name__iendswith=".pdf",
    ).first()
    if existing and Path(existing.path).is_file():
        return existing

    workspace = Path(job.output_directory)
    report_dir = workspace / "outputs" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"JOB_{job.pk}_report.pdf"

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "UrbanEyeTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#8d390d"),
        spaceAfter=10,
    )
    body = styles["BodyText"]
    body.leading = 15
    story = [
        Paragraph("UrbanEye Encroachment Detection Report", title),
        Paragraph(f"<b>Job:</b> #{job.pk}", body),
        Paragraph(
            f"<b>Analysis period:</b> {job.start_date} to {job.end_date}",
            body,
        ),
        Paragraph(
            "<b>Interpretation:</b> Automated results identify areas requiring "
            "official and legal verification. They do not establish encroachment.",
            body,
        ),
        Spacer(1, 8),
    ]

    summary = job.result_summary or {}
    rows = [
        ["Metric", "Value"],
        ["Job status", job.get_status_display()],
        ["Detected change regions", str(summary.get("candidate_count", 0))],
        ["Raw changed pixels", str(summary.get("raw_changed_pixels", 0))],
        [
            "Postprocessed changed pixels",
            str(summary.get("postprocessed_changed_pixels", 0)),
        ],
    ]
    table = Table(rows, colWidths=[75 * mm, 95 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8d390d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9b8ac")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fbf6f1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    candidates = list(job.candidates.all())
    story.append(Paragraph("<b>Candidate regions</b>", styles["Heading2"]))
    if not candidates:
        story.append(Paragraph("No reportable change regions were identified.", body))
    else:
        candidate_rows = [["Candidate", "Status", "Changed area (m²)"]]
        for candidate in candidates:
            candidate_rows.append(
                [
                    candidate.candidate_id,
                    candidate.status.replace("_", " ").title(),
                    str(candidate.attributes.get("change_area_m2", "Not available")),
                ]
            )
        candidate_table = Table(candidate_rows, colWidths=[40 * mm, 70 * mm, 60 * mm])
        candidate_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8d390d")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9b8ac")),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(candidate_table)

    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "This report is generated from satellite change detection and "
            "synthetic cadastral validation data. All potential cases require "
            "manual GIS review and field verification.",
            body,
        )
    )
    SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    ).build(story)

    return DetectionArtifact.objects.create(
        job=job,
        kind=DetectionArtifact.Kind.REPORT,
        name=report_path.name,
        path=str(report_path),
    )
