// SPARK core v0: event-driven, think-less inference core for a small L-style model.
// Bit-exact with hw/golden/spark_golden.py.
//
// Per input byte ("token"):
//   1. Recall unit (optional): update the hash table with the byte that just
//      arrived, then look up the new context. Confident hit -> output the stored
//      byte and skip every layer ("instinct" path).
//   2. Stage 0: embedding events -> layer-0 accumulators, then membrane/spike pass.
//   3. Stage 2 (optional exit head): layer-0 spike events -> exit logits, argmax.
//      If the top-1/top-2 margin >= exit_th, output and stop ("early exit").
//   4. Stage 1: layer-0 spike events -> layer-1, membrane/spike pass.
//   5. Stage 3: layer-1 spike events -> main head, argmax -> output.
// Event-driven: only non-zero (or, in delta mode, changed) inputs cost cycles.
// Dense mode (sparse_en = 0) processes every input, as a GPU would.
module spark_core #(
    parameter P = 8,
    parameter CTX = 3,              // bytes of input context (embedding tables)
    parameter EMB_HEX = "emb.hex",
    parameter EMB1_HEX = "emb1.hex",
    parameter EMB2_HEX = "emb2.hex",
    parameter TH0_HEX = "th0.hex",
    parameter TH1_HEX = "th1.hex",
    parameter W0_HEX = "w0.hex",
    parameter W1_HEX = "w1.hex",
    parameter W2_HEX = "w2.hex",
    parameter W3_HEX = "w3.hex"
) (
    input             clk,
    input             rst,
    input             start,
    input      [7:0]  in_byte,
    // configuration
    input             sparse_en,
    input             delta_en,
    input             exit_en,
    input             recall_en,
    input      [15:0] cap,
    input      [31:0] exit_th,      // signed
    input      [1:0]  conf_th,
    input      [8:0]  cfg_a,        // membrane decay, Q8
    input      [3:0]  acc_sh,
    input      [3:0]  s_sh,
    input             adapt_en,     // adaptive controller
    input             thr_en,       // 1: threshold spikes min((h-th)>>s_sh,7), 0: signed spikes
    // weight / embedding load port (weights are loaded at boot, e.g. from flash)
    input             ld_we,
    input      [2:0]  ld_sel,       // 0 emb, 1..4 = w0..w3
    input      [10:0] ld_addr,
    input      [63:0] ld_data,
    // results
    output reg        done,
    output reg [7:0]  pred,
    output reg [1:0]  path,         // 0 full, 1 early exit, 2 recall
    output reg [31:0] tok_cycles,
    output reg [31:0] wreads,       // weight words read (P weights each)
    output reg [31:0] cyc_engine,   // cycles the MAC engine was busy
    output reg [31:0] cyc_scan,     // cycles spent scanning inputs
    output reg [31:0] cyc_post,     // membrane / argmax pass cycles
    output reg [31:0] cyc_recall,   // recall unit cycles
    output     [15:0] nz0, nz1, nz2, nz3,
    output     [15:0] pr0, pr1, pr2, pr3
);
    // ------------------------------------------------------------------ states
    localparam S_IDLE = 5'd0, S_RU_RD = 5'd1, S_RU_WR = 5'd2, S_RL_RD = 5'd3,
               S_RL_DEC = 5'd4, S_ST_INIT = 5'd5, S_SC_RD = 5'd6, S_SC_WAIT = 5'd7,
               S_EV_SEL = 5'd8, S_EV_RUN = 5'd9, S_SC_WB = 5'd10, S_PO_RUN = 5'd11,
               S_ST_NEXT = 5'd12, S_DONE = 5'd13,
               S_PRE_RD = 5'd14, S_PRE_ACC = 5'd15, S_CLR = 5'd16,
               S_PO_LAT = 5'd17, S_PO_LANE = 5'd18, S_PO_WR = 5'd19;
    localparam Q = 4;             // lanes per cycle in the membrane / argmax pass

    reg [4:0]  state;
    // adaptive controller state
    reg        use_delta;         // this stage: change-only (1) or full recompute (0)
    reg [7:0]  n_nz, n_dl;        // pre-scan counts: non-zero inputs, changed inputs
    reg [3:0]  score;             // early-exit usefulness score
    reg [15:0] tokcnt, tokq;
    wire       eff_delta = adapt_en ? use_delta : delta_en;
    wire       try_exit  = exit_en && (!adapt_en || score >= 4'd4 || tokq[3:0] == 4'd0);
    reg [1:0]  stg;
    reg [7:0]  byte_r;
    reg [31:0] ctx, ctx_prev;
    // sizes derived from the lane count P
    localparam DM = 64, HM = 128, VM = 256;
    localparam CD = DM / P, CH = HM / P, CV = VM / P;     // chunks per vector
    localparam CD0 = CD * CTX;                            // layer-0 input chunks (context window)
    reg [7:0]  hist1, hist2;      // previous two input bytes
    reg [1:0]  started;           // tokens seen, saturating at CTX
    localparam AWC = 6;                                   // chunk-address width
    reg [5:0]  c;                 // source chunk
    reg [P-1:0] mask;
    reg [4*P-1:0] srcw, sentw;
    reg [7:0]  ev_j;
    reg signed [4:0] ev_v;
    reg [6:0]  e;                 // engine step 0..NC
    reg [6:0]  m;                 // post-pass step 0..NCo
    reg signed [31:0] t1, t2;
    reg [7:0]  idx;
    reg [15:0] nzc [0:3];
    reg [15:0] prc [0:3];
    assign nz0 = nzc[0]; assign nz1 = nzc[1]; assign nz2 = nzc[2]; assign nz3 = nzc[3];
    assign pr0 = prc[0]; assign pr1 = prc[1]; assign pr2 = prc[2]; assign pr3 = prc[3];

    wire [6:0] nin_ch = (stg == 2'd0) ? CD0 : CH;          // source chunks
    wire [6:0] nc     = (stg[1]) ? CV : CH;                 // output chunks
    wire       is_head = stg[1];

    // ---------------------------------------------------------------- memories
    // read addresses / write controls are driven combinationally below
    reg  [11:0] emb_ra, emb1_ra, emb2_ra, w0_ra, w1_ra, w2_ra, w3_ra;
    wire [4*P-1:0] emb_rd, emb1_rd, emb2_rd, w0_rd, w1_rd, w2_rd, w3_rd;
    spark_bram #(4*P, VM*CD, 12, EMB_HEX)  u_emb  (clk, ld_we && ld_sel == 3'd0, ld_addr, ld_data[4*P-1:0], emb_ra, emb_rd);
    spark_bram #(4*P, VM*CD, 12, EMB1_HEX) u_emb1 (clk, ld_we && ld_sel == 3'd5, ld_addr, ld_data[4*P-1:0], emb1_ra, emb1_rd);
    spark_bram #(4*P, VM*CD, 12, EMB2_HEX) u_emb2 (clk, ld_we && ld_sel == 3'd6, ld_addr, ld_data[4*P-1:0], emb2_ra, emb2_rd);
    spark_bram #(4*P, DM*CTX*CH, 12, W0_HEX) u_w0 (clk, ld_we && ld_sel == 3'd1, ld_addr, ld_data[4*P-1:0], w0_ra, w0_rd);
    // per-neuron firing thresholds (16-bit), one word of P lanes per chunk
    reg  [AWC-1:0] th_ra; wire [16*P-1:0] th0_rd, th1_rd;
    spark_ram #(16*P, CH, AWC, TH0_HEX) u_th0 (clk, 1'b0, {AWC{1'b0}}, {16*P{1'b0}}, th_ra, th0_rd);
    spark_ram #(16*P, CH, AWC, TH1_HEX) u_th1 (clk, 1'b0, {AWC{1'b0}}, {16*P{1'b0}}, th_ra, th1_rd);
    spark_bram #(4*P, HM*CH, 12, W1_HEX)  u_w1  (clk, ld_we && ld_sel == 3'd2, ld_addr, ld_data[4*P-1:0], w1_ra, w1_rd);
    spark_bram #(4*P, HM*CV, 12, W2_HEX)  u_w2  (clk, ld_we && ld_sel == 3'd3, ld_addr, ld_data[4*P-1:0], w2_ra, w2_rd);
    spark_bram #(4*P, HM*CV, 12, W3_HEX)  u_w3  (clk, ld_we && ld_sel == 3'd4, ld_addr, ld_data[4*P-1:0], w3_ra, w3_rd);

    reg acc_we [0:3]; reg [AWC-1:0] acc_wa [0:3]; reg [16*P-1:0] acc_wd [0:3]; reg [AWC-1:0] acc_ra [0:3];
    wire [16*P-1:0] acc_rd [0:3];
    spark_ram #(16*P, CH, AWC) u_acc0 (clk, acc_we[0], acc_wa[0], acc_wd[0], acc_ra[0], acc_rd[0]);
    spark_ram #(16*P, CH, AWC) u_acc1 (clk, acc_we[1], acc_wa[1], acc_wd[1], acc_ra[1], acc_rd[1]);
    spark_ram #(16*P, CV, AWC) u_acc2 (clk, acc_we[2], acc_wa[2], acc_wd[2], acc_ra[2], acc_rd[2]);
    spark_ram #(16*P, CV, AWC) u_acc3 (clk, acc_we[3], acc_wa[3], acc_wd[3], acc_ra[3], acc_rd[3]);

    reg h_we [0:1]; reg [AWC-1:0] h_wa [0:1]; reg [16*P-1:0] h_wd [0:1]; reg [AWC-1:0] h_ra [0:1];
    wire [16*P-1:0] h_rd [0:1];
    spark_ram #(16*P, CH, AWC) u_h0 (clk, h_we[0], h_wa[0], h_wd[0], h_ra[0], h_rd[0]);
    spark_ram #(16*P, CH, AWC) u_h1 (clk, h_we[1], h_wa[1], h_wd[1], h_ra[1], h_rd[1]);

    reg s_we [0:1]; reg [AWC-1:0] s_wa [0:1]; reg [4*P-1:0] s_wd [0:1]; reg [AWC-1:0] s_ra [0:1];
    wire [4*P-1:0] s_rd [0:1];
    spark_ram #(4*P, CH, AWC) u_s0 (clk, s_we[0], s_wa[0], s_wd[0], s_ra[0], s_rd[0]);
    spark_ram #(4*P, CH, AWC) u_s1 (clk, s_we[1], s_wa[1], s_wd[1], s_ra[1], s_rd[1]);

    reg sn_we [0:3]; reg [AWC-1:0] sn_wa [0:3]; reg [4*P-1:0] sn_wd [0:3]; reg [AWC-1:0] sn_ra [0:3];
    wire [4*P-1:0] sn_rd [0:3];
    spark_ram #(4*P, CD0, AWC) u_sn0 (clk, sn_we[0], sn_wa[0], sn_wd[0], sn_ra[0], sn_rd[0]);
    spark_ram #(4*P, CH, AWC) u_sn1 (clk, sn_we[1], sn_wa[1], sn_wd[1], sn_ra[1], sn_rd[1]);
    spark_ram #(4*P, CH, AWC) u_sn2 (clk, sn_we[2], sn_wa[2], sn_wd[2], sn_ra[2], sn_rd[2]);
    spark_ram #(4*P, CH, AWC) u_sn3 (clk, sn_we[3], sn_wa[3], sn_wd[3], sn_ra[3], sn_rd[3]);

    // recall table entry: {valid[42], tag[41:10], value[9:2], conf[1:0]}
    // stored as two block RAMs (33-bit valid+tag, 10-bit value+conf) so each fits
    // the 36-bit simple-dual-port block RAM mode
    reg        t_we; reg [9:0] t_wa, t_ra; reg [42:0] t_wd; wire [42:0] t_rd;
    spark_spram #(33, 1024, 10) u_tab_tag (clk, t_we, t_wa, t_wd[42:10], t_ra, t_rd[42:10]);
    spark_spram #(10, 1024, 10) u_tab_dat (clk, t_we, t_wa, t_wd[9:0],   t_ra, t_rd[9:0]);

    // recall context = last 3 bytes; multiplicative (Fibonacci) hash -> 10-bit slot
    localparam [31:0] CTX_MASK = 32'h00FF_FFFF;
    function [9:0] rhash(input [31:0] x);
        reg [31:0] y;
        begin y = x * 32'h9E37_79B1; rhash = y[31:22]; end
    endfunction

    // ------------------------------------------------------- stage data muxes
    reg [4*P-1:0] src_rd, sent_rd, w_rd;
    reg [16*P-1:0] acc_rd_s;
    always @* begin
        case (stg)
            2'd0: begin
                w_rd = w0_rd;
                case (c / CD)
                    0: src_rd = emb_rd;
                    1: src_rd = (started > 2'd1) ? emb1_rd : {4*P{1'b0}};
                    default: src_rd = (started > 2'd2) ? emb2_rd : {4*P{1'b0}};
                endcase
            end
            2'd1: begin src_rd = s_rd[0]; w_rd = w1_rd; end
            2'd2: begin src_rd = s_rd[0]; w_rd = w2_rd; end
            default: begin src_rd = s_rd[1]; w_rd = w3_rd; end
        endcase
        sent_rd  = sn_rd[stg];
        acc_rd_s = acc_rd[stg];
    end

    // per-lane event values from the freshly read words (SC_WAIT) and from the
    // latched words (EV_SEL)
    integer l0, l1, l2, l3, l4, l5;
    reg [P-1:0] nzmask_rd, srcnz_rd, chg_rd;
    reg [7:0]   pc_nz, pc_dl;
    always @* begin
        pc_nz = 8'd0; pc_dl = 8'd0;
        for (l0 = 0; l0 < P; l0 = l0 + 1) begin
            pc_nz = pc_nz + srcnz_rd[l0];
            pc_dl = pc_dl + chg_rd[l0];
        end
    end
    reg signed [4:0] vlat [0:P-1];
    reg signed [4:0] vtmp;
    always @* begin
        for (l1 = 0; l1 < P; l1 = l1 + 1) begin
            vtmp = eff_delta ? ($signed(src_rd[4*l1 +: 4]) - $signed(sent_rd[4*l1 +: 4]))
                             : $signed(src_rd[4*l1 +: 4]);
            nzmask_rd[l1] = (vtmp != 0);
            srcnz_rd[l1]  = (src_rd[4*l1 +: 4] != 4'd0);
            chg_rd[l1]    = (src_rd[4*l1 +: 4] != sent_rd[4*l1 +: 4]);
            vlat[l1] = eff_delta ? ($signed(srcw[4*l1 +: 4]) - $signed(sentw[4*l1 +: 4]))
                                 : $signed(srcw[4*l1 +: 4]);
        end
    end
    reg [3:0] sel;
    always @* begin
        sel = 4'd0;
        for (l2 = P - 1; l2 >= 0; l2 = l2 - 1) if (mask[l2]) sel = l2[3:0];
    end

    // engine: acc += w * v for P lanes
    reg [16*P-1:0] acc_new;
    always @* begin
        for (l3 = 0; l3 < P; l3 = l3 + 1)
            acc_new[16*l3 +: 16] = $signed(acc_rd_s[16*l3 +: 16])
                                 + $signed(w_rd[4*l3 +: 4]) * ev_v;
    end

    // post pass (membrane/spike or argmax): one chunk is latched, then
    // processed Q lanes per cycle to keep the logic small
    reg [16*P-1:0] po_acc, po_h, po_th, h_neww;
    reg [4*P-1:0]  s_neww;
    reg [1:0]      q;
    reg [16*Q-1:0] h_grp;
    reg [4*Q-1:0]  s_grp;
    reg signed [24:0] dec;
    reg signed [25:0] sum;
    reg signed [15:0] hs, hl, al, tl;
    reg signed [17:0] u, us;
    reg [16:0] mag;
    reg signed [4:0] sp;
    reg signed [16:0] hr;
    always @* begin
        for (l4 = 0; l4 < Q; l4 = l4 + 1) begin
            hl  = po_h[16*(q*Q + l4) +: 16];
            al  = po_acc[16*(q*Q + l4) +: 16];
            dec = ($signed(hl) * $signed({1'b0, cfg_a})) >>> 8;
            sum = dec + ($signed(al) >>> acc_sh);
            hs  = (sum > 26'sd32767) ? 16'sd32767 : (sum < -26'sd32768) ? -16'sd32768 : sum[15:0];
            mag = (hs < 0) ? (-{hs[15], hs}) : {1'b0, hs};
            mag = mag >> s_sh;
            if (mag > 17'd7) mag = 17'd7;
            sp  = (hs < 0) ? -$signed({1'b0, mag[3:0]}) : $signed({1'b0, mag[3:0]});
            if (thr_en) begin
                tl = po_th[16*(q*Q + l4) +: 16];
                u  = $signed(hs) - $signed(tl);
                us = u >>> s_sh;
                sp = (us < 0) ? 5'sd0 : (us > 7) ? 5'sd7 : us[4:0];
            end
            hr  = $signed(hs) - ($signed(sp) <<< s_sh);
            h_grp[16*l4 +: 16] = hr[15:0];
            s_grp[4*l4 +: 4]   = sp[3:0];
        end
    end

    // argmax over Q lanes, continuing the running top-1 / top-2
    reg signed [31:0] n1, n2, xv;
    reg [7:0] nidx;
    always @* begin
        n1 = t1; n2 = t2; nidx = idx;
        for (l5 = 0; l5 < Q; l5 = l5 + 1) begin
            xv = $signed(po_acc[16*(q*Q + l5) +: 16]);
            if (xv > n1) begin n2 = n1; n1 = xv; nidx = m * P + q * Q + l5; end
            else if (xv > n2) n2 = xv;
        end
    end

    // ---------------------------------------------- memory port control (comb)
    integer k, kf;
    always @* begin
        emb_ra  = byte_r * CD + (c % CD);
        emb1_ra = hist1 * CD + (c % CD);
        emb2_ra = hist2 * CD + (c % CD);
        th_ra = m;
        w0_ra = 12'd0; w1_ra = 12'd0; w2_ra = 12'd0; w3_ra = 12'd0;
        for (k = 0; k < 4; k = k + 1) begin
            acc_we[k] = 1'b0; acc_wa[k] = 0; acc_wd[k] = {16*P{1'b0}}; acc_ra[k] = 0;
            sn_we[k] = 1'b0; sn_wa[k] = 0; sn_wd[k] = sentw; sn_ra[k] = c;
        end
        for (k = 0; k < 2; k = k + 1) begin
            h_we[k] = 1'b0; h_wa[k] = 0; h_wd[k] = h_neww; h_ra[k] = 0;
            s_we[k] = 1'b0; s_wa[k] = 0; s_wd[k] = s_neww; s_ra[k] = c;
        end
        t_we = 1'b0; t_wa = rhash(ctx_prev); t_ra = rhash(ctx_prev); t_wd = 43'd0;

        case (state)
            S_RU_RD: t_ra = rhash(ctx_prev);
            S_RU_WR: begin
                t_we = 1'b1; t_wa = rhash(ctx_prev);
                if (t_rd[42] && t_rd[41:10] == ctx_prev)
                    t_wd = (t_rd[9:2] == byte_r)
                         ? {1'b1, ctx_prev, byte_r, (t_rd[1:0] == 2'd3) ? 2'd3 : t_rd[1:0] + 2'd1}
                         : {1'b1, ctx_prev, byte_r, 2'd0};
                else
                    t_wd = {1'b1, ctx_prev, byte_r, 2'd0};
            end
            S_RL_RD: t_ra = rhash(ctx);
            S_EV_RUN: begin
                if (e < nc) begin
                    w0_ra = ev_j * CH + e;
                    w1_ra = ev_j * CH + e;
                    w2_ra = ev_j * CV + e;
                    w3_ra = ev_j * CV + e;
                    acc_ra[stg] = e;
                end
                if (e >= 1) begin
                    acc_we[stg] = 1'b1; acc_wa[stg] = e - 1; acc_wd[stg] = acc_new;
                end
            end
            S_SC_WB: begin
                sn_we[stg] = delta_en | adapt_en; sn_wa[stg] = c;
            end
            S_CLR: begin
                acc_we[stg] = 1'b1; acc_wa[stg] = m; acc_wd[stg] = {16*P{1'b0}};
            end
            S_PO_RUN: begin
                acc_ra[stg] = m;
                h_ra[stg[0]] = m;
            end
            S_PO_WR: begin
                if (!delta_en && !adapt_en) begin
                    acc_we[stg] = 1'b1; acc_wa[stg] = m; acc_wd[stg] = {16*P{1'b0}};
                end
                if (!is_head) begin
                    h_we[stg[0]] = 1'b1; h_wa[stg[0]] = m;
                    s_we[stg[0]] = 1'b1; s_wa[stg[0]] = m;
                end
            end
            default: ;
        endcase
    end

    // ------------------------------------------------------------- main FSM
    always @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE; done <= 1'b0; ctx_prev <= 32'd0; ctx <= 32'd0;
            stg <= 2'd0; score <= 4'd8; tokcnt <= 16'd0; tokq <= 16'd0;
            hist1 <= 8'd0; hist2 <= 8'd0; started <= 2'd0; byte_r <= 8'd0;
        end else begin
            done <= 1'b0;
            if (state != S_IDLE) tok_cycles <= tok_cycles + 1;
            case (state)
                S_IDLE: if (start) begin
                    byte_r <= in_byte; tok_cycles <= 32'd1;
                    hist1 <= byte_r; hist2 <= hist1;
                    if (started != CTX) started <= started + 2'd1;
                    tokq <= tokcnt; tokcnt <= tokcnt + 16'd1;
                    wreads <= 0; cyc_engine <= 0; cyc_scan <= 0; cyc_post <= 0; cyc_recall <= 0;
                    for (kf = 0; kf < 4; kf = kf + 1) begin nzc[kf] <= 0; prc[kf] <= 0; end
                    if (recall_en) state <= S_RU_RD;
                    else begin
                        ctx_prev <= {ctx_prev[23:0], in_byte} & CTX_MASK;
                        stg <= 2'd0; state <= S_ST_INIT;
                    end
                end
                S_RU_RD:  begin cyc_recall <= cyc_recall + 1; state <= S_RU_WR; end
                S_RU_WR:  begin
                    cyc_recall <= cyc_recall + 1;
                    ctx <= {ctx_prev[23:0], byte_r} & CTX_MASK;
                    state <= S_RL_RD;
                end
                S_RL_RD:  begin cyc_recall <= cyc_recall + 1; ctx_prev <= ctx; state <= S_RL_DEC; end
                S_RL_DEC: begin
                    cyc_recall <= cyc_recall + 1;
                    if (t_rd[42] && t_rd[41:10] == ctx && t_rd[1:0] >= conf_th) begin
                        pred <= t_rd[9:2]; path <= 2'd2; state <= S_DONE;
                    end else begin
                        stg <= 2'd0; state <= S_ST_INIT;
                    end
                end
                S_ST_INIT: begin
                    c <= 4'd0; n_nz <= 8'd0; n_dl <= 8'd0;
                    state <= adapt_en ? S_PRE_RD : S_SC_RD;
                end
                // adaptive pre-scan: count non-zero and changed inputs, then pick
                // the cheaper way to update this stage
                S_PRE_RD: begin cyc_scan <= cyc_scan + 1; state <= S_PRE_ACC; end
                S_PRE_ACC: begin
                    cyc_scan <= cyc_scan + 1;
                    if (c + 1 == nin_ch) begin
                        use_delta <= (n_dl + pc_dl) <= (n_nz + pc_nz);
                        c <= 4'd0; m <= 5'd0;
                        state <= ((n_dl + pc_dl) <= (n_nz + pc_nz)) ? S_SC_RD : S_CLR;
                    end else begin
                        n_nz <= n_nz + pc_nz; n_dl <= n_dl + pc_dl;
                        c <= c + 1; state <= S_PRE_RD;
                    end
                end
                S_CLR: begin
                    cyc_scan <= cyc_scan + 1;
                    if (m + 1 == nc) state <= S_SC_RD;
                    m <= m + 1;
                end
                S_SC_RD:   begin cyc_scan <= cyc_scan + 1; state <= S_SC_WAIT; end
                S_SC_WAIT: begin
                    cyc_scan <= cyc_scan + 1;
                    srcw <= src_rd;
                    sentw <= (adapt_en && !use_delta) ? {4*P{1'b0}} : sent_rd;
                    mask <= sparse_en ? nzmask_rd : {P{1'b1}};
                    state <= S_EV_SEL;
                end
                S_EV_SEL: begin
                    cyc_scan <= cyc_scan + 1;
                    if (mask == {P{1'b0}}) state <= S_SC_WB;
                    else if (sparse_en && cap != 16'd0 && nzc[stg] >= cap) begin
                        mask <= {P{1'b0}}; state <= S_SC_WB;
                    end else begin
                        ev_j <= c * P + sel;
                        ev_v <= vlat[sel];
                        mask[sel] <= 1'b0;
                        if (delta_en || adapt_en) sentw[4*sel +: 4] <= srcw[4*sel +: 4];
                        prc[stg] <= prc[stg] + 1;
                        if (vlat[sel] != 0) nzc[stg] <= nzc[stg] + 1;
                        e <= 5'd0;
                        state <= S_EV_RUN;
                    end
                end
                S_EV_RUN: begin
                    cyc_engine <= cyc_engine + 1;
                    if (e < nc) wreads <= wreads + 1;
                    if (e == nc) state <= S_EV_SEL;
                    e <= e + 1;
                end
                S_SC_WB: begin
                    cyc_scan <= cyc_scan + 1;
                    if (c + 1 == nin_ch) begin
                        m <= 5'd0; t1 <= -32'sd1073741824; t2 <= -32'sd1073741824; idx <= 8'd0;
                        state <= S_PO_RUN;
                    end else begin
                        c <= c + 1; state <= S_SC_RD;
                    end
                end
                S_PO_RUN: begin cyc_post <= cyc_post + 1; state <= S_PO_LAT; end
                S_PO_LAT: begin
                    cyc_post <= cyc_post + 1;
                    po_acc <= acc_rd_s; po_h <= h_rd[stg[0]]; q <= 2'd0;
                    po_th  <= stg[0] ? th1_rd : th0_rd;
                    state <= S_PO_LANE;
                end
                S_PO_LANE: begin
                    cyc_post <= cyc_post + 1;
                    h_neww[16*Q*q +: 16*Q] <= h_grp;
                    s_neww[4*Q*q +: 4*Q]   <= s_grp;
                    if (is_head) begin t1 <= n1; t2 <= n2; idx <= nidx; end
                    q <= q + 2'd1;
                    if (q == P / Q - 1) state <= S_PO_WR;
                end
                S_PO_WR: begin
                    cyc_post <= cyc_post + 1;
                    if (m + 1 == nc) state <= S_ST_NEXT;
                    else state <= S_PO_RUN;
                    m <= m + 1;
                end
                S_ST_NEXT: begin
                    case (stg)
                        2'd0: begin stg <= try_exit ? 2'd2 : 2'd1; state <= S_ST_INIT; end
                        2'd2: if ($signed(t1 - t2) >= $signed(exit_th)) begin
                                  pred <= idx; path <= 2'd1; state <= S_DONE;
                                  score <= (score >= 4'd13) ? 4'd15 : score + 4'd2;
                              end else begin
                                  stg <= 2'd1; state <= S_ST_INIT;
                                  score <= (score == 4'd0) ? 4'd0 : score - 4'd1;
                              end
                        2'd1: begin stg <= 2'd3; state <= S_ST_INIT; end
                        default: begin pred <= idx; path <= 2'd0; state <= S_DONE; end
                    endcase
                end
                S_DONE: begin done <= 1'b1; state <= S_IDLE; end
                default: state <= S_IDLE;
            endcase
        end
    end
endmodule
