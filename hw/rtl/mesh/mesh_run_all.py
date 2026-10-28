"""Runs the mesh check for the 4x4 and 8x8 meshes (used by the virtual device regression); exit code 0 only if every output matches."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__)); out = []; ok = True
for a in (["4", "4", "4", "2"], ["8", "4", "4", "2"]):
    r = subprocess.run([sys.executable, os.path.join(here, "gen_and_check.py")] + a, capture_output=True, text=True); out.append(r.stdout.strip().split("\n")[0]); ok &= (r.returncode == 0)
print("\n".join(out)); sys.exit(0 if ok else 1)
