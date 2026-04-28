# MelodyLeak — slide content for Gamma

> Paste each `## Slide N` block into Gamma as a separate slide.
> Where a plot is referenced, attach `results/plots/NN_*.png`.

---

## Slide 1 — Title

**MelodyLeak**
*Foundation-Model Music as a Covert Speech Channel*

Murali Krishna Ediga · CS 5542 · Quiz Challenge 2 · Spring 2026
University of Missouri–Kansas City

---

## Slide 2 — Problem & motivation

Generative audio foundation models are now production-grade for *both directions*:

* **Generate** music and speech (MusicGen, SpeechT5, AudioLDM2)
* **Transcribe** speech (Whisper, wav2vec2)

Question: *can a single pipeline use both ends to smuggle a hidden message inside generated music?*

Why this matters: as generative-AI audio proliferates online, content provenance and covert-channel detection become open security problems. Demonstrating channels of this kind is a prerequisite to building defences.

---

## Slide 3 — Models used (HuggingFace, inference only)

| Role | Model | Params | License |
|---|---|---|---|
| TTS | `microsoft/speecht5_tts` + `speecht5_hifigan` | 144M | MIT |
| Carrier | `facebook/musicgen-small` | 300M | CC-BY-NC-4.0 |
| Decoder (Vector A) | `openai/whisper-base` | 74M | MIT |
| Decoder + perceptual (Vector B) | `laion/clap-htsat-unfused` | 153M | CC0 |

No fine-tuning. No training. All inference on a single RTX 5080 (≈3.4 GB VRAM total).

---

## Slide 4 — Two-vector design

```
SECRET ──┬── Vector A (semantic, high-bw, fragile)
         │       SpeechT5 ─┐
         │                 ├── mix at α dB ── Whisper ── recovered text
         │       MusicGen ─┘
         │
         └── Vector B (categorical, low-bw, robust)
                 secret bits → MusicGen prompt codebook (4 categories, 2 bits/clip) → CLAP cosine ── recovered bits
```

* **Vector A** trades secrecy for bandwidth: 5–10 bps of speech, but anyone listening hears it.
* **Vector B** trades bandwidth for secrecy: ~0.33 bps, but the carrier looks like ordinary music.

---

## Slide 5 — Prompt / input engineering

**Vector A.** Two mix variants compared:
* *flat:* full-band TTS vocals + music (baseline)
* *bandpass-shaped:* TTS vocals filtered to 300–3400 Hz (telephone band) before mixing — hypothesis: matches Whisper's training distribution better, should reduce WER at same loudness

**Vector B.** 4-prompt codebook over mood × tempo:

| bits | prompt |
|---|---|
| 00 | happy upbeat acoustic guitar pop, 140 bpm, major |
| 01 | happy warm soft acoustic guitar, 60 bpm, major |
| 10 | sad melancholic piano, 140 bpm, minor |
| 11 | sad melancholic piano, 60 bpm, minor |

---

## Slide 6 — Vector A results: WER vs α

`![results/plots/01_wer_vs_alpha.png]`

Three carrier styles, five gain levels, three secret sentences (n=45 runs).

**Findings.**
* **Ambient is the most permissive carrier** — WER stays ~0.18 across the entire α range (-6 to -30 dB).
* **Classical is the worst** — WER blows up past α=-18 dB; string formants compete with vocals in the same band.
* **Lo-fi sits between** — usable until α=-30 dB.

The carrier choice matters as much as the gain level.

---

## Slide 7 — Vector A: bandpass surprise

`![results/plots/02_flat_vs_bandpass.png]`

**Hypothesis:** bandpass-shaping vocals (300–3400 Hz) should *reduce* WER at the same loudness, because Whisper was trained heavily on telephone-band speech.

**Result:** bandpass-shaping **hurts**, especially on classical (WER 0.51 → 1.78) and lo-fi (0.16 → 0.32). Only ambient is roughly neutral.

**Interpretation:** Whisper relies on out-of-band fricatives (sibilants, /s/, /sh/) above 3.4 kHz that telephone-band filtering removes. The "improvement" backfires.

This is a counterintuitive finding worth its own line in the report.

---

## Slide 8 — Vector B results: BER under distortion

`![results/plots/03_ber_vs_distortion.png]`

20 generated clips × 7 distortion conditions (n=140 decodes).

**Headline:** BER **flat at 0.20** through MP3 (320 / 192 / 128 kbps), time-stretch ±5%, and AWGN at 30 dB. Only AWGN at 10 dB pushes BER up (0.40).

**The 0.20 is structural, not codec-induced.** Confusion matrix on clean audio:

| true → | 00 | 01 | 10 |
|---|---|---|---|
| 00 (happy fast) | **5/5** | 0 | 0 |
| 01 (happy slow) | 3 | 2 | 0 |
| 10 (sad fast) | 0 | 0 | **5/5** |
| 11 (sad slow) | 0 | 0 | 5 |

**CLAP perfectly discriminates mood (happy vs sad) but is tempo-blind.** A 1-bit mood-only codebook would give BER = 0 at all distortions tested — capacity halves, robustness jumps.

---

## Slide 9 — Cross-evaluation: dual failure modes

`![results/plots/04_cross_eval_scatter.png]`

* Vector A: ~50 bps speech, WER from 0.17 (α=-6) to 0.83 (α=-30) — **fragile to gain attenuation**.
* Vector B: ~0.33 bps, BER 0.20 across all codec/time-stretch conditions — **fragile to noise but not codec**.

**Insight.** *The two vectors fail in opposite directions.* A defence that catches Vector A (e.g., an audio-formant classifier) does not catch Vector B (no formants leaked). A defence that catches Vector B (prompt-distribution KL over a session) does not catch Vector A (one clip is enough). **Defending generative-AI audio covert channels requires more than one detector.**

---

## Slide 10 — Limitations, ethics, future work, AI disclosure

**Limitations.**
* `n=3` listening test (small)
* English-only secrets, single TTS speaker
* Single carrier model (MusicGen-small)
* No active steganalysis tested

**Ethics.** Demonstration of a covert channel as a prerequisite for *defensive* research. Vector A is detectable by anyone listening attentively — it is **not** perceptually-secure steganography. Vector B leaks via prompt-distribution biases over a session. Framed as a measurement of the attack surface, not a deployment guide.

**Future work.**
1. Adversarial perturbation of MusicGen output to fool Whisper while preserving human listening (gradient ascent on Whisper logits with perceptual constraint) — not feasible in 24 h.
2. Mood-only 1-bit Vector B + redundancy coding for near-zero BER.
3. Detection: train a Whisper-as-input classifier on (clean MusicGen) vs (vocal-mixed MusicGen).

**AI tools disclosure.**
* Anthropic Claude (this assistant) — adversarial design review, code scaffolding, slide outline. Specific decisions logged in `AI_DISCLOSURE.md`.
* HuggingFace pretrained models for inference only.
* Gamma for slide layout. All evaluation, plots, listening-test design, and write-up are author's own.

**Repo:** github.com/muralikrish9/CS5542 (`QuizChallenge2/`) — code, eval CSVs, plots, audio samples.
**Demo video:** *(insert YouTube link)*
