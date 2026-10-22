# usage: python3 mkgds.py <routed.def> <outdir>   -> outdir/tile_i_j.gds (3x2 tiles, 20 um halo), SRAM macro replaced by its LEF pins/obstructions
import sys, re, os, klayout.db as db
DEF, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
PDK='/opt/eda_pdk/share/pdk/sky130A'; M='/opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8'
lay={"met1":(68,20),"met2":(69,20),"met3":(70,20),"met4":(71,20)}
rects=[];cur=None
for line in open(M+'.lef'):
    m=re.match(r"\s*LAYER\s+(\w+)\s*;",line)
    if m: cur=m.group(1); continue
    m=re.match(r"\s*RECT\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*;",line)
    if m and cur in lay: rects.append((cur,*[float(v) for v in m.groups()]))
s=db.Layout(); sc=s.create_cell("sky130_sram_2kbyte_1rw1r_32x512_8")
for n,x1,y1,x2,y2 in rects: sc.shapes(s.layer(*lay[n])).insert(db.DBox(x1,y1,x2,y2))
s.write(OUT+"/sram_standin.gds")
opt=db.LoadLayoutOptions(); cfg=opt.lefdef_config
cfg.map_file=f'{PDK}/libs.tech/klayout/tech/sky130A.map'
cfg.lef_files=[f'{PDK}/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef',f'{PDK}/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef',M+'.lef']
cfg.macro_layout_files=[f'{PDK}/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds', OUT+"/sram_standin.gds"]
cfg.macro_resolution_mode=2
ly=db.Layout(); ly.read(DEF,opt); top=ly.top_cell(); print("top",top.name,"cells",ly.cells(),top.dbbox(),flush=True)
ly.write(OUT+"/chip.gds")
W,H=7500,6200; nx,ny=3,2; halo=20
for i in range(nx):
    for j in range(ny):
        x0=max(0,i*W/nx-halo); x1=min(W,(i+1)*W/nx+halo); y0=max(0,j*H/ny-halo); y1=min(H,(j+1)*H/ny+halo)
        b=db.Box(int(x0/ly.dbu),int(y0/ly.dbu),int(x1/ly.dbu),int(y1/ly.dbu))
        t=db.Layout(); t.dbu=ly.dbu
        for li in ly.layer_indexes(): t.insert_layer(ly.get_info(li))
        ci=ly.clip_into(top.cell_index(),t,b); t.cell(ci).name="tile_%d_%d"%(i,j)
        t.write(f"{OUT}/tile_{i}_{j}.gds"); print("tile",i,j,flush=True)
