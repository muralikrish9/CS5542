# CS 5542 — Quiz Challenge-1: Stable Diffusion for E-Commerce

**Author:** Murali Ediga · University of Missouri–Kansas City
**Due:** April 20, 2026
**Scenario:** Option 1 — E-Commerce Product Image Generation

---

## Summary

A controlled, evaluated image generation pipeline that turns Amazon-style product metadata into studio-quality product images using Stable Diffusion. Three prompt control strategies are compared across **15 products** and evaluated with **CLIP** alignment, consistency, and diversity metrics.

| Strategy | Model | CFG | Steps | CLIP Align | Consistency | Diversity |
|----------|-------|-----|-------|-----------:|------------:|----------:|
| A · Naive | SDXL-Turbo | 0.0 | 4 | 0.314 ± 0.018 | 0.907 | 0.349 |
| B · Structured | SDXL-Turbo | 0.0 | 4 | 0.308 ± 0.016 | **0.932** | 0.332 |
| C · Structured + Negative | SD 1.5 | 7.5 | 25 | 0.306 ± 0.021 | 0.881 | 0.304 |

**Key finding:** structured prompts improve image→image consistency by **+2.7 points** over naive prompts — the metric that matters for brand uniformity in a catalog.

---

## Repository layout

```
Week11_Lab/
├── code/
│   ├── generate.py      SDXL-Turbo generation (strategies A + B)
│   ├── regen_c.py       SD 1.5 generation with CFG (strategy C)
│   ├── evaluate.py      CLIP alignment · consistency · diversity
│   ├── make_grids.py    3-column comparison grids
│   ├── build_ppt.py     Generates the submission deck
│   └── build_video.py   Renders the 86-second demo video
├── data/
│   └── products.csv     15 curated products, 7 metadata fields
├── outputs/
│   ├── A_naive/         45 images
│   ├── B_structured/    45 images
│   ├── C_negative/      45 images
│   ├── grids/           15 naive|structured|negative comparison grids
│   ├── eval_summary.csv
│   └── eval_results.json
├── slides/
│   └── CS5542_QuizChallenge1_Murali_Ediga.pptx
└── video/
    └── cs5542_quiz1_demo.mp4  (86 s, 1920×1080)
```

---

## Run on a GPU box

```bash
# 1. environment
python -m venv .venv && source .venv/bin/activate
pip install diffusers transformers accelerate safetensors open_clip_torch pillow

# 2. generate 135 images (~60 s on an RTX PRO 5000)
python code/generate.py --csv data/products.csv --out outputs --n 3
python code/regen_c.py   --csv data/products.csv --out outputs --n 3

# 3. evaluate + assemble comparison grids
python code/evaluate.py  --out outputs
python code/make_grids.py --out outputs --grid-out outputs/grids

# 4. build slides + video
python code/build_ppt.py
python code/build_video.py   # requires ffmpeg for mp4 encode
```

---

## Control mechanisms

1. **Structured prompt templates** — metadata → canonical prompt:
   `{title}, {color}, made of {material}, {style} style, {features}, studio lighting, clean white background, centered product shot, 4k, photorealistic, commercial photography`
2. **Negative prompt conditioning (CFG)** — a fixed negative prompt is applied via classifier-free guidance. SDXL-Turbo runs at `guidance_scale = 0` so negative prompts have no effect; strategy C switches to Stable Diffusion 1.5 with `guidance_scale = 7.5` so the negative prompt actually shapes sampling.

---

## Evaluation metrics

- **Prompt alignment** — CLIP ViT-B/32 cosine similarity between the prompt and the generated image.
- **Consistency** — mean pairwise CLIP-image similarity within a `(product, strategy)` group. Higher = the three seeds render a more unified-looking product.
- **Diversity** — `1 − mean_pairwise_similarity` across a strategy. Higher = more visual variation across the catalog.
- **Failures** — images with CLIP-alignment below 0.22 (heuristic threshold). None triggered at this scale.

See `outputs/eval_results.json` for per-image scores and `outputs/eval_summary.csv` for the aggregate table.

---

## Findings

- Structured prompts (**B**) maximize image-to-image consistency (+2.7 pts over A) — the metric that matters most for catalog uniformity.
- Naive prompts (**A**) score marginally higher on CLIP-alignment because short prompts are easier for CLIP to match (length bias); CLIP-alignment is NOT a reliable quality metric on its own.
- Turbo models disable classifier-free guidance (`guidance_scale = 0`), so any strategy that needs negative prompts has to run on a non-turbo base.

## Limitations

- 15 products × 3 seeds is a small sample. No human preference study.
- No ControlNet (pose/layout) conditioning. No brand-specific LoRA fine-tuning.
- CLIP ViT-B/32 is English-only — results may not generalize to multilingual catalogs.

---

## AI-tool disclosure

Claude (Anthropic) was used to scaffold `generate.py`, `evaluate.py`, and slide layouts, and to draft prompt templates. All code was executed and verified by the author on an NVIDIA RTX PRO 5000 (48 GB). Dataset curation, strategy selection, evaluation, and interpretation are the author’s own.

---

## Links

- GitHub: https://github.com/muralikrish9/CS5542/tree/master/Week11_Lab
- Demo video: uploaded to YouTube (link added after upload)
