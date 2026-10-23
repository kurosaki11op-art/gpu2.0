"""Host side of tile_board_top (Tang Nano 20K, UART 115200 8N1). usage: python tile_host.py /dev/ttyUSB1  (or COMx)
Sends an update then a lookup to word 5 and prints the 16-bit word read back; needs `pip install pyserial`.
Flit 72 bit = {type[1:0], dst[5:0], src[5:0], tag[7:0], addr[17:0], data[31:0]}; type 0 lookup, 2 posted add."""
import sys, serial
def flit(ty, addr, data, tag=1): return ((ty << 70) | (tag << 56) | (addr << 32) | data).to_bytes(9, "big")
s = serial.Serial(sys.argv[1], 115200, timeout=2)
s.write(b"E"); assert s.read(1) == b"\x5a", "no ping reply"
s.write(b"T" + flit(2, 5, 0x0102)); assert s.read(1) == b"K"
s.write(b"T" + flit(0, 5, 0)); r = s.read(9); print("response flit", r.hex(), "word", r[-2:].hex())
