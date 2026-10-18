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
//   4 PREDICT  score the list; pred = first known class with the top score. arg 1 = LOOK AGAIN: the scores are not
//              cleared first, so several views of one input (e.g. one-pixel shifts, test-time saccades) are summed
//   5 KNOWN    mark class arg as known
//   6 CLEAR    zero the table, the dream counters, the example counts and the known classes (2 cycles per code bit)
//   7 MEM      memory transfer (export / import of what the chip knows), address mem_addr:
//              arg 0 = read word mem_addr into rd_w / rd_c; arg 1 = write wr_w / wr_c to word mem_addr;
//              arg 2 = set the example counts n[c] = wr_c field c and the known classes = wr_w[C-1:0]
//              (rd_n / rd_known always show the current counts and known classes)
//              arg 3 (build option CORTEX_CONTEXT) = FREEZE: copy the dream counters and example counts into a frozen
//              copy (3 cycles per code bit)
//              arg 4 (build option CORTEX_IMPRINT) = IMPRINT class mem_addr[3:0]: while that class has seen at most IMPN
//              examples, raise its table field at every code bit to its mean code times 2^IMPS:
//              W = max(W, min((on << IMPS) >> (blen(n) - 1), CMAX)) (shifts and compares; 3 cycles per code bit). The
//              few-shot fix of 15 Oct 2026: a new class learned from a few examples is no longer outvoted by old ones.
//              arg 5 (build option CORTEX_SLOW) = FOLLOW: slow table S (SB-bit signed fields) follows the fast table W:
//              S += (((W << SFR) - S) + 2^(SLOWK-1)) >>> SLOWK for every code bit and class (3 cycles per code bit); arg 6 = SCOPY: S = W << SFR;
//              arg 7 = read S word mem_addr into rd_s. With CORTEX_SLOW, PREDICT scores with S instead of W (learning, PRACTISE
//              and DREAM still use W). The host decides when to FOLLOW (every CH real examples / night dreams) and SCOPYs after
//              a stage too short to consolidate. Redesign 6 of 18 Oct 2026 (all-at-once clothing +3.3, words +2.6 in the model); SLOWK = 5 (19 Oct: slower consolidation also lifts staged clothing 78.5 -> 81.6).
//              args 8-12 (build option CORTEX_EMBED, 20 Oct 2026, Redesign 8) = the table-score embedding for new words: a word is a PROTOTYPE slot (C signed sums, a label, a count)
//              in the space of the table's own scores over the known classes. They use the score vector left in acc[] by the PREDICT just before (acc is not cleared for these commands);
//              e[j] = acc[j] if class j is known, else 0. mem_addr fields: slot = [5:0].
//              arg 8 = ENROLL: slot, shift override = [8:6] (0 = automatic min(bitlen(count), 5)), label = [12:9]; empty slot: p = e, else p += (e - p) >>> s; count saturates at 255 (C cycles)
//              arg 9 = WINNER: first slot = [5:0], number of slots = [11:6]; emb_slot = the first EMPTY slot in range, else the slot with the smallest L1 distance sum |e - p| (first on a tie)
//              arg 10 = MATCH: emb_slot / emb_lab / emb_dist = the filled slot (any) with the smallest L1 distance (first on a tie) and its label
//              arg 11 = read prototype element mem_addr[9:0] = slot * 16 + class -> rd_e;  arg 12 = read slot meta mem_addr[5:0] -> rd_e = {filled, label, count}
//              Old words are enrolled by competitive learning (WINNER, then ENROLL into the winner with shift 5), new words from a few recordings by ENROLL with shift 0 (a running mean).
// Build option CORTEX_CONTEXT (context memory, bit-exact with CortexInt(context=True)): DREAM with cmd_frozen = 1
// dreams from the frozen copy instead of the live counters. The host freezes before a day that brings known classes
// back (a new condition), dreams old knowledge from the frozen copy during that day and alternates live / frozen at
// night, so the old condition is not overwritten. Costs a second dream-counter memory (ASIC; the FPGA RAM is full).
`timescale 1ns/1ps
// CORTEX_PIPE: pipelined score loop (1 code bit per cycle) and dream prefetch queue; on in the ASIC build, off on the
// Tang Nano (the extra logic does not fit: 101% LUT4). Same results either way, bit-exact.
`ifdef CORTEX_ASIC
`define CORTEX_PIPE
`endif
module cortex_core #(
    parameter NB = 4608, parameter AW = 13, parameter C = 10, parameter WB = 5, parameter CB = 10,
    parameter CMAX = 15, parameter MARGIN = 32, parameter SW = 20, parameter IMPS = 2, parameter IMPN = 8,
    parameter SB = 8, parameter SFR = 3, parameter SLOWK = 5,
    parameter NP = 48, parameter EMB_SMAX = 5
) (
    input  wire          clk, rst,
    input  wire          cmd_valid, input wire [2:0] cmd_op, input wire [3:0] cmd_arg,
`ifdef CORTEX_CONTEXT
    input  wire          cmd_frozen,
`endif
    input  wire          lb_we, input wire [AW-1:0] lb_waddr, input wire [AW-1:0] lb_wdata, input wire [AW:0] lb_len,
    input  wire          lane_we, input wire [4:0] lane_waddr, input wire [31:0] lane_wdata,
    input  wire [AW-1:0] mem_addr, input wire [C*WB-1:0] wr_w, input wire [C*CB-1:0] wr_c,
    output reg           busy, output reg [3:0] pred, output reg updated, output reg [AW:0] llen_out,
`ifdef CORTEX_SLOW
    output reg [C*SB-1:0] rd_s,
`endif
`ifdef CORTEX_EMBED
    output reg [5:0] emb_slot, output reg [3:0] emb_lab, output reg [23:0] emb_dist, output reg signed [SW-1:0] rd_e,
`endif
    output reg [C*WB-1:0] rd_w, output reg [C*CB-1:0] rd_c, output wire [C*CB-1:0] rd_n, output wire [C-1:0] rd_known
);
    localparam [CB-1:0] TOP = (1 << CB) - 1;
    localparam S_IDLE = 0,
               S_C0 = 1, S_C1 = 2, S_C2 = 3, S_C3 = 4, S_C4 = 5, S_C5 = 6, S_N = 7,
               S_H0 = 8, S_H1 = 9, S_H2 = 10, S_H3 = 11,
               S_S0 = 12, S_S1 = 13, S_S2 = 14, S_S3 = 15, S_S4 = 16, S_R = 17,
               S_U0 = 18, S_U1 = 19, S_U2 = 20, S_U3 = 21, S_U4 = 22, S_U5 = 23,
               S_D0 = 24, S_D1 = 25, S_D2 = 26, S_D3 = 27, S_P = 28, S_DONE = 29, S_Z0 = 30, S_Z1 = 31,
               S_M0 = 32, S_M1 = 33, S_M2 = 34, S_F0 = 35, S_F1 = 36, S_F2 = 37,
               S_I0 = 38, S_I1 = 39, S_I2 = 40,
               S_L0 = 41, S_L1 = 42, S_L2 = 43, S_Y0 = 44, S_Y1 = 45, S_Y2 = 46, S_Q0 = 47, S_Q1 = 48,
               S_N0 = 49, S_N1 = 50, S_N2 = 51, S_W0 = 52, S_W1 = 53, S_W2 = 54, S_W3 = 55, S_X0 = 56, S_X1 = 57, S_X2 = 58, S_X3 = 59;

`ifndef CORTEX_ASIC
    (* ram_style = "block" *) reg [C*WB-1:0] wmem [0:NB-1];
    (* ram_style = "block" *) reg [C*CB-1:0] cmem [0:NB-1];
    (* ram_style = "block" *) reg [AW-1:0]   lbuf [0:NB-1];
`endif
`ifdef CORTEX_SLOW
    reg [C*SB-1:0] sq; reg s_wen, s_wen_n; reg [C*SB-1:0] s_wd, s_wd_n;
    always @(negedge clk) begin s_wen_n <= s_wen; s_wd_n <= s_wd; end
`ifndef CORTEX_ASIC
    (* ram_style = "block" *) reg [C*SB-1:0] smem [0:NB-1];
    always @(posedge clk) begin
        sq <= smem[m_addr_n];
        if (s_wen_n) smem[m_addr_n] <= s_wd_n;
    end
`else
    wire [C*SB-1:0] s_rd;
    sram_array #(.W(C*SB), .DEPTH(NB), .AW(AW)) u_smem (.clk(clk), .we(s_wen_n), .wa(m_addr_n), .wd(s_wd_n), .ra(m_addr_n), .rd(s_rd));
    always @(*) sq = s_rd;
`endif
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
    reg signed [SW-1:0] best; reg have_rv; reg sd0, sd1, se0, se1;   // score pipeline stage flags
    reg [AW:0] pb; reg pf0, pf1, push, pop; reg [2:0] qcnt; reg [1:0] qw, qr; reg [CB-1:0] dq [0:3];   // dream prefetch
    reg [CB-1:0] onf, ncur; reg [4:0] L;
    reg [C*WB-1:0] wt; reg [C*CB-1:0] ct; reg [CB:0] nn;
    integer j;
`ifdef CORTEX_EMBED
    // prototype memory: slot * 16 + class (C <= 16, NP <= 64 slots), a filled flag, a label and a count per slot
    reg signed [SW-1:0] pv [0:NP*16-1]; reg [NP-1:0] pfill; reg [3:0] plab [0:NP-1]; reg [7:0] pcnt [0:NP-1];
    reg [5:0] e_s; reg [3:0] e_sh, e_lab, e_shift, e_j; reg [6:0] e_cur, e_end, e_bslot; reg [23:0] e_dist, e_best; reg e_have; integer e_dd;
    wire signed [SW-1:0] evec = known[e_j] ? acc[e_j] : {SW{1'b0}};
    wire [9:0] e_idx = {e_s, e_j};
    wire [9:0] e_cidx = {e_cur[5:0], e_j};
    wire signed [SW:0] ediff = $signed({evec[SW-1], evec}) - $signed({pv[e_cidx][SW-1], pv[e_cidx]});
    wire [SW:0] eabs = ediff[SW] ? -ediff : ediff;
    function [3:0] blen8; input [7:0] v; integer q; begin blen8 = 0; for (q = 0; q < 8; q = q + 1) if (v[q]) blen8 = q + 1; end endfunction
    integer ei; initial begin for (ei = 0; ei < NP * 16; ei = ei + 1) pv[ei] = 0; for (ei = 0; ei < NP; ei = ei + 1) begin plab[ei] = 0; pcnt[ei] = 0; end end   // power-up zero (simulation); a slot is empty until pfill is set
`endif
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
`ifdef CORTEX_CONTEXT
    // context memory: frozen copy of the dream counters (read with the live ones, written only by FREEZE)
    reg [CB-1:0] fn [0:C-1]; reg dsrc; reg f_wen, f_wen_n; reg [AW-1:0] f_wa, f_wa_n; reg [C*CB-1:0] f_wd, f_wd_n, fq;
    always @(negedge clk) begin f_wen_n <= f_wen; f_wa_n <= f_wa; f_wd_n <= f_wd; end
`ifdef CORTEX_ASIC
    wire [C*CB-1:0] f_rd;
    sram_array #(.W(C*CB), .DEPTH(NB), .AW(AW)) u_fmem (.clk(clk), .we(f_wen_n), .wa(f_wa_n), .wd(f_wd_n), .ra(m_addr_n), .rd(f_rd));
    always @(*) fq = f_rd;
`else
    reg [C*CB-1:0] fmem [0:NB-1];
    always @(posedge clk) begin
        fq <= fmem[m_addr_n];
        if (f_wen_n) fmem[f_wa_n] <= f_wd_n;
    end
`endif
    wire [CB-1:0] ndream = cmd_frozen ? fn[cmd_arg] : n[cmd_arg];
    wire [CB-1:0] dword = dsrc ? fq[y*CB +: CB] : cq[y*CB +: CB];
`else
    wire [CB-1:0] ndream = n[cmd_arg];
    wire [CB-1:0] dword = cq[y*CB +: CB];
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
`ifdef CORTEX_IMPRINT
    // IMPRINT: the class's field at the current code bit, its imprint value, and the word with the field raised
    reg [4:0] ish;                                                       // floor(log2 n[y])
    wire [CB+IMPS-1:0] iup0 = {{IMPS{1'b0}}, cq[y*CB +: CB]} << IMPS;
    wire [CB+IMPS-1:0] iup1 = iup0 >> ish;
    wire [WB-1:0] iup = (iup1 > CMAX) ? CMAX[WB-1:0] : iup1[WB-1:0];
    wire iraise = $signed(wy) < $signed({1'b0, iup});
    reg [C*WB-1:0] iword;
    always @(*) begin iword = wq; iword[y*WB +: WB] = iraise ? iup : wy; end
`endif

    always @(posedge clk) begin
        w_wen <= 0; c_wen <= 0; lb_wen <= 0;
`ifdef CORTEX_SLOW
        s_wen <= 0;
`endif
`ifdef CORTEX_CONTEXT
        f_wen <= 0;
`endif
        if (lane_we) lanes[lane_waddr] <= lane_wdata;
        if (rst) begin
            st <= S_IDLE; busy <= 0; known <= 0; pred <= 0; updated <= 0; llen_out <= 0;
            for (j = 0; j < C; j = j + 1) n[j] <= 0;
`ifdef CORTEX_EMBED
            pfill <= 0;
`endif
        end else case (st)
        S_IDLE: begin
            busy <= 0;
            if (cmd_valid) begin
                y <= cmd_arg; busy <= 1; i <= 0; llen <= lb_len; predict_mode <= 0; updated <= 0;
                `ifdef CORTEX_EMBED
                if (!(cmd_op == 3'd4 && cmd_arg[0]) && !(cmd_op == 3'd7 && cmd_arg >= 4'd8 && cmd_arg <= 4'd10)) for (j = 0; j < C; j = j + 1) acc[j] <= 0;   // PREDICT arg 1 / EMBED 8-10 keep the sum
`else
                if (!(cmd_op == 3'd4 && cmd_arg[0])) for (j = 0; j < C; j = j + 1) acc[j] <= 0;   // PREDICT arg 1 keeps the sum
`endif
                case (cmd_op)
                    3'd1: st <= S_C0;
                    3'd2: st <= S_S0;
                    3'd3: begin                     // a class with no examples dreams nothing (skips straight to practise)
                        st <= S_D0; b <= (ndream == 0) ? NB : 0; k <= 0; lane <= 0; L <= blen(ndream); ncur <= ndream;
`ifdef CORTEX_CONTEXT
                        dsrc <= cmd_frozen;
`endif
                    end
                    3'd4: begin st <= S_S0; predict_mode <= 1; end
                    3'd5: begin known[cmd_arg] <= 1'b1; st <= S_DONE; end
                    3'd6: begin b <= 0; st <= S_Z0; end
                    3'd7: begin
                        if (cmd_arg == 4'd2) begin
                            known <= wr_w[C-1:0];
                            for (j = 0; j < C; j = j + 1) n[j] <= wr_c[j*CB +: CB];
                            st <= S_DONE;
`ifdef CORTEX_CONTEXT
                        end else if (cmd_arg == 4'd3) begin
                            for (j = 0; j < C; j = j + 1) fn[j] <= n[j];
                            b <= 0; st <= S_F0;
`endif
`ifdef CORTEX_EMBED
                        end else if (cmd_arg == 4'd8) begin
                            e_s <= mem_addr[5:0]; e_sh <= {1'b0, mem_addr[8:6]}; e_lab <= mem_addr[12:9]; st <= S_N0;
                        end else if (cmd_arg == 4'd9) begin
                            e_cur <= {1'b0, mem_addr[5:0]}; e_end <= {1'b0, mem_addr[5:0]} + mem_addr[11:6]; e_have <= 0; e_bslot <= {1'b0, mem_addr[5:0]}; st <= S_W1;
                        end else if (cmd_arg == 4'd10) begin
                            e_cur <= 0; e_end <= NP; e_have <= 0; e_bslot <= 0; e_best <= 0; st <= S_X1;
                        end else if (cmd_arg == 4'd11) begin
                            rd_e <= pv[mem_addr[9:0]]; st <= S_DONE;
                        end else if (cmd_arg == 4'd12) begin
                            rd_e <= {pfill[mem_addr[5:0]], plab[mem_addr[5:0]], pcnt[mem_addr[5:0]]}; st <= S_DONE;
`endif
`ifdef CORTEX_SLOW
                        end else if (cmd_arg == 4'd5) begin
                            b <= 0; st <= S_L0;
                        end else if (cmd_arg == 4'd6) begin
                            b <= 0; st <= S_Y0;
                        end else if (cmd_arg == 4'd7) begin
                            m_addr <= mem_addr; st <= S_Q0;
`endif
`ifdef CORTEX_IMPRINT
                        end else if (cmd_arg == 4'd4) begin
                            y <= mem_addr[3:0]; b <= 0; ish <= blen(n[mem_addr[3:0]]) - 1'b1;
                            st <= (n[mem_addr[3:0]] == 0 || n[mem_addr[3:0]] > IMPN) ? S_DONE : S_I0;
`endif
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
`ifdef CORTEX_PIPE
        // ---- score the list: pipelined, one code bit per cycle. A list read issued in cycle t gives its code bit in
        // cycle t+2 (-> table address), whose table word arrives in cycle t+4 (-> add to every class score) ---------
        S_S0: begin sd0 <= 0; sd1 <= 0; se0 <= 0; se1 <= 0; st <= S_S1; end
        S_S1: begin
            if (i != llen) begin lb_addr <= i[AW-1:0]; i <= i + 1; sd0 <= 1; end else sd0 <= 0;
            sd1 <= sd0;
            if (sd1) begin m_addr <= lb_q; se0 <= 1; end else se0 <= 0;
            se1 <= se0;
`ifdef CORTEX_SLOW
            if (se1) for (j = 0; j < C; j = j + 1) acc[j] <= acc[j] + (predict_mode ? $signed(sq[j*SB +: SB]) : $signed(wq[j*WB +: WB]));
`else
            if (se1) for (j = 0; j < C; j = j + 1) acc[j] <= acc[j] + $signed(wq[j*WB +: WB]);
`endif
            if (i == llen && !sd0 && !sd1 && !se0 && !se1) begin sc_i <= 0; have_rv <= 0; st <= predict_mode ? S_P : S_R; end
        end
`else
        S_S0: if (i == llen) begin sc_i <= 0; have_rv <= 0; st <= predict_mode ? S_P : S_R; end
              else begin lb_addr <= i[AW-1:0]; st <= S_S1; end
        S_S1: st <= S_S2;
        S_S2: begin m_addr <= lb_q; st <= S_S3; end
        S_S3: st <= S_S4;
        S_S4: begin
`ifdef CORTEX_SLOW
            for (j = 0; j < C; j = j + 1) acc[j] <= acc[j] + (predict_mode ? $signed(sq[j*SB +: SB]) : $signed(wq[j*WB +: WB]));
`else
            for (j = 0; j < C; j = j + 1) acc[j] <= acc[j] + $signed(wq[j*WB +: WB]);
`endif
            i <= i + 1; st <= S_S0;
        end
`endif
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
`ifdef CORTEX_PIPE
        // ---- dream: for every code bit, draw r < n[y] from its lane (redraw if too big); on if r < on[y, bit].
        // Pipelined: the dream-counter words are prefetched one per cycle into a 4-entry queue (a read issued in cycle t
        // arrives in cycle t+2) while the generator consumes them; same draws, same order, ~1 cycle per code bit plus
        // redraws.
        S_D0: begin pb <= b; pf0 <= 0; pf1 <= 0; qcnt <= 0; qw <= 0; qr <= 0; st <= S_D1; end
        S_D1: begin
            if (pb != NB && ({1'b0, qcnt} + pf0 + pf1) < 4) begin m_addr <= pb[AW-1:0]; pb <= pb + 1; pf0 <= 1; end
            else pf0 <= 0;
            pf1 <= pf0;
            push = pf1; pop = 0;
            if (push) begin dq[qw] <= dword; qw <= qw + 1'b1; end
            if (qcnt != 0) begin
                lanes[lane] <= lane_next;
                if (rnd < ncur) begin
                    if (rnd < dq[qr]) begin lb_wa <= k[AW-1:0]; lb_wd <= b[AW-1:0]; lb_wen <= 1; k <= k + 1; end
                    b <= b + 1; lane <= lane + 1; qr <= qr + 1'b1; pop = 1;
                end
            end
            qcnt <= qcnt + push - pop;
            if (b == NB) begin llen <= k; llen_out <= k; i <= 0; st <= S_S0; end
        end
`else
        // ---- dream: for every code bit, draw r < n[y] from its lane (redraw if too big); on if r < on[y, bit] ----
        S_D0: if (b == NB) begin llen <= k; llen_out <= k; i <= 0; st <= S_S0; end
              else begin m_addr <= b[AW-1:0]; st <= S_D1; end
        S_D1: st <= S_D2;
        S_D2: begin onf <= dword; st <= S_D3; end
        S_D3: begin
            lanes[lane] <= lane_next;
            if (rnd < ncur) begin
                if (rnd < onf) begin lb_wa <= k[AW-1:0]; lb_wd <= b[AW-1:0]; lb_wen <= 1; k <= k + 1; end
                b <= b + 1; lane <= lane + 1; st <= S_D0;
            end
        end
`endif
`ifdef CORTEX_CONTEXT
        // ---- FREEZE: copy every dream-counter word into the frozen copy
        S_F0: begin m_addr <= b[AW-1:0]; st <= S_F1; end
        S_F1: st <= S_F2;
        S_F2: begin
            f_wd <= cq; f_wa <= b[AW-1:0]; f_wen <= 1;
            if (b == NB - 1) st <= S_DONE; else begin b <= b + 1; st <= S_F0; end
        end
`endif
`ifdef CORTEX_IMPRINT
        // ---- imprint: one code bit per 3 cycles (read word, raise class y's field, write back) -------------------
        S_I0: begin m_addr <= b[AW-1:0]; st <= S_I1; end
        S_I1: st <= S_I2;
        S_I2: begin
            if (iraise) begin w_wd <= iword; w_wen <= 1; end
            if (b == NB - 1) st <= S_DONE; else begin b <= b + 1; st <= S_I0; end
        end
`endif
`ifdef CORTEX_SLOW
        // ---- FOLLOW: S += (((W << SFR) - S) + 2^(SLOWK-1)) >>> SLOWK for every field of every code bit (3 cycles per code bit)
        S_L0: begin m_addr <= b[AW-1:0]; st <= S_L1; end
        S_L1: st <= S_L2;
        S_L2: begin
            for (j = 0; j < C; j = j + 1)
                s_wd[j*SB +: SB] <= $signed(sq[j*SB +: SB]) + ((($signed(wq[j*WB +: WB]) <<< SFR) - $signed(sq[j*SB +: SB]) + (1 << (SLOWK - 1))) >>> SLOWK);
            s_wen <= 1;
            if (b == NB - 1) st <= S_DONE; else begin b <= b + 1; st <= S_L0; end
        end
        // ---- SCOPY: S = W << SFR
        S_Y0: begin m_addr <= b[AW-1:0]; st <= S_Y1; end
        S_Y1: st <= S_Y2;
        S_Y2: begin
            for (j = 0; j < C; j = j + 1) s_wd[j*SB +: SB] <= $signed(wq[j*WB +: WB]) <<< SFR;
            s_wen <= 1;
            if (b == NB - 1) st <= S_DONE; else begin b <= b + 1; st <= S_Y0; end
        end
        // ---- read S word
        S_Q0: st <= S_Q1;
        S_Q1: begin rd_s <= sq; st <= S_DONE; end
`endif
`ifdef CORTEX_EMBED
        // ---- ENROLL: shift s = override or min(bitlen(count), EMB_SMAX); empty slot copies the vector
        S_N0: begin e_j <= 0; e_shift <= (e_sh != 0) ? e_sh : ((blen8(pcnt[e_s]) > EMB_SMAX) ? EMB_SMAX : blen8(pcnt[e_s])); st <= S_N1; end
        S_N1: begin
            if (!pfill[e_s]) pv[e_idx] <= evec;
            else begin e_dd = $signed(evec) - $signed(pv[e_idx]); pv[e_idx] <= pv[e_idx] + (e_dd >>> e_shift); end
            if (e_j == C - 1) st <= S_N2; else e_j <= e_j + 1'b1;
        end
        S_N2: begin
            if (!pfill[e_s]) begin pfill[e_s] <= 1'b1; pcnt[e_s] <= 8'd1; plab[e_s] <= e_lab; end
            else if (pcnt[e_s] != 8'd255) pcnt[e_s] <= pcnt[e_s] + 1'b1;
            st <= S_DONE;
        end
        // ---- WINNER: first empty slot in range, else the smallest L1 distance (first on a tie)
        S_W1: begin
            if (e_cur == e_end) begin emb_slot <= e_bslot[5:0]; st <= S_DONE; end
            else if (!pfill[e_cur[5:0]]) begin emb_slot <= e_cur[5:0]; st <= S_DONE; end
            else begin e_j <= 0; e_dist <= 0; st <= S_W2; end
        end
        S_W2: begin
            e_dist <= e_dist + eabs;
            if (e_j == C - 1) st <= S_W3; else e_j <= e_j + 1'b1;
        end
        S_W3: begin
            if (!e_have || e_dist < e_best) begin e_best <= e_dist; e_bslot <= e_cur; e_have <= 1'b1; end
            e_cur <= e_cur + 1'b1; st <= S_W1;
        end
        // ---- MATCH: smallest L1 distance over all filled slots
        S_X1: begin
            if (e_cur == e_end) begin emb_slot <= e_bslot[5:0]; emb_lab <= plab[e_bslot[5:0]]; emb_dist <= e_best; st <= S_DONE; end
            else if (!pfill[e_cur[5:0]]) e_cur <= e_cur + 1'b1;
            else begin e_j <= 0; e_dist <= 0; st <= S_X2; end
        end
        S_X2: begin
            e_dist <= e_dist + eabs;
            if (e_j == C - 1) st <= S_X3; else e_j <= e_j + 1'b1;
        end
        S_X3: begin
            if (!e_have || e_dist < e_best) begin e_best <= e_dist; e_bslot <= e_cur; e_have <= 1'b1; end
            e_cur <= e_cur + 1'b1; st <= S_X1;
        end
`endif
        // ---- predict: first known class with the top score -------------------------------------------------------
        S_P: if (sc_i == C) st <= S_DONE;
             else begin
                 if (known[sc_i] && (!have_rv || acc[sc_i] > best)) begin best <= acc[sc_i]; pred <= sc_i; have_rv <= 1; end
                 sc_i <= sc_i + 1;
             end
        // ---- clear ------------------------------------------------------------------------------------------------
        S_Z0: if (b == NB) begin known <= 0; for (j = 0; j < C; j = j + 1) n[j] <= 0;
`ifdef CORTEX_EMBED
                  pfill <= 0;
`endif
                  st <= S_DONE; end
              else begin m_addr <= b[AW-1:0]; w_wd <= 0; c_wd <= 0; w_wen <= 1; c_wen <= 1;
`ifdef CORTEX_SLOW
                   s_wd <= 0; s_wen <= 1;
`endif
                   st <= S_Z1; end
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
