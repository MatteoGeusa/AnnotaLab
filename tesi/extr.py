#!/usr/bin/env python3
"""
Extract the audio track from a video file using ffmpeg.

Requirements:
    ffmpeg installed and on your PATH
      - macOS:   brew install ffmpeg
      - Ubuntu:  sudo apt install ffmpeg
      - Windows: winget install ffmpeg   (or download from ffmpeg.org)

Usage:
    python extract_audio.py video.mp4                  # -> video.mp3
    python extract_audio.py video.mp4 -f wav           # -> video.wav
    python extract_audio.py video.mkv -o out.m4a       # custom output
    python extract_audio.py video.mp4 --copy           # no re-encode (fast, lossless)
    python extract_audio.py *.mp4 -f mp3 -b 320k       # batch, 320 kbps
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

CODECS = {
    "mp3": ["-c:a", "libmp3lame"],
    "wav": ["-c:a", "pcm_s16le"],
    "flac": ["-c:a", "flac"],
    "m4a": ["-c:a", "aac"],
    "aac": ["-c:a", "aac"],
    "ogg": ["-c:a", "libvorbis"],
    "opus": ["-c:a", "libopus"],
}
LOSSLESS = {"wav", "flac"}


def extract_audio(video: Path, output: Path, bitrate: str, copy: bool,
                  sample_rate: int | None, mono: bool) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-i", str(video), "-vn"]  # -vn = drop video

    if copy:
        cmd += ["-c:a", "copy"]
    else:
        fmt = output.suffix.lstrip(".").lower()
        if fmt not in CODECS:
            raise ValueError(f"Unsupported format '{fmt}'. Use one of: {', '.join(CODECS)}")
        cmd += CODECS[fmt]
        if fmt not in LOSSLESS:
            cmd += ["-b:a", bitrate]
        if sample_rate:
            cmd += ["-ar", str(sample_rate)]
        if mono:
            cmd += ["-ac", "1"]

    cmd.append(str(output))
    subprocess.run(cmd, check=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Extract audio from video files.")
    p.add_argument("videos", nargs="+", type=Path, help="Input video file(s)")
    p.add_argument("-o", "--output", type=Path,
                   help="Output file (only with a single input)")
    p.add_argument("-f", "--format", default="mp3", choices=CODECS.keys(),
                   help="Output format (default: mp3)")
    p.add_argument("-b", "--bitrate", default="192k",
                   help="Bitrate for lossy formats (default: 192k)")
    p.add_argument("--copy", action="store_true",
                   help="Copy the original audio stream without re-encoding")
    p.add_argument("--sample-rate", type=int, help="e.g. 16000 or 44100")
    p.add_argument("--mono", action="store_true", help="Downmix to mono")
    args = p.parse_args()

    if shutil.which("ffmpeg") is None:
        sys.exit("Error: ffmpeg not found. Install it and make sure it's on your PATH.")
    if args.output and len(args.videos) > 1:
        sys.exit("Error: --output can only be used with a single input file.")

    failures = 0
    for video in args.videos:
        if not video.is_file():
            print(f"✗ {video}: file not found", file=sys.stderr)
            failures += 1
            continue

        if args.output:
            out = args.output
        elif args.copy:
            # .mka (Matroska audio) can hold any codec, so it's a safe container for --copy
            out = video.with_suffix(".mka")
        else:
            out = video.with_suffix(f".{args.format}")

        try:
            extract_audio(video, out, args.bitrate, args.copy, args.sample_rate, args.mono)
            print(f"✓ {video} -> {out}")
        except (subprocess.CalledProcessError, ValueError) as e:
            print(f"✗ {video}: {e}", file=sys.stderr)
            failures += 1

    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()