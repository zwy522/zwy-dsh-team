#!/usr/bin/env python3
import random, os
K=128
random.seed(20261127)
def pack(vals,w):
    x=0
    for i,v in enumerate(vals): x |= (v & ((1<<w)-1)) << (i*w)
    return f"{x:0{(len(vals)*w)//4}x}"
def i2f(x):
    s=1 if x<0 else 0; a=-x if s else x
    if a==0: return 0
    msb=a.bit_length()-1; e=127+msb
    frac=(a>>(msb-23)) if msb>=23 else (a<<(23-msb))
    return (s<<31)|(e<<23)|(frac&0x7fffff)
lines=[]
for case in range(5):
    w=[random.randint(-128,127) for _ in range(K)]
    x=[random.randint(-128,127) for _ in range(K)]
    dot=sum(a*b for a,b in zip(w,x))
    lines.append(f"{pack(w,8)} {pack(x,8)} {i2f(dot):08x}")
out=os.path.join(os.path.dirname(__file__),"..","tb","vectors.txt")
open(out,"w").write("\n".join(lines)+"\n")
print("wrote",out)
