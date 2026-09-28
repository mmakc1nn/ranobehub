"""Speech synthesis backed by Silero TTS (https://github.com/snakers4/silero-models)."""

import io
import os
import re
import threading

import torch
import torchaudio

# Package id per language, as published by snakers4/silero-models.
LANGUAGE_MODELS = {
    "ru": "v4_ru",
    "en": "v3_en",
}

DEFAULT_SAMPLE_RATE = 48000
MAX_CHUNK_CHARS = 800
MAX_TEXT_CHARS = 20_000

# Auto-detect CUDA; override with TTS_DEVICE=cpu / cuda / cuda:1 / mps.
DEVICE = torch.device(os.environ.get("TTS_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu"))

_lock = threading.Lock()
_model_cache: dict[str, torch.nn.Module] = {}


def get_model(language: str) -> torch.nn.Module:
    if language not in LANGUAGE_MODELS:
        raise ValueError(f"Unsupported language: {language}")
    with _lock:
        model = _model_cache.get(language)
        if model is None:
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language=language,
                speaker=LANGUAGE_MODELS[language],
                trust_repo=True,
            )
            model.to(DEVICE)
            _model_cache[language] = model
    return model


def list_speakers(language: str) -> list[str]:
    return list(get_model(language).speakers)


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+")


def split_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into speech-friendly chunks, preferring sentence boundaries."""
    text = text.strip()
    if not text:
        return []

    sentences = _SENTENCE_SPLIT_RE.split(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i:i + max_chars])
            continue

        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks


def synthesize(
    text: str,
    language: str,
    speaker: str,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> bytes:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"Text is too long (max {MAX_TEXT_CHARS} characters per request)")

    model = get_model(language)
    if speaker not in model.speakers:
        raise ValueError(f"Unknown speaker '{speaker}' for language '{language}'")

    chunks = split_into_chunks(text)
    if not chunks:
        raise ValueError("Text is empty")

    audio_parts = [
        model.apply_tts(text=chunk, speaker=speaker, sample_rate=sample_rate)
        for chunk in chunks
    ]
    full_audio = torch.cat(audio_parts) if len(audio_parts) > 1 else audio_parts[0]
    full_audio = full_audio.cpu()

    buffer = io.BytesIO()
    torchaudio.save(buffer, full_audio.unsqueeze(0), sample_rate, format="wav", backend="soundfile")
    buffer.seek(0)
    return buffer.read()
