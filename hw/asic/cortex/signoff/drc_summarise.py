import re,collections,glob
exec(open("/tmp/drc/an.py").read().split("tot=collections")[0])
W,H=7500,6200;nx,ny=3,2
tot=collections.Counter();pos=collections.defaultdict(list)
for f in sorted(glob.glob("/tmp/drc/v3/why_*.txt")):
    i,j=[int(v) for v in re.search(r"why_(\d)_(\d)",f).groups()]
    x0,x1=i*W/nx,(i+1)*W/nx; y0,y1=j*H/ny,(j+1)*H/ny
    toks=parse(open(f).read())
    for k in range(0,len(toks)-1,2):
        rule=toks[k]
        for b in re.findall(r"\{(-?\d+) (-?\d+) (-?\d+) (-?\d+)\}",toks[k+1]):
            x1_,y1_,x2_,y2_=[int(v)*0.005 for v in b]; cx,cy=(x1_+x2_)/2,(y1_+y2_)/2
            if x0<=cx<x1 and y0<=cy<y1: tot[rule]+=1; pos[rule].append((round(cx),round(cy)))
print("tiles",len(glob.glob("/tmp/drc/v3/why_*.txt")),"errors in tile interiors:",sum(tot.values()))
for r,c in tot.most_common(25): print(c,r[:95],pos[r][:2])
