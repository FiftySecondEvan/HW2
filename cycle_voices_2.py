# maninthearena_every_word.py
# Speak each word with a different voice (rotating) and produce a single file.

import asyncio
import io
import os
import re
import wave
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

VOICES = [
    "alloy", "echo", "fable", "onyx", "nova", "shimmer",
    "coral", "verse", "ballad", "ash", "sage", "marin", "cedar",
]
MODEL = "gpt-4o-mini-tts"
INPUT_TXT = "teddyrooseveltquote.txt"
OUT_WAV = "maninthearena.wav"
OUT_MP3 = "maninthearena.mp3"
SILENCE_MS = 60  # short pad between words to reduce clicks

async def tts_wav_bytes(client: AsyncOpenAI, text: str, voice: str) -> bytes:
    """Stream a single word to WAV bytes using the given voice."""
    buf = bytearray()
    async with client.audio.speech.with_streaming_response.create(
        model=MODEL,
        voice=voice,
        input=text,
        response_format="wav",   # WAV lets us stitch clips without external tools
    ) as resp:
        async for chunk in resp.iter_bytes():
            if chunk:
                buf.extend(chunk)
    return bytes(buf)

def read_wav_params(wav_bytes: bytes):
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        return wf.getnchannels(), wf.getsampwidth(), wf.getframerate()

def extract_frames(wav_bytes: bytes) -> bytes:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        return wf.readframes(wf.getnframes())

def silence_pcm(nchannels: int, sampwidth: int, framerate: int, ms: int) -> bytes:
    frames = int(framerate * (ms / 1000.0))
    return b"\x00" * frames * nchannels * sampwidth

async def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in .env")
    client = AsyncOpenAI(api_key=api_key)

    # Read and tokenize text into "words" (keep punctuation attached to its word)
    src = Path(INPUT_TXT)
    if not src.exists():
        raise FileNotFoundError(f"{INPUT_TXT} not found.")
    text = src.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"{INPUT_TXT} is empty.")
    words = re.findall(r"\S+", text)
    if not words:
        raise SystemExit("No words found to synthesize.")

    print(f"Words to speak: {len(words)} | cycling voices: {len(VOICES)}")

    # Synthesize the first word to establish WAV params
    first_voice = VOICES[0]
    first_bytes = await tts_wav_bytes(client, words[0], first_voice)
    nch, sw, sr = read_wav_params(first_bytes)
    gap = silence_pcm(nch, sw, sr, SILENCE_MS)

    # Open final WAV for writing; set params from first clip
    with wave.open(OUT_WAV, "wb") as out_wf:
        out_wf.setnchannels(nch)
        out_wf.setsampwidth(sw)
        out_wf.setframerate(sr)

        # write first word
        out_wf.writeframes(extract_frames(first_bytes))
        out_wf.writeframes(gap)

        # loop remaining words, rotating voices
        for i, word in enumerate(words[1:], start=1):
            voice = VOICES[i % len(VOICES)]
            print(f"{i+1:04d}/{len(words):04d}  [{voice}]  {word}")
            try:
                wav_bytes = await tts_wav_bytes(client, word, voice)
                # sanity check: ensure params match (they should)
                nch2, sw2, sr2 = read_wav_params(wav_bytes)
                if (nch2, sw2, sr2) != (nch, sw, sr):
                    raise RuntimeError(f"Param mismatch from API for word '{word}'")
                out_wf.writeframes(extract_frames(wav_bytes))
                out_wf.writeframes(gap)
            except Exception as e:
                print(f"  (skip '{word}' with voice '{voice}': {e})")

    # Try to export MP3 if pydub+ffmpeg are available; otherwise keep WAV
    try:
        from pydub import AudioSegment  # requires ffmpeg in PATH
        AudioSegment.from_wav(OUT_WAV).export(OUT_MP3, format="mp3")
        print(f"\n✅ Saved {Path(OUT_MP3).resolve()} (and kept {OUT_WAV} too)")
    except Exception:
        print(f"\n✅ Saved {Path(OUT_WAV).resolve()} (install pydub+ffmpeg to also write MP3)")

if __name__ == "__main__":
    asyncio.run(main())
