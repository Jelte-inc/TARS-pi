from fastapi import FastAPI, Request, BackgroundTasks
import aiofiles
from audio_player import play_audio

app = FastAPI()

@app.post("/upload-audio")
async def upload_audio(request: Request, background: BackgroundTasks):
    filename = request.headers.get("X-Filename", "upload.raw")
    out_path = f"received_audio_files/{filename}"

    async with aiofiles.open(out_path, "wb") as buffer:
        async for chunk in request.stream():
            await buffer.write(chunk)

    background.add_task(play_audio, path=out_path)

    return {"status": "ok", "saved_as": out_path}
