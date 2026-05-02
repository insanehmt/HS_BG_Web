# 輕量版 Docker 映像檔（公開圖鑑頁面用，無爬蟲）
# 本地端使用完整版（含 Playwright）
FROM python:3.11-slim

WORKDIR /app

# 安裝 Python 依賴
COPY requirements_web.txt ./
RUN pip install --no-cache-dir -r requirements_web.txt

# 複製應用程式與資料
COPY web/ ./web/
COPY data/ ./data/

# 建立上傳目錄
RUN mkdir -p web/uploads

# 雲端預設公開模式
ENV PUBLIC_MODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# 以 gunicorn 運行（2 worker，適合免費雲端方案）
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--chdir", "/app", "web.app:app"]
