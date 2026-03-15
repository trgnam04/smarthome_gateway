# internal/models/routing.py
from dataclasses import dataclass
from .enums import Intent

@dataclass
class TriggerDef:
    source_device: str
    event_name: str

@dataclass
class ActionDef:
    target_device: str
    target_endpoint: str
    intent: Intent

@dataclass
class MappingRule:
    rule_id: str
    trigger: TriggerDef
    action: ActionDef