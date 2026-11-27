// Sequentially shared 12-modulus CRT: one red16/mod32 unit, one 96x8 multiply,
// one mod-P accumulator; 12 cycles per slot. No behavioral division.
module ozcore_crt_seq_s1 (
    input  logic clk, rst, start,
    input  logic [12*32-1:0] dots,
    output logic [31:0] fp_out,
    output logic out_valid,
    output logic busy
);
    localparam signed [95:0] P      = 96'h006fb193bc3ea899dc188f8900;
    localparam signed [95:0] P_HALF = 96'h0037d8c9de1f544cee0c47c480;

    function automatic int get_m(input int j);
        case (j)
            0: get_m=256; 1: get_m=255; 2: get_m=253; 3: get_m=251;
            4: get_m=247; 5: get_m=241; 6: get_m=239; 7: get_m=233;
            8: get_m=229; 9: get_m=227; 10: get_m=223; 11: get_m=217;
            default: get_m=1;
        endcase
    endfunction
    function automatic int get_inv(input int j);
        case (j)
            0: get_inv=185; 1: get_inv=211; 2: get_inv=124; 3: get_inv=76;
            4: get_inv=72; 5: get_inv=231; 6: get_inv=45; 7: get_inv=78;
            8: get_inv=45; 9: get_inv=217; 10: get_inv=10; 11: get_inv=149;
            default: get_inv=1;
        endcase
    endfunction
    function automatic logic [95:0] get_mi(input int j);
        case (j)
            0: get_mi=96'h006fb193bc3ea899dc188f89; 1: get_mi=96'h007021b571b058f2cee77700;
            2: get_mi=96'h007104a1a1220ec62ea47d00; 3: get_mi=96'h0071eb2b962d8c5791f24b00;
            4: get_mi=96'h0073c372c52d3fd878537f00; 5: get_mi=96'h0076a542a3d8559e1ff81900;
            6: get_mi=96'h0077a36e0af935210e070700; 7: get_mi=96'h007ab81e79209615d1f5a100;
            8: get_mi=96'h007cdcdf48eff7ba887dd500; 9: get_mi=96'h007df68043f0f445c335a300;
            10: get_mi=96'h008038e9e26ef65bad749700; 11: get_mi=96'h0083c483d1198d189bd63100;
            default: get_mi=96'sd0;
        endcase
    endfunction
    function automatic int red16(input int x, input int mm);
        int comp, q1, q2, q3, q4;
        begin
            comp = 256 - mm;
            q1 = comp * (x >> 8)  + (x & 8'hff);
            q2 = comp * (q1 >> 8) + (q1 & 8'hff);
            q3 = comp * (q2 >> 8) + (q2 & 8'hff);
            q4 = comp * (q3 >> 8) + (q3 & 8'hff);
            red16 = (q4 < mm) ? q4 : (q4 - mm);
        end
    endfunction
    function automatic int mod32(input int v, input int mm);
        int a, r;
        begin
            if (mm == 256) mod32 = v & 8'hff;
            else begin
                a = (v < 0) ? -v : v;
                r = red16((a >> 16) & 16'hffff, mm);
                r = red16(((r << 8) | ((a >> 8) & 8'hff)) & 16'hffff, mm);
                r = red16(((r << 8) | (a & 8'hff)) & 16'hffff, mm);
                mod32 = (v < 0 && r != 0) ? (mm - r) : r;
            end
        end
    endfunction
    function automatic logic [31:0] i2f(input logic signed [95:0] x);
        logic s; logic [31:0] a; logic [5:0] msb; logic [22:0] frac; logic [7:0] e; int k;
        begin
            s = x[31]; a = s ? -x[31:0] : x[31:0]; msb = 0; frac='0; e='0;
            for (k=0;k<32;k++) if (a[k]) msb = k[5:0];
            if (a != 0) begin
                e = 8'd127 + msb;
                if (msb >= 6'd23) frac = a >> (msb - 6'd23);
                else frac = a << (6'd23 - msb);
            end
            i2f = {s, e, frac[22:0]};
        end
    endfunction

    logic [3:0] j;
    logic signed [95:0] sum, amyi;
    logic [31:0] t;
    int mm, iv, r;

    assign busy = (j != 0) || out_valid;

    always_ff @(posedge clk) begin
        if (rst) begin
            j <= 0; sum = '0; out_valid <= 1'b0; fp_out <= '0;
        end else if (start && !busy) begin
            j <= 1; sum = '0; out_valid <= 1'b0;
        end else if (j != 0) begin
            mm = get_m(j-1); iv = get_inv(j-1);
            r = mod32(dots[(j-1)*32 +: 32], mm);
            t = mod32(r * iv, mm);
            if (t > (mm >> 1)) t = t - mm;
            amyi = $signed(get_mi(j-1)) * $signed(t);
            sum = sum + amyi;
            if (sum > P_HALF) sum = sum - P;
            else if (sum < -P_HALF) sum = sum + P;
            if (j == 12) begin
                fp_out <= i2f(sum);
                out_valid <= 1'b1;
                j <= 0;
            end else j <= j + 1;
        end else out_valid <= 1'b0;
    end
endmodule
