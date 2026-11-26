#!/usr/bin/env python3
import random, os
K,N,S=128,16,12
random.seed(20261126)
def u(v,b): return v & ((1<<b)-1)
def pack(vals): # vals 12xK signed int8 -> 12*K*16 bit hex, low byte
    x=0
    for c in range(S):
        for j in range(K): x |= u(vals[c][j],8) << ((c*K+j)*16)
    return f"{x:0{(S*K*16)//4}x}"
lines=[]
# weights per column
W=[]
for n in range(N):
    w=[[random.randint(-128,127) for _ in range(K)] for _ in range(S)]
    W.append(w); lines.append(pack(w))
# 5 activation frames
for case in range(5):
    X=[[random.randint(-128,127) for _ in range(K)] for _ in range(S)]
    lines.append(pack(X))
    xout=0; exp=[]
    for c in range(S):
        for n in range(N):
            a=sum(W[n][c][j]*X[c][j] for j in range(K))
            exp.append(a); xout |= u(a,32) << ((c*N+n)*32)
    lines.append(f"{xout:0{(S*N*32)//4}x}")
out=os.path.join(os.path.dirname(__file__),"..","tb","vectors.txt")
open(out,"w").write("\n".join(lines)+"\n")
print("wrote",out,"N",N,"K",K,"cases",5)
