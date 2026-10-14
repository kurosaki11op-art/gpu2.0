// SPARK Cortex core: fast table + dream memory + dream generator, bit-exact with hw/brain/cortex_int.py.
// Integer only: adds, compares, shifts, XOR. No multiplier, no divider.
//
// Memories (one word per code bit b, all classes side by side, so one read serves every class):
//   wmem[b] : C fields of WB-bit signed table counters (saturate at +-CMAX)
//   cmem[b] : C fields of CB-bit dream counters (on-counts); n[c] = per-class example count, halved when full
//   lbuf    : the current list of active code bits (loaded by the host, or written by the dream generator)
//   lanes   : 32 xorshift32 random generators; code bit b uses lane b % 32
// Commands (cmd_op, cmd_arg = class); the host marks a class known (op 5) before teaching it:
//   1 LEARN    count the list into class arg (halve the class's counts when its example count is full), then PRACTISE
//   2 PRACTISE surprise-gated update of the table for class arg
//   3 DREAM    generate a dream of class arg into lbuf, then PRACTISE it as class arg
//   4 PREDICT  score the list; pred = first known class with the top score
//   5 KNOWN    mark class arg as known
//   6 CLEAR    zero the table, the dream counters, the example counts and the known classes (2 cycles per code bit)
//   7 MEM      memory transfer (export / import of what the chip knows), address mem_addr:
//              arg 0 = read word mem_addr into rd_w / rd_c; arg 1 = write wr_w / wr_c to word mem_addr;
//              arg 2 = set the example counts n[c] = wr_c field c and the known classes = wr_w[C-1:0]
//              (rd_n / rd_known always show the current counts and known classes)
`timescale 1ns/1ps
module cortex_core #(
    parameter NB = 4608, parameter AW = 13, parameter C = 10, parameter WB = 5, parameter CB = 10,
    parameter CMAX = 15, parameter MARGIN = 8, parameter SW = 20
) (
    input  wire          clk, rst,
    input  wire          cmd_valid, input wire [2:0] cmd_op, input wire [3:0] cmd_arg,
    input  wire          lb_we, input wire [AW-1:0] lb_waddr, input wire [AW-1:0] lb_wdata, input wire [AW:0] lb_len,
    input  wire          lane_we, input wire [4:0] lane_waddr, input wire [31:0] lane_wdata,
    input  wire [AW-1:0] mem_addr, input wire [C*WB-1:0] wr_w, input wire [C*CB-1:0] wr_c,
    output reg           busy, output reg [3:0] pred, output reg updated, output reg [AW:0] llen_out,
    output reg [C*WB-1:0] rd_w, output reg [C*CB-1:0] rd_c, output wire [C*CB-1:0] rd_n, output wire [C-1:0] rd_known
);
    localparam [CB-1:0] TOP = (1 << CB) - 1;
    localparam S_IDLE = 0,
               S_C0 = 1, S_C1 = 2, S_C2 = 3, S_C3 = 4, S_C4 = 5, S_C5 = 6, S_N = 7,
               S_H0 = 8, S_H1 = 9, S_H2 = 10, S_H3 = 11,
               S_S0 = 12, S_S1 = 13, S_S2 = 14, S_S3 = 15, S_S4 = 16, S_R = 17,
               S_U0 = 18, S_U1 = 19, S_U2 = 20, S_U3 = 21, S_U4 = 22, S_U5 = 23,
               S_D0 = 24, S_D1 = 25, S_D2 = 26, S_D3 = 27, S_P = 28, S_DONE = 29, S_Z0 = 30, S_Z1 = 31,
               S_M0 = 32, S_M1 = 33, S_M2 = 34;

`ifndef CORTEX_ASIC
    (* ram_style = "block" *) reg [C*WB-1:0] wmem [0:NB-1];
    (* ram_style = "block" *) reg [C*CB-1:0] cmem [0:NB-1];
    (* ram_style = "block" *) reg [AW-1:0]   lbuf [0:NB-1];
`endif
    reg [31:0] lanes [0:31];
    reg [CB-1:0] n [0:C-1];
    reg [C-1:0] known;

    reg [5:0] st; reg [3:0] y, rv, sc_i; reg predict_mode;
    reg [AW:0] i, llen, k, b; reg [4:0] lane;
    reg [AW-1:0] lb_addr, m_addr; reg [AW-1:0] lb_q; reg [C*WB-1:0] wq; reg [C*CB-1:0] cq;
    reg [AW-1:0] lb_wa, lb_wd; reg lb_wen;
    reg [C*WB-1:0] w_wd; reg w_wen; reg [C*CB-1:0] c_wd; reg c_wen;
    reg signed [SW-1:0] acc [0:C-1];
    reg signed [SW-1:0] best; reg have_rv;
    reg [CB-1:0] onf, ncur; reg [4:0] L;
    reg [C*WB-1:0] wt; reg [C*CB-1:0] ct; reg [CB:0] nn;
    integer j;
    genvar gi;
    generate for (gi = 0; gi < C; gi = gi + 1) begin : g_n
        assign rd_n[gi*CB +: CB] = n[gi];
    end endgenerate
    assign rd_known = known;

    // ---- memories: synchronous read; writes come one cycle after the FSM asks (registered enables) -------------
    // single port: the host writes only while the core is idle and the dream generator writes only while nothing
    // reads the list, so reads and writes never share a cycle and one address serves both
    wire lbw = lb_we | lb_wen;
    wire [AW-1:0] lba = lb_we ? lb_waddr : lb_wen ? lb_wa : lb_addr, lbd = lb_we ? lb_wdata : lb_wd;
    // every block-RAM input is re-registered on the falling edge: the RAMs still sample on the rising edge, so the
    // behaviour is cycle-for-cycle the same, but the hold margin at the RAM inputs becomes half a clock period
    reg lbw_n, w_wen_n, c_wen_n; reg [AW-1:0] lba_n, lbd_n, m_addr_n; reg [C*WB-1:0] w_wd_n; reg [C*CB-1:0] c_wd_n;
    always @(negedge clk) begin
        lbw_n <= lbw; lba_n <= lba; lbd_n <= lbd; m_addr_n <= m_addr;
        w_wen_n <= w_wen; w_wd_n <= w_wd; c_wen_n <= c_wen; c_wd_n <= c_wd;
    end
`ifdef CORTEX_ASIC
    // ASIC build: OpenRAM SRAM macros (sram_array in hw/asic/spark_mem_sky130.v; port 0 writes, port 1 reads). The macro
    // presents read data half a cycle after the clock edge that takes the address and holds it to the next edge, so using
    // its output directly gives the same cycle timing as the FPGA block RAMs above.
    wire [AW-1:0] lb_rd; wire [C*WB-1:0] w_rd; wire [C*CB-1:0] c_rd;
    sram_array #(.W(AW), .DEPTH(NB), .AW(AW)) u_lbuf (.clk(clk), .we(lbw_n), .wa(lba_n), .wd(lbd_n), .ra(lba_n), .rd(lb_rd));
    sram_array #(.W(C*WB), .DEPTH(NB), .AW(AW)) u_wmem (.clk(clk), .we(w_wen_n), .wa(m_addr_n), .wd(w_wd_n), .ra(m_addr_n), .rd(w_rd));
    sram_array #(.W(C*CB), .DEPTH(NB), .AW(AW)) u_cmem (.clk(clk), .we(c_wen_n), .wa(m_addr_n), .wd(c_wd_n), .ra(m_addr_n), .rd(c_rd));
    always @(*) begin lb_q = lb_rd; wq = w_rd; cq = c_rd; end
`else
    always @(posedge clk) begin
        if (lbw_n) lbuf[lba_n] <= lbd_n;
        else lb_q <= lbuf[lba_n];
    end
    always @(posedge clk) begin
        wq <= wmem[m_addr_n];
        if (w_wen_n) wmem[m_addr_n] <= w_wd_n;
    end
    always @(posedge clk) begin
        cq <= cmem[m_addr_n];
        if (c_wen_n) cmem[m_addr_n] <= c_wd_n;
    end

`endif

    function [31:0] xs; input [31:0] s; reg [31:0] t; begin
        t = s ^ (s << 13); t = t ^ (t >> 17); xs = t ^ (t << 5);
    end endfunction
    function [4:0] blen; input [CB-1:0] v; integer q; begin
        blen = 0; for (q = 0; q < CB; q = q + 1) if (v[q]) blen = q + 1;
    end endfunction

    wire signed [WB-1:0] wy = wq[y*WB +: WB];
    wire signed [WB-1:0] wr = wq[rv*WB +: WB];
    wire [31:0] lane_next = xs(lanes[lane]);
    wire [31:0] rnd = lane_next & ((32'd1 << L) - 32'd1);

    always @(posedge clk) begin
        w_wen <= 0; c_wen <= 0; lb_wen <= 0;
        if (lane_we) lanes[lane_waddr] <= lane_wdata;
        if (rst) begin
            st <= S_IDLE; busy <= 0; known <= 0; pred <= 0; updated <= 0; llen_out <= 0;
            for (j = 0; j < C; j = j + 1) n[j] <= 0;
        end else case (st)
        S_IDLE: begin
            busy <= 0;
            if (cmd_valid) begin
                y <= cmd_arg; busy <= 1; i <= 0; llen <= lb_len; predict_mode <= 0; updated <= 0;
                for (j = 0; j < C; j = j + 1) acc[j] <= 0;
                case (cmd_op)
                    3'd1: st <= S_C0;
                    3'd2: st <= S_S0;
                    3'd3: begin                     // a class with no examples dreams nothing (skips straight to practise)
                        st <= S_D0; b <= (n[cmd_arg] == 0) ? NB : 0; k <= 0; lane <= 0; L <= blen(n[cmd_arg]); ncur <= n[cmd_arg];
                    end
                    3'd4: begin st <= S_S0; predict_mode <= 1; end
                    3'd5: begin known[cmd_arg] <= 1'b1; st <= S_DONE; end
                    3'd6: begin b <= 0; st <= S_Z0; end
                    3'd7: begin
                        if (cmd_arg == 4'd2) begin
                            known <= wr_w[C-1:0];
                            for (j = 0; j < C; j = j + 1) n[j] <= wr_c[j*CB +: CB];
                            st <= S_DONE;
                        end else begin m_addr <= mem_addr; st <= (cmd_arg == 4'd1) ? S_M2 : S_M0; end
                    end
                    default: st <= S_DONE;
                endcase
            end
        end
        // ---- count: on[y, bit] += 1 for every listed bit, then n[y] += 1 ----------------------------------------
        S_C0: if (i == llen) st <= S_N; else begin lb_addr <= i[AW-1:0]; st <= S_C1; end
        S_C1: st <= S_C2;
        S_C2: begin m_addr <= lb_q; st <= S_C3; end
        S_C3: st <= S_C4;
        S_C4: begin c_wd <= cq + ({{(C*CB-1){1'b0}}, 1'b1} << (y * CB)); c_wen <= 1; st <= S_C5; end
        S_C5: begin i <= i + 1; st <= S_C0; end
        S_N: begin
            nn = n[y] + 1'b1;
            if (nn >= TOP) begin n[y] <= nn[CB-1:0]; b <= 0; st <= S_H0; end
            else begin n[y] <= nn[CB-1:0]; i <= 0; st <= S_S0; end
        end
        // ---- synaptic scaling: halve every on-count of class y, then n[y] ---------------------------------------
        S_H0: if (b == NB) begin n[y] <= n[y] >> 1; i <= 0; st <= S_S0; end
              else begin m_addr <= b[AW-1:0]; st <= S_H1; end
        S_H1: st <= S_H2;
        S_H2: begin ct = cq; ct[y*CB +: CB] = cq[y*CB +: CB] >> 1; c_wd <= ct; c_wen <= 1; st <= S_H3; end
        S_H3: begin b <= b + 1; st <= S_H0; end
        // ---- score: acc[c] += table[c, bit] for every listed bit -----------------------------------------------
        S_S0: if (i == llen) begin sc_i <= 0; have_rv <= 0; st <= predict_mode ? S_P : S_R; end
              else begin lb_addr <= i[AW-1:0]; st <= S_S1; end
        S_S1: st <= S_S2;
        S_S2: begin m_addr <= lb_q; st <= S_S3; end
        S_S3: st <= S_S4;
        S_S4: begin
            for (j = 0; j < C; j = j + 1) acc[j] <= acc[j] + $signed(wq[j*WB +: WB]);
            i <= i + 1; st <= S_S0;
        end
        // ---- rival: first known class other than y with the top score; update when the margin is small ---------
        S_R: if (sc_i == C) begin
                 if (have_rv && (acc[y] - best <= MARGIN)) begin updated <= 1; i <= 0; st <= S_U0; end
                 else st <= S_DONE;
             end else begin
                 if (sc_i != y && known[sc_i] && (!have_rv || acc[sc_i] > best)) begin
                     best <= acc[sc_i]; rv <= sc_i; have_rv <= 1;
                 end
                 sc_i <= sc_i + 1;
             end
        S_U0: if (i == llen) st <= S_DONE; else begin lb_addr <= i[AW-1:0]; st <= S_U1; end
        S_U1: st <= S_U2;
        S_U2: begin m_addr <= lb_q; st <= S_U3; end
        S_U3: st <= S_U4;
        S_U4: begin
            wt = wq;
            if (wy < CMAX)  wt[y*WB +: WB]  = wy + 1'b1;
            if (wr > -CMAX) wt[rv*WB +: WB] = wr - 1'b1;
            w_wd <= wt; w_wen <= 1; st <= S_U5;
        end
        S_U5: begin i <= i + 1; st <= S_U0; end
        // ---- dream: for every code bit, draw r < n[y] from its lane (redraw if too big); on if r < on[y, bit] ----
        S_D0: if (b == NB) begin llen <= k; llen_out <= k; i <= 0; st <= S_S0; end
              else begin m_addr <= b[AW-1:0]; st <= S_D1; end
        S_D1: st <= S_D2;
        S_D2: begin onf <= cq[y*CB +: CB]; st <= S_D3; end
        S_D3: begin
            lanes[lane] <= lane_next;
            if (rnd < ncur) begin
                if (rnd < onf) begin lb_wa <= k[AW-1:0]; lb_wd <= b[AW-1:0]; lb_wen <= 1; k <= k + 1; end
                b <= b + 1; lane <= lane + 1; st <= S_D0;
            end
        end
        // ---- predict: first known class with the top score -------------------------------------------------------
        S_P: if (sc_i == C) st <= S_DONE;
             else begin
                 if (known[sc_i] && (!have_rv || acc[sc_i] > best)) begin best <= acc[sc_i]; pred <= sc_i; have_rv <= 1; end
                 sc_i <= sc_i + 1;
             end
        // ---- clear ------------------------------------------------------------------------------------------------
        S_Z0: if (b == NB) begin known <= 0; for (j = 0; j < C; j = j + 1) n[j] <= 0; st <= S_DONE; end
              else begin m_addr <= b[AW-1:0]; w_wd <= 0; c_wd <= 0; w_wen <= 1; c_wen <= 1; st <= S_Z1; end
        S_Z1: begin b <= b + 1; st <= S_Z0; end
        // ---- memory transfer ---------------------------------------------------------------------------------------
        S_M0: st <= S_M1;                                    // read: data valid the cycle after next
        S_M1: begin rd_w <= wq; rd_c <= cq; st <= S_DONE; end
        S_M2: begin w_wd <= wr_w; c_wd <= wr_c; w_wen <= 1; c_wen <= 1; st <= S_DONE; end
        S_DONE: begin busy <= 0; st <= S_IDLE; end
        default: st <= S_IDLE;
        endcase
    end
endmodule
