"""Photo figures of the JOH metapaper: crop, rotate and number the parts.

    python3 make_photo_figures.py

Reads ../photos/*.jpg (already without EXIF) and writes photo_*.jpg next to this script.
Parts are marked with numbered white discs; what each number means is in the figure
caption, so a caption can be corrected without touching the picture. Coordinates are in
the pixels of the source photo.
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTOS = os.path.join(HERE, "..", "photos")
INK = (34, 34, 34)

# name: (source, crop box, degrees counter-clockwise after the crop, [(number, x, y), ...])
FIGURES = {
    "photo_calibrator_inside": ("calibrator_inside.jpg", (30, 160, 1500, 1100), 0, [
        (1, 300, 650), (2, 290, 375), (3, 690, 520), (4, 505, 492), (5, 685, 725),
        (6, 468, 905), (7, 1068, 830), (8, 880, 1018), (9, 655, 950), (10, 1415, 460)]),
    "photo_board_input": ("board_input.jpg", (250, 60, 1820, 1470), 0, [
        (1, 940, 700), (2, 1010, 300), (3, 1460, 1020), (3, 1490, 1310)]),
    # Revision B close-up supplied as a PNG. No labels are burned into this evidence
    # image: U6, the 47 kOhm resistor and the RA2 link are identified in the caption.
    "photo_board_ref3040": ("board_ref3040.png", (0, 0, 1500, 2100), 0, []),
    "photo_boards": ("boards_three.jpg", (150, 140, 1500, 1980), 0, [
        (1, 1180, 820), (2, 490, 1150), (3, 490, 1400), (4, 650, 1720)]),
    "photo_channel_a": ("calibrator_vs_ph150.jpg", (0, 430, 1500, 1300), 0, [
        (1, 185, 620), (2, 890, 700), (3, 470, 1120)]),
    "photo_setup_f": ("setup_electrode.jpg", (80, 100, 1400, 1720), 90, [
        (1, 720, 480), (2, 1120, 640), (3, 860, 1470), (4, 360, 380), (4, 390, 1040)]),
    "photo_r50m": ("calibrator_50M.jpg", (300, 100, 1110, 960), 0, []),   # the caption says it all
}

# Final photographs used by the metapaper.  The previews have an identical canvas so
# Markdown renderers display portrait and landscape photographs at a consistent size.
# Each preview remains a link to the corresponding full-resolution photograph.
PREVIEWS = {
    "preview_i-02.jpg": os.path.join(HERE, "..", "article", "img", "i-02.jpg"),
    "preview_board_input.jpg": os.path.join(HERE, "photo_board_input.jpg"),
    "preview_board_bottom.jpg": os.path.join(HERE, "..", "photos", "board_a_bottom.png"),
    "preview_calibrator_inside.jpg": os.path.join(HERE, "photo_calibrator_inside.jpg"),
    "preview_soldering.jpg": os.path.join(HERE, "soldering.jpg"),
    "preview_r50m.jpg": os.path.join(HERE, "photo_r50m.jpg"),
    "preview_boards.jpg": os.path.join(HERE, "photo_boards.jpg"),
    "preview_setup_f.jpg": os.path.join(HERE, "photo_setup_f.jpg"),
}
PREVIEW_SIZE = (520, 390)


def disc(draw, x, y, r, n):
    draw.ellipse((x - r, y - r, x + r, y + r), fill="white", outline=INK, width=max(2, r // 7))
    font = ImageFont.load_default(size=int(r * 1.15))
    draw.text((x, y), str(n), fill=INK, font=font, anchor="mm")


def make(name, src, box, rot, marks):
    im = Image.open(os.path.join(PHOTOS, src)).convert("RGB")
    k = im.width / 1500 if im.height > im.width else im.width / 2000   # marks use the 1500/2000-wide grid
    x0, y0, x1, y1 = (round(v * k) for v in box)
    im = im.crop((x0, y0, x1, y1))
    w = im.width
    pts = [(n, round(x * k) - x0, round(y * k) - y0) for n, x, y in marks]
    if rot == 90:                               # counter-clockwise; discs are drawn upright after it
        im = im.transpose(Image.Transpose.ROTATE_90)
        pts = [(n, y, w - x) for n, x, y in pts]
    d = ImageDraw.Draw(im)
    r = round(0.03 * max(im.size))
    for n, x, y in pts:
        disc(d, x, y, r, n)
    im.save(os.path.join(HERE, name + ".jpg"), quality=88)
    print(name, im.size)


def make_preview(name, source):
    with Image.open(source) as original:
        im = original.convert("RGB")
    im.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", PREVIEW_SIZE, "white")
    canvas.paste(im, ((PREVIEW_SIZE[0] - im.width) // 2, (PREVIEW_SIZE[1] - im.height) // 2))
    canvas.save(os.path.join(HERE, name), quality=88)
    print(name, canvas.size)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--previews-only",
        action="store_true",
        help="refresh equal-size Markdown previews without regenerating the edited photos",
    )
    args = parser.parse_args()
    if not args.previews_only:
        for name, spec in FIGURES.items():
            make(name, *spec)
    for name, source in PREVIEWS.items():
        make_preview(name, source)
