# ⚡ Hướng Dẫn Triển Khai MiniMax Music 3 Trên Lightning.ai

Tài liệu này hướng dẫn bạn đưa toàn bộ hệ thống MiniMax Music 3 lên **Lightning.ai Studio (GPU L4 24GB, T4 16GB hoặc A10G 24GB)** và kết nối với domain **`apimusic.ksmart.com.es`**.

---

## 🖥️ 1. Khởi Tạo Studio trên Lightning.ai

1. Đăng nhập vào [Lightning.ai](https://lightning.ai).
2. Tạo một **Studio mới** (hoặc chọn Studio đang có).
3. Tại mục chọn phần cứng (Hardware), chọn:
   - **NVIDIA L4 (24GB VRAM)** (Khuyến nghị tốt nhất, tối ưu chi phí & tốc độ).
   - Hoặc **NVIDIA T4 (16GB VRAM)** / **A10G (24GB VRAM)**.

---

## 📦 2. Đưa Mã Nguồn Lên Lightning.ai Studio

Trong giao diện Terminal của Lightning Studio, clone repo của bạn:
```bash
git clone <URL_REPO_CUA_BAN> music-os
cd music-os
```

Hoặc tải zip mã nguồn từ máy tính lên thư mục Studio.

---

## ⚙️ 3. Chạy Cài Đặt Tự Động (1-Click)

Chạy script cài đặt môi trường, biên dịch engine CUDA cho Linux và tải bộ 5 model GGUF (tối ưu 16GB):
```bash
bash lightning_setup.sh
```

Quá trình này sẽ:
1. Cài đặt các gói build `cmake`, `build-essential`.
2. Tự động biên dịch `minimaxmusic.cpp` với cờ `GGML_CUDA=ON` tạo file nhị phân `runtime/mm-server`.
3. Tải bộ 5 weights GGUF từ Hugging Face vào thư mục `models/`.

---

## ▶️ 4. Khởi Động Hệ Thống

Mở 2 tab Terminal trên Lightning Studio:

### Terminal 1: Chạy Inference Engine
```bash
bash start_server_linux.sh
```
*(Engine sẽ nạp toàn bộ 5 model lên GPU VRAM và lắng nghe tại cổng `8086`)*

### Terminal 2: Chạy API Gateway
```bash
bash start_api_linux.sh
```
*(FastAPI Gateway sẽ lắng nghe tại cổng `0.0.0.0:8000`)*

---

## 🌐 5. Kết Nối Cloudflare Tunnel Tới `apimusic.ksmart.com.es`

Trong Terminal thứ 3 của Lightning Studio:

1. Tải và cài đặt `cloudflared` trên Linux:
```bash
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

2. Chạy tunnel với token của bạn từ Cloudflare Zero Trust Dashboard:
```bash
cloudflared tunnel run --token <YOUR_CLOUDFLARE_TUNNEL_TOKEN>
```

> **Lưu ý cấu hình Cloudflare Dashboard:**
> - **Public Hostname:** `apimusic.ksmart.com.es`
> - **Service:** `HTTP://localhost:8000`

---

## ✅ 6. Kiểm Tra Hoạt Động

Từ máy tính cá nhân hoặc bất kỳ đâu trên Internet:
- **Kiểm tra Health:**
  ```bash
  curl https://apimusic.ksmart.com.es/health
  ```
- **Tài liệu API Swagger:** Truy cập trình duyệt `https://apimusic.ksmart.com.es/docs`
- **Gửi request tạo bài hát:**
  ```bash
  curl -X POST https://apimusic.ksmart.com.es/v1/music/generate \
       -H "Content-Type: application/json" \
       -d '{
         "title": "Song on Cloud",
         "style": "Electronic synthwave, punchy drums, female lead vocals",
         "lyrics": "[verse]\nDriving fast into the night\n[chorus]\nLights are glowing bright",
         "duration": 60
       }'
  ```
