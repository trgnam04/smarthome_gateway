# internal/models/runtime.py
from dataclasses import dataclass
from typing import Optional
from .enums import Intent

@dataclass
class Event:
    """Sự kiện sinh ra từ phần cứng"""
    source_device: str
    event_name: str
    raw_payload: Optional[str] = None

@dataclass
class Command:
    """Lệnh điều khiển truyền tới phần cứng"""
    target_device: str
    target_endpoint: str
    intent: Intent