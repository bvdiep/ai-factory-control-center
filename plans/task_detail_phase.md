#4

**Nhiệm vụ**: Sửa khái niệm user trong Project và đưa một số actions của Phase vào trang detail phase, ô Phase info.

**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**:
- Sửa khái niệm user trong Project:
    - Bỏ users (danh sách) trong Project, thay vào đó là một user duy nhất (project.user). Ý nghĩa của user này là Project Manager.
- Thêm status "processed" cho Phase.
- Trang detail phase, mục Phase info:
    - Nếu user là PM của project (project.user) thì có các nút:
        - Cancel
        - Approve
        - Init
    - Nếu user là user của phase thì có nút:
        - Execute.

Trước mắt mọi nút này đều mở lên một popup alert là "Under construction"

- Cập nhật tài liệu /plans/technical_document.md