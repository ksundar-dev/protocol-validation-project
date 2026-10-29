# Lab Protocol v0.1

## 1. Physical link
UART, 8N1: 1 start bit, 8 data bits (LSB first), 1 stop bit, no parity. The line idles high.
In simulation the baud rate is the clock divided by CLKS_PER_BIT = 16.

## 2. Frame format

| Field   | Size       | Notes                         |
|---------|------------|-------------------------------|
| SOF     | 1 byte     | always 0x7E                   |
| CMD     | 1 byte     | see section 3                 |
| LEN     | 1 byte     | payload length, 0 to 255      |
| PAYLOAD | LEN bytes  | command specific              |
| CRC16   | 2 bytes    | high byte first               |

CRC: CRC-16/CCITT-FALSE, computed over CMD, LEN and PAYLOAD (SOF is not included).
Polynomial 0x1021, init 0xFFFF, no bit reflection, final XOR 0x0000.
Check value: crc16("123456789") = 0x29B1.
Running the CRC over CMD, LEN, PAYLOAD plus the two CRC bytes gives 0x0000.

## 3. Commands (host to DUT)

| CMD  | Name     | Payload                       |
|------|----------|-------------------------------|
| 0x01 | REG_WR   | addr (1 byte), data (4 bytes, big-endian) |
| 0x02 | REG_RD   | addr (1 byte)                 |
| 0x10 | I2C_XFER | defined in Phase 3            |
| 0x20 | SPI_XFER | defined in Phase 4            |
| 0x30 | ETH_TX   | defined in Phase 5            |
| 0x31 | ETH_RX   | defined in Phase 5            |

## 4. Responses (DUT to host)
Response CMD = request CMD | 0x80. The first payload byte is a status code.
REG_RD response payload: status (1 byte), data (4 bytes, big-endian).

## 5. Status codes

| Code | Name    |
|------|---------|
| 0x00 | OK      |
| 0x02 | BAD_CMD |
| 0x03 | BAD_LEN |

## 6. DUT error handling
- Bad CRC: the frame is dropped silently and an error counter increments. No response is sent.
- Bytes received while idle that are not 0x7E are ignored.
- Unknown CMD with a good CRC: respond with status BAD_CMD.
- Inter-byte timeout: if too many clocks pass between bytes inside a frame, the parser abandons the frame and counts an error.
- The parser must always return to idle. It must never hang.
