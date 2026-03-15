# internal/devices/knx_device.py

from typing import List, Optional
from internal.models import Event, Command, Intent
from .base_device import Device
from .knx_utils import KNXUtils

class KNXDevice(Device):
    def process_incoming(self, raw_hex: str) -> List[Event]:
        events = []
        parsed = KNXUtils.parse_cemi_frame(raw_hex)
        if not parsed: return events
        
        target_ga = parsed["target_ga"]
        incoming_semantic = parsed["semantic"]

        for ep_name, ep_config in self.config.endpoints.items():
            if ep_config.status_ga == target_ga:
                ep_type_name = self.profile.endpoints[ep_name].type
                interface_logic = self.profile.interface_types[ep_type_name]
                
                for event_name, expected_semantic in interface_logic.control.items():
                    if (expected_semantic.apci == incoming_semantic.apci and 
                        expected_semantic.value == incoming_semantic.value):
                        
                        # Chỉ những endpoint có cấu hình 'controlled' (như Rơ-le) mới thực sự được update_state
                        self.state_manager.update_state(ep_name, incoming_semantic.value)
                        
                        full_event_name = f"{ep_name}:{event_name}"
                        events.append(Event(self.system_id, full_event_name, raw_hex))
        return events

    def execute_action(self, command: Command) -> Optional[str]:
        ep_name = command.target_endpoint
        ep_config = self.config.endpoints.get(ep_name)
        if not ep_config or not ep_config.command_ga: return None

        intent = command.intent
        if intent == Intent.TOGGLE:
            current_state = self.state_manager.get_state_value(ep_name)
            intent = Intent.TURN_OFF if current_state == 1 else Intent.TURN_ON

        ep_type_name = self.profile.endpoints[ep_name].type
        interface_logic = self.profile.interface_types[ep_type_name]
        
        cmd_key = "turn_on" if intent == Intent.TURN_ON else "turn_off"
        target_semantic = interface_logic.controlled.get(cmd_key)
        
        if not target_semantic: return None

        # Không tự cập nhật State ở đây (Optimistic). 
        # Chờ phần cứng KNX phản hồi vào hàm process_incoming để đảm bảo tính đồng nhất 100%.
        return KNXUtils.build_cemi_frame(
            src_addr="1.1.250", 
            dst_ga=ep_config.command_ga, 
            semantic=target_semantic, 
            data_length=interface_logic.data_length
        )