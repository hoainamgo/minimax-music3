"""
Client Python giao tiếp trực tiếp với mm-server.exe (minimaxmusic.cpp)
"""

import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Generator

class MinimaxMusicClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8086"):
        self.base_url = base_url.rstrip("/")

    def health_check(self) -> bool:
        try:
            res = requests.get(f"{self.base_url}/health", timeout=3)
            return res.status_code == 200 and res.json().get("status") == "ok"
        except Exception:
            return False

    def get_props(self) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/props", timeout=5)
            return res.json()
        except Exception as e:
            return {"error": str(e)}

    def generate_music(
        self,
        caption: str,
        lyrics: str,
        duration: int = 180,
        steps: int = 25,
        dit_cfg: float = 5.0,
        lm_cfg: float = 1.5,
        seed: int = -1,
        output_format: str = "mp3",
        lm_batch_size: int = 1,
        synth_batch_size: int = 1,
        poll_interval: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Gửi yêu cầu tạo nhạc tới mm-server và chờ kết quả.
        
        Args:
            caption: Mô tả thể loại, nhạc cụ, vocal (Structured Caption)
            lyrics: Lời bài hát kèm thẻ [verse], [chorus] hoặc để trống nếu instrumental
            duration: Độ dài tính bằng giây (10 - 300)
            steps: Số bước diffusion (20 - 50)
            dit_cfg: CFG scale cho DiT (4.0 - 7.0)
            lm_cfg: CFG scale cho Language Model
            seed: Seed ngẫu nhiên (-1 là ngẫu nhiên)
            output_format: 'mp3', 'wav16', 'wav24', 'wav32'
        """
        payload = {
            "caption": caption,
            "lyrics": lyrics,
            "duration": int(duration),
            "steps": int(steps),
            "cfg": float(dit_cfg),
            "dit_cfg": float(dit_cfg),
            "lm_cfg": float(lm_cfg),
            "seed": int(seed),
            "lm_seed": int(seed),
            "output_format": output_format,
            "lm_batch_size": int(lm_batch_size),
            "synth_batch_size": int(synth_batch_size),
        }

        res = requests.post(f"{self.base_url}/synth", json=payload, timeout=10)
        if res.status_code != 200:
            raise RuntimeError(f"Lỗi gửi yêu cầu synth: {res.status_code} - {res.text}")

        resp_data = res.json()
        job_id = resp_data.get("id")
        if not job_id:
            raise RuntimeError(f"Không nhận được job id từ server: {resp_data}")

        print(f"[*] Bắt đầu xử lý Job ID: {job_id}")

        # Polling trạng thái job
        while True:
            job_res = requests.get(f"{self.base_url}/job?id={job_id}", timeout=10)
            if job_res.status_code != 200:
                time.sleep(poll_interval)
                continue

            # mm-server có thể trả về audio stream hoặc json status
            content_type = job_res.headers.get("Content-Type", "")
            if "audio" in content_type or "octet-stream" in content_type:
                return {
                    "status": "done",
                    "job_id": job_id,
                    "audio_bytes": job_res.content,
                    "content_type": content_type,
                    "format": output_format
                }

            try:
                status_json = job_res.json()
                status = status_json.get("status", "")
                if status == "failed":
                    raise RuntimeError(f"Job thất bại: {status_json.get('error', 'Lỗi không xác định')}")
                elif status == "cancelled":
                    raise RuntimeError("Job đã bị huỷ.")
                elif status == "done":
                    # Tải file audio
                    audio_res = requests.get(f"{self.base_url}/job?id={job_id}&result=1", timeout=30)
                    return {
                        "status": "done",
                        "job_id": job_id,
                        "audio_bytes": audio_res.content,
                        "format": output_format
                    }
                else:
                    progress = status_json.get("progress", 0)
                    print(f"[*] Đang tiến hành ({status}): {progress}%")
            except ValueError:
                pass

            time.sleep(poll_interval)

    def cancel_job(self, job_id: str) -> bool:
        try:
            res = requests.post(f"{self.base_url}/job?id={job_id}&action=cancel", timeout=5)
            return res.status_code == 200
        except Exception:
            return False
