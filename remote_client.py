"""
Module Client kết nối từ máy tính tới Backend MiniMax Music 3 trên Lightning.ai
Mặc định kết nối qua domain: https://apimusic.ksmart.com.es
"""

import os
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Callable

DEFAULT_API_URL = os.environ.get("MINIMAX_API_URL", "https://apimusic.ksmart.com.es").rstrip("/")
DEFAULT_DOWNLOAD_DIR = Path.home() / "Music" / "MiniMax_AI"

class RemoteMusicClient:
    def __init__(self, api_url: str = DEFAULT_API_URL, api_key: str = ""):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def check_health(self) -> Dict[str, Any]:
        """Kiểm tra tình trạng kết nối tới Cloud Backend."""
        try:
            res = requests.get(f"{self.api_url}/health", headers=self._headers(), timeout=5)
            if res.status_code == 200:
                return res.json()
            return {"status": "error", "code": res.status_code, "msg": res.text}
        except Exception as e:
            return {"status": "offline", "error": str(e)}

    def submit_generation(
        self,
        style: str,
        lyrics: str = "",
        title: str = "Untitled",
        vocal_mode: str = "female",
        instrumental: bool = False,
        duration: int = 120,
        steps: int = 25,
        dit_cfg: float = 5.0,
        seed: int = -1,
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """Gửi yêu cầu tạo nhạc lên Lightning backend."""
        payload = {
            "title": title,
            "style": style,
            "lyrics": lyrics,
            "vocal_mode": vocal_mode,
            "instrumental": instrumental,
            "duration": duration,
            "steps": steps,
            "dit_cfg": dit_cfg,
            "seed": seed,
            "output_format": output_format,
        }

        url = f"{self.api_url}/v1/music/generate"
        res = requests.post(url, json=payload, headers=self._headers(), timeout=15)
        if res.status_code != 200:
            raise RuntimeError(f"Lỗi gửi yêu cầu ({res.status_code}): {res.text}")
        return res.json()

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Kiểm tra trạng thái của một Task."""
        url = f"{self.api_url}/v1/music/tasks/{task_id}"
        res = requests.get(url, headers=self._headers(), timeout=10)
        if res.status_code != 200:
            raise RuntimeError(f"Lỗi lấy trạng thái task ({res.status_code}): {res.text}")
        return res.json()

    def download_file(self, task_id: str, save_dir: Path = DEFAULT_DOWNLOAD_DIR, custom_filename: str = "") -> Path:
        """Tải bài hát hoàn chỉnh về máy tính cá nhân."""
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        url = f"{self.api_url}/v1/music/tasks/{task_id}/download"
        res = requests.get(url, headers=self._headers(), timeout=60, stream=True)
        if res.status_code != 200:
            raise RuntimeError(f"Lỗi tải file ({res.status_code}): {res.text}")

        # Lấy tên file từ Content-Disposition hoặc đặt tên mặc định
        filename = custom_filename
        if not filename:
            cd = res.headers.get("content-disposition", "")
            if "filename=" in cd:
                filename = cd.split("filename=")[-1].strip('"\'; ')
            else:
                filename = f"music_{task_id}.mp3"

        out_path = save_dir / filename
        with open(out_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)

        return out_path

    def generate_and_wait(
        self,
        style: str,
        lyrics: str = "",
        title: str = "Untitled",
        vocal_mode: str = "female",
        instrumental: bool = False,
        duration: int = 120,
        steps: int = 25,
        dit_cfg: float = 5.0,
        seed: int = -1,
        output_format: str = "mp3",
        save_dir: Path = DEFAULT_DOWNLOAD_DIR,
        on_progress: Optional[Callable[[int, str], None]] = None,
        poll_interval: float = 3.0,
    ) -> Path:
        """Quy trình toàn diện: Gửi yêu cầu -> Chờ xử lý -> Tự động tải về máy."""
        if on_progress:
            on_progress(5, "Đang gửi yêu cầu tới Lightning Backend...")

        submit_resp = self.submit_generation(
            style=style,
            lyrics=lyrics,
            title=title,
            vocal_mode=vocal_mode,
            instrumental=instrumental,
            duration=duration,
            steps=steps,
            dit_cfg=dit_cfg,
            seed=seed,
            output_format=output_format
        )

        task_id = submit_resp.get("task_id")
        if not task_id:
            raise RuntimeError(f"Không nhận được task_id: {submit_resp}")

        start_time = time.time()
        while True:
            status_resp = self.get_task_status(task_id)
            status = status_resp.get("status", "")
            progress = status_resp.get("progress", 0)

            if status == "pending":
                if on_progress:
                    on_progress(15, f"Đang xếp hàng chờ xử lý trên GPU ({int(time.time() - start_time)}s)...")
            elif status == "processing":
                if on_progress:
                    on_progress(50, f"GPU đang tạo nhạc MiniMax Music 3 ({int(time.time() - start_time)}s)...")
            elif status == "completed":
                if on_progress:
                    on_progress(90, "Đang tải bài hát về máy...")
                safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip() or "song"
                ext = output_format if output_format == "mp3" else "wav"
                filename = f"{safe_title}_{task_id[:6]}.{ext}"
                file_path = self.download_file(task_id, save_dir=save_dir, custom_filename=filename)
                if on_progress:
                    on_progress(100, f"Hoàn tất: {file_path.name}")
                return file_path
            elif status == "failed":
                err = status_resp.get("error", "Lỗi không xác định từ Backend")
                raise RuntimeError(f"Tạo nhạc thất bại: {err}")

            time.sleep(poll_interval)
