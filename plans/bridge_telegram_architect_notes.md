# Bridge Telegram - Dify Architecture Notes

## Mục tiêu
Xây dựng một bridge giữa Telegram và Dify để:
- Nhận và trả dữ liệu giữa hai nền tảng.
- Lưu trữ toàn bộ tin nhắn của hai bên.
- Xử lý trước các tin nhắn media (photo, audio, video) hoặc document từ Telegram (sử dụng LLM/VLM qua litellm để trích xuất dữ liệu).
- Tương tác với dữ liệu hiện tại (Project, Phase...).
- Forward/routing giữa các apps khác nhau trong Dify.

## Đánh giá kiến trúc hiện tại
- Hệ thống hiện tại sử dụng FastHTML và SQLModel.
- Các model hiện có: `User`, `Role`, `Project`, `Phase`, `Execution`, `ExecutionMessage`.
- Cần thêm một model mới để lưu trữ tin nhắn từ Telegram/Dify, gọi là `BridgeMessage`. Model này cần liên kết với `Project`.

## Đề xuất thiết kế cấu trúc code
1. **Database Models**:
   - Thêm model `BridgeMessage` vào `app/models/__init__.py`.
   - Thuộc tính: `id`, `project_id`, `sender` (telegram/dify), `message_type` (text/image/audio/video/document), `content` (text content hoặc file path), `extracted_data` (dữ liệu trích xuất từ VLM/LLM), `created_at`.

2. **Routers**:
   - Tạo `app/routers/telegram.py` để xử lý webhook từ Telegram.
   - Tạo `app/routers/dify.py` để xử lý webhook/API từ Dify (nếu cần) hoặc tích hợp logic gọi Dify API vào trong xử lý Telegram.

3. **Services**:
   - Tạo `app/services/telegram_service.py`: Xử lý gửi/nhận tin nhắn Telegram, tải file media.
   - Tạo `app/services/dify_service.py`: Xử lý gọi API của Dify (chat messages).
   - Tạo `app/services/llm_service.py`: Sử dụng `litellm` để gọi các model VLM/LLM trích xuất thông tin từ ảnh/media.

4. **Ảnh hưởng đến kiến trúc hiện tại**:
   - Không làm thay đổi các luồng hiện tại.
   - Chỉ thêm các bảng mới trong database và các endpoint mới cho webhook.
   - Cần cấu hình biến môi trường cho Telegram Bot Token, Dify API Key, và các API Key cho LLM (OpenAI, Anthropic, v.v. qua litellm).
