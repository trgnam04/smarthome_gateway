# tests/test_knx_utils.py
import pytest
# Lưu ý: Pytest sẽ tự động tìm module trong internal/ nếu bạn chạy từ thư mục gốc
# nên chúng ta bỏ phần sys.path.insert rườm rà.

from internal.devices.knx_utils import KNXUtils
from internal.models import SemanticData

def test_parse_individual_address():
    """Kiểm tra hàm dịch địa chỉ vật lý (Individual Address)"""
    # Địa chỉ 1.1.250 -> 11 FA
    hex_addr = KNXUtils._parse_individual_address("1.1.250")
    assert hex_addr == "11 FA"

    # Địa chỉ 1.1.10 -> 11 0A
    hex_addr = KNXUtils._parse_individual_address("1.1.10")
    assert hex_addr == "11 0A"

def test_parse_group_address():
    """Kiểm tra hàm dịch địa chỉ logic (Group Address)"""
    # Địa chỉ 2/1/1 -> 11 01
    hex_ga = KNXUtils._parse_group_address("2/1/1")
    assert hex_ga == "11 01"

    # Địa chỉ 3/1/4 -> 19 04
    hex_ga = KNXUtils._parse_group_address("3/1/4")
    assert hex_ga == "19 04"

def test_build_cemi_frame_turn_on():
    """Kiểm tra đóng gói Frame Lệnh BẬT Rơ-le (Value = 1)"""
    semantic = SemanticData(apci="GroupValueWrite", value=1)
    
    # Gateway (1.1.250) gửi lệnh BẬT xuống kênh (2/1/1)
    frame = KNXUtils.build_cemi_frame(
        src_addr="1.1.250",
        dst_ga="2/1/1",
        semantic=semantic,
        data_length=1
    )
    # Expected: MessageCode CF1 CF2 SRC_HEX DST_HEX LEN APDU
    expected_frame = "11 00 BC E0 11 FA 11 01 01 81"
    assert frame == expected_frame

def test_build_cemi_frame_turn_off():
    """Kiểm tra đóng gói Frame Lệnh TẮT Rơ-le (Value = 0)"""
    semantic = SemanticData(apci="GroupValueWrite", value=0)
    
    frame = KNXUtils.build_cemi_frame(
        src_addr="1.1.250",
        dst_ga="2/1/1",
        semantic=semantic,
        data_length=1
    )
    expected_frame = "11 00 BC E0 11 FA 11 01 01 80"
    assert frame == expected_frame

def test_parse_cemi_frame_status_on():
    """Kiểm tra giải mã Frame KNX Phản hồi trạng thái BẬT"""
    # Gói tin từ Room Controller 1.1.10 báo trạng thái BẬT (0x81) vào GA 2/1/2
    raw_hex = "29 00 BC E0 11 0A 11 02 01 81"
    
    parsed = KNXUtils.parse_cemi_frame(raw_hex)
    assert parsed is not None
    assert parsed["target_ga"] == "2/1/2"
    assert parsed["semantic"].apci == "GroupValueWrite"
    assert parsed["semantic"].value == 1

def test_parse_cemi_frame_status_off():
    """Kiểm tra giải mã Frame KNX Phản hồi trạng thái TẮT"""
    # Gói tin từ Room Controller 1.1.10 báo trạng thái TẮT (0x80) vào GA 2/1/2
    raw_hex = "29 00 BC E0 11 0A 11 02 01 80"
    
    parsed = KNXUtils.parse_cemi_frame(raw_hex)
    assert parsed is not None
    assert parsed["target_ga"] == "2/1/2"
    assert parsed["semantic"].apci == "GroupValueWrite"
    assert parsed["semantic"].value == 0

def test_parse_cemi_frame_invalid():
    """Kiểm tra khả năng bắt lỗi với frame rác hoặc sai mã Message Code"""
    # Gói tin gửi đi (L_Data.req = 0x11) không phải là gói nhận (0x29)
    raw_hex_tx = "11 00 BC E0 11 FA 11 01 01 81"
    parsed = KNXUtils.parse_cemi_frame(raw_hex_tx)
    assert parsed is None

    # Gói tin rớt mạng, thiếu byte
    raw_hex_short = "29 00 BC"
    parsed_short = KNXUtils.parse_cemi_frame(raw_hex_short)
    assert parsed_short is None