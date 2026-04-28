"""MelodyLeak — Gradio demo for both vectors.

Run: python app/gradio_app.py  (from QuizChallenge2/ dir)
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import gradio as gr

# Make src importable when running as `python app/gradio_app.py`
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src import vector_a as va
from src import vector_b as vb
from src.eval_utils import wer, ber

PROMPTS = {
    "lo-fi hip-hop, soft piano, 60 bpm, mellow": "lofi",
    "ambient pad, ethereal, slow, atmospheric": "ambient",
    "classical string quartet, baroque style, 80 bpm": "classical",
}


def _check_bits(bits: str) -> str:
    bits = bits.strip().replace(" ", "")
    if not all(c in "01" for c in bits):
        raise ValueError("Bits must be 0/1 only")
    if len(bits) % 2 != 0:
        raise ValueError("Need even number of bits (2 bits/clip)")
    return bits


def encode_a(secret: str, prompt: str, alpha_db: float, variant: str, seconds: float, progress=gr.Progress()):
    secret = secret.strip()
    if not secret:
        raise gr.Error("Type a secret message")
    progress(0.1, desc="Generating TTS...")
    vocals = va.tts(secret)
    progress(0.4, desc="Generating music (~5-10s)...")
    music, sr = va.musicgen(prompt, seconds=seconds, seed=42)
    progress(0.8, desc="Mixing...")
    mixed = va.mix(vocals, music, sr, alpha_db=alpha_db, variant=variant)
    progress(0.95, desc="Whisper decoding...")
    transcript = va.decode(mixed)
    score = wer(secret, transcript)
    return (va.SR, mixed), transcript, f"WER = {score:.3f}"


def encode_b(bits: str, seconds: float, progress=gr.Progress()):
    bits = _check_bits(bits)
    progress(0.05, desc=f"Generating {len(bits)//2} clips...")
    book = {c["bits"]: c["prompt"] for c in vb.codebook()}
    audios = []
    for i in range(0, len(bits), 2):
        sym = bits[i : i + 2]
        progress(0.1 + 0.7 * (i / max(len(bits), 1)), desc=f"Generating clip {i//2 + 1} ({sym})")
        audio, sr = vb.musicgen_clip(book[sym], seconds=seconds, seed=i)
        audios.append((audio, sr, sym))
    progress(0.85, desc="CLAP decoding...")
    pred_bits = []
    for audio, sr, sym in audios:
        pred, _ = vb.decode_clip(audio, sr)
        pred_bits.append(pred)
    pred_str = "".join(pred_bits)
    score = ber(bits, pred_str)
    # Pad audios to fixed slots
    pads = [None, None, None, None]
    for i, (audio, sr, _) in enumerate(audios[:4]):
        pads[i] = (sr, audio)
    return *pads, pred_str, f"BER = {score:.3f}  ({sum(a==b for a,b in zip(bits,pred_str))}/{len(bits)} bits correct)"


def build_ui():
    with gr.Blocks(title="MelodyLeak — Foundation-Model Audio Covert Channels") as demo:
        gr.Markdown(
            "# MelodyLeak\n"
            "**Foundation-model music as a covert speech channel.**\n\n"
            "Two vectors share a single MusicGen carrier:\n"
            "* **Vector A** — semantic. SpeechT5 reads a secret; mix under MusicGen; recover with Whisper.\n"
            "* **Vector B** — categorical. Encode 2 bits per clip via MusicGen prompt choice; decode with CLAP.\n"
        )
        with gr.Tabs():
            with gr.Tab("Vector A — Semantic covert speech"):
                with gr.Row():
                    with gr.Column():
                        sec = gr.Textbox(label="Secret message", value="meet at the third corner past the old library at sunset tomorrow")
                        prm = gr.Dropdown(label="Music prompt", choices=list(PROMPTS.keys()), value=list(PROMPTS.keys())[0])
                        alpha = gr.Slider(label="Vocal-to-music gain α (dB)", minimum=-30, maximum=-3, value=-12, step=3)
                        var = gr.Radio(label="Mix variant", choices=["flat", "bandpass"], value="flat")
                        secs = gr.Slider(label="Clip length (s)", minimum=4, maximum=15, value=10, step=1)
                        btn = gr.Button("Encode + Decode", variant="primary")
                    with gr.Column():
                        out_audio = gr.Audio(label="Mixed audio (you should hear music; speech is hidden)", type="numpy")
                        out_text = gr.Textbox(label="Whisper recovery")
                        out_score = gr.Textbox(label="WER vs ground truth")
                btn.click(encode_a, [sec, prm, alpha, var, secs], [out_audio, out_text, out_score])

            with gr.Tab("Vector B — CLAP-prompt categorical"):
                with gr.Row():
                    with gr.Column():
                        bits = gr.Textbox(label="Bits to transmit (even-length, e.g. 01101011)", value="01101011")
                        secsB = gr.Slider(label="Clip length per symbol (s)", minimum=4, maximum=10, value=6, step=1)
                        btnB = gr.Button("Encode + Decode", variant="primary")
                        gr.Markdown(
                            "**Codebook:**  \n"
                            "* 00 → happy fast (140 bpm, major)\n"
                            "* 01 → happy slow (60 bpm, major)\n"
                            "* 10 → sad fast (140 bpm, minor)\n"
                            "* 11 → sad slow (60 bpm, minor)\n"
                        )
                    with gr.Column():
                        a1 = gr.Audio(label="Clip 1", type="numpy")
                        a2 = gr.Audio(label="Clip 2", type="numpy")
                        a3 = gr.Audio(label="Clip 3", type="numpy")
                        a4 = gr.Audio(label="Clip 4", type="numpy")
                        out_pred = gr.Textbox(label="Recovered bits (CLAP argmax)")
                        out_ber = gr.Textbox(label="BER")
                btnB.click(encode_b, [bits, secsB], [a1, a2, a3, a4, out_pred, out_ber])

        gr.Markdown(
            "---\n"
            "Models: SpeechT5 (TTS) · MusicGen-small (carrier) · Whisper-base (decoder) · CLAP-HSAT (decoder + perceptual).  \n"
            "Repo: github.com/muralikrish9/CS5542 — *QuizChallenge2/*"
        )
    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch(inbrowser=True, share=False)
