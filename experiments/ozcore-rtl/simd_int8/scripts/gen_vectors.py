#!/usr/bin/env python3
"""Generate random + edge vectors and expected outputs for ozcore_simd_int8."""
import random, os
K, S = 8, 12
random.seed(20261126)
lines=[]
def enc8(v): return v & 0xff
def acc_bits(v): return v & 0xffffffff
def sh_bits(v): return v & 0x1ff
def add_case(w, x, e, s):
    wf=0; xf=0; ef=0; sf=0
    for i in range(S):
        for j in range(K):
            wf |= enc8(w[i][j]) << ((i*K+j)*8)
            xf |= enc8(x[i][j]) << ((i*K+j)*8)
        ef |= sh_bits(e[i]) << (i*9)
        sf |= sh_bits(s[i]) << (i*9)
    acc=0; sh=0
    for i in range(S):
        a=sum(w[i][j]*x[i][j] for j in range(K))
        acc |= acc_bits(a) << (i*32)
        sh |= sh_bits(e[i]+s[i]) << (i*9)
    lines.append(f"{wf:0{(S*K*8)//4}x} {xf:0{(S*K*8)//4}x} {ef:0{(S*9)//4}x} {sf:0{(S*9)//4}x} {acc:0{(S*32)//4}x} {sh:0{(S*9)//4}x}")

# all zeros
add_case([[0]*K for _ in range(S)], [[0]*K for _ in range(S)], [0]*S, [0]*S)
# all +127 / -128
add_case([[127]*K for _ in range(S)], [[127]*K for _ in range(S)], [0]*S, [0]*S)
add_case([[-128]*K for _ in range(S)], [[-128]*K for _ in range(S)], [0]*S, [0]*S)
# random
for _ in range(120):
    w=[[random.randint(-128,127) for _ in range(K)] for _ in range(S)]
    x=[[random.randint(-128,127) for _ in range(K)] for _ in range(S)]
    e=[random.randint(-256,255) for _ in range(S)]
    s=[random.randint(-256,255) for _ in range(S)]
    add_case(w,x,e,s)
out=os.path.join(os.path.dirname(__file__),"..","tb","vectors.txt")
open(out,"w").write("\n".join(lines)+"\n")
print("wrote",out,len(lines),"cases")
