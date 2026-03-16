# internal/devices/rs485_device.py

from typing import List, Optional
from internal.models import Event, Command, Intent
from .base_device import Device

class RS485Device(Device):
    
    @staticmethod
    def _match_hex_template(template: str, raw_hex: str) -> bool:
        """
        Hàm so khớp chuỗi Hex có hỗ trợ Wildcard 'XX'.
        Ví dụ: template = "01 03 00 02 XX 02" sẽ khớp với raw_hex = "01 03 00 02 4A 02 8C 3A"
        """
        t_bytes = template.strip().split()
        r_bytes = raw_hex.strip().split()
        
        # Nếu raw_hex thu được ngắn hơn template cơ bản -> Chắc chắn sai frame
        if len(r_bytes) < len(t_bytes):
            return False
            
        for t, r in zip(t_bytes, r_bytes):
            # Nếu template là XX -> Bỏ qua, không check byte này
            if t.upper() == "XX":
                continue
            # Nếu khác nhau -> Không khớp
            if t.upper() != r.upper():
                return False
                
        # Khớp toàn bộ các byte quan trọng (bỏ qua phần đuôi CRC dư thừa nếu có)
        return True

    def process_incoming(self, raw_hex: str) -> List[Event]:
        events = []
        device_id = self.config.common_params.get("device_id", "")

        for ep_name, ep_def in self.profile.endpoints.items():
            iface_type = self.profile.interface_types.get(ep_def.type)
            if not iface_type: continue
            
            for evt_name, semantic in iface_type.control.items():
                # Ráp ID thiết bị vào đầu template. VD: "01" + "03 00 01 XX 02" -> "01 03 00 01 XX 02"
                expected_template = f"{device_id} {semantic.value}"
                
                # SỬ DỤNG HÀM MATCHING MỚI THAY VÌ "=="
                if self._match_hex_template(expected_template, raw_hex):
                    # Nút nhấn chỉ feed Event cho Broker!
                    events.append(Event(self.system_id, f"{ep_name}:{evt_name}", raw_hex))
        
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