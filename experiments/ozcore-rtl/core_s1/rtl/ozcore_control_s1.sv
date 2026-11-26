// Minimal single-modulus core control: weight load, compute, output.
module ozcore_control_s1 (
    input  logic clk, rst,
    input  logic start,
    output logic weight_wr_en,
    output logic psum_wr_en,
    output logic out_valid,
    output logic busy,
    output logic done
);
    typedef enum logic [1:0] {IDLE, LOAD, COMPUTE, OUT} state_t;
    state_t state;
    always_ff @(posedge clk) begin
        if (rst) begin state <= IDLE; done <= 1'b0; end
        else begin
            done <= 1'b0;
            case (state)
                IDLE: if (start) state <= LOAD;
                LOAD: state <= COMPUTE;
                COMPUTE: begin psum_wr_en <= 1'b1; state <= OUT; end
                OUT: begin psum_wr_en <= 1'b0; done <= 1'b1; state <= IDLE; end
                default: state <= IDLE;
            endcase
        end
    end
    assign weight_wr_en = (state == LOAD);
    assign out_valid = (state == OUT);
    assign busy = (state != IDLE);
endmodule
