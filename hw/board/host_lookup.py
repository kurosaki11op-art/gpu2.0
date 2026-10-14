#!/usr/bin/env python3
"""Drive the SPARK-L board (lookup_board_top.v) from a PC over the Tang Nano 20K's USB-UART.
Streams a file through the board in 255-byte chunks, checks every prediction against the bit-exact reference model,
and reads the board's own counters (bytes, correct, table hits).
Needs: pip install pyserial.   Examples:
  py -3.12 hw\\board\\host_lookup.py --port COM5 --file hw\\system\\data\\prose_slices.txt --max-bytes 20000
  python hw/board/host_lookup.py --dry-run --file hw/system/data/prose_slices.txt      (no board: a software stand-in answers)"""
import argparse, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "system"))
from lookup_ref import LookupCoreV2  # noqa


class FakeBoard:
    """Byte-level stand-in for the board protocol, for testing this script without hardware."""
    def __init__(self, tb):
        self.tb = tb; self.out = bytearray(); self.inb = bytearray(); self._reset()

    def _reset(self):
        self.core = LookupCoreV2(self.tb); self.n = self.c = self.h = 0; self.last = None

    def _feed(self, b):
        if self.last is not None and self.last == b: self.c += 1
        r = self.core.step(b); self.n += 1; self.h += r[1]; self.last = r[0]; return r

    def write(self, data):
        self.inb += data
        while self.inb:
            cmd = self.inb[0]
            if cmd == 0xE0: self.out.append(0x5A); del self.inb[:1]
            elif cmd == 0xB0: self._reset(); self.out.append(0xB1); del self.inb[:1]
            elif cmd == 0xD2:
                if len(self.inb) < 2 or len(self.inb) < 2 + self.inb[1]: return
                n = self.inb[1]; x = 0
                for b in self.inb[2:2 + n]:
                    p = self._feed(b)[0]; self.out.append(p); x ^= p
                self.out.append(x); del self.inb[:2 + n]
            elif cmd == 0xF0:
                bs = b"".join(v.to_bytes(4, "little") for v in (self.n, self.c, self.h)); x = 0
                for v in bs: x ^= v
                self.out += bs + bytes([x]); del self.inb[:1]
            else: del self.inb[:1]

    def read(self, n):
        r = bytes(self.out[:n]); del self.out[:n]; return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port"); ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--file", required=True); ap.add_argument("--max-bytes", type=int, default=20000)
    ap.add_argument("--tb", type=int, default=11, help="must match the TB parameter the bitstream was built with")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        dev = FakeBoard(a.tb)
    else:
        import serial
        dev = serial.Serial(a.port, a.baud, timeout=2)

    def rd(n):
        r = dev.read(n)
        if len(r) != n: raise SystemExit(f"board did not answer (got {len(r)} of {n} bytes): check port, baud and bitstream")
        return r
    data = open(a.file, "rb").read()[:a.max_bytes]
    dev.write(bytes([0xE0])); assert rd(1) == b"\x5a", "ping failed"
    dev.write(bytes([0xB0])); assert rd(1) == b"\xb1", "clear failed"
    ref = LookupCoreV2(a.tb); mism = 0; t0 = time.time()
    for i in range(0, len(data), 255):
        chunk = data[i:i + 255]
        dev.write(bytes([0xD2, len(chunk)]) + chunk)
        got = rd(len(chunk) + 1); x = 0
        for j, b in enumerate(chunk):
            p = ref.step(b)[0]; mism += got[j] != p; x ^= got[j]
        if x != got[-1]: raise SystemExit("checksum error on the UART link")
    dt = time.time() - t0
    dev.write(bytes([0xF0])); r = rd(13)
    n, c, h = (int.from_bytes(r[k:k + 4], "little") for k in (0, 4, 8))
    print(f"{'(dry run) ' if a.dry_run else ''}{n} bytes in {dt:.1f} s ({n / max(dt, 1e-9):.0f} bytes/s over the UART)")
    print(f"board's own score: next-byte accuracy {c / max(1, n - 1):.2%}, table hit rate {h / max(1, n):.2%}")
    print(f"bit-exact check against the reference model: {mism} mismatching predictions of {n}")


if __name__ == "__main__":
    main()
