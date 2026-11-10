# -*- coding: utf-8 -*-
"""Build a clean, readable Word draft from the proposal content."""
import os, re, sys
sys.path.insert(0, "tools")
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from fill_proposal_template_v2 import SEC1, SEC2, SEC3, SEC4, PLAN, REFS, TITLE

OUT = "docs/proposal/开题报告-初稿-完善版.docx"
FIG = "docs/proposal/figures"
FONT = "宋体"

def set_run(r, size=12, bold=False, font=FONT):
    r.font.name = font
    r._element.rPr.rFonts.set(qn('w:eastAsia'), font)
    r.font.size = Pt(size)
    r.bold = bold

def body(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0.74)
    p.paragraph_format.line_spacing = 1.35
    p.paragraph_format.space_after = Pt(4)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    set_run(p.add_run(text), 12)

def heading(doc, text, size=16):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_run(p.add_run(text), size, True)

def subheading(doc, text, size=13):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    set_run(p.add_run(text), size, True)

def figure(doc, path, caption, width=13.0):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.add_run().add_picture(path, width=Cm(width))
    cp = doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_after = Pt(6)
    set_run(cp.add_run(caption), 10.5)

def page_number_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE')
    run._r.addnext(fld)
    # put a text run inside simple field
    r = OxmlElement('w:r'); t = OxmlElement('w:t'); t.text = '1'
    fld.append(r); r.append(t)

def add_header(section):
    p = section.header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("国防科技大学研究生学位论文开题报告"), 10.5)
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single'); bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1'); bottom.set(qn('w:color'), '000000')
    pbdr.append(bottom); pPr.append(pbdr)

def add_page_border(section):
    sectPr = section._sectPr
    pgBorders = OxmlElement('w:pgBorders')
    pgBorders.set(qn('w:offsetFrom'), 'page')
    for edge in ('top', 'left', 'bottom', 'right'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'single'); el.set(qn('w:sz'), '6')
        el.set(qn('w:space'), '24'); el.set(qn('w:color'), '000000')
        pgBorders.append(el)
    sectPr.append(pgBorders)

def main():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21.0); sec.page_height = Cm(29.7)
    sec.left_margin = Cm(2.5); sec.right_margin = Cm(2.5)
    sec.top_margin = Cm(2.4); sec.bottom_margin = Cm(2.2)
    add_header(sec); page_number_footer(sec); add_page_border(sec)
    style = doc.styles['Normal']
    style.font.name = FONT; style.font.size = Pt(12)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)

    # cover
    for _ in range(3): doc.add_paragraph()
    for txt, sz, bold in [("国防科技大学", 26, True), ("", 12, False),
                          ("博士/硕士研究生学位论文", 22, True), ("开题报告", 26, True)]:
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run(p.add_run(txt), sz, bold)
    doc.add_paragraph(); doc.add_paragraph()
    fields = [
        ("论文题目", "面向多精度统一执行的 Ozaki 模拟 GEMM 加速器关键技术研究"),
        ("姓    名", "________"), ("学    号", "________"),
        ("学科专业", "计算机科学与技术"),
        ("研究方向", "计算机体系结构 / 多精度矩阵计算"),
        ("指导教师", "________"), ("职    称", "________"),
        ("协助指导教师", "________"), ("职    称", "________"),
        ("学    院", "________"),
        ("开题时间", "2026 年 11 月    日"),
    ]
    for k, v in fields:
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run(p.add_run(f"{k}：{v}"), 14)
    doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("国防科技大学研究生院制"), 14)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(p.add_run("二〇二六年十一月"), 12)
    doc.add_page_break()

    # 说明（模板要求，简要保留）
    heading(doc, "说  明", 18)
    for txt in ["一、开题报告应按下述要求打印后装订成册：",
                "1. 使用 A4 白纸，双面打印；",
                "2. 封面中填写内容使用三号仿宋字体；",
                "3. 表中填写内容使用小四号宋体字体。",
                "二、编号由学院教学科研处（教务处）填写，由 9 位数字组成。"]:
        body(doc, txt)
    doc.add_page_break()

    # 一
    heading(doc, "一、学位论文选题的立论依据")
    for txt in SEC1:
        if re.match(r'^\d+\.\d+', txt): subheading(doc, txt)
        else: body(doc, txt)
    figure(doc, os.path.join(FIG, "fig1_peak_ratio.png"), "图 1  低精度峰值相对 FP64 的倍数（公开规格示意）")

    # 二
    heading(doc, "二、文献综述")
    for txt in SEC2:
        if re.match(r'^\d+\.\d+', txt): subheading(doc, txt)
        else: body(doc, txt)
    figure(doc, os.path.join(FIG, "fig2_ozaki_flow.png"), "图 2  Ozaki-II 分解与 CRT 重构流程")

    # 三
    heading(doc, "三、研究内容")
    for head, paras in SEC3:
        subheading(doc, head)
        for txt in paras: body(doc, txt)
        if head.startswith("3.4"):
            figure(doc, os.path.join(FIG, "fig3_oge_arch.png"), "图 3  OGE 架构：FTU + INT8 阵列 + CRT epilogue + 精度合同")
            figure(doc, os.path.join(FIG, "fig4_overhead.png"), "图 4  小/中矩阵非 GEMM 开销随 K 的变化（示意，目标 <10%）")

    # 四
    heading(doc, "四、研究条件")
    for txt in SEC4:
        if re.match(r'^\d+\.\d+', txt): subheading(doc, txt)
        else: body(doc, txt)
    figure(doc, os.path.join(FIG, "fig5_roadmap.png"), "图 5  36 个月技术路线与里程碑")

    # 五
    heading(doc, "五、学位论文工作计划")
    tbl = doc.add_table(rows=1, cols=3); tbl.style = 'Table Grid'
    hdr = ["起止日期（每阶段≤3个月）", "主要完成研究内容", "预期成果"]
    for i, h in enumerate(hdr):
        c = tbl.rows[0].cells[i]; c.text = ""
        set_run(c.paragraphs[0].add_run(h), 10.5, True)
    for dates, content, result in PLAN:
        row = tbl.add_row().cells
        for i, v in enumerate([dates, content, result]):
            row[i].text = ""
            set_run(row[i].paragraphs[0].add_run(v), 9.5)

    # 六
    heading(doc, "六、主要参考文献")
    for i, ref in enumerate(REFS, 1):
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0.74); p.paragraph_format.first_line_indent = Cm(-0.74)
        set_run(p.add_run(f"[{i}] {ref}"), 10.5)

    # 七
    heading(doc, "七、导师评语")
    body(doc, "（由导师填写）")
    doc.save(OUT)
    print("saved", OUT)

if __name__ == "__main__":
    main()
