# -*- coding: utf-8 -*-
"""Build a readable DOCX/PDF from docs/reports/OzCore-复现报告.md."""
import os, re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = "docs/reports/OzCore-复现报告.md"
OUT = "docs/reports/OzCore-复现报告.docx"
BASE = "docs/reports"
FONT = "宋体"
HEAD = "黑体"

def set_run(r, size=11.5, bold=False, font=FONT):
    r.font.name = font
    r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), font)
    r.font.size = Pt(size); r.bold = bold

def rich(p, text, size=11.5, bold=False):
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    for part in re.split(r'(\*\*[^*]+\*\*|`[^`]+`)', text):
        if not part: continue
        if part.startswith('**') and part.endswith('**'):
            set_run(p.add_run(part[2:-2]), size, True)
        elif part.startswith('`') and part.endswith('`'):
            set_run(p.add_run(part[1:-1]), size-0.5, bold, "Consolas")
        else:
            set_run(p.add_run(part), size, bold)

def body(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.4
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.first_line_indent = Cm(0.74)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    rich(p, text, 11.5)

def heading(doc, text, level=1, pb=False):
    if pb: doc.add_page_break()
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12 if level == 1 else 8)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    set_run(p.add_run(text), {1: 16, 2: 13.5, 3: 12}.get(level, 12), True, HEAD)

def bullets(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(2)
    rich(p, text, 11.5)

def add_table(doc, rows):
    cells = []
    for r in rows:
        r = r.strip()
        if r.startswith('|'): r = r[1:]
        if r.endswith('|'): r = r[:-1]
        cells.append([c.strip() for c in r.split('|')])
    cells = [row for row in cells if not all(re.fullmatch(r':?-{2,}:?', c.replace(' ', '')) for c in row if c)]
    if not cells: return
    ncol = max(len(r) for r in cells)
    t = doc.add_table(rows=len(cells), cols=ncol)
    t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False; t.allow_autofit = False
    for i, row in enumerate(cells):
        for j in range(ncol):
            c = t.cell(i, j); c.text = ''
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            rich(p, row[j] if j < len(row) else '', 9.5, bold=(i == 0))
    for j in range(ncol):
        tcPr = t.cell(0, j)._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), 'E8EEF7'); tcPr.append(shd)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_figure(doc, path, caption):
    if not os.path.exists(path):
        print("missing", path); return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(path, width=Cm(15.2))
    cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(6)
    set_run(cp.add_run(caption), 10, False)

def code_block(doc, lines):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.4); p.paragraph_format.line_spacing = 1.05
    p.paragraph_format.space_after = Pt(4)
    for i, line in enumerate(lines):
        r = p.add_run(line + ("\n" if i < len(lines)-1 else ""))
        set_run(r, 8.5, False, "Consolas")

def cover(doc):
    for _ in range(4): doc.add_paragraph()
    for line, sz in [("OzCore（MICRO 2026）", 22), ("Artifact 复现报告", 22)]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        set_run(p.add_run(line), sz, True, HEAD)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("CPU-only artifact 复现 + TSMC 28 nm 替代综合"), 14, False)
    doc.add_paragraph(); doc.add_paragraph()
    for k, v in [("版本", "v1.0"), ("日期", "2026-11-26"),
                 ("范围", "Category A（CPU redraw）+ Ten-four INT8 TSMC 28 nm 替代综合")]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run(p.add_run(f"{k}：{v}"), 11.5)
    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("本报告不含 NDA/私有数据；面积数字均标注来源与工艺口径。"), 10, False)
    doc.add_page_break()

def main():
    lines = [l.rstrip('\n') for l in open(SRC, encoding='utf-8')]
    doc = Document()
    s = doc.sections[0]
    s.page_width = Cm(21.0); s.page_height = Cm(29.7)
    s.left_margin = Cm(2.5); s.right_margin = Cm(2.5)
    s.top_margin = Cm(2.4); s.bottom_margin = Cm(2.2)
    style = doc.styles['Normal']; style.font.name = FONT; style.font.size = Pt(11.5)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    cover(doc)
    i = 0; first_h2 = True
    while i < len(lines):
        line = lines[i]; s = line.strip()
        if not s: i += 1; continue
        if s.startswith('# '): i += 1; continue
        m = re.match(r'^(#{2,4})\s+(.*)$', s)
        if m:
            level = len(m.group(1)) - 1
            text = m.group(2).strip()
            pb = level == 1 and not first_h2
            first_h2 = False
            heading(doc, text, level, pb=pb)
            i += 1; continue
        if s.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip()); i += 1
            add_table(doc, rows); continue
        m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', s)
        if m:
            path = os.path.normpath(os.path.join(BASE, m.group(2)))
            add_figure(doc, path, m.group(1)); i += 1; continue
        if s.startswith('```'):
            code = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code.append(lines[i].rstrip()); i += 1
            i += 1
            code_block(doc, code); continue
        if s.startswith('- '): bullets(doc, s[2:].strip()); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.*)$', s)
        if m:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.35; p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.left_indent = Cm(0.4); p.paragraph_format.first_line_indent = Cm(0.4)
            rich(p, f"{m.group(1)}. {m.group(2)}", 11.5); i += 1; continue
        if s in ('---','***'): i += 1; continue
        body(doc, s); i += 1
    # page numbers
    fp = doc.sections[0].footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE')
    r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = '1'; r.append(t); fld.append(r)
    run._r.addnext(fld)
    doc.save(OUT)
    print("wrote", OUT)

if __name__ == '__main__':
    main()
