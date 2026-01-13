from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
import edge_tts
import asyncio
import io
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/tts")
async def tts(
    text: str = Query(..., max_length=500),
    voice: str = Query("ru-RU-SvetlanaNeural"),
    rate: str = Query("-5%"),
    volume: int = Query(0),   # ← только число
    pitch: str = Query("+0Hz")
):
    allowed_voices = ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]
    if voice not in allowed_voices:
        voice = "ru-RU-SvetlanaNeural"

    volume = max(-100, min(100, volume))

    async def generate():
        logger.info(f"Генерация для: {text[:50]}... | Голос: {voice} | Скорость: {rate} | Громкость: {volume} | Тон: {pitch}")
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )
        buffer = io.BytesIO()
        audio_chunks = 0
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                if chunk["data"]:
                    buffer.write(chunk["data"])
                    audio_chunks += 1
                    logger.info(f"Чанк аудио: {len(chunk['data'])} байт")
                else:
                    logger.warning("Получен пустой чанк аудио")
        
        if audio_chunks == 0:
            logger.error("Не было получено ни одного чанка аудио!")
            return None
        
        buffer.seek(0)
        return buffer

    try:
        audio_buffer = await generate()
        if audio_buffer is None:
            return {"error": "Не удалось сгенерировать аудио. Проверьте текст и параметры."}
        
        return StreamingResponse(audio_buffer, media_type="audio/mpeg")
    except Exception as e:
        logger.exception("Ошибка при генерации аудио")
        return {"error": str(e)}