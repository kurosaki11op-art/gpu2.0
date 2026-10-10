"""Write spark_meter.kicad_sch (KiCad 7) from design.py: symbols from the official KiCad libraries,
every connected pin gets a short wire stub and a net label, unused pins get no-connect flags."""
import uuid, json
from design import PARTS, PWR_FLAGS
from kisym import symbol_def, pins

U = lambda: str(uuid.uuid4())
ROOT = U()
PROJECT = 'spark_meter'
STUB = 2.54
LAYOUT = {  # schematic placement (mm, on the 2.54 grid), A3 sheet
    'J1': (45.72, 71.12), 'J2': (45.72, 162.56), 'RS1': (127.0, 45.72), 'U1': (139.7, 96.52), 'C4': (101.6, 45.72),
    'C3': (152.4, 45.72), 'R8': (177.8, 45.72), 'D1': (203.2, 45.72), 'R1': (101.6, 132.08), 'R2': (127.0, 132.08),
    'R3': (152.4, 132.08), 'R4': (177.8, 132.08), 'U2': (215.9, 96.52), 'C1': (101.6, 177.8), 'C2': (127.0, 177.8),
    'R5': (152.4, 177.8), 'R6': (177.8, 177.8), 'R7': (203.2, 177.8), 'J3': (279.4, 45.72), 'J4': (279.4, 96.52),
    'J5': (279.4, 152.4), 'TP1': (330.2, 45.72), 'TP2': (355.6, 45.72), 'TP3': (381.0, 45.72),
    'H1': (330.2, 228.6), 'H2': (345.44, 228.6), 'H3': (360.68, 228.6), 'H4': (375.92, 228.6),
}
FLAG_POS = [(330.2, 101.6), (355.6, 101.6), (381.0, 101.6), (330.2, 134.62)]


def r(v):
    return round(v, 2)


def stub_dir(rot):  # direction away from the symbol body, schematic coordinates (y down)
    return {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[int(rot) % 360]


def main():
    libs, items, symbols = {}, [], []
    netmap = {}  # for parity checks: (ref, pin) -> net

    def place(ref, lib_id, value, fp, pinnets, at, sym_uuid):
        lib, name = lib_id.split(':')
        sdef = symbol_def(lib, name)
        libs[lib_id] = sdef.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
        X, Y = at
        plist = pins(sdef)
        seen = {}
        for p in plist:
            px, py = r(X + p['x']), r(Y - p['y'])
            net = pinnets.get(p['num'], None) if ref[0] != '#' else pinnets.get('1')
            netmap[(ref, p['num'])] = net
            if (px, py) in seen:
                continue
            seen[(px, py)] = net
            if net is None:
                items.append(f'(no_connect (at {px} {py}) (uuid {U()}))')
                continue
            dx, dy = stub_dir(p['rot'])
            ex, ey = r(px + dx * STUB), r(py + dy * STUB)
            items.append(f'(wire (pts (xy {px} {py}) (xy {ex} {ey})) (stroke (width 0) (type default)) (uuid {U()}))')
            ang = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[(dx, dy)]
            just = 'right' if ang == 180 else 'left'
            items.append(f'(label "{net}" (at {ex} {ey} {ang}) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid {U()}))')
        hide = ' hide' if ref[0] == '#' else ''
        pin_entries = ' '.join(f'(pin "{p["num"]}" (uuid {U()}))' for p in plist)
        symbols.append(
            f'(symbol (lib_id "{lib_id}") (at {X} {Y} 0) (unit 1) (in_bom {"no" if ref[0] in "#H" else "yes"}) (on_board {"no" if ref[0] == "#" else "yes"}) (dnp no) (uuid {sym_uuid})\n'
            f'  (property "Reference" "{ref}" (at {r(X + 3)} {r(Y - 6)} 0) (effects (font (size 1.27 1.27)) (justify left){hide}))\n'
            f'  (property "Value" "{value}" (at {r(X + 3)} {r(Y + 8)} 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
            f'  (property "Footprint" "{fp}" (at {X} {Y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'  (property "Datasheet" "~" (at {X} {Y} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'  {pin_entries}\n'
            f'  (instances (project "{PROJECT}" (path "/{ROOT}" (reference "{ref}") (unit 1)))))')

    uuids = {}
    for ref, (lib_id, value, fp, pinnets) in PARTS.items():
        uuids[ref] = U()
        place(ref, lib_id, value, fp, pinnets, LAYOUT[ref], uuids[ref])
    for i, net in enumerate(PWR_FLAGS):
        place(f'#FLG0{i + 1}', 'power:PWR_FLAG', 'PWR_FLAG', '', {'1': net}, FLAG_POS[i], U())

    text = [f'(kicad_sch (version 20230121) (generator eeschema)',
            f'  (uuid {ROOT})', '  (paper "A3")',
            '  (title_block (title "SPARK power-measurement board") (date "2026-10-10") (rev "0.1") (company "Team L Lawliet - CKCET")'
            ' (comment 1 "Inline USB-C power meter for the SPARK FPGA prototype") (comment 2 "INA219 shunt monitor + LM75 + DS18B20 probe header + ESP32 header"))',
            '  (lib_symbols', *['    ' + d for d in libs.values()], '  )',
            *['  ' + it for it in items], *['  ' + s for s in symbols],
            '  (sheet_instances (path "/" (page "1")))', ')']
    open(f'{PROJECT}.kicad_sch', 'w').write('\n'.join(text) + '\n')
    json.dump({'root': ROOT, 'symbols': uuids, 'pins': {f'{k[0]}:{k[1]}': v for k, v in netmap.items() if k[0][0] != '#'}},
              open('sch_links.json', 'w'), indent=1)
    print('schematic written:', len(PARTS), 'parts,', len(items), 'wires/labels/no-connects')


if __name__ == '__main__':
    main()
