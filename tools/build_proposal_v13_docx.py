# -*- coding: utf-8 -*-
"""Build a readable DOCX from the v1.3 proposal markdown (tables, figures, headings)."""
import os, re, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = "docs/proposal/开题报告-Ozaki-OGE-v1.3.md"
OUT = "docs/proposal/开题报告-Ozaki-OGE-v1.3.docx"
FIGDIR = "docs/proposal"
FONT = "宋体"
HEADFONT = "黑体"

def set_run(r, size=12, bold=False, font=FONT, color=None):
    r.font.name = font
    r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), font)
    r.font.size = Pt(size)
    r.bold = bold
    if color: r.font.color.rgb = RGBColor(*color)

def add_rich(p, text, size=12, bold=False, font=FONT):
    # strip links to text, keep bold/code segments
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    parts = re.split(r'(\*\*[^*]+\*\*|`[^`]+`)', text)
    for part in parts:
        if not part: continue
        if part.startswith('**') and part.endswith('**'):
            set_run(p.add_run(part[2:-2]), size, True, font)
        elif part.startswith('`') and part.endswith('`'):
            set_run(p.add_run(part[1:-1]), size-0.5, bold, "Consolas")
        else:
            set_run(p.add_run(part), size, bold, font)

def body(doc, text, indent=True):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.line_spacing = 1.35
    pf.space_after = Pt(4)
    if indent: pf.first_line_indent = Cm(0.74)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    add_rich(p, text, 12)

def heading(doc, text, level=1, page_break=False):
    if page_break:
        doc.add_page_break()
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(10 if level > 1 else 14)
    pf.space_after = Pt(6)
    pf.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    size = {1: 16, 2: 13.5, 3: 12, 4: 12}.get(level, 12)
    set_run(p.add_run(text), size, True, HEADFONT)

def bullet(doc, text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(2)
    add_rich(p, text, 12)

def quote(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(4)
    set_run(p.add_run(text), 11, False, FONT, (90, 90, 90))

def add_table(doc, rows):
    # parse rows, then drop markdown separator rows (|---|)
    cells = []
    for r in rows:
        r = r.strip()
        if r.startswith('|'): r = r[1:]
        if r.endswith('|'): r = r[:-1]
        cells.append([c.strip() for c in r.split('|')])
    cells = [row for row in cells if not all(re.fullmatch(r':?-{2,}:?', c.replace(' ', '')) for c in row if c)]
    if not cells: return
    ncol = max(len(r) for r in cells)
    table = doc.add_table(rows=len(cells), cols=ncol)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    for i, row in enumerate(cells):
        for j in range(ncol):
            cell = table.cell(i, j)
            cell.text = ''
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
            txt = row[j] if j < len(row) else ''
            add_rich(p, txt, 9, bold=(i == 0))
    # small header shading
    for j in range(ncol):
        tcPr = table.cell(0, j)._tc.get_or_add_tcPr()
        shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), 'E8EEF7')
        tcPr.append(shd)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def add_figure(doc, path, caption):
    if not os.path.exists(path):
        print("missing figure", path); return
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(path, width=Cm(15.5))
    cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(6)
    set_run(cp.add_run(caption), 10.5, False, FONT)

def header_footer(sec):
    p = sec.header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("国防科技大学研究生学位论文开题报告"), 9.5, False, FONT, (110,110,110))
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run()
    fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE')
    r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = '1'; r.append(t); fld.append(r)
    run._r.addnext(fld)

def cover(doc):
    for _ in range(3): doc.add_paragraph()
    for txt, sz, bold in [("国防科技大学", 26, True), ("", 12, False),
                          ("博士/硕士研究生学位论文", 20, True), ("开题报告", 26, True)]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run(p.add_run(txt), sz, bold, HEADFONT)
    doc.add_paragraph(); doc.add_paragraph()
    fields = [
        ("论文题目", "面向多格式 AI 计算的可重构—Ozaki 双模加速器关键技术研究"),
        ("姓名", "________"), ("学号", "________"),
        ("学科专业", "计算机科学与技术"),
        ("研究方向", "计算机体系结构 / 多格式矩阵计算"),
        ("指导教师", "________"), ("职称", "________"),
        ("协助指导教师", "________"), ("职称", "________"),
        ("学院", "________"),
        ("开题时间", "2026 年 11 月"),
    ]
    for k, v in fields:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(6)
        set_run(p.add_run(f"{k}：{v}"), 13, False, FONT)
    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("国防科技大学研究生院制"), 13, False, FONT)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("二〇二六年十一月"), 12, False, FONT)
    doc.add_section(WD_SECTION.NEW_PAGE)

def main():
    lines = [l.rstrip('\n') for l in open(SRC, encoding='utf-8')]
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0); sec.page_height = Cm(29.7)
    sec.left_margin = Cm(2.5); sec.right_margin = Cm(2.5)
    sec.top_margin = Cm(2.4); sec.bottom_margin = Cm(2.2)
    header_footer(sec)
    style = doc.styles['Normal']
    style.font.name = FONT; style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    cover(doc)
    heading(doc, "博士学位论文开题报告（v1.3）", level=2)

    i = 0
    first_h1 = True
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1; continue
        if s.startswith('# '):
            i += 1; continue
        m = re.match(r'^(#{2,4})\s+(.*)$', s)
        if m:
            level = len(m.group(1)) - 1
            text = m.group(2).strip()
            pb = level == 1 and (text.startswith('第 ') or text in ('摘要','参考文献','附录 A 前期数据与复现'))
            heading(doc, text, level, page_break=pb)
            i += 1; continue
        if s.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i].strip()); i += 1
            add_table(doc, rows); continue
        img = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', s)
        if img:
            cap, path = img.group(1), img.group(2)
            add_figure(doc, os.path.join(FIGDIR, path), cap)
            i += 1; continue
        if s in ('---','***'):
            i += 1; continue
        if s.startswith('> '):
            quote(doc, s[2:].strip()); i += 1; continue
        if s.startswith('- '):
            bullet(doc, s[2:].strip()); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.*)$', s)
        if m:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.3
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Cm(0.4)
            p.paragraph_format.first_line_indent = Cm(0.4)
            add_rich(p, f"{m.group(1)}. {m.group(2)}", 12)
            i += 1; continue
        body(doc, s)
        i += 1
    doc.save(OUT)
    print("wrote", OUT)

if __name__ == '__main__':
    main()
