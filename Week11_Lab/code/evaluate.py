"""
Evaluation:
  - Prompt Alignment  : CLIP similarity(text prompt, generated image)
  - Consistency       : mean pairwise CLIP-image similarity within (product, strategy)
  - Diversity         : 1 - mean pairwise CLIP-image similarity within strategy (across products)
"""
import argparse, json, csv, itertools
from pathlib import Path
import numpy as np
import torch
from PIL import Image
import open_clip

def load_clip():
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    tokenizer = open_clip.get_tokenizer("ViT-B-32")
    model = model.to("cuda").eval()
    return model, preprocess, tokenizer

@torch.no_grad()
def embed_images(model, preprocess, paths):
    imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in paths]).to("cuda")
    feats = model.encode_image(imgs)
    feats /= feats.norm(dim=-1, keepdim=True)
    return feats

@torch.no_grad()
def embed_texts(model, tokenizer, texts):
    toks = tokenizer(texts).to("cuda")
    feats = model.encode_text(toks)
    feats /= feats.norm(dim=-1, keepdim=True)
    return feats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs")
    args = ap.parse_args()
    root = Path(args.out)
    log = json.load(open(root / "generation_log.json"))

    model, preprocess, tokenizer = load_clip()

    rows = []
    for entry in log:
        path = root / entry["file"]
        emb = embed_images(model, preprocess, [path])
        txt = embed_texts(model, tokenizer, [entry["prompt"]])
        align = float((emb @ txt.T).item())
        rows.append({**entry, "clip_align": align, "_img_emb": emb.cpu().numpy()[0]})

    # Consistency per (product, strategy)
    by_key = {}
    for r in rows:
        by_key.setdefault((r["product_id"], r["strategy"]), []).append(r["_img_emb"])
    consistency = {}
    for k, embs in by_key.items():
        if len(embs) < 2:
            continue
        sims = []
        for a, b in itertools.combinations(embs, 2):
            sims.append(float(np.dot(a, b)))
        consistency[f"{k[0]}|{k[1]}"] = float(np.mean(sims))

    # Diversity per strategy (mean pairwise similarity across ALL images in strategy; lower = more diverse)
    by_strat = {}
    for r in rows:
        by_strat.setdefault(r["strategy"], []).append(r["_img_emb"])
    diversity = {}
    for strat, embs in by_strat.items():
        sims = []
        for a, b in itertools.combinations(embs, 2):
            sims.append(float(np.dot(a, b)))
        diversity[strat] = 1.0 - float(np.mean(sims)) if sims else 0.0

    # Aggregate alignment
    agg = {}
    for r in rows:
        agg.setdefault(r["strategy"], []).append(r["clip_align"])
    align_summary = {s: {"mean": float(np.mean(v)), "std": float(np.std(v))} for s, v in agg.items()}
    cons_by_strat = {}
    for k, v in consistency.items():
        strat = k.split("|")[1]
        cons_by_strat.setdefault(strat, []).append(v)
    cons_summary = {s: {"mean": float(np.mean(v)), "std": float(np.std(v))} for s, v in cons_by_strat.items()}

    # Failure = alignment < 0.22 (CLIP threshold, common heuristic)
    failures = [{"file": r["file"], "prompt": r["prompt"], "clip_align": r["clip_align"]}
                for r in rows if r["clip_align"] < 0.22]

    # Strip ndarrays for json
    for r in rows:
        r.pop("_img_emb", None)

    summary = {
        "n_images": len(rows),
        "alignment_by_strategy": align_summary,
        "consistency_by_strategy": cons_summary,
        "diversity_by_strategy": diversity,
        "n_failures": len(failures),
    }
    with open(root / "eval_results.json", "w") as f:
        json.dump({"summary": summary, "per_image": rows, "failures": failures,
                   "consistency_per_group": consistency}, f, indent=2)

    # CSV summary table
    with open(root / "eval_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["strategy", "align_mean", "align_std", "consistency_mean", "diversity"])
        for s in ["A_naive", "B_structured", "C_negative"]:
            w.writerow([
                s,
                round(align_summary[s]["mean"], 4),
                round(align_summary[s]["std"], 4),
                round(cons_summary.get(s, {"mean": 0})["mean"], 4),
                round(diversity.get(s, 0), 4),
            ])
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
