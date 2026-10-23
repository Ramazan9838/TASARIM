"""Kaynak SVG, vektör PDF ve 600 dpi PNG üretimi (cairosvg).
Kullanım: python3 build.py [01 02 ...]"""
import io
import sys
import time

import cairosvg
from PIL import Image

from compositions import COMPS
from motifs import CX, CY

Image.MAX_IMAGE_PIXELS = None
DPI = 600
EXPECTED = (11811, 16535)


def raster_phase(svg):
    """Raster fazı hizalaması: 600 dpi'da sayfa 11811,02 x 16535,43 px eder;
    tam sayı piksele yuvarlanan PNG'de geometrik eksenler (250 / 350 mm)
    piksel ızgarasının orta çizgisine (5905,5 / 8267,5 px) düşmez. Tezhip
    alanı PNG için dx, dy kadar (mikron mertebesi) kaydırılır; böylece
    PNG'nin ayna ekseni tasarımın ayna ekseniyle çakışır. SVG ve PDF
    değişmez."""
    ppm = DPI / 25.4
    dx = CX - (EXPECTED[0] / 2) / ppm
    dy = CY - (EXPECTED[1] / 2) / ppm
    tag = '<g clip-path="url(#tezhip_alani)">'
    return svg.replace(tag, f'<g transform="translate({-dx:.6f},{-dy:.6f})">' + tag, 1).replace("</svg>", "</g></svg>")


def build(k):
    t0 = time.time()
    svg = COMPS[k]()
    with open(f"tezhip_{k}.svg", "w", encoding="utf-8") as fh:
        fh.write(svg)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=f"tezhip_{k}.pdf")
    png = cairosvg.svg2png(bytestring=raster_phase(svg).encode(), dpi=DPI)
    im = Image.open(io.BytesIO(png))
    del png
    if im.size != EXPECTED:
        raise SystemExit(f"{k}: PNG boyutu {im.size} != {EXPECTED}")
    im.convert("RGB").save(f"tezhip_{k}.png", dpi=(DPI, DPI), compress_level=6)
    import json, os
    from compositions import HAT
    hp = "hat_alanlari.json"
    data = json.load(open(hp, encoding="utf-8")) if os.path.exists(hp) else {}
    data[k] = HAT[k]
    json.dump(dict(sorted(data.items())), open(hp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"{k}: SVG {len(svg) / 1e6:.1f} MB, PNG {im.size[0]}x{im.size[1]} px, {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    for k in (sys.argv[1:] or sorted(COMPS)):
        build(k)
