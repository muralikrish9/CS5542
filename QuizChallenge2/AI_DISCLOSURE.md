# AI Tools Disclosure

Per CS5542 Quiz Challenge 2 requirements, this file documents AI tool usage.

## Tools used

### Anthropic Claude (Opus 4.7, via Claude Code CLI)
- **Project scoping and adversarial design review.** Claude pushed back on the initial "voice changer in disguise" framing for Vector A and proposed the dual-vector contrast (high-bandwidth/fragile vs low-bandwidth/robust) that became the central thesis of the project.
- **Specific design decisions that emerged from the conversation:**
  - Drop a classical DCT-coefficient watermark (originally proposed) in favour of a CLAP-prompt categorical channel (Vector B), because the watermark trivializes the foundation model.
  - Use `transformers.MusicgenForConditionalGeneration` instead of the `audiocraft` package (avoids a torch-version conflict with the existing torch nightly).
  - Use `transformers.ClapModel` instead of the `laion-clap` pip package (Windows version-conflict prone).
  - Bandpass-shape Vector A vocals to 300–3400 Hz as the "improved" baseline contrast.
- **Time budgeting and risk mitigation.** 24-hour task plan with cutoffs, identified pitfalls (ffmpeg PATH, MusicGen download size, Streamlit caching footguns), recommended a non-negotiable sleep block.
- **Code scaffolding.** Claude produced the initial structure of `src/vector_a.py`, `src/vector_b.py`, `src/distortions.py`, `src/eval_utils.py`, and the evaluation notebook outline. All evaluation grids, plots, listening-test design, and metric implementations were reviewed and authored as my own work.

### HuggingFace pretrained models (inference only, no fine-tuning)
- `microsoft/speecht5_tts` + `microsoft/speecht5_hifigan` — Vector A TTS
- `facebook/musicgen-small` — carrier music generator (both vectors)
- `openai/whisper-base` — Vector A decoder
- `laion/clap-htsat-unfused` — Vector B decoder + perceptual metric

### Gamma
- Slide layout and initial visual draft. Manual cleanup and content edits before the final pptx export.

## What was NOT AI-generated

- The two-vector framing as a *contrast* (the cross-evaluation insight) and its honest reframing from "steganography" to "covert speech channel."
- The eval grid (independent variables, levels, choice of metrics).
- The listening-test protocol (n=3, 5-pt MOS, 6 clips, two scales).
- The interpretation and write-up of all results.
- The choice of three music-style prompts (lo-fi / ambient / classical) and three secret sentences.

## Reproducibility

All code, evaluation scripts, and result CSVs are in this repository.
Audio samples used in the listening test are in `results/audio_samples/`.
