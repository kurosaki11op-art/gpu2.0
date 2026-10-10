"""Tiny helpers: extract a symbol definition from a KiCad 7 .kicad_sym library and list its pins."""
import re
LIB = '/usr/share/kicad/symbols'

def block(text, start):
    depth = 0; i = start; instr = False
    while True:
        ch = text[i]
        if ch == '"' and text[i - 1] != '\\': instr = not instr
        elif not instr:
            if ch == '(': depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0: return text[start:i + 1]
        i += 1

def symbol_def(lib, name):
    t = open(f'{LIB}/{lib}.kicad_sym').read()
    i = t.index(f'(symbol "{name}"')
    return block(t, i)

def pins(sdef):
    out = []
    for m in re.finditer(r'\(pin (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', sdef):
        b = block(sdef, m.start())
        name = re.search(r'\(name "([^"]*)"', b).group(1); num = re.search(r'\(number "([^"]*)"', b).group(1)
        hidden = ' hide' in b.split('(at')[0]
        out.append(dict(type=m.group(1), x=float(m.group(3)), y=float(m.group(4)), rot=float(m.group(5)), name=name, num=num, hidden=hidden))
    return out

if __name__ == '__main__':
    import sys
    for spec in sys.argv[1:]:
        lib, name = spec.split(':')
        d = symbol_def(lib, name)
        print(spec, 'extends' if '(extends' in d[:200] else '', re.search(r'"Footprint" "([^"]*)"', d).group(1) if '"Footprint"' in d else '')
        for p in pins(d): print('   ', p['num'], p['name'], p['type'], p['x'], p['y'], p['rot'], 'H' if p['hidden'] else '')
