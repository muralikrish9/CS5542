"""Vector B: CLAP-prompt categorical channel.

Encode bits by choice of MusicGen prompt from a 4-category codebook
(2 bits per clip). Decode via CLAP text-audio cosine similarity:
argmax over the 4 anchor prompts -> 2-bit symbol.

Codebook: {happy fast, happy slow, sad fast, sad slow}.
"""
from __future__ import annotations
import functools
import json
from pathlib import Path
import numpy as np
import torch
import librosa
import soundfile as sf

from .vector_a import _load_musicgen, DEVICE  # reuse cached MusicGen

DATA = Path(__file__).parent.parent / "data"
CLAP_SR = 48000  # CLAP expects 48 kHz audio


def codebook() -> list[dict]:
    p = DATA / "prompts.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    # fallback default codebook (also written by data setup)
    return [
        {"bits": "00", "prompt": "happy upbeat acoustic guitar pop, fast tempo, 140 bpm, major key, cheerful"},
        {"bits": "01", "prompt": "happy warm soft acoustic guitar, slow tempo, 60 bpm, major key, gentle"},
        {"bits": "10", "prompt": "sad melancholic piano, fast tempo, 140 bpm, minor key, anxious"},
        {"bits": "11", "prompt": "sad melancholic piano, slow tempo, 60 bpm, minor key, somber"},
    ]


@functools.lru_cache(maxsize=1)
def _load_clap():
    from transformers import ClapModel, ClapProcessor

    proc = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    model = ClapModel.from_pretrained("laion/clap-htsat-unfused").to(DEVICE)
    model.eval()
    return proc, model


def musicgen_clip(prompt: str, seconds: float = 6.0, seed: int | None = 0) -> tuple[np.ndarray, int]:
    proc, model, sr = _load_musicgen()
    if seed is not None:
        torch.manual_seed(seed)
    max_new = int(seconds * 50)
    inp = proc(text=[prompt], padding=True, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        out = model.generate(**inp, max_new_tokens=max_new, do_sample=True, guidance_scale=3.0)
    audio = out[0, 0].cpu().numpy().astype(np.float32)
    return audio, sr


def encode_bits(bits: str, seconds: float = 6.0, seed_base: int = 0) -> list[dict]:
    """Encode a binary string of even length as a list of MusicGen clips.

    Returns: list of {bits, prompt, audio, sr} per 2-bit symbol.
    """
    assert len(bits) % 2 == 0, "need even number of bits"
    book = {c["bits"]: c["prompt"] for c in codebook()}
    out = []
    for i in range(0, len(bits), 2):
        sym = bits[i : i + 2]
        prompt = book[sym]
        audio, sr = musicgen_clip(prompt, seconds=seconds, seed=seed_base + i)
        out.append({"bits": sym, "prompt": prompt, "audio": audio, "sr": sr})
    return out


def _clap_text_embed(prompts: list[str]) -> torch.Tensor:
    proc, model = _load_clap()
    inp = proc(text=prompts, return_tensors="pt", padding=True).to(DEVICE)
    with torch.no_grad():
        out = model.get_text_features(**inp)
    emb = out.pooler_output if hasattr(out, "pooler_output") else out
    return emb / emb.norm(dim=-1, keepdim=True)


def _clap_audio_embed(audio: np.ndarray, sr: int) -> torch.Tensor:
    if sr != CLAP_SR:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=CLAP_SR)
    proc, model = _load_clap()
    inp = proc(audio=audio, return_tensors="pt", sampling_rate=CLAP_SR).to(DEVICE)
    with torch.no_grad():
        out = model.get_audio_features(**inp)
    emb = out.pooler_output if hasattr(out, "pooler_output") else out
    return emb / emb.norm(dim=-1, keepdim=True)


def decode_clip(audio: np.ndarray, sr: int) -> tuple[str, np.ndarray]:
    """Decode one 2-bit symbol from a clip via CLAP cosine.

    Returns (predicted_bits, similarity_vector_over_codebook).
    """
    book = codebook()
    text_emb = _clap_text_embed([c["prompt"] for c in book])
    audio_emb = _clap_audio_embed(audio, sr)
    sims = (audio_emb @ text_emb.T).squeeze(0).cpu().numpy()
    best = int(np.argmax(sims))
    return book[best]["bits"], sims


def decode_bits(clips: list[tuple[np.ndarray, int]]) -> tuple[str, list[np.ndarray]]:
    """Decode a list of (audio, sr) clips into a bit string."""
    out_bits = []
    out_sims = []
    for audio, sr in clips:
        bits, sims = decode_clip(audio, sr)
        out_bits.append(bits)
        out_sims.append(sims)
    return "".join(out_bits), out_sims


def ber(reference: str, hypothesis: str) -> float:
    n = max(len(reference), len(hypothesis))
    ref = reference.ljust(n, "0")
    hyp = hypothesis.ljust(n, "0")
    errors = sum(1 for a, b in zip(ref, hyp) if a != b)
    return errors / n


def demo(bits: str = "01101011") -> dict:
    """Encode 8 bits = 4 clips; decode back."""
    clips = encode_bits(bits, seconds=6.0)
    out_dir = Path(__file__).parent.parent / "results" / "audio_samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    audios = []
    for i, c in enumerate(clips):
        path = out_dir / f"vec_b_demo_{i}_{c['bits']}.wav"
        sf.write(path, c["audio"], c["sr"])
        audios.append((c["audio"], c["sr"]))
    recovered, sims = decode_bits(audios)
    return {
        "secret_bits": bits,
        "recovered": recovered,
        "ber": ber(bits, recovered),
        "n_clips": len(clips),
    }


if __name__ == "__main__":
    print(demo())
