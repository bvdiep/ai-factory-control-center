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

## Cấu trúc dự án
- `app/main.py`: Entry point của ứng dụng FastHTML.
- `app/models/__init__.py`: Định nghĩa các bảng dữ liệu bằng SQLModel.
- `app/core/database.py`: Cấu hình kết nối cơ sở dữ liệu.
- `app/core/auth.py`: Xử lý xác thực người dùng.
- `scripts/init_db.py`: Script khởi tạo và seed dữ liệu ban đầu.
- `requirements.txt`: Danh sách các thư viện phụ thuộc.
- `ecosystem.config.js`: Cấu hình chạy PM2.
