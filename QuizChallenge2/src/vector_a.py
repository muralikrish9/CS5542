"""Vector A: semantic covert speech channel.

Encode a secret as TTS vocals mixed under MusicGen-generated music;
recover via Whisper ASR.

Pipeline:
  text -> SpeechT5 (16kHz vocals) -> [optional bandpass 300-3400 Hz]
  prompt -> MusicGen-small (32kHz) -> resample to 16kHz
  mix: music + 10^(alpha_db/20) * vocals
  decode: Whisper(mix) -> recovered text
"""
from __future__ import annotations
import functools
from pathlib import Path
import numpy as np
import soundfile as sf
import torch
import librosa
from scipy.signal import butter, sosfiltfilt

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SR = 16000  # mix sample rate (Whisper native)


@functools.lru_cache(maxsize=1)
def _load_tts():
    from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
    from datasets import load_dataset

    proc = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
    model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(DEVICE)
    vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(DEVICE)
    embeddings_ds = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
    speaker_emb = torch.tensor(embeddings_ds[7306]["xvector"]).unsqueeze(0).to(DEVICE)
    return proc, model, vocoder, speaker_emb


@functools.lru_cache(maxsize=1)
def _load_musicgen():
    from transformers import AutoProcessor, MusicgenForConditionalGeneration

    proc = AutoProcessor.from_pretrained("facebook/musicgen-small")
    model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small").to(DEVICE)
    sr = model.config.audio_encoder.sampling_rate
    return proc, model, sr


@functools.lru_cache(maxsize=1)
def _load_whisper(size: str = "base"):
    import whisper

    return whisper.load_model(size, device=DEVICE)


def tts(text: str) -> np.ndarray:
    proc, model, vocoder, speaker_emb = _load_tts()
    inputs = proc(text=text, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        speech = model.generate_speech(inputs["input_ids"], speaker_emb, vocoder=vocoder)
    return speech.cpu().numpy().astype(np.float32)


def musicgen(prompt: str, seconds: float = 10.0, seed: int | None = 42) -> tuple[np.ndarray, int]:
    proc, model, sr = _load_musicgen()
    if seed is not None:
        torch.manual_seed(seed)
    # MusicGen uses 50 audio tokens per second
    max_new = int(seconds * 50)
    mg_inputs = proc(text=[prompt], padding=True, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        out = model.generate(**mg_inputs, max_new_tokens=max_new, do_sample=True, guidance_scale=3.0)
    audio = out[0, 0].cpu().numpy().astype(np.float32)
    return audio, sr


def bandpass(x: np.ndarray, sr: int = SR, low: float = 300.0, high: float = 3400.0) -> np.ndarray:
    sos = butter(6, [low, high], btype="band", fs=sr, output="sos")
    return sosfiltfilt(sos, x).astype(np.float32)


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x**2) + 1e-12))


def mix(
    vocals: np.ndarray,
    music: np.ndarray,
    music_sr: int,
    alpha_db: float = -12.0,
    variant: str = "flat",
) -> np.ndarray:
    """Mix vocals (16kHz) under music (any sr) at gain alpha_db dB.

    variant: 'flat' = no shaping; 'bandpass' = bandpass-filter vocals to 300-3400 Hz.
    Returns 16kHz mix normalized to [-1, 1].
    """
    music_16k = librosa.resample(music, orig_sr=music_sr, target_sr=SR) if music_sr != SR else music
    n = max(len(vocals), len(music_16k))
    vocals = np.pad(vocals, (0, n - len(vocals)))
    music_16k = np.pad(music_16k, (0, n - len(music_16k)))
    if variant == "bandpass":
        vocals = bandpass(vocals, SR)
    vocals = vocals / max(_rms(vocals), 1e-6)
    music_16k = music_16k / max(_rms(music_16k), 1e-6)
    alpha = 10 ** (alpha_db / 20)
    out = music_16k + alpha * vocals
    peak = max(np.abs(out).max(), 1.0)
    return (out / peak).astype(np.float32)


def decode(audio: np.ndarray | str | Path, whisper_size: str = "base") -> str:
    model = _load_whisper(whisper_size)
    if isinstance(audio, (str, Path)):
        result = model.transcribe(str(audio), fp16=False, language="en")
    else:
        x = np.asarray(audio, dtype=np.float32)
        result = model.transcribe(x, fp16=False, language="en")
    return result["text"].strip()


def encode(
    secret: str,
    music_prompt: str,
    alpha_db: float = -12.0,
    variant: str = "flat",
    seconds: float = 10.0,
    seed: int | None = 42,
) -> tuple[np.ndarray, dict]:
    """Encode `secret` as covert speech under `music_prompt` carrier.

    Returns (mix_16k, meta). meta has keys: vocals, music, music_sr, alpha_db, variant.
    """
    vocals = tts(secret)
    music, music_sr = musicgen(music_prompt, seconds=seconds, seed=seed)
    mixed = mix(vocals, music, music_sr, alpha_db=alpha_db, variant=variant)
    meta = {
        "vocals": vocals,
        "music": music,
        "music_sr": music_sr,
        "alpha_db": alpha_db,
        "variant": variant,
        "secret": secret,
        "music_prompt": music_prompt,
    }
    return mixed, meta


def demo(secret: str = "hello quiz challenge two") -> dict:
    mixed, meta = encode(secret, "lo-fi hip-hop, soft piano, 60 bpm", alpha_db=-6.0, variant="flat", seconds=8.0)
    out = Path(__file__).parent.parent / "results" / "audio_samples" / "vec_a_demo.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, mixed, SR)
    text = decode(out)
    return {"path": str(out), "secret": secret, "recovered": text}


if __name__ == "__main__":
    print(demo())
