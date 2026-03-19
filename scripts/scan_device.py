import serial
import time

# Cấu hình kết nối - Thay đổi 'COM3' hoặc '/dev/ttyUSB0' cho phù hợp
PORT = '/dev/ttyUSB0' 
BAUDRATE = 9600
DEVICE_ID = 0x03

def calculate_crc(data):
    """Tính toán Modbus CRC16 [cite: 38, 249]"""
    crc = 0xFFFF
    for pos in data:
        crc ^= pos
        for i in range(8):
            if (crc & 1) != 0:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')

def scan_registers(start_addr, end_addr):
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.2)
        print(f"--- Bắt đầu scan từ {hex(start_addr)} đến {hex(end_addr)} ---")
        
        for addr in range(start_addr, end_addr + 1):
            # Tạo frame Read Holding Register (0x03), đọc 1 thanh ghi 
            addr_high = (addr >> 8) & 0xFF
            addr_low = addr & 0xFF
            msg = bytearray([DEVICE_ID, 0x03, addr_high, addr_low, 0x00, 0x01])
            msg += calculate_crc(msg)
            
            ser.write(msg)
            response = ser.read(10) # Đọc tối đa 10 byte phản hồi
            
            if len(response) >= 5:
                # Kiểm tra nếu là phản hồi lỗi (Function Code | 0x80)
                if response[1] == 0x83:
                    error_code = response[2]
                    if error_code == 0x02:
                        # Illegal Data Address 
                        pass 
                    else:
                        print(f"Addr {hex(addr)}: Lỗi Modbus {error_code}")
                else:
                    # Nếu không phải lỗi, đây là thanh ghi khả dụng
                    print(f"==> Addr {hex(addr)}: OK (Phản hồi: {response.hex().upper()})")
            
            time.sleep(0.05) # Giãn cách để tránh treo bus
            
        ser.close()
        print("--- Scan hoàn tất ---")
    except Exception as e:
        print(f"Lỗi kết nối: {e}")

# Quét dải địa chỉ phổ biến của panel 
# 0x1000 - 0x1040: Các thiết lập hệ thống và điều khiển
# 0x1310 - 0x1317: Trạng thái chi tiết phím bấm
scan_registers(0x1000, 0x1035)