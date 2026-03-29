FROM python:3.12-slim

# 1. Cài đặt công cụ hệ thống & Playwright Dependencies (Full list)
# Đảm bảo có đầy đủ các thư viện share (.so) để Chromium không bị crash khi chạy
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    libffi-dev \
    docker.io \
    rsync \
    zip \
    # --- Playwright System Dependencies ---
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Cài đặt Docker Compose V2 (DooD - Docker out of Docker)
RUN mkdir -p /usr/local/lib/docker/cli-plugins/ && \
    curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose && \
    ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

WORKDIR /app

# 3. Nâng cấp bộ cài đặt Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 4. Cài đặt thư viện Python & Playwright
COPY requirements.txt .
# Chúng ta cài 'playwright' trực tiếp ở đây để chắc chắn lệnh ở bước 5 hoạt động
RUN pip install --no-cache-dir playwright && \
    pip install --no-cache-dir --prefer-binary -r requirements.txt

# 5. Cài đặt Chromium Browser và các dependencies hệ thống bổ sung của nó
# Lệnh 'install-deps' sẽ đảm bảo không sót bất kỳ thư viện nào từ bước 1
RUN python -m playwright install chromium && \
    python -m playwright install-deps chromium

# 6. Copy mã nguồn vào container
COPY . .

# 7. Chạy ứng dụng (Đảm bảo đường dẫn app/main.py là chính xác)
CMD ["python", "app/main.py"]