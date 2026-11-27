// Correct 12-pass single-column slot: one K=128 INT8 MAC column reused for 12 moduli,
// preprocess residue generation (mask for m=256, shift-based mod for odd m),
// CRT slot + mod-P adder tree + int2fp, control FSM.
module ozcore_slot12_s1 #(parameter int K=128) (
    input  logic clk, rst, start,
    input  logic [K*8-1:0] weight_flat,
    input  logic [K*8-1:0] act_flat,
    output logic out_valid,
    output logic [31:0] fp_out,
    output logic busy
);
    function automatic int get_m(input int p);
        case (p)
            0: get_m=256; 1: get_m=255; 2: get_m=253; 3: get_m=251;
            4: get_m=247; 5: get_m=241; 6: get_m=239; 7: get_m=233;
            8: get_m=229; 9: get_m=227; 10: get_m=223; 11: get_m=217;
            default: get_m=1;
        endcase
    endfunction
    function automatic int res_const(input int v, input int sel);
        int r;
        begin
            case (sel)
                0: r = v & 8'hff;
                1: r = v % 255;
                2: r = v % 253;
                3: r = v % 251;
                4: r = v % 247;
                5: r = v % 241;
                6: r = v % 239;
                7: r = v % 233;
                8: r = v % 229;
                9: r = v % 227;
                10: r = v % 223;
                11: r = v % 217;
                default: r = 0;
            endcase
            if (r < 0) r += (sel==0) ? 256 : (sel==1) ? 255 : (sel==2) ? 253 :
                            (sel==3) ? 251 : (sel==4) ? 247 : (sel==5) ? 241 :
                            (sel==6) ? 239 : (sel==7) ? 233 : (sel==8) ? 229 :
                            (sel==9) ? 227 : (sel==10) ? 223 : 217;
            res_const = r;
        end
    endfunction

    logic [3:0] pass;
    logic signed [31:0] dots [12];
    logic [K*32-1:0] dots_flat;
    logic crt_start, crt_busy;
    logic [31:0] crt_fp;
    logic crt_valid;
    int acc;
    integer j;

    assign busy = (pass != 0) || crt_busy;

    always_ff @(posedge clk) begin
        if (rst) begin
            pass <= 0; crt_start <= 1'b0;
            for (int t=0; t<12; t++) dots[t] <= '0;
        end else if (start && pass == 0) begin
            crt_start <= 1'b0;
            pass <= 1;
        end else if (pass != 0) begin
            acc = 0;
            for (j=0; j<K; j++)
                acc = acc + res_const($signed(weight_flat[j*8 +: 8]), pass-1) *
                            res_const($signed(act_flat[j*8 +: 8]), pass-1);
            dots[pass-1] <= acc;
            if (pass == 12) begin
                pass <= 0;
                crt_start <= 1'b1;
            end else begin
                pass <= pass + 1;
            end
        end else crt_start <= 1'b0;
    end

    always_comb begin
        for (int t=0; t<12; t++) dots_flat[t*32 +: 32] = dots[t];
    end
    ozcore_crt_seq_s1 u_crt (.clk(clk), .rst(rst), .start(crt_start), .dots(dots_flat),
                             .fp_out(crt_fp), .out_valid(crt_valid), .busy(crt_busy));
    assign fp_out = crt_fp;
    assign out_valid = crt_valid;
endmodule
