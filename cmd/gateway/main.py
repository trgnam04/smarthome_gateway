import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from internal.models import Protocol, DeviceProfile
from internal.devices import DeviceManager
from internal.router import MappingEngine, EventBroker
from internal.hal import GatewaySerialPort


all_profiles = {
        "rs485_niren_4_btn_v1": DeviceProfile.from_json_file("configs/profiles/profile_rs485_niren_4_button_panel.json"),        
        "rs485_relay_24_ch_v1": DeviceProfile.from_json_file("configs/profiles/profile_rs485_corx_relay_24_channel.json")
    }

    # 2. Khởi tạo Manager và nạp JSON
dev_mgr = DeviceManager()
dev_mgr.load_from_json_file("configs/devices/devices_scene2.json", all_profiles)

mapping_engine = MappingEngine()
mapping_engine.load_from_json_file("configs/mappings/mapping_scene2.json")

broker = EventBroker(dev_mgr, mapping_engine)

# Khởi tạo HAL (Giao tiếp phần cứng)
gateway_port = GatewaySerialPort(port="/dev/ttyUSB0", baudrate=9600)

# 1. Liên kết luồng GỬI: Broker -> HAL
broker.bind_hardware_tx(gateway_port.send)

# 2. Liên kết luồng NHẬN: HAL -> Broker
gateway_port.bind_rx_callback(broker.process_incoming_raw)

# Khởi động lắng nghe Serial (Chạy ngầm)
gateway_port.start()

# Giữ main thread sống
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    gateway_port.stop()