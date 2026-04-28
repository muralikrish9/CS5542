"""Metric helpers: WER, BER, CLAP cosine, mel-cepstral distortion."""
from __future__ import annotations
import re
import numpy as np
import torch
import jiwer
import librosa


_norm = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.RemoveMultipleSpaces(),
    jiwer.Strip(),
    jiwer.ReduceToListOfListOfWords(),
])


def wer(reference: str, hypothesis: str) -> float:
    if not reference.strip():
        return 1.0
    return float(jiwer.wer(reference, hypothesis, reference_transform=_norm, hypothesis_transform=_norm))


def ber(reference: str, hypothesis: str) -> float:
    n = max(len(reference), len(hypothesis))
    if n == 0:
        return 0.0
    ref = reference.ljust(n, "0")
    hyp = hypothesis.ljust(n, "0")
    return sum(1 for a, b in zip(ref, hyp) if a != b) / n


def clap_cosine(audio: np.ndarray, sr: int, prompt: str) -> float:
    """Cosine similarity between CLAP audio embedding and CLAP text embedding of `prompt`."""
    from .vector_b import _clap_audio_embed, _clap_text_embed

    a = _clap_audio_embed(audio, sr)
    t = _clap_text_embed([prompt])
    return float((a @ t.T).item())


def mel_cepstral_distortion(reference: np.ndarray, candidate: np.ndarray, sr: int = 16000, n_mfcc: int = 13) -> float:
    """Mean MCD between two waveforms (lower = more similar)."""
    n = min(len(reference), len(candidate))
    ref = reference[:n]
    cand = candidate[:n]
    ref_mfcc = librosa.feature.mfcc(y=ref, sr=sr, n_mfcc=n_mfcc)
    cand_mfcc = librosa.feature.mfcc(y=cand, sr=sr, n_mfcc=n_mfcc)
    m = min(ref_mfcc.shape[1], cand_mfcc.shape[1])
    diff = ref_mfcc[:, :m] - cand_mfcc[:, :m]
    return float(np.mean(np.sqrt(np.sum(diff**2, axis=0))))
