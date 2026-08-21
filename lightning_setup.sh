#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Cài đặt & Build MiniMax Music 3 Engine trên Lightning.ai"
echo "=========================================================="

# 1. Cập nhật & Cài đặt build tools
sudo apt-get update -y
sudo apt-get install -y cmake build-essential git libsndfile1-dev

# 2. Cài đặt Python requirements
pip install -r requirements.txt

# 3. Clone & Build minimaxmusic.cpp cho Linux CUDA
if [ ! -f "runtime/mm-server" ]; then
    echo "[*] Đang clone và biên dịch minimaxmusic.cpp với CUDA..."
    if [ ! -d "minimaxmusic.cpp" ]; then
        git clone --recursive https://github.com/ServeurpersoCom/minimaxmusic.cpp.git
    fi
    cd minimaxmusic.cpp
    cmake -B build -DGGML_CUDA=ON
    cmake --build build --config Release -j$(nproc)
    
    mkdir -p ../runtime
    cp build/bin/mm-server ../runtime/mm-server 2>/dev/null || cp build/mm-server ../runtime/mm-server
    chmod +x ../runtime/mm-server
    cd ..
    echo "[✓] Biên dịch thành công: runtime/mm-server"
fi

# 4. Tải models GGUF (Tối ưu 16GB VRAM)
python download_models.py

echo "=========================================================="
echo "  Cài đặt hoàn tất! Để khởi động:"
echo "  1. Chạy Engine: bash start_server_linux.sh"
echo "  2. Chạy API:    bash start_api_linux.sh"
echo "=========================================================="
