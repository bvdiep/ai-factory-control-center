#7

# MISSION: TÍCH HỢP OPENHANDS SDK VÀO AI-FACTORY-CONTROL-CENTER (EXTENDED METRICS)

**Context**: 
Chúng ta đang xây dựng màn hình Execution cho hệ thống AI Factory (url `/projects/{project_id}/phases/{phase_id}/execution`). Nhiệm vụ của bạn là triển khai logic gọi OpenHands SDK từ FastHTML để thực hiện các task tự động hóa, đảm bảo tính bền vững (persistence) và hiển thị thời gian thực với hệ thống logging/metrics chi tiết.

**Target Codebase**: `/home/dd/work/diep/ai-factory-control-center`
**Tech Stack**: FastHTML, OpenHands SDK, LiteLLM, SQLite, WebSockets.

## 1. SETUP & DEPENDENCIES
- Cập nhật `requirements.txt`: `openhands-sdk`, `litellm`, `python-dotenv`.
- Cập nhật `env.sample`: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `OPENHANDS_STORAGE_PATH`.
- Khởi tạo cấu trúc thư mục lưu trữ: `$OPENHANDS_STORAGE_PATH/{project_id}/{phase_id}/` chứa 2 thư mục con là `sessions/` và `logs/`.

## 2. DATABASE SCHEMA (OPTIMIZED FOR INSIGHTS)
- **Table `executions`**: `id`, `phase_id`, `status`, `start_date`, `total_input_tokens`, `total_output_tokens`, `total_reasoning_tokens`, `total_cost`.
- **Table `execution_messages`**: 
    - `id`, `execution_id`, `role`, `content`.
    - `metrics` (JSON): Lưu trữ chi tiết nhất có thể: 
        - `prompt_tokens`, `completion_tokens`.
        - `reasoning_tokens` (đặc biệt quan trọng cho Gemini 3.1 Pro/o1).
        - `cached_tokens_read`, `cached_tokens_creation`.
        - `latency` (TTFT - Time to first token, total duration).
        - `model_name`, `provider`.
- **Lưu ý**: Tuyệt đối không lưu raw terminal logs vào SQLite để tránh quá tải, sử dụng file log vật lý.

## 3. LOGIC THỰC THI & STORAGE
- **LiteLLM Integration**: Cấu hình OpenHands qua LiteLLM. Truyền `Model`, `Temperature`, `System prompt`, `User prompt` từ form. 
- **Persistence**: 
    - Sử dụng `FileStore` tại `$OPENHANDS_STORAGE_PATH/{project_id}/{phase_id}/sessions/`.
    - Kiểm tra và tái sử dụng `session_id` cũ nếu tồn tại để duy trì trạng thái Agent.
- **Advanced Logging**: 
    - **WebSocket Stream**: Đẩy trực tiếp mọi event (stdout, tool_call, observation) lên UI Terminal.
    - **Append-to-File**: Lưu mọi event vào `$OPENHANDS_STORAGE_PATH/{project_id}/{phase_id}/logs/{execution_id}.log`. Mỗi lần Agent hành động (action) hoặc nhận phản hồi từ hệ thống (observation) đều phải ghi kèm timestamp.
- **Message Catching**: Lưu response cuối cùng của Agent vào `execution_messages`.

## 4. METRICS EXTRACTION (LƯU TỐI ĐA DỮ LIỆU)
Sau mỗi turn tương tác, cần trích xuất từ LiteLLM/OpenHands:
- **Usage Metadata**: Trích xuất toàn bộ object `usage` từ LiteLLM response (bao gồm các trường legacy và các trường mới như `reasoning_tokens`, `cache_hit_tokens`).
- **Cost Calculation**: Tính toán chi phí dựa trên token thực tế (nếu SDK hỗ trợ hoặc dùng hàm helper).
- **Step Tracking**: Đếm số bước (steps) mà Agent đã thực hiện trong turn đó trước khi trả lời user.

## 5. RESUME & DOCUMENTATION
- **Resume**: Nút Resume phải khôi phục lại Session từ đĩa, đồng thời đọc `N` dòng cuối từ file `.log` để "re-hydrate" giao diện Console trên Browser.
- **Documentation**: Cập nhật `/plans/technical_document.md` chi tiết về:
    - Sơ đồ lưu trữ file logs/sessions.
    - Cấu trúc JSON của trường `metrics` để phục vụ việc vẽ biểu đồ sau này.

**Yêu cầu**: Code sạch, xử lý exception cẩn thận (đặc biệt là lỗi kết nối SDK/LLM), bổ sung comment tiếng Việt trong code.