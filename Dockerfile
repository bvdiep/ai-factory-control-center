FROM python:3.12-slim

# 1. Cài đặt các công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 2. Thêm Repository chính thức của Docker để cài Docker Compose V2
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    chmod a+r /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Cài đặt Docker CLI và Docker Compose Plugin
RUN apt-get update && apt-get install -y \
    docker-ce-cli \
    docker-compose-plugin \
    && rm -rf /var/lib/apt/lists/*

# 4. Tạo alias để lệnh 'docker-compose' vẫn hoạt động (nếu code của bạn dùng dấu gạch ngang)
RUN ln -s /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

WORKDIR /app

# 5. Cài đặt Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Đảm bảo đường dẫn này khớp với cấu trúc thư mục của bạn
CMD ["python", "app/main.py"]