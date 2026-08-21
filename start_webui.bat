@echo off
chcp 65001 >nul
echo =======================================================
echo   Khởi chạy Giao diện Web UI MiniMax Music 3
echo =======================================================

cd /d "%~dp0"
python webui.py
pause
