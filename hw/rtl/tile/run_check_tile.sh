#!/bin/sh
# L tile checks: (1) 4x4 mesh with the behavioural memory replaying real lookups, (2) one tile with the OpenRAM macros (byte masks, banks, saturation).
cd "$(dirname "$0")"
MAC=/opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8.v
iverilog -g2012 -o /tmp/t_mesh.vvp -Ptb_mesh.ACTIVE=16 -Ptb_mesh.NTOK=50 l_router.v l_tile.v sram_wrap.v tb_mesh.v 2>/dev/null && vvp -n /tmp/t_mesh.vvp | grep MESH
iverilog -g2012 -DOPENRAM -o /tmp/t_open.vvp l_router.v l_tile.v sram_wrap.v tb_tile_openram.v ../cortex/cortex_cg.v $MAC && vvp -n /tmp/t_open.vvp | grep -E "OPENRAM|MISMATCH"
