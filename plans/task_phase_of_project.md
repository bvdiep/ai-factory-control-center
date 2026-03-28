#2

**Nhiệm vụ**: Tạo ra entity Phase của Project

**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**:
- Tạo ra thực thể Phase trong đó:
    - Thuộc tính mission: dùng để mô tả mục tiêu, nhiệm vụ của phase cũng như các deliverable kì vọng.
    - Phase thuộc một dự án (required).
    - Phase có thuộc tính Role (required), ý nghĩa là phase đó phù hợp với user của role đó thực thi.
    - Phase có thể assign cho user (optional). Nếu role của user khác role của phase thì có thông báo dạng warning (non-blocking)
    - Trường skill (default null): text sẽ lưu trữ kĩ năng cần thiết để thực thi.
    - Status: mặc định là "pending", các giá trị có thể là pending, init, processing, cancel, done
    - Logging (text): ghi lại một số log theo dõi phase
    - Token in, token out, cache hit, reasoning: các thông số của openhands khi thực hiện task.
    - Order: thứ tự của phase trong Project.
- Quản lý project và phase:
    - Từ màn hình dashboard có danh sách Project, có một link để trỏ sang màn hình detail của Project:
        - Phần phía trên hiển thị các thông tin cơ bản của project
        - Phần phía dưới liệt kê các phases của Project theo thứ tự phase.order, hiển thị các thông tin cơ bản của mỗi phase. Có link để mở ra popup xem chi tiết toàn bộ các trường của Phase đó.
    - Quản lý Phase:
        - Sử dụng luôn màn hình detail project để quản lý phase.
        - Cho phép thêm một phase vào dự án
        - So sánh order, nếu có một phase với order ngay sau nó (tức có order lớn hơn đầu tiên) mà status của nó khác "pending" thì không cho phép thêm.
        - Chỉ cho phép sửa với phase ở trạng thái Pending. Không cho phép sửa phase ở các trạng thái khác.
- Cập nhật tài liệu /plans/technical_document.md