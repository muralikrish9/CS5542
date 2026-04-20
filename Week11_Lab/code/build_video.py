"""Assemble a 90s demo video for Quiz Challenge-1.
Sections:
  0-6s   title card
  6-20s  pipeline / methodology
  20-40s prompt strategies (naive / structured / negative)
  40-75s results gallery (4 products, ~9s each)
  75-90s metrics + closing
All frames rendered as 1920x1080 PNGs and encoded with ffmpeg."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, shutil, os

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "video"
OUT.mkdir(exist_ok=True)
FRAMES = OUT / "frames"
if FRAMES.exists(): shutil.rmtree(FRAMES)
FRAMES.mkdir()

W, H = 1920, 1080
NAVY = (11, 31, 59)
TEAL = (20, 184, 166)
WHITE = (255, 255, 255)
INK = (31, 42, 68)
MUTED = (107, 114, 128)
FAINT = (243, 244, 246)
PALE = (203, 213, 225)

def load_font(size, bold=False):
    names = ["segoeuib.ttf" if bold else "segoeui.ttf",
             "arialbd.ttf" if bold else "arial.ttf",
             "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except: pass
    return ImageFont.load_default()

def draw_card(title_eyebrow, title, lines=None, accent_bar=True):
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    if accent_bar:
        d.rectangle([0, 0, W, 12], fill=TEAL)
    d.text((100, 70), title_eyebrow, fill=TEAL, font=load_font(28, True))
    d.text((100, 120), title, fill=NAVY, font=load_font(64, True))
    d.rectangle([100, 230, 180, 238], fill=TEAL)
    if lines:
        y = 280
        for ln, sz, col, bold in lines:
            d.text((100, y), ln, fill=col, font=load_font(sz, bold))
            y += int(sz * 1.6)
    return img

def title_card():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 820, W, 828], fill=TEAL)
    d.text((100, 140), "CS 5542 · QUIZ CHALLENGE-1", fill=TEAL, font=load_font(32, True))
    d.text((100, 210), "AI-Controlled E-Commerce", fill=WHITE, font=load_font(96, True))
    d.text((100, 330), "Product Image Generation", fill=WHITE, font=load_font(96, True))
    d.text((100, 500), "Comparing prompt control strategies on SDXL-Turbo", fill=PALE, font=load_font(40))
    d.text((100, 560), "and Stable Diffusion 1.5 across 15 products", fill=PALE, font=load_font(40))
    d.text((100, 870), "Murali Ediga", fill=WHITE, font=load_font(36, True))
    d.text((100, 920), "University of Missouri–Kansas City  ·  April 20, 2026", fill=PALE, font=load_font(24))
    return img

def pipeline_card():
    img = draw_card("01 · METHODOLOGY", "End-to-end pipeline", lines=[
        ("Metadata CSV → Prompt templating → Stable Diffusion → 135 images → CLIP evaluation", 32, INK, False),
    ])
    d = ImageDraw.Draw(img)
    boxes = [("Metadata", "15 products"),
             ("Prompt", "A / B / C"),
             ("Stable Diffusion", "SDXL-Turbo + SD 1.5"),
             ("Outputs", "135 images"),
             ("Evaluation", "CLIP + consistency")]
    x0, y0 = 100, 480
    bw, bh, gap = 320, 300, 40
    for i, (t, sub) in enumerate(boxes):
        x = x0 + i * (bw + gap)
        accent = (i == 2)
        bg = NAVY if accent else WHITE
        d.rectangle([x, y0, x + bw, y0 + bh], fill=bg, outline=(229,231,235), width=2)
        d.rectangle([x, y0, x + 10, y0 + bh], fill=TEAL)
        d.text((x + 30, y0 + 40), t, fill=(WHITE if accent else NAVY), font=load_font(32, True))
        d.text((x + 30, y0 + 110), sub, fill=(PALE if accent else INK), font=load_font(22))
    return img

def prompt_card():
    img = draw_card("02 · PROMPT STRATEGIES", "Three prompts, one product")
    d = ImageDraw.Draw(img)
    cols = [
        ("A · Naive",   "Classic Leather Oxford Shoes",
         "Just the title — baseline."),
        ("B · Structured",
         "Classic Leather Oxford Shoes, Brown, made of Genuine Leather, Formal style, Lace-up stitched sole polished finish, studio lighting, clean white background, centered product shot, 4k, photorealistic, commercial photography",
         "Metadata → templated prompt + quality tokens."),
        ("C · Structured + Negative",
         "Same structured prompt, rendered with SD 1.5 + CFG 7.5",
         "Negative: blurry, low quality, watermark, cluttered background, cartoon, sketch."),
    ]
    x0, y0 = 100, 320
    bw, bh, gap = 560, 600, 40
    for i, (label, text, note) in enumerate(cols):
        x = x0 + i * (bw + gap)
        d.rectangle([x, y0, x + bw, y0 + bh], fill=WHITE, outline=(229,231,235), width=2)
        d.rectangle([x, y0, x + bw, y0 + 12], fill=TEAL)
        d.text((x + 30, y0 + 40), label, fill=NAVY, font=load_font(34, True))
        # wrap
        font = load_font(22)
        wrap_text(d, text, font, x + 30, y0 + 120, bw - 60, 26, INK, max_lines=15)
        d.text((x + 30, y0 + bh - 70), note, fill=TEAL, font=load_font(20, True))
    return img

def wrap_text(d, text, font, x, y, max_w, lh, col, max_lines=99):
    words = text.split()
    line, cur = "", ""
    n = 0
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            d.text((x, y + n * lh), cur, fill=col, font=font)
            cur = w
            n += 1
            if n >= max_lines: return
    if cur:
        d.text((x, y + n * lh), cur, fill=col, font=font)

def grid_card(grid_path, product_label):
    img = draw_card("03 · RESULTS", product_label)
    d = ImageDraw.Draw(img)
    d.text((100, 240), "Naive   ·   Structured   ·   Structured + Negative",
           fill=TEAL, font=load_font(24, True))
    g = Image.open(grid_path).convert("RGB")
    # scale to width 1720
    gw = 1720
    gh = int(g.height * gw / g.width)
    g = g.resize((gw, gh))
    img.paste(g, (100, 320))
    return img

def metrics_card():
    img = draw_card("04 · EVALUATION", "Quantitative results (CLIP)")
    d = ImageDraw.Draw(img)
    hdr = ["Strategy", "CLIP align", "Consistency", "Diversity"]
    rows = [
        ("A · Naive",                 "0.314", "0.907",   "0.349"),
        ("B · Structured",            "0.308", "0.932 ★", "0.332"),
        ("C · Structured + Negative", "0.306", "0.881",   "0.304"),
    ]
    x0, y0 = 100, 330
    cw = [600, 300, 360, 300]
    rh = 80
    # header
    x = x0
    d.rectangle([x0, y0, x0 + sum(cw), y0 + rh], fill=NAVY)
    for h, w in zip(hdr, cw):
        d.text((x + 20, y0 + 22), h, fill=WHITE, font=load_font(28, True))
        x += w
    # rows
    y = y0 + rh
    for i, row in enumerate(rows):
        bg = WHITE if i % 2 == 0 else FAINT
        d.rectangle([x0, y, x0 + sum(cw), y + rh], fill=bg, outline=(229,231,235))
        x = x0
        for j, (cell, w) in enumerate(zip(row, cw)):
            color = TEAL if "★" in cell else INK
            bold = "★" in cell
            d.text((x + 20, y + 22), cell, fill=color, font=load_font(26, bold))
            x += w
        y += rh
    d.text((100, 780), "Finding: structured prompts +2.7 pts image consistency over naive.",
           fill=NAVY, font=load_font(30, True))
    d.text((100, 830), "Limitation: CLIP-alignment favors short prompts (length bias).",
           fill=INK, font=load_font(26))
    d.text((100, 880), "Turbo models disable CFG → negative prompts require non-turbo base.",
           fill=INK, font=load_font(26))
    return img

def closing_card():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 120, W, 128], fill=TEAL)
    d.text((100, 200), "Thank you.", fill=TEAL, font=load_font(120, True))
    d.text((100, 420), "GitHub",   fill=TEAL,  font=load_font(28, True))
    d.text((100, 470), "github.com/muralikrish9/CS5542/tree/master/Week11_Lab", fill=WHITE, font=load_font(32))
    d.text((100, 600), "Demo video",  fill=TEAL,  font=load_font(28, True))
    d.text((100, 650), "youtu.be/LR7pLWJjRjQ", fill=WHITE, font=load_font(32))
    d.text((100, 900), "Murali Ediga · CS 5542 · Spring 2026", fill=PALE, font=load_font(24))
    return img

# -------- assemble timeline (90s total, 30 fps) --------
FPS = 30
SEGMENTS = [
    (title_card,      6),
    (pipeline_card,  12),
    (prompt_card,    18),
]
# Results: 4 products, 8s each = 32s
products = [
    ("p01_compare.png", "p01 · Classic Leather Oxford Shoes"),
    ("p03_compare.png", "p03 · Wireless Over-Ear Headphones"),
    ("p07_compare.png", "p07 · Leather Crossbody Handbag"),
    ("p13_compare.png", "p13 · Velvet Tufted Sofa"),
]

frame_idx = 0
def add(img, seconds):
    global frame_idx
    n = int(seconds * FPS)
    for _ in range(n):
        img.save(FRAMES / f"f_{frame_idx:05d}.png")
        frame_idx += 1

print("rendering title/pipeline/prompt...")
add(title_card(), 6)
add(pipeline_card(), 12)
add(prompt_card(), 18)
print("rendering results...")
for fn, label in products:
    grid_path = ROOT / "outputs" / "grids" / fn
    add(grid_card(grid_path, label), 8)
print("rendering metrics/closing...")
add(metrics_card(), 12)
add(closing_card(), 6)

# Total: 6+12+18+32+12+6 = 86s  (under 90, within 1-2 min)
print(f"total frames: {frame_idx} ({frame_idx/FPS:.1f}s)")

# encode locally if possible, else via lab-pc
video_path = OUT / "cs5542_quiz1_demo.mp4"
ffmpeg = shutil.which("ffmpeg")
if ffmpeg:
    subprocess.check_call([
        ffmpeg, "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES / "f_%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
        "-preset", "medium",
        str(video_path),
    ])
    print("video:", video_path)
else:
    print("no local ffmpeg; frames left in", FRAMES)
