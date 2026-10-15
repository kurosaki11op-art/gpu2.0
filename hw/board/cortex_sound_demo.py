#!/usr/bin/env python3
"""Live sound demo: say a new word a few times, SPARK Cortex learns it, and still knows the words it knew.

  python cortex_sound_demo.py --data D:\\cortex_data                 # emulator (bit-exact with the chip)
  python cortex_sound_demo.py --data D:\\cortex_data --port COM5     # the real Tang Nano 20K (today's bitstream)
  python cortex_sound_demo.py --data D:\\cortex_data --headless      # scripted check, no microphone

The chip first learns 8 of the 10 Speech Commands words in stages (--preload clips per word). Then type commands:
  teach N        record 1 s from the microphone (or: teach N file.wav) and teach it as word number N (8 or 9 are free)
  ask            record 1 s (or: ask file.wav) and say which word the chip heard
  sleep          a short night of dreams (consolidates the new word with the old ones)
  test           accuracy on test clips of every word the chip knows
  quit
The PC turns each second of sound into a 28x28 sound picture with the chip's integer cochlea (noise floor on); the
board encodes and learns it like an image. Microphone: pip install sounddevice (optional; wav files work without it).
"""
import argparse, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "brain"))
from cortex_host import Board, Emu, SEED_LANES, run_stage, speech  # noqa
from cortex_demo import Brain  # noqa
from feature_layer import Features  # noqa


def picture(x):
    import cochlea_int
    x = np.asarray(x, np.int16)[:16000]
    x = np.pad(x, (0, 16000 - len(x)))
    return cochlea_int.sound_picture_int(x[None])[0]


def record():
    import sounddevice as sd
    print("  speak now (1 s)...", flush=True)
    x = sd.rec(16000, samplerate=16000, channels=1, dtype="int16"); sd.wait()
    return x[:, 0]


def load_wav(path):
    import cochlea
    return cochlea.read(path).astype(np.int16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200); ap.add_argument("--data", default="cortex_data")
    ap.add_argument("--preload", type=int, default=300); ap.add_argument("--words", default="0-7")
    ap.add_argument("--headless", action="store_true", help="scripted run: teach the next word from --teach test-set clips")
    ap.add_argument("--teach", type=int, default=10, help="clips used to teach the new word in --headless")
    ap.add_argument("--daydreams", type=int, default=1, help="daydreams of the new word after each taught clip")
    a = ap.parse_args()
    import cochlea
    xtr, ytr, xte, yte = speech(a.data)
    print("learning feature detectors from sound pictures (no labels)...")
    fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
    enc = lambda x: np.concatenate([f.encode(x) for f in fes], 1)
    dev = Board(a.port, a.baud) if a.port else Emu(4608)
    dev.seed(SEED_LANES); dev.clear()
    brain = Brain(dev, enc, xte, yte)
    lo, hi = (int(v) for v in a.words.split("-"))
    print(f"pre-teaching words {lo}-{hi} ({', '.join(cochlea.WORDS[lo:hi + 1])}), {a.preload} clips each, in stages of two...")
    for s0 in range(lo, hi + 1, 2):
        s = [c for c in (s0, s0 + 1) if c <= hi]
        sel = np.concatenate([np.where(ytr == c)[0][:a.preload] for c in s]); sel = sel[np.random.RandomState(s0).permutation(len(sel))]
        run_stage(dev, enc(xtr[sel]), ytr[sel], brain.known)
    r = brain.test_old(); print(f"ready: {r[0]:.1%} on {r[1]} test clips of the known words")
    if a.headless:
        new = hi + 1; idx = np.where(yte == new)[0]
        for i in idx[:a.teach]:
            brain.teach(new, xte[i], daydreams=a.daydreams)
        print(f"taught word {new} ('{cochlea.WORDS[new]}') from {a.teach} clips; sleeping...")
        brain.sleep()
        rest = idx[a.teach:a.teach + 150]
        acc_new = np.mean([brain.ask(xte[i]) == new for i in rest])
        r = brain.test_old(400)
        print(f"new word: {acc_new:.1%} on {len(rest)} unseen clips; all known words: {r[0]:.1%} on {r[1]} clips")
        return
    while True:
        try:
            cmd = input("> ").split()
        except EOFError:
            break
        if not cmd:
            continue
        try:
            if cmd[0] == "quit":
                break
            if cmd[0] in ("teach", "ask"):
                x = load_wav(cmd[-1]) if cmd[-1].endswith(".wav") else record()
                p = picture(x)
                if cmd[0] == "teach":
                    c = int(cmd[1]); brain.teach(c, p, daydreams=a.daydreams)
                    print(f"  taught word {c} ({brain.counts[c]} times so far)")
                else:
                    c = brain.ask(p); print(f"  heard word {c} ({cochlea.WORDS[c] if c < len(cochlea.WORDS) else 'your word'})")
            elif cmd[0] == "sleep":
                print(f"  slept: {brain.sleep()} dreams")
            elif cmd[0] == "test":
                r = brain.test_old(400); print(f"  {r[0]:.1%} on {r[1]} test clips of the known words")
        except Exception as e:
            print("  error:", e)


if __name__ == "__main__":
    main()
