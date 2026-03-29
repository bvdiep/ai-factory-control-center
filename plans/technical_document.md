# Tài liệu Kỹ thuật: AI Factory Control Center

## 1. Tổng quan hệ thống
AI Factory Control Center là một hệ thống quản lý điều khiển được xây dựng dựa trên framework **FastHTML** cho giao diện web và **SQLModel** cho việc tương tác với cơ sở dữ liệu (SQLite). Hệ thống cung cấp các chức năng cơ bản về xác thực người dùng và quản lý dự án theo vai trò.

## 2. Kiến trúc và Các khối chức năng (Functional Blocks)

Hệ thống được chia thành các khối chức năng chính sau, áp dụng kiến trúc phân lớp (Layered Architecture) để tăng tính module hóa và dễ bảo trì:

### 2.1. Khối Giao diện Web (Web Interface - FastHTML)
- **Vị trí**: `app/main.py`, `app/routers/`
- **Mô tả**: Đóng vai trò là Entry point của ứng dụng và xử lý routing. Sử dụng FastHTML để render giao diện người dùng (UI) trực tiếp từ mã Python.
- **Thành phần**:
  - Giao diện Đăng nhập (Login).
  - Giao diện Bảng điều khiển (Dashboard).
  - Giao diện Thực thi Giai đoạn (Phase Execution).
  - Giao diện Quản lý người dùng (User Management - Dành cho Admin).
  - Xử lý điều hướng (Routing) và Middleware (Beforeware) để bảo vệ các route yêu cầu xác thực.

### 2.2. Khối Dịch vụ (Services)
- **Vị trí**: `app/services/`
- **Mô tả**: Chứa các logic nghiệp vụ cốt lõi của ứng dụng, tách biệt khỏi tầng giao diện và routing.
- **Thành phần**:
  - `openhands_service.py`: Quản lý việc tương tác với OpenHands SDK, khởi tạo Agent, LLM, Workspace và chạy các tiến trình ngầm để thực thi nhiệm vụ AI.

### 2.3. Khối Cấu hình (Configuration)
- **Vị trí**: `app/core/config.py`
- **Mô tả**: Quản lý tập trung các biến môi trường và cấu hình của hệ thống.
- **Thành phần**:
  - Lớp `Settings` load các biến từ file `.env` (như `OPENHANDS_STORAGE_PATH`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `SECRET_KEY`).

### 2.4. Khối Xác thực và Phân quyền (Authentication & Authorization)
- **Vị trí**: `app/core/auth.py`
- **Mô tả**: Xử lý các nghiệp vụ liên quan đến bảo mật người dùng.
- **Thành phần**:
  - Băm mật khẩu và kiểm tra mật khẩu sử dụng thư viện `bcrypt`.
  - Xác thực thông tin đăng nhập của người dùng.
  - Quản lý phiên đăng nhập (Session management) thông qua FastHTML session.
  - Middleware kiểm tra trạng thái đăng nhập trước khi cho phép truy cập các trang nội bộ.

### 2.5. Khối Mô hình Dữ liệu (Data Models)
- **Vị trí**: `app/models/__init__.py`
- **Mô tả**: Định nghĩa cấu trúc cơ sở dữ liệu sử dụng SQLModel (kết hợp giữa Pydantic và SQLAlchemy).
- **Các thực thể (Entities)**:
  - **User**: Lưu trữ thông tin người dùng (username, name, hashed_password, role_id, status, created_at, updated_at).
  - **Role**: Định nghĩa vai trò của người dùng (name, skill).
  - **Project**: Quản lý thông tin dự án (name, description, path, config_override, created_at, updated_at, status, user_id). Mỗi dự án có một người quản lý (Project Manager - PM). Trường `path` lưu tên thư mục tương đối (duy nhất, không khoảng trắng, chỉ bao gồm chữ cái, số, gạch dưới, gạch ngang, dấu chấm).
  - **Phase**: Quản lý các giai đoạn thực hiện của dự án (mission, project_id, role_id, user_id, skill, status, logging, tokens, order, created_at, updated_at). Các trạng thái bao gồm: `Pending`, `Start`, `Processing`, `Processed`, `Cancel`, `Done`.
  - **Execution**: Quản lý các lần thực thi của một Phase (phase_id, project_id, status, start_date, total_input_tokens, total_output_tokens, total_reasoning_tokens, total_cost, cache_read_tokens, cache_write_tokens, cache_hit_percent, latency, model_name). Trường `project_id` là foreign key trực tiếp đến `project.id`, giúp xác định Execution thuộc Project nào mà không cần join qua Phase. Khi tạo Execution mới, `project_id` luôn được set đồng thời với `phase_id`.
  - **ExecutionMessage**: Lưu trữ lịch sử hội thoại và log của mỗi lần thực thi (execution_id, role, content, metrics).

### 2.6. Khối Cơ sở dữ liệu (Database Core)
- **Vị trí**: `app/core/database.py`
- **Mô tả**: Quản lý kết nối đến cơ sở dữ liệu SQLite (`system.db`).
- **Thành phần**:
  - Khởi tạo Engine kết nối.
  - Cung cấp Session cho các thao tác truy vấn dữ liệu.

### 2.7. Khối Tiện ích và Khởi tạo (Scripts)
- **Vị trí**: `scripts/init_db.py`
- **Mô tả**: Script dùng để khởi tạo cấu trúc bảng trong cơ sở dữ liệu và tạo dữ liệu mẫu (seed data) ban đầu khi triển khai hệ thống.

### 2.8. Khối Quản lý Người dùng (User Management)
- **Vị trí**: `app/routers/users.py`
- **Mô tả**: Cung cấp các chức năng quản lý người dùng dành cho Admin.
- **Thành phần**:
  - Danh sách người dùng với phân trang (10 users/page).
  - Tìm kiếm theo `username` hoặc `name`.
  - Lọc theo trạng thái `status`.
  - Thêm mới người dùng qua modal popup (yêu cầu `username` duy nhất).
  - Chỉnh sửa thông tin người dùng qua modal popup.


### 2.9. Khối Quản lý Dự án (Project Management)
- **Vị trí**: `app/routers/projects.py`
- **Mô tả**: Cung cấp các chức năng quản lý danh sách dự án dành cho Admin.
- **Thành phần**:
  - Danh sách dự án với phân trang.
  - Tìm kiếm theo `name` hoặc `description`.
  - Lọc theo trạng thái `status`.
  - Thêm mới dự án qua modal popup.
  - Chỉnh sửa dự án qua modal popup.
  - Xóa dự án.



### 2.10. Khối Hoạt động của Tôi (My Activity)
- **Vị trí**: `app/routers/activity.py`
- **Mô tả**: Cung cấp giao diện tập trung cho các nhiệm vụ mà người dùng hiện tại được giao phụ trách.
- **Thành phần**:
  - Truy vấn các dự án mà người dùng tham gia ít nhất một giai đoạn (Phase).
  - Sắp xếp dự án theo thời gian tạo mới nhất.


### 2.11. Khối Quản lý Role-Skill (Role Management)
- **Vị trí**: `app/routers/roles.py`
- **Mô tả**: Cung cấp các chức năng quản lý vai trò (Role) và kỹ năng (Skill) đi kèm dành cho Admin.
- **Thành phần**:
  - Danh sách các Role.
  - Thêm mới Role qua modal popup (yêu cầu `name` duy nhất).
  - Chỉnh sửa thông tin Role qua modal popup (tên, skill).
  - Xóa Role (chỉ khi Role chưa được gán cho bất kỳ người dùng nào).
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
- **Phần Project**: Liệt kê danh sách các Dự án (Projects) mà người dùng là Project Manager (PM) dưới dạng các thẻ (cards) có độ cao cố định, mỗi hàng 4 thẻ. Nội dung dài sẽ được cắt bớt. Thẻ có màu nền xanh dương nhạt.
- **Phần Activity**: Liệt kê danh sách các Giai đoạn (Phases) mà người dùng được gán vào, sắp xếp theo thời gian cập nhật mới nhất. Hiển thị dưới dạng các thẻ (cards) có độ cao cố định tương tự phần Project, mỗi hàng 4 thẻ. Thẻ có màu nền xanh lá nhạt. Mỗi thẻ hiển thị rõ trạng thái (Status) của Phase. Khi click vào thẻ, người dùng sẽ được chuyển hướng trực tiếp đến màn hình Thực thi (Execution) của Phase đó thay vì màn hình chi tiết Project.

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
- Thêm mới người dùng qua modal popup với các thông tin: username, name, password, role, status.
- Sửa đổi thông tin người dùng hiện có qua modal popup.
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
  - Xem chi tiết toàn bộ các trường của Phase (Mission, Skill, Status, Conversation, Metrics) cùng thông tin Dự án liên quan qua nút "Details". Tại đây, hệ thống cung cấp các nút thao tác dựa trên vai trò:
    - **Start**: Chuyển trạng thái giữa `Pending` và `Start`. Chỉ kích hoạt khi Phase ở trạng thái `Pending` hoặc `Start`.
    - **Approve**: Chuyển trạng thái giữa `Processed` và `Done`. Chỉ kích hoạt khi Phase ở trạng thái `Processed` hoặc `Done`.
    - **Cancel**: Chuyển trạng thái thành `Cancel` bất cứ lúc nào (có cảnh báo xác nhận). Khi đã `Cancel`, nút sẽ bị vô hiệu hóa.
  - **Skill**: Lấy từ `role.skill` tương ứng với role của phase.
  - **Conversation**: Thay thế phần "Logging" cũ, hiển thị link "View Conversation". Khi nhấn vào sẽ mở modal popup danh sách tin nhắn giữa user và agent (tương tự màn hình Execution).
  - **Status Color**: Trạng thái Phase được tô màu tương ứng (Pending: xám, Start: vàng, Processing: xanh dương, Processed: xanh lá, Done: xanh ngọc, Cancel: đỏ).
    - Nếu người dùng là PM của dự án: Có các nút **Cancel**, **Approve**, **Init**.
    - Nếu người dùng được gán cho phase đó: Có nút **Execute** dẫn sang trang thực thi (Execution).
  - Thêm mới Phase vào dự án: Nhập Order, Mission, Chọn Role và User (tùy chọn).
  - Ràng buộc khi thêm Phase: Không cho phép thêm Phase có `order` nhỏ hơn một Phase đã bắt đầu (status khác `Pending`).
  - Chỉnh sửa Phase: Chỉ cho phép chỉnh sửa các Phase đang ở trạng thái `Pending`.
  - Cảnh báo: Hệ thống hiển thị cảnh báo (non-blocking) qua thông báo alert nếu người dùng được gán cho Phase có vai trò (Role) không khớp với vai trò yêu cầu của Phase đó.

### 3.7. Chức năng Quản lý Dự án (Project Management - Admin Only)
- Chỉ hiển thị menu "Projects" cho người dùng có vai trò `Admin`.
- Truy cập tại route `/projects`.
- Cho phép tìm kiếm dự án theo `name` hoặc `description`.
- Cho phép lọc danh sách dự án theo trạng thái.
- Hỗ trợ phân trang danh sách dự án.
- Thêm mới dự án qua modal popup (không chuyển hướng trang). Yêu cầu `path` phải là duy nhất và chỉ chứa: chữ cái, số, gạch dưới, gạch ngang, dấu chấm. Không chứa khoảng trắng hay ký tự đặc biệt khác.
- Chỉnh sửa dự án qua modal popup. Ràng buộc về `path` tương tự như khi thêm mới.
- Xóa dự án (có xác nhận).
- Tự động cập nhật trường `updated_at` mỗi khi chỉnh sửa dự án.


### 3.8. Chức năng Hoạt động của Tôi (My Activity)
- Truy cập tại route `/my-activity` (yêu cầu đã đăng nhập).
- Liệt kê các Dự án (Projects) mà người dùng hiện tại được gán vào ít nhất một giai đoạn (Phase).
- Các dự án được sắp xếp theo thứ tự `created_at` giảm dần.
- Với mỗi dự án, hiển thị danh sách các giai đoạn (Phases) dưới dạng danh sách các thẻ (cards) full-width, sắp xếp theo `order`.
- Thông tin mỗi giai đoạn bao gồm: Thứ tự (Order), Nhiệm vụ (Mission), Trạng thái (Status), Người thực hiện (Assigned User).
- Phân biệt hiển thị qua thẻ:
    - Nếu giai đoạn do chính người dùng hiện tại phụ trách: Thẻ có viền nổi bật, có nút **Execute** và font chữ bình thường đẻ điều hướng sang Execution.
    - Nếu giai đoạn do người khác phụ trách: Thẻ được làm mờ (opacity) và font chữ nhạt hơn để dễ phân biệt.


### 3.9. Chức năng Thực thi Giai đoạn (Phase Execution)
- Truy cập khi người dùng nhấn nút **Execute** tại trang chi tiết Phase hoặc trang "My Activity".
- Giao diện có menu điều hướng tương tự như các trang khác, giúp người dùng dễ dàng di chuyển giữa các chức năng.
- **Thành phần giao diện**:
    - **Thông tin tóm tắt**: Hiển thị tên Dự án, Đường dẫn Workspace và Trạng thái hiện tại của Phase.
    - **Nhiệm vụ (Mission)**: Hiển thị chi tiết nội dung nhiệm vụ cần thực hiện và Skill của Role.
    - **Thanh Metrics**: Hiển thị các chỉ số tổng hợp của các lần thực thi (Token In, Token Out, Reasoning, Cache Read, Cache Hit, Avg Latency, Total Cost).
    - **Form thực thi**:
        - Ô nhập **Prompt** (TextArea full-width). Sau khi nhấn nút Execute và thực thi thành công, nội dung ô Prompt sẽ tự động được xóa bỏ.
        - Dropdown chọn **Model** (gemini-3-flash-preview, openai-gpt-5.4-mini).
        - Nút **Execute** để bắt đầu chạy Agent. Nút này chỉ được kích hoạt (enabled) khi Phase ở trạng thái `Start` hoặc `Processing`. Nếu ở trạng thái khác, nút sẽ bị vô hiệu hóa (disabled, màu xám) và hiển thị ghi chú "Wrong phase status" bên cạnh.
        - Link **Make Processed**: Hiển thị bên trái link "Force complete" khi Phase ở trạng thái `Start` hoặc `Processing`. Khi nhấn vào, hệ thống yêu cầu xác nhận trước khi chuyển trạng thái của Phase thành `Processed`.
        - Nút **Conversation** để mở modal xem lịch sử hội thoại và chi tiết metrics của từng tin nhắn.
        - **Log Console**: Ô hiển thị log quá trình thực thi với giao diện kiểu terminal/console, được stream realtime qua Server-Sent Events (SSE).
- **Cơ chế hoạt động**:
    - Sử dụng `openhands.sdk` (Agent, LLM, LocalConversation, LocalWorkspace) để thực thi nhiệm vụ.
    - Khi người dùng nhấn **Execute**, nếu Phase đang ở trạng thái `Start`, hệ thống sẽ tự động chuyển trạng thái sang `Processing`.
    - Quá trình thực thi chạy ngầm (background task) và ghi log ra file.
    - Giao diện web liên tục cập nhật trạng thái và metrics thông qua polling (AJAX) và stream log (SSE).
    - Lưu trữ toàn bộ tin nhắn (user, agent) và metrics (token, cost, latency) vào cơ sở dữ liệu (`Execution`, `ExecutionMessage`).


### 3.10. Chức năng Quản lý Role-Skill (Role Management - Admin Only)
- Chỉ hiển thị menu "Role-Skill" cho người dùng có vai trò `Admin`.
- Truy cập tại route `/roles`.
- Hiển thị danh sách các Role hiện có trong hệ thống.
- Thêm mới Role qua modal popup: Nhập tên Role (duy nhất) và Skill (tùy chọn).
- Chỉnh sửa Role qua modal popup: Cho phép thay đổi tên và Skill.
- Xóa Role: Chỉ cho phép xóa nếu Role đó không được gán cho bất kỳ người dùng nào. Nếu có người dùng đang mang Role này, hệ thống sẽ từ chối xóa.


### 3.11. Chức năng File Explorer
- Truy cập thông qua liên kết "File Explorer" ở góc phải tiêu đề dự án tại trang "My Activity" hoặc trang "Execution".
- Cho phép người dùng duyệt qua các thư mục và file trong thư mục gốc của dự án (`{settings.PROJECT_ROOT}/{project.path}`).
- Hiển thị danh sách thư mục và file, trong đó thư mục được xếp lên trên, sau đó đến file, tất cả được sắp xếp theo thứ tự bảng chữ cái.
- Hỗ trợ điều hướng vào các thư mục con thông qua breadcrumbs.
- Cho phép xem nội dung các file text trực tiếp trên trình duyệt (chỉ xem, không chỉnh sửa).
- Tích hợp cơ chế bảo mật để ngăn chặn directory traversal (chỉ cho phép truy cập trong phạm vi thư mục dự án).
- **Tính năng Upload**: Cho phép tải file lên thư mục hiện tại. Chỉ hỗ trợ các định dạng: docx, pdf, txt, md, csv, jpg, png, jpeg, gif.
- **Tính năng Download**: Cho phép tải file hoặc toàn bộ thư mục (dưới dạng file zip) về máy. Nếu tải từ thư mục gốc của dự án, hệ thống sẽ tự động loại bỏ các file/thư mục được khai báo trong `.gitignore` (sử dụng lệnh `rsync`).
- **Tính năng Delete**: Cho phép xóa file hoặc thư mục (có hộp thoại xác nhận trước khi xóa).
- **Tính năng Create Folder**: Cho phép tạo thư mục mới trong thư mục hiện tại.
## 4. Môi trường triển khai
- **Ngôn ngữ**: Python 3
- **Cơ sở dữ liệu**: SQLite
- **Quản lý tiến trình**: Hỗ trợ chạy trực tiếp qua Python hoặc sử dụng PM2 (`ecosystem.config.js`) cho môi trường production.

## 5. Storage Structure
- `$OPENHANDS_STORAGE_PATH/{project_id}/{phase_id}/sessions/`: Stores OpenHands session data.
- `$OPENHANDS_STORAGE_PATH/{project_id}/{phase_id}/logs/`: Stores execution logs.

## 6. Metrics JSON Structure
```json
{
  "prompt_tokens": 100,
  "completion_tokens": 50,
  "reasoning_tokens": 10,
  "cached_tokens_read": 0,
  "cached_tokens_creation": 0,
  "latency": 1.5,
  "model_name": "gpt-4o",
  "provider": "openai"
}
```
