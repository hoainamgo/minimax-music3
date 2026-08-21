#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  [1/4] Cập nhật hệ thống & Thư viện phụ trợ..."
echo "=========================================================="
sudo apt-get update -y > /dev/null 2>&1
sudo apt-get install -y cmake build-essential git libsndfile1-dev ffmpeg > /dev/null 2>&1

echo "=========================================================="
echo "  [2/4] Cài đặt Python requirements..."
echo "=========================================================="
pip install -r requirements.txt

echo "=========================================================="
echo "  [3/4] Biên dịch Engine Inference với CUDA GPU..."
echo "=========================================================="
mkdir -p runtime models outputs

if [ ! -f "runtime/mm-server" ]; then
    if [ ! -d "audio.cpp" ]; then
        echo "[*] Đang tải mã nguồn audio.cpp (GGML MiniMax Music 3)..."
        git clone --recursive https://github.com/0xShug0/audio.cpp.git
    fi
    cd audio.cpp
    cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
    cmake --build build --config Release -j$(nproc)
    
    # Tìm và copy binary vào runtime/mm-server
    find build -type f -name "audio-server" -o -name "mm-server" -o -name "audiocpp*" | head -n 1 | xargs -I {} cp {} ../runtime/mm-server
    chmod +x ../runtime/mm-server
    cd ..
    echo "[✓] Biên dịch thành công: runtime/mm-server"
fi

echo "=========================================================="
echo "  [4/4] Tải 5 model GGUF (Tối ưu 16GB VRAM)..."
echo "=========================================================="
python download_models.py

echo "=========================================================="
echo "  🎉 CÀI ĐẶT HOÀN TẤT TRÊN GPU LINUX / COLAB!"
echo "=========================================================="
