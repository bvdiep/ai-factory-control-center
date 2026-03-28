#1

Code base: /home/dd/work/diep/ai-factory-control-center
Nhiệm vụ của tính năng: quản lý users, cho phép admin thêm, sửa user
Chi tiết nhiệm vụ như sau:
- Bổ sung trường status cho bảng user, mặc định sẽ là active.
- Bổ sung thêm trường name cho bảng user.
- Khi login nếu user có status là inactive thì không cho phép login.
- Tạo tính năng quản lý user, trong đó:
    - Chỉ role admin mới có quyền với tính năng này.
    - Phần danh sách user có phân trang, có thể lọc theo status, có thể tìm kiếm theo username, name.
    - Cho phép tạo mới, sửa user.
    - Các user không được phép trùng username.
- Bổ sung menu User tương ứng. Chú ý là menu này chỉ có cho role tương ứng.
- Cập nhật tài liệu /plans/technical_document.md
