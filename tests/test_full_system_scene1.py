# tests/test_full_system_json.py

import pytest
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from internal.models import Protocol, DeviceProfile
from internal.devices import DeviceManager
from internal.router import MappingEngine, EventBroker

# =====================================================================
# KỊCH BẢN KIỂM THỬ TÍCH HỢP (INTEGRATION TEST)
# =====================================================================

def test_full_system_integration():
    """Kiểm thử luồng hoạt động toàn hệ thống thông qua cấu hình JSON"""
    
    # Sử dụng thư mục tạm để ghi các file cấu hình ra ổ cứng ảo          
    # 1. Nạp Profile từ dữ liệu tĩnh
    all_profiles = {
        "rs485_niren_4_btn_v1": DeviceProfile.from_json_file("configs/profiles/profile_rs485_niren_4_button_panel.json"),
        "hager_txa_4_fold_relay": DeviceProfile.from_json_file("configs/profiles/profile_knx_hager_relay_10_channel.json")
    }

    # 2. Khởi tạo Manager và nạp JSON
    dev_mgr = DeviceManager()
    dev_mgr.load_from_json_file("configs/devices/devices_scene1.json", all_profiles)
    
    mapping_engine = MappingEngine()
    mapping_engine.load_from_json_file("configs/mappings/mapping_scene1.json")
    
    # 3. Khởi tạo Broker và kết nối Hardware ảo
    broker = EventBroker(dev_mgr, mapping_engine)
    hardware_output_log = []
    broker.bind_hardware_tx(lambda p, h: hardware_output_log.append((p, h)))

    # -----------------------------------------------------------------
    # KỊCH BẢN A: Người dùng nhấn Nút số 1 trên Panel số 1
    # -----------------------------------------------------------------
    # Tín hiệu vật lý: Device ID = 01, Lệnh = 03 00 02 02 02
    broker.process_incoming_raw(Protocol.RS485, "01 03 00 02 02 02")
    
    # Kiểm tra hệ thống xuất lệnh KNX:
    assert len(hardware_output_log) == 1, "Hệ thống phải xuất ra đúng 1 lệnh điều khiển."
    protocol, sent_hex = hardware_output_log.pop(0)
    
    # Theo mapping, panel_1:btn_1 điều khiển relay_10_ch:ch_1
    # KNX ch_1 được cấu hình Command GA là '2/1/1' (Hex: 11 01)
    # Message Code = 11 (L_Data.req)
    # APDU = 81 (GroupValueWrite = 0x80 + Value 1)
    assert protocol == Protocol.KNX
    assert sent_hex == "11 00 BC E0 11 FA 11 01 01 81"

    # -----------------------------------------------------------------
    # KỊCH BẢN B: Rơ-le KNX Kênh số 5 báo trạng thái ON lên Bus
    # -----------------------------------------------------------------
    # KNX ch_5 có Status GA là '2/2/5' (Hex: 12 05)
    # Giả lập rơ-le thực tế (địa chỉ vật lý 1.1.10 = 11 0A) bắn status ON (81) lên mạng
    broker.process_incoming_raw(Protocol.KNX, "29 00 BC E0 11 0A 12 05 01 81")
    
    # Kiểm tra hệ thống xuất lệnh RS485:
    # Theo mapping, ch_5 báo status ON sẽ kích hoạt turn_on đèn nền của panel_2:btn_1
    # Panel 2 có ID = 02. Đèn nền btn_1 ON = 05 00 00 FF 00
    assert len(hardware_output_log) == 1
    protocol, sent_hex = hardware_output_log.pop(0)
    
    assert protocol == Protocol.RS485
    assert sent_hex == "02 05 00 00 FF 00"

    # -----------------------------------------------------------------
    # KỊCH BẢN C: Rơ-le KNX Kênh số 10 báo trạng thái OFF lên Bus
    # -----------------------------------------------------------------
    # KNX ch_10 có Status GA là '2/2/10' (Hex: 12 0A)
    # Giả lập rơ-le bắn status OFF (80)
    broker.process_incoming_raw(Protocol.KNX, "29 00 BC E0 11 0A 12 0A 01 80")
    
    # Kiểm tra hệ thống xuất lệnh RS485 tắt đèn:
    # ch_10 map với panel_3:btn_2.
    # Panel 3 có ID = 03. Đèn nền btn_2 OFF = 05 00 01 00 00
    assert len(hardware_output_log) == 1
    protocol, sent_hex = hardware_output_log.pop(0)
    
    assert protocol == Protocol.RS485
    assert sent_hex == "03 05 00 01 00 00"

if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])