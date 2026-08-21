"""
FastAPI Gateway Server cho MiniMax Music 3
Cung cấp REST API chuẩn kết nối Internet qua domain apimusic.ksmart.com.es
"""

import os
import sys
import uuid
import time
import asyncio
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from client import MinimaxMusicClient

# Thư mục lưu audio sinh ra
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Khởi tạo FastAPI app
app = FastAPI(
    title="MiniMax Music 3 API Gateway",
    description="REST API tạo nhạc AI chất lượng cao từ text prompt và lyrics, chạy trên GPU 16GB VRAM",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Kích hoạt CORS để frontend/n8n/client gọi từ bất cứ đâu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mm_client = MinimaxMusicClient(base_url="http://127.0.0.1:8086")

# Quản lý cấu hình API Key (để trống nếu không yêu cầu key)
API_KEY = os.environ.get("MUSIC_API_KEY", "")

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key không hợp lệ hoặc thiếu X-API-Key header")
    return True

# Database in-memory lưu trữ tác vụ
tasks_db: Dict[str, Dict[str, Any]] = {}
task_queue: asyncio.Queue = asyncio.Queue()

# Request schemas
class MusicGenerateRequest(BaseModel):
    title: Optional[str] = Field(default="Untitled", description="Tên bài hát")
    style: str = Field(..., description="Mô tả phong cách, thể loại (VD: Pop ballad, acoustic guitar, emotional piano)")
    lyrics: Optional[str] = Field(default="", description="Lời bài hát kèm tag [verse], [chorus] hoặc để trống nếu hòa tấu")
    vocal_mode: Optional[str] = Field(default="female", description="male, female, duet, choir, auto")
    instrumental: Optional[bool] = Field(default=False, description="True nếu chỉ tạo nhạc không lời")
    duration: Optional[int] = Field(default=120, ge=10, le=300, description="Độ dài bài hát (giây, 10 - 300)")
    steps: Optional[int] = Field(default=25, ge=10, le=50, description="Số bước DiT diffusion (20 - 30)")
    dit_cfg: Optional[float] = Field(default=5.0, ge=1.0, le=10.0, description="CFG Guidance scale (1.0 - 10.0)")
    seed: Optional[int] = Field(default=-1, description="Seed ngẫu nhiên (-1 là random)")
    output_format: Optional[str] = Field(default="mp3", description="mp3, wav16, wav24")

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    created_at: float
    duration: int
    title: str
    error: Optional[str] = None
    download_url: Optional[str] = None

def build_caption(req: MusicGenerateRequest) -> str:
    if req.instrumental:
        return (
            f"### Global Metadata\nGenre & Style: {req.style}. Mood: Cinematic, melodic. Instrumental only.\n"
            f"### Vocal Details\nNo vocals. Strictly instrumental.\n"
            f"### Arrangement\nFull acoustic and electronic instrumentation, high dynamic range."
        )
    vocal_map = {
        "male": "One adult male lead singer, masculine tenor-to-baritone timbre, natural and emotional phrasing.",
        "female": "One adult female lead singer, feminine mezzo-soprano timbre, clean and emotional vocal delivery.",
        "duet": "Two distinct lead singers (one male and one female) alternating verses and harmonizing together in choruses.",
        "choir": "Mixed vocal ensemble and layered choir harmonies.",
        "auto": "Natural expressive lead vocals matching the genre.",
    }
    vocal_desc = vocal_map.get(req.vocal_mode.lower(), "Natural expressive lead vocals.")
    return (
        f"### Global Metadata\nGenre & Style: {req.style}. Production profile: high fidelity, studio master.\n"
        f"### Vocal Details\n{vocal_desc}\n"
        f"### Arrangement\nRich instrumentation, section dynamics, polished sound design."
    )

async def worker_loop():
    """Worker background tuần tự xử lý từng bài hát để tránh quá tải GPU/VRAM."""
    while True:
        task_id, req = await task_queue.get()
        try:
            tasks_db[task_id]["status"] = "processing"
            tasks_db[task_id]["progress"] = 10
            
            caption = build_caption(req)
            lyrics = "" if req.instrumental else (req.lyrics or "").strip()

            # Chạy inference trên thread riêng
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: mm_client.generate_music(
                    caption=caption,
                    lyrics=lyrics,
                    duration=req.duration,
                    steps=req.steps,
                    dit_cfg=req.dit_cfg,
                    seed=req.seed,
                    output_format=req.output_format,
                )
            )

            audio_bytes = result.get("audio_bytes")
            if not audio_bytes:
                raise RuntimeError("Không nhận được dữ liệu âm thanh từ inference engine.")

            ext = "mp3" if req.output_format == "mp3" else "wav"
            file_name = f"{task_id}.{ext}"
            file_path = OUTPUT_DIR / file_name
            with open(file_path, "wb") as f:
                f.write(audio_bytes)

            tasks_db[task_id]["status"] = "completed"
            tasks_db[task_id]["progress"] = 100
            tasks_db[task_id]["file_path"] = str(file_path)
            tasks_db[task_id]["download_url"] = f"/v1/music/tasks/{task_id}/download"

        except Exception as e:
            tasks_db[task_id]["status"] = "failed"
            tasks_db[task_id]["error"] = str(e)
            print(f"[!] Lỗi khi xử lý Task {task_id}: {e}")
        finally:
            task_queue.task_done()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(worker_loop())

@app.get("/health", tags=["System"])
def health_check():
    """Kiểm tra tình trạng hoạt động của API Gateway và mm-server."""
    server_ready = mm_client.health_check()
    return {
        "status": "ok" if server_ready else "degraded",
        "gateway": "running",
        "engine_connected": server_ready,
        "active_queue_size": task_queue.qsize(),
    }

@app.post("/v1/music/generate", response_model=TaskStatusResponse, tags=["Music Generation"])
async def generate_music(
    req: MusicGenerateRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    Tạo bài hát mới qua API.
    Hỗ trợ xử lý bất đồng bộ, trả về task_id để theo dõi tiến trình và tải file.
    """
    verify_api_key(x_api_key)

    if not mm_client.health_check():
        raise HTTPException(
            status_code=503,
            detail="Inference engine (mm-server) chưa sẵn sàng. Vui lòng đảm bảo start_server.bat đang chạy."
        )

    task_id = uuid.uuid4().hex[:16]
    task_info = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "created_at": time.time(),
        "duration": req.duration,
        "title": req.title or "Untitled",
        "error": None,
        "download_url": None,
    }
    tasks_db[task_id] = task_info

    await task_queue.put((task_id, req))
    return TaskStatusResponse(**task_info)

@app.get("/v1/music/tasks/{task_id}", response_model=TaskStatusResponse, tags=["Music Generation"])
def get_task_status(task_id: str, x_api_key: Optional[str] = Header(None)):
    """Kiểm tra trạng thái bài hát đang được tạo."""
    verify_api_key(x_api_key)
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy task_id")
    return TaskStatusResponse(**task)

@app.get("/v1/music/tasks/{task_id}/download", tags=["Music Generation"])
def download_music(task_id: str):
    """Tải trực tiếp tệp âm thanh MP3/WAV."""
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Không tìm thấy task_id")
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Task chưa hoàn tất (trạng thái: {task.get('status')})")

    file_path = task.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy tệp âm thanh trên đĩa")

    ext = Path(file_path).suffix.lstrip(".")
    media_type = "audio/mpeg" if ext == "mp3" else "audio/wav"
    filename = f"{task.get('title', 'song')}.{ext}"
    return FileResponse(file_path, media_type=media_type, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
