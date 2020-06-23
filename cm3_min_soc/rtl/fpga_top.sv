/**
 *  Top wrapper for FPGA. This is necessary as Verilator doesn't handle INOUT nets currently
 *
 *  Tiny Labs Inc
 *  2020
 **/

module fpga_top 
  #(
    parameter XILINX_ENC_CM3 = 0,
    parameter ROM_SZ = 16384,
    parameter RAM_SZ = 16384,
    parameter ROM_FILE = ""
    )(
      input  CLK_100M,
      input  RESET,
      // JTAG/SWD pins
      input  TCK_SWDCLK,
      input  TDI,
      inout  TMS_SWDIO,
      output TDO,
      // GPIO port
      inout wire   GPIO0
      );


   // Clocks and PLL
   logic     hclk;
   logic     pll_locked, pll_feedback;

   generate
      if (XILINX_ENC_CM3) begin : gen_pll
         
         // Full CM3 core can support HCLK=40MHz
         PLLE2_BASE #(
                      .BANDWIDTH ("OPTIMIZED"),
                      .CLKFBOUT_MULT (12),
                      .CLKOUT0_DIVIDE(30),    // 40MHz
                      .CLKFBOUT_PHASE(0.0),   // Phase offset in degrees of CLKFB, (-360-360)
                      .CLKIN1_PERIOD(10.0),   // 100MHz input clock
                      .CLKOUT0_DUTY_CYCLE(0.5),
                      .CLKOUT0_PHASE(0.0),
                      .DIVCLK_DIVIDE(1),    // Master division value , (1-56)
                      .REF_JITTER1(0.0),    // Reference input jitter in UI (0.000-0.999)
                      .STARTUP_WAIT("FALSE") // Delay DONE until PLL Locks, ("TRUE"/"FALSE")
                      ) u_pll (
                                  // Clock outputs: 1-bit (each) output
                                  .CLKOUT0(hclk),
                                  .CLKFBOUT(pll_feedback), // 1-bit output, feedback clock
                                  .LOCKED(pll_locked),
                                  .CLKIN1(CLK_100M),
                                  .PWRDWN(1'b0),
                                  .RST(1'b0),
                                  .CLKFBIN(pll_feedback)    // 1-bit input, feedback clock
                                  );
      end // block: gen_pll
      else begin : gen_pll

         // Obsfucated CM3 core can only support 30MHz HCLK
         PLLE2_BASE #(
                      .BANDWIDTH ("OPTIMIZED"),
                      .CLKFBOUT_MULT (12),
                      .CLKOUT0_DIVIDE(40),    // 50MHz
                      .CLKFBOUT_PHASE(0.0),   // Phase offset in degrees of CLKFB, (-360-360)
                      .CLKIN1_PERIOD(10.0),   // 100MHz input clock
                      .CLKOUT0_DUTY_CYCLE(0.5),
                      .CLKOUT0_PHASE(0.0),
                      .DIVCLK_DIVIDE(1),    // Master division value , (1-56)
                      .REF_JITTER1(0.0),    // Reference input jitter in UI (0.000-0.999)
                      .STARTUP_WAIT("FALSE") // Delay DONE until PLL Locks, ("TRUE"/"FALSE")
                      ) u_pll (
                                  // Clock outputs: 1-bit (each) output
                                  .CLKOUT0(hclk),
                                  .CLKFBOUT(pll_feedback), // 1-bit output, feedback clock
                                  .LOCKED(pll_locked),
                                  .CLKIN1(CLK_100M),
                                  .PWRDWN(1'b0),
                                  .RST(1'b0),
                                  .CLKFBIN(pll_feedback)    // 1-bit input, feedback clock
                                  );

      end
   endgenerate

   // Generate reset logic from pushbutton/pll
   logic               poreset_n;
   logic [7:0]         reset_ctr;
   always @(posedge hclk)
     begin
        if (RESET | !pll_locked)
          reset_ctr <= 'hff;
        else if (reset_ctr)
          reset_ctr = reset_ctr - 1;
     end
   assign poreset_n = reset_ctr ? 1'b0 : 1'b1;
   
   // Inferred BUFIO on SWDIO
   logic               swdoe, swdout;
   assign TMS_SWDIO = swdoe ? swdout : 1'bz;

   // Inferred BUFIO  for gpio
   logic [7:0]         gpio_i, gpio_o, gpio_oe;
   assign GPIO0 = gpio_oe[0] ? gpio_o[0] : 1'bz;
   assign gpio_i = {7'h0, GPIO0};

   // Instantiate soc
   cm3_min_soc
     #(
       .XILINX_ENC_CM3  (XILINX_ENC_CM3),
       .ROM_SZ          (ROM_SZ),
       .RAM_SZ          (RAM_SZ),
       .ROM_FILE        (ROM_FILE)
       )
   u_soc (
          .CLK        (hclk),
          .PORESETn   (poreset_n),
          .TCK_SWDCLK (TCK_SWDCLK),
          .TDI        (TDI),
          .TMS_SWDIN  (TMS_SWDIO),
          .TDO        (TDO),
          .SWDOUT     (swdout),
          .SWDOUTEN   (swdoe),
          .GPIO_O     (gpio_o),
          .GPIO_I     (gpio_i),
          .GPIO_OE    (gpio_oe)
          );
   
endmodule // fpga_top
