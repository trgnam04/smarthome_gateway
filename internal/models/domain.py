from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

class Protocol(str, Enum):
    KNX = "knx"
    RS485 = "rs485"

class Intent(str, Enum):
    TURN_ON = "TURN_ON"
    TURN_OFF = "TURN_OFF"
    TOGGLE = "TOGGLE"

# --- MÔ HÌNH SEMANTIC DATA ---
@dataclass
class SemanticData:
    """Định nghĩa ngữ nghĩa của một lệnh (thay vì chuỗi Hex tĩnh)"""
    apci: str    # VD: "GroupValueWrite"
    value: Any   # VD: 1, 0, hoặc giá trị %

@dataclass
class InterfaceType:
    """Lớp định nghĩa tính năng (Ví dụ: logic của Relay 1-bit)"""
    dpt: str
    data_length: int
    control: Dict[str, SemanticData] = field(default_factory=dict)
    controlled: Dict[str, SemanticData] = field(default_factory=dict)

# --- MÔ HÌNH PROFILE & CONFIG ---
@dataclass
class EndpointDef:
    """Định nghĩa một kênh vật lý trên thiết bị"""
    name: str
    type: str # Tham chiếu đến key trong InterfaceType

@dataclass
class DeviceProfile:
    profile_id: str
    protocol: Protocol
    device_type: str
    interface_types: Dict[str, InterfaceType] = field(default_factory=dict)
    endpoints: Dict[str, EndpointDef] = field(default_factory=dict)

@dataclass
class EndpointConfig:
    """Cấu hình GA của người dùng cho từng kênh"""
    command_ga: Optional[str] = None
    status_ga: Optional[str] = None

@dataclass
class DeviceConfig:
    """ Cấu hình thiết bị riêng biệt trong một hệ thống
    - system_id, profile_id: sử dụng cho application, hỗ trợ việc hiển thị và log
    - common_params: chưa xác định rõ chức năng nhưng sẽ hỗ trợ nhiều cho thiết bị RS485
    - endpoints: hỗ trợ cấu hình cho các endpoint của thiết bị - cụ thể ở đây là KNX
    """
    system_id: str
    profile_id: str
    common_params: Dict[str, Any]
    endpoints: Dict[str, EndpointConfig] = field(default_factory=dict)

# --- MÔ HÌNH RUNTIME ---
@dataclass
class Event:
    source_device: str
    event_name: str
    raw_payload: Optional[str] = None

@dataclass
class Command:
    target_device: str
    target_endpoint: str
    intent: Intent