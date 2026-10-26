#!/usr/bin/env python3
"""Transcribe audio/video files locally with faster-whisper.

Usage:
    python transcribe.py recording.m4a
    python transcribe.py ~/Recordings --model medium --output-dir transcripts --srt
"""
import argparse
import sys
import time
from pathlib import Path

AUDIO_EXTS = {
    ".m4a", ".mp3", ".wav", ".flac", ".ogg", ".opus", ".aac", ".wma",
    ".mp4", ".mov", ".mkv", ".webm", ".avi", ".3gp", ".amr",
}


def find_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_EXTS)
    sys.exit(f"Not found: {target}")


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def pick_device() -> tuple[str, str]:
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def main() -> None:
    ap = argparse.ArgumentParser(description="Transcribe recordings to .txt (and optionally .srt) locally.")
    ap.add_argument("input", type=Path, help="audio/video file or folder of recordings")
    ap.add_argument("--model", default="small", help="tiny, base, small, medium, large-v3, turbo (default: small)")
    ap.add_argument("--language", default="en", help="language code, or 'auto' to detect (default: en)")
    ap.add_argument("--output-dir", type=Path, help="where to write transcripts (default: next to each file)")
    ap.add_argument("--srt", action="store_true", help="also write .srt subtitles")
    args = ap.parse_args()

    files = find_files(args.input)
    if not files:
        sys.exit(f"No audio files found in {args.input}")
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    todo = []
    for f in files:
        out_dir = args.output_dir or f.parent
        txt = out_dir / (f.stem + ".txt")
        if txt.exists():
            print(f"skip  {f.name} (transcript exists)")
        else:
            todo.append((f, txt))
    if not todo:
        print("Nothing to do.")
        return

    from faster_whisper import WhisperModel

    device, compute_type = pick_device()
    print(f"Loading model '{args.model}' on {device} ({compute_type})...")
    try:
        model = WhisperModel(args.model, device=device, compute_type=compute_type)
    except Exception as e:
        sys.exit(
            f"Could not load model '{args.model}': {e}\n"
            "The first run downloads the model from huggingface.co (one-time, model weights only;\n"
            "your audio never leaves this machine). Check your internet connection, or pass a\n"
            "local model folder path to --model."
        )
    language = None if args.language == "auto" else args.language

    total_start = time.time()
    for i, (f, txt) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {f.name} ...", flush=True)
        start = time.time()
        try:
            segments, info = model.transcribe(str(f), language=language, vad_filter=True)
            segments = list(segments)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        txt.write_text("\n".join(s.text.strip() for s in segments) + "\n", encoding="utf-8")
        if args.srt:
            srt = txt.with_suffix(".srt")
            blocks = [
                f"{n}\n{srt_time(s.start)} --> {srt_time(s.end)}\n{s.text.strip()}\n"
                for n, s in enumerate(segments, 1)
            ]
            srt.write_text("\n".join(blocks), encoding="utf-8")
        took = time.time() - start
        print(f"  done: {info.duration:.0f}s audio in {took:.1f}s -> {txt}")
    print(f"Finished {len(todo)} file(s) in {time.time() - total_start:.1f}s.")


if __name__ == "__main__":
    main()
