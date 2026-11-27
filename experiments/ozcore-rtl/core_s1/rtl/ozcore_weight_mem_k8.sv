// Single-modulus weight memory: N columns x K bytes.
module ozcore_weight_mem_k8 #(parameter int N=128, K=8) (
    input  logic clk,
    input  logic wr_en,
    input  logic [$clog2(N)-1:0] wr_col,
    input  logic [K*8-1:0] wr_data,
    input  logic [$clog2(N)-1:0] rd_col,
    output logic [K*8-1:0] rd_data
);
    logic [7:0] mem [N][K];
    always_ff @(posedge clk) begin
        if (wr_en) for (int j=0; j<K; j++) mem[wr_col][j] <= wr_data[j*8 +: 8];
    end
    always_comb begin
        for (int j=0; j<K; j++) rd_data[j*8 +: 8] = mem[rd_col][j];
    end
endmodule
