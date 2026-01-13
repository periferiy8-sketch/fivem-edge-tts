from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import edge_tts
import asyncio
import io

app = FastAPI(title="Edge TTS for FiveM", version="1.0")

@app.get("/tts")
async def tts(
    text: str = Query(..., max_length=500),
    voice: str = Query("ru-RU-SvetlanaNeural"),
    rate: str = Query("0%"),
    volume: str = Query("0%"),
    pitch: str = Query("0Hz")
):
    # Валидация голоса
    allowed_voices = ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]
    if voice not in allowed_voices:
        voice = "ru-RU-SvetlanaNeural"

    async def generate_audio():
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )
        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])
        audio_buffer.seek(0)
        return audio_buffer

    try:
        audio_stream = await generate_audio()
        return StreamingResponse(audio_stream, media_type="audio/mpeg")
    except Exception as e:
        return {"error": str(e)}