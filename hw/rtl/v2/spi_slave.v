// spi_slave.v -- SPI mode 0 slave (CPOL=0, CPHA=0), MSB first, 8-bit frames, oversampled in `clk`.
// Plain Verilog-2005, synthesizable. Synchronous active-high `rst`, every register reset.
//
// Two modules:
//   spi_slave_core  -- synchronisers + shift registers. TX interface: tx_data/tx_load/tx_ready
//                      (one-byte holding register).
//   spi_slave       -- spi_slave_core with a 16-byte TX FIFO in front (tx_push/tx_full/tx_empty).
//                      This is the module the chip top instantiates.
//
// Timing requirements (clk domain):
//   * f_clk >= 8 * f_sck. sck, cs_n and mosi each pass through a 2-FF synchroniser (same depth, so
//     their relative timing is preserved); edges are detected one cycle later. MISO changes at most
//     3 clk cycles after the SCK falling edge, i.e. before the host samples it half an SCK period later.
//   * Host must leave >= 4 clk between CS_N falling and the first SCK rising edge (first MISO bit is
//     presented when CS_N assertion is seen by the synchroniser).
//   * cs_n high resets the bit counters (a partial byte is discarded); miso is driven 0 while cs_n high.
//
// RX: rx_data/rx_valid -- rx_valid pulses one clk after the 8th rising SCK edge of a byte is seen.
// TX: the byte in the holding register when a byte slot starts (CS_N fall or the 8th falling SCK
//     edge of the previous byte) is shifted out during that slot; if the holding register is empty,
//     0x00 is shifted out. The holding register is only consumed when the host actually clocks the
//     first bit of its slot (first rising SCK edge), so a byte queued just before CS_N rises is not lost.

module spi_slave_core (
    input            clk,
    input            rst,
    // pins
    input            sck,
    input            cs_n,
    input            mosi,
    output           miso,
    // core side
    output reg [7:0] rx_data,
    output reg       rx_valid,
    input      [7:0] tx_data,
    input            tx_load,      // pulse: write tx_data into the holding register (only when tx_ready)
    output           tx_ready      // holding register empty
);
    // ---------------------------------------------------------------- synchronisers
    reg [2:0] sck_s, cs_s, mosi_s;          // [0],[1] = 2-FF synchroniser, [2] = previous (edge detect)
    always @(posedge clk) begin
        if (rst) begin
            sck_s <= 3'b000; cs_s <= 3'b111; mosi_s <= 3'b000;
        end else begin
            sck_s  <= {sck_s[1:0],  sck};
            cs_s   <= {cs_s[1:0],   cs_n};
            mosi_s <= {mosi_s[1:0], mosi};
        end
    end
    wire sel    = ~cs_s[1];
    wire sck_r  =  sck_s[1] & ~sck_s[2];
    wire sck_f  = ~sck_s[1] &  sck_s[2];
    wire cs_f   = ~cs_s[1]  &  cs_s[2];     // CS_N falling: slot start
    wire mosi_v =  mosi_s[1];

    // ---------------------------------------------------------------- holding register
    reg [7:0] hold; reg hold_v;
    assign tx_ready = ~hold_v;

    // ---------------------------------------------------------------- shift logic
    reg [2:0] rcnt;            // rising edges seen in the current byte
    reg [2:0] fcnt;            // falling edges seen in the current byte
    reg [7:0] rsh;             // RX shift register
    reg [7:0] tsh;             // TX shift register (MSB on miso)
    reg       t_from_hold;     // tsh was loaded from the holding register (consume on first rising edge)

    wire consume = sel & sck_r & (rcnt == 3'd0) & t_from_hold;

    always @(posedge clk) begin
        rx_valid <= 1'b0;
        if (rst) begin
            rx_data <= 8'd0; hold <= 8'd0; hold_v <= 1'b0;
            rcnt <= 3'd0; fcnt <= 3'd0; rsh <= 8'd0; tsh <= 8'd0; t_from_hold <= 1'b0;
        end else begin
            // holding register: load / consume
            if (consume) hold_v <= 1'b0;
            if (tx_load && !hold_v) begin hold <= tx_data; hold_v <= 1'b1; end

            if (!sel) begin
                rcnt <= 3'd0; fcnt <= 3'd0; t_from_hold <= 1'b0; tsh <= 8'd0;
            end else if (cs_f) begin
                // first slot: present the first bit
                tsh <= hold_v ? hold : 8'd0; t_from_hold <= hold_v;
                rcnt <= 3'd0; fcnt <= 3'd0;
            end else begin
                if (sck_r) begin
                    rsh  <= {rsh[6:0], mosi_v};
                    rcnt <= rcnt + 3'd1;
                    if (consume) t_from_hold <= 1'b0;
                    if (rcnt == 3'd7) begin rx_data <= {rsh[6:0], mosi_v}; rx_valid <= 1'b1; end
                end
                if (sck_f) begin
                    fcnt <= fcnt + 3'd1;
                    if (fcnt == 3'd7) begin          // end of byte: start the next slot
                        tsh <= hold_v ? hold : 8'd0; t_from_hold <= hold_v;
                    end else
                        tsh <= {tsh[6:0], 1'b0};
                end
            end
        end
    end

    assign miso = sel & tsh[7];
endmodule

module spi_slave #(
    parameter FIFO_AW = 4                   // 2**FIFO_AW byte TX FIFO (16)
) (
    input            clk,
    input            rst,
    input            sck,
    input            cs_n,
    input            mosi,
    output           miso,
    output     [7:0] rx_data,
    output           rx_valid,
    input      [7:0] tx_data,
    input            tx_push,      // pulse: queue tx_data (ignored when tx_full)
    output           tx_full,
    output           tx_empty,     // FIFO empty (the holding register may still hold one byte)
    output [FIFO_AW:0] tx_level
);
    localparam DEPTH = 1 << FIFO_AW;
    reg [7:0] mem [0:DEPTH-1];
    reg [FIFO_AW:0] wp, rp;
    wire [FIFO_AW:0] lvl = wp - rp;
    assign tx_level = lvl;
    assign tx_full  = (lvl == DEPTH);
    assign tx_empty = (lvl == 0);

    wire core_ready;
    wire pop = core_ready & ~tx_empty;

    integer i;
    always @(posedge clk) begin
        if (rst) begin
            wp <= 0; rp <= 0;
            for (i = 0; i < DEPTH; i = i + 1) mem[i] <= 8'd0;
        end else begin
            if (tx_push && !tx_full) begin mem[wp[FIFO_AW-1:0]] <= tx_data; wp <= wp + 1'b1; end
            if (pop) rp <= rp + 1'b1;
        end
    end

    spi_slave_core u_core (
        .clk(clk), .rst(rst), .sck(sck), .cs_n(cs_n), .mosi(mosi), .miso(miso),
        .rx_data(rx_data), .rx_valid(rx_valid),
        .tx_data(mem[rp[FIFO_AW-1:0]]), .tx_load(pop), .tx_ready(core_ready));
endmodule
