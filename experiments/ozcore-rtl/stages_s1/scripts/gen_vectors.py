#!/usr/bin/env python3
import random, os
K=128
random.seed(20261126)
def u(v,b): return v & ((1<<b)-1)
def pack(vals,w):  # little-endian packed
    x=0
    for i,v in enumerate(vals): x |= u(v,w) << (i*w)
    return f"{x:0{(len(vals)*w)//4}x}"
lines=[]
# preprocess
pre_in=[random.randint(-32768,32767) for _ in range(K)]
pre_exp=[u(v,8) for v in pre_in]
lines.append(f"{pack(pre_in,16)} {pack(pre_exp,8)}")
# postprocess
post_in=[random.randint(-2**31,2**31-1) for _ in range(K)]
post_exp=[u(v,32) for v in post_in]
lines.append(f"{pack(post_in,32)} {pack(post_exp,32)}")
# mac
w=[random.randint(-128,127) for _ in range(K)]
x=[random.randint(-128,127) for _ in range(K)]
acc=sum(a*b for a,b in zip(w,x))
lines.append(f"{pack(w,8)} {pack(x,8)} {u(acc,32):08x}")
# lane
wl=[random.randint(-32768,32767) for _ in range(K)]
xl=[random.randint(-32768,32767) for _ in range(K)]
acc2=sum((a & 0xff if a>=0 else (a & 0xff))*(b & 0xff) for a,b in zip(wl,xl))
# use signed int8 low bytes:
acc2=sum(((a & 0xff)-256 if (a & 0x80) else (a & 0xff))*((b & 0xff)-256 if (b & 0x80) else (b & 0xff)) for a,b in zip(wl,xl))
lines.append(f"{pack(wl,16)} {pack(xl,16)} {u(acc2,32):08x}")
out=os.path.join(os.path.dirname(__file__),"..","tb","vectors.txt")
open(out,"w").write("\n".join(lines)+"\n")
print("wrote",out)
