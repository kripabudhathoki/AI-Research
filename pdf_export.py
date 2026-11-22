"""Create a PDF copy of the research brief (needs fpdf2)."""
from fpdf import FPDF

from workflow import RunState


def _t(text: str) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


def make_pdf(state: RunState) -> bytes:
    b = state.final_brief
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_fill_color(79, 70, 229)
    pdf.rect(0, 0, 210, 34, "F")
    pdf.set_xy(15, 8)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 9, "Research Brief", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _t(b.topic), new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(15, 40)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.multi_cell(0, 5, _t(f"Data source: {b.data_source} | Date: {state.run_date} | "
                            f"Revisions used: {state.revisions_used} of 1"),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    def heading(text):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(79, 70, 229)
        pdf.cell(0, 8, _t(text), new_x="LMARGIN", new_y="NEXT")

    def para(text, bullet=False):
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5.5, _t(("- " if bullet else "") + text), new_x="LMARGIN", new_y="NEXT")

    heading("Summary")
    para(b.summary)
    pdf.ln(2)
    heading("Competitors (up to 2)")
    for c in b.competitors or ["None identified"]:
        para(c, bullet=True)
    pdf.ln(2)
    heading("Key observations")
    for i, o in enumerate(b.observations or ["None available"], 1):
        para(f"{i}. {o}")
    pdf.ln(2)
    heading("Sources and missing information")
    para("Sources:")
    for s in b.sources or ["None"]:
        para(s, bullet=True)
    para("Missing information:")
    for m in b.missing:
        para(m, bullet=True)
    return bytes(pdf.output())
