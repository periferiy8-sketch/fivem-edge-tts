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
    volume: str = Query("+0%"),  # ← ДОЛЖЕН БЫТЬ СТРОКОЙ С %
    pitch: str = Query("+0Hz")
):
    allowed_voices = ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]
    if voice not in allowed_voices:
        voice = "ru-RU-SvetlanaNeural"

    # Убедимся, что volume в правильном формате
    if not volume.endswith('%'):
        volume = "+0%"

    async def generate():
        logger.info(f"Генерация: {text[:30]}... | Голос: {voice} | Скорость: {rate} | Громкость: {volume} | Тон: {pitch}")
        
        # Создаём Communicate с правильными параметрами
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,   # ← строка "+0%"
            pitch=pitch
        )
        
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