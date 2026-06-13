FROM python:3.11-slim

WORKDIR /app

# 安裝 Python 依賴（含 Playwright）
COPY requirements_web.txt ./
RUN pip install --no-cache-dir -r requirements_web.txt

# 安裝 Playwright Chromium 及其系統依賴（--with-deps 自動裝 apt 套件）
RUN apt-get update && \
    playwright install --with-deps chromium && \
    rm -rf /var/lib/apt/lists/*

# 複製應用程式與資料
COPY web/ ./web/
COPY data/ ./data/

# 建立上傳目錄
RUN mkdir -p web/uploads

ENV PUBLIC_MODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--chdir", "/app", "web.app:app"]
