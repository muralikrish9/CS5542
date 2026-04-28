"""Render the pptx to PNGs (via PowerPoint COM) then stitch to MP4 with ffmpeg.

Output: slides/QuizChallenge2_demo.mp4 (~75 sec, 1920x1080, no audio)
"""
from __future__ import annotations
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
SLIDES = ROOT / "slides"
PPTX = SLIDES / "QuizChallenge2.pptx"
PNG_DIR = SLIDES / "_png"
MP4 = SLIDES / "QuizChallenge2_demo.mp4"

# 10 slides, ~7.5 sec each = 75 sec total
SECONDS_PER_SLIDE = 7.5
WIDTH, HEIGHT = 1920, 1080


def export_slides_to_png():
    """Use PowerPoint via COM to export each slide as a PNG at 1920x1080."""
    import comtypes.client

    if PNG_DIR.exists():
        shutil.rmtree(PNG_DIR)
    PNG_DIR.mkdir(parents=True)

    pp = comtypes.client.CreateObject("PowerPoint.Application")
    # PowerPoint 2016+ doesn't allow visible=False on all SKUs; set to 1 if 0 fails.
    try:
        pp.Visible = 1
    except Exception:
        pass

    pres = pp.Presentations.Open(str(PPTX.resolve()), WithWindow=False)
    n = pres.Slides.Count
    print(f"[video] exporting {n} slides to PNG @ {WIDTH}x{HEIGHT} ...")
    for i in range(1, n + 1):
        out = PNG_DIR / f"slide_{i:02d}.png"
        pres.Slides(i).Export(str(out.resolve()), "PNG", WIDTH, HEIGHT)
        print(f"[video]   {out.name}")
    pres.Close()
    pp.Quit()
    return n


def stitch_mp4(n_slides: int):
    """ffmpeg: still PNGs -> H.264 MP4 with `SECONDS_PER_SLIDE` per frame."""
    fps = 1.0 / SECONDS_PER_SLIDE
    pattern = str(PNG_DIR / "slide_%02d.png")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "warning",
        "-framerate", f"{fps}",
        "-i", pattern,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps=30",
        "-r", "30",
        str(MP4.resolve()),
    ]
    print(f"[video] stitching -> {MP4.name}")
    subprocess.run(cmd, check=True)


def main():
    if not PPTX.exists():
        print(f"[video] no pptx at {PPTX}; run `python -m src.make_slides` first")
        sys.exit(1)
    n = export_slides_to_png()
    stitch_mp4(n)
    duration = n * SECONDS_PER_SLIDE
    print(f"[video] DONE — {MP4} ({duration:.0f} s, no audio)")


if __name__ == "__main__":
    main()
