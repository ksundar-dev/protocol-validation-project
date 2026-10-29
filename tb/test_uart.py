import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge, Timer

CLK_NS = 10
CLKS_PER_BIT = 16
BIT_NS = CLK_NS * CLKS_PER_BIT  # 160 ns per UART bit


async def reset(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_NS, units="ns").start())
    dut.rst_n.value = 0
    dut.tx_valid.value = 0
    dut.tx_data.value = 0
    dut.rx_line.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)


async def drive_byte(dut, byte, stop_level=1):
    """Bit-bang one byte onto rx_line: start bit, 8 data bits LSB first, stop bit."""
    dut.rx_line.value = 0
    await Timer(BIT_NS, units="ns")
    for i in range(8):
        dut.rx_line.value = (byte >> i) & 1
        await Timer(BIT_NS, units="ns")
    dut.rx_line.value = stop_level
    await Timer(BIT_NS, units="ns")
    dut.rx_line.value = 1


async def collect_rx(dut, got, errs):
    """Background monitor: record every byte and every framing error the RX reports."""
    while True:
        await RisingEdge(dut.clk)
        if int(dut.rx_valid.value):
            got.append(int(dut.rx_data.value))
        if int(dut.rx_frame_err.value):
            errs.append(1)


async def read_tx_byte(dut):
    """Watch tx_line, wait for a start bit, sample each bit mid-bit, return the byte."""
    await FallingEdge(dut.tx_line)
    await Timer(BIT_NS // 2, units="ns")
    assert int(dut.tx_line.value) == 0, "start bit not low at mid-bit"
    value = 0
    for i in range(8):
        await Timer(BIT_NS, units="ns")
        value |= int(dut.tx_line.value) << i
    await Timer(BIT_NS, units="ns")
    assert int(dut.tx_line.value) == 1, "stop bit not high"
    return value


async def write_tx_byte(dut, byte):
    """Hand one byte to the TX block, waiting until it is ready."""
    while int(dut.tx_ready.value) == 0:
        await RisingEdge(dut.clk)
    dut.tx_data.value = byte
    dut.tx_valid.value = 1
    await RisingEdge(dut.clk)
    dut.tx_valid.value = 0


# RX tests :D

@cocotb.test()
async def test_rx_single_byte(dut):
    await reset(dut)
    got, errs = [], []
    cocotb.start_soon(collect_rx(dut, got, errs))
    await drive_byte(dut, 0xA5)
    await ClockCycles(dut.clk, 20)
    assert got == [0xA5]
    assert errs == []


@cocotb.test()
async def test_rx_all_256_values(dut):
    await reset(dut)
    got, errs = [], []
    cocotb.start_soon(collect_rx(dut, got, errs))
    for b in range(256):
        await drive_byte(dut, b)
    await ClockCycles(dut.clk, 20)
    assert got == list(range(256))
    assert errs == []


@cocotb.test()
async def test_rx_back_to_back_random(dut):
    await reset(dut)
    got, errs = [], []
    cocotb.start_soon(collect_rx(dut, got, errs))
    sent = [random.randrange(256) for _ in range(30)]
    for b in sent:
        await drive_byte(dut, b)
    await ClockCycles(dut.clk, 20)
    assert got == sent


@cocotb.test()
async def test_rx_framing_error_then_recovery(dut):
    await reset(dut)
    got, errs = [], []
    cocotb.start_soon(collect_rx(dut, got, errs))
    await drive_byte(dut, 0x42, stop_level=0)   # bad stop bit
    await Timer(2 * BIT_NS, units="ns")
    await drive_byte(dut, 0x99)                 # a good byte must still work
    await ClockCycles(dut.clk, 20)
    assert len(errs) == 1
    assert got == [0x99]


# TX tests :D

@cocotb.test()
async def test_tx_single_byte(dut):
    await reset(dut)
    mon = cocotb.start_soon(read_tx_byte(dut))
    await write_tx_byte(dut, 0xA5)
    assert await mon == 0xA5


@cocotb.test()
async def test_tx_known_patterns(dut):
    await reset(dut)
    for b in [0x00, 0xFF, 0x55, 0xAA, 0x01, 0x80, 0x7E]:
        mon = cocotb.start_soon(read_tx_byte(dut))
        await write_tx_byte(dut, b)
        got = await mon
        assert got == b, f"sent {b:#04x}, decoded {got:#04x}"


@cocotb.test()
async def test_tx_random_bytes(dut):
    await reset(dut)
    for _ in range(20):
        b = random.randrange(256)
        mon = cocotb.start_soon(read_tx_byte(dut))
        await write_tx_byte(dut, b)
        got = await mon
        assert got == b, f"sent {b:#04x}, decoded {got:#04x}"
