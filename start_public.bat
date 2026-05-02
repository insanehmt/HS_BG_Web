@echo off
echo =============================================
echo  HS BG 圖鑑網站 - 本地公開模式
echo  朋友可透過 http://你的IP:5001 訪問
echo =============================================
echo.

REM 設定 SYNC_TOKEN（請自行修改為安全的密碼）
set SYNC_TOKEN=changeme_please

REM 使用 Docker Compose 啟動
docker compose up --build

pause
