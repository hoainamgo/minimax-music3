@echo off
chcp 65001 >nul
echo =======================================================
echo   Khởi chạy REST API Gateway MiniMax Music 3
echo   (Cổng 8000 -> Sẵn sàng kết nối Internet Tunnel)
echo =======================================================

cd /d "%~dp0"
python api_server.py
pause
