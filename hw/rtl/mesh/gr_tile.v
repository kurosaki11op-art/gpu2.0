// General mesh tile (28 Oct 2026, SIMULATED): a 5-port router (local, N, E, S, W) with dimension-order (X then Y) routing, a 4-flit input FIFO per port,
// round-robin arbitration per output and ready-based back-pressure, plus an endpoint that injects a list of flits from memory and stores arriving payloads by slot.
// Flit (184 bits): {dest x (8), dest y (8), slot (16), timestamp (16), payload (136 = one block-floating-point word)}. One flit per link per cycle.
// Ports index: 0 local, 1 north (row Y-1), 2 east (column X+1), 3 south (row Y+1), 4 west (column X-1).
module gr_tile #(parameter X = 0, Y = 0, NI = 30, NSLOT = 32, EXPECT = 30, parameter FILE_INJ = "inj_0_0.hex") (
    input clk, input rst, input go,
    input in_n_v, input [183:0] in_n_f, output rdy_n, input in_e_v, input [183:0] in_e_f, output rdy_e, input in_s_v, input [183:0] in_s_f, output rdy_s, input in_w_v, input [183:0] in_w_f, output rdy_w,
    output reg out_n_v, output reg [183:0] out_n_f, input ord_n, output reg out_e_v, output reg [183:0] out_e_f, input ord_e, output reg out_s_v, output reg [183:0] out_s_f, input ord_s, output reg out_w_v, output reg [183:0] out_w_f, input ord_w,
    output reg done, output reg [31:0] cnt_hops, output reg [31:0] cnt_wait, output reg [31:0] lat_sum, output reg [31:0] recv_n, input [15:0] rd_slot, output [135:0] rd_data);
    reg [183:0] fq [0:19]; reg [2:0] cnt [0:4]; reg [1:0] rp [0:4]; reg [1:0] wp [0:4]; reg [2:0] rr [0:4];
    reg [183:0] inj [0:NI-1]; reg [135:0] rcv [0:NSLOT-1]; initial $readmemh(FILE_INJ, inj);
    assign rdy_n = (cnt[1] <= 2); assign rdy_e = (cnt[2] <= 2); assign rdy_s = (cnt[3] <= 2); assign rdy_w = (cnt[4] <= 2); assign rd_data = rcv[rd_slot];
    reg [15:0] cyc; reg running; reg [15:0] ii; reg ej_v; reg [183:0] ej_f;
    reg [4:0] push, pop; reg [183:0] pf [0:4]; reg [2:0] route [0:4]; reg [4:0] has; reg [183:0] head [0:4]; reg [3:0] win [0:4]; reg [4:0] gr_o; integer p, o, k, q; reg [3:0] cand; reg rdy_o; reg [2:0] nrp; reg [31:0] hinc, winc;
    always @(posedge clk) begin
        if (rst) begin hinc = 0; winc = 0; for (p = 0; p < 5; p = p + 1) begin cnt[p] <= 0; rp[p] <= 0; wp[p] <= 0; rr[p] <= 0; end out_n_v <= 0; out_e_v <= 0; out_s_v <= 0; out_w_v <= 0; ej_v <= 0; done <= 0; cnt_hops <= 0; cnt_wait <= 0; lat_sum <= 0; recv_n <= 0; running <= 0; ii <= 0; cyc <= 0; end
        else begin
            if (go) begin running <= 1; ii <= 0; cyc <= 0; lat_sum <= 0; recv_n <= 0; done <= 0; end else if (running) cyc <= cyc + 1;
            // heads and routes (from the state at the start of the cycle)
            for (p = 0; p < 5; p = p + 1) begin has[p] = (cnt[p] != 0); head[p] = fq[p * 4 + rp[p]];
                route[p] = (head[p][183:176] > X) ? 2 : (head[p][183:176] < X) ? 4 : (head[p][175:168] > Y) ? 3 : (head[p][175:168] < Y) ? 1 : 0; end
            pop = 0; hinc = 0; winc = 0; out_n_v <= 0; out_e_v <= 0; out_s_v <= 0; out_w_v <= 0; ej_v <= 0;
            for (o = 0; o < 5; o = o + 1) begin
                rdy_o = (o == 0) ? 1'b1 : (o == 1) ? ord_n : (o == 2) ? ord_e : (o == 3) ? ord_s : ord_w; cand = 4'd15;
                for (k = 0; k < 5; k = k + 1) begin q = (rr[o] + k) % 5; if (cand == 4'd15 && has[q] && route[q] == o) cand = q; end
                if (cand != 4'd15 && rdy_o) begin
                    pop[cand] = 1; rr[o] <= (cand + 1) % 5;
                    case (o) 0: begin ej_v <= 1; ej_f <= head[cand]; end 1: begin out_n_v <= 1; out_n_f <= head[cand]; end 2: begin out_e_v <= 1; out_e_f <= head[cand]; end 3: begin out_s_v <= 1; out_s_f <= head[cand]; end 4: begin out_w_v <= 1; out_w_f <= head[cand]; end endcase
                    if (o != 0) hinc = hinc + 1;
                end
            end
            for (p = 0; p < 5; p = p + 1) if (has[p] && !pop[p]) winc = winc + 1;
            cnt_hops <= cnt_hops + hinc; cnt_wait <= cnt_wait + winc;
            // pushes: arrivals from the four neighbours and the local injection
            push = 0; pf[1] = in_n_f; pf[2] = in_e_f; pf[3] = in_s_f; pf[4] = in_w_f; push[1] = in_n_v; push[2] = in_e_v; push[3] = in_s_v; push[4] = in_w_v;
            if (running && ii < NI && cnt[0] <= 3) begin push[0] = 1; pf[0] = inj[ii]; pf[0][151:136] = cyc; ii <= ii + 1; end
            for (p = 0; p < 5; p = p + 1) begin
                if (push[p]) begin fq[p * 4 + wp[p]] <= pf[p]; wp[p] <= wp[p] + 1; end
                if (pop[p]) rp[p] <= rp[p] + 1;
                cnt[p] <= cnt[p] + (push[p] ? 1 : 0) - (pop[p] ? 1 : 0);
            end
            // endpoint receive (the router ejected a flit last cycle)
            if (ej_v) begin rcv[ej_f[167:152]] <= ej_f[135:0]; recv_n <= recv_n + 1; lat_sum <= lat_sum + ((cyc - ej_f[151:136]) & 16'hFFFF); end
            if (running && ii == NI && recv_n == EXPECT) done <= 1;
        end
    end
endmodule
