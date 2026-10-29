module dump;
    initial begin
        $dumpfile("waves_icarus.vcd");
        $dumpvars(0, counter);
    end
endmodule
