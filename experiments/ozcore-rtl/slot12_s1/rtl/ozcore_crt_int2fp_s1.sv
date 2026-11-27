// Complete single-slot postprocess: 12-modulus CRT, balanced mod-P wrap, int32->float.
module ozcore_crt_int2fp_s1 (
    input  logic signed [12*32-1:0] dots,
    output logic [31:0] fp_out,
    output logic signed [95:0] crt_out
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
            4: get_inv=72;  5: get_inv=231; 6: get_inv=45;  7: get_inv=78;
            8: get_inv=45;  9: get_inv=217; 10: get_inv=10; 11: get_inv=149;
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

    // Paper's divider-free modulo: red16 = new_single_s12 with comp=256-m.
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

    // 32-bit signed reduction by three Horner limbs, no divider.
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

    logic signed [31:0] t [12];
    logic signed [95:0] amyi [12];
    logic signed [95:0] sum;
    int rtmp;
    integer j;

    always_comb begin
        for (j = 0; j < 12; j++) begin
            int mm, iv;
            mm = get_m(j); iv = get_inv(j);
            rtmp = mod32(dots[j*32 +: 32], mm);
            rtmp = mod32(rtmp * iv, mm);
            t[j] = rtmp;
            if (t[j] > (mm >> 1)) t[j] = t[j] - mm;
            amyi[j] = $signed(get_mi(j)) * t[j];
        end
        sum = 96'sd0;
        for (j = 0; j < 12; j++) begin
            sum = sum + amyi[j];
            if (sum > P_HALF) sum = sum - P;
            else if (sum < -P_HALF) sum = sum + P;
        end
        crt_out = sum;
    end

    // int32 -> binary32 (truncating; no rounding/sticky).
    logic sign;
    logic [31:0] mag;
    logic [5:0] msb;
    logic [22:0] frac;
    logic [7:0] expo;
    integer k;
    always_comb begin
        sign = sum[31];
        mag = sign ? -sum[31:0] : sum[31:0];
        msb = 0;
        for (k = 0; k < 32; k++) if (mag[k]) msb = k[5:0];
        frac = '0; expo = '0;
        if (mag != 0) begin
            expo = 8'd127 + msb;
            if (msb >= 6'd23) frac = (mag >> (msb - 6'd23));
            else               frac = (mag << (6'd23 - msb));
        end
        fp_out = {sign, expo, frac[22:0]};
    end
endmodule
