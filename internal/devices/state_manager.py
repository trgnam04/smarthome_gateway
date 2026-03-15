# internal/devices/state_manager.py

from typing import Dict, Any, Optional
from internal.models import DeviceProfile, DeviceConfig, EndpointState

class EndpointStateManager:
    """
    Component chịu trách nhiệm quản lý, lưu trữ và xác thực trạng thái 
    của toàn bộ các kênh (endpoints) trên một thiết bị.
    """
    def __init__(self, profile: DeviceProfile, config: DeviceConfig):
        self.profile = profile
        self.config = config
        self._states: Dict[str, EndpointState] = {}
        
        # Tự động khởi tạo bộ nhớ State cho các kênh được người dùng khai báo
        self._initialize_states()

    def _initialize_states(self):
        for ep_name in self.config.endpoints.keys():
            # Khởi tạo giá trị mặc định dựa trên DPT hoặc loại dữ liệu
            ep_def = self.profile.endpoints.get(ep_name)
            if not ep_def:
                continue
                
            iface_type = self.profile.interface_types.get(ep_def.type)
            default_val = 0 # Mặc định cho DPT 1 (On/Off) hoặc Raw
            
            # Tương lai: Nếu là dpt 9.001 (Nhiệt độ), có thể default là 0.0
            if iface_type and iface_type.dpt.startswith("9."):
                default_val = 0.0
                
            self._states[ep_name] = EndpointState(value=default_val)

    def update_state(self, endpoint_name: str, new_value: Any) -> bool:
        """
        Cập nhật trạng thái. Có thể bổ sung logic validate kiểu dữ liệu ở đây.
        Trả về True nếu giá trị thực sự thay đổi, False nếu không đổi.
        """
        if endpoint_name not in self._states:
            return False
            
        current_state = self._states[endpoint_name]
        
        # Nếu trạng thái không đổi, không cần update timestamp
        if current_state.value == new_value:
            return False
            
        current_state.update(new_value)
        # TƯƠNG LAI: Bắn Event qua Message Queue / WebSockets để Web UI cập nhật
        print(f"[State Manager] Kênh '{endpoint_name}' thay đổi -> {new_value}")
        return True

    def get_state_value(self, endpoint_name: str) -> Optional[Any]:
        """Lấy giá trị hiện tại của một kênh"""
        state_obj = self._states.get(endpoint_name)
        return state_obj.value if state_obj else None
        
    def get_all_states(self) -> Dict[str, Any]:
        """Trả về toàn bộ trạng thái (Dùng cho API lấy dữ liệu lên Web UI)"""
        return {ep: state.value for ep, state in self._states.items()}