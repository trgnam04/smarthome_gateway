# Tổ chức dự án
```
smart-gateway/
├── cmd/
│   └── gateway/
│       └── main.* # Entry point của chương trình (Khởi tạo mọi thứ ở đây)
├── configs/
│   └── profiles/               # Chứa các file JSON tĩnh định nghĩa chuẩn thiết bị
├── internal/                   # Chứa toàn bộ source code (Không cho project khác import)
│   ├── models/
│   │   ├── __init__.py      # Facade Pattern: Gom các module nhỏ lại thành 1 interface thống nhất
│   │   ├── enums.py         # Chứa các hằng số, Enum
│   │   ├── profile.py       # Chứa các model liên quan đến bản thiết kế tĩnh (Profile)
│   │   ├── config.py        # Chứa các model cấu hình do user sinh ra
│   │   ├── runtime.py       # Chứa các model dữ liệu chạy trong RAM (Event, Command)
│   │   └── routing.py       # (Bổ sung) Chứa các model cho Mapping/Rule
│   ├── devices/                # MODULE: Quản lý logic thiết bị (State, Profile)
│   │   ├── __init__.py       # File khai báo module
│   │   ├── base_device.py    # Lớp trừu tượng (Abstract Base Class)
│   │   ├── knx_device.py     # Lớp thực thi cho KNX
│   │   ├── rs485_device.py   # Lớp thực thi cho RS485
│   │   └── manager.py        # Lớp quản lý vòng đời và Factory khởi tạo
│   ├── router/
│   │   ├── __init__.py          # File khai báo module
│   │   ├── mapping_engine.py    # Chịu trách nhiệm lưu trữ và tra cứu Rules
│   │   └── event_broker.py      # Chịu trách nhiệm nhận sự kiện, điều phối và gọi Hardware
│   ├── hal/                    # MODULE: Hardware Abstraction Layer
│   │   ├── rs485_port.* # (Code sau) Xử lý đọc/ghi cổng COM/UART
│   │   └── knx_tpuart.* # (Code sau) Xử lý đọc/ghi raw cEMI frame
│   ├── api/                    # (Code sau) Module REST/gRPC API cho Web UI
│   └── storage/                # (Code sau) Module đọc/ghi Database (SQLite/JSON)
├── web/                        # (Code sau) Frontend assets (HTML, JS, React/Vue)
├── scripts/                    # Các script build, deploy, test hệ thống
├── tests/                      # Unit tests cho devices và router
└── README.md
```

Các module chính trong Phase 1 Core Logic bao gồm:
- Module `models`
- Module `devices`
- Module `router`
- Module `hal`

# Design log

Note: KIỂM SOÁT CÁC THIẾT BỊ - QUẢN LÝ, ĐIỀU KHIỂN VÀ HIỆN THỰC
Liên quan: các class device của thiết bị, cụ thể là các method execution_action trong class device của rs485 và knx.
Nội dung: 
- Hiện tại theo triết lý control/controlled đã định nghĩa trước đó, ta thiết kế device prorile theo kiểu như sau:
    + Controll: Được feed hoàn toàn cho event broker để build bảng mapping.
    + Controlled: Được sử dụng bởi các device object để build gói tin và đẩy xuống đường bus.
- đối với Rs485 thì tương đối ổn, theo pattern hứng và xử lý sự kiện -> dễ mở rộng trong tương lai.
- Đối với KNX hiện tại hướng hiện thực đang theo hơi hướng hard code và khó mở rộng
- Semantic Data là gì? -> phục vụ cho việc build gói tin trong KNX phần useful data
- Interface Type -> quản lý triết lý định nghĩa thiết bị trong gateway bao gồm controll và controlled
-> tuy nhiên chúng ta cần cải thiện lại cách hiện thực các method execution trong class device
- Cần thêm việc check byte, crc ở gateway do từ EB tới gateway qua đường uart dữ liệu có thể bị nhiễu -> check ở gateway là tốt nhất

Note: FLOW KHỞI TẠO MỘT THIẾT BỊ KNX HOẶC RS485 TRÊN GIAO DIỆN HỆ THỐNG
Liên quan: Maybe cần chỉnh sửa class DeviceConfig lại cho phù hợp bao gồm trường dữ liệu và một số method hỗ trợ parse dữ liệu từ đường dẫn file json.
Nội dung:
    Khi người dùng chọn thêm thiết bị, bung list các thiết bị được define sẵn profile rồi lên để người dùng chọn, hoặc người dùng có thể chọn custom device và tự thêm profile mà người dùng tự định nghĩa vào cho nó.
    Sau khi đã chọn device và profile tương ứng, chúng ta cần một định dạng file json lưu trữ các thông tin cần thiết cho device đó -> Sau khi nhận được file json đó ta sẽ có hàm để khởi tạo các thiết bị với thông số do nguời dùng đã điều chỉnh và với file json profile của thiết bị -> vậy là ta đã tạo thành công các device vào trong hệ thống.
    Cần có chế độ start và chế độ cấu hình khi thực hiện cấu hình để quyết định khi nào dữ liệu trên RAM được update lại.

Note: QUẢN LÝ STATE CỦA CÁC THIẾT BỊ
Liên quan: Class Intent trong file domain.py
Nội dung:
- Phải phân biệt được sự khác nhau giữa các Intent TURN_ON, TURN_OFF và TOGGLE. Trong các intent đó chỉ có TOGGLE là thực hiện check state thôi.
- Chỉ các interface controlled mới cần lưu trữ state thôi, còn hiện tại các interface control thì chưa cần lưu trữ state do nó là do event broker nắm giữ

Note: VẤN ĐỀ TRUYỀN TẢI GÓI TIN GIỮA PI VÀ MCU
Liên quan: Hardware layer
Nội dung:
- Để pi có thể  nhận gói tin một cách chính xác hơn, chúng ta set thời gian nghỉ giữa hai gói tin là một con số  cố  định từ đó chúng ta canh thời gian nghỉ giữa hai gói tin để  thực hiện việc đóng gói dữ liệu -> cứ cho là lúc nào dữ liệu cũng đáng tin cậy. 

# Vibe code log
- không thống nhất device profile type -> trường interface ngay hàm process_incoming ở class RS485Device - ĐÃ FIX

- Cần cập nhật việc khởi tạo DeviceProfile cho thiết bị thông qua file json -> cập nhật ở module models, dataclass DeviceProfile

# Todo
- [x] Cập nhật việc khởi tạo DeviceProfile cho thiết bị thông qua file json -> cập nhật ở module models, dataclass DeviceProfile
- [ ] Cập nhật lại type cho knx device profile: thay vì relay_1_bit -> có thể thay bằng cái khác gắn với KNX hơn và phân biệt type thực sự qua prefix 1_bit chẳng hạn hoặc phân biệt thông qua DPT và type thì sau này sẽ hỗ trợ cho việc parse các giá trị nhiều bit
- [ ] Xử lý vấn đề khởi tạo thiết bị từ file json
- [ ] Ra một kịch bản đơn giản để test toàn bộ cơ chế broker có thể theo pytest hoặc không để đọc log của hệ thống
- [ ] Verify Dữ liệu do hệ thống tạo ra và xử  lý

# Command
To run test

```
    python -m unittest tests/test_knx_utils.py
```



