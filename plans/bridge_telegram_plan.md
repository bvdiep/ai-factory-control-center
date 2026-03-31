# Kế hoạch triển khai Bridge Telegram - Dify

## Giai đoạn 1: Thiết lập cơ sở dữ liệu và cấu trúc cơ bản
1. Thêm model `BridgeMessage` vào `app/models/__init__.py`.
2. Cập nhật `alembic` để tạo bảng mới trong database.
3. Thêm các biến môi trường cần thiết vào `.env` (TELEGRAM_BOT_TOKEN, DIFY_API_KEY, OPENAI_API_KEY, v.v.).

## Giai đoạn 2: Triển khai luồng chat text cơ bản
1. Tạo `app/services/telegram_service.py` để xử lý webhook và gửi tin nhắn.
2. Tạo `app/services/dify_service.py` để gọi API chat của Dify.
3. Tạo `app/routers/telegram.py` để nhận webhook từ Telegram.
4. Xử lý logic: Nhận tin nhắn text từ Telegram -> Lưu vào DB -> Gửi sang Dify -> Nhận phản hồi từ Dify -> Lưu vào DB -> Gửi lại Telegram.

## Giai đoạn 3: Xử lý hình ảnh với VLM (litellm)
1. Cập nhật `telegram_service.py` để tải ảnh từ Telegram.
2. Tạo `app/services/llm_service.py` sử dụng `litellm` để gọi model multimodal (ví dụ: `gpt-4o` hoặc `claude-3-5-sonnet-20240620`) để lấy mô tả ảnh.
3. Cập nhật logic webhook: Nhận ảnh -> Tải ảnh -> Gửi qua VLM lấy mô tả -> Ghép mô tả và caption -> Gửi sang Dify -> Nhận phản hồi -> Gửi lại Telegram.

## Giai đoạn 4: Tích hợp với Project và Routing (Tương lai)
1. Thêm logic để xác định Project dựa trên chat_id hoặc command từ Telegram.
2. Thêm logic routing để chọn Dify App dựa trên Project hoặc Phase.
