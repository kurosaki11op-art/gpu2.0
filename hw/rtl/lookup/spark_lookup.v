// SPARK-L: a lookup-only predictor core. No matrices, no multipliers, no weights.
//
// Per input byte it (1) updates four hashed recall tables with the byte that just followed each stored context
// (a local, one-pass, gradient-free learning rule: hysteresis counters) and (2) looks up the new context and answers
// with the highest-order table that hits, else a space.
//
// Operations used: XOR, shifts (CRC-32 hash), compares, 2-bit counters, RAM reads and writes. Bit-exact with
// hw/system/lookup_ref.py (which matches hw/system/hash_study.py "crc" and the accuracy numbers in hw/results/matrix_free.md).
//
// Table entry (23 bits): {valid, tag[11:0], value[7:0], count[1:0]}.  4 tables x 2^TB entries.
// Cycles per byte: 5 (4 for the first byte after reset, which has no stored context to learn from). The clear sweep after reset takes 2^TB cycles.
module spark_lookup #(
    parameter TB = 12                    // log2(entries per table)
) (
    input             clk,
    input             rst,
    input             in_valid,          // present a byte (only when busy == 0)
    input      [7:0]  in_byte,
    output            busy,              // high while clearing after reset or processing a byte
    output reg        out_valid,         // one-cycle pulse: prediction for the NEXT byte is ready
    output reg [7:0]  pred,
    output reg        hit,               // a table answered (else pred = 0x20)
    output reg [1:0]  order_idx,         // which table answered: 0..3 = order 2, 3, 4, 6
    output reg [1:0]  count              // that entry's confidence counter
);
    localparam NORD = 4;
    localparam [5:0] ORD0 = 6'd2, ORD1 = 6'd3, ORD2 = 6'd4, ORD3 = 6'd6;      // context bytes per table
    localparam EW = 23;

    // ------------------------------------------------------------------ CRC-32 hash (XOR and shifts only)
    // zlib.crc32(x.to_bytes(6, "little"), salt): reflected polynomial 0xEDB88320, start value = salt.
    function [31:0] crc6;
        input [47:0] x;
        input [31:0] salt;
        integer j, b;
        reg [31:0] c;
        begin
            c = salt ^ 32'hFFFF_FFFF;
            for (j = 0; j < 6; j = j + 1) begin
                c = c ^ {24'd0, x[8*j +: 8]};
                for (b = 0; b < 8; b = b + 1)
                    c = c[0] ? ((c >> 1) ^ 32'hEDB8_8320) : (c >> 1);
            end
            crc6 = c ^ 32'hFFFF_FFFF;
        end
    endfunction

    reg [47:0] hist;                              // last six bytes, newest in the low byte
    wire [47:0] m0 = hist & ((48'd1 << (8 * ORD0)) - 48'd1);
    wire [47:0] m1 = hist & ((48'd1 << (8 * ORD1)) - 48'd1);
    wire [47:0] m2 = hist & ((48'd1 << (8 * ORD2)) - 48'd1);
    wire [47:0] m3 = hist & ((48'd1 << (8 * ORD3)) - 48'd1);
    wire [31:0] hv0 = crc6(m0, 32'd1), hv1 = crc6(m1, 32'd2), hv2 = crc6(m2, 32'd3), hv3 = crc6(m3, 32'd4);
    wire [TB-1:0] ns0 = hv0[31:32-TB], ns1 = hv1[31:32-TB], ns2 = hv2[31:32-TB], ns3 = hv3[31:32-TB];
    wire [11:0]   nt0 = hv0[15:4],     nt1 = hv1[15:4],     nt2 = hv2[15:4],     nt3 = hv3[15:4];

    // slot and tag of the context that ended at the previous byte (used to learn the byte that followed it)
    reg [TB-1:0] ps0, ps1, ps2, ps3;
    reg [11:0]   pt0, pt1, pt2, pt3;
    reg          have_ctx;

    // ------------------------------------------------------------------ the four tables
    reg  [TB-1:0] ra0, ra1, ra2, ra3, wa0, wa1, wa2, wa3;
    reg           we0, we1, we2, we3;
    reg  [EW-1:0] wd0, wd1, wd2, wd3;
    wire [EW-1:0] rd0, rd1, rd2, rd3;
    spark_lk_ram #(EW, TB) u_t0 (clk, we0, wa0, wd0, ra0, rd0);
    spark_lk_ram #(EW, TB) u_t1 (clk, we1, wa1, wd1, ra1, rd1);
    spark_lk_ram #(EW, TB) u_t2 (clk, we2, wa2, wd2, ra2, rd2);
    spark_lk_ram #(EW, TB) u_t3 (clk, we3, wa3, wd3, ra3, rd3);

    // hysteresis update of one entry: value b followed the stored context
    function [EW-1:0] learn;
        input [EW-1:0] e;                          // entry read from the table
        input [11:0]   tag;                        // tag of the stored context
        input [7:0]    b;
        reg v; reg [11:0] et; reg [7:0] ev; reg [1:0] ec;
        begin
            v = e[22]; et = e[21:10]; ev = e[9:2]; ec = e[1:0];
            if (v && et == tag) begin
                if (ev == b)      learn = {1'b1, tag, ev, (ec == 2'd3) ? 2'd3 : ec + 2'd1};
                else if (ec != 0) learn = {1'b1, tag, ev, ec - 2'd1};
                else              learn = {1'b1, tag, b, 2'd0};
            end else              learn = {1'b1, tag, b, 2'd0};
        end
    endfunction

    // ------------------------------------------------------------------ control
    localparam S_CLR = 3'd0, S_IDLE = 3'd1, S_URD = 3'd2, S_UWR = 3'd3, S_PRD = 3'd4, S_PCAP = 3'd5;
    reg [2:0]    st;
    reg [TB-1:0] clr;
    reg [7:0]    b_r;
    assign busy = (st != S_IDLE);

    // read address mux: previous-context slots while learning, new-context slots while predicting
    always @* begin
        if (st == S_URD) begin ra0 = ps0; ra1 = ps1; ra2 = ps2; ra3 = ps3; end
        else             begin ra0 = ns0; ra1 = ns1; ra2 = ns2; ra3 = ns3; end
    end

    // write port, driven combinationally so that a write lands on the clock edge that ends its state
    // (a registered write would collide with the next state's read of the same slot)
    always @* begin
        {we0, we1, we2, we3} = 4'b0000;
        {wa0, wa1, wa2, wa3} = {4{ {TB{1'b0}} }};
        {wd0, wd1, wd2, wd3} = {4{ {EW{1'b0}} }};
        if (st == S_CLR) begin                     // zero every entry (valid = 0): silicon has no power-on contents
            {we0, we1, we2, we3} = 4'b1111;
            wa0 = clr; wa1 = clr; wa2 = clr; wa3 = clr;
        end else if (st == S_UWR && have_ctx) begin // learn the byte that followed each stored context
            {we0, we1, we2, we3} = 4'b1111;
            wa0 = ps0; wa1 = ps1; wa2 = ps2; wa3 = ps3;
            wd0 = learn(rd0, pt0, b_r); wd1 = learn(rd1, pt1, b_r);
            wd2 = learn(rd2, pt2, b_r); wd3 = learn(rd3, pt3, b_r);
        end
    end

    // entries chosen by tag compare, highest order first
    wire h0 = rd0[22] && rd0[21:10] == pt0;
    wire h1 = rd1[22] && rd1[21:10] == pt1;
    wire h2 = rd2[22] && rd2[21:10] == pt2;
    wire h3 = rd3[22] && rd3[21:10] == pt3;

    always @(posedge clk) begin
        out_valid <= 1'b0;
        if (rst) begin
            st <= S_CLR; clr <= {TB{1'b0}}; hist <= 48'd0; have_ctx <= 1'b0;
        end else case (st)
            S_CLR: begin
                clr <= clr + 1'b1;
                if (clr == {TB{1'b1}}) st <= S_IDLE;
            end
            S_IDLE: if (in_valid) begin
                b_r <= in_byte;
                st <= have_ctx ? S_URD : S_UWR;
            end
            S_URD: st <= S_UWR;                    // read the four stored-context entries
            S_UWR: begin                           // (the learning write is on the combinational write port above)
                hist <= {hist[39:0], b_r};
                st <= S_PRD;
            end
            S_PRD: begin                           // new-context slots are on the read address; remember them for the next byte's learning
                ps0 <= ns0; ps1 <= ns1; ps2 <= ns2; ps3 <= ns3;
                pt0 <= nt0; pt1 <= nt1; pt2 <= nt2; pt3 <= nt3;
                st <= S_PCAP;
            end
            S_PCAP: begin                          // tags are now in pt*, entries in rd*
                have_ctx <= 1'b1;
                out_valid <= 1'b1;
                if (h3)      begin pred <= rd3[9:2]; hit <= 1'b1; order_idx <= 2'd3; count <= rd3[1:0]; end
                else if (h2) begin pred <= rd2[9:2]; hit <= 1'b1; order_idx <= 2'd2; count <= rd2[1:0]; end
                else if (h1) begin pred <= rd1[9:2]; hit <= 1'b1; order_idx <= 2'd1; count <= rd1[1:0]; end
                else if (h0) begin pred <= rd0[9:2]; hit <= 1'b1; order_idx <= 2'd0; count <= rd0[1:0]; end
                else         begin pred <= 8'h20;    hit <= 1'b0; order_idx <= 2'd0; count <= 2'd0; end
                st <= S_IDLE;
            end
            default: st <= S_IDLE;
        endcase
    end
endmodule

// One write port, one registered read port (block RAM on FPGAs). Contents are cleared by the core after reset.
module spark_lk_ram #(
    parameter W = 23,
    parameter AW = 12
) (
    input               clk,
    input               we,
    input  [AW-1:0]     wa,
    input  [W-1:0]      wd,
    input  [AW-1:0]     ra,
    output reg [W-1:0]  rd
);
    reg [W-1:0] mem [0:(1 << AW) - 1];
    always @(posedge clk) begin
        if (we) mem[wa] <= wd;
        rd <= mem[ra];
    end
endmodule
