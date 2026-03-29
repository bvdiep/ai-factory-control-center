FROM python:3.12-slim

# 1. Cài đặt các công cụ hệ thống, Docker CLI & Playwright Dependencies
# Thêm các thư viện X11, Gtk, và NSS cần thiết cho Chromium
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
    && rm -rf /var/lib/apt/lists/*

# 2. Cài đặt Docker Compose V2 (Giữ nguyên logic của bạn)
RUN mkdir -p /usr/local/lib/docker/cli-plugins/ && \
    curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose && \
    ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

WORKDIR /app

# 3. Nâng cấp bộ cài đặt Python
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 4. Cài đặt các thư viện từ requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# 5. Cài đặt Chromium Browser thông qua module python
RUN python -m playwright install chromium

# 6. Copy mã nguồn
COPY . .

# 7. Chạy ứng dụng
CMD ["python", "app/main.py"]