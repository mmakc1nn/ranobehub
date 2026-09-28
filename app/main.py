from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import tts

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Ranobe Reader TTS")


class SpeakRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=tts.MAX_TEXT_CHARS)
    language: str = "ru"
    speaker: str
    sample_rate: int = tts.DEFAULT_SAMPLE_RATE


@app.get("/api/languages")
def get_languages():
    return {"languages": list(tts.LANGUAGE_MODELS.keys())}


@app.get("/api/voices")
def get_voices(language: str = "ru"):
    try:
        return {"language": language, "speakers": tts.list_speakers(language)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/speak")
def speak(payload: SpeakRequest):
    try:
        audio_bytes = tts.synthesize(
            text=payload.text,
            language=payload.language,
            speaker=payload.speaker,
            sample_rate=payload.sample_rate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(content=audio_bytes, media_type="audio/wav")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
