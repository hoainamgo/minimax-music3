@echo off
chcp 65001 >nul
echo =======================================================
echo   Khởi chạy MiniMax Music 3 Desktop GUI
echo   (Client trên PC - Kết nối Lightning.ai Backend)
echo =======================================================

cd /d "%~dp0"
python music_gui.py
