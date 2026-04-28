# MelodyLeak — Listening Test (n=3)

You'll listen to 6 short audio clips. For each, rate two things on a 1–5 scale:

| Scale | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| **Music quality** (does this sound like clean music?) | clearly broken / unpleasant | obvious artifacts | noticeable but tolerable | mostly clean | indistinguishable from clean music |
| **Speech audibility** (can you hear words underneath?) | none | maybe a hum, no words | a few syllables | most words discernible | speech is clearly audible |

## Clips

The clips are in `results/audio_samples/`:

1. `vec_a_flat_lofi_a-6_s0.wav` — flat mix at α = -6 dB
2. `vec_a_flat_lofi_a-18_s0.wav` — flat mix at α = -18 dB
3. `vec_a_flat_lofi_a-30_s0.wav` — flat mix at α = -30 dB
4. `vec_a_bp_lofi_a-18_s0.wav` — bandpass-shaped mix at α = -18 dB
5. `vec_b_00.wav` — Vector B, "happy fast" category
6. `vec_b_11.wav` — Vector B, "sad slow" category

## Submission

Reply with a single CSV-pasted block matching `listening_test/results.csv`:

```
clip,listener,music_quality,speech_audibility
1,YOURNAME,4,2
2,YOURNAME,3,4
...
```

Plus any free-text observations.
