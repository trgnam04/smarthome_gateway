# internal/router/event_broker.py

from typing import Callable, Optional
from ..models import Event, Command, Protocol
from ..devices.manager import DeviceManager
from .mapping_engine import MappingEngine

class EventBroker:
    """
    Nhận Raw Byte từ phần cứng, chuyển cho Device dịch thành Event,
    hỏi MappingEngine, tạo Command, và xuất lại Raw Byte cho phần cứng.
    """
    def __init__(self, device_manager: DeviceManager, mapping_engine: MappingEngine):
        self.device_mgr = device_manager
        self.mapping_engine = mapping_engine
        # Callback function (Delegate) để gửi byte xuống tầng Hardware
        self.hardware_tx_callback: Optional[Callable[[Protocol, str], None]] = None

    def bind_hardware_tx(self, callback_func: Callable[[Protocol, str], None]):
        """Đăng ký hàm gửi dữ liệu vật lý (Dependency Injection)"""
        self.hardware_tx_callback = callback_func

    def process_incoming_raw(self, protocol: Protocol, raw_hex: str):
        """Hàm này được Hardware Layer gọi liên tục khi có dữ liệu đến"""
        print(f"\n[Broker] <-- Nhận từ Bus {protocol.name}: {raw_hex}")
        
        # 1. Quét qua các thiết bị để tìm xem gói tin này thuộc về ai
        for device in self.device_mgr.get_all():
            if device.profile.protocol == protocol:
                
                # Thiết bị (Object) tự phân tích cấu trúc cEMI hoặc Modbus
                events = device.process_incoming(raw_hex)
                
                if events:
                    for event in events:
                        print(f"  [!] Thiết bị '{device.system_id}' phát ra sự kiện: '{event.event_name}'")
                        self._dispatch_event(event)

    def _dispatch_event(self, event: Event):
        """Định tuyến sự kiện nội bộ"""
        actions = self.mapping_engine.get_actions_for_event(event)
        
        if not actions:
            print(f"  [-] Không có mapping nào cho sự kiện này.")
            return

        for action in actions:
            # LƯU Ý: Đã thay đổi target_interface thành target_endpoint cho phù hợp kiến trúc mới
            command = Command(
                target_device=action.target_device,
                target_endpoint=action.target_endpoint, 
                intent=action.intent
            )
            print(f"  [>] Định tuyến đến '{command.target_device}' (Endpoint: {command.target_endpoint}, Intent: {command.intent.name})")
            self._dispatch_command(command)

    def _dispatch_command(self, command: Command):
        """Gửi lệnh đến thiết bị đích và yêu cầu xuất raw byte"""
        target_dev = self.device_mgr.get_device(command.target_device)
        
        if not target_dev:
            print(f"  [x] Lỗi: Không tìm thấy thiết bị đích '{command.target_device}'")
            return

        # Yêu cầu thiết bị đích tự lắp ráp chuỗi Hex dựa trên Intent
        raw_hex_to_send = target_dev.execute_action(command)
        
        if raw_hex_to_send and self.hardware_tx_callback:
            print(f"  [Tx] --> Yêu cầu Hardware gửi lệnh: {raw_hex_to_send}")
            # Gọi hàm callback để thực sự ném byte ra cổng UART/Serial
            self.hardware_tx_callback(target_dev.profile.protocol, raw_hex_to_send)