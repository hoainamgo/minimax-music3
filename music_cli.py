"""
Command-Line Interface (CLI) cho MiniMax Music 3 Client
Chạy trên máy tính PC cá nhân, kết nối Lightning.ai qua Internet
"""

import sys
import argparse
import time
from pathlib import Path
from remote_client import RemoteMusicClient, DEFAULT_API_URL, DEFAULT_DOWNLOAD_DIR

def print_banner():
    print("=" * 60)
    print("       🎵 MINIMAX MUSIC 3 - PC CLIENT CLI")
    print("   Backend: Lightning.ai | Domain: https://apimusic.ksmart.com.es")
    print("=" * 60)

def cmd_health(args):
    client = RemoteMusicClient(api_url=args.url, api_key=args.key)
    print(f"[*] Đang kiểm tra kết nối tới: {args.url} ...")
    health = client.check_health()
    if health.get("status") == "ok":
        print(f"[✓] Kết nối THÀNH CÔNG!")
        print(f"    - Gateway: {health.get('gateway')}")
        print(f"    - Inference Engine (GPU): {'Online' if health.get('engine_connected') else 'Offline'}")
        print(f"    - Hàng đợi chờ: {health.get('active_queue_size', 0)} bài")
    else:
        print(f"[✗] Không thể kết nối hoặc Server đang bận:")
        print(f"    {health}")

def cmd_generate(args):
    client = RemoteMusicClient(api_url=args.url, api_key=args.key)
    save_dir = Path(args.output_dir)

    print_banner()
    print(f"[*] Tiêu đề:     {args.title}")
    print(f"[*] Phong cách:  {args.style}")
    print(f"[*] Giọng hát:   {args.vocal}")
    print(f"[*] Thời lượng:  {args.duration}s")
    print(f"[*] Định dạng:   {args.format}")
    print(f"[*] Backend:     {args.url}")
    print("-" * 60)

    def progress_callback(pct, msg):
        print(f"[{pct:3d}%] {msg}")

    try:
        out_file = client.generate_and_wait(
            style=args.style,
            lyrics=args.lyrics or "",
            title=args.title,
            vocal_mode=args.vocal,
            instrumental=args.instrumental,
            duration=args.duration,
            steps=args.steps,
            dit_cfg=args.cfg,
            seed=args.seed,
            output_format=args.format,
            save_dir=save_dir,
            on_progress=progress_callback,
        )
        print("=" * 60)
        print(f"[✓] HOÀN TẤT TẠO NHẠC!")
        print(f"[📁] Đã lưu tại: {out_file.resolve()}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[✗] LỖI: {e}")
        sys.exit(1)

def cmd_wizard(args):
    """Giao diện hỏi đáp từng bước trực quan trong terminal."""
    client = RemoteMusicClient(api_url=args.url, api_key=args.key)
    print_banner()
    print("  CHẾ ĐỘ TẠO BÀI HÁT TỪNG BƯỚC (INTERACTIVE WIZARD)")
    print("-" * 60)

    title = input("1. Tên bài hát [Mặc định: My Song]: ").strip() or "My Song"
    style = input("2. Thể loại / Mô tả phong cách (VD: Pop ballad, acoustic guitar, emotional piano): ").strip()
    while not style:
        print("   [!] Vui lòng nhập mô tả phong cách!")
        style = input("2. Thể loại / Mô tả phong cách: ").strip()

    print("\n3. Chọn giọng hát:")
    print("   [1] Female (Giọng Nữ)")
    print("   [2] Male (Giọng Nam)")
    print("   [3] Duet (Song ca Nam Nữ)")
    print("   [4] Không lời (Instrumental)")
    vocal_choice = input("   Lựa chọn (1-4) [Mặc định: 1]: ").strip()
    
    vocal_mode = "female"
    instrumental = False
    if vocal_choice == "2":
        vocal_mode = "male"
    elif vocal_choice == "3":
        vocal_mode = "duet"
    elif vocal_choice == "4":
        instrumental = True

    lyrics = ""
    if not instrumental:
        print("\n4. Nhập lời bài hát (kèm [verse], [chorus]...). Gõ 'END' trên dòng mới để hoàn thành:")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        lyrics = "\n".join(lines).strip()
        if not lyrics:
            print("   [i] Để trống lyrics -> Model sẽ tự hòa tấu/sáng tác.")

    dur_str = input("\n5. Thời lượng bài hát tính bằng giây (10-300) [Mặc định: 120]: ").strip()
    duration = int(dur_str) if dur_str.isdigit() else 120

    fmt = input("6. Định dạng xuất (mp3 / wav) [Mặc định: mp3]: ").strip().lower()
    if fmt not in ["mp3", "wav"]:
        fmt = "mp3"

    print("\n" + "=" * 60)
    print("  Đang gửi bài hát lên GPU Lightning.ai để xử lý...")
    print("=" * 60)

    def progress_callback(pct, msg):
        print(f"[{pct:3d}%] {msg}")

    try:
        out_file = client.generate_and_wait(
            style=style,
            lyrics=lyrics,
            title=title,
            vocal_mode=vocal_mode,
            instrumental=instrumental,
            duration=duration,
            output_format=fmt,
            save_dir=Path(args.output_dir),
            on_progress=progress_callback
        )
        print("\n" + "=" * 60)
        print(f"🎉 TẠO NHẠC THÀNH CÔNG!")
        print(f"🎵 File audio: {out_file.resolve()}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[✗] LỖI: {e}")

def main():
    parser = argparse.ArgumentParser(description="MiniMax Music 3 PC Client CLI")
    parser.add_argument("--url", default=DEFAULT_API_URL, help="URL Backend (Mặc định: https://apimusic.ksmart.com.es)")
    parser.add_argument("--key", default="", help="API Key nếu backend yêu cầu")
    parser.add_argument("--output-dir", default=str(DEFAULT_DOWNLOAD_DIR), help="Thư mục lưu bài hát tải về")

    subparsers = parser.add_subparsers(dest="command", help="Lệnh thực hiện")

    # Command: health
    p_health = subparsers.add_parser("health", help="Kiểm tra kết nối tới Backend")
    p_health.set_defaults(func=cmd_health)

    # Command: wizard
    p_wizard = subparsers.add_parser("wizard", help="Giao diện hỏi đáp từng bước (Khuyên dùng)")
    p_wizard.set_defaults(func=cmd_wizard)

    # Command: generate
    p_gen = subparsers.add_parser("generate", help="Tạo bài hát trực tiếp qua tham số dòng lệnh")
    p_gen.add_argument("--title", default="My Song", help="Tên bài hát")
    p_gen.add_argument("--style", required=True, help="Mô tả phong cách bài hát")
    p_gen.add_argument("--lyrics", default="", help="Lời bài hát")
    p_gen.add_argument("--vocal", default="female", choices=["female", "male", "duet", "choir", "auto"], help="Giọng hát")
    p_gen.add_argument("--instrumental", action="store_true", help="Chỉ tạo nhạc hòa tấu")
    p_gen.add_argument("--duration", type=int, default=120, help="Thời lượng giây (10-300)")
    p_gen.add_argument("--steps", type=int, default=25, help="Số bước DiT")
    p_gen.add_argument("--cfg", type=float, default=5.0, help="DiT Guidance CFG")
    p_gen.add_argument("--seed", type=int, default=-1, help="Seed ngẫu nhiên (-1 là random)")
    p_gen.add_argument("--format", default="mp3", choices=["mp3", "wav"], help="Định dạng xuất")
    p_gen.set_defaults(func=cmd_generate)

    if len(sys.argv) == 1:
        # Nếu chỉ chạy 'python music_cli.py' không cờ -> mở wizard
        args = parser.parse_args(["wizard"])
        cmd_wizard(args)
        return

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
