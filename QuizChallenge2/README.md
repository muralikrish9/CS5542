# MelodyLeak

> *Foundation-model music as a covert speech channel.*

Quiz Challenge 2 submission — CS 5542 (Big Data Analytics & AI), Spring 2026.

## What it is

Two-vector audio "steganography" pipeline that uses pretrained foundation models on both ends of the channel:

| Vector | Encoder | Decoder | Capacity | Robust to |
|---|---|---|---|---|
| **A — semantic** | SpeechT5 + MusicGen, mix at gain α | Whisper-base | high (≥ 5–10 bps text) | clean speech mixes; **fragile** under MP3 |
| **B — categorical** | MusicGen prompt codebook (4 prompts → 2 bits/clip) | CLAP text-audio cosine | low (~ 0.33 bps) | **robust to MP3, AWGN, time-stretch** |

The **insight** is the contrast: the two vectors fail in opposite ways. Defending against one does not defend against the other.

## Models used (all HuggingFace, inference only)

* `microsoft/speecht5_tts` + `microsoft/speecht5_hifigan` — Vector A TTS
* `facebook/musicgen-small` — carrier music generator (both vectors)
* `openai/whisper-base` — Vector A decoder
* `laion/clap-htsat-unfused` — Vector B decoder + perceptual metric

No fine-tuning. No training. All inference on a local RTX 5080.

## Repo layout

```
QuizChallenge2/
├── README.md                       # this file
├── requirements.txt                # pip deps
├── AI_DISCLOSURE.md                # AI tools used
├── src/
│   ├── vector_a.py                 # TTS + MusicGen + mix + Whisper
│   ├── vector_b.py                 # MusicGen codebook + CLAP decode
│   ├── distortions.py              # MP3 round-trip / AWGN / time-stretch
│   ├── eval_utils.py               # WER, BER, MCD
│   ├── run_eval.py                 # full eval grid -> results/*.csv
│   ├── make_plots.py               # results/*.csv -> results/plots/*.png
│   └── smoke_test.py               # 4-model load + 3s round-trip
├── notebooks/
│   ├── 01_demo_endtoend.ipynb      # narrative demo of both vectors
│   └── 02_evaluation.ipynb         # eval grid + plots
├── app/
│   └── gradio_app.py               # 2-tab demo (Vector A / Vector B)
├── data/
│   ├── secrets.txt                 # 3 ground-truth secrets
│   └── prompts.json                # 4-category Vector B codebook
├── results/
│   ├── results_vec_a.csv           # 54 Vector A runs
│   ├── results_vec_b.csv           # 140 Vector B decodes
│   ├── plots/                      # 5 PNGs for the deck
│   └── audio_samples/              # representative WAVs (incl. demo + listening test)
├── listening_test/
│   ├── form_template.md            # what listeners filled in
│   └── results.csv                 # n=3 MOS ratings
└── slides/
    └── QuizChallenge2.pptx
```

## How to run

```bash
pip install -r requirements.txt
# ffmpeg must be on PATH (Whisper + MP3 round-trip need it)
#   scoop install ffmpeg     (or)     winget install Gyan.FFmpeg

# 1) sanity check (loads all 4 models, 3-second round-trip)
python -m src.smoke_test

# 2) full eval grid (writes results/*.csv)
python -m src.run_eval

# 3) plots from CSVs
python -m src.make_plots

# 4) live demo
python app/gradio_app.py
```

GPU recommended (~3.4 GB total VRAM across all 4 models on float32).
First run pulls ~5 GB of HF weights to `~/.cache/huggingface/`.

## Eval grid (summary)

**Vector A:** 5 vocal-gain levels α ∈ {-6, -12, -18, -24, -30} dB × 3 music prompts × 3 secrets × 2 mix variants (flat baseline; bandpass-shaped 300–3400 Hz "improved", run only at α = -18 dB) = 54 runs. Metric: WER (Whisper-base).

**Vector B:** 4 codebook categories × 5 trials × 7 distortions {none, MP3 320/192/128 kbps, AWGN 30/10 dB, time-stretch ±5%} = 140 decodes. Metric: BER.

## Demo video

See `slides/` and the YouTube link in the deck.

## AI tools disclosure

See `AI_DISCLOSURE.md`.
