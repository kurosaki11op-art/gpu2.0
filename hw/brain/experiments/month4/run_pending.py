#!/usr/bin/env python3
"""Relaunch unfinished background experiments after a container restart (idempotent; 20 Oct 2026). A restart kills every background job, so after any restart run:  python run_pending.py
For each job: read its log, keep only the arms that have no result line yet, and start the job again for those arms (output appended to the same log) unless its recorded process is still alive.
Sound codes are cached per feature channel (CACHE/ch_*.npz), so a restarted sound job resumes at the first unfinished channel."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
S = os.environ.get("SCRATCH", "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad")
SUB = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "data", "sc_subset"))
JOBS = [  # (log, script, args, env, arms)
    ("brain_strict_noise_twice.log", "brain_strict_noise_gate.py", [SUB, S + "/bs_cache"], {"OUT": "x"}, ["twice"]),
    ("brain_strict_geom_a.log", "brain_strict_sound.py", [SUB, S + "/bs_cache35"], {"NW": "35", "OUT": "brain_strict_geom_a.json"}, ["geom:3:3:1:1:4:4", "geom:3:3:1:1:4:2"]),
    ("brain_strict_geom_b.log", "brain_strict_sound.py", [SUB, S + "/bs_cache35"], {"NW": "35", "OUT": "brain_strict_geom_b.json"}, ["geom:3:5:1:1:4:4", "geom:2:7:1:1:4:4"]),
    ("sc35_views_m32.log", "sc35_views.py", [S + "/data"], {"MARGIN": "32"}, ["T=15 k=5:"]),
    ("sc35_views_m256.log", "sc35_views.py", [S + "/data"], {"MARGIN": "256"}, ["T=15 k=5:"]),
]


def alive(pid):
    try: os.kill(pid, 0); return True
    except OSError: return False


for log, script, args, env, arms in JOBS:
    path = os.path.join(HERE, log); done = set()
    if os.path.exists(path):
        for line in open(path):
            for a in arms:
                if line.startswith(a + " {") or line.startswith(a + " "): done.add(a) if "{" in line[:len(a) + 3] else None
    todo = [a for a in arms if a not in done]; pidf = os.path.join(HERE, "." + log + ".pid")
    if not todo: print("done    ", log); continue
    if os.path.exists(pidf) and alive(int(open(pidf).read() or 0)): print("running ", log, ",".join(todo)); continue
    p = subprocess.Popen(["nohup", sys.executable, "-u", os.path.join(HERE, script)] + args, cwd=HERE, env=dict(os.environ, ARMS=",".join(todo), **env), stdout=open(path, "a"), stderr=subprocess.STDOUT, start_new_session=True)
    open(pidf, "w").write(str(p.pid)); print("started ", log, ",".join(todo))
