# -*- coding: utf-8 -*-
"""Readable architecture/composition figures for proposal v1.3."""
import os, math
from PIL import Image, ImageDraw, ImageFont
OUT="docs/proposal/figures"
FONT="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BOLD="/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
def f(sz,b=False): return ImageFont.truetype(BOLD if b else FONT,sz,index=0)
def center(d,b,t,fo,fill=(20,20,20)):
    x0,y0,x1,y1=b; bb=d.textbbox((0,0),t,font=fo); w,h=bb[2]-bb[0],bb[3]-bb[1]
    d.text((x0+(x1-x0-w)/2,y0+(y1-y0-h)/2-bb[1]),t,font=fo,fill=fill)
def box(d,b,t="",fo=None,fill=(218,232,245),outline=(31,78,121),w=2):
    d.rounded_rectangle(b,radius=8,fill=fill,outline=outline,width=w)
    if t: center(d,b,t,fo or f(18))
def arrow(d,p0,p1,c=(31,78,121),w=3):
    d.line([p0,p1],fill=c,width=w); a=math.atan2(p1[1]-p0[1],p1[0]-p0[0]); L=10
    for s in (-0.5,0.5): d.line([p1,(p1[0]-L*math.cos(a+s),p1[1]-L*math.sin(a+s))],fill=c,width=w)

# Fig3
W,H=1300,780; img=Image.new("RGB",(W,H),"white"); d=ImageDraw.Draw(img)
center(d,(0,10,W,50),"ODA：可重构—Ozaki 双模加速器",f(26,True))
# left
for i,(txt,fc,oc) in enumerate([
    ("格式解析\n精度/形状",(218,232,245),(31,78,121)),
    ("模式选择\nO / R",(255,242,204),(191,143,0)),
    ("SRAM/NoC\n双缓冲",(218,232,245),(31,78,121)),
    ("编译器/运行时\n组合+合同",(226,239,218),(84,130,53))]):
    y=120+i*120; box(d,(25,y,235,y+90),txt,f(18),fill=fc,outline=oc)
# fabric
d.rounded_rectangle([270,115,870,665],radius=12,fill=(248,250,252),outline=(31,78,121),width=3)
d.text((285,128),"128×128 = 64 × 16×16 tile",font=f(19,True),fill=(20,45,80))
colors={"i":(189,215,238),"f4":(244,177,131),"f8":(197,224,180),"id":(230,230,230)}
outl={"i":(31,78,121),"f4":(191,80,20),"f8":(84,130,53),"id":(165,165,165)}
x0,y0,tw,th,g=295,170,64,42,6
for r in range(8):
    for c in range(8):
        t="i" if r<4 and c<5 else ("f8" if r>=5 and c>=5 else ("id" if (r+c)%3==0 else "f4"))
        x=x0+c*(tw+g); y=y0+r*(th+g)
        d.rounded_rectangle([x,y,x+tw,y+th],radius=4,fill=colors[t],outline=outl[t],width=2)
d.rectangle([x0-4,y0-4,x0+2*(tw+g)-g+4,y0+2*(th+g)-g+4],outline=(192,0,0),width=4)
d.text((x0+4,y0+4),"A",font=f(20,True),fill=(192,0,0))
d.rectangle([x0+5*(tw+g)-4,y0-4,x0+6*(tw+g)-g+4,y0+th+4],outline=(191,80,20),width=4)
d.text((x0+5*(tw+g)+3,y0+3),"B",font=f(18,True),fill=(191,80,20))
d.text((300,620),"A 2×2 INT8 / O-mode     B 1×1 FP4 / R-mode",font=f(16),fill=(60,60,60))
# right
d.rounded_rectangle([900,115,1275,375],radius=10,fill=(218,232,245),outline=(31,78,121),width=2)
d.text((915,128),"O-mode：目标 >8 bit",font=f(21,True),fill=(20,45,80))
d.text((915,168),"FP16 / BF16 / FP32 / FP64",font=f(17),fill=(40,70,110))
d.text((915,205),"缩放/取模 → INT8 GEMM",font=f(18),fill=(25,25,25))
d.text((915,240),"→ CRT/舍入 → 精度合同",font=f(18),fill=(25,25,25))
d.text((915,288),"同一 INT8 tile，按 s 次余数",font=f(16),fill=(50,50,50))
d.text((915,318),"GEMM 模拟高精度。",font=f(16),fill=(50,50,50))
d.rounded_rectangle([900,400,1275,660],radius=10,fill=(252,235,215),outline=(191,80,20),width=2)
d.text((915,413),"R-mode：目标 ≤8 bit",font=f(21,True),fill=(100,40,10))
d.text((915,453),"INT8/FP8/FP6/FP4/INT4",font=f(17),fill=(130,55,15))
d.text((915,490),"格式前端 → BSP MAC",font=f(18),fill=(25,25,25))
d.text((915,525),"→ 原生累加 → 格式舍入",font=f(18),fill=(25,25,25))
d.text((915,573),"4×4 切片物理组合；无格式",font=f(16),fill=(50,50,50))
d.text((915,603),"转换、无多 pass 模拟。",font=f(16),fill=(50,50,50))
for y in (165,285,405,525): arrow(d,(240,y),(267,y))
arrow(d,(875,245),(897,245)); arrow(d,(875,530),(897,530),c=(191,80,20))
center(d,(0,690,W,720),"O-mode 模拟高精度；R-mode 原生执行低精度；共享 SRAM/NoC、CRT 与调度。",f(16),(60,60,60))
img.save(os.path.join(OUT,"fig3_oda_arch.png"))

# Fig4
W,H=1200,650; img=Image.new("RGB",(W,H),"white"); d=ImageDraw.Draw(img)
center(d,(0,10,W,50),"子阵列组合：适配格式与 GEMM 形状",f(25,True))
x0,y0,tw,th,g=45,120,62,42,7
colors={"i":(189,215,238),"f4":(244,177,131),"f8":(197,224,180),"id":(232,232,232)}
outl={"i":(31,78,121),"f4":(191,80,20),"f8":(84,130,53),"id":(160,160,160)}
for r in range(7):
    for c in range(7):
        t="i" if c<3 and r<3 else ("f8" if c>=4 and r<2 else ("f4" if c>=4 and r>=3 else "id"))
        x=x0+c*(tw+g); y=y0+r*(th+g)
        d.rounded_rectangle([x,y,x+tw,y+th],radius=5,fill=colors[t],outline=outl[t],width=2)
d.rectangle([x0-5,y0-5,x0+2*(tw+g)-g+5,y0+2*(th+g)-g+5],outline=(192,0,0),width=4)
d.text((x0+4,y0+4),"A",font=f(22,True),fill=(192,0,0))
d.rectangle([x0+3*(tw+g)-5,y0-5,x0+4*(tw+g)-g+5,y0+th+5],outline=(191,80,20),width=4)
d.text((x0+3*(tw+g)+3,y0+3),"B",font=f(22,True),fill=(191,80,20))
d.rectangle([x0+4*(tw+g)-5,y0+3*(th+g)-5,x0+6*(tw+g)-g+5,y0+4*(th+g)-g+5],outline=(84,130,53),width=4)
d.text((x0+4*(tw+g)+3,y0+3*(th+g)+3),"C",font=f(22,True),fill=(84,130,53))
# right panels
def panel(b,title,lines,fc,oc):
    d.rounded_rectangle(b,radius=10,fill=fc,outline=oc,width=2)
    d.text((b[0]+14,b[1]+10),title,font=f(19,True),fill=(25,25,25))
    y=b[1]+48
    for line in lines:
        d.text((b[0]+18,y),line,font=f(16),fill=(40,40,40)); y+=30
panel((630,110,1175,230),"A  2×2 = INT8 32×32",["大 GEMM / Ozaki 逐模数 GEMM","复用高、同步开销低"],(218,232,245),(31,78,121))
panel((630,250,1175,370),"B  1×1 = FP4 16×16",["小 GEMM / 低精度原生","低延迟、可独立门控"],(252,235,215),(191,80,20))
panel((630,390,1175,510),"C  2×1 = FP8 32×16",["中等 GEMM / FP8 原生","兼顾并行度与复用"],(226,239,218),(84,130,53))
panel((630,530,1175,610),"约束",["无格式转换；tile 对齐；避免碎片化。"],(245,245,245),(120,120,120))
center(d,(0,625,W,650),"O-mode 用 INT8 tile；R-mode 用原生 FP4/FP8/INT8 tile；同一 Fabric 分时/分区。",f(14),(90,90,90))
img.save(os.path.join(OUT,"fig4_subarray.png"))
print("saved readable fig3/fig4")

# Fig 5: roadmap
W,H=1200,650; img=Image.new("RGB",(W,H),"white"); d=ImageDraw.Draw(img)
center(d,(0,8,W,45),"36 个月技术路线与里程碑（v1.3 双模）",f(24,True))
left,top,qw,rh=230,95,72,62
labels=["WP1 格式刻画/选择","WP2 O-mode Ozaki","WP3 R-mode BSP","WP4 双模集成","WP5 FireSim/U250","WP6 论文/答辩"]
starts=[0,1,1,4,7,10]; spans=[2,4,5,4,3,2]
for i,lab in enumerate(labels):
    d.text((10,top+i*rh+15),lab,font=f(18),fill=(20,20,20))
    x=left+starts[i]*qw; w=spans[i]*qw
    d.rounded_rectangle([x,top+i*rh+6,x+w-6,top+i*rh+rh-8],radius=6,fill=(218,232,245),outline=(31,78,121),width=2)
for q in range(13):
    x=left+q*qw
    d.line([(x,top-8),(x,top+6*rh+8)],fill=(220,220,220),width=1)
    if q<12: d.text((x+qw/2-18,top-38),f"Q{q+1}",font=f(14),fill=(60,60,60))
ms=[("M0",0),("M1",3),("M2",6),("M3",9),("M4",12),("M5",15),("M6",18)]
for name,q in ms:
    x=left+q*qw
    d.ellipse([x-6,top+6*rh+16,x+6,top+6*rh+28],fill=(192,0,0))
    d.text((x-12,top+6*rh+32),name,font=f(14,True),fill=(192,0,0))
center(d,(0,610,W,640),"M1：BSP 面积/时序与 O-mode 模型 Go/No-Go；M4：双模集成；M5：U250/FireSim 系统评估。",f(15),(90,90,90))
img.save(os.path.join(OUT,"fig5_roadmap.png"))
print("saved fig3/fig4/fig5")
