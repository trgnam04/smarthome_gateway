# internal/models/enums.py
from enum import Enum

class Protocol(str, Enum):
    KNX = "knx"
    RS485 = "rs485"

class Intent(str, Enum):
    TURN_ON = "TURN_ON"
    TURN_OFF = "TURN_OFF"
    TOGGLE = "TOGGLE"
    # Bạn có thể bổ sung thêm DIM_UP, DIM_DOWN, STOP... sau này