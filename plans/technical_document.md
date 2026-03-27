# Tài liệu Kỹ thuật: AI Factory Control Center

## 1. Tổng quan hệ thống
AI Factory Control Center là một hệ thống quản lý điều khiển được xây dựng dựa trên framework **FastHTML** cho giao diện web và **SQLModel** cho việc tương tác với cơ sở dữ liệu (SQLite). Hệ thống cung cấp các chức năng cơ bản về xác thực người dùng và quản lý dự án theo vai trò.

## 2. Kiến trúc và Các khối chức năng (Functional Blocks)

Hệ thống được chia thành các khối chức năng chính sau:

### 2.1. Khối Giao diện Web (Web Interface - FastHTML)
- **Vị trí**: `app/main.py`
- **Mô tả**: Đóng vai trò là Entry point của ứng dụng. Sử dụng FastHTML để render giao diện người dùng (UI) trực tiếp từ mã Python mà không cần framework frontend riêng biệt.
- **Thành phần**:
  - Giao diện Đăng nhập (Login).
  - Giao diện Bảng điều khiển (Dashboard).
  - Giao diện Quản lý người dùng (User Management - Dành cho Admin).
  - Xử lý điều hướng (Routing) và Middleware (Beforeware) để bảo vệ các route yêu cầu xác thực.

### 2.2. Khối Xác thực và Phân quyền (Authentication & Authorization)
- **Vị trí**: `app/core/auth.py`
- **Mô tả**: Xử lý các nghiệp vụ liên quan đến bảo mật người dùng.
- **Thành phần**:
  - Băm mật khẩu và kiểm tra mật khẩu sử dụng thư viện `bcrypt`.
  - Xác thực thông tin đăng nhập của người dùng.
  - Quản lý phiên đăng nhập (Session management) thông qua FastHTML session.
  - Middleware kiểm tra trạng thái đăng nhập trước khi cho phép truy cập các trang nội bộ.

### 2.3. Khối Mô hình Dữ liệu (Data Models)
- **Vị trí**: `app/models/__init__.py`
- **Mô tả**: Định nghĩa cấu trúc cơ sở dữ liệu sử dụng SQLModel (kết hợp giữa Pydantic và SQLAlchemy).
- **Các thực thể (Entities)**:
  - **User**: Lưu trữ thông tin người dùng (username, name, hashed_password, role_id, status).
  - **Role**: Định nghĩa vai trò của người dùng (name, system_prompt).
  - **Project**: Quản lý thông tin dự án (name, description, path, config_override, status, user_id). Mỗi dự án có một người quản lý (Project Manager - PM).
  - **Phase**: Quản lý các giai đoạn thực hiện của dự án (mission, project_id, role_id, user_id, skill, status, logging, tokens, order). Các trạng thái bao gồm: `pending`, `init`, `processing`, `processed`, `cancel`, `done`.

### 2.4. Khối Cơ sở dữ liệu (Database Core)
- **Vị trí**: `app/core/database.py`
- **Mô tả**: Quản lý kết nối đến cơ sở dữ liệu SQLite (`system.db`).
- **Thành phần**:
  - Khởi tạo Engine kết nối.
  - Cung cấp Session cho các thao tác truy vấn dữ liệu.

### 2.5. Khối Tiện ích và Khởi tạo (Scripts)
- **Vị trí**: `scripts/init_db.py`
- **Mô tả**: Script dùng để khởi tạo cấu trúc bảng trong cơ sở dữ liệu và tạo dữ liệu mẫu (seed data) ban đầu khi triển khai hệ thống.

### 2.6. Khối Quản lý Người dùng (User Management)
- **Vị trí**: `app/routers/users.py`
- **Mô tả**: Cung cấp các chức năng quản lý người dùng dành cho Admin.
- **Thành phần**:
  - Danh sách người dùng với phân trang (10 users/page).
  - Tìm kiếm theo `username` hoặc `name`.
  - Lọc theo trạng thái `status`.
  - Thêm mới người dùng (yêu cầu `username` duy nhất).
  - Chỉnh sửa thông tin người dùng.


## 3. Các chức năng của hệ thống

### 3.1. Chức năng Đăng nhập (Login)
- Người dùng nhập `username` và `password` tại trang `/login`.
- Hệ thống kiểm tra thông tin trong cơ sở dữ liệu, trạng thái `status` (phải là `active`) và đối chiếu mật khẩu đã được băm (bcrypt).
- Nếu hợp lệ, hệ thống tạo session lưu `user_id` và chuyển hướng đến trang Dashboard.
- Nếu không hợp lệ, hiển thị thông báo lỗi.

### 3.2. Chức năng Bảng điều khiển (Dashboard)
- Truy cập tại route `/dashboard` (yêu cầu đã đăng nhập).
- Hiển thị lời chào mừng với tên người dùng.
- Hiển thị Vai trò (Role) hiện tại của người dùng.
- Liệt kê danh sách các Dự án (Projects) mà người dùng là Project Manager (PM), bao gồm:
  - Tên dự án.
  - Mô tả dự án.
  - Đường dẫn (Path) của dự án.

### 3.3. Chức năng Đăng xuất (Logout)
- Truy cập tại route `/logout`.
- Hệ thống xóa toàn bộ dữ liệu trong session hiện tại.
- Chuyển hướng người dùng về lại trang Đăng nhập.

### 3.4. Chức năng Quản lý Người dùng (User Management - Admin Only)
- Chỉ hiển thị menu "Users" cho người dùng có vai trò `Admin`.
- Truy cập tại route `/users`.
- Cho phép tìm kiếm người dùng theo `username` hoặc `name`.
- Cho phép lọc danh sách người dùng theo trạng thái (`active`/`inactive`).
- Hỗ trợ phân trang danh sách người dùng.
- Thêm mới người dùng với các thông tin: username, name, password, role, status.
- Sửa đổi thông tin người dùng hiện có.
- Ràng buộc: `username` phải là duy nhất trên toàn hệ thống.

### 3.5. Bảo vệ Route (Route Protection)
- Hệ thống sử dụng `Beforeware` để tự động kiểm tra session của người dùng trước khi truy cập bất kỳ trang nào (ngoại trừ `/login`, `/static`, `/favicon.ico`).
- Nếu chưa đăng nhập, người dùng sẽ bị buộc chuyển hướng về trang `/login`.

### 3.6. Chức năng Quản lý Dự án và Phase (Project & Phase Management)
- **Chi tiết Dự án**: 
  - Truy cập thông qua liên kết tại tên dự án ở trang Dashboard.
  - Hiển thị thông tin cơ bản của dự án (Tên, Mô tả, Path, Trạng thái).
  - Liệt kê danh sách các giai đoạn (Phases) của dự án, sắp xếp theo thứ tự (`order`).
- **Quản lý Phase**:
  - Xem chi tiết toàn bộ các trường của Phase (Mission, Skill, Status, Logging, Metrics) cùng thông tin Dự án liên quan qua nút "Details". Tại đây, hệ thống cung cấp các nút thao tác dựa trên vai trò (hiện đang ở chế độ chờ phát triển - "Under construction"):
    - Nếu người dùng là PM của dự án: Có các nút **Cancel**, **Approve**, **Init**.
    - Nếu người dùng được gán cho phase đó: Có nút **Execute**.
  - Thêm mới Phase vào dự án: Nhập Order, Mission, Chọn Role và User (tùy chọn).
  - Ràng buộc khi thêm Phase: Không cho phép thêm Phase có `order` nhỏ hơn một Phase đã bắt đầu (status khác `pending`).
  - Chỉnh sửa Phase: Chỉ cho phép chỉnh sửa các Phase đang ở trạng thái `pending`.
  - Cảnh báo: Hệ thống hiển thị cảnh báo (non-blocking) qua thông báo alert nếu người dùng được gán cho Phase có vai trò (Role) không khớp với vai trò yêu cầu của Phase đó.


## 4. Môi trường triển khai
- **Ngôn ngữ**: Python 3
- **Cơ sở dữ liệu**: SQLite
- **Quản lý tiến trình**: Hỗ trợ chạy trực tiếp qua Python hoặc sử dụng PM2 (`ecosystem.config.js`) cho môi trường production.
