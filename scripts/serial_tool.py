import serial
import threading
import curses
import time

# --- CẤU HÌNH ---
PORT = '/dev/ttyUSB1'  # Thay đổi cổng của bạn ở đây
BAUDRATE = 9600
AUTO_BREAK_TIME = 0.05  # Thời gian nghỉ sau mỗi lần gửi (giây)

class HexSerialTool:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        self.ser = None
        
        # Thiết lập màu sắc
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) # Nhận
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Gửi
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)   # Lỗi

        # Khởi tạo cửa sổ
        self.height, self.width = stdscr.getmaxyx()
        self.output_win = curses.newwin(self.height - 3, self.width, 0, 0)
        self.output_win.scrollok(True)
        
        self.input_win = curses.newwin(3, self.width, self.height - 3, 0)
        self.input_win.box()
        self.input_win.addstr(0, 2, "[ Nhập dữ liệu HEX và nhấn ENTER ]")

        try:
            self.ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
            self.log(f"Đã kết nối {PORT} tại {BAUDRATE} bps", 1)
        except Exception as e:
            self.log(f"Lỗi kết nối: {e}", 3)

        # Thread đọc dữ liệu
        self.rx_thread = threading.Thread(target=self.receive_data, daemon=True)
        self.rx_thread.start()

        self.main_loop()

    def log(self, message, color_pair=0):
        """Hiển thị dữ liệu lên màn hình chính"""
        self.output_win.addstr(f"{message}\n", curses.color_pair(color_pair))
        self.output_win.refresh()

    def receive_data(self):
        """Luồng nhận dữ liệu từ ttyUSB"""
        while self.running and self.ser:
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                # Chuyển sang định dạng HEX
                hex_data = " ".join(f"{b:02X}" for b in data)
                self.log(f"RX: {hex_data}", 1)
            time.sleep(0.01)

    def send_data(self, hex_str):
        """Chuyển chuỗi hex người dùng nhập sang bytes và gửi"""
        try:
            # 1. Loại bỏ khoảng trắng và các ký tự không phải hex
            clean_hex = "".join(c for c in hex_str if c in "0123456789abcdefABCDEF")
            
            # 2. Kiểm tra nếu độ dài chuỗi lẻ (thiếu nửa byte) thì báo lỗi
            if len(clean_hex) % 2 != 0:
                self.log("Lỗi: Chuỗi Hex phải có số ký tự chẵn (ví dụ: 0A thay vì A)", 3)
                return

            # 3. Chuyển đổi thành bytes (Ví dụ: "CD" -> 0xCD)
            byte_data = bytes.fromhex(clean_hex)
            
            # 4. Gửi dữ liệu xuống cổng ttyUSB
            self.ser.write(byte_data)
            
            # Hiển thị lại để xác nhận số lượng byte đã gửi
            self.log(f"TX ({len(byte_data)} bytes): {byte_data.hex(' ').upper()}", 2)
            
            # Auto Break Time (Nghỉ giữa các khung truyền)
            if AUTO_BREAK_TIME > 0:
                time.sleep(AUTO_BREAK_TIME)
                
        except Exception as e:
            self.log(f"Lỗi: {e}", 3)

    def main_loop(self):
        """Xử lý nhập liệu từ người dùng"""
        while self.running:
            self.input_win.clear()
            self.input_win.box()
            self.input_win.addstr(0, 2, f"[ Cổng: {PORT} | Định dạng: HEX ]")
            self.input_win.addstr(1, 1, "> ")
            self.input_win.refresh()

            # Nhập chuỗi từ bàn phím
            curses.echo()
            user_input = self.input_win.getstr(1, 3).decode('utf-8')
            curses.noecho()

            if user_input.lower() in ['exit', 'quit']:
                self.running = False
                break

            if user_input:
                self.send_data(user_input)

if __name__ == "__main__":
    try:
        curses.wrapper(HexSerialTool)
    except KeyboardInterrupt:
        pass