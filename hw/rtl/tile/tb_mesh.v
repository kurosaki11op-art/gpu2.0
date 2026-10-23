// 4 x 4 mesh of L tiles. Each active client runs token streams from trace.hex: per token, 8 sequential steps, each step sends 6 lookups
// (one per context order) to the owning tiles and waits for all 6 replies. owner tile = slot mod 16, local address = slot / 16.
// Checks every reply against the value the owning tile's memory must hold, prints cycles per token and per lookup.
`timescale 1ns/1ps
module tb_mesh;
    parameter NX = 4, NY = 4, NT = NX * NY, FW = 72, NTOK = 200, ACTIVE = 1;     // ACTIVE = number of client tiles running streams
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg [31:0] trace [0:NTOK * 48 * ACTIVE - 1];
    wire [FW-1:0] c_rsp_f [0:NT-1]; wire c_rsp_v [0:NT-1]; reg c_rsp_r [0:NT-1];
    reg c_req_v [0:NT-1]; reg [FW-1:0] c_req_f [0:NT-1]; wire c_req_r [0:NT-1];
    // links: for each tile, 4 neighbour ports of each network
    wire [4*FW-1:0] rq_o [0:NT-1], rp_o [0:NT-1], rq_i [0:NT-1], rp_i [0:NT-1];
    wire [3:0] rq_ov [0:NT-1], rp_ov [0:NT-1], rq_iv [0:NT-1], rp_iv [0:NT-1], rq_or [0:NT-1], rp_or [0:NT-1], rq_ir [0:NT-1], rp_ir [0:NT-1];
    genvar x, y;
    generate for (y = 0; y < NY; y = y + 1) for (x = 0; x < NX; x = x + 1) begin : t
        localparam id = y * NX + x;
        // neighbour wiring: port 0 = north, 1 = east, 2 = south, 3 = west
        assign rq_i[id][0*FW +: FW] = (y > 0) ? rq_o[id - NX][2*FW +: FW] : {FW{1'b0}};
        assign rq_iv[id][0] = (y > 0) ? rq_ov[id - NX][2] : 1'b0;      assign rq_or[id][0] = (y > 0) ? rq_ir[id - NX][2] : 1'b1;
        assign rq_i[id][1*FW +: FW] = (x < NX - 1) ? rq_o[id + 1][3*FW +: FW] : {FW{1'b0}};
        assign rq_iv[id][1] = (x < NX - 1) ? rq_ov[id + 1][3] : 1'b0;  assign rq_or[id][1] = (x < NX - 1) ? rq_ir[id + 1][3] : 1'b1;
        assign rq_i[id][2*FW +: FW] = (y < NY - 1) ? rq_o[id + NX][0*FW +: FW] : {FW{1'b0}};
        assign rq_iv[id][2] = (y < NY - 1) ? rq_ov[id + NX][0] : 1'b0; assign rq_or[id][2] = (y < NY - 1) ? rq_ir[id + NX][0] : 1'b1;
        assign rq_i[id][3*FW +: FW] = (x > 0) ? rq_o[id - 1][1*FW +: FW] : {FW{1'b0}};
        assign rq_iv[id][3] = (x > 0) ? rq_ov[id - 1][1] : 1'b0;       assign rq_or[id][3] = (x > 0) ? rq_ir[id - 1][1] : 1'b1;
        assign rp_i[id][0*FW +: FW] = (y > 0) ? rp_o[id - NX][2*FW +: FW] : {FW{1'b0}};
        assign rp_iv[id][0] = (y > 0) ? rp_ov[id - NX][2] : 1'b0;      assign rp_or[id][0] = (y > 0) ? rp_ir[id - NX][2] : 1'b1;
        assign rp_i[id][1*FW +: FW] = (x < NX - 1) ? rp_o[id + 1][3*FW +: FW] : {FW{1'b0}};
        assign rp_iv[id][1] = (x < NX - 1) ? rp_ov[id + 1][3] : 1'b0;  assign rp_or[id][1] = (x < NX - 1) ? rp_ir[id + 1][3] : 1'b1;
        assign rp_i[id][2*FW +: FW] = (y < NY - 1) ? rp_o[id + NX][0*FW +: FW] : {FW{1'b0}};
        assign rp_iv[id][2] = (y < NY - 1) ? rp_ov[id + NX][0] : 1'b0; assign rp_or[id][2] = (y < NY - 1) ? rp_ir[id + NX][0] : 1'b1;
        assign rp_i[id][3*FW +: FW] = (x > 0) ? rp_o[id - 1][1*FW +: FW] : {FW{1'b0}};
        assign rp_iv[id][3] = (x > 0) ? rp_ov[id - 1][1] : 1'b0;       assign rp_or[id][3] = (x > 0) ? rp_ir[id - 1][1] : 1'b1;
        l_tile #(x, y, 1 << 18, FW) tile (.clk(clk), .rst(rst),
            .cl_req_valid(c_req_v[id]), .cl_req_flit(c_req_f[id]), .cl_req_ready(c_req_r[id]),
            .cl_rsp_valid(c_rsp_v[id]), .cl_rsp_flit(c_rsp_f[id]), .cl_rsp_ready(c_rsp_r[id]),
            .rq_in_flit(rq_i[id]), .rq_in_valid(rq_iv[id]), .rq_in_ready(rq_ir[id]), .rq_out_flit(rq_o[id]), .rq_out_valid(rq_ov[id]), .rq_out_ready(rq_or[id]),
            .rp_in_flit(rp_i[id]), .rp_in_valid(rp_iv[id]), .rp_in_ready(rp_ir[id]), .rp_out_flit(rp_o[id]), .rp_out_valid(rp_ov[id]), .rp_out_ready(rp_or[id]));
    end endgenerate
    // clients
    integer c, cyc = 0; always @(posedge clk) cyc <= cyc + 1;
    integer tok [0:NT-1], step [0:NT-1], sent [0:NT-1], got [0:NT-1], t0 [0:NT-1]; reg done [0:NT-1];
    integer tok_cycles, lookups, bad, finished, ptr; reg [31:0] slot; reg [FW-1:0] fl; reg [15:0] exp;
    integer tot_tok_cycles = 0, tot_tokens = 0; reg [31:0] dx, dy, sx, sy;
    initial begin
        $readmemh("trace.hex", trace); bad = 0; finished = 0; lookups = 0;
        for (c = 0; c < NT; c = c + 1) begin c_req_v[c] = 0; c_req_f[c] = 0; c_rsp_r[c] = 1; tok[c] = 0; step[c] = 0; sent[c] = 0; got[c] = 0; done[c] = (c >= ACTIVE); end
        repeat (4) @(negedge clk); rst = 0;
        while (finished < ACTIVE) @(negedge clk);
        $display("MESH %0dx%0d active clients %0d tokens each %0d: total cycles %0d, mean cycles per token %0d, lookups %0d, wrong replies %0d", NX, NY, ACTIVE, NTOK, cyc,
                 tot_tok_cycles / tot_tokens, lookups, bad);
        $finish;
    end
    always @(negedge clk) if (!rst) begin
        for (c = 0; c < ACTIVE; c = c + 1) if (!done[c]) begin
            // handshake of this cycle (set at the previous negedge, consumed at the posedge)
            if (c_req_v[c] && c_req_r[c]) begin c_req_v[c] = 0; end
            if (c_rsp_v[c] && c_rsp_r[c]) begin
                got[c] = got[c] + 1; lookups = lookups + 1;
                exp = c_rsp_f[c][49:32] * 40503 + (c_rsp_f[c][49:32] >> 3);                   // what the owning tile's memory holds at that address
                if (c_rsp_f[c][15:0] !== exp) bad = bad + 1;
            end
            if (step[c] == 0 && sent[c] == 0 && got[c] == 0 && tok[c] < NTOK && !c_req_v[c]) t0[c] = cyc;
            // issue the 6 lookups of the current step, one per cycle
            if (sent[c] < 6 && !c_req_v[c] && tok[c] < NTOK) begin
                ptr = ((tok[c] * ACTIVE + c) * 48) + step[c] * 6 + sent[c]; slot = trace[ptr];
                fl = {FW{1'b0}};
                // build flit: dst tile = slot mod 16 as {y, x}, src = this client tile
                fl[71:70] = 2'd0; dx = (slot % 16) % NX; dy = (slot % 16) / NX; fl[69:64] = {dy[2:0], dx[2:0]}; sx = c % NX; sy = c / NX; fl[63:58] = {sy[2:0], sx[2:0]}; fl[57:50] = sent[c]; fl[49:32] = slot / 16; fl[31:0] = 0;
                c_req_f[c] = fl; c_req_v[c] = 1; sent[c] = sent[c] + 1;
            end
            if (got[c] == 6) begin
                got[c] = 0; sent[c] = 0; step[c] = step[c] + 1;
                if (step[c] == 8) begin
                    step[c] = 0; tot_tok_cycles = tot_tok_cycles + (cyc - t0[c]); tot_tokens = tot_tokens + 1; tok[c] = tok[c] + 1; t0[c] = cyc;
                    if (tok[c] == NTOK) begin done[c] = 1; finished = finished + 1; end
                end
            end
        end
    end
endmodule
