from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio

app = FastAPI()

# CORS — обязательно для FiveM NUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}

@app.get("/tts")
async def tts(
    text: str = Query(..., max_length=500),
    voice: str = Query("ru-RU-SvetlanaNeural"),
    rate: str = Query("-5%"),
    volume: str = Query("+0%"),
    pitch: str = Query("+0Hz"),
    mode: str = Query("buffer")  # ← НОВЫЙ ПАРАМЕТР
):
    allowed_voices = ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]
    if voice not in allowed_voices:
        voice = "ru-RU-SvetlanaNeural"
    if not volume.endswith('%'):
        volume = "+0%"

    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )

        if mode == "stream":
            # Режим 1: Streaming (быстро, без SSML)
            async def audio_stream():
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio" and chunk["data"]:
                        yield chunk["data"]
            return StreamingResponse(audio_stream(), media_type="audio/mpeg")

        else:
            # Режим 2: Buffer (медленнее, но с SSML)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio" and chunk["data"]:
                    audio_data += chunk["data"]
            if len(audio_data) == 0:
                raise HTTPException(status_code=500, detail="Empty audio generated")
            return Response(audio_data, media_type="audio/mpeg")

    except Exception as e:
        print(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")