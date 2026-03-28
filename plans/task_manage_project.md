**Nhiệm vụ**: Thêm trang Projects và update entity Project, Phase, User.

**Code base**: /home/dd/work/diep/ai-factory-control-center

**Chi tiết nhiệm vụ**:
- Tạo trang Projects, trong đó:
    - Hiển thị danh sách các projects
    - Mỗi project có các thông tin cơ bản như name, description, path, user, status
    - Có thể thêm, sửa, xóa project
    - Có thể tìm kiếm, lọc project theo status
    - Form tạo mới và sửa project thì mở ở modal popup.
- Update project:
    - Thêm trường updated_at để lưu ngày update gần nhất
    - Lưu ý cập nhật updated_at khi sửa project.
- Update phase:
    - Thêm trường created_at để lưu ngày tạo mới phase.
    - Thêm trường updated_at để lưu ngày update gần nhất.
    - Lưu ý cập nhật updated_at khi sửa phase.
- Update user:
    - Thêm trường created_at để lưu ngày tạo mới user.
    - Thêm trường updated_at để lưu ngày update gần nhất.
    - Lưu ý cập nhật updated_at khi sửa user.

- Cập nhật tài liệu /plans/technical_document.md