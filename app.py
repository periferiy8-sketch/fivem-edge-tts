from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import edge_tts
import asyncio
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

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

    async def generate():
        # Добавляем браузерные заголовки
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Origin": "https://www.bing.com",
            "Referer": "https://www.bing.com/"
        }
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch,
            proxy=None  # ← пока без прокси
        )
        # Устанавливаем заголовки
        communicate.session.headers.update(headers)
        
        buffer = io.BytesIO()
        audio_chunks = 0
        async for chunk in communicate.stream():
            if chunk["type"] == "audio" and chunk["data"]:
                buffer.write(chunk["data"])
                audio_chunks += 1
        if audio_chunks == 0:
            logger.error("Аудио не сгенерировано")
            return None
        buffer.seek(0)
        return buffer

    try:
        audio_buffer = await generate()
        if audio_buffer is None:
            return {"error": "Не удалось сгенерировать аудио"}
        return StreamingResponse(audio_buffer, media_type="audio/mpeg")
    except Exception as e:
        logger.exception("Ошибка в TTS")
        return {"error": str(e)}