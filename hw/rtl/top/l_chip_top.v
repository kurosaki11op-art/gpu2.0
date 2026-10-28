// L chip top, dispatcher over the layers (28 Oct 2026, SIMULATED): one command interface; op 0 = recognise (L Cortex stage 1, L Deep woken only when the margin is small),
// op 1 = numeric job (L Forge matrix product). Activity flags show which layer is awake: the flags are what a power controller would use to gate clocks and memory banks.
module l_chip_top (
    input clk, input rst, input op, input start, input wr_en, input [12:0] wr_addr, input wr_bit,
    output busy, output done, output routed, output [3:0] pred, output [199:0] scores_flat,
    output cortex_active, output deep_active, output forge_active,
    input [7:0] c_raddr, output signed [16:0] c_macc, output signed [11:0] c_eacc, output [31:0] cycles);
    wire sys_busy, sys_done, s2, mm_busy, mm_done; wire [31:0] sys_cyc, mm_cyc;
    l_system sys (.clk(clk), .rst(rst), .wr_en(wr_en), .wr_addr(wr_addr), .wr_bit(wr_bit), .start(start && !op), .busy(sys_busy), .done(sys_done), .routed(routed), .pred(pred), .scores_flat(scores_flat), .cycles(sys_cyc), .s2_active(s2));
    forge_tile_mm #(16, 16, 8) mm (.clk(clk), .rst(rst), .start(start && op), .busy(mm_busy), .done(mm_done), .cycles(mm_cyc), .c_raddr(c_raddr), .c_macc(c_macc), .c_eacc(c_eacc));
    assign cycles = op ? mm_cyc : sys_cyc;
    assign busy = sys_busy | mm_busy; assign done = sys_done | mm_done;
    assign cortex_active = sys_busy && !s2; assign deep_active = s2; assign forge_active = mm_busy;
endmodule
