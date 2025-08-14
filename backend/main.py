from fastapi import FastAPI, UploadFile, File, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import tempfile, shutil, subprocess, uuid, os

from edudub.backend.gender_detector import assign_voices_by_speaker
from edudub.backend.whisper_translate import transcribe_and_translate
from edudub.backend.tts_client import generate_dub

app = FastAPI()

# ✅ CORS middleware for local frontend on http://localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend files if needed
frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_root():
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        return HTMLResponse(content=f"<h1>index.html not found at {index_path}</h1>", status_code=404)
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

@app.post("/dub/")
async def dub_video(background_tasks: BackgroundTasks, file: UploadFile = File(...), target_lang: str = "hi"):
    temp_dir = Path(tempfile.gettempdir()) / f"dub_{uuid.uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Save uploaded video
        original_video_path = temp_dir / "original.mp4"
        with open(original_video_path, "wb") as f:
            f.write(await file.read())
        print(f"[INFO] Video saved at {original_video_path}")

        # Step 0: Detect speaker gender and assign voices
        voice_map = assign_voices_by_speaker(str(original_video_path))
        print(f"[INFO] Assigned Voice Map: {voice_map}")

        # Step 1: Transcription & Translation
        # Step 1: Transcription & Translation
        transcribed_text = transcribe_and_translate(original_video_path.read_bytes(), target_lang)
        if (not transcribed_text or 
        not isinstance(transcribed_text, list) or 
        not transcribed_text[0].get("text", "").strip()):
            raise ValueError("Transcription failed or returned empty text")

# For printing:
        print(f"[INFO] Transcribed & Translated Text (first 100 chars): {transcribed_text[0]['text'][:100]}...")


        # Step 2: Generate audio dub
        dubbed_audio_path = generate_dub(transcribed_text, target_lang, voice_map=voice_map)
        if not dubbed_audio_path or not os.path.exists(dubbed_audio_path):
            raise RuntimeError("Failed to generate dubbed audio.")
        dubbed_audio_path = Path(dubbed_audio_path)
        print(f"[INFO] Dubbed audio saved at {dubbed_audio_path}")

        # Step 3: Merge original video with new audio
        output_video_path = temp_dir / "dubbed_video.mp4"
        cmd = [
            "ffmpeg", "-i", str(original_video_path),
            "-i", str(dubbed_audio_path),
            "-c:v", "copy", "-map", "0:v:0", "-map", "1:a:0",
            "-shortest", str(output_video_path), "-y"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"[FFmpeg stdout] {result.stdout}")
        print(f"[FFmpeg stderr] {result.stderr}")

        if not output_video_path.exists():
            raise RuntimeError("Failed to generate final dubbed video.")

        # ✅ Cleanup temp files after response
        background_tasks.add_task(shutil.rmtree, temp_dir, ignore_errors=True)

        return FileResponse(
            path=output_video_path,
            media_type="video/mp4",
            filename="dubbed_video.mp4"
        )

    except Exception as e:
        print(f"[ERROR] {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.websocket("/ws/dub")
async def websocket_dub(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("🔧 WebSocket dubbing not implemented yet.")

# Entry point for local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("edudub.backend.main:app", host="0.0.0.0", port=8000, reload=True)
