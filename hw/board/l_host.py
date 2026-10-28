"""Host for the L board top (hw/rtl/top/l_board_top.v) over a serial port. 28 Oct 2026. The protocol is verified only in simulation against a UART model (hw/rtl/top/run_check_board.py); this script has NOT been run against a board. Usage: python l_host.py PORT [BAUD] sends one routed-test image bit vector from DATA_DIR if given, else prints the protocol self-check.
Protocol: 0xA5, op. op 0x01 RECOGNISE then 772 bytes (6,176 bits, bit i in byte i//8 at position i%8): reply 0x5A, routed, pred, cycles (4 bytes little endian). op 0x02 MATMUL: reply 0x5B, cycles (4 bytes), then 256 outputs of 5 bytes (macc as 3 bytes, eacc as 2 bytes, both sign-extended)."""
import sys
NB = 6176
def pack_bits(bits):
    assert len(bits) == NB; out = bytearray(NB // 8)
    for i, b in enumerate(bits):
        if b: out[i // 8] |= 1 << (i % 8)
    return bytes(out)
def recognise(ser, bits):
    ser.write(bytes([0xA5, 0x01]) + pack_bits(bits)); r = ser.read(7)
    if len(r) != 7 or r[0] != 0x5A: raise IOError("bad reply %r" % r)
    return {"routed": r[1], "pred": r[2], "cycles": int.from_bytes(r[3:7], "little")}
def _s(v, n): return v - (1 << n) if v >> (n - 1) else v
def matmul(ser):
    ser.write(bytes([0xA5, 0x02])); h = ser.read(5)
    if len(h) != 5 or h[0] != 0x5B: raise IOError("bad header %r" % h)
    body = ser.read(256 * 5); out = [(_s(int.from_bytes(body[5 * k:5 * k + 3], "little"), 24), _s(int.from_bytes(body[5 * k + 3:5 * k + 5], "little"), 16)) for k in range(256)]
    return int.from_bytes(h[1:5], "little"), out
if __name__ == "__main__":
    class Fake:                                    # protocol self-check without a board
        def __init__(self): self.sent = b""; self.reply = bytes([0x5A, 1, 7]) + (1234).to_bytes(4, "little")
        def write(self, b): self.sent += b
        def read(self, n): r, self.reply = self.reply[:n], self.reply[n:]; return r
    f = Fake(); bits = [1 if i % 3 == 0 else 0 for i in range(NB)]; r = recognise(f, bits)
    assert f.sent[:2] == bytes([0xA5, 1]) and len(f.sent) == 774 and f.sent[2] == 0b01001001 and r == {"routed": 1, "pred": 7, "cycles": 1234}; print("protocol self-check passed")
    if len(sys.argv) > 1 and sys.argv[1] != "--check":
        import serial; ser = serial.Serial(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 115200, timeout=10); print(matmul(ser)[0], "cycles for the matrix product")
