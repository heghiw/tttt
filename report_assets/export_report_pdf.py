from __future__ import annotations

from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)
from PIL import Image as PILImage


def _md_inline_to_rl(text: str) -> str:
    safe = escape(text)

    safe = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', safe)

    safe = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', safe)

    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)

    safe = re.sub(r"(?<!\*)\*([^\s][^*]*?)\*(?!\*)", r"<i>\1</i>", safe)

    return safe


def markdown_to_flowables(markdown_text: str, *, base_dir: Path, max_width_pt: float) -> list:
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        spaceAfter=6,
    )
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18, leading=22, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, leading=18, spaceAfter=8)
    h3 = ParagraphStyle("H3", parent=styles["Heading3"], fontSize=12, leading=16, spaceAfter=6)
    code = ParagraphStyle("Code", parent=styles["Code"], fontName="Courier", fontSize=9.5, leading=12)

    flowables = []

    lines = markdown_text.splitlines()
    i = 0
    in_code = False
    code_buf: list[str] = []

    def flush_paragraph(par_lines: list[str]) -> None:
        text = " ".join([ln.strip() for ln in par_lines]).strip()
        if not text:
            return
        flowables.append(Paragraph(_md_inline_to_rl(text), normal))

    def flush_code() -> None:
        nonlocal code_buf
        if not code_buf:
            return
        flowables.append(Preformatted("\n".join(code_buf), code))
        flowables.append(Spacer(1, 4))
        code_buf = []

    paragraph_buf: list[str] = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip("\n")

        if line.strip().startswith("```"):
            if in_code:
                in_code = False
                flush_code()
            else:
                flush_paragraph(paragraph_buf)
                paragraph_buf = []
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()

        img_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped)
        if img_match:
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            alt_text = (img_match.group(1) or "").strip()
            rel_path = img_match.group(2).strip().strip('"').strip("'")
            img_path = (base_dir / rel_path).resolve()
            if img_path.exists():
                with PILImage.open(img_path) as im:
                    w_px, h_px = im.size
                img = Image(str(img_path))
                if w_px > 0 and h_px > 0:
                    aspect = h_px / float(w_px)
                    target_w = min(max_width_pt, float(w_px))
                    img.drawWidth = target_w
                    img.drawHeight = target_w * aspect
                img.hAlign = "CENTER"
                flowables.append(img)
                if alt_text:
                    caption = ParagraphStyle(
                        "Caption",
                        parent=normal,
                        fontSize=10,
                        leading=12,
                        textColor="#333333",
                        spaceBefore=4,
                        spaceAfter=8,
                    )
                    flowables.append(Paragraph(_md_inline_to_rl(alt_text), caption))
                else:
                    flowables.append(Spacer(1, 8))
            else:
                flowables.append(Paragraph(_md_inline_to_rl(stripped), normal))
            i += 1
            continue

        if not stripped:
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            i += 1
            continue

        if stripped in ("---", "***", "___"):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            flowables.append(Spacer(1, 6))
            flowables.append(HRFlowable(width="100%", thickness=1, color="#dddddd"))
            flowables.append(Spacer(1, 8))
            i += 1
            continue

        if stripped.startswith("#"):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            if level <= 1:
                flowables.append(Paragraph(_md_inline_to_rl(text), h1))
            elif level == 2:
                flowables.append(Paragraph(_md_inline_to_rl(text), h2))
            else:
                flowables.append(Paragraph(_md_inline_to_rl(text), h3))
            i += 1
            continue

        if stripped.startswith(("- ", "* ")):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            items = []
            while i < len(lines):
                s = lines[i].strip()
                if s.startswith(("- ", "* ")):
                    items.append(s[2:].strip())
                    i += 1
                    continue
                break
            flowables.append(
                ListFlowable(
                    [ListItem(Paragraph(_md_inline_to_rl(it), normal)) for it in items],
                    bulletType="bullet",
                    leftIndent=14,
                )
            )
            flowables.append(Spacer(1, 4))
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph(paragraph_buf)
            paragraph_buf = []
            items = []
            while i < len(lines):
                s = lines[i].strip()
                m = re.match(r"^(\d+)\.\s+(.*)$", s)
                if m:
                    items.append(m.group(2).strip())
                    i += 1
                    continue
                break
            flowables.append(
                ListFlowable(
                    [ListItem(Paragraph(_md_inline_to_rl(it), normal)) for it in items],
                    bulletType="1",
                    leftIndent=14,
                )
            )
            flowables.append(Spacer(1, 4))
            continue

        paragraph_buf.append(line)
        i += 1

    flush_paragraph(paragraph_buf)
    if in_code:
        flush_code()

    return flowables


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report_md = repo_root / "REPORT.md"
    out_pdf = repo_root / "REPORT.pdf"

    md_text = report_md.read_text(encoding="utf-8")
    max_width_pt = A4[0] - (16 * mm) - (16 * mm)
    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="IS-211 Mandatory Assignment Report",
    )

    story = markdown_to_flowables(md_text, base_dir=repo_root, max_width_pt=max_width_pt)
    doc.build(story)

    print(f"Wrote {out_pdf}")


if __name__ == "__main__":
    main()
