# 🎵 MiniMax Music 3 - Local GPU Engine & Internet API Gateway

Kho mã nguồn đóng gói toàn bộ engine suy luận MiniMax Music 3 chạy cục bộ trên GPU NVIDIA (tối ưu hóa đặc biệt cho dòng card **16GB VRAM**), đồng thời tích hợp sẵn **FastAPI REST API Gateway** để gọi trực tiếp từ Internet thông qua domain **`apimusic.ksmart.com.es`**.

---

## 🌐 1. Cấu Trúc API Internet (`apimusic.ksmart.com.es`)

Gateway chạy trên cổng local `8000` (được Cloudflare Tunnel chuyển tiếp từ `https://apimusic.ksmart.com.es`):

- **Swagger / OpenAPI Documentation:** `https://apimusic.ksmart.com.es/docs`
- **Health Check:** `GET https://apimusic.ksmart.com.es/health`
- **Tạo nhạc mới (Async Queue):** `POST https://apimusic.ksmart.com.es/v1/music/generate`
- **Kiểm tra trạng thái tiến trình:** `GET https://apimusic.ksmart.com.es/v1/music/tasks/{task_id}`
- **Tải file nhạc hoàn chỉnh:** `GET https://apimusic.ksmart.com.es/v1/music/tasks/{task_id}/download`

### 📝 Chi tiết Payload `POST /v1/music/generate`
```json
{
  "title": "Giai Điệu Mùa Thu",
  "style": "Modern Pop Ballad, emotive acoustic guitar, warm bass, high fidelity studio master",
  "lyrics": "[verse 1]\nWalking down the autumn street...\n[chorus]\nI remember the song of you and me...",
  "vocal_mode": "female",
  "instrumental": false,
  "duration": 120,
  "steps": 25,
  "dit_cfg": 5.0,
  "seed": -1,
  "output_format": "mp3"
}
```

### 📥 Phản hồi mẫu (Response):
```json
{
  "task_id": "8f3b2a1c0d9e4a5b",
  "status": "pending",
  "progress": 0,
  "created_at": 1740112800.0,
  "duration": 120,
  "title": "Giai Điệu Mùa Thu",
  "error": null,
  "download_url": null
}
```

Khi task hoàn thành:
`GET https://apimusic.ksmart.com.es/v1/music/tasks/8f3b2a1c0d9e4a5b`
```json
{
  "task_id": "8f3b2a1c0d9e4a5b",
  "status": "completed",
  "progress": 100,
  "download_url": "/v1/music/tasks/8f3b2a1c0d9e4a5b/download"
}
```

---

## ⚡ 2. Cấu Hình & Tối Ưu Cho VGA 16GB VRAM

| Thành phần Model | File GGUF | Định dạng / Quant | Dung lượng VRAM |
| :--- | :--- | :--- | :--- |
| **Language Model (LM)** | `MiniMax-Music3-language_model-Q4_K_M.gguf` | Q4_K_M | ~4.5 GB |
| **RVQ Depth Decoder** | `MiniMax-Music3-rvq_depth_decoder-Q8_0.gguf` | Q8_0 | ~0.4 GB |
| **Condition Encoder** | `MiniMax-Music3-condition_encoder-F32.gguf` | F32 | ~0.1 GB |
| **Diffusion Transformer (DiT)** | `MiniMax-Music3-transformer-Q4_K_M.gguf` | Q4_K_M | ~1.8 GB |
| **Vocoder (VAE)** | `MiniMax-Music3-vocoder-F32.gguf` | F32 | ~0.2 GB |
| **Tổng cộng** | **Bộ 5 weights hoàn chỉnh** | — | **~7.0 GB** |

> 🚀 Với cờ `--keep-loaded`, toàn bộ 5 mô hình thường trú trên VRAM 16GB, GPU không mất thời gian nạp lại model giữa các stage, cho tốc độ xử lý nhanh nhất.

---

## 🚀 3. Hướng Dẫn Vận Hành Hệ Thống

### Bước 1: Cài đặt thư viện phụ trợ
```bash
pip install -r requirements.txt
```

### Bước 2: Tải bộ Model GGUF (chỉ cần chạy lần đầu)
```bash
python download_models.py
```
*(Hoặc chạy `download_models.bat`)*

### Bước 3: Khởi động Inference Engine
Chạy `start_server.bat` (lắng nghe trên cổng `127.0.0.1:8086`).

### Bước 4: Khởi động API Gateway (Internet Access)
Chạy `start_api.bat` (lắng nghe trên cổng `0.0.0.0:8000`).

### Bước 5: Kết nối Cloudflare Tunnel tới `apimusic.ksmart.com.es`
Trên Cloudflare Zero Trust:
1. Tạo hoặc chọn Tunnel hiện có.
2. Thêm **Public Hostname**:
   - **Subdomain:** `apimusic`
   - **Domain:** `ksmart.com.es`
   - **Type:** `HTTP`
   - **URL:** `127.0.0.1:8000`
3. Chạy lệnh:
   ```cmd
   cloudflared tunnel run --token <YOUR_TOKEN>
   ```
*(Hoặc xem hướng dẫn trong `setup_tunnel.bat`)*
