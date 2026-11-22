"""Export research brief to PDF format.

Uses ReportLab when installed for styled typography; falls back to a clean
built-in pure-Python PDF generator if ReportLab is not available.
"""

import io
from typing import Any, List


def _pure_python_pdf(title: str, subtitle: str, sections: List[tuple]) -> bytes:
    """Generate a standard PDF 1.4 document using pure Python without external dependencies."""
    lines: List[str] = [
        f"RESEARCH BRIEF: {title.upper()}",
        f"Data Source: {subtitle}",
        "--------------------------------------------------------------------------------",
        "",
    ]

    for sec_title, items in sections:
        lines.append(f"[{sec_title.upper()}]")
        if isinstance(items, str):
            # Wrap simple paragraphs
            words = items.split()
            cur = ""
            for w in words:
                if len(cur) + len(w) + 1 > 75:
                    lines.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            if cur:
                lines.append(cur)
        elif isinstance(items, list):
            for it in items:
                # Wrap list items
                words = str(it).split()
                cur = "  * "
                for w in words:
                    if len(cur) + len(w) + 1 > 75:
                        lines.append(cur)
                        cur = "    " + w
                    else:
                        cur = f"{cur} {w}".strip() if cur == "  * " else f"{cur} {w}"
                if cur:
                    lines.append(cur)
        lines.append("")

    # Build PDF page text stream
    stream_content = "BT /F1 10 Tf 45 745 Td 13 TL\n"
    for line in lines[:55]:  # Fits on standard single page
        clean = (
            line.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .encode("latin1", "replace")
            .decode("latin1")
        )
        stream_content += f"({clean}) ' \n"
    stream_content += "ET"
    stream_bytes = stream_content.encode("latin1")

    obj1 = b"1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
    obj2 = b"2 0 obj\n<</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n"
    obj3 = b"3 0 obj\n<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources <</Font <</F1 4 0 R>>>> /Contents 5 0 R>>\nendobj\n"
    obj4 = b"4 0 obj\n<</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>\nendobj\n"
    obj5 = (
        f"5 0 obj\n<</Length {len(stream_bytes)}>>\nstream\n".encode("latin1")
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )

    header = b"%PDF-1.4\n"
    offsets = [0]
    body = b""
    for obj in [obj1, obj2, obj3, obj4, obj5]:
        offsets.append(len(header) + len(body))
        body += obj

    xref_pos = len(header) + len(body)
    xref = f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("latin1")
    for o in offsets[1:]:
        xref += f"{o:010d} 00000 n \n".encode("latin1")
    trailer = f"trailer\n<</Size {len(offsets)} /Root 1 0 R>>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin1")
    return header + body + xref + trailer


def brief_to_pdf(state: Any) -> bytes:
    """Convert a research brief RunState object into PDF bytes."""
    topic = getattr(state.plan, "topic", "Market Research")
    label = getattr(state.findings, "label", "Research Findings")
    final = state.final

    summary_text = getattr(final, "summary", "")
    competitors = getattr(final, "competitors", [])
    observations = getattr(final, "key_observations", [])
    sources_missing = getattr(final, "sources_and_missing", [])

    comp_lines = [f"{c.name}: {c.description}" for c in competitors] if competitors else ["No competitors identified."]

    sections = [
        ("Summary", summary_text),
        ("Competitors (up to 2)", comp_lines),
        ("Key Observations", observations),
        ("Sources & Missing Information", sources_missing),
    ]

    # Try ReportLab first if installed
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#312e81"),
            spaceAfter=4,
        )
        sub_style = ParagraphStyle(
            "DocSub",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=10,
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#4338ca"),
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=5,
        )
        bullet_style = ParagraphStyle(
            "Bullet",
            parent=body_style,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        )

        elements = [
            Paragraph(f"Research Brief: {topic}", title_style),
            Paragraph(f"Data source: {label}", sub_style),
            HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb"), spaceAfter=8),
        ]

        # Summary
        elements.append(Paragraph("Summary", h2_style))
        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 4))

        # Competitors
        elements.append(Paragraph("Competitors (up to 2)", h2_style))
        for c in comp_lines:
            elements.append(Paragraph(f"• {c}", bullet_style))
        elements.append(Spacer(1, 4))

        # Observations
        elements.append(Paragraph("Key Observations", h2_style))
        for o in observations:
            elements.append(Paragraph(f"• {o}", bullet_style))
        elements.append(Spacer(1, 4))

        # Sources & Missing
        elements.append(Paragraph("Sources & Missing Information", h2_style))
        for sm in sources_missing:
            elements.append(Paragraph(f"• {sm}", bullet_style))

        doc.build(elements)
        return buf.getvalue()
    except Exception:
        # Fall back gracefully to pure Python PDF generator
        return _pure_python_pdf(topic, label, sections)
