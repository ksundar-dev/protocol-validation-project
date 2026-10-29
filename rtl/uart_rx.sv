module uart_rx #(parameter int CLKS_PER_BIT = 16) (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       rx,
    output logic [7:0] data,
    output logic       valid,      // 1-clock pulse when a byte is received
    output logic       frame_err   // 1-clock pulse when the stop bit was low
);
    typedef enum logic [2:0] {IDLE, START, DATA, STOP, RECOVER} state_t;
    state_t      state;
    logic [15:0] clk_cnt;
    logic [2:0]  bit_idx;
    logic [7:0]  shreg;
    logic        rx_meta, rx_sync;   // 2-flop synchronizer for the async input

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            rx_meta   <= 1'b1;
            rx_sync   <= 1'b1;
            state     <= IDLE;
            clk_cnt   <= '0;
            bit_idx   <= '0;
            shreg     <= '0;
            data      <= '0;
            valid     <= 1'b0;
            frame_err <= 1'b0;
        end 
        else begin
            rx_meta   <= rx;
            rx_sync   <= rx_meta;
            valid     <= 1'b0;
            frame_err <= 1'b0;
            case (state)
                IDLE: begin
                    if (!rx_sync) begin
                        clk_cnt <= '0;
                        state   <= START;
                    end
                end
                START: begin
                    // wait half a bit then confirm the start bit is still on low
                    if (clk_cnt == CLKS_PER_BIT / 2 - 1) begin
                        clk_cnt <= '0;
                        if (!rx_sync) begin
                            bit_idx <= '0;
                            state   <= DATA;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end
                DATA: begin
                    if (clk_cnt == CLKS_PER_BIT - 1) begin
                        clk_cnt <= '0;
                        shreg   <= {rx_sync, shreg[7:1]};   // LSB arrives first
                        if (bit_idx == 3'd7) state <= STOP;
                        else bit_idx <= bit_idx + 1'b1;
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end
                STOP: begin
                    if (clk_cnt == CLKS_PER_BIT - 1) begin
                        clk_cnt <= '0;
                        if (rx_sync) begin
                            data  <= shreg;
                            valid <= 1'b1;
                            state <= IDLE;
                        end else begin
                            frame_err <= 1'b1;
                            state     <= RECOVER;
                        end
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end
                RECOVER: begin
                    // after a framing error wait for the line to go idle again
                    if (rx_sync) state <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
