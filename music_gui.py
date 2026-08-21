"""
Giao Diện Desktop GUI Hiện Đại Cho MiniMax Music 3 Client (PC)
Kết nối Remote Backend trên Lightning.ai (apimusic.ksmart.com.es)
"""

import os
import sys
import threading
import subprocess
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from remote_client import RemoteMusicClient, DEFAULT_API_URL, DEFAULT_DOWNLOAD_DIR

class MiniMaxMusicGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("MiniMax Music 3 - Desktop Studio (Remote Lightning.ai)")
        self.geometry("980x750")
        self.minsize(880, 680)

        # Cấu hình icon/style
        self._configure_styles()

        # Biến trạng thái
        self.api_url_var = tk.StringVar(value=DEFAULT_API_URL)
        self.server_status_var = tk.StringVar(value="Đang kiểm tra kết nối...")
        self.title_var = tk.StringVar(value="Giai Điệu Mùa Hạ")
        self.vocal_mode_var = tk.StringVar(value="female")
        self.instrumental_var = tk.BooleanVar(value=False)
        self.duration_var = tk.IntVar(value=120)
        self.steps_var = tk.IntVar(value=25)
        self.cfg_var = tk.DoubleVar(value=5.0)
        self.format_var = tk.StringVar(value="mp3")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_text_var = tk.StringVar(value="Sẵn sàng tạo bài hát mới.")
        self.last_audio_file: Optional[Path] = None

        self.client = RemoteMusicClient(api_url=self.api_url_var.get())

        # Xây dựng layout
        self._create_widgets()

        # Kiểm tra kết nối server ban đầu trên luồng riêng
        self.after(500, self._check_server_async)

    def _configure_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Màu sắc hiện đại
        self.configure(bg="#1e1e2e")
        self.style.configure(".", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4")
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#89b4fa")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 11, "bold"), foreground="#fab387")
        self.style.configure("Status.TLabel", font=("Segoe UI", 9), foreground="#a6adc8")
        
        self.style.configure("TFrame", background="#1e1e2e")
        self.style.configure("Card.TFrame", background="#252538", relief="flat")

        self.style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), background="#89b4fa", foreground="#11111b", padding=8)
        self.style.map("Primary.TButton", background=[("active", "#b4befe")])

        self.style.configure("Action.TButton", font=("Segoe UI", 9), background="#45475a", foreground="#cdd6f4", padding=4)
        self.style.map("Action.TButton", background=[("active", "#585b70")])

        self.style.configure("Tag.TButton", font=("Segoe UI", 8), background="#313244", foreground="#a6adc8", padding=2)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header & Server Connection Bar
        header_card = ttk.Frame(main_frame, style="Card.TFrame", padding=12)
        header_card.pack(fill=tk.X, pady=(0, 12))

        header_top = ttk.Frame(header_card, style="Card.TFrame")
        header_top.pack(fill=tk.X)

        title_lbl = ttk.Label(header_top, text="🎵 MiniMax Music 3 - Remote PC Studio", style="Header.TLabel")
        title_lbl.pack(side=tk.LEFT)

        status_lbl = ttk.Label(header_top, textvariable=self.server_status_var, font=("Segoe UI", 10, "italic"))
        status_lbl.pack(side=tk.RIGHT)

        conn_bar = ttk.Frame(header_card, style="Card.TFrame")
        conn_bar.pack(fill=tk.X, pady=(8, 0))

        ttk.Label(conn_bar, text="Backend Endpoint:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 8))
        self.url_entry = ttk.Entry(conn_bar, textvariable=self.api_url_var, font=("Consolas", 10), width=45)
        self.url_entry.pack(side=tk.LEFT, padx=(0, 8))

        reconnect_btn = ttk.Button(conn_bar, text="🔄 Kiểm tra lại", style="Action.TButton", command=self._check_server_async)
        reconnect_btn.pack(side=tk.LEFT)

        # 2. Body Container (Chia 2 cột: Left Input, Right Controls & Lyrics)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_col = ttk.Frame(content_frame, style="Card.TFrame", padding=12)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        right_col = ttk.Frame(content_frame, style="Card.TFrame", padding=12)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # --- CỘT TRÁI: Style, Tiêu đề, Preset & Cấu hình ---
        ttk.Label(left_col, text="1. Thông Tin Bài Hát", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(0, 6))

        ttk.Label(left_col, text="Tên bài hát:").pack(anchor=tk.W)
        self.title_entry = ttk.Entry(left_col, textvariable=self.title_var, font=("Segoe UI", 10))
        self.title_entry.pack(fill=tk.X, pady=(2, 8))

        ttk.Label(left_col, text="Mô tả phong cách & thể loại (Style / Genre):").pack(anchor=tk.W)
        self.style_text = tk.Text(left_col, height=4, bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4", font=("Segoe UI", 10), relief="flat")
        self.style_text.insert(tk.END, "Modern pop ballad, warm acoustic guitar, emotive piano, energetic rhythm, studio master")
        self.style_text.pack(fill=tk.X, pady=(2, 6))

        # Preset tags
        preset_frame = ttk.Frame(left_col, style="Card.TFrame")
        preset_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(preset_frame, text="Mẫu nhanh:", font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 4))
        
        presets = [
            ("Pop Ballad", "Modern pop ballad, emotional piano, warm strings, heartfelt vocal"),
            ("EDM / Dance", "Energetic EDM dance pop, punchy bassline, synthesizer hooks, fast BPM"),
            ("Acoustic", "Intimate acoustic guitar, soft shaker, natural organic feel"),
            ("Epic Cinematic", "Cinematic orchestral rock, heavy drums, brass swells, dramatic"),
        ]
        for name, p_style in presets:
            btn = ttk.Button(preset_frame, text=name, style="Tag.TButton", command=lambda s=p_style: self._set_style(s))
            btn.pack(side=tk.LEFT, padx=2)

        ttk.Label(left_col, text="Giọng hát & Hòa tấu:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(4, 2))
        vocal_frame = ttk.Frame(left_col, style="Card.TFrame")
        vocal_frame.pack(fill=tk.X, pady=(0, 8))

        for v_mode, v_label in [("female", "Nữ (Female)"), ("male", "Nam (Male)"), ("duet", "Song ca (Duet)"), ("auto", "Tự động")]:
            rb = ttk.Radiobutton(vocal_frame, text=v_label, value=v_mode, variable=self.vocal_mode_var)
            rb.pack(side=tk.LEFT, padx=(0, 8))

        inst_cb = ttk.Checkbutton(left_col, text="Chỉ hòa tấu (Instrumental - Không lời)", variable=self.instrumental_var, command=self._toggle_instrumental)
        inst_cb.pack(anchor=tk.W, pady=(0, 10))

        # Tham số kỹ thuật
        ttk.Label(left_col, text="2. Cấu Hình Thời Lượng & Tham Số", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(6, 4))
        
        dur_frame = ttk.Frame(left_col, style="Card.TFrame")
        dur_frame.pack(fill=tk.X, pady=2)
        ttk.Label(dur_frame, text="Thời lượng:").pack(side=tk.LEFT)
        self.dur_val_lbl = ttk.Label(dur_frame, text=f"{self.duration_var.get()} giây", font=("Segoe UI", 9, "bold"))
        self.dur_val_lbl.pack(side=tk.RIGHT)
        
        dur_slider = ttk.Scale(left_col, from_=10, to=300, variable=self.duration_var, command=lambda v: self.dur_val_lbl.config(text=f"{int(float(v))} giây"))
        dur_slider.pack(fill=tk.X, pady=(0, 8))

        param_grid = ttk.Frame(left_col, style="Card.TFrame")
        param_grid.pack(fill=tk.X)
        
        ttk.Label(param_grid, text="DiT Steps:").grid(row=0, column=0, sticky=tk.W, padx=2)
        steps_sp = ttk.Spinbox(param_grid, from_=10, to=50, textvariable=self.steps_var, width=6)
        steps_sp.grid(row=0, column=1, padx=4)

        ttk.Label(param_grid, text="CFG Scale:").grid(row=0, column=2, sticky=tk.W, padx=(12, 2))
        cfg_sp = ttk.Spinbox(param_grid, from_=1.0, to=10.0, increment=0.5, textvariable=self.cfg_var, width=6)
        cfg_sp.grid(row=0, column=3, padx=4)

        ttk.Label(param_grid, text="Định dạng:").grid(row=0, column=4, sticky=tk.W, padx=(12, 2))
        fmt_cb = ttk.Combobox(param_grid, values=["mp3", "wav"], textvariable=self.format_var, width=6, state="readonly")
        fmt_cb.grid(row=0, column=5, padx=4)

        # --- CỘT PHẢI: Lời bài hát (Lyrics Editor) ---
        right_header = ttk.Frame(right_col, style="Card.TFrame")
        right_header.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(right_header, text="3. Lời Bài Hát (Lyrics)", style="SubHeader.TLabel").pack(side=tk.LEFT)
        
        tag_bar = ttk.Frame(right_header, style="Card.TFrame")
        tag_bar.pack(side=tk.RIGHT)
        for tag in ["[verse]", "[chorus]", "[bridge]", "[outro]"]:
            t_btn = ttk.Button(tag_bar, text=f"+ {tag}", style="Tag.TButton", command=lambda t=tag: self._insert_tag(t))
            t_btn.pack(side=tk.LEFT, padx=2)

        self.lyrics_text = tk.Text(right_col, bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4", font=("Segoe UI", 10), wrap=tk.WORD, relief="flat")
        self.lyrics_text.insert(tk.END, "[verse 1]\nWalking through the summer rain\nMemories of you remain\nFootsteps echoing the street\nCatching up to every beat\n\n[chorus]\nTake my hand and feel the sound\nMusic turning all around\nShining bright into the sky\nYou and I will learn to fly\n\n[outro]")
        self.lyrics_text.pack(fill=tk.BOTH, expand=True, pady=4)

        # 3. Footer Action & Progress Bar
        footer_card = ttk.Frame(main_frame, style="Card.TFrame", padding=12)
        footer_card.pack(fill=tk.X, pady=(12, 0))

        progress_row = ttk.Frame(footer_card, style="Card.TFrame")
        progress_row.pack(fill=tk.X, pady=(0, 6))

        self.progress_bar = ttk.Progressbar(progress_row, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12))

        self.gen_btn = ttk.Button(progress_row, text="🚀 BẮT ĐẦU TẠO NHẠC", style="Primary.TButton", command=self._start_generate_thread)
        self.gen_btn.pack(side=tk.RIGHT)

        status_bar = ttk.Frame(footer_card, style="Card.TFrame")
        status_bar.pack(fill=tk.X)

        self.status_lbl = ttk.Label(status_bar, textvariable=self.progress_text_var, font=("Segoe UI", 10))
        self.status_lbl.pack(side=tk.LEFT)

        self.open_file_btn = ttk.Button(status_bar, text="▶️ Phát Bài Hát", style="Action.TButton", command=self._play_audio, state=tk.DISABLED)
        self.open_file_btn.pack(side=tk.RIGHT, padx=4)

        self.open_folder_btn = ttk.Button(status_bar, text="📂 Mở Thư Mục", style="Action.TButton", command=self._open_folder)
        self.open_folder_btn.pack(side=tk.RIGHT, padx=4)

    def _set_style(self, style_str: str):
        self.style_text.delete("1.0", tk.END)
        self.style_text.insert(tk.END, style_str)

    def _insert_tag(self, tag: str):
        self.lyrics_text.insert(tk.INSERT, f"\n{tag}\n")

    def _toggle_instrumental(self):
        if self.instrumental_var.get():
            self.lyrics_text.config(state=tk.DISABLED, bg="#11111b")
        else:
            self.lyrics_text.config(state=tk.NORMAL, bg="#181825")

    def _check_server_async(self):
        url = self.api_url_var.get().strip()
        self.client = RemoteMusicClient(api_url=url)
        self.server_status_var.set("⏳ Đang kiểm tra kết nối...")

        def run():
            health = self.client.check_health()
            if health.get("status") == "ok":
                status_text = "🟢 Cloud Backend Đang Hoạt Động (GPU Sẵn Sàng)"
            else:
                status_text = "🔴 Backend Không Phản Hồi (Kiểm tra lại URL / Cloudflare Tunnel)"
            self.after(0, lambda: self.server_status_var.set(status_text))

        threading.Thread(target=run, daemon=True).start()

    def _start_generate_thread(self):
        style = self.style_text.get("1.0", tk.END).strip()
        if not style:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập phong cách / thể loại bài hát!")
            return

        lyrics = "" if self.instrumental_var.get() else self.lyrics_text.get("1.0", tk.END).strip()
        title = self.title_var.get().strip() or "My Song"
        vocal_mode = self.vocal_mode_var.get()
        instrumental = self.instrumental_var.get()
        duration = int(self.duration_var.get())
        steps = int(self.steps_var.get())
        cfg = float(self.cfg_var.get())
        out_fmt = self.format_var.get()

        self.gen_btn.config(state=tk.DISABLED)
        self.open_file_btn.config(state=tk.DISABLED)
        self.progress_var.set(5)
        self.progress_text_var.set("Đang kết nối Cloud Lightning.ai...")

        def worker():
            def on_prog(pct, msg):
                self.after(0, lambda: (self.progress_var.set(pct), self.progress_text_var.set(msg)))

            try:
                out_path = self.client.generate_and_wait(
                    style=style,
                    lyrics=lyrics,
                    title=title,
                    vocal_mode=vocal_mode,
                    instrumental=instrumental,
                    duration=duration,
                    steps=steps,
                    dit_cfg=cfg,
                    output_format=out_fmt,
                    save_dir=DEFAULT_DOWNLOAD_DIR,
                    on_progress=on_prog,
                )
                self.last_audio_file = out_path
                self.after(0, lambda: self._on_generate_success(out_path))
            except Exception as e:
                self.after(0, lambda: self._on_generate_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_generate_success(self, file_path: Path):
        self.gen_btn.config(state=tk.NORMAL)
        self.open_file_btn.config(state=tk.NORMAL)
        self.progress_var.set(100)
        self.progress_text_var.set(f"✅ Đã tải về: {file_path.name}")
        messagebox.showinfo("Thành Công", f"Tạo bài hát hoàn tất!\nĐã lưu tại:\n{file_path}")

    def _on_generate_error(self, err_msg: str):
        self.gen_btn.config(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_text_var.set(f"❌ Lỗi: {err_msg}")
        messagebox.showerror("Lỗi Tạo Nhạc", f"Không thể tạo nhạc:\n{err_msg}")

    def _play_audio(self):
        if self.last_audio_file and self.last_audio_file.exists():
            if sys.platform == "win32":
                os.startfile(str(self.last_audio_file))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self.last_audio_file)])
            else:
                subprocess.Popen(["xdg-open", str(self.last_audio_file)])

    def _open_folder(self):
        folder = DEFAULT_DOWNLOAD_DIR
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(folder))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])

if __name__ == "__main__":
    app = MiniMaxMusicGUI()
    app.mainloop()
