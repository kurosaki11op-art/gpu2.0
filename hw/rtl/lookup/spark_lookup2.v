// SPARK-L v2: lookup-only predictor core, no matrices, no multipliers, no weights.
// v2 over v1: 2-way set-associative hashed tables with one LRU bit per set (fewer conflict evictions), a direct-mapped
// order-1 table as fallback, and a 32-entry programmable confidence table indexed by (which table answered, its counter).
// Bit-exact with LookupCoreV2 in hw/system/lookup_ref.py.
//
// Hashed set (47 bits): {lru, way1[22:0], way0[22:0]}, entry = {valid, tag[11:0], value[7:0], count[1:0]}; 4 tables x 2^TB sets.
// Order-1 entry (11 bits): {valid, value[7:0], count[1:0]}, 256 entries indexed by the last byte.
// Confidence bucket: src*4 + count (src 0-3 = hashed order 2/3/4/6, 4 = order-1 table), 20 = nothing answered.
// Cycles per byte: 5 (4 for the first byte). Reads and writes never share a clock edge (block-RAM collisions avoided).
module spark_lookup2 #(
    parameter TB = 11,                   // log2(sets per table); 2 ways per set
    parameter CONF_HEX = "conf_lut.hex"  // initial confidence table (32 x 8 bit); writable at run time through cfg_*
) (
    input             clk,
    input             rst,
    input             in_valid,
    input      [7:0]  in_byte,
    input             cfg_we,            // write one confidence entry
    input      [4:0]  cfg_addr,
    input      [7:0]  cfg_data,
    output            busy,
    output reg        out_valid,
    output reg [7:0]  pred,
    output reg        hit,
    output reg [2:0]  src,               // 0-3 hashed order 2/3/4/6, 4 order-1 table, 5 none
    output reg [1:0]  count,
    output reg [4:0]  bucket,
    output reg [7:0]  conf               // calibrated confidence, 255 = certain
);
    localparam [5:0] ORD0 = 6'd2, ORD1 = 6'd3, ORD2 = 6'd4, ORD3 = 6'd6;
    localparam EW = 23, SW = 47;

    function [31:0] crc6;                // zlib.crc32(x.to_bytes(6, "little"), salt): XOR and shifts only
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

    // hysteresis update of a matching entry's value/count
    function [9:0] bump;                 // {value, count}
        input [9:0] vc;
        input [7:0] b;
        begin
            if (vc[9:2] == b)        bump = {vc[9:2], (vc[1:0] == 2'd3) ? 2'd3 : vc[1:0] + 2'd1};
            else if (vc[1:0] != 0)   bump = {vc[9:2], vc[1:0] - 2'd1};
            else                     bump = {b, 2'd0};
        end
    endfunction

    // learn one 2-way set: hit way is updated and becomes most recently used; a miss installs into an invalid way
    // (way 0 first) or the LRU way, and the other way becomes LRU
    function [SW-1:0] learn2;
        input [SW-1:0] s;
        input [11:0]   tag;
        input [7:0]    b;
        reg [EW-1:0] e0, e1; reg lru, h0, h1, v;
        begin
            e0 = s[22:0]; e1 = s[45:23]; lru = s[46];
            h0 = e0[22] && e0[21:10] == tag; h1 = e1[22] && e1[21:10] == tag;
            if (h0)      begin e0 = {1'b1, tag, bump(e0[9:0], b)}; lru = 1'b1; end
            else if (h1) begin e1 = {1'b1, tag, bump(e1[9:0], b)}; lru = 1'b0; end
            else begin
                v = !e0[22] ? 1'b0 : (!e1[22] ? 1'b1 : lru);
                if (v) e1 = {1'b1, tag, b, 2'd0}; else e0 = {1'b1, tag, b, 2'd0};
                lru = ~v;
            end
            learn2 = {lru, e1, e0};
        end
    endfunction

    reg [47:0] hist;
    wire [47:0] m0 = hist & ((48'd1 << (8 * ORD0)) - 48'd1);
    wire [47:0] m1 = hist & ((48'd1 << (8 * ORD1)) - 48'd1);
    wire [47:0] m2 = hist & ((48'd1 << (8 * ORD2)) - 48'd1);
    wire [47:0] m3 = hist & ((48'd1 << (8 * ORD3)) - 48'd1);
    wire [31:0] hv0 = crc6(m0, 32'd1), hv1 = crc6(m1, 32'd2), hv2 = crc6(m2, 32'd3), hv3 = crc6(m3, 32'd4);
    wire [TB-1:0] ns0 = hv0[31:32-TB], ns1 = hv1[31:32-TB], ns2 = hv2[31:32-TB], ns3 = hv3[31:32-TB];
    wire [11:0]   nt0 = hv0[15:4],     nt1 = hv1[15:4],     nt2 = hv2[15:4],     nt3 = hv3[15:4];

    reg [TB-1:0] ps0, ps1, ps2, ps3;     // slot and tag of the context that ended at the previous byte
    reg [11:0]   pt0, pt1, pt2, pt3;
    reg          have_ctx;

    localparam S_CLR = 3'd0, S_IDLE = 3'd1, S_URD = 3'd2, S_UWR = 3'd3, S_PRD = 3'd4, S_PCAP = 3'd5;
    reg [2:0]    st;
    reg [TB-1:0] clr;
    reg [7:0]    b_r;
    assign busy = (st != S_IDLE);
    wire re = (st == S_URD) || (st == S_PRD);

    // ------------------------------------------------------------------ memories
    reg  [TB-1:0] ra0, ra1, ra2, ra3, wa0, wa1, wa2, wa3;
    reg           we0, we1, we2, we3, we4;
    reg  [SW-1:0] wd0, wd1, wd2, wd3;
    wire [SW-1:0] rd0, rd1, rd2, rd3;
    reg  [7:0]    ra4, wa4;
    reg  [10:0]   wd4;
    wire [10:0]   rd4;
    spark_lk2_ram #(SW, TB) u_t0 (clk, we0, wa0, wd0, re, ra0, rd0);
    spark_lk2_ram #(SW, TB) u_t1 (clk, we1, wa1, wd1, re, ra1, rd1);
    spark_lk2_ram #(SW, TB) u_t2 (clk, we2, wa2, wd2, re, ra2, rd2);
    spark_lk2_ram #(SW, TB) u_t3 (clk, we3, wa3, wd3, re, ra3, rd3);
    spark_lk2_ram #(11, 8)  u_o1 (clk, we4, wa4, wd4, re, ra4, rd4);

    reg [7:0] conf_lut [0:31];
    initial $readmemh(CONF_HEX, conf_lut);
    always @(posedge clk) if (cfg_we) conf_lut[cfg_addr] <= cfg_data;

    always @* begin
        // order-1 table: the last byte is both the context to learn from (before the shift) and to predict from (after it)
        ra4 = hist[7:0];
        if (st == S_URD) begin ra0 = ps0; ra1 = ps1; ra2 = ps2; ra3 = ps3; end
        else             begin ra0 = ns0; ra1 = ns1; ra2 = ns2; ra3 = ns3; end
    end

    // write port (combinational: the write lands on the edge that ends its state)
    always @* begin
        {we0, we1, we2, we3, we4} = 5'b00000;
        {wa0, wa1, wa2, wa3} = {4{ {TB{1'b0}} }}; wa4 = 8'd0;
        {wd0, wd1, wd2, wd3} = {4{ {SW{1'b0}} }}; wd4 = 11'd0;
        if (st == S_CLR) begin
            {we0, we1, we2, we3, we4} = 5'b11111;
            wa0 = clr; wa1 = clr; wa2 = clr; wa3 = clr; wa4 = clr[7:0];
        end else if (st == S_UWR && have_ctx) begin
            {we0, we1, we2, we3, we4} = 5'b11111;
            wa0 = ps0; wa1 = ps1; wa2 = ps2; wa3 = ps3; wa4 = hist[7:0];
            wd0 = learn2(rd0, pt0, b_r); wd1 = learn2(rd1, pt1, b_r);
            wd2 = learn2(rd2, pt2, b_r); wd3 = learn2(rd3, pt3, b_r);
            wd4 = rd4[10] ? {1'b1, bump(rd4[9:0], b_r)} : {1'b1, b_r, 2'd0};
        end
    end

    // prediction: per table, which way matches
    function [10:0] pick;                // {hit, value, count}
        input [SW-1:0] s;
        input [11:0]   tag;
        begin
            if (s[22] && s[21:10] == tag)       pick = {1'b1, s[9:0]};
            else if (s[45] && s[44:33] == tag)  pick = {1'b1, s[32:23]};
            else                                pick = 11'd0;
        end
    endfunction
    wire [10:0] k0 = pick(rd0, pt0), k1 = pick(rd1, pt1), k2 = pick(rd2, pt2), k3 = pick(rd3, pt3);

    reg [4:0] bk;
    always @* begin
        if (k3[10])      bk = 5'd12 + k3[1:0];
        else if (k2[10]) bk = 5'd8 + k2[1:0];
        else if (k1[10]) bk = 5'd4 + k1[1:0];
        else if (k0[10]) bk = 5'd0 + k0[1:0];
        else if (rd4[10]) bk = 5'd16 + rd4[1:0];
        else             bk = 5'd20;
    end

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
            S_URD: st <= S_UWR;
            S_UWR: begin
                hist <= {hist[39:0], b_r};
                st <= S_PRD;
            end
            S_PRD: begin
                ps0 <= ns0; ps1 <= ns1; ps2 <= ns2; ps3 <= ns3;
                pt0 <= nt0; pt1 <= nt1; pt2 <= nt2; pt3 <= nt3;
                st <= S_PCAP;
            end
            S_PCAP: begin
                have_ctx <= 1'b1; out_valid <= 1'b1;
                bucket <= bk; conf <= conf_lut[bk];
                if (k3[10])       begin pred <= k3[9:2];  hit <= 1'b1; src <= 3'd3; count <= k3[1:0];  end
                else if (k2[10])  begin pred <= k2[9:2];  hit <= 1'b1; src <= 3'd2; count <= k2[1:0];  end
                else if (k1[10])  begin pred <= k1[9:2];  hit <= 1'b1; src <= 3'd1; count <= k1[1:0];  end
                else if (k0[10])  begin pred <= k0[9:2];  hit <= 1'b1; src <= 3'd0; count <= k0[1:0];  end
                else if (rd4[10]) begin pred <= rd4[9:2]; hit <= 1'b1; src <= 3'd4; count <= rd4[1:0]; end
                else              begin pred <= 8'h20;    hit <= 1'b0; src <= 3'd5; count <= 2'd0;     end
                st <= S_IDLE;
            end
            default: st <= S_IDLE;
        endcase
    end
endmodule

module spark_lk2_ram #(
    parameter W = 47,
    parameter AW = 11
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
