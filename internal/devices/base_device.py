# internal/devices/base_device.py

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from ..models import DeviceProfile, DeviceConfig, Event, Command
from .state_manager import EndpointStateManager

class Device(ABC):
    def __init__(self, config: DeviceConfig, profile: DeviceProfile):
        self.system_id = config.system_id
        self.config = config
        self.profile = profile
        # Trạng thái khởi tạo cho từng kênh được khai báo
        self.states: Dict[str, Any] = {ep: 0 for ep in config.endpoints.keys()}

        self.state_manager = EndpointStateManager(profile, config)

    @abstractmethod
    def process_incoming(self, raw_hex: str) -> List[Event]:
        pass

    @abstractmethod
    def execute_action(self, command: Command) -> Optional[str]:
        pass    