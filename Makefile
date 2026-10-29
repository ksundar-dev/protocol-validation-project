SIM ?= icarus
DESIGN ?= counter
TOPLEVEL_LANG = verilog
SIM_BUILD = sim_build_$(DESIGN)_$(SIM)
export PYTHONPATH := $(CURDIR)/tb:$(CURDIR)/host:$(PYTHONPATH)

ifeq ($(DESIGN),counter)
TOPLEVEL = counter
MODULE = test_counter
VERILOG_SOURCES = $(CURDIR)/rtl/counter.sv
endif

ifeq ($(DESIGN),uart)
TOPLEVEL = uart_tb_top
MODULE = test_uart
VERILOG_SOURCES = $(CURDIR)/rtl/uart_tx.sv $(CURDIR)/rtl/uart_rx.sv $(CURDIR)/tb/uart_tb_top.sv
endif

ifeq ($(SIM),icarus)
COMPILE_ARGS += -g2012 -DICARUS_DUMP
ifeq ($(DESIGN),counter)
VERILOG_SOURCES += $(CURDIR)/tb/dump.sv
COMPILE_ARGS += -s dump
endif
endif

ifeq ($(SIM),verilator)
EXTRA_ARGS += --trace --trace-structs -Wno-fatal
endif

include $(shell cocotb-config --makefiles)/Makefile.sim
