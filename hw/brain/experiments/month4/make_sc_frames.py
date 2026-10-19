"""Run on the user's PC (19 Oct 2026): convert up to N Speech Commands clips per word (all 35 word folders of the extracted v0.02 set) straight to integer-cochlea frame sums,
so a much larger data set can be pushed as small files (28x28 int32 per clip, about 3 KB, instead of a 32 KB .wav). Same preprocessing as sc35_prep.py (pad / crop to 16,000 samples, integer cochlea).
Writes OUT/<word>.npz with S (clips, 28, 28) and spk (speaker hash from the file name). Needs numpy. usage: python make_sc_frames.py EXTRACTED_DIR OUT_DIR [N=1000]"""
import os, random, sys, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea, cochlea_int
src, out = sys.argv[1], sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
os.makedirs(out, exist_ok=True)
for w in sorted(d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d)) and not d.startswith("_")):
    fs = sorted(f for f in os.listdir(os.path.join(src, w)) if f.endswith(".wav")); random.Random(w).shuffle(fs); fs = fs[:n]
    X, spk = [], []
    for f in fs:
        with wave.open(os.path.join(src, w, f)) as r:
            x = np.frombuffer(r.readframes(r.getnframes()), np.int16).astype(np.float64)
        o = np.zeros(16000); o[:min(16000, len(x))] = x[:16000]; X.append(o); spk.append(int(f.split("_")[0], 16))
    X = np.stack(X)
    S = np.concatenate([cochlea_int._bank(X[i:i + 500].astype(np.int16).astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB).astype(np.int32) for i in range(0, len(X), 500)])
    np.savez_compressed(os.path.join(out, w + ".npz"), S=S, spk=np.array(spk, dtype=np.int64)); print(w, len(fs), flush=True)
