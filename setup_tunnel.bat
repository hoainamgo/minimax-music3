@echo off
chcp 65001 >nul
echo =======================================================
echo   Cấu hình Cloudflare Tunnel cho apimusic.ksmart.com.es
echo =======================================================

echo.
echo Bước 1: Nếu chưa cài đặt cloudflared:
echo   winget install --id Cloudflare.cloudflared
echo.
echo Bước 2: Chạy tunnel với Token được cấp từ Cloudflare Zero Trust:
echo   cloudflared tunnel run --token ^<YOUR_CLOUDFLARE_TUNNEL_TOKEN^>
echo.
echo Cấu hình Public Hostname trên Cloudflare Dashboard:
echo   - Subdomain: apimusic
echo   - Domain: ksmart.com.es
echo   - Service Type: HTTP
echo   - URL: 127.0.0.1:8000
echo.
pause
