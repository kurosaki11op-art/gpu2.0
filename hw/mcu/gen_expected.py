#!/usr/bin/env python3
"""Writes the model's expected results for all 10,000 Fashion-MNIST test images (the bit-exact reference model of the RTL, hw/brain/experiments/month5/ldeep_ref.py): model_expected_10k.npz (pred, routed, final margin) for the host script, and, for the PC check of the C core,
test_images_10k.bin and sys_exp_10k.txt in a scratch folder.   usage: python gen_expected.py DATA_DIR SCRATCH_DIR"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "brain")); sys.path.insert(0, os.path.join(HERE, "..", "brain", "experiments", "month5")); sys.argv = sys.argv[:1] + sys.argv[1:]
D, SCR = sys.argv[1], sys.argv[2]
from cortex_core import load  # noqa
import ldeep_ref as R
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); X, y = np.ascontiguousarray(z["X"], np.uint8), z["y"]
rr, S, pp = R.run(X); srt = np.sort(S, 1); mrg = (srt[:, -1] - srt[:, -2]).astype(np.int32)
np.savez_compressed(os.path.join(HERE, "model_expected_10k.npz"), pred=pp.astype(np.uint8), routed=rr.astype(np.uint8), margin=mrg, label=y.astype(np.uint8))
xtr, ytr, xte, yte = load(D, "fashion"); assert (yte == y).all()
open(os.path.join(SCR, "test_images_10k.bin"), "wb").write(xte.astype(np.uint8).tobytes())
open(os.path.join(SCR, "sys_exp_10k.txt"), "w").write("\n".join("%d " % rr[i] + " ".join(str(int(v)) for v in S[i]) + " %d" % pp[i] for i in range(len(y))) + "\n")
print("wrote model_expected_10k.npz (%d images), accuracy of the model %.4f, routed %.1f%%" % (len(y), (pp == y).mean(), 100 * rr.mean()))
