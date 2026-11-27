// Reduced OzCore INT8 top: preprocess INT8 pass-through (low byte),
// N columns x 12 planes x K=128 dot products, postprocess bypass, output aligner.
// This is a functional, single-cycle-compute INT8 path; no CRT/float path.
module ozcore_top_int8 #(
    parameter int K = 128,
    parameter int N = 2,
    parameter int S_MAX = 12
) (
    input  logic clk,
    input  logic rst,
    input  logic weight_valid,
    input  logic [$clog2(N)-1:0] weight_col,
    input  logic [S_MAX*K*16-1:0] weight_flat, // low byte of each 16-bit int slot
    input  logic act_valid,
    input  logic [S_MAX*K*16-1:0] act_flat,
    input  logic out_ready,
    output logic out_valid,
    output logic [S_MAX*N*32-1:0] out_flat, // [slot c][column n][31:0]
    output logic weight_ready,
    output logic act_ready
);
    logic signed [7:0] w_mem [N][S_MAX][K];
    logic signed [7:0] act [S_MAX][K];
    logic signed [31:0] acc [N][S_MAX];

    integer n, c, j;
    assign weight_ready = 1'b1;
    assign act_ready = ~out_valid | out_ready;

    always_ff @(posedge clk) begin
        if (rst) begin
            out_valid <= 1'b0;
            out_flat <= '0;
        end else begin
            if (weight_valid) begin
                for (c = 0; c < S_MAX; c++)
                    for (j = 0; j < K; j++)
                        w_mem[weight_col][c][j] <= weight_flat[(c*K+j)*16 +: 8];
            end

            if (act_valid && act_ready) begin
                for (c = 0; c < S_MAX; c++)
                    for (j = 0; j < K; j++)
                        act[c][j] <= act_flat[(c*K+j)*16 +: 8];

                for (n = 0; n < N; n++) begin
                    for (c = 0; c < S_MAX; c++) begin
                        acc[n][c] = 32'sd0;
                        for (j = 0; j < K; j++)
                            acc[n][c] = acc[n][c] + $signed(w_mem[n][c][j]) * $signed(act_flat[(c*K+j)*16 +: 8]);
                    end
                end
                for (n = 0; n < N; n++)
                    for (c = 0; c < S_MAX; c++)
                        out_flat[(c*N+n)*32 +: 32] <= acc[n][c];
                out_valid <= 1'b1;
            end else if (out_valid && out_ready) begin
                out_valid <= 1'b0;
            end
        end
    end
endmodule
