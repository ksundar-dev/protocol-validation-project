module uart_tx #(parameter int CLKS_PER_BIT = 16) (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data,
    input  logic       valid,   // pulse high for 1 clock while ready is high
    output logic       ready,   // high when idle and able to accept a byte
    output logic       tx
);

    typedef enum logic [1:0] {IDLE, START, DATA, STOP} state_t;
    state_t      state;
    logic [15:0] clk_cnt;
    logic [2:0]  bit_idx;
    logic [7:0]  shreg;

    assign ready = (state == IDLE);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state   <= IDLE;
            tx      <= 1'b1;
            clk_cnt <= '0;
            bit_idx <= '0;
            shreg   <= '0;
        end 
        else begin
            case (state)
                IDLE: begin
                    if (valid) begin
                        shreg   <= data;
                        clk_cnt <= '0;
                        tx      <= 1'b0;
                        state   <= START;
                    end
                end
                START: begin
                    if (clk_cnt == CLKS_PER_BIT - 1) begin
                        clk_cnt <= '0;
                        bit_idx <= '0;
                        tx      <= shreg[0];
                        shreg   <= {1'b0, shreg[7:1]};
                        state   <= DATA;
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end
                DATA: begin
                    if (clk_cnt == CLKS_PER_BIT - 1) begin
                        clk_cnt <= '0;
                        if (bit_idx == 3'd7) begin
                            tx    <= 1'b1;
                            state <= STOP;
                        end else begin
                            tx      <= shreg[0];
                            shreg   <= {1'b0, shreg[7:1]};
                            bit_idx <= bit_idx + 1'b1;
                        end
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end
                STOP: begin
                    if (clk_cnt == CLKS_PER_BIT - 1) begin
                        clk_cnt <= '0;
                        state   <= IDLE;
                    end else begin
                        clk_cnt <= clk_cnt + 1'b1;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
