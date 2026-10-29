"""labctl: host library for the Protocol Validation Lab. See docs/protocol.md."""

SOF = 0x7E

CMD_REG_WR = 0x01
CMD_REG_RD = 0x02
CMD_I2C_XFER = 0x10
CMD_SPI_XFER = 0x20
CMD_ETH_TX = 0x30
CMD_ETH_RX = 0x31
RESP_FLAG = 0x80

STATUS_OK = 0x00
STATUS_BAD_CMD = 0x02
STATUS_BAD_LEN = 0x03


class FrameError(Exception):
    """Raised when a received frame is malformed."""


def crc16(data: bytes, init: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no final XOR."""
    crc = init
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def build_frame(cmd: int, payload: bytes = b"") -> bytes:
    """Return SOF | CMD | LEN | PAYLOAD | CRC16(hi, lo)."""
    payload = bytes(payload)
    if len(payload) > 255:
        raise ValueError("payload longer than 255 bytes")
    body = bytes([cmd, len(payload)]) + payload
    return bytes([SOF]) + body + crc16(body).to_bytes(2, "big")


def parse_frame(data: bytes):
    """Validate a complete frame and return (cmd, payload). Raises FrameError."""
    data = bytes(data)
    if len(data) < 5:
        raise FrameError("frame too short")
    if data[0] != SOF:
        raise FrameError("bad SOF")
    length = data[2]
    if len(data) != 5 + length:
        raise FrameError("length mismatch")
    expected = crc16(data[1:-2])
    received = int.from_bytes(data[-2:], "big")
    if expected != received:
        raise FrameError(f"bad CRC: expected {expected:#06x}, got {received:#06x}")
    return data[1], data[3:3 + length]
