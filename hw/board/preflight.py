#!/usr/bin/env python3
"""Board-day preflight for SPARK Cortex (run on your PC before docs/month4_board_plan.md step 1).
Checks: Python version, packages, the data folder, the bitstream file, serial ports, and (with --port) that the board
answers the ping. Prints OK / FIX lines; changes nothing on your PC.
  python hw\\board\\preflight.py --data D:\\cortex_data [--port COM5]"""
import argparse, gzip, importlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ok = True


def say(good, what, fix=""):
    global ok
    ok &= good
    print(("OK   " if good else "FIX  ") + what + ("" if good or not fix else "  ->  " + fix))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="cortex_data"); ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200)
    a = ap.parse_args()
    say(sys.version_info >= (3, 8), f"Python {sys.version.split()[0]}", "install Python 3.8 or newer")
    for pkg, need in (("numpy", True), ("serial", True), ("numba", False)):
        try:
            importlib.import_module(pkg); say(True, f"package {pkg}")
        except ImportError:
            if need:
                say(False, f"package {pkg} missing", "python -m pip install -r hw\\board\\requirements.txt")
            else:
                print(f"note package {pkg} missing (optional: dry runs will be slow)")
    f = os.path.join(a.data, "mnist.npz")
    if os.path.exists(f):
        say(os.path.getsize(f) > 10_000_000, f"data {f} ({os.path.getsize(f) // 1_000_000} MB)", "delete it and rerun the dry run to download again")
    else:
        print(f"note {f} not there yet: the first dry run downloads it (~11 MB) into {a.data}")
    bit = os.path.join(HERE, "..", "pnr_cortex", "cortex_tangnano20k.fs.gz")
    if os.path.exists(bit):
        with gzip.open(bit) as g:
            head = g.read(64)
        say(len(head) == 64, "bitstream hw/pnr_cortex/cortex_tangnano20k.fs.gz", "git pull again; the file looks damaged")
        unz = bit[:-3]
        if not os.path.exists(unz):
            print("note unzip it before programming: the .fs file goes to openFPGALoader / Gowin Programmer")
    else:
        say(False, "bitstream missing", "git pull (it lives in hw/pnr_cortex/)")
    try:
        from serial.tools import list_ports
        ports = [p.device + " (" + (p.description or "") + ")" for p in list_ports.comports()]
        print("note serial ports:", ", ".join(ports) if ports else "none found (board not plugged in, or driver missing)")
    except Exception:
        pass
    if a.port:
        try:
            import serial
            with serial.Serial(a.port, a.baud, timeout=2) as s:
                s.write(bytes([0xE0])); r = s.read(1)
            say(r == b"\x5a", f"board on {a.port} answers the ping", "check the bitstream is programmed, the port, and the pins in tangnano20k.cst")
        except Exception as e:
            say(False, f"could not open {a.port}: {e}", "pick the port shown above; close other programs using it")
    print("\nall checks passed - go to step 1 of the board plan" if ok else "\nfix the FIX lines above, then run this again")


if __name__ == "__main__":
    main()
