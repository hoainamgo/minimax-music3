# 🎵 MiniMax Music 3 - Full Stack AI Music Studio

Hệ thống tạo nhạc AI chất lượng cao toàn diện:
- **Backend (Cloud GPU trên Lightning.ai):** Cung cấp CUDA inference engine (`minimaxmusic.cpp` GGUF 16GB VRAM) và FastAPI REST API Gateway kết nối qua `https://apimusic.ksmart.com.es`.
- **Client (Trên PC cá nhân):** Bao gồm Desktop GUI hiện đại và Command-Line Interface (CLI) để gửi yêu cầu và tự động tải file bài hát hoàn chỉnh về máy tính.

---

## 🖥️ 1. Hướng Dẫn Sử Dụng Trên PC Cá Nhân (Client)

### 🔹 Cách 1: Sử dụng Desktop GUI (Giao diện đồ họa)
Nhấp đúp vào **`run_gui.bat`** (hoặc chạy `python music_gui.py`):
- **Trạng thái Server:** Hiển thị trực quan kết nối tới `https://apimusic.ksmart.com.es` (Xanh/Đỏ).
- **Mẫu phong cách nhanh:** Pop Ballad, EDM Dance, Acoustic, Epic Cinematic, v.v.
- **Trình soạn thảo lời (Lyrics):** Nút chèn nhanh cấu trúc `[verse]`, `[chorus]`, `[bridge]`, `[outro]`.
- **Tiến trình sinh nhạc:** Thanh phần trăm động, không bị đơ giao diện.
- **Tự động tải & Phát nhạc:** Nút **"▶️ Phát Bài Hát"** và **"📂 Mở Thư Mục"** (mặc định lưu tại thư mục `Music/MiniMax_AI`).

### 🔹 Cách 2: Sử dụng CLI (Dòng lệnh & Wizard hỏi đáp)
- **Chế độ Wizard hỏi đáp từng bước:** Nhấp đúp vào **`run_cli.bat`** (hoặc `python music_cli.py wizard`).
- **Tạo nhanh 1 dòng lệnh:**
  ```bash
  python music_cli.py generate --title "Summer Vibe" --style "Tropical House, sunny acoustic guitar, female vocal" --duration 120
  ```
- **Kiểm tra kết nối backend:**
  ```bash
  python music_cli.py health
  ```

---

## ☁️ 2. Triển Khai Backend Trên Lightning.ai (1-Click)

Chi tiết từng bước cấu hình Cloud GPU (L4 24GB / T4 16GB) và Cloudflare Tunnel tới `apimusic.ksmart.com.es` đã được lưu tại:
👉 [DEPLOY_LIGHTNING_AI.md](file:///c:/Apps/23.%20Music%20OS/DEPLOY_LIGHTNING_AI.md)

Tóm tắt lệnh chạy trên Lightning Studio:
```bash
# 1. Cài đặt tự động engine & tải model
bash lightning_setup.sh

# 2. Khởi chạy Inference Engine (Terminal 1)
bash start_server_linux.sh

# 3. Khởi chạy API Gateway (Terminal 2)
bash start_api_linux.sh

# 4. Khởi chạy Cloudflare Tunnel (Terminal 3)
cloudflared tunnel run --token <YOUR_TOKEN>
```

---

## 📁 3. Cấu Trúc Thư Mục Dự Án

```
c:\Apps\23. Music OS\
├── music_gui.py             # Desktop GUI Client hiện đại trên PC
├── run_gui.bat              # Kích hoạt 1-click Desktop GUI
├── music_cli.py             # CLI Client & Wizard hỏi đáp trên PC
├── run_cli.bat              # Kích hoạt 1-click CLI Wizard
├── remote_client.py         # Module kết nối API https://apimusic.ksmart.com.es
├── api_server.py            # FastAPI REST Gateway (Chạy trên backend)
├── DEPLOY_LIGHTNING_AI.md   # Hướng dẫn chi tiết triển khai Cloud Lightning.ai
├── lightning_setup.sh       # Script 1-click build & setup cho Linux Lightning.ai
├── start_server_linux.sh    # Khởi động Engine trên Linux
├── start_api_linux.sh       # Khởi động API trên Linux
├── runtime/                 # Nhân nhị phân CUDA mm-server.exe
├── download_models.py       # Tải 5 model GGUF (Tối ưu 16GB VRAM)
├── requirements.txt         # Thư viện Python phụ thuộc
└── README.md                # Tài liệu tổng hợp
```
