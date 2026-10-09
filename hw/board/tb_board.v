`timescale 1ns/1ps
// tb_board.v -- end-to-end test of spark_board_top through a bit-level UART model.
// Run from hw/build (needs emb.hex, w0..w3.hex, stim.hex there):
//   iverilog -g2012 -o board.vvp ../rtl/spark_ram.v ../rtl/spark_core.v ../board/uart_rx.v \
//     ../board/uart_tx.v ../board/spark_board_top.v ../board/tb_board.v && vvp -n board.vvp
// Checks: ping reply, config ack, marker echo, 7-byte token replies well-formed
// (checksum, path <= 2), and pred/path/tok_cycles equal to a second spark_core
// instance driven directly (tb_spark_core style) with the same config + bytes.
// Optional plusarg +ntok=N (tokens per config, default 24).
module tb_board;
    localparam CLK_HZ = 1_000_000, BAUD = 100_000;   // 10 clocks per bit (sim speed-up)
    localparam CPB = CLK_HZ / BAUD;

    reg clk = 0;
    always #5 clk = ~clk;

    reg  host_tx = 1'b1;       // -> FPGA uart_rx
    wire host_rx;              // <- FPGA uart_tx
    wire [5:0] led_n; wire trig;
    reg  btn = 1'b0;

    spark_board_top #(.CLK_HZ(CLK_HZ), .BAUD(BAUD), .POR_BITS(4)) dut (
        .clk(clk), .btn_s1(btn), .btn_s2(1'b0), .uart_rx(host_tx), .uart_tx(host_rx),
        .led_n(led_n), .trig_out(trig));

    // ---------------------------------------------------- reference core
    reg r_rst = 1, r_start = 0; reg [7:0] r_byte = 0;
    reg r_sparse = 1, r_delta = 0, r_exit = 0, r_recall = 0, r_adapt = 0;
    reg [15:0] r_cap = 0; reg [31:0] r_exit_th = 64; reg [1:0] r_conf = 1;
    wire r_done; wire [7:0] r_pred; wire [1:0] r_path; wire [31:0] r_cyc;
    wire [31:0] x0, x1, x2, x3, x4; wire [15:0] y0, y1, y2, y3, y4, y5, y6, y7;
    spark_core ref_core (
        .clk(clk), .rst(r_rst), .start(r_start), .in_byte(r_byte),
        .sparse_en(r_sparse), .delta_en(r_delta), .exit_en(r_exit), .recall_en(r_recall),
        .cap(r_cap), .exit_th(r_exit_th), .conf_th(r_conf),
        .cfg_a(9'd230), .acc_sh(4'd2), .s_sh(4'd4), .adapt_en(r_adapt), .thr_en(1'b1),
        .ld_we(1'b0), .ld_sel(3'd0), .ld_addr(11'd0), .ld_data(64'd0),
        .done(r_done), .pred(r_pred), .path(r_path), .tok_cycles(r_cyc), .wreads(x0),
        .cyc_engine(x1), .cyc_scan(x2), .cyc_post(x3), .cyc_recall(x4),
        .nz0(y0), .nz1(y1), .nz2(y2), .nz3(y3), .pr0(y4), .pr1(y5), .pr2(y6), .pr3(y7));

    // ---------------------------------------------------- UART host model
    task send_byte(input [7:0] b);
        integer i;
        begin
            host_tx = 1'b0; repeat (CPB) @(posedge clk);
            for (i = 0; i < 8; i = i + 1) begin host_tx = b[i]; repeat (CPB) @(posedge clk); end
            host_tx = 1'b1; repeat (CPB) @(posedge clk);
        end
    endtask

    reg [7:0] rxq [0:255]; integer rx_wr = 0, rx_rd = 0, frame_err = 0;
    always begin : receiver
        integer i; reg [7:0] b;
        @(negedge host_rx);
        repeat (CPB / 2) @(posedge clk);
        if (host_rx !== 1'b0) frame_err = frame_err + 1;
        for (i = 0; i < 8; i = i + 1) begin repeat (CPB) @(posedge clk); b[i] = host_rx; end
        repeat (CPB) @(posedge clk);
        if (host_rx !== 1'b1) frame_err = frame_err + 1;
        rxq[rx_wr[7:0]] = b; rx_wr = rx_wr + 1;
    end

    integer errors = 0;
    task get_byte(output [7:0] b);
        integer to;
        begin
            to = 0;
            while (rx_rd == rx_wr && to < 2000000) begin @(posedge clk); to = to + 1; end
            if (rx_rd == rx_wr) begin
                $display("ERROR: timeout waiting for reply byte"); errors = errors + 1; b = 8'hxx;
            end else begin b = rxq[rx_rd[7:0]]; rx_rd = rx_rd + 1; end
        end
    endtask

    task expect_byte(input [7:0] e, input [8*16-1:0] what);
        reg [7:0] b;
        begin
            get_byte(b);
            if (b !== e) begin
                $display("ERROR: %0s reply %02x, expected %02x", what, b, e); errors = errors + 1;
            end
        end
    endtask

    task set_cfg(input [4:0] flags, input [15:0] cap, input [31:0] th, input [1:0] conf);
        begin
            send_byte(8'hC0); send_byte({2'd0, 1'b1, flags});   // bit5 thr_en = 1 send_byte(cap[7:0]); send_byte(cap[15:8]);
            send_byte(th[7:0]); send_byte(th[15:8]); send_byte(th[23:16]); send_byte(th[31:24]);
            send_byte({6'd0, conf});
            expect_byte(8'hC1, "config");
            if ({dut.adapt_en, dut.recall_en, dut.exit_en, dut.delta_en, dut.sparse_en} !== flags ||
                dut.cap !== cap || dut.exit_th !== th || dut.conf_th !== conf) begin
                $display("ERROR: config registers not applied"); errors = errors + 1;
            end
            {r_adapt, r_recall, r_exit, r_delta, r_sparse} = flags;
            r_cap = cap; r_exit_th = th; r_conf = conf;
        end
    endtask

    integer ntok_total = 0, cyc_sum;
    task run_token(input [7:0] b);
        reg [7:0] r [0:6]; reg [7:0] x; integer i; reg [31:0] cyc;
        begin
            send_byte(8'hD0); send_byte(b);
            for (i = 0; i < 7; i = i + 1) get_byte(r[i]);
            x = r[0] ^ r[1] ^ r[2] ^ r[3] ^ r[4] ^ r[5];
            cyc = {r[5], r[4], r[3], r[2]};
            if (x !== r[6]) begin $display("ERROR: checksum %02x != %02x", r[6], x); errors = errors + 1; end
            if (r[1] > 2) begin $display("ERROR: bad path %0d", r[1]); errors = errors + 1; end
            // same byte through the directly driven reference core
            @(negedge clk); r_byte = b; r_start = 1; @(negedge clk); r_start = 0;
            while (!r_done) @(negedge clk);
            if (r[0] !== r_pred || r[1] !== {6'd0, r_path} || cyc !== r_cyc) begin
                $display("ERROR: token %0d byte %02x: board pred=%0d path=%0d cyc=%0d, direct pred=%0d path=%0d cyc=%0d",
                         ntok_total, b, r[0], r[1], cyc, r_pred, r_path, r_cyc);
                errors = errors + 1;
            end
            cyc_sum = cyc_sum + cyc;
            ntok_total = ntok_total + 1;
        end
    endtask

    reg [7:0] stim [0:65535];
    integer t, pos = 0, ntok = 24, c, tok_led0, leds_seen_busy = 0;
    always @(posedge clk) if (!led_n[1]) leds_seen_busy = 1;

    task run_cfg(input [8*32-1:0] name, input [4:0] flags, input [15:0] cap, input [31:0] th, input [1:0] conf);
        integer p0;
        begin
            set_cfg(flags, cap, th, conf);
            cyc_sum = 0; p0 = ntok_total;
            for (t = 0; t < ntok; t = t + 1) begin run_token(stim[pos]); pos = pos + 1; end
            $display("  %0s: %0d tokens, avg tok_cycles %0d", name, ntok, cyc_sum / ntok);
        end
    endtask

    initial begin
        void'($value$plusargs("ntok=%d", ntok));
        $readmemh("stim.hex", stim);
        repeat (3) @(posedge clk); r_rst = 0;
        repeat (60) @(posedge clk);                 // POR (2^4 clocks) + margin
        send_byte(8'hE0); expect_byte(8'h5A, "ping");
        send_byte(8'h55);                           // junk byte must be ignored
        send_byte(8'hE0); expect_byte(8'h5A, "ping2");
        send_byte(8'hA1); expect_byte(8'hA1, "marker on");
        if (trig !== 1'b1 || led_n[2] !== 1'b0) begin $display("ERROR: marker pin"); errors = errors + 1; end
        tok_led0 = led_n[0];
        //        name                       flags(adapt,recall,exit,delta,sparse) cap  exit_th  conf
        run_cfg("dense",                    5'b00000, 16'd0,  32'd64, 2'd1);
        run_cfg("event-driven",             5'b00001, 16'd0,  32'd64, 2'd1);
        run_cfg("event + change-only + cap",5'b00011, 16'd16, 32'd64, 2'd1);
        run_cfg("adaptive",                 5'b11101, 16'd0,  32'd64, 2'd1);
        run_cfg("adaptive exit_th=-1e6",    5'b11101, 16'd0,  -32'sd1000000, 2'd1);
        send_byte(8'hA0); expect_byte(8'hA0, "marker off");
        if (trig !== 1'b0) begin $display("ERROR: marker pin off"); errors = errors + 1; end
        if (led_n[0] !== (tok_led0 ^ (ntok_total & 1))) begin $display("ERROR: token LED"); errors = errors + 1; end
        if (!leds_seen_busy) begin $display("ERROR: busy LED never on"); errors = errors + 1; end
        if (frame_err) begin $display("ERROR: %0d UART framing errors", frame_err); errors = errors + 1; end
        if (rx_rd != rx_wr) begin $display("ERROR: %0d unexpected reply bytes", rx_wr - rx_rd); errors = errors + 1; end
        if (errors == 0) $display("PASS: %0d tokens over UART, all replies well-formed and equal to direct core runs", ntok_total);
        else $display("FAIL: %0d errors", errors);
        $finish;
    end
endmodule
