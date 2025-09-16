import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AsyncOpenAI

INPUT_TXT = "teddyrooseveltquote.txt"
OUTFILE = "maninthearena.mp3"
MODEL = "gpt-4o-mini-tts"
VOICE = "fable"  # stand-in for “Obama”-style narration

async def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in .env")

    src = Path(INPUT_TXT)
    if not src.exists():
        raise FileNotFoundError(f"{INPUT_TXT} not found in this folder.")
    text = src.read_text(encoding="utf-8").strip()
    if not text:
        raise SystemExit(f"{INPUT_TXT} is empty.")

    client = AsyncOpenAI(api_key=api_key)
    print(f"Narrating '{src.name}' with voice='{VOICE}' → {OUTFILE}")

    # Stream straight to an MP3 file (no temp tools required)
    async with client.audio.speech.with_streaming_response.create(
        model=MODEL,
        voice=VOICE,
        input=text,
        response_format="mp3",
    ) as resp:
        with open(OUTFILE, "wb") as f:
            async for chunk in resp.iter_bytes():
                if chunk:
                    f.write(chunk)

    print(f"✅ Saved: {Path(OUTFILE).resolve()}")

if __name__ == "__main__":
    asyncio.run(main())
