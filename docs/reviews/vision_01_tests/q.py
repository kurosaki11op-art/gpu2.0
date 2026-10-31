import subprocess,sys,os,numpy as np,json
W=sys.argv[1];V,T=128,64
def nll(d,mode):
    ids=np.fromfile(f"{d}/inputs.bin",np.float32).reshape(-1,T).astype(np.int64);lg=np.fromfile(f"{d}/out_{mode}.bin",np.float32).reshape(-1,T,V);lg=lg-lg.max(-1,keepdims=True)
    lp=lg-np.log(np.exp(lg).sum(-1,keepdims=True));return float(-np.take_along_axis(lp[:,:-1],ids[:,1:][...,None],-1).mean())
d=f"{W}/lm"
def run(mode,**e):
    subprocess.run([f"{W}/../gpu_sim_q",d,mode,"16"],check=True,capture_output=True,env=dict(os.environ,**e));return nll(d,mode)
f=run("fp32");print("fp32",round(f,4))
for b,q in((8,127),(6,31),(5,15),(4,7),(3,3)):
    for mode in("w8","int8"):
        print(b,"bit",mode,"wo emb %+.4f"%(run(mode,V_WQ=str(q))-f),"with emb %+.4f"%(run(mode,V_WQ=str(q),V_QEMB="1")-f),flush=True)
