"""Re-generate strategy C with SD 2.1 + CFG so negative prompts actually affect output.
SDXL-turbo uses guidance_scale=0 by design (speed), which disables classifier-free guidance
and therefore ignores the negative_prompt. We switch to stable-diffusion-2-1-base for C only."""
import argparse, csv, json, time
from pathlib import Path
import torch
from diffusers import StableDiffusionPipeline

from generate import structured_prompt, NEGATIVE

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="data/products.csv")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--n", type=int, default=3)
    args = ap.parse_args()
    out = Path(args.out) / "C_negative"
    out.mkdir(parents=True, exist_ok=True)

    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16
    ).to("cuda")
    pipe.set_progress_bar_config(disable=True)

    with open(args.csv, encoding="utf-8") as f:
        products = list(csv.DictReader(f))

    # Update generation_log.json for C entries
    log_path = Path(args.out) / "generation_log.json"
    log = json.load(open(log_path))

    t0 = time.time()
    new_entries = []
    for p in products:
        pid = p["product_id"]
        prompt = structured_prompt(p)
        for i in range(args.n):
            seed = 1000 + i
            g = torch.Generator(device="cuda").manual_seed(seed)
            img = pipe(
                prompt=prompt,
                negative_prompt=NEGATIVE,
                num_inference_steps=25,
                guidance_scale=7.5,
                generator=g,
                width=512, height=512,
            ).images[0]
            fname = f"{pid}_C_negative_{i}.png"
            img.save(out / fname)
            new_entries.append({
                "product_id": pid, "strategy": "C_negative", "seed": seed,
                "prompt": prompt, "negative": NEGATIVE,
                "file": f"C_negative/{fname}",
                "model": "stable-diffusion-v1-5",
            })
        print(f"[C] {pid} done, {time.time()-t0:.0f}s")

    log = [e for e in log if e["strategy"] != "C_negative"] + new_entries
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"[done C] {len(new_entries)} images in {time.time()-t0:.1f}s")

if __name__ == "__main__":
    main()
