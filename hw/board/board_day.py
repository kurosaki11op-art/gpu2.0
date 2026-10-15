#!/usr/bin/env python3
"""Board day in one command: runs the month-4 board plan's steps in order and collects every output into one report
file to send back (docs/month4_board_plan.md). The power bench (step 6) and the live demos stay separate because they
need you at the keyboard.

  python hw\\board\\board_day.py --port COM5 --data D:\\cortex_data            # steps 0-5 on the board
  python hw\\board\\board_day.py --data D:\\cortex_data --dry-run-only          # only the PC-side steps (no board)

Writes board_day_<date>_<time>.txt in the current folder. Each step's output is copied as it is; nothing is edited."""
import argparse, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--data", default="cortex_data")
    ap.add_argument("--per-class", type=int, default=300)
    ap.add_argument("--dry-run-only", action="store_true")
    ap.add_argument("--sound", action="store_true", help="also step 9: spoken words (needs Speech Commands in <data>/speech)")
    a = ap.parse_args()
    if not a.dry_run_only and not a.port:
        sys.exit("give --port COMx (or --dry-run-only)")
    py = sys.executable; host = os.path.join(HERE, "cortex_host.py"); pc = str(a.per_class)
    steps = [("0 preflight", [py, os.path.join(HERE, "preflight.py"), "--data", a.data] + (["--port", a.port] if a.port else [])),
             ("1 dry run (emulator, no board)", [py, host, "--dry-run", "--per-class", pc, "--data", a.data])]
    if not a.dry_run_only:
        steps += [("3 board: learns in stages (MEASURED)", [py, host, "--port", a.port, "--per-class", pc, "--data", a.data]),
                  ("4 board: senses raw pixels itself", [py, host, "--port", a.port, "--per-class", pc, "--data", a.data, "--onchip-encode"]),
                  ("5 board: memory transfer", [py, os.path.join(HERE, "cortex_transfer.py"), "--port", a.port, "--per-class", pc, "--data", a.data])]
        if a.sound:
            steps.append(("9 board: spoken words", [py, host, "--task", "sound", "--port", a.port, "--per-class", "200", "--data", a.data]))
    name = time.strftime("board_day_%Y%m%d_%H%M%S.txt")
    with open(name, "w") as rep:
        rep.write(f"SPARK Cortex board day {time.strftime('%Y-%m-%d %H:%M:%S')}  port={a.port}  per-class={pc}\n")
        for title, cmd in steps:
            print(f"\n=== step {title} ===", flush=True); rep.write(f"\n=== step {title} ===\n$ {' '.join(cmd)}\n"); rep.flush()
            t0 = time.time()
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                print(line, end="", flush=True); rep.write(line); rep.flush()
            p.wait()
            rep.write(f"[exit code {p.returncode}, {time.time() - t0:.0f} s]\n"); rep.flush()
            if p.returncode != 0:
                print(f"step {title} failed (exit code {p.returncode}); stopping here - send me {name}")
                break
    print(f"\nreport saved: {os.path.abspath(name)}  - send this file back")


if __name__ == "__main__":
    main()
