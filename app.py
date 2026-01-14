from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response
import edge_tts
import asyncio
from pydub import AudioSegment
import io

app = FastAPI()

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}

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

        audio = AudioSegment.from_file(mp3_buffer, format="mp3")
        ogg_buffer = io.BytesIO()
        audio.export(ogg_buffer, format="ogg", codec="libvorbis")
        ogg_data = ogg_buffer.getvalue()

        return Response(ogg_data, media_type="audio/ogg")

    except Exception as e:
        print(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")