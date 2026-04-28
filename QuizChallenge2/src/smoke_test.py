"""Smoke test: load all 4 foundation models, run a 3s round-trip.

Pre-warms HF weights (~5GB total). Run once at start.
"""
import time
import numpy as np
import torch
import soundfile as sf
from pathlib import Path

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[smoke] device={DEVICE}")

OUT = Path(__file__).parent.parent / "results" / "audio_samples"
OUT.mkdir(parents=True, exist_ok=True)


def t(label):
    return lambda: print(f"[smoke] {label} t={time.time()-T0:.1f}s")


T0 = time.time()

print("[smoke] loading SpeechT5 TTS...")
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset

tts_proc = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
tts_model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts").to(DEVICE)
tts_vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan").to(DEVICE)
embeddings_ds = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
speaker_emb = torch.tensor(embeddings_ds[7306]["xvector"]).unsqueeze(0).to(DEVICE)
t("SpeechT5 loaded")()

print("[smoke] loading MusicGen-small...")
from transformers import AutoProcessor, MusicgenForConditionalGeneration

mg_proc = AutoProcessor.from_pretrained("facebook/musicgen-small")
mg_model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small").to(DEVICE)
t("MusicGen loaded")()

print("[smoke] loading Whisper-base...")
import whisper

wh_model = whisper.load_model("base", device=DEVICE)
t("Whisper loaded")()

print("[smoke] loading CLAP...")
from transformers import ClapModel, ClapProcessor

clap_proc = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
clap_model = ClapModel.from_pretrained("laion/clap-htsat-unfused").to(DEVICE)
t("CLAP loaded")()

# === generate 2s TTS ===
print("[smoke] TTS: 'hello quiz challenge two'")
inputs = tts_proc(text="hello quiz challenge two", return_tensors="pt").to(DEVICE)
with torch.no_grad():
    speech = tts_model.generate_speech(inputs["input_ids"], speaker_emb, vocoder=tts_vocoder)
tts_audio = speech.cpu().numpy()  # 16kHz
sf.write(OUT / "smoke_tts.wav", tts_audio, 16000)
print(f"[smoke] TTS shape={tts_audio.shape} sr=16000 dur={len(tts_audio)/16000:.2f}s")
t("TTS done")()

# === generate 3s music ===
print("[smoke] MusicGen: 'lo-fi hip-hop, soft piano, 60 bpm'")
mg_inputs = mg_proc(text=["lo-fi hip-hop, soft piano, 60 bpm"], padding=True, return_tensors="pt").to(DEVICE)
with torch.no_grad():
    mg_audio = mg_model.generate(**mg_inputs, max_new_tokens=150)  # ~3s @ 50Hz tokens
mg_sr = mg_model.config.audio_encoder.sampling_rate
mg_np = mg_audio[0, 0].cpu().numpy()
sf.write(OUT / "smoke_music.wav", mg_np, mg_sr)
print(f"[smoke] Music shape={mg_np.shape} sr={mg_sr} dur={len(mg_np)/mg_sr:.2f}s")
t("Music done")()

# === resample music to 16k, mix at -12 dB, save, transcribe ===
print("[smoke] mix + Whisper round-trip")
import librosa

mg_16k = librosa.resample(mg_np, orig_sr=mg_sr, target_sr=16000)
# pad shorter
n = max(len(tts_audio), len(mg_16k))
tts_pad = np.pad(tts_audio, (0, n - len(tts_audio)))
mg_pad = np.pad(mg_16k, (0, n - len(mg_16k)))
# normalize
def rms(x):
    return float(np.sqrt(np.mean(x**2) + 1e-12))
tts_norm = tts_pad / rms(tts_pad)
mg_norm = mg_pad / rms(mg_pad)
alpha_db = -12
alpha = 10 ** (alpha_db / 20)
mixed = mg_norm + alpha * tts_norm
mixed = mixed / max(np.abs(mixed).max(), 1.0)
sf.write(OUT / "smoke_mix.wav", mixed, 16000)
result = wh_model.transcribe(str(OUT / "smoke_mix.wav"), fp16=False, language="en")
print(f"[smoke] alpha={alpha_db}dB transcript: {result['text']!r}")
t("Round-trip done")()

# === CLAP cosine ===
print("[smoke] CLAP: 'lo-fi hip-hop' similarity")
mg_48k = librosa.resample(mg_np, orig_sr=mg_sr, target_sr=48000)
clap_inputs = clap_proc(text=["lo-fi hip-hop, soft piano"], audio=mg_48k, return_tensors="pt", sampling_rate=48000).to(DEVICE)
with torch.no_grad():
    clap_out = clap_model(**clap_inputs)
audio_emb = clap_out.audio_embeds / clap_out.audio_embeds.norm(dim=-1, keepdim=True)
text_emb = clap_out.text_embeds / clap_out.text_embeds.norm(dim=-1, keepdim=True)
cos = (audio_emb @ text_emb.T)[0, 0].item()
print(f"[smoke] CLAP cosine = {cos:.3f}")
t("CLAP done")()

print(f"\n[smoke] ALL OK total={time.time()-T0:.1f}s")
