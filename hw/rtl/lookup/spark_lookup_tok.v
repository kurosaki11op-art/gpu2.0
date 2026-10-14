// SPARK-L token core: a token-level lookup drafter for real LLM speculative decoding. No matrices, no multipliers.
// Bit-exact with TokCore in hw/system/lookup_tok_ref.py (the design whose acceptance token_lookup_test.py measured).
//
// Commands (when busy = 0):
//   cmd_op = 0 LEARN cmd_tok : a token the big model committed. Updates every order (1-4 tokens of context) whose context
//                              exists, then appends the token to the history. done pulses at the end.
//   cmd_op = 1 DRAFT cmd_k   : propose up to cmd_k tokens by chaining lookups from the committed history (highest order
//                              first, stop at the first miss). One d_valid pulse per token with d_tok, d_src (order 1-4 as 0-3)
//                              and d_cnt (that entry's counter); then done with d_n = number proposed. Drafting never writes.
// Tables: 4 x 2^TB entries of {valid, tag[11:0], value[TW-1:0], count[1:0]}. Hash: CRC-32 (XOR and shifts) over the last
// o tokens as 4 little-endian bytes each, oldest first, start value = order index + 1; one token per clock cycle.
// Cycle cost: LEARN about 18 cycles; DRAFT up to about 18 cycles per proposed token (about 5 us for 8 tokens at 27 MHz).
module spark_lookup_tok #(
    parameter TB = 12,
    parameter TW = 18                     // token-ID width (2^18 = 262,144 >= common LLM vocabularies)
) (
    input              clk,
    input              rst,
    input              cmd_valid,
    input              cmd_op,
    input  [TW-1:0]    cmd_tok,
    input  [3:0]       cmd_k,
    output             busy,
    output reg         d_valid,
    output reg [TW-1:0] d_tok,
    output reg [1:0]   d_src,
    output reg [1:0]   d_cnt,
    output reg         done,
    output reg [3:0]   d_n
);
    localparam EW = 1 + 12 + TW + 2;

    function [31:0] crc_tok;              // fold one token (4 little-endian bytes) into a running CRC-32
        input [31:0] c_in;
        input [TW-1:0] tok;
        integer j, b;
        reg [31:0] c, x;
        begin
            c = c_in; x = {{(32 - TW){1'b0}}, tok};
            for (j = 0; j < 4; j = j + 1) begin
                c = c ^ {24'd0, x[8*j +: 8]};
                for (b = 0; b < 8; b = b + 1)
                    c = c[0] ? ((c >> 1) ^ 32'hEDB8_8320) : (c >> 1);
            end
            crc_tok = c;
        end
    endfunction

    // committed history (H0 = newest) and the draft's private copy
    reg [TW-1:0] H0, H1, H2, H3, D0, D1, D2, D3;
    reg [2:0]    hlen, dlen;
    reg          mode;                    // 0 learn, 1 draft
    reg [TW-1:0] t_r;
    reg [3:0]    kmax, n;
    reg [1:0]    k, j;
    reg [31:0]   c;
    reg [TB-1:0] slot_r; reg [11:0] tag_r;
    reg [TB-1:0] clr;

    localparam S_CLR = 4'd0, S_IDLE = 4'd1, S_K = 4'd2, S_H = 4'd3, S_RD = 4'd4, S_USE = 4'd5, S_SHIFT = 4'd6, S_DONE = 4'd7;
    reg [3:0] st;
    assign busy = (st != S_IDLE);

    // token j of the history being hashed (0 = newest)
    reg [TW-1:0] hsel;
    always @* begin
        case (j)
            2'd0: hsel = mode ? D0 : H0;
            2'd1: hsel = mode ? D1 : H1;
            2'd2: hsel = mode ? D2 : H2;
            default: hsel = mode ? D3 : H3;
        endcase
    end
    wire [2:0]  len_cur = mode ? dlen : hlen;
    wire [31:0] cnext = crc_tok(c, hsel);
    wire [31:0] cv = c ^ 32'hFFFF_FFFF;    // final CRC value once all o tokens are folded in

    // ------------------------------------------------------------------ tables (one op per table per cycle)
    reg  [TB-1:0] ra, wa; reg [EW-1:0] wd; reg [3:0] re_v, we_v;
    wire [EW-1:0] rd0, rd1, rd2, rd3;
    spark_lkt_ram #(EW, TB) u_t0 (clk, we_v[0], wa, wd, re_v[0], ra, rd0);
    spark_lkt_ram #(EW, TB) u_t1 (clk, we_v[1], wa, wd, re_v[1], ra, rd1);
    spark_lkt_ram #(EW, TB) u_t2 (clk, we_v[2], wa, wd, re_v[2], ra, rd2);
    spark_lkt_ram #(EW, TB) u_t3 (clk, we_v[3], wa, wd, re_v[3], ra, rd3);
    reg [EW-1:0] e;
    always @* case (k) 2'd0: e = rd0; 2'd1: e = rd1; 2'd2: e = rd2; default: e = rd3; endcase
    wire e_hit = e[EW-1] && e[EW-2 -: 12] == tag_r;
    wire [TW-1:0] e_val = e[TW+1:2];
    wire [1:0]    e_cnt = e[1:0];

    // learned entry (hysteresis)
    reg [EW-1:0] learned;
    always @* begin
        if (e_hit) begin
            if (e_val == t_r)        learned = {1'b1, tag_r, e_val, (e_cnt == 2'd3) ? 2'd3 : e_cnt + 2'd1};
            else if (e_cnt != 2'd0)  learned = {1'b1, tag_r, e_val, e_cnt - 2'd1};
            else                     learned = {1'b1, tag_r, t_r, 2'd0};
        end else                     learned = {1'b1, tag_r, t_r, 2'd0};
    end

    always @* begin                         // memory port control (combinational; writes land on the edge ending their state)
        re_v = 4'b0000; we_v = 4'b0000; ra = cv[31:32-TB]; wa = slot_r; wd = learned;
        if (st == S_CLR) begin we_v = 4'b1111; wa = clr; wd = {EW{1'b0}}; end
        else if (st == S_RD) re_v[k] = 1'b1;
        else if (st == S_USE && !mode) we_v[k] = 1'b1;
    end

    always @(posedge clk) begin
        d_valid <= 1'b0; done <= 1'b0;
        if (rst) begin
            st <= S_CLR; clr <= {TB{1'b0}}; hlen <= 3'd0;
        end else case (st)
            S_CLR: begin clr <= clr + 1'b1; if (clr == {TB{1'b1}}) st <= S_IDLE; end
            S_IDLE: if (cmd_valid) begin
                mode <= cmd_op; t_r <= cmd_tok; kmax <= cmd_k; n <= 4'd0;
                D0 <= H0; D1 <= H1; D2 <= H2; D3 <= H3; dlen <= hlen;
                k <= cmd_op ? 2'd3 : 2'd0;
                st <= (cmd_op && cmd_k == 4'd0) ? S_DONE : S_K;
            end
            S_K: begin                         // does order k have a context? learn walks k up, draft walks k down
                if (len_cur >= {1'b0, k} + 3'd1) begin c <= {30'd0, k} + 32'd1 ^ 32'hFFFF_FFFF; j <= k; st <= S_H; end
                else if (!mode) begin if (k == 2'd3) st <= S_SHIFT; else k <= k + 2'd1; end
                else begin if (k == 2'd0) st <= S_DONE; else k <= k - 2'd1; end
            end
            S_H: begin                         // fold tokens j = k .. 0 (oldest first), one per cycle
                c <= cnext;
                if (j == 2'd0) st <= S_RD; else j <= j - 2'd1;
            end
            S_RD: begin slot_r <= cv[31:32-TB]; tag_r <= cv[15:4]; st <= S_USE; end
            S_USE: begin
                if (!mode) begin              // learn: the write is issued combinationally in this state
                    if (k == 2'd3) st <= S_SHIFT; else begin k <= k + 2'd1; st <= S_K; end
                end else if (e_hit) begin     // draft: propose this token, extend the draft history, restart from order 4
                    d_valid <= 1'b1; d_tok <= e_val; d_src <= k; d_cnt <= e_cnt;
                    D3 <= D2; D2 <= D1; D1 <= D0; D0 <= e_val; if (dlen != 3'd4) dlen <= dlen + 3'd1;
                    n <= n + 4'd1; k <= 2'd3;
                    st <= (n + 4'd1 == kmax) ? S_DONE : S_K;
                end else begin
                    if (k == 2'd0) st <= S_DONE; else begin k <= k - 2'd1; st <= S_K; end
                end
            end
            S_SHIFT: begin
                H3 <= H2; H2 <= H1; H1 <= H0; H0 <= t_r; if (hlen != 3'd4) hlen <= hlen + 3'd1;
                st <= S_DONE;
            end
            S_DONE: begin done <= 1'b1; d_n <= n; st <= S_IDLE; end
            default: st <= S_IDLE;
        endcase
    end
endmodule

module spark_lkt_ram #(
    parameter W = 33,
    parameter AW = 12
) (
    input               clk,
    input               we,
    input  [AW-1:0]     wa,
    input  [W-1:0]      wd,
    input               re,
    input  [AW-1:0]     ra,
    output reg [W-1:0]  rd
);
    (* ram_style = "block", no_rw_check *) reg [W-1:0] mem [0:(1 << AW) - 1];
    always @(posedge clk) begin
        if (we) mem[wa] <= wd;
        if (re) rd <= mem[ra];
    end
endmodule
