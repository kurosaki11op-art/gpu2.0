# klayout -b -r render.py -rd gds=... -rd png=... [-rd box=x1,y1,x2,y2 (um)] [-rd w=2400 -rd h=1400]
import pya
PDK = '/opt/eda_pdk/share/pdk/sky130A'
view = pya.LayoutView()
view.load_layout(gds, True)
view.load_layer_props(f'{PDK}/libs.tech/klayout/tech/sky130A.lyp')
view.max_hier()
view.set_config('background-color', '#ffffff')
view.set_config('grid-visible', 'false')
view.set_config('text-visible', 'false')
if 'box' in globals():
    x1, y1, x2, y2 = [float(v) for v in box.split(',')]
    view.zoom_box(pya.DBox(x1, y1, x2, y2))
else:
    view.zoom_fit()
W = int(globals().get('w', 2400)); H = int(globals().get('h', 1400))
view.save_image(png, W, H)
print('saved', png)
