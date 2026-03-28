FROM python:3.12-slim

# 1. Cài đặt các công cụ hệ thống & Docker CLI
# Chúng ta cài 'docker.io' để có lệnh docker điều khiển máy host qua socket
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    libffi-dev \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# 2. Cài đặt Docker Compose V2 (Bản plugin chính thức)
RUN mkdir -p /usr/local/lib/docker/cli-plugins/ && \
    curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose && \
    ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

WORKDIR /app

# 3. Nâng cấp bộ cài đặt Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 4. Cài đặt các thư viện từ máy local
COPY requirements.txt .
# Dùng --prefer-binary để tránh việc pip cố gắng build lại các gói C từ đầu
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# 5. Copy mã nguồn (Giả sử file SQLite 'factory.db' nằm trong app/)
COPY . .

# 6. Chạy ứng dụng (Điều chỉnh đường dẫn main.py cho đúng)
# Nếu file của bạn nằm ở thư mục gốc thì dùng "python main.py"
CMD ["python", "app/main.py"]