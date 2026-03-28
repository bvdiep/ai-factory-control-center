**Nhiệm vụ**: Điều chỉnh project.path
**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**:
- Trường project.path không còn lưu đường dẫn tuyệt đối của project nữa mà sẽ chỉ lưu đường dẫn tương đối của project.
- Việc ghép trường này vào các vị trí cần thiết để đảm bảo đúng thư mục đã được thực hiện thủ công (setup cho openhand workspace ...)
- Ở nhiệm vụ này chúng ta sẽ bổ sung rules cho trường này:
    - Project.path phải là string chỉ bao gồm chữ cái, số, dấu gạch dưới, dấu gạch ngang, dấu chấm.
    - Project.path không được chứa khoảng trắng.
    - Project.path không được chứa ký tự đặc biệt, không chứa cả các ký tự gạch chéo (tức chỉ chấp nhận một tầng)
    - Project.path phải là duy nhất, không thể có hai project trùng path.
    - Project.path không được bỏ trống.
    - Thực hiện tạo ngay thư mục này ở trong PROJECT_ROOT
    - Không cho phép sửa path này sau khi đã tạo.

- Hãy cập nhật lại tài liệu /plans/technical_document.md cho phù hợp nếu cần thiết.
