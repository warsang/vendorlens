#!/usr/bin/env python
"""Build docs/demo.mp4 from docs/video-slides.html.

Pipeline (Windows, no extra Python deps):
  1. parse each scene's data-narration from the HTML
  2. screenshot the scene at 1920x1080 with headless Chrome/Edge
  3. synthesize the narration to WAV with Windows SAPI (System.Speech)
  4. mux image + audio into a segment with ffmpeg
  5. concatenate the segments into docs/demo.mp4

Requires: chrome or msedge, ffmpeg, PowerShell (for SAPI). Re-run any time the
slides change:
    python docs/build_video.py
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DOCS = Path(__file__).resolve().parent
SLIDES = DOCS / "video-slides.html"
OUT = DOCS / "demo.mp4"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    found = shutil.which("chrome") or shutil.which("msedge")
    if found:
        return found
    raise SystemExit("no Chrome/Edge found")


def parse_scenes() -> list[dict]:
    raw = SLIDES.read_text(encoding="utf-8")
    scenes = []
    for m in re.finditer(r'<section class="scene"[^>]*data-s="(\d+)"'
                         r'(?:\s+data-narration="([^"]*)")?', raw):
        scenes.append({"n": int(m.group(1)),
                       "narration": html.unescape(m.group(2) or "")})
    scenes.sort(key=lambda s: s["n"])
    if not scenes:
        raise SystemExit("no scenes parsed from " + str(SLIDES))
    return scenes


def screenshot(chrome: str, n: int, out_png: Path, profile: Path) -> None:
    url = SLIDES.resolve().as_uri() + f"?scene={n}"
    subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check",
        f"--user-data-dir={profile}", "--window-size=1920,1080",
        f"--screenshot={out_png}", url,
    ], check=True, capture_output=True)
    if not out_png.exists():
        raise SystemExit(f"scene {n}: screenshot not produced")


def tts(text: str, out_wav: Path) -> None:
    script = out_wav.with_suffix(".ps1")
    script.write_text(
        "param([string]$txtPath,[string]$wav)\n"
        "Add-Type -AssemblyName System.Speech\n"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer\n"
        "$s.Rate = 1\n"
        "$s.SetOutputToWaveFile($wav)\n"
        "$s.Speak((Get-Content -Raw -Encoding UTF8 $txtPath))\n"
        "$s.Dispose()\n", encoding="utf-8")
    txt = out_wav.with_suffix(".txt")
    txt.write_text(text, encoding="utf-8")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-File", str(script), "-txtPath", str(txt), "-wav",
                    str(out_wav)], check=True, capture_output=True)
    if not out_wav.exists() or out_wav.stat().st_size < 1000:
        raise SystemExit(f"TTS failed for: {text[:40]}...")


def segment(png: Path, wav: Path, out_mp4: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(png),
        "-i", str(wav), "-af", "apad=pad_dur=0.25",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-r", "30", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-shortest", str(out_mp4),
    ], check=True, capture_output=True)


def duration(mp4: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", str(mp4)],
                         check=True, capture_output=True, text=True)
    return float(out.stdout.strip())


def main() -> int:
    chrome = find_chrome()
    scenes = parse_scenes()
    tmp = Path(tempfile.mkdtemp(prefix="vlvid_"))
    profile = tmp / "chrome-profile"
    print(f"{len(scenes)} scenes -> {OUT}")
    segs = []
    for s in scenes:
        n = s["n"]
        png, wav, seg = tmp / f"s{n}.png", tmp / f"s{n}.wav", tmp / f"s{n}.mp4"
        screenshot(chrome, n, png, profile)
        tts(s["narration"], wav)
        segment(png, wav, seg)
        d = duration(seg)
        segs.append(seg)
        print(f"  scene {n}: {d:4.1f}s  {s['narration'][:52]}...")
    listfile = tmp / "list.txt"
    listfile.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs),
                        encoding="utf-8")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listfile),
        "-c", "copy", str(OUT)], check=True, capture_output=True)
    total = duration(OUT)
    print(f"wrote {OUT}  ({total:.1f}s, {OUT.stat().st_size/1e6:.2f} MB)")
    if total > 180:
        print("WARNING: longer than 3 minutes")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
