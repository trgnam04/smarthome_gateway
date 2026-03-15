import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from internal.models import DeviceProfile

# Khởi tạo profile từ file JSON lưu trên ổ cứng
profile_knx = DeviceProfile.from_json_file("configs/profiles/profile_knx_hager_relay.json")
profile_rs485 = DeviceProfile.from_json_file("configs/profiles/profile_rs485_niren_4_button_panel.json")

# In thử ra để xem dữ liệu đã được parse đúng chuẩn Object chưa

print(f"Loaded Profile: {profile_rs485.profile_id}")
print(f"Button 1 Type: {profile_rs485.endpoints['btn_1'].type}")
print(f"Logic DPT: {profile_rs485.interface_types['niren_button_1'].dpt}")

print(f"Loaded Profile: {profile_knx.profile_id}")
print(f"Channel 1 Type: {profile_knx.endpoints['ch_1'].type}")
print(f"Logic DPT: {profile_knx.interface_types['relay_1_bit'].dpt}")