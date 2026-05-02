@echo off
chcp 65001 >nul
title Hearthstone Advisor - 打牌建議
color 0A
cd /d %~dp0
echo.
echo  ============================================
echo   Hearthstone 打牌顧問
echo   請先開啟爐石，進入對戰後自動顯示建議
echo  ============================================
echo.
python run_advisor.py
echo.
echo  程式已結束，按任意鍵關閉...
pause
