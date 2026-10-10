# klayout -b -r def2gds.py -rd def=... -rd out=...   (KLayout batch mode)
# Reads the routed DEF with the SKY130 technology LEFs and replaces every cell abstract with its real GDS layout:
# sky130_fd_sc_hd standard cells and the OpenRAM SRAM macros.
import pya
PDK = '/opt/eda_pdk/share/pdk/sky130A'
SRAM = '/opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8'
opt = pya.LoadLayoutOptions()
cfg = opt.lefdef_config
cfg.map_file = f'{PDK}/libs.tech/klayout/tech/sky130A.map'
cfg.lef_files = [f'{PDK}/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef',
                 f'{PDK}/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef', SRAM + '.lef']
cfg.macro_layout_files = [f'{PDK}/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds', SRAM + '.gds']
cfg.macro_resolution_mode = 2          # always use the GDS layout of a macro
ly = pya.Layout()
ly.read(def_file if 'def_file' in globals() else globals()['def'], opt)
top = ly.top_cell()
print('top cell', top.name, 'cells', ly.cells(), 'bbox um', top.dbbox())
ly.write(out)
