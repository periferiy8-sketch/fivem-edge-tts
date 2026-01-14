from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
import edge_tts
import asyncio

app = FastAPI()

# === Будильник для UptimeRobot ===
@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}

# === Основной TTS эндпоинт ===
@app.get("/tts")
async def tts(
    text: str = Query(..., max_length=500),
    voice: str = Query("ru-RU-SvetlanaNeural"),
    rate: str = Query("-5%"),
    volume: str = Query("+0%"),
    pitch: str = Query("+0Hz")
):
    allowed_voices = ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]
    if voice not in allowed_voices:
        voice = "ru-RU-SvetlanaNeural"
    if not volume.endswith('%'):
        volume = "+0%"

    async def audio_stream():
        try:
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=pitch
            )
            async for chunk in communicate.stream():
                if chunk["type"] == "audio" and chunk["data"]:
                    yield chunk["data"]
        except Exception as e:
            # Логируем ошибку (в Render будет в логах)
            print(f"TTS error: {e}")
            raise HTTPException(status_code=500, detail="TTS generation failed")

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")