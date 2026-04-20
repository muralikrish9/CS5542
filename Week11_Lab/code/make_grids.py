"""Build side-by-side comparison grids (naive | structured | negative) per product."""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

STRATS = ["A_naive", "B_structured", "C_negative"]
LABELS = ["Naive prompt", "Structured prompt", "Structured + Negative"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--grid-out", default="outputs/grids")
    args = ap.parse_args()
    root = Path(args.out)
    grid_dir = Path(args.grid_out)
    grid_dir.mkdir(parents=True, exist_ok=True)

    log = json.load(open(root / "generation_log.json"))
    by_product = {}
    for e in log:
        by_product.setdefault(e["product_id"], {}).setdefault(e["strategy"], []).append(e["file"])

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    for pid, strat_files in by_product.items():
        # pick seed=0 (first image) from each strategy
        rows = []
        for s in STRATS:
            files = sorted(strat_files.get(s, []))
            if not files: continue
            img = Image.open(root / files[0]).convert("RGB").resize((512, 512))
            rows.append(img)
        if len(rows) != 3: continue
        W, H = 512, 512
        LABEL_H = 40
        grid = Image.new("RGB", (W * 3, H + LABEL_H), "white")
        draw = ImageDraw.Draw(grid)
        for i, (img, lbl) in enumerate(zip(rows, LABELS)):
            draw.text((i * W + 10, 8), lbl, fill="black", font=font)
            grid.paste(img, (i * W, LABEL_H))
        grid.save(grid_dir / f"{pid}_compare.png")
        print(f"grid: {pid}")

if __name__ == "__main__":
    main()
