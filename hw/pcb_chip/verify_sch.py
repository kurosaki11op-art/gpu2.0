"""Schematic verification (KiCad 7 has no CLI ERC): parse the netlist KiCad itself exported from the
schematic and check (1) every pin is on exactly the net the design intends, (2) electrical rules."""
import re, sys
from design import PARTS, PWR_FLAGS

net_txt = open('spark_chip_board.net').read()
nodes = {}   # (ref, pin) -> (net, pintype)
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', net_txt, re.S):
    name = m.group(1).lstrip('/')
    for n in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "[^"]*"\))? \(pintype "([^"]+)"\)', m.group(2)):
        nodes[(n.group(1), n.group(2))] = (name, n.group(3))

errors, checks = [], 0
# documented waivers: CH340C V3 (power_out) must tie to VCC=3V3 when the chip runs from 3.3 V (CH340 datasheet)
WAIVE_DRIVERS = {('+3V3', ('U2', '4'))}
# 1. connectivity parity with the design
for ref, (_, _, _, pinnets) in PARTS.items():
    for pin, want in pinnets.items():
        checks += 1
        got = nodes.get((ref, pin))
        if got is None:
            errors.append(f'{ref}.{pin}: missing from KiCad netlist'); continue
        if want is None and not got[0].startswith('unconnected-'):
            errors.append(f'{ref}.{pin}: should be unconnected, is on {got[0]}')
        elif want is not None and got[0] != want:
            errors.append(f'{ref}.{pin}: on {got[0]}, design says {want}')
extra = [k for k in nodes if k[0] not in PARTS]
if extra:
    errors.append(f'unexpected pins in netlist: {extra[:5]}')
# 2. electrical rules
nets = {}
for (ref, pin), (net, typ) in nodes.items():
    nets.setdefault(net, []).append((ref, pin, typ))
for net, members in nets.items():
    if net.startswith('unconnected-'):
        continue
    checks += 1
    if len({m[0] for m in members}) < 2:
        errors.append(f'net {net}: only one component ({members})')
    types = [m[2] for m in members]
    if any(t == 'power_in' for t in types) and net not in PWR_FLAGS and 'power_out' not in types:
        errors.append(f'net {net}: power input pins but no power source / PWR_FLAG')
    drivers = [(m[0], m[1]) for m in members if m[2] in ('output', 'power_out') and (net, (m[0], m[1])) not in WAIVE_DRIVERS]
    if len(drivers) > 1:
        errors.append(f'net {net}: more than one driver')
    if any(t == 'input' for t in types) and not any(t in ('output', 'bidirectional', 'passive', 'power_out', 'tri_state', 'open_collector') for t in types):
        errors.append(f'net {net}: input pins with nothing driving them')
print(f'schematic check: {len(nodes)} pins on {len(nets)} nets, {checks} checks, {len(errors)} errors')
for e in errors:
    print('  ERROR', e)
sys.exit(1 if errors else 0)
