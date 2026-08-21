@echo off
chcp 65001 >nul
echo =======================================================
echo   Khởi động MiniMax Music 3 Engine (CUDA 16GB VRAM)
echo =======================================================

cd /d "%~dp0"

REM Kiểm tra thư mục models
if not exist "models\MiniMax-Music3-language_model-Q4_K_M.gguf" (
    echo [!] Chưa tìm thấy model trong thư mục models!
    echo [*] Đang chạy script tải model tự động từ Hugging Face...
    python download_models.py
)

echo [*] Khởi động mm-server trên 127.0.0.1:8086...
echo [*] Tối ưu hóa: --keep-loaded (Toàn bộ model nằm trên VRAM 16GB để đạt tốc độ cao nhất)
echo.

set PATH=%~dp0runtime;%PATH%
"%~dp0runtime\mm-server.exe" --models "%~dp0models" --host 127.0.0.1 --port 8086 --keep-loaded --max-batch 1

pause
