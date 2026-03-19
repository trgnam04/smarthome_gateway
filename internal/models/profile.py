# internal/models/profile.py
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .enums import Protocol

@dataclass
class SemanticData:
    """Định nghĩa ngữ nghĩa của một lệnh KNX/RS485
        - KNX:
            + apci: GroupValueWrite/Read/Response
            + value: maybe theo DPT
        - RS485:
            + apci: raw
            + value: byte string
    """
    apci: str    # VD: "GroupValueWrite"
    value: Any   # VD: 1, 0, hoặc giá trị %

@dataclass
class InterfaceType:
    """Lớp định nghĩa tính năng (Ví dụ: logic của Relay 1-bit)"""
    dpt: str
    data_length: int
    control: Dict[str, SemanticData] = field(default_factory=dict)
    controlled: Dict[str, SemanticData] = field(default_factory=dict)

    base_frame: Optional[str] = None
    bit_index: Optional[int] = None

@dataclass
class EndpointDef:
    """Định nghĩa một kênh vật lý trên thiết bị"""
    name: str
    type: str  # Tham chiếu đến key trong InterfaceType

@dataclass
class DeviceProfile:
    """Bản thiết kế tĩnh của một thiết bị vật lý"""
    profile_id: str
    protocol: Protocol
    device_type: str
    description: Optional[str] = None # Bổ sung thêm trường này vì file JSON thường có
    interface_types: Dict[str, InterfaceType] = field(default_factory=dict)
    endpoints: Dict[str, EndpointDef] = field(default_factory=dict)

    @classmethod
    @classmethod
    def from_dict(cls, data: dict) -> "DeviceProfile":
        """
        Factory Method: Khởi tạo DeviceProfile từ một Dictionary.
        Phân tách bóc tách (parsing) các lớp dữ liệu lồng nhau.
        """
        # 1. Ép kiểu Protocol Enum
        protocol = Protocol(data["protocol"])

        # 2. Bóc tách Interface Types
        interface_types = {}
        for it_key, it_val in data.get("interface_types", {}).items():
            
            # Xử lý control mapping (Chỉ parse nếu v là kiểu dict)
            control = {}
            for k, v in it_val.get("control", {}).items():
                if isinstance(v, dict):
                    control[k] = SemanticData(**v)
                    
            # Xử lý controlled mapping (SỬA LỖI TẠI ĐÂY: Chỉ parse nếu v là kiểu dict)
            controlled = {}
            for k, v in it_val.get("controlled", {}).items():
                if isinstance(v, dict):
                    controlled[k] = SemanticData(**v)
            
            # Lấy base_frame và bit_index 
            # (Hỗ trợ cả trường hợp nằm ngoài, hoặc lỡ viết nhầm bên trong controlled)
            base_frame = it_val.get("base_frame") or it_val.get("controlled", {}).get("base_frame")
            
            bit_index = it_val.get("bit_index")
            if bit_index is None: # Phải dùng None vì bit_index có thể có giá trị 0
                bit_index = it_val.get("controlled", {}).get("bit_index")
            
            interface_types[it_key] = InterfaceType(
                dpt=it_val.get("dpt", ""),
                data_length=it_val.get("data_length", 0),
                control=control,
                controlled=controlled,
                base_frame=base_frame,
                bit_index=bit_index
            )

        # 3. Bóc tách Endpoints
        endpoints = {
            ep_key: EndpointDef(**ep_val) 
            for ep_key, ep_val in data.get("endpoints", {}).items()
        }

        # 4. Trả về đối tượng DeviceProfile hoàn chỉnh
        return cls(
            profile_id=data["profile_id"],
            protocol=protocol,
            device_type=data["device_type"],
            description=data.get("description"),
            interface_types=interface_types,
            endpoints=endpoints
        )

    @classmethod
    def from_json_file(cls, filepath: str) -> "DeviceProfile":
        """Factory Method: Đọc file JSON và khởi tạo object"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)