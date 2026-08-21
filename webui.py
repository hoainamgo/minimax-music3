"""
Web UI Gradio cho MiniMax Music 3 Local Inference (Tối ưu VGA 16GB)
"""

import os
import sys
import tempfile
from pathlib import Path
import gradio as gr
from client import MinimaxMusicClient

client = MinimaxMusicClient()

def check_server():
    if client.health_check():
        props = client.get_props()
        return "🟢 Server đang chạy và sẵn sàng!", str(props)
    return "🔴 Server chưa chạy. Hãy chạy 'start_server.bat' trước!", "{}"

def generate_song(
    title: str,
    genre_style: str,
    vocal_mode: str,
    lyrics: str,
    instrumental: bool,
    duration: int,
    steps: int,
    dit_cfg: float,
    seed: int,
    output_format: str,
):
    if not client.health_check():
        raise gr.Error("Server mm-server chưa bật! Vui lòng khởi động start_server.bat")

    # Xây dựng structured caption chuẩn cho MiniMax Music 3
    if instrumental:
        caption = f"### Global Metadata\nGenre: {genre_style}. Mood: Cinematic, expressive. Pure Instrumental track.\n### Vocal Details\nNo vocals. Strictly instrumental.\n### Arrangement\nFull acoustic and electronic instruments, layered harmonies, professional mix."
        lyrics_text = ""
    else:
        vocal_desc = {
            "Male (Nam)": "One adult male lead singer, masculine tenor-to-baritone timbre, expressive delivery.",
            "Female (Nữ)": "One adult female lead singer, feminine mezzo-soprano timbre, clean and emotional delivery.",
            "Duet (Song ca)": "Two distinct lead singers: one male and one female alternating verses and harmonizing on choruses.",
            "Auto / Mix": "Natural lead vocals fitting the musical style."
        }.get(vocal_mode, "Natural lead vocals.")

        caption = f"### Global Metadata\nGenre & Style: {genre_style}. Mood: melodic, high production quality.\n### Vocal Details\n{vocal_desc}\n### Arrangement\nRich instrumentation, modern mixing and mastering."
        lyrics_text = lyrics.strip()

    print(f"Generating song with caption:\n{caption}")

    try:
        res = client.generate_music(
            caption=caption,
            lyrics=lyrics_text,
            duration=int(duration),
            steps=int(steps),
            dit_cfg=float(dit_cfg),
            seed=int(seed) if seed != -1 else -1,
            output_format=output_format,
        )

        audio_bytes = res.get("audio_bytes")
        if not audio_bytes:
            raise gr.Error("Không nhận được dữ liệu âm thanh từ server.")

        ext = "mp3" if output_format == "mp3" else "wav"
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}", prefix="minimax_song_")
        temp_file.write(audio_bytes)
        temp_file.close()

        return temp_file.name, f"✅ Tạo nhạc thành công! Độ dài: {duration}s"
    except Exception as e:
        raise gr.Error(f"Lỗi tạo nhạc: {str(e)}")

# Khởi tạo Giao diện Gradio
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="slate",
)

with gr.Blocks(title="MiniMax Music 3 - Local GPU Studio (16GB VRAM)") as demo:
    gr.Markdown("""
    # 🎵 MiniMax Music 3 - Local Studio (VGA 16GB Optimized)
    **Engine:** `minimaxmusic.cpp` (GGUF + CUDA) | **Tối ưu VRAM:** 16GB GPU (Full In-Memory `--keep-loaded`)
    """)

    with gr.Row():
        server_status = gr.Textbox(label="Trạng thái Server", value="Đang kiểm tra...", interactive=False, scale=3)
        refresh_btn = gr.Button("🔄 Kiểm tra kết nối", scale=1)

    with gr.Tabs():
        with gr.TabItem("🎹 Tạo bài hát mới"):
            with gr.Row():
                with gr.Column(scale=5):
                    title_input = gr.Textbox(label="Tên bài hát (Title)", placeholder="VD: Giai điệu mùa hạ", value="")
                    style_input = gr.Textbox(
                        label="Phong cách / Thể loại (Style & Genre)",
                        placeholder="VD: Modern pop ballad with acoustic guitar, emotive piano, warm bass and energetic drums",
                        lines=3,
                        value="Modern pop ballad, warm acoustic guitar, emotional piano, energetic beat, commercial radio mix"
                    )

                    with gr.Row():
                        vocal_mode = gr.Dropdown(
                            label="Giọng hát (Vocal Mode)",
                            choices=["Male (Nam)", "Female (Nữ)", "Duet (Song ca)", "Auto / Mix"],
                            value="Female (Nữ)"
                        )
                        instrumental = gr.Checkbox(label="Chỉ hòa tấu (Instrumental - Không lời)", value=False)

                    lyrics_input = gr.Textbox(
                        label="Lời bài hát (Lyrics kèm tag [verse], [chorus], [bridge]...)",
                        lines=10,
                        placeholder="[intro]\n[verse 1]\nNhững tháng năm trôi qua thật êm đềm...\n[chorus]\nTa cùng nhau bước trên con đường dài...\n[outro]",
                        value="[verse 1]\nWalking down the neon street\nListening to the city beat\nShadows dancing in the light\nEverything is feeling right\n\n[chorus]\nTake my hand and fly away\nInto the light of yesterday\nMusic playing in our soul\nTonight we are feeling whole"
                    )

                with gr.Column(scale=4):
                    with gr.Accordion("⚙️ Cấu hình sinh nhạc (Inference Params)", open=True):
                        duration = gr.Slider(label="Thời lượng (giây)", minimum=10, maximum=300, step=10, value=120)
                        steps = gr.Slider(label="Số bước DiT (Steps)", minimum=10, maximum=50, step=5, value=25)
                        dit_cfg = gr.Slider(label="Guidance Scale (DiT CFG)", minimum=1.0, maximum=10.0, step=0.5, value=5.0)
                        seed = gr.Number(label="Seed (-1 để ngẫu nhiên)", value=-1, precision=0)
                        output_format = gr.Radio(label="Định dạng xuất", choices=["mp3", "wav16", "wav24"], value="mp3")

                    generate_btn = gr.Button("🚀 BẮT ĐẦU TẠO BÀI HÁT", variant="primary", size="lg")
                    result_status = gr.Textbox(label="Tiến trình", interactive=False)
                    audio_output = gr.Audio(label="Bản nhạc hoàn chỉnh", type="filepath")

        with gr.TabItem("ℹ️ Hướng dẫn & Tối ưu 16GB"):
            gr.Markdown("""
            ### 💡 Tối ưu hóa trên VGA 16GB VRAM:
            - **Cấu hình model:**
              - `MiniMax-Music3-language_model-Q4_K_M.gguf` (~4.5 GB)
              - `MiniMax-Music3-rvq_depth_decoder-Q8_0.gguf` (~0.4 GB)
              - `MiniMax-Music3-condition_encoder-F32.gguf` (~0.1 GB)
              - `MiniMax-Music3-transformer-Q4_K_M.gguf` (~1.8 GB)
              - `MiniMax-Music3-vocoder-F32.gguf` (~0.2 GB)
            - **Tổng dung lượng VRAM thực tế:** ~7.0 GB.
            - Nhờ đó, trên card 16GB VRAM (như RTX 4080, RTX 4070Ti Super, RTX 3090, v.v.), server bật cờ `--keep-loaded` giữ trọn bộ model trên VRAM mà không cần hoán đổi đĩa, tốc độ sinh nhạc đạt tối đa!
            """)

    refresh_btn.click(check_server, outputs=[server_status])
    generate_btn.click(
        generate_song,
        inputs=[
            title_input,
            style_input,
            vocal_mode,
            lyrics_input,
            instrumental,
            duration,
            steps,
            dit_cfg,
            seed,
            output_format
        ],
        outputs=[audio_output, result_status]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
