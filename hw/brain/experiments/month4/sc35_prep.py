"""Prepare the 35-word Speech Commands subset (data/sc_subset, 100 clips per word, pushed by the user 18 Oct 2026) for the new-word tests.
Each clip (16 kHz, 1 s) is padded / cropped to 16,000 samples and passed through the same integer cochlea as the other speech sets -> sc35_framesums_int.npz
(S frame sums, y word index in WORDS, spk speaker hash from the file name, te = speaker-disjoint test flag: speaker hash mod 5 == 0). usage: SUBSET_DIR DATA_DIR"""
import os, sys, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea, cochlea_int
root, D = sys.argv[1], sys.argv[2]
WORDS = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
X, y, spk = [], [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(root, w))):
        with wave.open(os.path.join(root, w, f)) as r:
            x = np.frombuffer(r.readframes(r.getnframes()), np.int16).astype(np.float64)
        out = np.zeros(16000); out[:min(16000, len(x))] = x[:16000]
        X.append(out); y.append(wi); spk.append(int(f.split("_")[0], 16))
X = np.stack(X); S = []
for i in range(0, len(X), 500):
    S.append(cochlea_int._bank(X[i:i + 500].astype(np.int16).astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB).astype(np.int32))
S = np.concatenate(S); spk = np.array(spk); te = (spk % 5) == 0
np.savez_compressed(os.path.join(D, "sc35_framesums_int.npz"), S=S, y=np.array(y), spk=spk, te=te, words=np.array(WORDS))
print("clips", len(y), "words", len(WORDS), "test", int(te.sum()), "frame sums", S.shape)
