"""
CS 5542 Quiz Challenge-1: E-commerce Product Image Generation
Stable Diffusion (SDXL-Turbo) with three prompt strategies:
  A) naive        - title only
  B) structured   - templated (category/material/style/color/features) + quality tokens
  C) negative     - structured prompt + negative prompt conditioning

Run (on lab-pc):
    source /home/lab-pc/nami-venv/bin/activate
    python generate.py --csv data/products.csv --out outputs --n 3
"""
import argparse, csv, os, json, time
from pathlib import Path
import torch
from diffusers import AutoPipelineForText2Image

NEGATIVE = (
    "blurry, low quality, low resolution, distorted, deformed, jpeg artifacts, "
    "watermark, text, logo, cluttered background, extra limbs, bad anatomy, "
    "oversaturated, cartoon, sketch, unrealistic proportions"
)

QUALITY = "studio lighting, clean white background, centered product shot, 4k, photorealistic, commercial photography"

def naive_prompt(row):
    return row["title"]

def structured_prompt(row):
    return (
        f"{row['title']}, {row['color']}, made of {row['material']}, "
        f"{row['style']} style, {row['features']}, {QUALITY}"
    )

STRATEGIES = {
    "A_naive":       (naive_prompt,      None),
    "B_structured":  (structured_prompt, None),
    "C_negative":    (structured_prompt, NEGATIVE),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/products.csv")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--n", type=int, default=3, help="images per (product, strategy)")
    ap.add_argument("--model", default="stabilityai/sdxl-turbo")
    ap.add_argument("--steps", type=int, default=4)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"[load] {args.model}")
    pipe = AutoPipelineForText2Image.from_pretrained(
        args.model, torch_dtype=torch.float16, variant="fp16"
    ).to("cuda")
    pipe.set_progress_bar_config(disable=True)

    with open(args.csv, newline="", encoding="utf-8") as f:
        products = list(csv.DictReader(f))

    log = []
    t0 = time.time()
    total = len(products) * len(STRATEGIES) * args.n
    done = 0
    for p in products:
        pid = p["product_id"]
        for strat, (fn, neg) in STRATEGIES.items():
            sdir = out / strat
            sdir.mkdir(exist_ok=True)
            prompt = fn(p)
            for i in range(args.n):
                seed = 1000 + i
                g = torch.Generator(device="cuda").manual_seed(seed)
                img = pipe(
                    prompt=prompt,
                    negative_prompt=neg,
                    num_inference_steps=args.steps,
                    guidance_scale=0.0,
                    generator=g,
                ).images[0]
                fname = f"{pid}_{strat}_{i}.png"
                img.save(sdir / fname)
                log.append({
                    "product_id": pid, "strategy": strat, "seed": seed,
                    "prompt": prompt, "negative": neg or "",
                    "file": f"{strat}/{fname}",
                })
                done += 1
                if done % 10 == 0:
                    elapsed = time.time() - t0
                    rate = done / elapsed
                    eta = (total - done) / rate
                    print(f"[{done}/{total}] {elapsed:.0f}s elapsed, ~{eta:.0f}s eta")

    with open(out / "generation_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print(f"[done] {total} images in {time.time()-t0:.1f}s -> {out}")

if __name__ == "__main__":
    main()
