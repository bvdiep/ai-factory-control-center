#6

**Nhiệm vụ**: Làm màn hình liệt kê các nhiệm vụ mình phải làm

**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**:
- Bổ sung một menu "My Activity" trong đó thể hiện các Projects mà user được gán vào ít nhất một phase.
- Sắp xếp theo thứ tự created_at (desc) của project
- Cách thể hiện cho từng project: mỗi project được thể hiện là một nhóm rải các phase (order từ nhỏ đến lớn của phase)
- Mỗi phase cần thể hiện:
    - Order
    - Mission
    - Status
    - Tên của assigned user.
    - Nếu phase đó là do chính user đang đăng nhập assigned thì có nút Execute. Trước măt nút này lên alert "Under construction"
    - Nếu phase đó không phải do user này phụ trách thì thể hiện font chữ màu khác đi.

- Cập nhật tài liệu /plans/technical_document.md