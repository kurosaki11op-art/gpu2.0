"""Make a small, pushable subset of the Google Speech Commands v0.02 set (run on the user's PC, 21 Oct 2026).
Keeps N random clips (fixed seed) per word for every word folder, skipping _background_noise_, copying them to OUT/<word>/*.wav.
35 words x 100 clips is about 110 MB (each 1 s 16 kHz clip is about 32 KB). usage: python make_sc_subset.py EXTRACTED_DIR OUT_DIR [N=100]"""
import os, random, shutil, sys
src, out = sys.argv[1], sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 100
words = sorted(d for d in os.listdir(src) if os.path.isdir(os.path.join(src, d)) and not d.startswith("_"))
for w in words:
    fs = sorted(f for f in os.listdir(os.path.join(src, w)) if f.endswith(".wav"))
    random.Random(w).shuffle(fs); os.makedirs(os.path.join(out, w), exist_ok=True)
    for f in fs[:n]:
        shutil.copy(os.path.join(src, w, f), os.path.join(out, w, f))
    print(w, min(n, len(fs)))
print(len(words), "words ->", out)
