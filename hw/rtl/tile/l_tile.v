// L tile: two routers (request network and response network), one SRAM bank of 16-bit words (two 8-bit counters n0, n1) and a bank controller.
// Flit (72 bits): {type[1:0], dst[5:0], src[5:0], tag[7:0], addr[17:0], data[31:0]}; dst/src = {y[2:0], x[2:0]}.
// Requests: type 0 = lookup (returns the word in a type 1 response), type 2 = update (posted): n0 += data[7:0], n1 += data[15:8], saturating at 255.
// The memory is sram_wrap: behavioural in simulation, the OpenRAM macro with -DOPENRAM, or any other memory with the same ports.
`timescale 1ns/1ps
module l_tile #(parameter X = 0, Y = 0, AW = 12, FW = 72) (
    input clk, rst,
    input  cl_req_valid, input [FW-1:0] cl_req_flit, output cl_req_ready,
    output cl_rsp_valid, output [FW-1:0] cl_rsp_flit, input cl_rsp_ready,
    input  [4*FW-1:0] rq_in_flit,  input  [3:0] rq_in_valid,  output [3:0] rq_in_ready,
    output [4*FW-1:0] rq_out_flit, output [3:0] rq_out_valid, input  [3:0] rq_out_ready,
    input  [4*FW-1:0] rp_in_flit,  input  [3:0] rp_in_valid,  output [3:0] rp_in_ready,
    output [4*FW-1:0] rp_out_flit, output [3:0] rp_out_valid, input  [3:0] rp_out_ready);
    localparam [5:0] ME = {Y[2:0], X[2:0]};
    // ---- request network
    wire [5*FW-1:0] q_of, q_if; wire [4:0] q_ov, q_ir, q_iv, q_or;
    assign q_if = {rq_in_flit, cl_req_flit}; assign q_iv = {rq_in_valid, cl_req_valid};
    assign cl_req_ready = q_ir[0]; assign rq_in_ready = q_ir[4:1];
    assign rq_out_flit = q_of[5*FW-1:FW]; assign rq_out_valid = q_ov[4:1];
    l_router #(X, Y, FW) rq (.clk(clk), .rst(rst), .in_flit(q_if), .in_valid(q_iv), .in_ready(q_ir), .out_flit(q_of), .out_valid(q_ov), .out_ready(q_or));
    // ---- bank controller: the local output of the request network; one request at a time (read, then respond or write back)
    wire mv = q_ov[0]; wire [FW-1:0] mf = q_of[FW-1:0];
    reg [FW-1:0] rsp_f; reg rsp_v; wire [4:0] p_ir, p_ov, p_or, p_iv; wire [5*FW-1:0] p_of, p_if;
    wire rsp_free = !rsp_v || p_ir[0];
    reg busy; reg [FW-1:0] held;                                   // request being served
    wire is_upd = (mf[71:70] == 2'd2);
`ifdef OPENRAM
    // the SRAM macros power up with unknown contents: after reset every word is written with zero (2^AW cycles); requests wait for it
    reg [AW:0] icnt; wire init = !icnt[AW];
    always @(posedge clk) if (rst) icnt <= 0; else if (init) icnt <= icnt + 1'b1;
`else
    wire init = 1'b0; wire [AW:0] icnt = {(AW + 1){1'b0}};
`endif
    wire accept = mv && !busy && !init && (is_upd || rsp_free);
    assign q_or = {rq_out_ready, accept};
    wire [AW-1:0] rd_addr = mf[AW+31:32];
    wire [15:0] rdata; wire we_req = busy && (held[71:70] == 2'd2); wire [15:0] w = rdata;
    wire [8:0] s0 = {1'b0, w[7:0]} + {1'b0, held[7:0]}, s1 = {1'b0, w[15:8]} + {1'b0, held[15:8]};
    wire [15:0] nw = {s1[8] ? 8'd255 : s1[7:0], s0[8] ? 8'd255 : s0[7:0]};
    sram_wrap #(AW) bank (.clk(clk), .re(accept), .ra(rd_addr), .rdata(rdata), .we(we_req | init), .wa(init ? icnt[AW-1:0] : held[AW+31:32]), .wd(init ? 16'h0000 : nw));
    always @(posedge clk) begin
        if (rst) begin busy <= 1'b0; rsp_v <= 1'b0; end
        else begin
            if (rsp_v && p_ir[0]) rsp_v <= 1'b0;
            if (accept) begin busy <= 1'b1; held <= mf; end
            else if (busy) begin
                busy <= 1'b0;
                if (held[71:70] == 2'd0) begin rsp_f <= {2'd1, held[63:58], ME, held[57:50], held[49:32], 16'd0, w}; rsp_v <= 1'b1; end
            end
        end
    end
    // ---- response network
    assign p_if = {rp_in_flit, rsp_f}; assign p_iv = {rp_in_valid, rsp_v};
    assign rp_in_ready = p_ir[4:1]; assign rp_out_flit = p_of[5*FW-1:FW]; assign rp_out_valid = p_ov[4:1];
    assign p_or = {rp_out_ready, cl_rsp_ready}; assign cl_rsp_valid = p_ov[0]; assign cl_rsp_flit = p_of[FW-1:0];
    l_router #(X, Y, FW) rp (.clk(clk), .rst(rst), .in_flit(p_if), .in_valid(p_iv), .in_ready(p_ir), .out_flit(p_of), .out_valid(p_ov), .out_ready(p_or));
endmodule
