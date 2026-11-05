/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : O-2018.06-SP1
// Date      : Thu Nov  5 15:38:00 2026
/////////////////////////////////////////////////////////////


module SNPS_CLOCK_GATE_HIGH_int8_mac ( CLK, EN, ENCLK, TE );
  input CLK, EN, TE;
  output ENCLK;


  CKLNQD1BWP40P140 latch ( .CP(CLK), .E(EN), .TE(TE), .Q(ENCLK) );
endmodule


module int8_mac ( clk, rst_n, valid_in, acc_clear, a, b, acc, valid_out );
  input [7:0] a;
  input [7:0] b;
  output [31:0] acc;
  input clk, rst_n, valid_in, acc_clear;
  output valid_out;
  wire   v_s1, clear_s1, v_s2, clear_s2, N74, N75, N76, N77, N78, N79, N80,
         N81, N82, N83, N84, N85, N86, N87, N88, N89, N90, N91, N92, N93, N94,
         N95, N96, N97, N98, N99, N100, N101, N102, N103, N104, N105, net37,
         n6, n7, \intadd_0/CI , \intadd_0/SUM[12] , \intadd_0/SUM[11] ,
         \intadd_0/SUM[10] , \intadd_0/SUM[9] , \intadd_0/SUM[8] ,
         \intadd_0/SUM[7] , \intadd_0/SUM[6] , \intadd_0/SUM[5] ,
         \intadd_0/SUM[4] , \intadd_0/SUM[3] , \intadd_0/SUM[2] ,
         \intadd_0/SUM[1] , \intadd_0/SUM[0] , \intadd_0/n13 , \intadd_0/n12 ,
         \intadd_0/n11 , \intadd_0/n10 , \intadd_0/n9 , \intadd_0/n8 ,
         \intadd_0/n7 , \intadd_0/n6 , \intadd_0/n5 , \intadd_0/n4 ,
         \intadd_0/n3 , \intadd_0/n2 , \intadd_0/n1 , \intadd_1/A[11] ,
         \intadd_1/A[10] , \intadd_1/A[9] , \intadd_1/A[8] , \intadd_1/A[7] ,
         \intadd_1/A[6] , \intadd_1/A[5] , \intadd_1/A[4] , \intadd_1/A[3] ,
         \intadd_1/A[2] , \intadd_1/A[1] , \intadd_1/A[0] , \intadd_1/B[11] ,
         \intadd_1/B[10] , \intadd_1/B[9] , \intadd_1/B[8] , \intadd_1/B[7] ,
         \intadd_1/B[6] , \intadd_1/B[5] , \intadd_1/B[4] , \intadd_1/B[3] ,
         \intadd_1/B[2] , \intadd_1/B[1] , \intadd_1/B[0] , \intadd_1/CI ,
         \intadd_1/SUM[11] , \intadd_1/SUM[10] , \intadd_1/SUM[9] ,
         \intadd_1/SUM[8] , \intadd_1/SUM[7] , \intadd_1/SUM[6] ,
         \intadd_1/SUM[5] , \intadd_1/SUM[4] , \intadd_1/SUM[3] ,
         \intadd_1/SUM[2] , \intadd_1/SUM[1] , \intadd_1/SUM[0] ,
         \intadd_1/n12 , \intadd_1/n11 , \intadd_1/n10 , \intadd_1/n9 ,
         \intadd_1/n8 , \intadd_1/n7 , \intadd_1/n6 , \intadd_1/n5 ,
         \intadd_1/n4 , \intadd_1/n3 , \intadd_1/n2 , \intadd_1/n1 , n8, n9,
         n10, n11, n12, n13, n14, n15, n16, n17, n18, n19, n20, n21, n22, n23,
         n24, n25, n26, n27, n28, n29, n30, n31, n32, n33, n34, n35, n36, n37,
         n38, n39, n40, n41, n42, n43, n44, n45, n46, n47, n48, n49, n50, n51,
         n52, n53, n54, n55, n56, n57, n58, n59, n60, n61, n62, n63, n64, n65,
         n66, n67, n68, n69, n70, n71, n72, n73, n74, n75, n76, n77, n78, n79,
         n80, n81, n82, n83, n84, n85, n86, n87, n88, n89, n90, n91, n92, n93,
         n94, n95, n96, n97, n98, n99, n100, n101, n102, n103, n104, n105,
         n106, n107, n108, n109, n110, n111, n112, n113, n114, n115, n116,
         n117, n118, n119, n120, n121, n122, n123, n124, n125, n126, n127,
         n128, n129, n130, n131, n132, n133, n134, n135, n136, n137, n138,
         n139, n140, n141, n142, n143, n144, n145, n146, n147, n148, n149,
         n150, n151, n152, n153, n154, n155, n156, n157, n158, n159, n160,
         n161, n162, n163, n164, n165, n166, n167, n168, n169, n170, n171,
         n172, n173, n174, n175, n176, n177, n178, n179, n180, n181, n182,
         n183, n184, n185, n186, n187, n188, n189, n190, n191, n192, n193,
         n194, n195, n196, n197, n198, n199, n200, n201, n202, n203, n204,
         n205, n206, n207, n208, n209, n210, n211, n212, n213, n214, n215,
         n216;
  wire   [7:0] a_s1;
  wire   [7:0] b_s1;
  wire   [15:0] prod_comb;
  wire   [31:0] prod_ext_s2;

  SNPS_CLOCK_GATE_HIGH_int8_mac clk_gate_acc_reg ( .CLK(clk), .EN(n6), .ENCLK(
        net37), .TE(n7) );
  DFCNQD1BWP40P140 \a_s1_reg[6]  ( .D(a[6]), .CP(clk), .CDN(rst_n), .Q(a_s1[6]) );
  DFCNQD1BWP40P140 \a_s1_reg[4]  ( .D(a[4]), .CP(clk), .CDN(rst_n), .Q(a_s1[4]) );
  DFCNQD1BWP40P140 \a_s1_reg[2]  ( .D(a[2]), .CP(clk), .CDN(rst_n), .Q(a_s1[2]) );
  DFCNQD1BWP40P140 \a_s1_reg[1]  ( .D(a[1]), .CP(clk), .CDN(rst_n), .Q(a_s1[1]) );
  DFCNQD1BWP40P140 \a_s1_reg[0]  ( .D(a[0]), .CP(clk), .CDN(rst_n), .Q(a_s1[0]) );
  DFCNQD1BWP40P140 \b_s1_reg[7]  ( .D(b[7]), .CP(clk), .CDN(rst_n), .Q(b_s1[7]) );
  DFCNQD1BWP40P140 \b_s1_reg[6]  ( .D(b[6]), .CP(clk), .CDN(rst_n), .Q(b_s1[6]) );
  DFCNQD1BWP40P140 \b_s1_reg[5]  ( .D(b[5]), .CP(clk), .CDN(rst_n), .Q(b_s1[5]) );
  DFCNQD1BWP40P140 \b_s1_reg[4]  ( .D(b[4]), .CP(clk), .CDN(rst_n), .Q(b_s1[4]) );
  DFCNQD1BWP40P140 \b_s1_reg[3]  ( .D(b[3]), .CP(clk), .CDN(rst_n), .Q(b_s1[3]) );
  DFCNQD1BWP40P140 \b_s1_reg[2]  ( .D(b[2]), .CP(clk), .CDN(rst_n), .Q(b_s1[2]) );
  DFCNQD1BWP40P140 \b_s1_reg[1]  ( .D(b[1]), .CP(clk), .CDN(rst_n), .Q(b_s1[1]) );
  DFCNQD1BWP40P140 \b_s1_reg[0]  ( .D(b[0]), .CP(clk), .CDN(rst_n), .Q(b_s1[0]) );
  DFCNQD1BWP40P140 clear_s1_reg ( .D(acc_clear), .CP(clk), .CDN(rst_n), .Q(
        clear_s1) );
  DFCNQD1BWP40P140 clear_s2_reg ( .D(clear_s1), .CP(clk), .CDN(rst_n), .Q(
        clear_s2) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[14]  ( .D(prod_comb[14]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[14]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[13]  ( .D(prod_comb[13]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[13]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[12]  ( .D(prod_comb[12]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[12]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[11]  ( .D(prod_comb[11]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[11]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[10]  ( .D(prod_comb[10]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[10]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[9]  ( .D(prod_comb[9]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[9]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[8]  ( .D(prod_comb[8]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[8]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[7]  ( .D(prod_comb[7]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[7]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[6]  ( .D(prod_comb[6]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[6]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[5]  ( .D(prod_comb[5]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[5]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[4]  ( .D(prod_comb[4]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[4]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[3]  ( .D(prod_comb[3]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[3]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[2]  ( .D(prod_comb[2]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[2]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[1]  ( .D(prod_comb[1]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[1]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[0]  ( .D(prod_comb[0]), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[0]) );
  DFCNQD1BWP40P140 v_s1_reg ( .D(valid_in), .CP(clk), .CDN(rst_n), .Q(v_s1) );
  DFCNQD1BWP40P140 v_s2_reg ( .D(v_s1), .CP(clk), .CDN(rst_n), .Q(v_s2) );
  DFCNQD1BWP40P140 valid_out_reg ( .D(v_s2), .CP(clk), .CDN(n216), .Q(
        valid_out) );
  DFCNQD1BWP40P140 \a_s1_reg[7]  ( .D(a[7]), .CP(clk), .CDN(rst_n), .Q(a_s1[7]) );
  DFCNQD1BWP40P140 \a_s1_reg[5]  ( .D(a[5]), .CP(clk), .CDN(rst_n), .Q(a_s1[5]) );
  DFCNQD1BWP40P140 \a_s1_reg[3]  ( .D(a[3]), .CP(clk), .CDN(rst_n), .Q(a_s1[3]) );
  DFCNQD1BWP40P140 \prod_ext_s2_reg[15]  ( .D(\intadd_1/n1 ), .CP(clk), .CDN(
        rst_n), .Q(prod_ext_s2[15]) );
  DFCNQD1BWP40P140 \acc_reg[28]  ( .D(N102), .CP(net37), .CDN(n216), .Q(
        acc[28]) );
  DFCNQD1BWP40P140 \acc_reg[26]  ( .D(N100), .CP(net37), .CDN(n216), .Q(
        acc[26]) );
  DFCNQD1BWP40P140 \acc_reg[24]  ( .D(N98), .CP(net37), .CDN(n216), .Q(acc[24]) );
  DFCNQD1BWP40P140 \acc_reg[22]  ( .D(N96), .CP(net37), .CDN(n216), .Q(acc[22]) );
  DFCNQD1BWP40P140 \acc_reg[20]  ( .D(N94), .CP(net37), .CDN(n216), .Q(acc[20]) );
  DFCNQD1BWP40P140 \acc_reg[18]  ( .D(N92), .CP(net37), .CDN(n216), .Q(acc[18]) );
  DFCNQD1BWP40P140 \acc_reg[31]  ( .D(N105), .CP(net37), .CDN(rst_n), .Q(
        acc[31]) );
  DFCNQD1BWP40P140 \acc_reg[1]  ( .D(N75), .CP(net37), .CDN(n216), .Q(acc[1])
         );
  DFCNQD1BWP40P140 \acc_reg[0]  ( .D(N74), .CP(net37), .CDN(n216), .Q(acc[0])
         );
  DFCNQD1BWP40P140 \acc_reg[14]  ( .D(N88), .CP(net37), .CDN(rst_n), .Q(
        acc[14]) );
  DFCNQD1BWP40P140 \acc_reg[13]  ( .D(N87), .CP(net37), .CDN(n216), .Q(acc[13]) );
  DFCNQD1BWP40P140 \acc_reg[12]  ( .D(N86), .CP(net37), .CDN(n216), .Q(acc[12]) );
  DFCNQD1BWP40P140 \acc_reg[11]  ( .D(N85), .CP(net37), .CDN(n216), .Q(acc[11]) );
  DFCNQD1BWP40P140 \acc_reg[10]  ( .D(N84), .CP(net37), .CDN(n216), .Q(acc[10]) );
  DFCNQD1BWP40P140 \acc_reg[9]  ( .D(N83), .CP(net37), .CDN(n216), .Q(acc[9])
         );
  DFCNQD1BWP40P140 \acc_reg[8]  ( .D(N82), .CP(net37), .CDN(n216), .Q(acc[8])
         );
  DFCNQD1BWP40P140 \acc_reg[7]  ( .D(N81), .CP(net37), .CDN(n216), .Q(acc[7])
         );
  DFCNQD1BWP40P140 \acc_reg[6]  ( .D(N80), .CP(net37), .CDN(n216), .Q(acc[6])
         );
  DFCNQD1BWP40P140 \acc_reg[5]  ( .D(N79), .CP(net37), .CDN(n216), .Q(acc[5])
         );
  DFCNQD1BWP40P140 \acc_reg[4]  ( .D(N78), .CP(net37), .CDN(n216), .Q(acc[4])
         );
  DFCNQD1BWP40P140 \acc_reg[3]  ( .D(N77), .CP(net37), .CDN(n216), .Q(acc[3])
         );
  DFCNQD1BWP40P140 \acc_reg[2]  ( .D(N76), .CP(net37), .CDN(n216), .Q(acc[2])
         );
  DFCNQD1BWP40P140 \acc_reg[29]  ( .D(N103), .CP(net37), .CDN(rst_n), .Q(
        acc[29]) );
  DFCNQD1BWP40P140 \acc_reg[27]  ( .D(N101), .CP(net37), .CDN(n216), .Q(
        acc[27]) );
  DFCNQD1BWP40P140 \acc_reg[25]  ( .D(N99), .CP(net37), .CDN(n216), .Q(acc[25]) );
  DFCNQD1BWP40P140 \acc_reg[23]  ( .D(N97), .CP(net37), .CDN(n216), .Q(acc[23]) );
  DFCNQD1BWP40P140 \acc_reg[21]  ( .D(N95), .CP(net37), .CDN(n216), .Q(acc[21]) );
  DFCNQD1BWP40P140 \acc_reg[19]  ( .D(N93), .CP(net37), .CDN(n216), .Q(acc[19]) );
  DFCNQD1BWP40P140 \acc_reg[17]  ( .D(N91), .CP(net37), .CDN(n216), .Q(acc[17]) );
  DFCNQD1BWP40P140 \acc_reg[16]  ( .D(N90), .CP(net37), .CDN(n216), .Q(acc[16]) );
  DFCNQD1BWP40P140 \acc_reg[30]  ( .D(N104), .CP(net37), .CDN(n216), .Q(
        acc[30]) );
  DFCNQD1BWP40P140 \acc_reg[15]  ( .D(N89), .CP(net37), .CDN(n216), .Q(acc[15]) );
  FA1D0BWP40P140 \intadd_0/U2  ( .A(prod_ext_s2[14]), .B(acc[14]), .CI(
        \intadd_0/n2 ), .CO(\intadd_0/n1 ), .S(\intadd_0/SUM[12] ) );
  FA1D0BWP40P140 \intadd_0/U3  ( .A(prod_ext_s2[13]), .B(acc[13]), .CI(
        \intadd_0/n3 ), .CO(\intadd_0/n2 ), .S(\intadd_0/SUM[11] ) );
  FA1D0BWP40P140 \intadd_0/U4  ( .A(prod_ext_s2[12]), .B(acc[12]), .CI(
        \intadd_0/n4 ), .CO(\intadd_0/n3 ), .S(\intadd_0/SUM[10] ) );
  FA1D0BWP40P140 \intadd_0/U5  ( .A(prod_ext_s2[11]), .B(acc[11]), .CI(
        \intadd_0/n5 ), .CO(\intadd_0/n4 ), .S(\intadd_0/SUM[9] ) );
  FA1D0BWP40P140 \intadd_0/U6  ( .A(prod_ext_s2[10]), .B(acc[10]), .CI(
        \intadd_0/n6 ), .CO(\intadd_0/n5 ), .S(\intadd_0/SUM[8] ) );
  FA1D0BWP40P140 \intadd_0/U7  ( .A(prod_ext_s2[9]), .B(acc[9]), .CI(
        \intadd_0/n7 ), .CO(\intadd_0/n6 ), .S(\intadd_0/SUM[7] ) );
  FA1D0BWP40P140 \intadd_0/U8  ( .A(prod_ext_s2[8]), .B(acc[8]), .CI(
        \intadd_0/n8 ), .CO(\intadd_0/n7 ), .S(\intadd_0/SUM[6] ) );
  FA1D0BWP40P140 \intadd_0/U9  ( .A(prod_ext_s2[7]), .B(acc[7]), .CI(
        \intadd_0/n9 ), .CO(\intadd_0/n8 ), .S(\intadd_0/SUM[5] ) );
  FA1D0BWP40P140 \intadd_0/U10  ( .A(prod_ext_s2[6]), .B(acc[6]), .CI(
        \intadd_0/n10 ), .CO(\intadd_0/n9 ), .S(\intadd_0/SUM[4] ) );
  FA1D0BWP40P140 \intadd_0/U11  ( .A(prod_ext_s2[5]), .B(acc[5]), .CI(
        \intadd_0/n11 ), .CO(\intadd_0/n10 ), .S(\intadd_0/SUM[3] ) );
  FA1D0BWP40P140 \intadd_0/U12  ( .A(prod_ext_s2[4]), .B(acc[4]), .CI(
        \intadd_0/n12 ), .CO(\intadd_0/n11 ), .S(\intadd_0/SUM[2] ) );
  FA1D0BWP40P140 \intadd_0/U13  ( .A(prod_ext_s2[3]), .B(acc[3]), .CI(
        \intadd_0/n13 ), .CO(\intadd_0/n12 ), .S(\intadd_0/SUM[1] ) );
  FA1D0BWP40P140 \intadd_0/U14  ( .A(prod_ext_s2[2]), .B(acc[2]), .CI(
        \intadd_0/CI ), .CO(\intadd_0/n13 ), .S(\intadd_0/SUM[0] ) );
  FA1D0BWP40P140 \intadd_1/U13  ( .A(\intadd_1/B[0] ), .B(\intadd_1/A[0] ), 
        .CI(\intadd_1/CI ), .CO(\intadd_1/n12 ), .S(\intadd_1/SUM[0] ) );
  FA1D0BWP40P140 \intadd_1/U12  ( .A(\intadd_1/B[1] ), .B(\intadd_1/A[1] ), 
        .CI(\intadd_1/n12 ), .CO(\intadd_1/n11 ), .S(\intadd_1/SUM[1] ) );
  FA1D0BWP40P140 \intadd_1/U11  ( .A(\intadd_1/B[2] ), .B(\intadd_1/A[2] ), 
        .CI(\intadd_1/n11 ), .CO(\intadd_1/n10 ), .S(\intadd_1/SUM[2] ) );
  FA1D0BWP40P140 \intadd_1/U10  ( .A(\intadd_1/B[3] ), .B(\intadd_1/A[3] ), 
        .CI(\intadd_1/n10 ), .CO(\intadd_1/n9 ), .S(\intadd_1/SUM[3] ) );
  FA1D0BWP40P140 \intadd_1/U9  ( .A(\intadd_1/B[4] ), .B(\intadd_1/A[4] ), 
        .CI(\intadd_1/n9 ), .CO(\intadd_1/n8 ), .S(\intadd_1/SUM[4] ) );
  FA1D0BWP40P140 \intadd_1/U8  ( .A(\intadd_1/B[5] ), .B(\intadd_1/A[5] ), 
        .CI(\intadd_1/n8 ), .CO(\intadd_1/n7 ), .S(\intadd_1/SUM[5] ) );
  FA1D0BWP40P140 \intadd_1/U7  ( .A(\intadd_1/B[6] ), .B(\intadd_1/A[6] ), 
        .CI(\intadd_1/n7 ), .CO(\intadd_1/n6 ), .S(\intadd_1/SUM[6] ) );
  FA1D0BWP40P140 \intadd_1/U6  ( .A(\intadd_1/B[7] ), .B(\intadd_1/A[7] ), 
        .CI(\intadd_1/n6 ), .CO(\intadd_1/n5 ), .S(\intadd_1/SUM[7] ) );
  FA1D0BWP40P140 \intadd_1/U5  ( .A(\intadd_1/B[8] ), .B(\intadd_1/A[8] ), 
        .CI(\intadd_1/n5 ), .CO(\intadd_1/n4 ), .S(\intadd_1/SUM[8] ) );
  FA1D0BWP40P140 \intadd_1/U4  ( .A(\intadd_1/B[9] ), .B(\intadd_1/A[9] ), 
        .CI(\intadd_1/n4 ), .CO(\intadd_1/n3 ), .S(\intadd_1/SUM[9] ) );
  FA1D0BWP40P140 \intadd_1/U3  ( .A(\intadd_1/B[10] ), .B(\intadd_1/A[10] ), 
        .CI(\intadd_1/n3 ), .CO(\intadd_1/n2 ), .S(\intadd_1/SUM[10] ) );
  FA1D0BWP40P140 \intadd_1/U2  ( .A(\intadd_1/B[11] ), .B(\intadd_1/A[11] ), 
        .CI(\intadd_1/n2 ), .CO(\intadd_1/n1 ), .S(\intadd_1/SUM[11] ) );
  TIELBWP40P140 U42 ( .ZN(n7) );
  INVD0P7BWP40P140 U43 ( .I(rst_n), .ZN(n8) );
  INVD0P7BWP40P140 U44 ( .I(n8), .ZN(n216) );
  INVD0P7BWP40P140 U45 ( .I(v_s2), .ZN(n23) );
  INVD0P7BWP40P140 U46 ( .I(clear_s2), .ZN(n22) );
  ND2D0P7BWP40P140 U47 ( .A1(n23), .A2(n22), .ZN(n6) );
  INVD0P7BWP40P140 U48 ( .I(a_s1[0]), .ZN(n10) );
  INVD0P7BWP40P140 U49 ( .I(b_s1[0]), .ZN(n65) );
  NR2D0P7BWP40P140 U50 ( .A1(n10), .A2(n65), .ZN(prod_comb[0]) );
  INVD0P7BWP40P140 U51 ( .I(a_s1[1]), .ZN(n73) );
  NR2D0P7BWP40P140 U52 ( .A1(prod_comb[0]), .A2(n73), .ZN(n12) );
  ND2D0P7BWP40P140 U53 ( .A1(a_s1[0]), .A2(a_s1[1]), .ZN(n53) );
  NR2D0P7BWP40P140 U54 ( .A1(a_s1[1]), .A2(n10), .ZN(n72) );
  ND2D0P7BWP40P140 U55 ( .A1(b_s1[1]), .A2(n72), .ZN(n9) );
  OAI21D0P7BWP40P140 U56 ( .A1(b_s1[1]), .A2(n53), .B(n9), .ZN(n11) );
  INVD0P7BWP40P140 U57 ( .I(b_s1[1]), .ZN(n63) );
  OAI211D0BWP40P140 U58 ( .A1(n10), .A2(n63), .B(a_s1[1]), .C(n65), .ZN(n14)
         );
  OA21D0BWP40P140 U59 ( .A1(n12), .A2(n11), .B(n14), .Z(prod_comb[1]) );
  NR2D0P7BWP40P140 U60 ( .A1(a_s1[0]), .A2(n73), .ZN(n36) );
  AOI22D0P7BWP40P140 U61 ( .A1(n72), .A2(b_s1[2]), .B1(n36), .B2(n63), .ZN(n13) );
  OAI21D0P7BWP40P140 U62 ( .A1(b_s1[2]), .A2(n53), .B(n13), .ZN(n15) );
  INVD0P7BWP40P140 U63 ( .I(a_s1[2]), .ZN(n25) );
  AOI22D0P7BWP40P140 U64 ( .A1(a_s1[1]), .A2(n25), .B1(a_s1[2]), .B2(n73), 
        .ZN(n100) );
  OAI21D0P7BWP40P140 U65 ( .A1(n100), .A2(n65), .B(n14), .ZN(n16) );
  ND2D0P7BWP40P140 U66 ( .A1(n15), .A2(n16), .ZN(\intadd_1/CI ) );
  OA21D0BWP40P140 U67 ( .A1(n16), .A2(n15), .B(\intadd_1/CI ), .Z(prod_comb[2]) );
  INR2D1BWP40P140 U68 ( .A1(acc[0]), .B1(clear_s2), .ZN(n18) );
  OAI21D0P7BWP40P140 U69 ( .A1(prod_ext_s2[0]), .A2(n18), .B(v_s2), .ZN(n17)
         );
  AOI21D0P7BWP40P140 U70 ( .A1(prod_ext_s2[0]), .A2(n18), .B(n17), .ZN(N74) );
  INVD0P7BWP40P140 U71 ( .I(acc[1]), .ZN(n214) );
  ND2D0P7BWP40P140 U72 ( .A1(prod_ext_s2[0]), .A2(acc[0]), .ZN(n215) );
  MUX2ND0BWP40P140 U73 ( .I0(n214), .I1(acc[1]), .S(n215), .ZN(n19) );
  NR2D0P7BWP40P140 U74 ( .A1(n19), .A2(clear_s2), .ZN(n21) );
  OAI21D0P7BWP40P140 U75 ( .A1(prod_ext_s2[1]), .A2(n21), .B(v_s2), .ZN(n20)
         );
  AOI21D0P7BWP40P140 U76 ( .A1(prod_ext_s2[1]), .A2(n21), .B(n20), .ZN(N75) );
  INVD0P7BWP40P140 U77 ( .I(\intadd_1/SUM[0] ), .ZN(prod_comb[3]) );
  INVD0P7BWP40P140 U78 ( .I(\intadd_1/SUM[1] ), .ZN(prod_comb[4]) );
  ND2D0P7BWP40P140 U79 ( .A1(v_s2), .A2(n22), .ZN(n139) );
  INVD0P7BWP40P140 U80 ( .I(n139), .ZN(n138) );
  NR2D0P7BWP40P140 U81 ( .A1(n23), .A2(n22), .ZN(n136) );
  AO22D0BWP40P140 U82 ( .A1(n138), .A2(\intadd_0/SUM[0] ), .B1(n136), .B2(
        prod_ext_s2[2]), .Z(N76) );
  INVD0P7BWP40P140 U83 ( .I(\intadd_1/SUM[2] ), .ZN(prod_comb[5]) );
  AO22D0BWP40P140 U84 ( .A1(n138), .A2(\intadd_0/SUM[1] ), .B1(n136), .B2(
        prod_ext_s2[3]), .Z(N77) );
  INVD0P7BWP40P140 U85 ( .I(\intadd_1/SUM[3] ), .ZN(prod_comb[6]) );
  AO22D0BWP40P140 U86 ( .A1(n138), .A2(\intadd_0/SUM[2] ), .B1(n136), .B2(
        prod_ext_s2[4]), .Z(N78) );
  INVD0P7BWP40P140 U87 ( .I(\intadd_1/SUM[4] ), .ZN(prod_comb[7]) );
  AO22D0BWP40P140 U88 ( .A1(n138), .A2(\intadd_0/SUM[3] ), .B1(n136), .B2(
        prod_ext_s2[5]), .Z(N79) );
  INVD0P7BWP40P140 U89 ( .I(\intadd_1/SUM[5] ), .ZN(prod_comb[8]) );
  AO22D0BWP40P140 U90 ( .A1(n138), .A2(\intadd_0/SUM[4] ), .B1(n136), .B2(
        prod_ext_s2[6]), .Z(N80) );
  INVD0P7BWP40P140 U91 ( .I(\intadd_1/SUM[6] ), .ZN(prod_comb[9]) );
  AO22D0BWP40P140 U92 ( .A1(n138), .A2(\intadd_0/SUM[5] ), .B1(n136), .B2(
        prod_ext_s2[7]), .Z(N81) );
  INVD0P7BWP40P140 U93 ( .I(\intadd_1/SUM[7] ), .ZN(prod_comb[10]) );
  AO22D0BWP40P140 U94 ( .A1(n138), .A2(\intadd_0/SUM[6] ), .B1(n136), .B2(
        prod_ext_s2[8]), .Z(N82) );
  INVD0P7BWP40P140 U95 ( .I(\intadd_1/SUM[8] ), .ZN(prod_comb[11]) );
  AO22D0BWP40P140 U96 ( .A1(n138), .A2(\intadd_0/SUM[7] ), .B1(n136), .B2(
        prod_ext_s2[9]), .Z(N83) );
  INVD0P7BWP40P140 U97 ( .I(\intadd_1/SUM[9] ), .ZN(prod_comb[12]) );
  AO22D0BWP40P140 U98 ( .A1(n138), .A2(\intadd_0/SUM[8] ), .B1(n136), .B2(
        prod_ext_s2[10]), .Z(N84) );
  INVD0P7BWP40P140 U99 ( .I(\intadd_1/SUM[10] ), .ZN(prod_comb[13]) );
  AO22D0BWP40P140 U100 ( .A1(n138), .A2(\intadd_0/SUM[9] ), .B1(n136), .B2(
        prod_ext_s2[11]), .Z(N85) );
  AO22D0BWP40P140 U101 ( .A1(n138), .A2(\intadd_0/SUM[10] ), .B1(n136), .B2(
        prod_ext_s2[12]), .Z(N86) );
  INVD0P7BWP40P140 U102 ( .I(\intadd_1/SUM[11] ), .ZN(prod_comb[14]) );
  INVD0P7BWP40P140 U103 ( .I(b_s1[2]), .ZN(n78) );
  AOI22D0P7BWP40P140 U104 ( .A1(n72), .A2(b_s1[3]), .B1(n36), .B2(n78), .ZN(
        n24) );
  OAI21D0P7BWP40P140 U105 ( .A1(b_s1[3]), .A2(n53), .B(n24), .ZN(n27) );
  INVD0P7BWP40P140 U106 ( .I(a_s1[3]), .ZN(n88) );
  AOI33D0BWP40P140 U107 ( .A1(a_s1[1]), .A2(a_s1[2]), .A3(n88), .B1(a_s1[3]), 
        .B2(n25), .B3(n73), .ZN(n99) );
  AOI22D0P7BWP40P140 U108 ( .A1(b_s1[0]), .A2(n88), .B1(a_s1[3]), .B2(n65), 
        .ZN(n26) );
  AOI22D0P7BWP40P140 U109 ( .A1(b_s1[1]), .A2(n88), .B1(a_s1[3]), .B2(n63), 
        .ZN(n38) );
  OAI22D0P7BWP40P140 U110 ( .A1(n99), .A2(n26), .B1(n100), .B2(n38), .ZN(n28)
         );
  ND2D0P7BWP40P140 U111 ( .A1(n27), .A2(n28), .ZN(\intadd_1/A[1] ) );
  OAI21D0P7BWP40P140 U112 ( .A1(n28), .A2(n27), .B(\intadd_1/A[1] ), .ZN(
        \intadd_1/A[0] ) );
  INVD0P7BWP40P140 U113 ( .I(n100), .ZN(n48) );
  NR3D0P7BWP40P140 U114 ( .A1(n88), .A2(a_s1[1]), .A3(a_s1[2]), .ZN(n29) );
  AOI31D0BWP40P140 U115 ( .A1(a_s1[3]), .A2(n65), .A3(n48), .B(n29), .ZN(
        \intadd_1/B[0] ) );
  INVD0P7BWP40P140 U116 ( .I(a_s1[4]), .ZN(n30) );
  INVD0P7BWP40P140 U117 ( .I(a_s1[5]), .ZN(n109) );
  AOI33D0BWP40P140 U118 ( .A1(a_s1[5]), .A2(n30), .A3(n88), .B1(a_s1[4]), .B2(
        a_s1[3]), .B3(n109), .ZN(n125) );
  NR2D0P7BWP40P140 U119 ( .A1(a_s1[4]), .A2(n88), .ZN(n31) );
  AOI21D0P7BWP40P140 U120 ( .A1(a_s1[4]), .A2(n88), .B(n31), .ZN(n126) );
  AOI221D0BWP40P140 U121 ( .A1(b_s1[0]), .A2(n125), .B1(n126), .B2(n125), .C(
        n109), .ZN(n34) );
  INVD0P7BWP40P140 U122 ( .I(b_s1[4]), .ZN(n101) );
  AOI22D0P7BWP40P140 U123 ( .A1(n72), .A2(b_s1[5]), .B1(n36), .B2(n101), .ZN(
        n32) );
  OAI21D0P7BWP40P140 U124 ( .A1(b_s1[5]), .A2(n53), .B(n32), .ZN(n33) );
  ND2D0P7BWP40P140 U125 ( .A1(n34), .A2(n33), .ZN(n50) );
  OAI21D0P7BWP40P140 U126 ( .A1(n34), .A2(n33), .B(n50), .ZN(\intadd_1/A[2] )
         );
  AOI22D0P7BWP40P140 U127 ( .A1(b_s1[2]), .A2(a_s1[3]), .B1(n88), .B2(n78), 
        .ZN(n39) );
  INVD0P7BWP40P140 U128 ( .I(n99), .ZN(n61) );
  INVD0P7BWP40P140 U129 ( .I(b_s1[3]), .ZN(n91) );
  AOI22D0P7BWP40P140 U130 ( .A1(a_s1[3]), .A2(b_s1[3]), .B1(n91), .B2(n88), 
        .ZN(n49) );
  AOI22D0P7BWP40P140 U131 ( .A1(n39), .A2(n61), .B1(n49), .B2(n48), .ZN(n42)
         );
  AOI22D0P7BWP40P140 U132 ( .A1(b_s1[1]), .A2(a_s1[5]), .B1(n109), .B2(n63), 
        .ZN(n46) );
  INVD0P7BWP40P140 U133 ( .I(n126), .ZN(n96) );
  AOI221D0BWP40P140 U134 ( .A1(b_s1[0]), .A2(a_s1[5]), .B1(n65), .B2(n109), 
        .C(n125), .ZN(n35) );
  AOI21D0P7BWP40P140 U135 ( .A1(n46), .A2(n96), .B(n35), .ZN(n41) );
  ND2D0P7BWP40P140 U136 ( .A1(b_s1[0]), .A2(n96), .ZN(n45) );
  INVD0P7BWP40P140 U137 ( .I(n36), .ZN(n55) );
  OAI22D0P7BWP40P140 U138 ( .A1(b_s1[4]), .A2(n53), .B1(b_s1[3]), .B2(n55), 
        .ZN(n37) );
  AOI21D0P7BWP40P140 U139 ( .A1(n72), .A2(b_s1[4]), .B(n37), .ZN(n44) );
  MAOI22D0BWP40P140 U140 ( .A1(n39), .A2(n48), .B1(n99), .B2(n38), .ZN(n43) );
  FA1D0BWP40P140 U141 ( .A(n42), .B(n41), .CI(n40), .CO(\intadd_1/B[3] ), .S(
        \intadd_1/B[2] ) );
  FA1D0BWP40P140 U142 ( .A(n45), .B(n44), .CI(n43), .CO(n40), .S(
        \intadd_1/B[1] ) );
  INVD0P7BWP40P140 U143 ( .I(n125), .ZN(n111) );
  AOI22D0P7BWP40P140 U144 ( .A1(b_s1[2]), .A2(a_s1[5]), .B1(n109), .B2(n78), 
        .ZN(n67) );
  AOI22D0P7BWP40P140 U145 ( .A1(n111), .A2(n46), .B1(n67), .B2(n96), .ZN(n52)
         );
  INVD0P7BWP40P140 U146 ( .I(a_s1[6]), .ZN(n64) );
  AOI22D0P7BWP40P140 U147 ( .A1(a_s1[5]), .A2(a_s1[6]), .B1(n64), .B2(n109), 
        .ZN(n114) );
  ND2D0P7BWP40P140 U148 ( .A1(b_s1[0]), .A2(n114), .ZN(n60) );
  OAI22D0P7BWP40P140 U149 ( .A1(b_s1[5]), .A2(n55), .B1(b_s1[6]), .B2(n53), 
        .ZN(n47) );
  AOI21D0P7BWP40P140 U150 ( .A1(n72), .A2(b_s1[6]), .B(n47), .ZN(n59) );
  AOI22D0P7BWP40P140 U151 ( .A1(b_s1[4]), .A2(a_s1[3]), .B1(n88), .B2(n101), 
        .ZN(n62) );
  AOI22D0P7BWP40P140 U152 ( .A1(n49), .A2(n61), .B1(n62), .B2(n48), .ZN(n58)
         );
  FA1D0BWP40P140 U153 ( .A(n52), .B(n51), .CI(n50), .CO(\intadd_1/B[4] ), .S(
        \intadd_1/A[3] ) );
  INVD0P7BWP40P140 U154 ( .I(n114), .ZN(n135) );
  INVD0P7BWP40P140 U155 ( .I(a_s1[7]), .ZN(n131) );
  AOI221D0BWP40P140 U156 ( .A1(b_s1[0]), .A2(n114), .B1(a_s1[6]), .B2(n135), 
        .C(n131), .ZN(n57) );
  MAOI22D0BWP40P140 U157 ( .A1(b_s1[7]), .A2(n72), .B1(n53), .B2(b_s1[7]), 
        .ZN(n54) );
  OAI21D0P7BWP40P140 U158 ( .A1(b_s1[6]), .A2(n55), .B(n54), .ZN(n56) );
  ND2D0P7BWP40P140 U159 ( .A1(n57), .A2(n56), .ZN(n85) );
  OAI21D0P7BWP40P140 U160 ( .A1(n57), .A2(n56), .B(n85), .ZN(n70) );
  FA1D0BWP40P140 U161 ( .A(n60), .B(n59), .CI(n58), .CO(n69), .S(n51) );
  INVD0P7BWP40P140 U162 ( .I(b_s1[5]), .ZN(n112) );
  AOI22D0P7BWP40P140 U163 ( .A1(b_s1[5]), .A2(n88), .B1(a_s1[3]), .B2(n112), 
        .ZN(n77) );
  MAOI22D0BWP40P140 U164 ( .A1(n62), .A2(n61), .B1(n100), .B2(n77), .ZN(n76)
         );
  AOI22D0P7BWP40P140 U165 ( .A1(b_s1[1]), .A2(n131), .B1(a_s1[7]), .B2(n63), 
        .ZN(n79) );
  AOI33D0BWP40P140 U166 ( .A1(a_s1[5]), .A2(a_s1[6]), .A3(n131), .B1(a_s1[7]), 
        .B2(n64), .B3(n109), .ZN(n134) );
  AOI221D0BWP40P140 U167 ( .A1(b_s1[0]), .A2(a_s1[7]), .B1(n65), .B2(n131), 
        .C(n134), .ZN(n66) );
  IAO21D1BWP40P140 U168 ( .A1(n79), .A2(n135), .B(n66), .ZN(n75) );
  AOI22D0P7BWP40P140 U169 ( .A1(a_s1[5]), .A2(b_s1[3]), .B1(n91), .B2(n109), 
        .ZN(n71) );
  AOI22D0P7BWP40P140 U170 ( .A1(n111), .A2(n67), .B1(n71), .B2(n96), .ZN(n74)
         );
  FA1D0BWP40P140 U171 ( .A(n70), .B(n69), .CI(n68), .CO(\intadd_1/B[5] ), .S(
        \intadd_1/A[4] ) );
  AOI22D0P7BWP40P140 U172 ( .A1(b_s1[4]), .A2(a_s1[5]), .B1(n109), .B2(n101), 
        .ZN(n90) );
  AOI22D0P7BWP40P140 U173 ( .A1(n111), .A2(n71), .B1(n90), .B2(n96), .ZN(n87)
         );
  INVD0P7BWP40P140 U174 ( .I(b_s1[7]), .ZN(n130) );
  MAOI22D0BWP40P140 U175 ( .A1(n73), .A2(n130), .B1(n130), .B2(n72), .ZN(n86)
         );
  FA1D0BWP40P140 U176 ( .A(n76), .B(n75), .CI(n74), .CO(n83), .S(n68) );
  INVD0P7BWP40P140 U177 ( .I(b_s1[6]), .ZN(n121) );
  AOI22D0P7BWP40P140 U178 ( .A1(a_s1[3]), .A2(n121), .B1(b_s1[6]), .B2(n88), 
        .ZN(n89) );
  OAI22D0P7BWP40P140 U179 ( .A1(n99), .A2(n77), .B1(n100), .B2(n89), .ZN(n81)
         );
  AOI22D0P7BWP40P140 U180 ( .A1(b_s1[2]), .A2(n131), .B1(a_s1[7]), .B2(n78), 
        .ZN(n92) );
  OAI22D0P7BWP40P140 U181 ( .A1(n135), .A2(n92), .B1(n134), .B2(n79), .ZN(n80)
         );
  NR2D0P7BWP40P140 U182 ( .A1(n81), .A2(n80), .ZN(n95) );
  AOI21D0P7BWP40P140 U183 ( .A1(n81), .A2(n80), .B(n95), .ZN(n82) );
  FA1D0BWP40P140 U184 ( .A(n84), .B(n83), .CI(n82), .CO(\intadd_1/B[6] ), .S(
        \intadd_1/A[5] ) );
  FA1D0BWP40P140 U185 ( .A(n87), .B(n86), .CI(n85), .CO(n94), .S(n84) );
  AOI22D0P7BWP40P140 U186 ( .A1(a_s1[3]), .A2(n130), .B1(b_s1[7]), .B2(n88), 
        .ZN(n98) );
  OAI22D0P7BWP40P140 U187 ( .A1(n99), .A2(n89), .B1(n100), .B2(n98), .ZN(n105)
         );
  AOI22D0P7BWP40P140 U188 ( .A1(b_s1[5]), .A2(a_s1[5]), .B1(n109), .B2(n112), 
        .ZN(n97) );
  AOI22D0P7BWP40P140 U189 ( .A1(n111), .A2(n90), .B1(n97), .B2(n96), .ZN(n104)
         );
  AOI22D0P7BWP40P140 U190 ( .A1(b_s1[3]), .A2(a_s1[7]), .B1(n131), .B2(n91), 
        .ZN(n102) );
  MAOI22D0BWP40P140 U191 ( .A1(n114), .A2(n102), .B1(n134), .B2(n92), .ZN(n103) );
  FA1D0BWP40P140 U192 ( .A(n95), .B(n94), .CI(n93), .CO(\intadd_1/B[7] ), .S(
        \intadd_1/A[6] ) );
  INVD0P7BWP40P140 U193 ( .I(n105), .ZN(n117) );
  AOI22D0P7BWP40P140 U194 ( .A1(a_s1[5]), .A2(b_s1[6]), .B1(n121), .B2(n109), 
        .ZN(n110) );
  AOI22D0P7BWP40P140 U195 ( .A1(n111), .A2(n97), .B1(n110), .B2(n96), .ZN(n116) );
  AOI21D0P7BWP40P140 U196 ( .A1(n100), .A2(n99), .B(n98), .ZN(n115) );
  AOI22D0P7BWP40P140 U197 ( .A1(b_s1[4]), .A2(a_s1[7]), .B1(n131), .B2(n101), 
        .ZN(n113) );
  INVD0P7BWP40P140 U198 ( .I(n134), .ZN(n123) );
  AOI22D0P7BWP40P140 U199 ( .A1(n114), .A2(n113), .B1(n123), .B2(n102), .ZN(
        n107) );
  FA1D0BWP40P140 U200 ( .A(n105), .B(n104), .CI(n103), .CO(n106), .S(n93) );
  FA1D0BWP40P140 U201 ( .A(n108), .B(n107), .CI(n106), .CO(\intadd_1/A[8] ), 
        .S(\intadd_1/A[7] ) );
  AOI22D0P7BWP40P140 U202 ( .A1(a_s1[5]), .A2(n130), .B1(b_s1[7]), .B2(n109), 
        .ZN(n124) );
  MOAI22D0BWP40P140 U203 ( .A1(n126), .A2(n124), .B1(n111), .B2(n110), .ZN(
        n120) );
  AOI22D0P7BWP40P140 U204 ( .A1(b_s1[5]), .A2(a_s1[7]), .B1(n131), .B2(n112), 
        .ZN(n122) );
  AOI22D0P7BWP40P140 U205 ( .A1(n114), .A2(n122), .B1(n123), .B2(n113), .ZN(
        n119) );
  FA1D0BWP40P140 U206 ( .A(n117), .B(n116), .CI(n115), .CO(n118), .S(n108) );
  FA1D0BWP40P140 U207 ( .A(n120), .B(n119), .CI(n118), .CO(\intadd_1/B[9] ), 
        .S(\intadd_1/B[8] ) );
  INVD0P7BWP40P140 U208 ( .I(n120), .ZN(n129) );
  AOI22D0P7BWP40P140 U209 ( .A1(b_s1[6]), .A2(n131), .B1(a_s1[7]), .B2(n121), 
        .ZN(n132) );
  MAOI22D0BWP40P140 U210 ( .A1(n123), .A2(n122), .B1(n135), .B2(n132), .ZN(
        n128) );
  AOI21D0P7BWP40P140 U211 ( .A1(n126), .A2(n125), .B(n124), .ZN(n127) );
  FA1D0BWP40P140 U212 ( .A(n129), .B(n128), .CI(n127), .CO(\intadd_1/B[10] ), 
        .S(\intadd_1/A[9] ) );
  AOI22D0P7BWP40P140 U213 ( .A1(b_s1[7]), .A2(n131), .B1(a_s1[7]), .B2(n130), 
        .ZN(n133) );
  OAI22D0P7BWP40P140 U214 ( .A1(n135), .A2(n133), .B1(n134), .B2(n132), .ZN(
        \intadd_1/A[10] ) );
  INVD0P7BWP40P140 U215 ( .I(\intadd_1/A[10] ), .ZN(\intadd_1/A[11] ) );
  AOI21D0P7BWP40P140 U216 ( .A1(n135), .A2(n134), .B(n133), .ZN(
        \intadd_1/B[11] ) );
  AO22D0BWP40P140 U217 ( .A1(n138), .A2(\intadd_0/SUM[11] ), .B1(n136), .B2(
        prod_ext_s2[13]), .Z(N87) );
  AO22D0BWP40P140 U218 ( .A1(n138), .A2(\intadd_0/SUM[12] ), .B1(n136), .B2(
        prod_ext_s2[14]), .Z(N88) );
  ND2D0P7BWP40P140 U219 ( .A1(prod_ext_s2[15]), .A2(n136), .ZN(n211) );
  IOA21D0BWP40P140 U220 ( .A1(n138), .A2(n137), .B(n211), .ZN(N89) );
  NR2D0P7BWP40P140 U221 ( .A1(prod_ext_s2[15]), .A2(n139), .ZN(n209) );
  INVD0P7BWP40P140 U222 ( .I(prod_ext_s2[15]), .ZN(n202) );
  NR2D0P7BWP40P140 U223 ( .A1(n202), .A2(n139), .ZN(n210) );
  FA1D0BWP40P140 U224 ( .A(acc[15]), .B(prod_ext_s2[15]), .CI(\intadd_0/n1 ), 
        .CO(n143), .S(n137) );
  XNR2UD0BWP40P140 U225 ( .A1(acc[16]), .A2(n143), .ZN(n140) );
  MUX2ND0BWP40P140 U226 ( .I0(n209), .I1(n210), .S(n140), .ZN(n141) );
  ND2D0P7BWP40P140 U227 ( .A1(n141), .A2(n211), .ZN(N90) );
  AOI21D0P7BWP40P140 U228 ( .A1(\intadd_0/n1 ), .A2(acc[15]), .B(
        prod_ext_s2[15]), .ZN(n142) );
  INR2D1BWP40P140 U229 ( .A1(acc[16]), .B1(n142), .ZN(n146) );
  AOI21D0P7BWP40P140 U230 ( .A1(prod_ext_s2[15]), .A2(n143), .B(n146), .ZN(
        n147) );
  XNR2UD0BWP40P140 U231 ( .A1(acc[17]), .A2(n147), .ZN(n144) );
  MUX2ND0BWP40P140 U232 ( .I0(n210), .I1(n209), .S(n144), .ZN(n145) );
  ND2D0P7BWP40P140 U233 ( .A1(n145), .A2(n211), .ZN(N91) );
  INVD0P7BWP40P140 U234 ( .I(acc[18]), .ZN(n150) );
  OAI21D0P7BWP40P140 U235 ( .A1(prod_ext_s2[15]), .A2(n146), .B(acc[17]), .ZN(
        n151) );
  OAI21D0P7BWP40P140 U236 ( .A1(n147), .A2(n202), .B(n151), .ZN(n152) );
  XNR2UD0BWP40P140 U237 ( .A1(n150), .A2(n152), .ZN(n148) );
  MUX2ND0BWP40P140 U238 ( .I0(n210), .I1(n209), .S(n148), .ZN(n149) );
  ND2D0P7BWP40P140 U239 ( .A1(n149), .A2(n211), .ZN(N92) );
  AOI21D0P7BWP40P140 U240 ( .A1(n202), .A2(n151), .B(n150), .ZN(n155) );
  AOI21D0P7BWP40P140 U241 ( .A1(prod_ext_s2[15]), .A2(n152), .B(n155), .ZN(
        n156) );
  XNR2UD0BWP40P140 U242 ( .A1(acc[19]), .A2(n156), .ZN(n153) );
  MUX2ND0BWP40P140 U243 ( .I0(n210), .I1(n209), .S(n153), .ZN(n154) );
  ND2D0P7BWP40P140 U244 ( .A1(n154), .A2(n211), .ZN(N93) );
  INVD0P7BWP40P140 U245 ( .I(acc[20]), .ZN(n159) );
  OAI21D0P7BWP40P140 U246 ( .A1(prod_ext_s2[15]), .A2(n155), .B(acc[19]), .ZN(
        n160) );
  OAI21D0P7BWP40P140 U247 ( .A1(n156), .A2(n202), .B(n160), .ZN(n161) );
  XNR2UD0BWP40P140 U248 ( .A1(n159), .A2(n161), .ZN(n157) );
  MUX2ND0BWP40P140 U249 ( .I0(n210), .I1(n209), .S(n157), .ZN(n158) );
  ND2D0P7BWP40P140 U250 ( .A1(n158), .A2(n211), .ZN(N94) );
  AOI21D0P7BWP40P140 U251 ( .A1(n202), .A2(n160), .B(n159), .ZN(n164) );
  AOI21D0P7BWP40P140 U252 ( .A1(prod_ext_s2[15]), .A2(n161), .B(n164), .ZN(
        n165) );
  XNR2UD0BWP40P140 U253 ( .A1(acc[21]), .A2(n165), .ZN(n162) );
  MUX2ND0BWP40P140 U254 ( .I0(n210), .I1(n209), .S(n162), .ZN(n163) );
  ND2D0P7BWP40P140 U255 ( .A1(n163), .A2(n211), .ZN(N95) );
  INVD0P7BWP40P140 U256 ( .I(acc[22]), .ZN(n168) );
  OAI21D0P7BWP40P140 U257 ( .A1(prod_ext_s2[15]), .A2(n164), .B(acc[21]), .ZN(
        n169) );
  OAI21D0P7BWP40P140 U258 ( .A1(n165), .A2(n202), .B(n169), .ZN(n170) );
  XNR2UD0BWP40P140 U259 ( .A1(n168), .A2(n170), .ZN(n166) );
  MUX2ND0BWP40P140 U260 ( .I0(n210), .I1(n209), .S(n166), .ZN(n167) );
  ND2D0P7BWP40P140 U261 ( .A1(n167), .A2(n211), .ZN(N96) );
  AOI21D0P7BWP40P140 U262 ( .A1(n202), .A2(n169), .B(n168), .ZN(n173) );
  AOI21D0P7BWP40P140 U263 ( .A1(prod_ext_s2[15]), .A2(n170), .B(n173), .ZN(
        n174) );
  XNR2UD0BWP40P140 U264 ( .A1(acc[23]), .A2(n174), .ZN(n171) );
  MUX2ND0BWP40P140 U265 ( .I0(n210), .I1(n209), .S(n171), .ZN(n172) );
  ND2D0P7BWP40P140 U266 ( .A1(n172), .A2(n211), .ZN(N97) );
  INVD0P7BWP40P140 U267 ( .I(acc[24]), .ZN(n177) );
  OAI21D0P7BWP40P140 U268 ( .A1(prod_ext_s2[15]), .A2(n173), .B(acc[23]), .ZN(
        n178) );
  OAI21D0P7BWP40P140 U269 ( .A1(n174), .A2(n202), .B(n178), .ZN(n179) );
  XNR2UD0BWP40P140 U270 ( .A1(n177), .A2(n179), .ZN(n175) );
  MUX2ND0BWP40P140 U271 ( .I0(n210), .I1(n209), .S(n175), .ZN(n176) );
  ND2D0P7BWP40P140 U272 ( .A1(n176), .A2(n211), .ZN(N98) );
  AOI21D0P7BWP40P140 U273 ( .A1(n202), .A2(n178), .B(n177), .ZN(n182) );
  AOI21D0P7BWP40P140 U274 ( .A1(prod_ext_s2[15]), .A2(n179), .B(n182), .ZN(
        n183) );
  XNR2UD0BWP40P140 U275 ( .A1(acc[25]), .A2(n183), .ZN(n180) );
  MUX2ND0BWP40P140 U276 ( .I0(n210), .I1(n209), .S(n180), .ZN(n181) );
  ND2D0P7BWP40P140 U277 ( .A1(n181), .A2(n211), .ZN(N99) );
  INVD0P7BWP40P140 U278 ( .I(acc[26]), .ZN(n186) );
  OAI21D0P7BWP40P140 U279 ( .A1(prod_ext_s2[15]), .A2(n182), .B(acc[25]), .ZN(
        n187) );
  OAI21D0P7BWP40P140 U280 ( .A1(n183), .A2(n202), .B(n187), .ZN(n188) );
  XNR2UD0BWP40P140 U281 ( .A1(n186), .A2(n188), .ZN(n184) );
  MUX2ND0BWP40P140 U282 ( .I0(n210), .I1(n209), .S(n184), .ZN(n185) );
  ND2D0P7BWP40P140 U283 ( .A1(n185), .A2(n211), .ZN(N100) );
  AOI21D0P7BWP40P140 U284 ( .A1(n202), .A2(n187), .B(n186), .ZN(n191) );
  AOI21D0P7BWP40P140 U285 ( .A1(prod_ext_s2[15]), .A2(n188), .B(n191), .ZN(
        n192) );
  XNR2UD0BWP40P140 U286 ( .A1(acc[27]), .A2(n192), .ZN(n189) );
  MUX2ND0BWP40P140 U287 ( .I0(n210), .I1(n209), .S(n189), .ZN(n190) );
  ND2D0P7BWP40P140 U288 ( .A1(n190), .A2(n211), .ZN(N101) );
  INVD0P7BWP40P140 U289 ( .I(acc[28]), .ZN(n195) );
  OAI21D0P7BWP40P140 U290 ( .A1(prod_ext_s2[15]), .A2(n191), .B(acc[27]), .ZN(
        n196) );
  OAI21D0P7BWP40P140 U291 ( .A1(n192), .A2(n202), .B(n196), .ZN(n197) );
  XNR2UD0BWP40P140 U292 ( .A1(n195), .A2(n197), .ZN(n193) );
  MUX2ND0BWP40P140 U293 ( .I0(n210), .I1(n209), .S(n193), .ZN(n194) );
  ND2D0P7BWP40P140 U294 ( .A1(n194), .A2(n211), .ZN(N102) );
  AOI21D0P7BWP40P140 U295 ( .A1(n202), .A2(n196), .B(n195), .ZN(n200) );
  AOI21D0P7BWP40P140 U296 ( .A1(prod_ext_s2[15]), .A2(n197), .B(n200), .ZN(
        n203) );
  XNR2UD0BWP40P140 U297 ( .A1(acc[29]), .A2(n203), .ZN(n198) );
  MUX2ND0BWP40P140 U298 ( .I0(n210), .I1(n209), .S(n198), .ZN(n199) );
  ND2D0P7BWP40P140 U299 ( .A1(n199), .A2(n211), .ZN(N103) );
  OAI21D0P7BWP40P140 U300 ( .A1(prod_ext_s2[15]), .A2(n200), .B(acc[29]), .ZN(
        n201) );
  OAI21D0P7BWP40P140 U301 ( .A1(n203), .A2(n202), .B(n201), .ZN(n206) );
  XOR2UD0BWP40P140 U302 ( .A1(acc[30]), .A2(n206), .Z(n204) );
  MUX2ND0BWP40P140 U303 ( .I0(n210), .I1(n209), .S(n204), .ZN(n205) );
  ND2D0P7BWP40P140 U304 ( .A1(n205), .A2(n211), .ZN(N104) );
  MAOI222D0BWP40P140 U305 ( .A(prod_ext_s2[15]), .B(acc[30]), .C(n206), .ZN(
        n207) );
  XNR2UD0BWP40P140 U306 ( .A1(n207), .A2(acc[31]), .ZN(n208) );
  MUX2ND0BWP40P140 U307 ( .I0(n210), .I1(n209), .S(n208), .ZN(n212) );
  ND2D0P7BWP40P140 U308 ( .A1(n212), .A2(n211), .ZN(N105) );
  INVD0P7BWP40P140 U309 ( .I(prod_ext_s2[1]), .ZN(n213) );
  MAOI222D0BWP40P140 U310 ( .A(n215), .B(n214), .C(n213), .ZN(\intadd_0/CI )
         );
endmodule

