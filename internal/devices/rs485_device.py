# internal/devices/rs485_device.py

from typing import List, Optional
# Sử dụng absolute import theo chuẩn project
from internal.models import Event, Command, Intent
from .base_device import Device

class RS485Device(Device):
    def process_incoming(self, raw_hex: str) -> List[Event]:
        events = []
        device_id = self.config.common_params.get("device_id", "")

        # 1. Quét qua từng kênh (endpoint) vật lý đã khai báo trong Profile
        for ep_name, ep_def in self.profile.endpoints.items():
            
            # 2. Tìm Type logic (ngữ nghĩa) của kênh này
            iface_type = self.profile.interface_types.get(ep_def.type)
            if not iface_type:
                continue
            
            # 3. Quét các sự kiện kích hoạt (control)
            for evt_name, semantic in iface_type.control.items():
                
                # Với RS485, value của SemanticData chứa chuỗi Hex tĩnh của thao tác
                # Ta ghép Device ID vào đầu chuỗi để so khớp
                expected_hex = f"{device_id} {semantic.value}"
                
                if expected_hex == raw_hex:
                    events.append(Event(
                        source_device=self.system_id,
                        event_name=f"{ep_name}:{evt_name}", # Định dạng chuẩn: "btn_1:pressed"
                        raw_payload=raw_hex
                    ))
        return events
    
    def execute_action(self, command: Command) -> Optional[str]:
        device_id = self.config.common_params.get("device_id", "")
        ep_name = command.target_endpoint
        
        ep_def = self.profile.endpoints.get(ep_name)
        if not ep_def: return None
            
        iface_type = self.profile.interface_types.get(ep_def.type)
        if not iface_type: return None

        intent = command.intent
        # Xử lý Logic Toggle bằng cách đọc State hiện tại
        if intent == Intent.TOGGLE:
            current_val = self.state_manager.get_state_value(ep_name)
            intent = Intent.TURN_OFF if current_val == 1 else Intent.TURN_ON

        target_semantic = None
        new_state_val = None

        if intent == Intent.TURN_ON:
            target_semantic = iface_type.controlled.get("turn_on") or iface_type.controlled.get("turn_on_indicator")
            new_state_val = 1
        elif intent == Intent.TURN_OFF:
            target_semantic = iface_type.controlled.get("turn_off") or iface_type.controlled.get("turn_off_indicator")
            new_state_val = 0
            
        if target_semantic and target_semantic.value:
            # OPTIMISTIC UPDATE: Cập nhật state nội bộ ngay khi xuất lệnh 
            # (Phù hợp với đặc thù giao thức RS485)
            if new_state_val is not None:
                self.state_manager.update_state(ep_name, new_state_val)
                
            return f"{device_id} {target_semantic.value}"
            
        return None