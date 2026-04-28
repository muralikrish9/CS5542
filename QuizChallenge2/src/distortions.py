"""Audio distortions for robustness evaluation: MP3 round-trip, AWGN, time-stretch."""
from __future__ import annotations
import subprocess
import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa


def mp3_roundtrip(audio: np.ndarray, sr: int, bitrate_kbps: int = 192) -> np.ndarray:
    """Encode -> MP3 at `bitrate_kbps` -> decode -> WAV. Returns 16-bit-equivalent float32."""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        wav_in = td / "in.wav"
        mp3_mid = td / "mid.mp3"
        wav_out = td / "out.wav"
        sf.write(wav_in, audio, sr)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_in), "-b:a", f"{bitrate_kbps}k", str(mp3_mid)],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3_mid), str(wav_out)],
            check=True,
        )
        out, out_sr = sf.read(wav_out, dtype="float32")
    if out_sr != sr:
        out = librosa.resample(out, orig_sr=out_sr, target_sr=sr)
    if out.ndim > 1:
        out = out.mean(axis=1)
    n = min(len(audio), len(out))
    return out[:n].astype(np.float32)


def awgn(audio: np.ndarray, snr_db: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    sig_power = float(np.mean(audio**2) + 1e-12)
    noise_power = sig_power / (10 ** (snr_db / 10))
    noise = rng.normal(0.0, np.sqrt(noise_power), size=audio.shape).astype(np.float32)
    return (audio + noise).astype(np.float32)


def time_stretch(audio: np.ndarray, rate: float = 1.05) -> np.ndarray:
    return librosa.effects.time_stretch(audio, rate=rate).astype(np.float32)


DISTORTIONS = [
    ("none", lambda x, sr: x),
    ("mp3_320", lambda x, sr: mp3_roundtrip(x, sr, 320)),
    ("mp3_192", lambda x, sr: mp3_roundtrip(x, sr, 192)),
    ("mp3_128", lambda x, sr: mp3_roundtrip(x, sr, 128)),
    ("awgn_30db", lambda x, sr: awgn(x, 30.0)),
    ("awgn_10db", lambda x, sr: awgn(x, 10.0)),
    ("ts_1.05", lambda x, sr: time_stretch(x, 1.05)),
]
