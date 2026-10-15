"""spread() from fewshot_saccades.py (importable without running that experiment)."""
import numpy as np


def spread(code, r=1):
    m = code.reshape(len(code), 4, 6, 6, 32); out = np.zeros_like(m); p = np.pad(m, ((0, 0), (0, 0), (r, r), (r, r), (0, 0)))
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            out |= p[:, :, dy:dy + 6, dx:dx + 6, :]
    return out.reshape(len(code), -1)
