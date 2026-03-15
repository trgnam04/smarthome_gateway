# internal/devices/manager.py
import json
from typing import Dict, List, Optional, Type
from internal.models import DeviceProfile, DeviceConfig, Protocol
from .base_device import Device
from .knx_device import KNXDevice
from .rs485_device import RS485Device

class DeviceManager:
    # Bảng đăng ký các lớp thiết bị (Factory Registry)
    _DEVICE_CLASSES: Dict[Protocol, Type[Device]] = {
        Protocol.KNX: KNXDevice,
        Protocol.RS485: RS485Device
    }

    def __init__(self):
        # Lưu trữ các thiết bị đang hoạt động (Runtime Objects)
        self._devices: Dict[str, Device] = {}

    def load_device(self, config: DeviceConfig, profile: DeviceProfile):
        """Khởi tạo Device Object dựa vào Protocol thông qua Factory"""
        device_class = self._DEVICE_CLASSES.get(profile.protocol)
        
        if not device_class:
            raise ValueError(f"Protocol không hợp lệ hoặc chưa được hỗ trợ: {profile.protocol}")
            
        # Khởi tạo đối tượng
        device = device_class(config, profile)
        self._devices[device.system_id] = device
        
        # Log ra các Endpoints đã được cấu hình
        configured_eps = list(config.endpoints.keys())
        print(f"[DeviceManager] Đã nạp: '{device.system_id}' | Khả dụng: {configured_eps}")

    def load_from_json_file(self, filepath: str, available_profiles: Dict[str, DeviceProfile]):
        """
        Đọc file devices.json, đối chiếu với Profile và nạp hàng loạt thiết bị vào RAM.
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"[DeviceManager] Lỗi: Không tìm thấy file database '{filepath}'")
            return
        except json.JSONDecodeError:
            print(f"[DeviceManager] Lỗi: File '{filepath}' sai định dạng JSON")
            return

        success_count = 0
        for system_id, dev_data in data.items():
            # 1. Chuyển đổi JSON Dict thành Object Config
            config = DeviceConfig.from_dict(system_id, dev_data)
            
            # 2. Tìm Profile tương ứng của thiết bị này
            profile = available_profiles.get(config.profile_id)
            if not profile:
                print(f"[DeviceManager] Bỏ qua '{system_id}': Không tìm thấy Profile '{config.profile_id}'")
                continue
                
            # 3. Tiến hành nạp vào bộ nhớ
            try:
                self.load_device(config, profile)
                success_count += 1
            except Exception as e:
                print(f"[DeviceManager] Bỏ qua '{system_id}' do lỗi khởi tạo: {str(e)}")
                
        print(f"[DeviceManager] Hoàn tất nạp {success_count}/{len(data)} thiết bị từ Database.")

    def get_device(self, system_id: str) -> Optional[Device]:
        return self._devices.get(system_id)
        
    def get_all(self) -> List[Device]:
        return list(self._devices.values())