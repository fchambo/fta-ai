"""Word documents: build .docx from simple markdown, read .docx/.xlsx text, convert to PDF."""
import os
import re
import shutil
import subprocess

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))")


def _hex(color):
    color = color.lstrip("#")
    return RGBColor(int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16))


def _add_inline(paragraph, text):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("[") and "](" in part:
            label, url = part[1:-1].split("](", 1)
            paragraph.add_run(label if label == url else f"{label} ({url})")
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            paragraph.add_run(part[1:-1]).italic = True
        else:
            paragraph.add_run(part)


def _shade(cell, color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color.lstrip("#"))
    tc_pr.append(shd)


def _add_table(doc, lines, color):
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r if c)]
    width = max(len(r) for r in rows)
    table = doc.add_table(rows=0, cols=width)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, values in enumerate(rows):
        cells = table.add_row().cells
        for j in range(width):
            p = cells[j].paragraphs[0]
            _add_inline(p, values[j] if j < len(values) else "")
            if i == 0:
                for run in p.runs:
                    run.bold = True
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                _shade(cells[j], color)
    doc.add_paragraph()


def markdown_to_docx(md_text, out_path, title=None, footer=None, color="0F766E"):
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(11)
    for level in (1, 2, 3):
        style = doc.styles[f"Heading {level}"]
        style.font.color.rgb = _hex(color)
        style.font.name = "Calibri"
    if title:
        doc.core_properties.title = title
    if footer:
        fp = doc.sections[0].footer.paragraphs[0]
        fp.text = footer
        fp.runs[0].font.size = Pt(8)

    lines, i = md_text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            i += 1
            continue
        if stripped.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            _add_table(doc, block, color)
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if heading:
            level = len(heading.group(1))
            doc.add_heading(heading.group(2).strip(), level=0 if level == 1 and i == 0 else min(level, 3))
        elif re.match(r"^-{3,}$", stripped):
            doc.add_paragraph("─" * 40)
        elif re.match(r"^[-*]\s+\[( |x)\]\s+", stripped):
            checked = stripped[3] == "x"
            p = doc.add_paragraph(style="List Bullet")
            _add_inline(p, ("☑ " if checked else "☐ ") + re.sub(r"^[-*]\s+\[( |x)\]\s+", "", stripped))
        elif re.match(r"^[-*•]\s+", stripped):
            indent = len(line) - len(line.lstrip())
            p = doc.add_paragraph(style="List Bullet 2" if indent >= 2 else "List Bullet")
            _add_inline(p, re.sub(r"^[-*•]\s+", "", stripped))
        elif re.match(r"^\d+[.)]\s+", stripped):
            p = doc.add_paragraph(style="List Number")
            _add_inline(p, re.sub(r"^\d+[.)]\s+", "", stripped))
        elif stripped.startswith(">"):
            p = doc.add_paragraph(style="Intense Quote")
            _add_inline(p, stripped.lstrip("> "))
        else:
            p = doc.add_paragraph()
            _add_inline(p, stripped)
        i += 1
    doc.save(out_path)


def _cell_text(value):
    from datetime import datetime
    if value is None:
        return ""
    if isinstance(value, datetime) and not (value.hour or value.minute):
        return value.date().isoformat()
    return str(value)


def read_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        doc = Document(path)
        out = [p.text for p in doc.paragraphs if p.text.strip()]
        for t in doc.tables:
            for row in t.rows:
                out.append(" | ".join(c.text.strip() for c in row.cells))
        return "\n".join(out)
    if ext in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=True, read_only=True)
        out = []
        for ws in wb.worksheets:
            out.append(f"## Sheet: {ws.title}")
            for row in ws.iter_rows(values_only=True):
                if any(v not in (None, "") for v in row):
                    out.append("\t".join(_cell_text(v) for v in row))
        return "\n".join(out)
    if ext == ".pdf":
        raise ValueError("Read PDFs with Claude's Read tool directly.")
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _pdf_font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("Body", path))
                return "Body"
            except Exception:
                continue
    return "Helvetica"


# PDF fonts have no color emoji: draw status markers as colored glyphs instead.
PDF_EMOJI = {"✅": ("✔", "#15803D"), "🔴": ("●", "#DC2626"), "🟡": ("●", "#CA8A04"),
             "🟢": ("●", "#15803D"), "⚪": ("○", "#6B7280"), "⚠️": ("!", "#CA8A04"), "⚠": ("!", "#CA8A04")}


def _pdf_inline(text):
    from xml.sax.saxutils import escape
    out = []
    for emoji in PDF_EMOJI:
        text = text.replace(emoji, f"\x00{emoji}\x00")
    if "\x00" in text:
        pieces = text.split("\x00")
        return "".join(f'<font color="{PDF_EMOJI[p][1]}">{PDF_EMOJI[p][0]}</font>' if p in PDF_EMOJI
                       else _pdf_inline(p) for p in pieces)
    for part in INLINE.split(text):
        if part.startswith("**") and part.endswith("**"):
            out.append(f"<b>{escape(part[2:-2])}</b>")
        elif part.startswith("[") and "](" in part:
            label, url = part[1:-1].split("](", 1)
            out.append(f'<link href="{escape(url)}" color="blue">{escape(label)}</link>')
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(f"<i>{escape(part[1:-1])}</i>")
        else:
            out.append(escape(part))
    return "".join(out)


def markdown_to_pdf(md_text, out_path, title=None, footer=None, color="0F766E"):
    """Render the same markdown subset straight to PDF: no Word or LibreOffice needed."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font, accent = _pdf_font(), colors.HexColor("#" + color.lstrip("#"))
    base = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=base["BodyText"], fontName=font, fontSize=10.5, leading=14)
    heads = {lvl: ParagraphStyle(f"h{lvl}", parent=body, fontSize=size, leading=size + 4, textColor=accent,
                                 spaceBefore=10, spaceAfter=6)
             for lvl, size in ((0, 20), (1, 16), (2, 13), (3, 11.5))}
    for st in heads.values():
        st.fontName = font
    quote = ParagraphStyle("quote", parent=body, leftIndent=12, textColor=colors.HexColor("#444444"))

    story, bullets, lines, i = [], [], md_text.splitlines(), 0

    def flush():
        if bullets:
            story.append(ListFlowable([ListItem(b, leftIndent=12) for b in bullets], bulletType="bullet",
                                      bulletFontName=font, start="•", leftIndent=12))
            bullets.clear()

    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped or stripped.startswith("<!--"):
            flush(); i += 1; continue
        if stripped.startswith("|"):
            flush()
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            block = [r for r in block if not all(re.fullmatch(r":?-{2,}:?", c) for c in r if c)]
            width = max(len(r) for r in block)
            th = ParagraphStyle("th", parent=body, textColor=colors.white)
            data = [[Paragraph(_pdf_inline(r[j] if j < len(r) else ""), th if n == 0 else body) for j in range(width)]
                    for n, r in enumerate(block)]
            table = Table(data, repeatRows=1, hAlign="LEFT", colWidths=[(A4[0] - 4 * cm) / width] * width)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), accent), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#BBBBBB")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story += [table, Spacer(1, 8)]
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)", stripped)
        checkbox = re.match(r"^[-*]\s+\[( |x)\]\s+(.*)", stripped)
        bullet = re.match(r"^(?:[-*•]|\d+[.)])\s+(.*)", stripped)
        if heading:
            flush()
            level = len(heading.group(1))
            story.append(Paragraph(_pdf_inline(heading.group(2)), heads[0 if level == 1 and not story else min(level, 3)]))
        elif checkbox:
            bullets.append(Paragraph(("☑ " if checkbox.group(1) == "x" else "☐ ") + _pdf_inline(checkbox.group(2)), body))
        elif bullet:
            bullets.append(Paragraph(_pdf_inline(bullet.group(1)), body))
        elif stripped.startswith(">"):
            flush(); story.append(Paragraph(_pdf_inline(stripped.lstrip("> ")), quote))
        elif re.match(r"^-{3,}$", stripped):
            flush(); story.append(Spacer(1, 10))
        else:
            flush(); story.append(Paragraph(_pdf_inline(stripped), body))
        i += 1
    flush()

    def decorate(canvas, doc):
        if footer:
            canvas.setFont(font, 8)
            canvas.setFillColor(colors.HexColor("#666666"))
            canvas.drawString(2 * cm, 1.2 * cm, footer)
            canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(doc.page))

    SimpleDocTemplate(out_path, pagesize=A4, title=title or "", leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=2 * cm, bottomMargin=2 * cm).build(story, onFirstPage=decorate, onLaterPages=decorate)


def to_pdf(docx_path):
    """Convert an existing .docx (e.g. one the agent edited) with LibreOffice when installed."""
    docx_path = os.path.abspath(docx_path)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice and os.path.exists("/Applications/LibreOffice.app"):
        soffice = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if not soffice:
        raise RuntimeError("LibreOffice is not installed: open the .docx in Word and use File > Save as PDF, "
                           "or regenerate the PDF from the markdown with 'docx --pdf'.")
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", os.path.dirname(docx_path), docx_path],
                   check=True, capture_output=True, timeout=120)
    return os.path.splitext(docx_path)[0] + ".pdf"
