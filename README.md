# Local voice-to-text (faster-whisper)

Transcribes recordings into `.txt` (and optionally `.srt`) files on this machine.
Audio never leaves the computer. The only network access is a one-time download
of the model weights from huggingface.co the first time you use each model size.
After that, it works fully offline.

## One-time setup

Requires Python 3.9+ and ffmpeg (`brew install ffmpeg` / `winget install ffmpeg` / `sudo apt install ffmpeg`).

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip install -r requirements.txt
```

## Usage

```bash
# one file -> recording.txt next to it
.venv/bin/python transcribe.py recording.m4a

# a whole folder (searched recursively), transcripts collected in one place, plus subtitles
.venv/bin/python transcribe.py ~/Recordings --output-dir transcripts --srt

# better accuracy, or a non-English / unknown language
.venv/bin/python transcribe.py interview.mp3 --model medium --language auto
```

Options:

| Flag | Default | Meaning |
|---|---|---|
| `--model` | `small` | `tiny`, `base`, `small`, `medium`, `large-v3`, `turbo`, or a path to a local model folder |
| `--language` | `en` | language code (`de`, `fr`, ...) or `auto` to detect |
| `--output-dir` | next to each file | where `.txt` / `.srt` files go |
| `--srt` | off | also write timestamped subtitles |

Files that already have a `.txt` transcript are skipped. To redo one, delete its `.txt`.
Supported inputs: m4a, mp3, wav, flac, ogg, opus, aac, wma, mp4, mov, mkv, webm, avi, 3gp, amr.

## Which model?

It uses an NVIDIA GPU automatically if one is available, otherwise the CPU (int8).
These are rough CPU speeds on a modern 4–8 core machine:

| Model | Download | Speed (CPU) | Accuracy | Use when |
|---|---|---|---|---|
| `tiny` | 75 MB | ~10–20x real-time | rough | quick drafts, clear audio |
| `base` | 145 MB | ~7–10x | okay | fast notes |
| `small` | 480 MB | ~3–5x | good | **default, best balance** |
| `medium` | 1.5 GB | ~1–2x | very good | accents, noisy rooms |
| `turbo` | 1.6 GB | ~1.5–3x | near large | best quality per second; good on GPU |
| `large-v3` | 3 GB | below 1x on CPU | best | when accuracy matters most (GPU recommended) |

"5x real-time" means a 10-minute recording takes about 2 minutes.
Models ending in `.en` (for example `small.en`) are slightly more accurate for English-only audio.

## Quick test

`samples/` has two short generated speech clips. Run
`.venv/bin/python transcribe.py samples --srt` and check the `.txt` files that appear.
