import random
import pytest
from labctl import FrameError, SOF, build_frame, crc16, parse_frame

def test_crc16_check_value():
    assert crc16(b"123456789") == 0x29B1

def test_crc16_residue_is_zero():
    data = bytes(range(20))
    assert crc16(data + crc16(data).to_bytes(2, "big")) == 0

def test_frame_layout():
    f = build_frame(0x02, b"\x10")
    assert f[0] == SOF
    assert f[1] == 0x02
    assert f[2] == 1
    assert f[3] == 0x10
    assert len(f) == 6
    assert int.from_bytes(f[-2:], "big") == crc16(f[1:-2])

@pytest.mark.parametrize("n", [0, 1, 5, 64, 255])
def test_roundtrip(n):
    rng = random.Random(n)
    payload = bytes(rng.randrange(256) for _ in range(n))
    cmd, got = parse_frame(build_frame(0x01, payload))
    assert cmd == 0x01
    assert got == payload

def test_every_single_bit_flip_is_rejected():
    f = build_frame(0x01, b"\x00\x00\x00\x00\x2A")
    for i in range(len(f)):
        for bit in range(8):
            bad = bytearray(f)
            bad[i] ^= 1 << bit
            with pytest.raises(FrameError):
                parse_frame(bytes(bad))

def test_truncated_frames_rejected():
    f = build_frame(0x01, b"\x01\x02\x03")
    for cut in range(len(f)):
        with pytest.raises(FrameError):
            parse_frame(f[:cut])

def test_trailing_garbage_rejected():
    with pytest.raises(FrameError):
        parse_frame(build_frame(0x02, b"\x00") + b"\x00")

def test_payload_too_long():
    with pytest.raises(ValueError):
        build_frame(0x01, bytes(256))
