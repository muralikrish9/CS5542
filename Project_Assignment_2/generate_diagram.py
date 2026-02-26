"""
generate_diagram.py
CS 5542 — Project Assignment 2 (Phase 2)
Pipeline Architecture Diagram Generator

Produces: assets/pipeline_diagram.png
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "assets", "pipeline_diagram.png")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

fig, ax = plt.subplots(figsize=(18, 10))
ax.set_xlim(0, 18)
ax.set_ylim(0, 10)
ax.axis('off')

fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

# ── Color palette ──────────────────────────────────────────────────────────────
COL_SRC  = '#1a6b3c'   # Data Sources — green
COL_KB   = '#1a3a6b'   # Knowledge Base — blue
COL_RET  = '#6b1a3a'   # Retrieval Pipeline — purple
COL_SF   = '#1a5c6b'   # Snowflake — teal
COL_APP  = '#6b4f1a'   # Application — amber
TXT      = '#e6edf3'
ARROW    = '#58a6ff'
SUBTEXT  = '#8b949e'


def draw_box(ax, x, y, w, h, label, sublabels, color, text_color=TXT):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.08",
        facecolor=color,
        edgecolor='#30363d',
        linewidth=1.5,
        zorder=3
    )
    ax.add_patch(box)
    # Main label
    ax.text(x + w/2, y + h - 0.32, label,
            ha='center', va='top', fontsize=11, fontweight='bold',
            color=text_color, zorder=4)
    # Sub-labels
    for i, sub in enumerate(sublabels):
        ax.text(x + w/2, y + h - 0.75 - i*0.42, sub,
                ha='center', va='top', fontsize=7.5,
                color=SUBTEXT, zorder=4)


def draw_arrow(ax, x1, y1, x2, y2, label=''):
    ax.annotate('',
        xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(
            arrowstyle='->', color=ARROW, lw=2.0,
            connectionstyle='arc3,rad=0.0'
        ),
        zorder=5
    )
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.18, label, ha='center', va='bottom',
                fontsize=7, color=ARROW, zorder=6)


# ── Title ──────────────────────────────────────────────────────────────────────
ax.text(9, 9.6, 'CS 5542 — End-to-End Multimodal RAG Pipeline',
        ha='center', va='center', fontsize=14, fontweight='bold', color=TXT, zorder=6)
ax.text(9, 9.25, 'Behavioral Fingerprinting of Multi-Agent AI Attack Swarms',
        ha='center', va='center', fontsize=9, color=SUBTEXT, zorder=6)

# ══════════════════════════════════════════════════════════════════════════════
# Layer 1 — Data Sources  (x=0.3, y=5.5, w=3.4, h=3.2)
# ══════════════════════════════════════════════════════════════════════════════
draw_box(ax, 0.3, 5.5, 3.4, 3.2,
         'Data Sources',
         [
             '● 12 Cybersecurity .txt files',
             '  (pentesting, malware, 5G,',
             '  adversarial AI, cryptography…)',
             '● 2 Research PDFs',
             '  (Attention Is All You Need,',
             '  BERT)',
             '● 6 Extracted figures (PNG)',
             '● Synthetic events/users (CSV)',
         ],
         COL_SRC)

# Lab badges inside
for i, lab in enumerate(['Lab 2', 'Lab 3', 'Lab 5']):
    bx = FancyBboxPatch((0.45 + i*1.1, 5.55), 0.95, 0.28,
                         boxstyle="round,pad=0.03", facecolor='#0d1117',
                         edgecolor='#30363d', linewidth=1, zorder=4)
    ax.add_patch(bx)
    ax.text(0.45 + i*1.1 + 0.475, 5.69, lab,
            ha='center', va='center', fontsize=6.5, color=SUBTEXT, zorder=5)

# ══════════════════════════════════════════════════════════════════════════════
# Layer 2 — Multimodal Knowledge Base  (x=4.2, y=5.5, w=3.4, h=3.2)
# ══════════════════════════════════════════════════════════════════════════════
draw_box(ax, 4.2, 5.5, 3.4, 3.2,
         'Multimodal Knowledge Base',
         [
             '● Text corpus: TF-IDF index +',
             '  dense embeddings',
             '  (all-MiniLM-L6-v2)',
             '● Image corpus: caption-based',
             '  TF-IDF index',
             '● Fixed chunking: size=900,',
             '  overlap=150 tokens',
             '● Semantic page-level chunks',
         ],
         COL_KB)

# ══════════════════════════════════════════════════════════════════════════════
# Layer 3 — Retrieval Pipeline  (x=8.1, y=5.5, w=3.4, h=3.2)
# ══════════════════════════════════════════════════════════════════════════════
draw_box(ax, 8.1, 5.5, 3.4, 3.2,
         'Retrieval & Reranking',
         [
             '● Sparse: TF-IDF / BM25',
             '● Dense: sentence-transformers',
             '  (all-MiniLM-L6-v2)',
             '● Hybrid: RRF fusion (α=0.5)',
             '● Rerank: cross-encoder',
             '  ms-marco-MiniLM-L-6-v2',
             '● Multimodal fusion (text+image)',
         ],
         COL_RET)

# ══════════════════════════════════════════════════════════════════════════════
# Layer 4 — Snowflake Warehouse  (x=4.2, y=1.5, w=3.4, h=3.2)
# ══════════════════════════════════════════════════════════════════════════════
draw_box(ax, 4.2, 1.5, 3.4, 3.2,
         'Snowflake Data Warehouse',
         [
             '● Account: SFEDU02-DCB73175',
             '● DB: CS5542_WEEK5',
             '● Tables: EVENTS, USERS',
             '● Stage: CS5542_STAGE (CSV)',
             '● Warehouse: COMPUTE_WH',
             '  (XSMALL, auto-suspend 60s)',
             '● Views & aggregation queries',
         ],
         COL_SF)

# ══════════════════════════════════════════════════════════════════════════════
# Layer 5 — Application Interface  (x=12.0, y=5.5, w=3.4, h=3.2)
# ══════════════════════════════════════════════════════════════════════════════
draw_box(ax, 12.0, 5.5, 3.4, 3.2,
         'Application Interface',
         [
             '● Streamlit app (Lab 4)',
             '● Query input + retrieval method',
             '  selector (sparse/dense/hybrid/',
             '  rerank)',
             '● Evidence display (text + image)',
             '● Metrics: P@5, R@10, latency',
             '● Query logging (CSV)',
             '● Snowflake analytics dashboard',
         ],
         COL_APP)

# ══════════════════════════════════════════════════════════════════════════════
# Lab tags row (bottom)
# ══════════════════════════════════════════════════════════════════════════════
lab_info = [
    (1.0, 'Week 1\nMini-RAG\nEmbeddings'),
    (4.9, 'Week 2\nAdv. RAG\nChunking'),
    (8.8, 'Week 3\nMultimodal\nRAG'),
    (12.7, 'Week 4\nStreamlit\nDeployment'),
]
for lx, ltxt in lab_info:
    b = FancyBboxPatch((lx, 1.6), 1.8, 1.2,
                        boxstyle="round,pad=0.06", facecolor='#161b22',
                        edgecolor='#21262d', linewidth=1.2, zorder=3)
    ax.add_patch(b)
    ax.text(lx + 0.9, 2.2, ltxt,
            ha='center', va='center', fontsize=7, color=SUBTEXT,
            zorder=4, linespacing=1.4)

# Week 5 tag
b5 = FancyBboxPatch((4.9, 1.6), 1.8, 1.2,
                     boxstyle="round,pad=0.06", facecolor='#161b22',
                     edgecolor='#21262d', linewidth=1.2, zorder=5)
ax.add_patch(b5)
ax.text(5.8, 2.2, 'Week 5\nSnowflake\nPipeline',
        ha='center', va='center', fontsize=7, color=SUBTEXT,
        zorder=6, linespacing=1.4)

# ══════════════════════════════════════════════════════════════════════════════
# Arrows  (horizontal pipeline)
# ══════════════════════════════════════════════════════════════════════════════
draw_arrow(ax, 3.7, 7.1, 4.2, 7.1, 'ingest')
draw_arrow(ax, 7.6, 7.1, 8.1, 7.1, 'index')
draw_arrow(ax, 11.5, 7.1, 12.0, 7.1, 'serve')

# Downward arrow: Retrieval → Snowflake
draw_arrow(ax, 9.8, 5.5, 5.9, 4.7, 'log events')

# Upward arrow: Snowflake → App (analytics)
draw_arrow(ax, 7.6, 3.0, 12.9, 5.5, 'analytics\n& metrics')

# ══════════════════════════════════════════════════════════════════════════════
# Legend
# ══════════════════════════════════════════════════════════════════════════════
legend_patches = [
    mpatches.Patch(color=COL_SRC, label='Data Sources (Labs 2,3,5)'),
    mpatches.Patch(color=COL_KB,  label='Knowledge Base (Labs 1,2,3)'),
    mpatches.Patch(color=COL_RET, label='Retrieval Pipeline (Labs 1,2,3)'),
    mpatches.Patch(color=COL_SF,  label='Snowflake Warehouse (Lab 5)'),
    mpatches.Patch(color=COL_APP, label='Application Interface (Lab 4)'),
]
legend = ax.legend(handles=legend_patches, loc='lower left', fontsize=7.5,
                   facecolor='#161b22', edgecolor='#30363d',
                   labelcolor=TXT, framealpha=0.9,
                   bbox_to_anchor=(0.01, 0.01))

plt.tight_layout(pad=0.2)
plt.savefig(OUTPUT_PATH, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print(f"Diagram saved to: {OUTPUT_PATH}")
