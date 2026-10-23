// 4 x 4 mesh of L tiles. Each active client runs token streams from trace.hex: per token, 8 sequential steps, each step sends 6 lookups
// (one per context order) to the owning tiles and waits for all 6 replies. owner tile = slot mod 16, local address = slot / 16.
// Checks every reply against the value the owning tile's memory must hold, prints cycles per token and per lookup.
`timescale 1ns/1ps
module tb_seq;
    parameter NX = 4, NY = 4, NT = NX * NY, FW = 72, NTOK = 20;     // ACTIVE = number of client tiles running streams
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    wire [FW-1:0] c_rsp_f [0:NT-1]; wire c_rsp_v [0:NT-1]; wire c_rsp_r [0:NT-1];
    wire c_req_v [0:NT-1]; wire [FW-1:0] c_req_f [0:NT-1]; wire c_req_r [0:NT-1];
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
        l_tile #(x, y, 18, FW) tile (.clk(clk), .rst(rst),
            .cl_req_valid(c_req_v[id]), .cl_req_flit(c_req_f[id]), .cl_req_ready(c_req_r[id]),
            .cl_rsp_valid(c_rsp_v[id]), .cl_rsp_flit(c_rsp_f[id]), .cl_rsp_ready(c_rsp_r[id]),
            .rq_in_flit(rq_i[id]), .rq_in_valid(rq_iv[id]), .rq_in_ready(rq_ir[id]), .rq_out_flit(rq_o[id]), .rq_out_valid(rq_ov[id]), .rq_out_ready(rq_or[id]),
            .rp_in_flit(rp_i[id]), .rp_in_valid(rp_iv[id]), .rp_in_ready(rp_ir[id]), .rp_out_flit(rp_o[id]), .rp_out_valid(rp_ov[id]), .rp_out_ready(rp_or[id]));
    end endgenerate

    // tile 0's client is the sequencer; the other tiles' clients are idle
    genvar q;
    generate for (q = 1; q < NT; q = q + 1) begin : idle
        assign c_req_v[q] = 1'b0; assign c_req_f[q] = {FW{1'b0}}; assign c_rsp_r[q] = 1'b1;
    end endgenerate
    reg start = 0; reg [7:0] tgt, b1, b2, b3, b4, b5; wire busy, done, sv; wire signed [15:0] ss; wire sb;
    l_seq #(0, 0, NX, FW) seq (.clk(clk), .rst(rst), .start(start), .tgt(tgt), .b1(b1), .b2(b2), .b3(b3), .b4(b4), .b5(b5), .busy(busy), .done(done),
        .step_valid(sv), .step_s(ss), .step_bit(sb), .req_valid(c_req_v[0]), .req_flit(c_req_f[0]), .req_ready(c_req_r[0]),
        .rsp_valid(c_rsp_v[0]), .rsp_flit(c_rsp_f[0]), .rsp_ready(c_rsp_r[0]));
    reg [7:0] text [0:NTOK + 8]; integer t, f, cyc = 0, t0; always @(posedge clk) cyc <= cyc + 1;
    always @(posedge clk) if (sv) $fwrite(f, "%0d %0d\n", ss, sb);
    initial begin
        $readmemh("text.hex", text); f = $fopen("seq_out.txt", "w");
        repeat (4) @(negedge clk); rst = 0; repeat (4) @(negedge clk);
        for (t = 0; t < NTOK; t = t + 1) begin
            tgt = text[t]; b1 = (t >= 1) ? text[t-1] : 8'hFF; b2 = (t >= 2) ? text[t-2] : 8'hFF; b3 = (t >= 3) ? text[t-3] : 8'hFF; b4 = (t >= 4) ? text[t-4] : 8'hFF; b5 = (t >= 5) ? text[t-5] : 8'hFF;
            @(negedge clk); start = 1; if (t == 0) t0 = cyc; @(negedge clk); start = 0; while (!done) @(negedge clk);
        end
        repeat (3) @(negedge clk);
        $display("SEQ tokens %0d, cycles per token %0d", NTOK, (cyc - t0) / NTOK); $fclose(f); $finish;
    end
endmodule
