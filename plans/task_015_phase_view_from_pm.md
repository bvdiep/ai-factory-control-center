**Nhiệm vụ**: Update màn hình phase của PM
**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**: Triền khai logic nghiệp vụ của màn hình phase của PM
- Màn hình phase của Prohect (`/projects/{project_id}/phases/{phase_id}`) chỉnh sửa như sau:
    - Skill: Lấy từ role.skill tương ứng với role của phase.
    - Bỏ cụm "Logging" mà thay bằng link "Conversation". Nếu nhấn vào link này thì mở ra modal popup danh sách các tin nhắn giữa user và agent trong bảng executionmessage. Modal popup này y hệt như click vào link "Conversation" ở màn hình Execution.
    - Logic dùng các buttons chuyển status của phase như sau:
        - Nút Start:
            - Nó chỉ enabled nếu status hiện tại là Pending hoặc Start. Nếu khác đi thì nó disabled.
            - Nếu status đang là Pending thì nó chuyển thành Start và đang lá Start thì nó chuyển thành Pending.
        - Nút Approve:
            - Nó chỉ enabled nếu status của phase đang là "Processed" hoặc "Done".
            - Nếu đang là Processed thì thành Done mà đang Done thì thành Processed.
        - Nút Cancel:
            - Nút này tác động vào phase chuyển nó thành Cancel bất cứ lúc nào. Khi nhấn nút này thì phải có cảnh báo. Nếu user xác nhận thì nó chuyên status phase thành Cancel. Khi đã là cancel rồi thì nút đó trở thành disabled.
    - Hãy tô màu của Status tương tự như màu ở trang Execution.

- Hãy cập nhật lại tài liệu /plans/technical_document.md
