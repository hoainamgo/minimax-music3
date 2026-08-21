#!/usr/bin/env bash
echo "=========================================================="
echo "  Khởi động MiniMax Music 3 Engine trên Linux GPU"
echo "=========================================================="

./runtime/mm-server --models models --host 127.0.0.1 --port 8086 --keep-loaded --max-batch 1
