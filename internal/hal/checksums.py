# internal/hal/checksums.py

class ChecksumUtils:
    @staticmethod
    def calc_knx_check_byte(data: bytes) -> bytes:
        """
        Tính toán Check Byte cho gói tin KNX (Thường là XOR của tất cả các byte)
        """
        chk = 0x00
        for b in data:
            chk ^= b
        return bytes([chk])

    @staticmethod
    def calc_modbus_crc16(data: bytes) -> bytes:
        """
        Tính toán 2 byte CRC-16 theo chuẩn Modbus RTU.
        Trả về 2 byte theo thứ tự Little-Endian (Byte thấp trước, Byte cao sau).
        """
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for _ in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return bytes([crc & 0xFF, (crc >> 8) & 0xFF])