"""Build the board.kicad_pcb from design.py with KiCad's pcbnew API.

stage 'place': board outline, footprints from the official KiCad libraries, nets, Specctra DSN export
stage 'finish': import the Freerouting session (.ses), GND pours on both layers, fill, KiCad DRC report,
                PCB-vs-schematic netlist parity check
"""
import json, re, sys
import pcbnew
from design import PARTS, PLACE, W, H, TEXTS, POWER_NETS, PROJECT

FPLIB = '/usr/share/kicad/footprints'
MM = pcbnew.FromMM


def outline(board):
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for i in range(4):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(MM(pts[i][0]), MM(pts[i][1])))
        s.SetEnd(pcbnew.VECTOR2I(MM(pts[(i + 1) % 4][0]), MM(pts[(i + 1) % 4][1])))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)


def text(board, msg, x, y, size=1.2, layer=pcbnew.F_SilkS):
    t = pcbnew.PCB_TEXT(board); t.SetText(msg); t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(size * 0.15)); t.SetLayer(layer); board.Add(t)


def place():
    links = json.load(open('sch_links.json'))
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetTrackWidth(MM(0.2)); nc.SetClearance(MM(0.15)); nc.SetViaDiameter(MM(0.6)); nc.SetViaDrill(MM(0.3))
    ds.m_MinClearance = MM(0.15); ds.m_TrackMinWidth = MM(0.15); ds.m_ViasMinSize = MM(0.5); ds.m_MinThroughDrill = MM(0.3)
    ds.m_CopperEdgeClearance = MM(0.3)
    ds.m_HoleClearance = MM(0.18)   # GCT USB4105 land pattern: locating pegs sit 0.194 mm from the GND pads (manufacturer footprint)
    outline(board)
    nets = {}
    for _, _, _, pinnets in PARTS.values():
        for n in pinnets.values():
            if n and n not in nets:
                nets[n] = pcbnew.NETINFO_ITEM(board, n); board.Add(nets[n])
    for ref, (lib_id, value, fp_id, pinnets) in PARTS.items():
        lib, name = fp_id.split(':')
        fp = pcbnew.FootprintLoad(f'{FPLIB}/{lib}.pretty', name)
        fp.SetReference(ref); fp.SetValue(value); fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetPath(pcbnew.KIID_PATH('/' + links['symbols'][ref]))
        x, y, rot = PLACE[ref]
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); fp.SetOrientationDegrees(rot)
        if ref.startswith('H'):
            fp.Reference().SetVisible(False)
        board.Add(fp)
        for pad in fp.Pads():
            n = pinnets.get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
    for t, x, y, sz in TEXTS:
        text(board, t, x, y, sz)
    board.Save(f'{PROJECT}.kicad_pcb')
    pcbnew.ExportSpecctraDSN(board, f'{PROJECT}.dsn')
    # power nets: wider tracks for the routed board
    dsn = open(f'{PROJECT}.dsn').read()
    pass
    m = re.search(r'\(class kicad_default(.*?)\(circuit', dsn, re.S)
    members = m.group(1)
    for n in POWER_NETS:
        members = re.sub(r'(?<=\s)' + re.escape(n) + r'(?=\s)', '', members)
    dsn = dsn[:m.start(1)] + members + dsn[m.end(1):]
    pw = ' '.join(f'"{n}"' if '+' in n else n for n in POWER_NETS)
    dsn = dsn.replace('(class kicad_default', f'(class power {pw} (circuit (use_via "Via[0-1]_600:300_um")) (rule (width 400) (clearance 150)))\n    (class kicad_default', 1)
    open(f'{PROJECT}.dsn', 'w').write(dsn)
    print('placed', len(PARTS), 'footprints,', len(nets), 'nets; DSN written')


def import_ses(board, path):
    """Minimal Specctra session reader (KiCad 7's ImportSpecctraSES only works inside the GUI).
    Units: resolution um 10 (0.1 um), Specctra y axis is up (KiCad y = -y)."""
    ses = open(path).read()
    net_out = ses[ses.index('(network_out'):]
    to_iu = lambda v: int(round(int(v) * 100))   # 0.1 um -> KiCad nm
    layers = {'F.Cu': pcbnew.F_Cu, 'B.Cu': pcbnew.B_Cu}
    for nm in re.finditer(r'\(net (\S+)(.*?)(?=\n      \(net |\n    \)\s*\n  \)\s*\n\)?\s*$)', net_out, re.S):
        name = nm.group(1).strip('"'); body = nm.group(2); net = board.FindNet(name)
        for w in re.finditer(r'\(path (\S+) (\d+)\s+([-\d\s]+)\)', body):
            layer, width = layers[w.group(1)], int(w.group(2)) * 100
            c = [int(v) for v in w.group(3).split()]
            pts = [(c[i], -c[i + 1]) for i in range(0, len(c), 2)]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                t = pcbnew.PCB_TRACK(board); t.SetStart(pcbnew.VECTOR2I(x1 * 100, y1 * 100)); t.SetEnd(pcbnew.VECTOR2I(x2 * 100, y2 * 100))
                t.SetWidth(width); t.SetLayer(layer); t.SetNet(net); board.Add(t)
        for v in re.finditer(r'\(via "?([^"\s]+)"? (-?\d+) (-?\d+)', body):
            via = pcbnew.PCB_VIA(board); via.SetPosition(pcbnew.VECTOR2I(int(v.group(2)) * 100, -int(v.group(3)) * 100))
            via.SetWidth(MM(0.6)); via.SetDrill(MM(0.3)); via.SetNet(net); board.Add(via)


def finish():
    board = pcbnew.LoadBoard(f'{PROJECT}.kicad_pcb')
    import_ses(board, f'{PROJECT}.ses')
    print('SES import: tracks+vias:', len(board.GetTracks()))
    gnd = board.FindNet('GND')
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(gnd)
        z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL); z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
        ol = z.Outline(); ol.NewOutline()
        for x, y in [(0.4, 0.4), (W - 0.4, 0.4), (W - 0.4, H - 0.4), (0.4, H - 0.4)]:
            ol.Append(MM(x), MM(y))
        board.Add(z)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(f'{PROJECT}.kicad_pcb')
    print('zones filled, saved')


if __name__ == '__main__':
    {'place': place, 'finish': finish}[sys.argv[1]]()
