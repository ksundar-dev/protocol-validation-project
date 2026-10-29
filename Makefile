   SIM ?= icarus
   TOPLEVEL_LANG = verilog
   TOPLEVEL = counter
   MODULE = test_counter
   VERILOG_SOURCES = $(CURDIR)/rtl/counter.sv
   SIM_BUILD = sim_build_$(SIM)
   export PYTHONPATH := $(CURDIR)/tb:$(PYTHONPATH)

   ifeq ($(SIM),icarus)
     COMPILE_ARGS += -g2012
     VERILOG_SOURCES += $(CURDIR)/tb/dump.sv
     COMPILE_ARGS += -s dump
   endif

   ifeq ($(SIM),verilator)
     EXTRA_ARGS += --trace --trace-structs -Wno-fatal
   endif

   include $(shell cocotb-config --makefiles)/Makefile.sim