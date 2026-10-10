"""The synthesized netlist has bit-split ports (splitnets -ports). Rename its module to spark_core_gl and
generate a spark_core wrapper with the original bus ports, so the RTL testbench drives the gate-level netlist."""
import re, sys
src, out_net, out_wrap = sys.argv[1], sys.argv[2], sys.argv[3]
s = open(src).read()
s = s.replace('module spark_core(', 'module spark_core_gl(', 1)
open(out_net, 'w').write(s)
hdr = s[:s.index(');') + 2]
body_decl = s
ports = {}
for m in re.finditer(r'^\s*(input|output)\s+(?:wire\s+)?(?:\[(\d+):(\d+)\]\s+)?(\\?\S+?)\s*;', body_decl, re.M):
    d, hi, lo, name = m.group(1), m.group(2), m.group(3), m.group(4)
    mb = re.match(r'\\(\w+)\[(\d+)\]$', name)
    if mb:
        base, bit = mb.group(1), int(mb.group(2))
        e = ports.setdefault(base, [d, set()]); e[1].add(bit)
    else:
        if hi is not None:
            ports[name] = [d, set(range(int(lo), int(hi) + 1))]
        else:
            ports.setdefault(name, [d, set()])
lines = ['module spark_core #(parameter P = 8, parameter CTX = 3, parameter EMB_HEX = "", parameter EMB1_HEX = "", parameter EMB2_HEX = "",',
         '  parameter TH0_HEX = "", parameter TH1_HEX = "", parameter W0_HEX = "", parameter W1_HEX = "", parameter W2_HEX = "", parameter W3_HEX = "") (']
decl, conns = [], []
for name, (d, bits) in ports.items():
    w = f'[{max(bits)}:0] ' if bits else ''
    decl.append(f'  {d} {w}{name}')
    if bits:
        conns += [f'    .\\{name}[{b}] ({name}[{b}])' for b in sorted(bits)]
    else:
        conns.append(f'    .{name}({name})')
lines.append(',\n'.join(decl) + ');')
lines.append('  spark_core_gl u (\n' + ',\n'.join(conns) + ');')
lines.append('endmodule')
open(out_wrap, 'w').write('\n'.join(lines) + '\n')
print(len(ports), 'ports')
