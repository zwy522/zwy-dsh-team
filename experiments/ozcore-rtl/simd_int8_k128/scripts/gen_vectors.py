#!/usr/bin/env python3
import random, os
K,S=128,12
random.seed(20261126)
lines=[]
def enc(v): return v & 0xff
def u(v,b): return v & ((1<<b)-1)
def add(w,x,e,s):
    wf=0;xf=0;ef=0;sf=0
    for i in range(S):
        for j in range(K):
            wf |= enc(w[i][j]) << ((i*K+j)*8)
            xf |= enc(x[i][j]) << ((i*K+j)*8)
        ef |= u(e[i],9) << (i*9); sf |= u(s[i],9) << (i*9)
    acc=0; sh=0
    for i in range(S):
        a=sum(w[i][j]*x[i][j] for j in range(K))
        acc |= u(a,32) << (i*32); sh |= u(e[i]+s[i],9) << (i*9)
    lines.append(f"{wf:0{(S*K*8)//4}x} {xf:0{(S*K*8)//4}x} {ef:0{(S*9)//4}x} {sf:0{(S*9)//4}x} {acc:0{(S*32)//4}x} {sh:0{(S*9)//4}x}")
add([[0]*K for _ in range(S)], [[0]*K for _ in range(S)], [0]*S, [0]*S)
add([[127]*K for _ in range(S)], [[127]*K for _ in range(S)], [0]*S, [0]*S)
add([[-128]*K for _ in range(S)], [[-128]*K for _ in range(S)], [0]*S, [0]*S)
for _ in range(17):
    w=[[random.randint(-128,127) for _ in range(K)] for _ in range(S)]
    x=[[random.randint(-128,127) for _ in range(K)] for _ in range(S)]
    e=[random.randint(-256,255) for _ in range(S)]
    s=[random.randint(-256,255) for _ in range(S)]
    add(w,x,e,s)
out=os.path.join(os.path.dirname(__file__),"..","tb","vectors.txt")
open(out,"w").write("\n".join(lines)+"\n")
print("wrote",out,len(lines))
