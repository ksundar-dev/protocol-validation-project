module uart_tb_top (
    input  logic       clk,
    input  logic       rst_n,

    // TX side
    input  logic [7:0] tx_data,
    input  logic       tx_valid,
    output logic       tx_ready,
    output logic       tx_line,

    // RX side
    input  logic       rx_line,
    
    output logic [7:0] rx_data,
    output logic       rx_valid,
    output logic       rx_frame_err
);
    uart_tx #(.CLKS_PER_BIT(16)) u_tx (.clk(clk), .rst_n(rst_n),.data(tx_data), .valid(tx_valid), .ready(tx_ready), .tx(tx_line));

    uart_rx #(.CLKS_PER_BIT(16)) u_rx (.clk(clk), .rst_n(rst_n),.rx(rx_line), .data(rx_data), .valid(rx_valid), .frame_err(rx_frame_err));

`ifdef ICARUS_DUMP
    initial begin
        $dumpfile("waves_uart.vcd");
        $dumpvars(0, uart_tb_top);
    end
`endif
endmodule
