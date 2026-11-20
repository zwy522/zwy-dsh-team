# -*- coding: utf-8 -*-
"""Generate simple figures for the proposal draft."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = "docs/proposal/figures"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
os.makedirs(OUT, exist_ok=True)

def f(sz, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, sz, index=0)

def center(d, box, text, font, fill=(20, 20, 20)):
    x0, y0, x1, y1 = box
    bb = d.textbbox((0, 0), text, font=font)
    w, h = bb[2]-bb[0], bb[3]-bb[1]
    d.text((x0 + (x1-x0-w)/2, y0 + (y1-y0-h)/2 - bb[1]), text, font=font, fill=fill)

def box(d, box, text, fill=(218, 232, 245), outline=(31, 78, 121), font=None, width=3):
    d.rounded_rectangle(box, radius=12, fill=fill, outline=outline, width=width)
    center(d, box, text, font or f(24))

def arrow(d, p0, p1, color=(31, 78, 121), width=4):
    d.line([p0, p1], fill=color, width=width)
    import math
    ang = math.atan2(p1[1]-p0[1], p1[0]-p0[0])
    L = 14
    for s in (-0.5, 0.5):
        d.line([p1, (p1[0]-L*math.cos(ang+s), p1[1]-L*math.sin(ang+s))], fill=color, width=width)

def save(img, name):
    img.save(os.path.join(OUT, name))

# Fig 1: peak ratios
img = Image.new("RGB", (1200, 620), "white"); d = ImageDraw.Draw(img)
center(d, (0, 10, 1200, 55), "低精度峰值 / FP64 峰值（倍）", f(30, True))
data = [("A100\n(INT8)", 64), ("RTX 4090\n(INT8)", 512), ("B200\n(INT8)", 122), ("B300\n(INT8)", 125)]
maxv = 550
x0, y0, x1, y1 = 100, 90, 1140, 540
# axes
d.line([(x0,y1),(x1,y1)], fill=(60,60,60), width=2)
d.line([(x0,y0),(x0,y1)], fill=(60,60,60), width=2)
for i in range(0, 6):
    v = i*100
    y = y1 - (v/maxv)*(y1-y0)
    d.line([(x0,y),(x1,y)], fill=(225,225,225), width=1)
    d.text((x0-55,y-10), str(v), font=f(18), fill=(60,60,60))
bw = 150
for i,(lab,v) in enumerate(data):
    x = x0 + 80 + i*240
    h = (v/maxv)*(y1-y0)
    d.rectangle([x, y1-h, x+bw, y1], fill=(47, 117, 181))
    center(d, (x, y1-h-40, x+bw, y1-h), f"{v}×", f(22, True), (31,78,121))
    center(d, (x-20, y1+8, x+bw+20, y1+70), lab, f(18))
center(d, (0, 575, 1200, 610), "注：公开规格的数量级对比，用于说明精度碎片化趋势，不作为本课题实测。", f(16), (90,90,90))
save(img, "fig1_peak_ratio.png")

# Fig 2: Ozaki II flow
img = Image.new("RGB", (1500, 480), "white"); d = ImageDraw.Draw(img)
center(d, (0, 5, 1500, 50), "Ozaki-II 分解与 CRT 重构流程", f(28, True))
boxes = [
    ((20, 150, 260, 300), "缩放/截断\nA′ = trunc(D·A)"),
    ((310, 150, 550, 300), "取模 p_i\nA′_i = A′ mod p_i"),
    ((600, 150, 840, 300), "INT8 GEMM\nC′_i = A′_i B′_i"),
    ((890, 150, 1130, 300), "CRT 重构\nC′ = Σ C′_i·w_i"),
    ((1180, 150, 1470, 300), "反缩放/舍入\nC ≈ D⁻¹C′E⁻¹"),
]
for bx, tx in boxes:
    box(d, bx, tx, font=f(19))
for i in range(len(boxes)-1):
    p0 = (boxes[i][0][2]+6, 225); p1 = (boxes[i+1][0][0]-6, 225)
    arrow(d, p0, p1)
center(d, (0, 330, 1500, 370), "每个模数一次低精度 GEMM；模数乘积 P 决定可恢复的整数范围", f(18), (70,70,70))
save(img, "fig2_ozaki_flow.png")

# Fig 3: OGE architecture
img = Image.new("RGB", (1500, 760), "white"); d = ImageDraw.Draw(img)
center(d, (0, 5, 1500, 50), "OGE：INT8-only 统一精度 GEMM 引擎", f(28, True))
box(d, (30, 150, 250, 300), "A/B tile\n(HBM→SRAM)", fill=(235,235,235), font=f(19))
box(d, (300, 150, 560, 300), "FTU\n缩放/指数感知取模\n余数平面打包", font=f(18))
box(d, (610, 150, 870, 300), "INT8 阵列\n128×128\n逐模数 GEMM", font=f(18))
box(d, (920, 150, 1200, 300), "CRT epilogue\nmod p_i / 加权\n128-bit 累加", font=f(18))
box(d, (1250, 150, 1470, 300), "mod P / 反缩放\n正确舍入\n→ C", fill=(235,235,235), font=f(18))
for p0,p1 in [((256,225),(294,225)),((566,225),(604,225)),((876,225),(914,225)),((1206,225),(1244,225))]:
    arrow(d, p0, p1)
box(d, (300, 380, 870, 500), "片上双缓冲：余数平面 / limb 平面\nFTU(i+1) 与 GEMM(i) 重叠；CRT(t-1) 与 GEMM(t) 重叠", fill=(255,242,204), outline=(191,143,0), font=f(18))
box(d, (920, 380, 1470, 500), "精度合同 + 守卫\nEXACT / BOUNDED(ε) / FAST\nulp 统计、越界回退、N/分块选择", fill=(226,239,218), outline=(84,130,53), font=f(18))
arrow(d, (870, 440), (920, 440), color=(84,130,53))
center(d, (0, 540, 1500, 580), "FP8/FP4 仅作为 WP6 可选扩展；主线 INT8-only。", f(18), (90,90,90))
save(img, "fig3_oge_arch.png")

# Fig 4: overhead vs K
img = Image.new("RGB", (1200, 620), "white"); d = ImageDraw.Draw(img)
center(d, (0, 10, 1200, 55), "小/中矩阵的非 GEMM 开销（示意）", f(30, True))
x0,y0,x1,y1 = 110, 90, 1130, 520
d.line([(x0,y1),(x1,y1)], fill=(60,60,60), width=2); d.line([(x0,y0),(x0,y1)], fill=(60,60,60), width=2)
ks = [1024, 2048, 4096, 8192, 16384]
vals = [55, 38, 22, 12, 8]
def px(i): return x0 + i*(x1-x0)/(len(ks)-1)
def py(v): return y1 - v/60*(y1-y0)
for v in range(0,61,10):
    y=py(v); d.line([(x0,y),(x1,y)], fill=(225,225,225), width=1); d.text((x0-45,y-10), f"{v}%", font=f(17), fill=(60,60,60))
for i,k in enumerate(ks):
    center(d, (px(i)-50, y1+8, px(i)+50, y1+40), str(k), f(17))
pts=[(px(i),py(v)) for i,v in enumerate(vals)]
d.line(pts, fill=(192,0,0), width=5)
for p,v in zip(pts,vals):
    d.ellipse([p[0]-7,p[1]-7,p[0]+7,p[1]+7], fill=(192,0,0)); d.text((p[0]+10,p[1]-30), f"{v}%", font=f(17), fill=(192,0,0))
d.line([(x0,py(10)),(x1,py(10))], fill=(84,130,53), width=3)
d.text((x1-150, py(10)-28), "目标 <10%", font=f(18, True), fill=(84,130,53))
center(d, (0, 555, 1200, 590), "K 增大时非 GEMM 开销被摊薄；困难区间在 K=1024–4096。", f(17), (90,90,90))
save(img, "fig4_overhead.png")

# Fig 5: roadmap
img = Image.new("RGB", (1500, 700), "white"); d = ImageDraw.Draw(img)
center(d, (0, 5, 1500, 50), "36 个月技术路线与里程碑", f(28, True))
left, top, qw, rh = 240, 110, 95, 62
labels = ["WP1 模型/算法规则", "WP2 微架构/模拟器", "WP3 精度合同/守卫", "WP4 RTL", "WP5 系统/应用", "WP6 可选扩展"]
starts = [0, 2, 3, 4, 7, 9]; spans = [3, 4, 4, 4, 4, 3]
for i,lab in enumerate(labels):
    d.text((20, top+i*rh+18), lab, font=f(17), fill=(20,20,20))
    x = left + starts[i]*qw; w = spans[i]*qw
    d.rounded_rectangle([x, top+i*rh+6, x+w-6, top+i*rh+rh-6], radius=8, fill=(218,232,245), outline=(31,78,121), width=2)
for q in range(13):
    x=left+q*qw
    d.line([(x,top-10),(x,top+6*rh+10)], fill=(220,220,220), width=1)
    if q<12:
        d.text((x+qw/2-25, top-45), f"Q{q+1}", font=f(15), fill=(60,60,60))
ms=[("M0",0),("M1",2),("M2",4),("M3",6),("M4",8),("M5",10),("M6",12)]
for name,q in ms:
    x=left+q*qw
    d.ellipse([x-8, top+6*rh+20, x+8, top+6*rh+36], fill=(192,0,0))
    d.text((x-14, top+6*rh+40), name, font=f(15, True), fill=(192,0,0))
center(d, (0, 650, 1500, 685), "M1：a64/a32 与 Go/No-Go；M4：RTL/综合/投稿；M5：Chipyard/FireSim/U250。", f(16), (90,90,90))
save(img, "fig5_roadmap.png")
print("figures saved")
