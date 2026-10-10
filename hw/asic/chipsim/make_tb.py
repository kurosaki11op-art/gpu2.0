"""Generate tb_chip.v: drives spark_chip only through its pins (bit-level UART), checks the UART weight-load
path by reading SRAM contents back, preloads the remaining weights directly into the SRAM models, runs tokens
over UART and writes chip_out.txt (pred path per token) for comparison with the golden model.
usage: make_tb.py rtl|gl"""
import sys
mode = sys.argv[1]
# memory: (ld_sel, hex file, depth)
MEMS = [('u_emb', 0, 'emb.hex', 2048), ('u_emb1', 5, 'emb1.hex', 2048), ('u_emb2', 6, 'emb2.hex', 2048),
        ('u_w0', 1, 'w0.hex', 3072), ('u_w1', 2, 'w1.hex', 2048), ('u_w2', 3, 'w2.hex', 4096), ('u_w3', 4, 'w3.hex', 4096)]
def sram(inst, b):
    if mode == 'rtl':
        return f'dut.u_core.{inst}.u.bank[{b}].col[0].u_sram'
    return f'dut.u.\\u_core.{inst}.u.bank[{b}].col[0].u_sram '
L = []
L.append('`timescale 1ns/1ps\nmodule tb_chip;')
L.append('  localparam CPB = 4;  // clocks per UART bit (CLK_HZ 1 MHz, BAUD 250 kbaud in this sim)')
L.append('  reg clk = 0, rst_n = 0, host_tx = 1; wire host_rx, ready, busy, tok, trig;')
L.append('  always #5 clk = ~clk;')
L.append('  spark_chip #(.CLK_HZ(1000000), .BAUD(250000)) dut (.clk(clk), .rst_n(rst_n), .uart_rx(host_tx), .uart_tx(host_rx), .ready(ready), .busy(busy), .tok(tok), .trig_out(trig));' if mode == 'rtl'
         else '  spark_chip dut (.clk(clk), .rst_n(rst_n), .uart_rx(host_tx), .uart_tx(host_rx), .ready(ready), .busy(busy), .tok(tok), .trig_out(trig));')
L.append('''  task send_byte(input [7:0] b); integer i; begin
    host_tx = 0; repeat (CPB) @(posedge clk);
    for (i = 0; i < 8; i = i + 1) begin host_tx = b[i]; repeat (CPB) @(posedge clk); end
    host_tx = 1; repeat (CPB) @(posedge clk); end endtask
  reg [7:0] rxq [0:1023]; integer rx_wr = 0, rx_rd = 0, errors = 0;
  always begin : receiver integer i; reg [7:0] b;
    @(negedge host_rx); repeat (CPB/2) @(posedge clk);
    for (i = 0; i < 8; i = i + 1) begin repeat (CPB) @(posedge clk); b[i] = host_rx; end
    repeat (CPB) @(posedge clk); rxq[rx_wr % 1024] = b; rx_wr = rx_wr + 1; end
  task get_byte(output [7:0] b); integer to; begin to = 0;
    while (rx_rd == rx_wr && to < 3000000) begin @(posedge clk); to = to + 1; end
    if (rx_rd == rx_wr) begin $display("ERROR: reply timeout"); errors = errors + 1; b = 8'hxx; end
    else begin b = rxq[rx_rd % 1024]; rx_rd = rx_rd + 1; end end endtask
  task expect_byte(input [7:0] e); reg [7:0] b; begin get_byte(b); if (b !== e) begin $display("ERROR: reply %h expected %h", b, e); errors = errors + 1; end end endtask
  task ld_word(input [2:0] sel, input [11:0] a, input [31:0] d); begin
    send_byte(8'hB0); send_byte({5'd0, sel}); send_byte(a[7:0]); send_byte({4'd0, a[11:8]});
    send_byte(d[7:0]); send_byte(d[15:8]); send_byte(d[23:16]); send_byte(d[31:24]); expect_byte(8'hB1); end endtask
  reg [31:0] wbuf [0:4095]; reg [7:0] stim [0:65535]; integer i, t, n, f, k, flags, exit_th, conf, uart_words, uart_bad;
  reg [7:0] r [0:6];
  initial begin
    n = 20; void'($value$plusargs("n=%d", n));
    flags = 6'b111101; void'($value$plusargs("flags=%d", flags));
    exit_th = 2; void'($value$plusargs("exit_th=%d", exit_th));
    conf = 8'h80; void'($value$plusargs("conf=%d", conf));      // conf_th 0, recall_mode 0, arb_th 128 (>>4 = 8)
    $readmemh("stim.hex", stim);
    repeat (5) @(posedge clk); rst_n = 1;
    send_byte(8'hE0); expect_byte(8'h5A);
    while (!ready) @(posedge clk);
    $display("chip ready (memory clear done), ping ok");''')
# preload + UART sample per memory
for inst, sel, hexf, depth in MEMS:
    nb = (depth + 511) // 512
    L.append(f'    $readmemh("{hexf}", wbuf);')
    for b in range(nb):
        L.append(f'    for (i = 0; i < 512; i = i + 1) {sram(inst, b)}.mem[i] = wbuf[{b * 512} + i];')
    # UART sample: 64 words spread over every bank, first written as complement then rewritten correctly via UART
    L.append(f'    uart_words = 0; uart_bad = 0;')
    L.append(f'    for (k = 0; k < 64; k = k + 1) begin i = (k * {depth // 64}) + (k % 7); ' + ' '.join(
        [f'if (i / 512 == {b}) {sram(inst, b)}.mem[i % 512] = ~wbuf[i];' for b in range(nb)]) + f' ld_word(3\'d{sel}, i, wbuf[i]); uart_words = uart_words + 1; end')
    L.append(f'    for (k = 0; k < 64; k = k + 1) begin i = (k * {depth // 64}) + (k % 7); ' + ' '.join(
        [f'if (i / 512 == {b} && {sram(inst, b)}.mem[i % 512] !== wbuf[i]) uart_bad = uart_bad + 1;' for b in range(nb)]) + ' end')
    L.append(f'    $display("{inst}: %0d words written over UART, %0d wrong in SRAM", uart_words, uart_bad); errors = errors + uart_bad;')
L.append('''    send_byte(8'hC0); send_byte(flags[7:0]); send_byte(8'd0); send_byte(8'd0);
    send_byte(exit_th[7:0]); send_byte(exit_th[15:8]); send_byte(exit_th[23:16]); send_byte(exit_th[31:24]); send_byte(conf[7:0]);
    expect_byte(8'hC1);
    f = $fopen("chip_out.txt", "w");
    for (t = 0; t < n; t = t + 1) begin
      send_byte(8'hD0); send_byte(stim[t]);
      for (i = 0; i < 7; i = i + 1) get_byte(r[i]);
      if ((r[0]^r[1]^r[2]^r[3]^r[4]^r[5]) !== r[6]) begin $display("ERROR: checksum"); errors = errors + 1; end
      $fwrite(f, "%0d %0d %0d\\n", r[0], r[1], {r[5], r[4], r[3], r[2]});
    end
    $fclose(f);
    if (errors == 0) $display("PASS: chip pins only; %0d tokens over UART", n); else $display("FAIL: %0d errors", errors);
    $finish;
  end
endmodule''')
open(f'tb_chip_{mode}.v', 'w').write('\n'.join(L) + '\n')
print('written', f'tb_chip_{mode}.v')
