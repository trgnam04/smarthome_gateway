# internal/devices/knx_utils.py

from dataclasses import dataclass
from typing import Any, Optional, Dict
from ..models import SemanticData

class KNXUtils:
    @staticmethod
    def _parse_individual_address(addr: str) -> str:
        """Chuyển đổi địa chỉ vật lý (VD: '1.1.250') sang Hex"""
        area, line, device = map(int, addr.split('.'))
        high_byte = (area << 4) | line
        low_byte = device
        return f"{high_byte:02X} {low_byte:02X}"

    @staticmethod
    def _parse_group_address(ga: str) -> str:
        """Chuyển đổi Group Address (VD: '2/1/2') sang Hex"""
        main, middle, sub = map(int, ga.split('/'))
        high_byte = (main << 3) | middle
        low_byte = sub
        return f"{high_byte:02X} {low_byte:02X}"

    @staticmethod
    def build_cemi_frame(src_addr: str, dst_ga: str, semantic: SemanticData, data_length: int) -> str:
        """Đóng gói Frame cEMI chiều đi (Gateway -> KNX)"""
        msg_code = "11" # L_Data.req
        add_info = "00"
        cf1 = "BC"
        cf2 = "E0" # Bit 7 = 1 (Target là Group Address)
        
        src_hex = KNXUtils._parse_individual_address(src_addr)
        dst_hex = KNXUtils._parse_group_address(dst_ga)
        len_hex = f"{data_length:02X}"
        
        apdu_hex = ""
        # 0x80 là GroupValueWrite cơ bản. Cộng thêm value (0 hoặc 1) cho DPT 1.xxx
        if semantic.apci == "GroupValueWrite" and data_length == 1:
            apdu_val = 0x80 + int(semantic.value)
            apdu_hex = f"{apdu_val:02X}"
            
        return f"{msg_code} {add_info} {cf1} {cf2} {src_hex} {dst_hex} {len_hex} {apdu_hex}"

    @staticmethod
    def parse_cemi_frame(raw_hex: str) -> Optional[Dict[str, Any]]:
        """Giải mã Frame cEMI chiều về (KNX -> Gateway)"""
        parts = raw_hex.strip().split(" ")
        if len(parts) < 8:
            return None
        
        msg_code = parts[0]
        if msg_code != "29": # L_Data.ind
            return None
            
        # Tính toán lại Group Address từ 2 byte Hex
        dst_hex_1, dst_hex_2 = int(parts[6], 16), int(parts[7], 16)
        main = (dst_hex_1 & 0xF8) >> 3
        middle = dst_hex_1 & 0x07
        sub = dst_hex_2
        dst_ga = f"{main}/{middle}/{sub}"
        
        # Bóc tách APDU để lấy Value và APCI
        apdu = int(parts[9], 16) if len(parts) > 9 else int(parts[-1], 16)
        value = apdu & 0x3F # 6 bit thấp
        apci_val = (apdu & 0x3C0) >> 6 # 4 bit APCI
        apci_str = "GroupValueWrite" if apci_val == 2 else "Unknown"
        
        return {
            "target_ga": dst_ga,
            "semantic": SemanticData(apci=apci_str, value=value)
        }