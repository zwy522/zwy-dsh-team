// Single-modulus INT8 postprocess: bypass int32 accumulators (no CRT).
module ozcore_postprocess_s1 #(parameter int K=128) (
    input  logic clk, rst,
    input  logic in_valid,
    input  logic [K*32-1:0] in_acc,
    input  logic out_ready,
    output logic out_valid,
    output logic [K*32-1:0] out_data,
    output logic in_ready
);
    assign in_ready = ~out_valid | out_ready;
    always_ff @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
            out_data <= '0;
        end else if (in_valid && in_ready) begin
            out_data <= in_acc;
            out_valid <= 1'b1;
        end else if (out_valid && out_ready) begin
            out_valid <= 1'b0;
        end
    end
endmodule
