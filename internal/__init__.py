# internal/__init__.py

"""
Internal Package - Smart Gateway.

Thư mục này chứa toàn bộ Core Logic của hệ thống (Models, Devices, Router, HAL, Storage).
Theo quy ước thiết kế, các đoạn mã nằm trong 'internal' chỉ được sử dụng nội bộ 
bởi ứng dụng (ví dụ: được gọi từ cmd/gateway/main.py hoặc tests/).

KHÔNG export các module nội bộ ra ngoài project ở file này để giữ không gian tên (namespace) sạch sẽ.
"""

# Lưu ý: Chúng ta cố tình để trống phần code ở đây. 
# Việc import sẽ được thực hiện trực tiếp vào từng sub-package (như `from internal.models import ...`)