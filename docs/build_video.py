#!/usr/bin/env python
"""Build docs/demo.mp4 from docs/video-slides.html.

Two narration sources:

  default        Windows SAPI per-scene narration (one WAV per scene).
  --audio FILE   use one pre-recorded narration track (e.g. MiniMax mp3).
                 Scene boundaries are estimated from each scene's narration
                 length, then snapped to the nearest detected pause so cuts
                 land between sentences, not mid-word.

Pipeline (Windows, no extra Python deps):
  1. parse each scene's data-narration from the HTML
  2. screenshot the scene at 1920x1080 with headless Chrome/Edge
  3. obtain the scene audio (SAPI, or a slice of --audio)
  4. mux image + audio into a segment with ffmpeg
  5. concatenate the segments into docs/demo.mp4

Requires: chrome or msedge, ffmpeg, PowerShell (SAPI). Examples:
    python docs/build_video.py
    python docs/build_video.py --audio "C:/Users/me/Downloads/narration.mp3"
"""
from __future__ import annotations

import argparse
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


def duration(media: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", str(media)],
                         check=True, capture_output=True, text=True)
    return float(out.stdout.strip())


def silences(media: Path, noise="-35dB", d=0.5) -> list[float]:
    out = subprocess.run(
        ["ffmpeg", "-i", str(media), "-af",
         f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"],
        capture_output=True, text=True)
    return [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out.stderr)]


def slice_audio(src: Path, start: float, end: float, out_m4a: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src), "-ss", f"{start:.3f}", "-to",
        f"{end:.3f}", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        str(out_m4a)], check=True, capture_output=True)


def segment(png: Path, audio: Path, out_mp4: Path, pad: float) -> None:
    dur = duration(audio) + max(0.0, pad)
    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", "30", "-i", str(png),
           "-i", str(audio)]
    if pad > 0:
        cmd += ["-af", f"apad=pad_dur={pad}"]
    cmd += ["-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-r", "30", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-t", f"{dur:.3f}", str(out_mp4)]
    subprocess.run(cmd, check=True, capture_output=True)


def scene_bounds(scenes: list[dict], total: float,
                 pause_points: list[float]) -> list[float]:
    weights = [max(1, len(s["narration"])) for s in scenes]
    cum, bounds = 0.0, [0.0]
    for w in weights:
        cum += w
        bounds.append(total * cum / sum(weights))
    for i in range(1, len(bounds) - 1):
        b = bounds[i]
        if pause_points:
            near = min(pause_points, key=lambda x: abs(x - b))
            if abs(near - b) <= 3.0:
                bounds[i] = near
    bounds[-1] = total
    for i in range(1, len(bounds)):
        if bounds[i] <= bounds[i - 1]:
            bounds[i] = bounds[i - 1] + 0.2
    return bounds


def concat(segs: list[Path], out: Path, tmp: Path) -> None:
    listfile = tmp / "list.txt"
    listfile.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs),
                        encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i",
                    str(listfile), "-c", "copy", str(out)],
                   check=True, capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audio", default=None,
                    help="single pre-recorded narration track (mp3/m4a/wav)")
    a = ap.parse_args()

    chrome = find_chrome()
    scenes = parse_scenes()
    tmp = Path(tempfile.mkdtemp(prefix="vlvid_"))
    profile = tmp / "chrome-profile"
    segs: list[Path] = []

    if a.audio:
        audio = Path(a.audio)
        total = duration(audio)
        pauses = silences(audio)
        bounds = scene_bounds(scenes, total, pauses)
        print(f"{len(scenes)} scenes, audio {total:.1f}s, "
              f"{len(pauses)} pauses -> {OUT}")
        for i, s in enumerate(scenes):
            png, aud, seg = tmp / f"s{s['n']}.png", tmp / f"s{s['n']}.m4a", \
                tmp / f"s{s['n']}.mp4"
            screenshot(chrome, s["n"], png, profile)
            slice_audio(audio, bounds[i], bounds[i + 1], aud)
            segment(png, aud, seg, 0.0)
            segs.append(seg)
            print(f"  scene {s['n']}: {duration(seg):4.1f}s "
                  f"({bounds[i]:.1f}-{bounds[i+1]:.1f})")
    else:
        print(f"{len(scenes)} scenes -> {OUT}")
        for s in scenes:
            png, wav, seg = tmp / f"s{s['n']}.png", tmp / f"s{s['n']}.wav", \
                tmp / f"s{s['n']}.mp4"
            screenshot(chrome, s["n"], png, profile)
            tts(s["narration"], wav)
            segment(png, wav, seg, 0.25)
            segs.append(seg)
            print(f"  scene {s['n']}: {duration(seg):4.1f}s  "
                  f"{s['narration'][:52]}...")

    concat(segs, OUT, tmp)
    total = duration(OUT)
    print(f"wrote {OUT}  ({total:.1f}s, {OUT.stat().st_size/1e6:.2f} MB)")
    if total > 180:
        print("WARNING: longer than 3 minutes")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
