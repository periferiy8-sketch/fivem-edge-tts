from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import edge_tts
import asyncio
import io

app = FastAPI()

@app.get("/tts")
async def tts(
    text: str = Query(..., max_length=500),
    voice: str = Query("ru-RU-SvetlanaNeural"),
    rate: str = Query("-5%"),      # ← остаётся со знаком % или +/-
    volume: int = Query(0),        # ← ТОЛЬКО число от -100 до 100
    pitch: str = Query("+0Hz")     # ← остаётся с Hz
):
    allowed_voices = ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]
    if voice not in allowed_voices:
        voice = "ru-RU-SvetlanaNeural"

    # Ограничиваем volume
    volume = max(-100, min(100, volume))

    async def generate():
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,          # "-5%"
            volume=volume,      # 0 (без %)
            pitch=pitch         # "+2Hz"
        )
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        buffer.seek(0)
        return buffer

    try:
        audio = await generate()
        return StreamingResponse(audio, media_type="audio/mpeg")
    except Exception as e:
        return {"error": str(e)}