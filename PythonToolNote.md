# Pytest
Nếu bạn đã bắt đầu viết các hàm hoặc tính năng cho ứng dụng Python của mình, thì **pytest** chính là "người gác cổng" giúp bạn đảm bảo mọi thứ hoạt động đúng như mong đợi trước khi tung ra thực tế.
---
## 1. Công dụng của Pytest là gì?
**Pytest** là một framework dùng để viết và chạy các đoạn mã kiểm thử (**unit tests**). Thay vì bạn phải chạy chương trình rồi nhập dữ liệu bằng tay để xem nó có lỗi không, bạn viết một file script để Python tự làm việc đó.

* **Tự động hóa:** Kiểm tra hàng trăm hàm chỉ trong vài giây.
* **Phát hiện lỗi sớm (Regression Testing):** Khi bạn sửa code ở file A, vô tình làm hỏng file B, pytest sẽ báo lỗi ngay lập tức.
* **Cú pháp đơn giản:** Khác với bộ thư viện `unittest` mặc định của Python (khá rườm rà), pytest cho phép bạn dùng lệnh `assert` cực kỳ tự nhiên.
* Ví dụ: `assert add(1, 2) == 3` (Chỉ cần thế này là xong một bài test).
---
## 2. Ý nghĩa của lệnh `python -m pytest`
Khi bạn gõ lệnh này trong terminal tại thư mục dự án, bạn đang ra lệnh cho Python thực hiện một cuộc "tổng kiểm tra". Cụ thể:
### Tại sao lại dùng `python -m pytest` thay vì chỉ gõ `pytest`?
Sử dụng `python -m` đảm bảo rằng pytest được chạy bằng chính **trình thông dịch Python** và **môi trường ảo** mà bạn đang kích hoạt. Nó giúp tránh lỗi "không tìm thấy module" nếu bạn có nhiều phiên bản Python trong máy.
### Quy trình "truy quét" của lệnh này:
1. **Tìm kiếm (Test Discovery):** Pytest sẽ lục lọi toàn bộ thư mục hiện tại và các thư mục con để tìm các file có tên bắt đầu bằng `test_*.py` hoặc kết thúc bằng `*_test.py`.
2. **Thu thập (Collection):** Bên trong các file đó, nó tìm các hàm có tên bắt đầu bằng `test_`.
3. **Thực thi (Execution):** Nó chạy tất cả các hàm đó và so sánh kết quả trả về với mong đợi của bạn (thông qua lệnh `assert`).
4. **Báo cáo (Reporting):** * Dấu **`.`** (chấm xanh): Test vượt qua (Passed).
* Chữ **`F`** (đỏ): Test thất bại (Failed) - nó sẽ hiện chi tiết sai ở đâu, dòng nào.
* Chữ **`E`**: Lỗi hệ thống hoặc lỗi cú pháp trong file test (Error).
---
## 3. Ví dụ thực tế
Giả sử bạn có file `logic.py`:
```python
def tinh_tong(a, b):
    return a + b
```
Và file `test_logic.py`:
```python
from logic import tinh_tong
def test_tinh_tong_dung():
    assert tinh_tong(10, 5) == 15
def test_tinh_tong_sai():
    assert tinh_tong(2, 2) == 5  # Cái này sẽ bị báo lỗi 'F'
```
Khi chạy `python -m pytest`, bạn sẽ thấy ngay mã nguồn của mình đang ổn hay đang "toang" ở đâu.

## Giải thích output của pytest
```
platform linux -- Python 3.10.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/trgnam04/Ubuntu_Workspace/THERSIS_WORKSPACE/smarthome_gateway
configfile: pyproject.toml
plugins: anyio-4.12.1
collected 8 items                                                                                                                                                                                              
tests/test_knx_utils.py .......                                                                                                                                                                            [ 87%]
tests/test_router_semantic.py .                                                                                                                                                                            [100%]
```

Dưới đây là giải thích chi tiết từng phần trong báo cáo của Pytest:

### 1. Thông tin môi trường (Header)

```text
platform linux -- Python 3.10.12, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/trgnam04/.../smarthome_gateway
configfile: pyproject.toml
```
* **platform linux:** Bạn đang chạy trên hệ điều hành Ubuntu.
* **Python 3.10.12 & pytest-9.0.2:** Phiên bản Python và Pytest hiện tại bạn đang dùng.
* **rootdir:** Thư mục gốc của dự án mà Pytest nhận diện được.
* **configfile:** Bạn có file `pyproject.toml`. Pytest đã đọc các cấu hình test từ file này thay vì dùng mặc định.
### 2. Thu thập dữ liệu (Collection)
```text
collected 8 items
```
Pytest đã tìm thấy tổng cộng **8 hàm kiểm thử** (test cases) trong project của bạn để thực thi.
### 3. Tiến trình thực thi (Progress)
Đây là phần quan trọng nhất để biết file nào đang chạy:
* **`tests/test_knx_utils.py ....... [ 87%]`**:
* File này chứa 7 bài test (tương ứng với **7 dấu chấm**).
* **Dấu chấm (`.`):** Có nghĩa là bài test đó đã **PASSED** (Vượt qua thành công). Nếu có lỗi, nó sẽ hiện chữ `F` (Fail) màu đỏ.
* `87%`: Cho biết sau khi chạy xong file này, bạn đã hoàn thành 87% tổng số bài test.
* **`tests/test_router_semantic.py . [100%]`**:
* File này chứa **1 bài test** còn lại.
* Tổng cộng 7 + 1 = 8 bài test đã chạy xong.
### 4. Kết luận (Summary)

```text
========================= 8 passed in 0.07s =========================
```
* **8 passed:** Tất cả 8 bài test đều thành công. Không có lỗi logic nào bị phát hiện dựa trên các `assert` bạn đã viết.
* **in 0.07s:** Tốc độ thực hiện cực kỳ nhanh (chưa tới 1/10 giây). Đây là ưu điểm lớn của Pytest so với việc test thủ công.
---
### Mẹo nhỏ cho bạn:
Nếu bạn muốn xem chi tiết tên từng hàm test nào đang chạy (thay vì chỉ nhìn dấu chấm), hãy thử thêm tham số `-v` (verbose):
```bash
python -m pytest -v
```
Khi đó, kết quả sẽ hiện rõ ràng kiểu:
`tests/test_knx_utils.py::test_parse_individual_address PASSED`