"""
Script tải model GGUF MiniMax-Music3 tối ưu cho GPU 16GB VRAM.
Nguồn model: Serveurperso/MiniMax-Music3-GGUF (Hugging Face)
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("Vui lòng cài đặt huggingface_hub: pip install huggingface_hub")
    sys.exit(1)

REPO_ID = "Serveurperso/MiniMax-Music3-GGUF"
MODEL_DIR = Path(__file__).parent / "models"

# Danh sách model tối ưu cho VGA 16GB:
# - Language Model: Q4_K_M (~4.5 GB) hoặc Q5_K_M (~5.5 GB)
# - RVQ Depth Decoder: Q8_0 (~0.4 GB)
# - Condition Encoder: F32 (~0.1 GB)
# - DiT Transformer: Q4_K_M (~1.8 GB) hoặc Q8_0 (~3.2 GB)
# - Vocoder VAE: F32 (~0.2 GB)
# Tổng VRAM chiếm dụng: ~7.0 GB -> chạy cực mượt với flag --keep-loaded trên GPU 16GB!

MODELS_16GB = [
    "MiniMax-Music3-language_model-Q4_K_M.gguf",
    "MiniMax-Music3-rvq_depth_decoder-Q8_0.gguf",
    "MiniMax-Music3-condition_encoder-F32.gguf",
    "MiniMax-Music3-transformer-Q4_K_M.gguf",
    "MiniMax-Music3-vocoder-F32.gguf",
]

def download_models(target_dir: Path = MODEL_DIR):
    target_dir.mkdir(parents=True, exist_ok=True)
    print("==================================================")
    print("  Tải bộ model MiniMax-Music3 GGUF (GPU 16GB VRAM)")
    print(f"  Thư mục lưu trữ: {target_dir.resolve()}")
    print("==================================================")

    for filename in MODELS_16GB:
        dest_path = target_dir / filename
        if dest_path.exists() and dest_path.stat().st_size > 1024 * 1024:
            print(f" [✓] Đã có sẵn: {filename} ({dest_path.stat().st_size / (1024*1024):.1f} MB)")
            continue

        print(f"\n [↓] Đang tải {filename} từ {REPO_ID}...")
        try:
            hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                local_dir=str(target_dir),
                local_dir_use_symlinks=False
            )
            print(f" [✓] Tải thành công: {filename}")
        except Exception as e:
            print(f" [✗] Lỗi khi tải {filename}: {e}")

    print("\n==================================================")
    print(" Hoàn tất tải models. Giờ bạn có thể chạy start_server.bat!")
    print("==================================================")

if __name__ == "__main__":
    download_models()
