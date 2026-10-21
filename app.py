# app.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import asyncio

# === ПАТЧ ДЛЯ ОБХОДА 403 (новый адрес Microsoft) ===
import edge_tts.communicate
import edge_tts.constants

edge_tts.constants.WSS_URL = "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"

_original_init = edge_tts.communicate.Communicate.__init__
def _patched_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    self._headers["Ocp-Apim-Subscription-Key"] = "6A5AA1D4EAFF4E9FB37E23D68491D6F4"
    if "TrustedClientToken" in self._headers:
        del self._headers["TrustedClientToken"]
edge_tts.communicate.Communicate.__init__ = _patched_init
# === КОНЕЦ ПАТЧА ===

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
async def test():
    return {
        "status": "updated",
        "version": "2.2",
        "ssml_support": True,
        "modes": ["stream", "buffer"],
        "message": "Patched for new MS endpoint"
    }

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
    mode: str = Query("buffer")
):
    print(f"[TTS DEBUG] Received mode={mode}, text preview: {repr(text[:30])}")

    allowed_voices = ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"]
    if voice not in allowed_voices:
        voice = "ru-RU-SvetlanaNeural"
    if not volume.endswith('%'):
        volume = "+0%"

    try:
        clean_text = text.strip()
        if clean_text.startswith("<") and not clean_text.startswith("<speak"):
            clean_text = f"<speak>{clean_text}</speak>"

        communicate = edge_tts.Communicate(
            text=clean_text,
            voice=voice,
            rate=rate,
            volume=volume,
            pitch=pitch
        )

        if mode == "stream":
            async def audio_stream():
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio" and chunk["data"]:
                        yield chunk["data"]
            return StreamingResponse(audio_stream(), media_type="audio/mpeg")
        else:
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio" and chunk["data"]:
                    audio_data += chunk["data"]
            if len(audio_data) == 0:
                raise HTTPException(status_code=500, detail="Empty audio generated")
            return Response(audio_data, media_type="audio/mpeg")

    except Exception as e:
        print(f"[TTS ERROR] {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")