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
        
        # 1. CẬP NHẬT TRẠNG THÁI LÊN RAM (Optimistic Update)
        new_state_val = None
        if intent == Intent.TURN_ON:
            new_state_val = 1
        elif intent == Intent.TURN_OFF:
            new_state_val = 0
        elif intent == Intent.TOGGLE:
            current_val = self.state_manager.get_state_value(ep_name)
            new_state_val = 0 if current_val == 1 else 1

        if new_state_val is not None:
            self.state_manager.update_state(ep_name, new_state_val)

        # ==========================================================
        # 2. STRATEGY 1: XỬ LÝ DPT BITMASK (Cho các thiết bị như LED Panel)
        # ==========================================================
        if iface_type.dpt == "modbus_bitmask":
            base_frame = iface_type.base_frame
            if not base_frame: return None
            
            # Quét toàn bộ các kênh của thiết bị này để gom bitmask
            mask_value = 0
            for iter_ep_name, iter_ep_def in self.profile.endpoints.items():
                iter_iface = self.profile.interface_types.get(iter_ep_def.type)
                
                # Nếu kênh này cũng thuộc loại bitmask và xài chung base_frame
                if iter_iface and iter_iface.dpt == "modbus_bitmask" and iter_iface.base_frame == base_frame:
                    bit_idx = iter_iface.bit_index
                    if bit_idx is not None:
                        # Đọc trạng thái hiện tại từ StateManager
                        state_val = self.state_manager.get_state_value(iter_ep_name) or 0
                        # Dịch bit và cộng dồn vào mask_value
                        mask_value |= (state_val << bit_idx)
            
            # Ráp thành chuỗi lệnh hoàn chỉnh: ID + Base Frame + Mask Byte
            # Ví dụ: "01" + "06 10 08 01" + "05" -> "01 06 10 08 01 05"
            return f"{device_id} {base_frame} {mask_value:02X}"

        # ==========================================================
        # 3. STRATEGY 2: XỬ LÝ DPT RAW_HEX TĨNH (Như Rơ-le RS485 cũ)
        # ==========================================================
        target_semantic = None
        if new_state_val == 1:
            target_semantic = iface_type.controlled.get("turn_on") or iface_type.controlled.get("turn_on_indicator")
        elif new_state_val == 0:
            target_semantic = iface_type.controlled.get("turn_off") or iface_type.controlled.get("turn_off_indicator")
            
        if target_semantic and target_semantic.value:
            return f"{device_id} {target_semantic.value}"
            
        return None