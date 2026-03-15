import os
import sys
import pytest
from internal.models import (
    Protocol, Intent, SemanticData, InterfaceType, EndpointDef, DeviceProfile,
    DeviceConfig, EndpointConfig, TriggerDef, ActionDef, MappingRule
)
from internal.devices import DeviceManager
from internal.router import MappingEngine, EventBroker

def test_rs485_to_knx_semantic_routing():
    """
    Kiểm thử luồng tích hợp tự động: 
    Nhấn nút RS485 -> EventBroker -> MappingEngine -> KNX Device -> Raw cEMI Frame
    """
    # 1. ĐỊNH NGHĨA PROFILE NGỮ NGHĨA
    profile_rs485 = DeviceProfile(
        profile_id="rs485_niren_4_btn", protocol=Protocol.RS485, device_type="button_panel",
        interface_types={
            "niren_btn_1": InterfaceType(
                dpt="raw", data_length=0,
                control={"pressed": SemanticData(apci="raw", value="03 00 02 02 02")},
                controlled={"turn_on_indicator": SemanticData(apci="raw", value="05 00 00 FF 00")}
            )
        },
        endpoints={"btn_1": EndpointDef(name="Nút 1", type="niren_btn_1")}
    )

    profile_knx = DeviceProfile(
        profile_id="knx_hager_txa_4", protocol=Protocol.KNX, device_type="actuator",
        interface_types={
            "relay_1_bit": InterfaceType(
                dpt="1.001", data_length=1,
                control={
                    "status_on": SemanticData(apci="GroupValueWrite", value=1),
                    "status_off": SemanticData(apci="GroupValueWrite", value=0)
                },
                controlled={
                    "turn_on": SemanticData(apci="GroupValueWrite", value=1),
                    "turn_off": SemanticData(apci="GroupValueWrite", value=0)
                }
            )
        },
        endpoints={"ch_1": EndpointDef(name="Output A", type="relay_1_bit")}
    )

    # 2. CẤU HÌNH THIẾT BỊ CỦA USER
    cfg_panel = DeviceConfig(
        system_id="dev_panel_livingroom", profile_id="rs485_niren_4_btn",
        common_params={"device_id": "0A"},
        endpoints={"btn_1": EndpointConfig()} 
    )
    
    cfg_relay = DeviceConfig(
        system_id="dev_relay_light", profile_id="knx_hager_txa_4",
        common_params={}, 
        endpoints={"ch_1": EndpointConfig(command_ga="2/1/1", status_ga="2/1/2")}
    )

    # 3. MAPPING ĐỊNH TUYẾN
    rule_1 = MappingRule(
        rule_id="r01",
        trigger=TriggerDef(source_device="dev_panel_livingroom", event_name="btn_1:pressed"),
        action=ActionDef(target_device="dev_relay_light", target_endpoint="ch_1", intent=Intent.TOGGLE)
    )

    # 4. KHỞI TẠO MODULES (COMPOSITION ROOT CHO BÀI TEST)
    dev_mgr = DeviceManager()
    dev_mgr.load_device(cfg_panel, profile_rs485)
    dev_mgr.load_device(cfg_relay, profile_knx)

    mapping_engine = MappingEngine()
    mapping_engine.load_rules([rule_1])

    broker = EventBroker(dev_mgr, mapping_engine)

    # 5. MOCK HARDWARE LAYER VÀ BẮT GIỮ OUTPUT
    # Thay vì chỉ print, ta lưu kết quả vào mảng để kiểm chứng
    hardware_output_log = []
    
    def mock_hardware_send(protocol: Protocol, raw_hex: str):
        hardware_output_log.append((protocol, raw_hex))
        
    broker.bind_hardware_tx(mock_hardware_send)

    # 6. RUNTIME: KÍCH HOẠT SỰ KIỆN TỪ RS485
    broker.process_incoming_raw(Protocol.RS485, "0A 03 00 02 02 02")

    # 7. KIỂM CHỨNG TỰ ĐỘNG (ASSERTIONS)
    # Đảm bảo hệ thống phát ra đúng 1 lệnh duy nhất
    assert len(hardware_output_log) == 1, "Hệ thống không xuất ra lệnh, hoặc xuất dư lệnh."
    
    protocol, sent_hex = hardware_output_log[0]
    
    # Đảm bảo lệnh xuất ra được định tuyến đúng xuống giao thức KNX
    assert protocol == Protocol.KNX, f"Giao thức sai. Mong đợi: {Protocol.KNX}, Thực tế: {protocol}"
    
    # Đảm bảo chuỗi Hex cEMI được build chính xác dựa trên cấu hình:
    # MessageCode(11) AddInfo(00) CF1(BC) CF2(E0) SRC(11 FA) DST(11 01) LEN(01) APDU(81)
    expected_hex = "11 00 BC E0 11 FA 11 01 01 81"
    assert sent_hex == expected_hex, f"Chuỗi Hex bị sai. Mong đợi: {expected_hex}, Thực tế: {sent_hex}"