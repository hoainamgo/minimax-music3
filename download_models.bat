@echo off
chcp 65001 >nul
echo =======================================================
echo   Tải Model MiniMax Music 3 GGUF (Cho VGA 16GB)
echo =======================================================

cd /d "%~dp0"
pip install -r requirements.txt
python download_models.py
pause
