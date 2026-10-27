from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "PROJECT_EXPLANATION.md"
OUTPUT = ROOT / "PROJECT_EXPLANATION.pdf"


def clean_inline(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("`", "")
    )


def flush_paragraph(lines, story, styles):
    if not lines:
        return
    text = " ".join(line.strip() for line in lines if line.strip())
    if text:
        story.append(Paragraph(clean_inline(text), styles["Body"]))
        story.append(Spacer(1, 0.08 * inch))
    lines.clear()


def build_pdf():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleMain",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=31,
            textColor=colors.HexColor("#0B1726"),
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#0D5C75"),
            spaceBefore=13,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#1F2933"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=9,
            leading=12,
            leftIndent=10,
            rightIndent=10,
            borderColor=colors.HexColor("#D8E2EA"),
            borderWidth=0.8,
            borderPadding=7,
            backColor=colors.HexColor("#F5F8FA"),
            textColor=colors.HexColor("#102A43"),
            spaceBefore=5,
            spaceAfter=9,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ShieldBullet",
            parent=styles["Body"],
            leftIndent=18,
            firstLineIndent=-10,
        )
    )

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.72 * inch,
        title="ShieldAI Project Explanation",
        author="ShieldAI",
    )

    story = []
    paragraph_lines = []
    code_lines = []
    in_code = False
    first_title = True

    for raw_line in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["CodeBlock"]))
                code_lines = []
                in_code = False
            else:
                flush_paragraph(paragraph_lines, story, styles)
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph(paragraph_lines, story, styles)
            continue

        if line.startswith("# "):
            flush_paragraph(paragraph_lines, story, styles)
            if not first_title:
                story.append(PageBreak())
            story.append(Paragraph(clean_inline(line[2:]), styles["TitleMain"]))
            first_title = False
            continue

        if line.startswith("## "):
            flush_paragraph(paragraph_lines, story, styles)
            story.append(Paragraph(clean_inline(line[3:]), styles["Heading"]))
            continue

        if line.startswith("- "):
            flush_paragraph(paragraph_lines, story, styles)
            story.append(Paragraph("- " + clean_inline(line[2:]), styles["ShieldBullet"]))
            continue

        paragraph_lines.append(line)

    flush_paragraph(paragraph_lines, story, styles)
    if code_lines:
        story.append(Preformatted("\n".join(code_lines), styles["CodeBlock"]))

    doc.build(story)


if __name__ == "__main__":
    build_pdf()
    print(OUTPUT)
