"""KiCad DRC (pcbnew.WriteDRCReport, the same engine as the PCB editor) + PCB-vs-schematic netlist parity."""
import os, re, sys
os.environ.setdefault('KICAD7_FOOTPRINT_DIR', '/usr/share/kicad/footprints')
os.environ.setdefault('KICAD7_SYMBOL_DIR', '/usr/share/kicad/symbols')
import pcbnew
b = pcbnew.LoadBoard('spark_meter.kicad_pcb')
pcbnew.WriteDRCReport(b, 'drc.rpt', pcbnew.EDA_UNITS_MILLIMETRES, True)
rpt = open('drc.rpt').read()
errs = len(re.findall(r'Severity: error', rpt)); warns = len(re.findall(r'Severity: warning', rpt))
unc = int(re.search(r'Found (\d+) unconnected', rpt).group(1))
# parity: every PCB pad net vs the netlist KiCad exported from the schematic
net_txt = open('spark_meter.net').read(); sch = {}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', net_txt, re.S):
    for n in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
        sch[(n.group(1), n.group(2))] = m.group(1).lstrip('/')
mism = 0; npads = 0
for fp in b.GetFootprints():
    for p in fp.Pads():
        if not p.GetNumber():
            continue
        npads += 1
        want = sch.get((fp.GetReference(), p.GetNumber()))
        got = p.GetNetname()
        if want is None or want.startswith('unconnected-'):
            want = ''
        if got != want:
            mism += 1; print('  parity mismatch', fp.GetReference(), p.GetNumber(), got, '!=', want)
tracks = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK']; vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
print(f'DRC: {errs} errors, {warns} warnings, {unc} unconnected | parity: {npads} pads, {mism} mismatches | '
      f'{len(tracks)} track segments, {len(vias)} vias, {len(b.GetFootprints())} footprints')
sys.exit(1 if errs or unc or mism else 0)
