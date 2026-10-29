import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


async def tick(dut):
    """Wait one clock edge, then 1 ns for registered outputs to settle"""
    await RisingEdge(dut.clk)
    await Timer(1, units="ns")


async def start_and_reset(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.en.value = 0
    dut.rst_n.value = 0
    for _ in range(3):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await tick(dut)


@cocotb.test()
async def test_reset_value(dut):
    await start_and_reset(dut)
    assert int(dut.count.value) == 0


@cocotb.test()
async def test_counts_up(dut):
    await start_and_reset(dut)
    dut.en.value = 1
    expected = 0
    for _ in range(20):
        await tick(dut)
        expected = (expected + 1) % 256
        assert int(dut.count.value) == expected


@cocotb.test()
async def test_hold_when_disabled(dut):
    await start_and_reset(dut)
    dut.en.value = 1
    for _ in range(5):
        await tick(dut)
    dut.en.value = 0
    await tick(dut)
    held = int(dut.count.value)
    for _ in range(5):
        await tick(dut)
        assert int(dut.count.value) == held


@cocotb.test()
async def test_wraparound(dut):
    await start_and_reset(dut)
    dut.en.value = 1
    expected = 0
    for _ in range(300):
        await tick(dut)
        expected = (expected + 1) % 256
        assert int(dut.count.value) == expected


@cocotb.test()
async def test_reset_midway(dut):
    await start_and_reset(dut)
    dut.en.value = 1
    for _ in range(10):
        await tick(dut)
    dut.rst_n.value = 0
    await tick(dut)
    assert int(dut.count.value) == 0
