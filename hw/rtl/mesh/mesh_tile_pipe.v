// L Forge mesh tile with double-buffered operands (29 Oct 2026, SIMULATED): the streaming version of mesh_tile.v. A stream of NP independent matrix products C_t = A_t B_t runs back to back; while the lane computes product t from operand bank t mod 2,
// the routers deliver the operands of product t+1 into the other bank, so communication overlaps compute (the accumulation order inside a product is unchanged, so results stay bit-exact with the lane golden model). go_comm starts the communication of product comm_prod into bank comm_bank,
// stop_comm ends it (the global controller sends it once every tile has all its words, because tiles keep forwarding for the others until then), go_comp starts the compute of product comp_prod from bank comp_bank. Results are kept per product. Link traversal counters accumulate over the stream.
// L Forge mesh tile (28 Oct 2026, SIMULATED): a tile with local memory, one forge_lane and a small router for a P x P mesh.
// Matrix product C = A B distributed SUMMA-style: tile (I,J) owns A(I,J) (MT rows, K-slice J of NBT blocks) and B(I,J) (K-slice I, NT columns, stored transposed).
// Phase 1 (communication): every tile sends its A words east and west along its row and its B words south and north along its column. The routers
// DELIVER each arriving flit to the local memory AND FORWARD it onward in the same direction (priority to forwarding over injection), so every word crosses
// one link per delivered copy. One flit (a 136-bit block word plus a 25-bit header) per link per cycle. Phase 2: each tile multiplies its assembled A row and B column
// with the lane, exactly as forge_tile_mm does. The router has no general addressing or arbitration between flows: it serves the row and column broadcasts of this pattern only.
module mesh_tile_pipe #(parameter I = 0, J = 0, P = 4, MT = 4, NT = 4, NBT = 2, NP = 2, parameter FA = "mesh_a_0_0.hex", parameter FB = "mesh_b_0_0.hex") (
    input clk, input rst, input go_comm, input [7:0] comm_prod, input comm_bank, input stop_comm, input go_comp, input [7:0] comp_prod, input comp_bank,
    input [160:0] in_w, input [160:0] in_e, input [160:0] in_n, input [160:0] in_s,
    output reg [160:0] out_e, output reg [160:0] out_w, output reg [160:0] out_n, output reg [160:0] out_s,
    output reg comm_done, output reg comp_done, output reg [31:0] tx_a, output reg [31:0] tx_b,
    input [15:0] c_raddr, output reg signed [16:0] c_macc, output reg signed [11:0] c_eacc);
    localparam NA = MT * NBT, NBW = NT * NBT, KB = P * NBT;
    reg [135:0] a_own [0:NP*NA-1]; reg [135:0] b_own [0:NP*NBW-1]; reg [135:0] a_row [0:2*MT*KB-1]; reg [135:0] b_col [0:2*NT*KB-1];   // two operand banks: one is filled by the routers while the other is read by the lane
    reg signed [16:0] cm [0:NP*MT*NT-1]; reg signed [11:0] ce [0:NP*MT*NT-1];
    initial begin $readmemh(FA, a_own); $readmemh(FB, b_own); end
    reg [15:0] ia_e, ia_w, ib_s, ib_n, ra, rb; reg comm_run; integer q; reg [7:0] cp; reg cbk;
    wire has_e = (J != P - 1), has_w = (J != 0), has_s = (I != P - 1), has_n = (I != 0);
    wire [7:0] my_j = J, my_i = I;
    // ---- communication ----
    always @(posedge clk) begin
        if (rst) begin comm_done <= 0; comm_run <= 0; out_e <= 0; out_w <= 0; out_n <= 0; out_s <= 0; tx_a <= 0; tx_b <= 0; end
        else begin
            if (go_comm) begin
                for (q = 0; q < NA; q = q + 1) a_row[comm_bank * MT * KB + (q / NBT) * KB + J * NBT + (q % NBT)] <= a_own[comm_prod * NA + q];
                for (q = 0; q < NBW; q = q + 1) b_col[comm_bank * NT * KB + (q / NBT) * KB + I * NBT + (q % NBT)] <= b_own[comm_prod * NBW + q];
                ia_e <= 0; ia_w <= 0; ib_s <= 0; ib_n <= 0; ra <= 0; rb <= 0; comm_run <= 1; comm_done <= 0; cp <= comm_prod; cbk <= comm_bank;
            end else if (stop_comm) begin comm_run <= 0; out_e <= 0; out_w <= 0; out_n <= 0; out_s <= 0;
            end else if (comm_run) begin
                // A east (forward what came from the west, else inject own)
                if (has_e && in_w[160]) out_e <= in_w; else if (has_e && ia_e < NA) begin out_e <= {1'b1, my_j, ia_e, a_own[cp * NA + ia_e]}; ia_e <= ia_e + 1; end else out_e <= 0;
                if (has_w && in_e[160]) out_w <= in_e; else if (has_w && ia_w < NA) begin out_w <= {1'b1, my_j, ia_w, a_own[cp * NA + ia_w]}; ia_w <= ia_w + 1; end else out_w <= 0;
                if (has_s && in_n[160]) out_s <= in_n; else if (has_s && ib_s < NBW) begin out_s <= {1'b1, my_i, ib_s, b_own[cp * NBW + ib_s]}; ib_s <= ib_s + 1; end else out_s <= 0;
                if (has_n && in_s[160]) out_n <= in_s; else if (has_n && ib_n < NBW) begin out_n <= {1'b1, my_i, ib_n, b_own[cp * NBW + ib_n]}; ib_n <= ib_n + 1; end else out_n <= 0;
                // flits placed on links this cycle count as link traversals next cycle
                tx_a <= tx_a + ((has_e && (in_w[160] || ia_e < NA)) ? 1 : 0) + ((has_w && (in_e[160] || ia_w < NA)) ? 1 : 0);
                tx_b <= tx_b + ((has_s && (in_n[160] || ib_s < NBW)) ? 1 : 0) + ((has_n && (in_s[160] || ib_n < NBW)) ? 1 : 0);
                // deliver arrivals
                if (in_w[160]) begin a_row[cbk * MT * KB + (in_w[151:136] / NBT) * KB + in_w[159:152] * NBT + (in_w[151:136] % NBT)] <= in_w[135:0]; end
                if (in_e[160]) begin a_row[cbk * MT * KB + (in_e[151:136] / NBT) * KB + in_e[159:152] * NBT + (in_e[151:136] % NBT)] <= in_e[135:0]; end
                if (in_n[160]) begin b_col[cbk * NT * KB + (in_n[151:136] / NBT) * KB + in_n[159:152] * NBT + (in_n[151:136] % NBT)] <= in_n[135:0]; end
                if (in_s[160]) begin b_col[cbk * NT * KB + (in_s[151:136] / NBT) * KB + in_s[159:152] * NBT + (in_s[151:136] % NBT)] <= in_s[135:0]; end
                ra <= ra + in_w[160] + in_e[160]; rb <= rb + in_n[160] + in_s[160];
                if (ra == (P - 1) * NA && rb == (P - 1) * NBW) comm_done <= 1;      // keep forwarding for the other tiles until the global barrier (go_comp)
            end
        end
    end
    // ---- compute (as forge_tile_mm) ----
    reg comp_started; always @(posedge clk) begin if (rst) comp_started <= 0; else if (go_comp) comp_started <= 1; else if (comp_done) comp_started <= 0; end
    reg [15:0] m, n, b; reg run; reg [7:0] kp; reg kbk; reg [135:0] wa, wb; reg v1, f1, l1; reg [15:0] m1, n1; reg v2; reg [15:0] m2, n2; wire signed [16:0] macc; wire signed [11:0] eacc; wire ov;
    forge_lane lane (.clk(clk), .rst(rst), .valid(v1), .first(f1), .ma(wa[127:0]), .mb(wb[127:0]), .ea(wa[135:128]), .eb(wb[135:128]), .macc(macc), .eacc(eacc), .out_valid(ov));
    always @(posedge clk) begin
        if (rst) begin comp_done <= 0; run <= 0; v1 <= 0; v2 <= 0; end
        else begin
            c_macc <= cm[c_raddr]; c_eacc <= ce[c_raddr];
            if (go_comp) begin run <= 1; m <= 0; n <= 0; b <= 0; comp_done <= 0; kp <= comp_prod; kbk <= comp_bank; end
            wa <= a_row[kbk * MT * KB + m * KB + b]; wb <= b_col[kbk * NT * KB + n * KB + b]; v1 <= run; f1 <= (b == 0); l1 <= (b == KB - 1); m1 <= m; n1 <= n;
            if (run && !go_comp) begin if (b == KB - 1) begin b <= 0; if (n == NT - 1) begin n <= 0; if (m == MT - 1) run <= 0; else m <= m + 1; end else n <= n + 1; end else b <= b + 1; end
            v2 <= v1 && l1; m2 <= m1; n2 <= n1; if (v2) begin cm[kp * MT * NT + m2 * NT + n2] <= macc; ce[kp * MT * NT + m2 * NT + n2] <= eacc; end
            if (!run && !v1 && !v2 && !comp_done && comp_started) comp_done <= 1;
        end
    end
endmodule
