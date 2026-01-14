from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import edge_tts
import asyncio
from pydub import AudioSegment
import io

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

    try:
        mp3_buffer = io.BytesIO()
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )
        async for chunk in communicate.stream():
            if chunk["type"] == "audio" and chunk["data"]:
                mp3_buffer.write(chunk["data"])
        mp3_buffer.seek(0)

        if mp3_buffer.getbuffer().nbytes == 0:
            raise HTTPException(status_code=500, detail="Empty audio generated")

        # Декодируем MP3 → аудио-объект
        audio = AudioSegment.from_file(mp3_buffer, format="mp3")

        # Приводим частоту к совместимой с CEF (22050 Гц)
        if audio.frame_rate not in (22050, 44100):
            audio = audio.set_frame_rate(22050)

        # Экспорт в OGG с параметрами, совместимыми с FiveM
        ogg_buffer = io.BytesIO()
        audio.export(
            ogg_buffer,
            format="ogg",
            codec="libvorbis",
            bitrate="96k"
        )
        ogg_data = ogg_buffer.getvalue()

        return Response(ogg_data, media_type="audio/ogg")

    except Exception as e:
        print(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")