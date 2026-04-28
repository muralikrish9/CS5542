"""Generate the 5 deck plots from results CSVs."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent
RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 160, "font.size": 11})


def _save(fig, name):
    out = PLOTS / name
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] {out}")


def plot_wer_vs_alpha(df_a: pd.DataFrame):
    """Plot 1: Vector A WER vs alpha for each music prompt."""
    flat = df_a[df_a["variant"] == "flat"].copy()
    g = flat.groupby(["alpha_db", "prompt_id"])["wer"].agg(["mean", "std"]).reset_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for pid, sub in g.groupby("prompt_id"):
        sub = sub.sort_values("alpha_db")
        ax.errorbar(sub["alpha_db"], sub["mean"], yerr=sub["std"].fillna(0), marker="o", label=pid, capsize=3)
    ax.set_xlabel("vocal-to-music gain α (dB)")
    ax.set_ylabel("Word Error Rate (Whisper-base)")
    ax.set_title("Vector A — WER vs α by music style")
    ax.invert_xaxis()  # quieter vocals (more negative dB) = harder, on the right
    ax.legend(title="music prompt")
    ax.grid(alpha=0.3)
    _save(fig, "01_wer_vs_alpha.png")


def plot_flat_vs_bandpass(df_a: pd.DataFrame):
    """Plot 2: flat vs bandpass at alpha=-18 dB."""
    sub = df_a[df_a["alpha_db"] == -18.0].copy()
    g = sub.groupby(["prompt_id", "variant"])["wer"].mean().unstack()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    g.plot(kind="bar", ax=ax, color=["#377eb8", "#e41a1c"])
    ax.set_ylabel("WER (mean over 3 secrets)")
    ax.set_xlabel("music prompt")
    ax.set_title("Vector A — flat vs bandpass-shaped vocals at α=-18 dB")
    ax.legend(title="mix variant")
    ax.set_ylim(0, max(1.05, g.values.max() * 1.1))
    plt.xticks(rotation=0)
    _save(fig, "02_flat_vs_bandpass.png")


def plot_ber_vs_distortion(df_b: pd.DataFrame):
    """Plot 3: BER per distortion, with error bars."""
    g = df_b.groupby("distortion")["ber"].agg(["mean", "std", "count"]).reset_index()
    order = ["none", "mp3_320", "mp3_192", "mp3_128", "awgn_30db", "awgn_10db", "ts_1.05"]
    g["ord"] = g["distortion"].map({n: i for i, n in enumerate(order)})
    g = g.sort_values("ord")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(g["distortion"], g["mean"], yerr=g["std"].fillna(0), capsize=4, color="#4daf4a")
    ax.axhline(0.5, color="red", linestyle="--", alpha=0.5, label="chance (0.5)")
    ax.set_ylabel("Bit Error Rate (BER)")
    ax.set_xlabel("distortion")
    ax.set_title("Vector B — BER under codec / noise / time-stretch")
    ax.set_ylim(0, 1.0)
    ax.legend()
    plt.xticks(rotation=20)
    ax.grid(axis="y", alpha=0.3)
    _save(fig, "03_ber_vs_distortion.png")


def plot_cross_eval(df_a: pd.DataFrame, df_b: pd.DataFrame):
    """Plot 4: capacity vs error after MP3-192 round-trip — the money plot."""
    # Vector A "effective bps" estimated from words per second of secret @ ~5 chars/word, 8 bits/char
    # Use clip duration ~10s
    a_flat = df_a[(df_a["variant"] == "flat") & (df_a["alpha_db"].isin([-6, -12, -18, -24, -30]))].copy()
    # Approximate bps per row: secret_len_chars * 8 / 10s
    a_flat["bps"] = a_flat["secret"].str.len() * 8.0 / 10.0
    # WER as error proxy (no MP3 in Vector A eval — note as limitation)
    a_summary = a_flat.groupby("alpha_db").agg(
        bps=("bps", "mean"),
        err=("wer", "mean"),
    ).reset_index()
    a_summary["label"] = a_summary["alpha_db"].apply(lambda d: f"A α={d}dB")

    # Vector B at MP3-192
    b_192 = df_b[df_b["distortion"] == "mp3_192"].copy()
    # 2 bits per 6s clip = 0.333 bps
    b_summary = b_192.groupby("distortion").agg(
        err=("ber", "mean"),
    ).reset_index()
    b_summary["bps"] = 2 / 6.0
    b_summary["label"] = "B mp3-192"

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.scatter(a_summary["bps"], a_summary["err"], s=120, c="#e41a1c", marker="o", label="Vector A (semantic)")
    for _, r in a_summary.iterrows():
        ax.annotate(r["label"], (r["bps"], r["err"]), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.scatter(b_summary["bps"], b_summary["err"], s=120, c="#377eb8", marker="s", label="Vector B (CLAP-categorical)")
    for _, r in b_summary.iterrows():
        ax.annotate(r["label"], (r["bps"], r["err"]), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel("effective channel capacity (bits per second, log scale)")
    ax.set_ylabel("error rate (WER for A, BER for B)")
    ax.set_title("Cross-evaluation — capacity vs error: dual failure modes")
    ax.axhline(0.5, color="gray", linestyle=":", alpha=0.5)
    ax.legend()
    ax.grid(alpha=0.3)
    _save(fig, "04_cross_eval_scatter.png")


def plot_listening_mos(path: Path | None = None):
    """Plot 5: listening-test MOS table. Reads listening_test/results.csv if present."""
    fpath = path or (ROOT / "listening_test" / "results.csv")
    if not fpath.exists():
        print(f"[plot] skipping listening-test plot — no file at {fpath}")
        return
    df = pd.read_csv(fpath)
    # expected columns: clip, listener, music_quality, speech_audibility
    g = df.groupby("clip").agg(
        music_q_mean=("music_quality", "mean"),
        music_q_std=("music_quality", "std"),
        speech_aud_mean=("speech_audibility", "mean"),
        speech_aud_std=("speech_audibility", "std"),
    ).reset_index()
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    x = np.arange(len(g))
    width = 0.4
    ax.bar(x - width / 2, g["music_q_mean"], width, yerr=g["music_q_std"].fillna(0), label="music quality", color="#984ea3", capsize=3)
    ax.bar(x + width / 2, g["speech_aud_mean"], width, yerr=g["speech_aud_std"].fillna(0), label="speech audibility", color="#ff7f00", capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(g["clip"], rotation=20)
    ax.set_ylabel("MOS (1-5 scale)")
    ax.set_title(f"Listening-test MOS (n={df['listener'].nunique()})")
    ax.set_ylim(0, 5.5)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    _save(fig, "05_listening_mos.png")


def main():
    df_a = pd.read_csv(RESULTS / "results_vec_a.csv")
    df_b = pd.read_csv(RESULTS / "results_vec_b.csv")
    plot_wer_vs_alpha(df_a)
    plot_flat_vs_bandpass(df_a)
    plot_ber_vs_distortion(df_b)
    plot_cross_eval(df_a, df_b)
    plot_listening_mos()


if __name__ == "__main__":
    main()
