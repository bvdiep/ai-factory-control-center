# AI Factory Control Center

Hệ thống quản lý điều khiển cho AI Factory, xây dựng bằng FastHTML và SQLModel.

## Cài đặt

### Yêu cầu hệ thống
- Python 3.x
- `rsync` và `zip` (để hỗ trợ tính năng nén và tải thư mục trong File Explorer).
  - Ubuntu/Debian: `sudo apt-get install rsync zip`
  - MacOS: `brew install rsync zip`

1. Tạo môi trường ảo (virtual environment):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

3. Khởi tạo cơ sở dữ liệu:
```bash
python scripts/init_db.py
```

## Chạy ứng dụng

### Chạy trực tiếp
```bash
python app/main.py
```
Ứng dụng sẽ chạy mặc định tại `http://localhost:5001` (hoặc cổng cấu hình trong FastHTML).

### Chạy với PM2
Nếu bạn muốn chạy ứng dụng trong môi trường production, hãy sử dụng PM2:
```bash
pm2 start ecosystem.config.js
```

### Build Docker
```bash
docker compose build --no-cache
docker compose up -d
```

### Clean build docker
```bash
docker builder prune -a
```

## Tích hợp Telegram - Dify Bridge

Hệ thống hỗ trợ tính năng Bridge (cầu nối) giữa Telegram và Dify, cho phép người dùng chat với Dify Agent trực tiếp thông qua Telegram Bot.

### Cách thức hoạt động của luồng Telegram - Dify:
1. **Nhận tin nhắn (Polling)**: Khi server khởi động, một tiến trình chạy ngầm (background task) sẽ liên tục gọi API `getUpdates` của Telegram để lấy các tin nhắn mới nhất gửi đến Bot.
2. **Xử lý tin nhắn**:
   - **Tin nhắn Text**: Hệ thống lưu tin nhắn vào database (`BridgeMessage`), sau đó gửi nội dung sang Dify thông qua API `chat-messages`.
   - **Tin nhắn Hình ảnh**: Hệ thống tải ảnh từ Telegram, sử dụng mô hình VLM (Vision-Language Model, mặc định là `gpt-4o` qua `litellm`) để trích xuất mô tả chi tiết của bức ảnh. Sau đó, hệ thống ghép mô tả này cùng với caption (nếu có) và gửi sang Dify.
3. **Nhận phản hồi từ Dify**: Hệ thống chờ Dify xử lý và trả về câu trả lời (chế độ blocking).
4. **Gửi lại Telegram**: Câu trả lời từ Dify được lưu vào database và gửi ngược lại cho người dùng trên Telegram thông qua API `sendMessage`.

### Cấu hình Bridge
Để kích hoạt tính năng này, bạn cần cấu hình các biến môi trường sau trong file `.env` (hoặc truyền qua `docker-compose.yaml`):

```env
# Token của Telegram Bot (lấy từ @BotFather)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# API Key của ứng dụng Dify (loại Chat App)
DIFY_API_KEY=your-dify-api-key

# URL của Dify API (mặc định: https://api.dify.ai/v1)
DIFY_API_URL=https://api.dify.ai/v1

# Model VLM dùng để đọc ảnh (mặc định: gpt-4o)
VLM_MODEL=gpt-4o

# API Key cho model VLM (ví dụ OpenAI)
OPENAI_API_KEY=your-openai-api-key
```

*Lưu ý: Ngay khi bạn khởi động server (qua `python app/main.py` hoặc Docker) và có cấu hình `TELEGRAM_BOT_TOKEN`, tiến trình polling sẽ tự động chạy và luồng chat sẽ được thông suốt.*

## Cấu trúc dự án
- `app/main.py`: Entry point của ứng dụng FastHTML.
- `app/models/__init__.py`: Định nghĩa các bảng dữ liệu bằng SQLModel.
- `app/core/database.py`: Cấu hình kết nối cơ sở dữ liệu.
- `app/core/auth.py`: Xử lý xác thực người dùng.
- `scripts/init_db.py`: Script khởi tạo và seed dữ liệu ban đầu.
- `requirements.txt`: Danh sách các thư viện phụ thuộc.
- `ecosystem.config.js`: Cấu hình chạy PM2.
