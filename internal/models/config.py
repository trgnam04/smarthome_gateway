# internal/models/config.py
from dataclasses import dataclass, field
from typing import Dict, Optional, Any

@dataclass
class EndpointConfig:
    """Cấu hình GA của người dùng cho từng kênh"""
    command_ga: Optional[str] = None
    status_ga: Optional[str] = None

@dataclass
class DeviceConfig:
    """Cấu hình khởi tạo thiết bị do user tạo ra"""
    system_id: str
    profile_id: str
    common_params: Dict[str, Any]
    endpoints: Dict[str, EndpointConfig] = field(default_factory=dict)
    name: Optional[str] = None # Thêm trường Name để hiển thị UI

    @classmethod
    def from_dict(cls, system_id: str, data: dict) -> "DeviceConfig":
        """Factory Method: Khởi tạo DeviceConfig từ dữ liệu JSON bóc tách"""
        
        # Bóc tách cấu hình của từng Endpoint
        endpoints_config = {}
        for ep_name, ep_data in data.get("endpoints", {}).items():
            endpoints_config[ep_name] = EndpointConfig(
                command_ga=ep_data.get("command_ga"),
                status_ga=ep_data.get("status_ga")
            )

        return cls(
            system_id=system_id,
            profile_id=data.get("profile_id", ""),
            common_params=data.get("common_params", {}),
            endpoints=endpoints_config,
            name=data.get("name")
        )