**Nhiệm vụ**: Logic phase ở màn Execution
**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**: Logic về các trạng thái phase
- Ở màn execution (`/projects/{project_id}/phases/{phase_id}/execution`) cần implement các rules sau về status của phase:
    - Nút Execute ở form sẽ luôn disabled và màu xám khi status của phase khác "Start", "Processing". Đồng thời với đó thì ở cạnh nút có ghi chú màu xám: "Wrong phase status". Nếu status phù hợp thì thể hiện như hiện tại.
    - Nếu phase đang ở status Start hoặc Processing thì ở bên trái link "Force complete" bổ sung thêm một link nữa màu đỏ "Make Processed" dùng để cho user chuyển status thành Processed.
    - Khi kích hoạt nút "Make Processed" thì phải có alert cảnh báo. Nếu user đồng ý thì thực hiện việc chuyển status của phase thành "Processed"
- Bổ sung thêm một rule trong màn execution: khi user nhấn nút Execute thì nút đã chuyển sang loading rồi: Yêu cầu là khi nó enable trở lại thì xóa nội dung ở ô Prompt đi.
- Khi status của Phase là Start và nhấn nút Execute thì chuyển status của phase thành Processing.

- Hãy cập nhật lại tài liệu /plans/technical_document.md
