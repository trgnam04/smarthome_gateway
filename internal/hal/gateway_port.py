# internal/hal/gateway_port.py

import serial
import threading
import time
from typing import Callable, Optional
from internal.models import Protocol
from .checksums import ChecksumUtils

class GatewaySerialPort:
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.is_running = False
        self.rx_callback: Optional[Callable[[Protocol, str], None]] = None

    def bind_rx_callback(self, callback: Callable[[Protocol, str], None]):
        """Đăng ký hàm callback để ném dữ liệu sạch lên EventBroker"""
        self.rx_callback = callback

    def start(self):
        """Mở cổng Serial và chạy Thread lắng nghe"""
        try:
            # Timeout = 0.05s (50ms) giúp gom đủ 1 frame Modbus/KNX (khoảng thời gian nghỉ giữa các frame)
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.05)
            self.is_running = True
            
            # Khởi chạy luồng đọc dữ liệu nền
            rx_thread = threading.Thread(target=self._read_loop, daemon=True)
            rx_thread.start()
            print(f"[HAL] Đã mở cổng {self.port} thành công. Đang lắng nghe...")
        except serial.SerialException as e:
            print(f"[HAL] LỖI: Không thể mở cổng {self.port}. Chi tiết: {e}")

    def stop(self):
        self.is_running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    # =======================================================
    # LUỒNG NHẬN DỮ LIỆU (RX FLOW)
    # =======================================================
    def _read_loop(self):
        """Vòng lặp gom frame từ đường truyền vật lý"""
        while self.is_running:
            if self.serial_conn and self.serial_conn.in_waiting > 0:
                # Đọc toàn bộ buffer có sẵn (Đã được gom nhờ timeout của pyserial)
                raw_bytes = self.serial_conn.read(self.serial_conn.in_waiting)
                if not raw_bytes:
                    continue
                
                # 1. PHÂN LOẠI GÓI TIN (Hàm do bạn tự hiện thực)
                protocol = self._detect_protocol(raw_bytes)
                
                # 2. XỬ LÝ THEO GIAO THỨC
                if protocol == Protocol.KNX:
                    self._process_knx_rx(raw_bytes)
                elif protocol == Protocol.RS485:
                    self._process_rs485_rx(raw_bytes)
                else:
                    print(f"[HAL] Gói tin không xác định, bỏ qua: {raw_bytes.hex(' ')}")
            
            time.sleep(0.01) # Tránh ăn 100% CPU

    def _detect_protocol(self, frame: bytes) -> Optional[Protocol]:
        """
        [TODO]: BẠN SẼ HIỆN THỰC LOGIC PHÂN BIỆT GÓI TIN TẠI ĐÂY.
        Ví dụ: Kiểm tra byte đầu tiên (Message Code của KNX) hoặc cấu trúc frame.
        Trả về Protocol.KNX, Protocol.RS485, hoặc None nếu frame rác.
        """
        # --- Khai báo method theo yêu cầu, nội dung bạn tự viết ---
        return "rs485"

    def _process_knx_rx(self, frame: bytes):
        """Kiểm tra Check Byte KNX, bóc tách và đẩy lên Router"""
        if len(frame) < 2: return
        
        payload = frame[:-1]
        received_check_byte = frame[-1:]
        calculated_check_byte = ChecksumUtils.calc_knx_check_byte(payload)
        
        if received_check_byte == calculated_check_byte:
            hex_str = payload.hex(" ").upper()
            if self.rx_callback:
                self.rx_callback(Protocol.KNX, hex_str)
        else:
            print("[HAL] Lỗi Checksum KNX! Gói tin bị drop.")

    def _process_rs485_rx(self, frame: bytes):
        """Kiểm tra CRC Modbus, bóc tách và đẩy lên Router"""
        if len(frame) < 4: return
        
        payload = frame[:-2]
        received_crc = frame[-2:]
        calculated_crc = ChecksumUtils.calc_modbus_crc16(payload)
        
        if received_crc == calculated_crc:
            hex_str = payload.hex(" ").upper()
            if self.rx_callback:
                self.rx_callback(Protocol.RS485, hex_str)
        else:
            print("[HAL] Lỗi CRC RS485! Gói tin bị drop.")

    # =======================================================
    # LUỒNG GỬI DỮ LIỆU (TX FLOW)
    # =======================================================
    def send(self, protocol: Protocol, raw_hex: str):
        """
        Hàm được EventBroker gọi để truyền dữ liệu xuống.
        Sẽ đóng gói thêm CRC/CheckByte tùy theo giao thức.
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("[HAL] Lỗi: Cổng Serial chưa mở!")
            return

        try:
            # Chuyển chuỗi Hex sạch (VD: "01 03 00 02 02 02") thành Bytes
            payload_bytes = bytes.fromhex(raw_hex)
            
            # Đóng gói thêm Checksum/CRC
            if protocol == Protocol.KNX:
                check_byte = ChecksumUtils.calc_knx_check_byte(payload_bytes)
                frame_to_send = payload_bytes + check_byte
            elif protocol == Protocol.RS485:
                crc_bytes = ChecksumUtils.calc_modbus_crc16(payload_bytes)
                frame_to_send = payload_bytes + crc_bytes
            else:
                return

            # Gửi ra đường bus vật lý
            self.serial_conn.write(frame_to_send)
            # print(f"[HAL] TX ({protocol.name}): {frame_to_send.hex(' ').upper()}")

        except ValueError as e:
            print(f"[HAL] Lỗi parse chuỗi Hex: {e}")