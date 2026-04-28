"""Full evaluation grid for both vectors.

Vector A: 5 alpha levels x 3 music prompts x 3 secrets x 2 mix variants
  (bandpass variant only at alpha=-18 dB; flat variant at all alphas)
  = 45 + 9 = 54 runs

Vector B: 4 categories x 5 trials x 7 distortions
  = 20 unique clips x 7 distortions = 140 decodes (clips reused across distortions)

Outputs:
  results/results_vec_a.csv
  results/results_vec_b.csv
"""
from __future__ import annotations
import time
import json
from pathlib import Path
import numpy as np
import pandas as pd
import soundfile as sf
import torch
import librosa

from . import vector_a as va
from . import vector_b as vb
from . import distortions as dx
from .eval_utils import wer, ber, mel_cepstral_distortion

ROOT = Path(__file__).parent.parent
RESULTS = ROOT / "results"
SAMPLES = RESULTS / "audio_samples"
RESULTS.mkdir(parents=True, exist_ok=True)
SAMPLES.mkdir(parents=True, exist_ok=True)

# === config ===
ALPHAS_DB = [-6, -12, -18, -24, -30]
PROMPTS = [
    ("lofi", "lo-fi hip-hop, soft piano, 60 bpm, mellow"),
    ("ambient", "ambient pad, ethereal, slow, atmospheric"),
    ("classical", "classical string quartet, baroque style, 80 bpm"),
]
SECRETS_FILE = ROOT / "data" / "secrets.txt"
SECRETS = [s.strip() for s in SECRETS_FILE.read_text(encoding="utf-8").splitlines() if s.strip()]
MUSIC_SECONDS = 10.0


def _t0(label):
    return time.time(), label


def _t1(t0, n=None):
    dt = time.time() - t0[0]
    extra = f" ({n} items, {dt/max(n,1):.2f}s/item)" if n else ""
    print(f"[eval] {t0[1]} done in {dt:.1f}s{extra}")


# === Vector A ===

def run_vector_a() -> pd.DataFrame:
    rows = []

    # Pre-generate music: one 10s clip per (prompt, seed) used across all secrets, alphas
    print("[eval] Vector A: generating 3 music clips...")
    music_cache = {}
    t0 = _t0("music gen")
    for pid, prompt in PROMPTS:
        audio, sr = va.musicgen(prompt, seconds=MUSIC_SECONDS, seed=42)
        music_cache[pid] = (audio, sr, prompt)
        sf.write(SAMPLES / f"music_{pid}.wav", audio, sr)
    _t1(t0, len(PROMPTS))

    # Pre-generate TTS for each secret
    print(f"[eval] Vector A: generating {len(SECRETS)} TTS clips...")
    tts_cache = {}
    t0 = _t0("TTS gen")
    for i, secret in enumerate(SECRETS):
        v = va.tts(secret)
        tts_cache[i] = v
        sf.write(SAMPLES / f"tts_{i}.wav", v, va.SR)
    _t1(t0, len(SECRETS))

    # 5 alpha x 3 prompts x 3 secrets x flat = 45 runs
    print("[eval] Vector A: 45 flat-variant mix+decode runs...")
    t0 = _t0("flat runs")
    for alpha_db in ALPHAS_DB:
        for pid, _ in PROMPTS:
            music_audio, music_sr, prompt = music_cache[pid]
            for sid, secret in enumerate(SECRETS):
                vocals = tts_cache[sid]
                mixed = va.mix(vocals, music_audio, music_sr, alpha_db=alpha_db, variant="flat")
                # save only one representative per (alpha, prompt) to limit disk
                if sid == 0:
                    sf.write(SAMPLES / f"vec_a_flat_{pid}_a{alpha_db}_s0.wav", mixed, va.SR)
                hyp = va.decode(mixed)
                w = wer(secret, hyp)
                # mel-cep distortion vs music_16k
                music_16k = librosa.resample(music_audio, orig_sr=music_sr, target_sr=va.SR)
                m = min(len(music_16k), len(mixed))
                mcd = mel_cepstral_distortion(music_16k[:m], mixed[:m], sr=va.SR)
                rows.append({
                    "vector": "A",
                    "variant": "flat",
                    "alpha_db": alpha_db,
                    "prompt_id": pid,
                    "music_prompt": prompt,
                    "secret_id": sid,
                    "secret": secret,
                    "hyp": hyp,
                    "wer": w,
                    "mcd": mcd,
                })
    _t1(t0, 45)

    # bandpass at alpha=-18 dB only: 1 alpha x 3 prompts x 3 secrets = 9 runs
    print("[eval] Vector A: 9 bandpass-variant runs at alpha=-18 dB...")
    t0 = _t0("bandpass runs")
    for pid, _ in PROMPTS:
        music_audio, music_sr, prompt = music_cache[pid]
        for sid, secret in enumerate(SECRETS):
            vocals = tts_cache[sid]
            mixed = va.mix(vocals, music_audio, music_sr, alpha_db=-18.0, variant="bandpass")
            if sid == 0:
                sf.write(SAMPLES / f"vec_a_bp_{pid}_a-18_s0.wav", mixed, va.SR)
            hyp = va.decode(mixed)
            w = wer(secret, hyp)
            music_16k = librosa.resample(music_audio, orig_sr=music_sr, target_sr=va.SR)
            m = min(len(music_16k), len(mixed))
            mcd = mel_cepstral_distortion(music_16k[:m], mixed[:m], sr=va.SR)
            rows.append({
                "vector": "A",
                "variant": "bandpass",
                "alpha_db": -18.0,
                "prompt_id": pid,
                "music_prompt": prompt,
                "secret_id": sid,
                "secret": secret,
                "hyp": hyp,
                "wer": w,
                "mcd": mcd,
            })
    _t1(t0, 9)

    df = pd.DataFrame(rows)
    return df


# === Vector B ===

def run_vector_b() -> pd.DataFrame:
    rows = []

    # 4 categories x 5 trials = 20 unique clips
    print("[eval] Vector B: generating 20 clips (4 categories x 5 trials)...")
    book = vb.codebook()
    clips = []  # list of (bits, prompt, audio, sr, trial)
    t0 = _t0("clip gen")
    for trial in range(5):
        for c in book:
            audio, sr = vb.musicgen_clip(c["prompt"], seconds=6.0, seed=1000 * trial + int(c["bits"], 2))
            clips.append({
                "bits": c["bits"],
                "prompt": c["prompt"],
                "audio": audio,
                "sr": sr,
                "trial": trial,
            })
    _t1(t0, len(clips))

    # save one clip per category for the listening test + demo
    saved = set()
    for cl in clips:
        if cl["bits"] not in saved:
            sf.write(SAMPLES / f"vec_b_{cl['bits']}.wav", cl["audio"], cl["sr"])
            saved.add(cl["bits"])

    # apply each distortion + decode
    print(f"[eval] Vector B: applying {len(dx.DISTORTIONS)} distortions x {len(clips)} clips...")
    t0 = _t0("distort+decode")
    for dist_name, dist_fn in dx.DISTORTIONS:
        for cl in clips:
            try:
                distorted = dist_fn(cl["audio"], cl["sr"])
            except Exception as e:
                rows.append({
                    "vector": "B",
                    "distortion": dist_name,
                    "trial": cl["trial"],
                    "true_bits": cl["bits"],
                    "pred_bits": "",
                    "ber": 1.0,
                    "error": str(e),
                })
                continue
            try:
                pred, sims = vb.decode_clip(distorted, cl["sr"])
            except Exception as e:
                rows.append({
                    "vector": "B",
                    "distortion": dist_name,
                    "trial": cl["trial"],
                    "true_bits": cl["bits"],
                    "pred_bits": "",
                    "ber": 1.0,
                    "error": str(e),
                })
                continue
            b = ber(cl["bits"], pred)
            rows.append({
                "vector": "B",
                "distortion": dist_name,
                "trial": cl["trial"],
                "true_bits": cl["bits"],
                "pred_bits": pred,
                "ber": b,
                "sim_00": float(sims[0]),
                "sim_01": float(sims[1]),
                "sim_10": float(sims[2]),
                "sim_11": float(sims[3]),
            })
    _t1(t0, len(clips) * len(dx.DISTORTIONS))

    df = pd.DataFrame(rows)
    return df


def main():
    print(f"[eval] device: {va.DEVICE}")
    print(f"[eval] secrets: {len(SECRETS)} | prompts: {len(PROMPTS)} | alphas: {ALPHAS_DB}")

    print("\n=== Vector A ===")
    df_a = run_vector_a()
    df_a.to_csv(RESULTS / "results_vec_a.csv", index=False)
    print(f"[eval] saved {len(df_a)} rows -> results_vec_a.csv")
    print(df_a.groupby(["alpha_db", "variant"])["wer"].mean().round(3).to_string())

    print("\n=== Vector B ===")
    df_b = run_vector_b()
    df_b.to_csv(RESULTS / "results_vec_b.csv", index=False)
    print(f"[eval] saved {len(df_b)} rows -> results_vec_b.csv")
    print(df_b.groupby("distortion")["ber"].mean().round(3).to_string())

    print("\n[eval] DONE.")


if __name__ == "__main__":
    main()
