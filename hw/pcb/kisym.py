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
    """Symbol definition text; `lib` is a KiCad library name or a path to a .kicad_sym file.
    Derived symbols ((extends "base")) are flattened into a complete definition, as KiCad does in schematics."""
    path = lib if lib.endswith('.kicad_sym') else f'{LIB}/{lib}.kicad_sym'
    t = open(path).read()
    i = t.index(f'(symbol "{name}"')
    d = block(t, i)
    m = re.match(r'\(symbol "[^"]+" \(extends "([^"]+)"\)', d)
    if m:
        base = symbol_def(lib, m.group(1))
        base = base.replace(f'(symbol "{m.group(1)}"', f'(symbol "{name}"', 1)
        base = base.replace(f'(symbol "{m.group(1)}_', f'(symbol "{name}_')
        for prop in ('Value', 'Footprint', 'Datasheet', 'Description'):
            cm = re.search(rf'\(property "{prop}" "([^"]*)"', d)
            if cm:
                base = re.sub(rf'(\(property "{prop}" )"[^"]*"', lambda x: x.group(1) + '"' + cm.group(1) + '"', base, count=1)
        return base
    return d

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
