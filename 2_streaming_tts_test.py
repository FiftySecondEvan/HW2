# 2_streaming_tts_test.py
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Try to use the SDK's local player if present; otherwise fall back.
try:
    from openai.audio import LocalAudioPlayer  # available in newer SDKs
    HAS_BUILTIN_PLAYER = True
except Exception:
    HAS_BUILTIN_PLAYER = False
    import io, tempfile, simpleaudio as sa, subprocess, sys

    class LocalAudioPlayer:
        def __init__(self, min_buffer_bytes: int = 64_000):
            self.buf = io.BytesIO()
            self.started = False
            self.min_buffer_bytes = min_buffer_bytes
            self.tmp_path = None

        async def stream_from(self, async_byte_iter):
            async for chunk in async_byte_iter:
                if not chunk:
                    continue
                self.buf.write(chunk)
                if not self.started and self.buf.tell() >= self.min_buffer_bytes:
                    self.started = True
                    await self._start_playback()
            # keep the file around if we couldn't auto-play
            return

        async def _start_playback(self):
            self.buf.seek(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                f.write(self.buf.read())
                self.tmp_path = f.name
            try:
                if sys.platform.startswith("darwin"):
                    subprocess.Popen(["open", self.tmp_path])
                elif sys.platform.startswith("win"):
                    os.startfile(self.tmp_path)  # type: ignore[attr-defined]
                else:
                    subprocess.Popen(["xdg-open", self.tmp_path])
            except Exception:
                print(f"Saved audio to: {self.tmp_path} (open manually if needed)")

async def main():
    # --- Setup ---
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in .env")

    client = AsyncOpenAI(api_key=api_key)

    # --- Ingest from teddyrooseveltquote.txt ---
    txt_path = Path("teddyrooseveltquote.txt")
    if not txt_path.exists():
        raise FileNotFoundError("teddyrooseveltquote.txt not found in this folder.")

    lines = [
        ln.strip() for ln in txt_path.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    if not lines:
        raise SystemExit("teddyrooseveltquote.txt is empty.")

    # --- Player & model config ---
    player = LocalAudioPlayer()
    model = "gpt-4o-mini-tts"
    voice = "alloy"
    fmt = "mp3"  # switch to "wav" if playback is finicky on your system

    print(f"Streaming {len(lines)} line(s) from {txt_path.name} "
          f"with model={model}, voice={voice} (SDK player: {HAS_BUILTIN_PLAYER})")

    # --- Stream each non-empty line ---
    for i, line in enumerate(lines, 1):
        print(f"\n▶️  Speaking line {i}/{len(lines)}: {line[:80]}{'...' if len(line)>80 else ''}")
        async with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=line,
            response_format=fmt,
        ) as response:
            await player.stream_from(response.iter_bytes())

    print("\nDone.")

if __name__ == "__main__":
    asyncio.run(main())
