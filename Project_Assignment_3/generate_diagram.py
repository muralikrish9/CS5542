"""
CS5542 PA3 — Architecture Diagram Generator
Creates architecture_diagram.png showing the full integrated stack.
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTPUT = os.path.join(os.path.dirname(__file__), "architecture_diagram.png")


def draw():
    fig, ax = plt.subplots(1, 1, figsize=(14, 7.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")
    fig.patch.set_facecolor("#fafafa")

    # Color palette
    C = {
        "data": "#2196F3",
        "retrieval": "#4CAF50",
        "agent": "#FF9800",
        "lora": "#9C27B0",
        "app": "#E91E63",
        "deploy": "#607D8B",
        "bg": "#ffffff",
        "text": "#1a1a2e",
        "arrow": "#555555",
    }

    def box(x, y, w, h, label, sublabel, color, lab_tag=None):
        rect = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.15",
            facecolor=color, edgecolor="#333333",
            linewidth=1.5, alpha=0.85, zorder=2,
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2 + 0.12, label,
                ha="center", va="center", fontsize=10, fontweight="bold",
                color="white", zorder=3)
        ax.text(x + w / 2, y + h / 2 - 0.18, sublabel,
                ha="center", va="center", fontsize=7.5,
                color="#eeeeee", style="italic", zorder=3)
        if lab_tag:
            ax.text(x + w - 0.08, y + 0.12, lab_tag,
                    ha="right", va="bottom", fontsize=6.5,
                    color="#ffeb3b", fontweight="bold", zorder=3,
                    bbox=dict(boxstyle="round,pad=0.1", fc="#00000044", ec="none"))

    def arrow(x1, y1, x2, y2):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(
                arrowstyle="-|>", color=C["arrow"],
                lw=2.0, connectionstyle="arc3,rad=0.0",
            ),
            zorder=1,
        )

    # Title
    ax.text(7, 7.6, "Behavioral Fingerprinting of Multi-Agent AI Attack Swarms",
            ha="center", va="center", fontsize=14, fontweight="bold", color=C["text"])
    ax.text(7, 7.25, "CS 5542 — Integrated System Architecture (Labs 1–9)",
            ha="center", va="center", fontsize=10, color="#666666")

    # ── Row 1: Data Sources ──
    box(0.3, 5.5, 2.8, 1.2, "Data Sources", "Honeypot logs, security events", C["data"], "Labs 1-3")
    box(3.6, 5.5, 2.8, 1.2, "Knowledge Base", "12 cybersecurity text files", C["data"], "Lab 2")
    box(6.9, 5.5, 2.8, 1.2, "Snowflake DW", "500 events, 50 users", C["data"], "Lab 5")

    # ── Row 2: Processing ──
    box(0.3, 3.5, 3.5, 1.2, "Retrieval Pipeline", "TF-IDF/BM25 + Dense + Rerank (+18% MAP)", C["retrieval"], "PA2")
    box(4.3, 3.5, 3.5, 1.2, "AI Agent (ReAct)", "LLaMA 3.3 70B via Groq, 5 tools", C["agent"], "Lab 6")
    box(8.3, 3.5, 2.5, 1.2, "Reflexion", "Self-critique (2 rounds)", C["agent"], "Lab 7")

    # ── Row 3: Adaptation + Reproducibility ──
    box(0.3, 1.5, 3.0, 1.2, "Domain Adaptation", "LoRA r=16, alpha=32, 57 pairs", C["lora"], "Lab 8")
    box(3.8, 1.5, 3.3, 1.2, "Reproducibility", "config.yaml, reproduce.sh, seed=42", C["retrieval"], "Lab 7")

    # ── Row 4: Deployment ──
    box(7.6, 1.5, 3.2, 1.2, "Streamlit Dashboard", "4 tabs: Query, Attacks, Replay, Monitor", C["app"], "Lab 9")
    box(11.3, 1.5, 2.3, 1.2, "Docker Deploy", "docker-compose, health checks", C["deploy"], "Lab 9")

    # Arrows: Data -> Processing
    arrow(1.7, 5.5, 1.7, 4.7)   # Data Sources -> Retrieval
    arrow(5.0, 5.5, 5.0, 4.7)   # Knowledge Base -> Agent
    arrow(8.3, 5.5, 6.5, 4.7)   # Snowflake -> Agent

    # Arrows: Retrieval <-> Agent
    arrow(3.8, 4.1, 4.3, 4.1)   # Retrieval -> Agent
    arrow(7.8, 4.1, 8.3, 4.1)   # Agent -> Reflexion

    # Arrows: Agent -> Adaptation / Reproducibility
    arrow(5.5, 3.5, 1.8, 2.7)   # Agent -> Domain Adaptation
    arrow(5.5, 3.5, 5.5, 2.7)   # Agent -> Reproducibility

    # Arrows: To Dashboard
    arrow(1.8, 1.5, 1.8, 0.8)   # Domain Adaptation down (conceptual)
    # Actually connect adaptation and repro to dashboard
    arrow(3.3, 2.1, 7.6, 2.1)   # Adaptation -> Dashboard
    arrow(7.1, 2.1, 7.6, 2.1)   # Repro -> Dashboard

    # Dashboard -> Docker
    arrow(10.8, 2.1, 11.3, 2.1)

    # Remove the dangling arrow
    # Instead connect Domain Adaptation up to Retrieval
    arrow(1.8, 2.7, 2.0, 3.5)

    plt.tight_layout(pad=0.5)
    fig.savefig(OUTPUT, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Generated: {OUTPUT} ({os.path.getsize(OUTPUT):,} bytes)")


if __name__ == "__main__":
    draw()
