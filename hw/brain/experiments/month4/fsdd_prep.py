"""Prepare the Free Spoken Digit Dataset (FSDD; 10 more words: zero..nine, 6 speakers, 50 recordings each, 8 kHz) as extra words (20 Oct 2026; downloaded from raw.githubusercontent.com).
Each clip is resampled to 16 kHz (linear interpolation, offline), padded / cropped to 1 s, passed through the same integer cochlea as the Speech Commands clips -> frame sums
fsdd_framesums_int.npz (S, y = digit, spk = speaker index, rep). usage: DATA_DIR"""
import os, sys, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea, cochlea_int
D = sys.argv[1]; root = os.path.join(D, "fsdd"); SP = ["george", "jackson", "lucas", "nicolas", "theo", "yweweler"]
X, y, spk, rep = [], [], [], []
for d in range(10):
    for si, sp in enumerate(SP):
        for n in range(50):
            p = os.path.join(root, f"{d}_{sp}_{n}.wav")
            if not os.path.exists(p): continue
            with wave.open(p) as w:
                x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64); fs = w.getframerate()
            t = np.arange(0, len(x) - 1, fs / 16000.0); x16 = np.interp(t, np.arange(len(x)), x)
            out = np.zeros(16000); out[:min(16000, len(x16))] = x16[:16000]
            pk = np.abs(out).max(); out = out * (12000.0 / pk) if pk > 0 else out                       # level like the Speech Commands clips
            X.append(out); y.append(d); spk.append(si); rep.append(n)
X = np.stack(X); S = []
for i in range(0, len(X), 1000):
    S.append(cochlea_int._bank(X[i:i + 1000].astype(np.int16).astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB).astype(np.int32))
S = np.concatenate(S); np.savez_compressed(os.path.join(D, "fsdd_framesums_int.npz"), S=S, y=np.array(y), spk=np.array(spk), rep=np.array(rep)); print("clips", len(y), "frame sums", S.shape)
