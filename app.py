from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import edge_tts
import asyncio
import io
import os

app = FastAPI()

@app.get("/tts")
async def tts(
    text: str = Query(..., max_length=500),
    voice: str = Query("ru-RU-SvetlanaNeural"),
    rate: str = Query("-5%"),
    volume: str = Query("+0%"),   # Должен быть строкой с %
    pitch: str = Query("+0Hz")
):
    allowed_voices = ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]
    if voice not in allowed_voices:
        voice = "ru-RU-SvetlanaNeural"
    if not volume.endswith('%'):
        volume = "+0%"

    async def generate():
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio" and chunk["data"]:
                buffer.write(chunk["data"])
        buffer.seek(0)
        return buffer

    try:
        audio = await generate()
        return StreamingResponse(audio, media_type="audio/mpeg")
    except Exception as e:
        return {"error": str(e)}