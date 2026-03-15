# internal/models/state.py
from dataclasses import dataclass, field
from typing import Any
import time

@dataclass
class EndpointState:
    """Đại diện cho trạng thái của một kênh vật lý tại một thời điểm"""
    value: Any = None
    last_updated: float = field(default_factory=time.time)
    
    def update(self, new_value: Any):
        self.value = new_value
        self.last_updated = time.time()