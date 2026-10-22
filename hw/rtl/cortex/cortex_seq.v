// SPARK Cortex stage and night sequencer (22 Oct 2026): the host schedule moved onto the chip. It drives the core's own commands for one learning stage, bit-exact with CortexSlow.stage (hw/brain/cortex_slow.py):
//   for every real example (the host has loaded its code list into the core's list buffer, then pulses ex_valid with the label): LEARN, DAYDREAM dreams of its class, the interleaved dreams of the old classes
//   (cumulative total ndream * old classes spread over the stage, found with a running remainder: no divider), and a FOLLOW every CH ticks (tick = one real example or one night dream; counter, no divider);
//   then, when the stage had old classes, the night: NIGHT passes of ndream * known classes dreams over the known classes in turn, FOLLOW every CH ticks, and an early stop: after every 256th night dream (counted over the chip's life)
//   the night ends if more than NSTOP table updates happened since the last check (or since the night began); finally SCOPY when the stage had fewer than 2 * CH examples.
// host interface: cfg_we/cfg_addr/cfg_val (0 ndream, 1 night, 2 daydream, 3 ch (0 = automatic: ch = max(CHMIN, N >> CHSH), the follow-interval rule of 22 Oct 2026: CHMIN 100, CHSH 5), 4 nstop, 5 N examples, 6 new-class mask), start; per example ex_valid + ex_label (ex_ready says it can take the next); done at the end.
// core interface: cmd_valid/cmd_op/cmd_arg out, busy / updated / known (the core's rd_known before the stage) in.
`timescale 1ns/1ps
module cortex_seq #(parameter C = 10, parameter CHMIN = 100, parameter CHSH = 5) (
    input  wire clk, rst,
    input  wire cfg_we, input wire [2:0] cfg_addr, input wire [31:0] cfg_val,
    input  wire start, input wire ex_valid, input wire [3:0] ex_label,
    output reg  ex_ready, output reg done,
    output reg  cmd_valid, output reg [2:0] cmd_op, output reg [3:0] cmd_arg,
    input  wire busy, input wire updated, input wire [C-1:0] known
);
    reg [23:0] ndream, nexamples; reg [7:0] night, nstop; reg [3:0] daydream; reg [15:0] ch; reg [C-1:0] newmask, oldmask, knmask;
    reg [15:0] tc, ch_eff; reg [31:0] tick, tick_m; reg [7:0] nd256; reg [8:0] blockw; reg [4:0] mc; reg [3:0] label;
    reg [31:0] total_d, acc, i; reg [4:0] nold, nkn, rr, kj; reg [7:0] pass; reg [31:0] jj, jmax; reg [3:0] dd; reg stop;
    reg [5:0] st, ret; reg [3:0] ci; reg [2:0] w; reg [2:0] iop; reg [3:0] iarg; reg lastupd;
    localparam S_IDLE = 0, S_KN = 1, S_WAITEX = 2, S_LEARN = 3, S_DAY = 4, S_ACC = 5, S_OLD = 6, S_TICK = 7, S_TICKF = 8, S_NEXT = 9, S_NIGHT0 = 10, S_NIGHTD = 11, S_M1 = 16, S_M2 = 17, S_MOD = 18, S_NTICK = 12, S_NCHK = 13, S_SCOPY = 14, S_DONE = 15,
               S_ISS = 20, S_W1 = 21, S_W2 = 22;
    function [4:0] pop; input [C-1:0] m; integer q; begin pop = 0; for (q = 0; q < C; q = q + 1) pop = pop + m[q]; end endfunction
    function [3:0] nth; input [C-1:0] m; input [4:0] n; integer q; reg [4:0] seen; reg got; begin nth = 0; seen = 0; got = 0; for (q = 0; q < C; q = q + 1) if (m[q] && !got) begin if (seen == n) begin nth = q; got = 1; end else seen = seen + 1; end end endfunction
    always @(posedge clk) begin
        cmd_valid <= 0;
        if (cfg_we) case (cfg_addr) 3'd0: ndream <= cfg_val; 3'd1: night <= cfg_val; 3'd2: daydream <= cfg_val; 3'd3: ch <= cfg_val; 3'd4: nstop <= cfg_val; 3'd5: nexamples <= cfg_val; 3'd6: newmask <= cfg_val; default: ; endcase
        if (rst) begin st <= S_IDLE; ex_ready <= 0; done <= 0; tc <= 0; tick <= 0; nd256 <= 0; end
        else case (st)
        S_IDLE: begin done <= 0; ex_ready <= 0; if (start) begin oldmask <= known & ~newmask; knmask <= known | newmask; ci <= 0; i <= 0; acc <= 0; rr <= 0;
            ch_eff <= (ch != 0) ? ch : (((nexamples >> CHSH) < CHMIN) ? CHMIN : (nexamples >> CHSH)); tick_m <= tick; st <= S_MOD; end end
        // tick modulo the interval of this stage, by repeated subtraction (the model counts ticks over the chip's life)
        S_MOD: if (tick_m >= ch_eff) tick_m <= tick_m - ch_eff; else begin tc <= tick_m[15:0]; st <= S_KN; end
        // mark the new classes known, one command each
        S_KN: begin
            if (ci == C) begin nold <= pop(oldmask); nkn <= pop(knmask); mc <= 0; total_d <= 0; st <= S_M1; end
            else if (newmask[ci]) begin iop <= 3'd5; iarg <= ci; ci <= ci + 1; ret <= S_KN; st <= S_ISS; end
            else ci <= ci + 1;
        end
        S_M1: if (mc == nold) begin ex_ready <= (nexamples != 0); st <= (nexamples == 0) ? S_NIGHT0 : S_WAITEX; end else begin total_d <= total_d + ndream; mc <= mc + 1; end
        S_WAITEX: if (ex_valid) begin label <= ex_label; ex_ready <= 0; iop <= 3'd1; iarg <= ex_label; dd <= 0; ret <= S_DAY; st <= S_ISS; end
        S_DAY: if (dd == daydream) begin acc <= acc + total_d; st <= S_OLD; end else begin iop <= 3'd3; iarg <= label; dd <= dd + 1; ret <= S_DAY; st <= S_ISS; end
        // the interleaved dreams of the old classes: floor(cumulative total / N) in all, by repeated subtraction
        S_OLD: if (acc >= nexamples) begin acc <= acc - nexamples; iop <= 3'd3; iarg <= nth(oldmask, rr); rr <= (rr + 1 == nold) ? 0 : rr + 1; ret <= S_OLD; st <= S_ISS; end else st <= S_TICK;
        S_TICK: begin tick <= tick + 1; if (tc + 1 == ch_eff) begin tc <= 0; iop <= 3'd7; iarg <= 4'd5; ret <= S_NEXT; st <= S_ISS; end else begin tc <= tc + 1; st <= S_NEXT; end end
        S_NEXT: begin i <= i + 1; if (i + 1 == nexamples) st <= S_NIGHT0; else begin ex_ready <= 1; st <= S_WAITEX; end end
        // the night
        S_NIGHT0: begin pass <= 0; jj <= 0; kj <= 0; blockw <= 0; stop <= 0; mc <= 0; jmax <= 0; st <= (nold == 0 || night == 0) ? S_SCOPY : S_M2; end
        S_M2: if (mc == nkn) st <= S_NIGHTD; else begin jmax <= jmax + ndream; mc <= mc + 1; end
        S_NIGHTD: if (stop || pass == night) st <= S_SCOPY;
                  else if (jj == jmax) begin pass <= pass + 1; jj <= 0; kj <= 0; st <= S_NIGHTD; end
                  else begin iop <= 3'd3; iarg <= nth(knmask, kj); kj <= (kj + 1 == nkn) ? 0 : kj + 1; ret <= S_NTICK; st <= S_ISS; end
        S_NTICK: begin
            blockw <= blockw + lastupd; nd256 <= nd256 + 1; jj <= jj + 1; tick <= tick + 1;
            if (tc + 1 == ch_eff) begin tc <= 0; iop <= 3'd7; iarg <= 4'd5; ret <= S_NCHK; st <= S_ISS; end else begin tc <= tc + 1; st <= S_NCHK; end
        end
        S_NCHK: begin
            if (nstop != 0 && nd256 == 0) begin if (blockw > nstop) stop <= 1; else blockw <= 0; end
            st <= S_NIGHTD;
        end
        S_SCOPY: begin if (nexamples < {ch_eff, 1'b0}) begin iop <= 3'd7; iarg <= 4'd6; ret <= S_DONE; st <= S_ISS; end else st <= S_DONE; end
        S_DONE: begin done <= 1; st <= S_IDLE; end
        // issue one core command and wait for it to finish
        S_ISS: if (!busy) begin cmd_valid <= 1; cmd_op <= iop; cmd_arg <= iarg; w <= 0; st <= S_W1; end
        S_W1: st <= S_W2;
        S_W2: if (!busy) begin lastupd <= updated; st <= ret; end
        default: st <= S_IDLE;
        endcase
    end
endmodule
