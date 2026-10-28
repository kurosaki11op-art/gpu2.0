"""Writes the full 10,000-image test inputs of the L Deep system (6,176 bits per image) and the labels to a scratch file for the virtual-device tests."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import cte, yte, xte
def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
X = np.concatenate([cte, _bits(xte)], 1).astype(np.uint8); out = os.environ.get("OUT", "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz")
np.savez_compressed(out, X=X, y=yte); print("saved", X.shape, out)
