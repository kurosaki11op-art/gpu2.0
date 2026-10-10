"""Photo-style preview of the routed board (top and bottom), drawn from the real KiCad PCB data:
every layer is converted to polygons by KiCad itself (BOARD.ConvertBrdLayerToPolygonalContours)."""
import os
os.environ.setdefault('KICAD7_FOOTPRINT_DIR', '/usr/share/kicad/footprints')
import pcbnew
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Circle, Rectangle
from matplotlib.path import Path

b = pcbnew.LoadBoard('spark_chip_board.kicad_pcb')
mm = pcbnew.ToMM
from design import W, H
MASK, COPPER, PAD, SILK, HOLE = '#1E5B3A', '#2E7A4C', '#D9AE52', '#F2F2EC', '#1A1D22'


def layer_patch(ax, layer, color):
    ps = pcbnew.SHAPE_POLY_SET()
    b.ConvertBrdLayerToPolygonalContours(layer, ps)
    for i in range(ps.OutlineCount()):
        rings = [ps.Outline(i)] + [ps.Hole(i, j) for j in range(ps.HoleCount(i))]
        verts, codes = [], []
        for r in rings:
            pts = [(mm(r.CPoint(k).x), mm(r.CPoint(k).y)) for k in range(r.PointCount())]
            if len(pts) < 3:
                continue
            verts += pts + [pts[0]]; codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 1) + [Path.CLOSEPOLY]
        if verts:
            ax.add_patch(PathPatch(Path(verts, codes), fc=color, ec='none'))


def draw(side, path):
    cu, mask, silk = ((pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_SilkS) if side == 'top'
                      else (pcbnew.B_Cu, pcbnew.B_Mask, pcbnew.B_SilkS))
    fig, ax = plt.subplots(figsize=(12, 12 * H / W), dpi=150)
    fig.patch.set_facecolor('#F3F0E8')
    ax.add_patch(Rectangle((0, 0), W, H, fc=MASK, ec='#123522', lw=1.5))
    layer_patch(ax, cu, COPPER)       # copper under solder mask
    layer_patch(ax, mask, PAD)        # mask openings = exposed, gold-plated pads
    layer_patch(ax, silk, SILK)       # silkscreen
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetDrillSizeX() > 0:
                ax.add_patch(Circle((mm(pad.GetPosition().x), mm(pad.GetPosition().y)), mm(pad.GetDrillSizeX()) / 2, fc=HOLE, ec='none'))
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            ax.add_patch(Circle((mm(t.GetPosition().x), mm(t.GetPosition().y)), mm(t.GetDrillValue()) / 2, fc=HOLE, ec='none'))
    ax.set_xlim(-1, W + 1); ax.set_ylim(H + 1, -1); ax.set_aspect('equal'); ax.axis('off')
    if side == 'bottom':
        ax.invert_xaxis()
    fig.subplots_adjust(0, 0, 1, 1); fig.savefig(path, facecolor=fig.get_facecolor()); plt.close(fig)


draw('top', 'img/pcb_top_render.png')
draw('bottom', 'img/pcb_bottom_render.png')
print('rendered')
