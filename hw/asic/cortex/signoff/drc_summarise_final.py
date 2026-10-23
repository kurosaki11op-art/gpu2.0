import re,collections,glob,sys
D=sys.argv[1]
exec(open("/tmp/drc/an.py").read().split("tot=collections")[0])
mac=[]
import subprocess
# macro placements from the odb-derived list saved earlier
for l in open("/tmp/pipe/macros.txt"):
    x,y=[float(v) for v in l.split()]; mac.append((x,y,x+683.1,y+416.54))
def near(cx,cy,pad): return any(a-pad<=cx<=c+pad and b-pad<=cy<=e+pad for a,b,c,e in mac)
W,H=7500,6200;nx,ny=3,2
tot=collections.Counter();totm=collections.Counter();pos=collections.defaultdict(list)
done=[]
for f in sorted(glob.glob(D+"/why_*.txt")):
    if open(f).read(1)=="": continue
    i,j=[int(v) for v in re.search(r"why_(\d)_(\d)",f).groups()]; done.append((i,j))
    x0,x1=i*W/nx,(i+1)*W/nx; y0,y1=j*H/ny,(j+1)*H/ny
    toks=parse(open(f).read())
    for k in range(0,len(toks)-1,2):
        rule=toks[k]
        for b in re.findall(r"\{(-?\d+) (-?\d+) (-?\d+) (-?\d+)\}",toks[k+1]):
            a=[int(v)*0.005 for v in b]; cx,cy=(a[0]+a[2])/2,(a[1]+a[3])/2
            if x0<=cx<x1 and y0<=cy<y1:
                tot[rule]+=1
                if near(cx,cy,3): totm[rule]+=1
                else: pos[rule].append((round(cx),round(cy)))
print("tiles with results:",done)
print("total errors:",sum(tot.values()),"within 3 um of a macro:",sum(totm.values()),"elsewhere (logic/routing):",sum(tot.values())-sum(totm.values()))
for r,c in tot.most_common(12): print(c,totm[r],r[:80],pos[r][:2])
