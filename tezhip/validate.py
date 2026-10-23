"""Doğrulama: kenar boşlukları ve ayna simetrisi; kontakt sayfası.
Kullanım: python3 validate.py [01 02 ...]  ->  validation.json, contact_sheet.png"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
DPI = 600
PX_PER_MM = DPI / 25.4
ASTAR = np.array([0xF7, 0xF3, 0xE8], dtype=np.int16)
TOL_ASTAR = 8          # astar sayılma eşiği (kanal başına)
TOL_SYM = 64           # simetri: kanal farkı bu değeri aşan piksel "farklı" sayılır
AXES = {"01": "D2", "02": "V", "03": "D2", "04": "D2", "05": "V", "06": "D2", "07": "D2"}
CHUNK = 512


def load(k):
    return np.asarray(Image.open(f"tezhip_{k}.png").convert("RGB"))


def margins(a):
    H, W, _ = a.shape
    rows = np.zeros(H, bool)
    cols = np.zeros(W, bool)
    for y in range(0, H, CHUNK):
        blk = a[y:y + CHUNK].astype(np.int16)
        m = (np.abs(blk - ASTAR) > TOL_ASTAR).any(axis=2)
        rows[y:y + CHUNK] = m.any(axis=1)
        cols |= m.any(axis=0)
    ys = np.flatnonzero(rows)
    xs = np.flatnonzero(cols)
    l, r = int(xs[0]), int(W - 1 - xs[-1])
    t, b = int(ys[0]), int(H - 1 - ys[-1])
    mm = lambda v: round(v / PX_PER_MM, 2)
    return {"sol_px": l, "sag_px": r, "ust_px": t, "alt_px": b,
            "sol_mm": mm(l), "sag_mm": mm(r), "ust_mm": mm(t), "alt_mm": mm(b),
            "fark_yatay_px": abs(l - r), "fark_dikey_px": abs(t - b),
            "ilk_son_x": [int(xs[0]), int(xs[-1])], "ilk_son_y": [int(ys[0]), int(ys[-1])]}


def sym_vertical(a):
    """Dikey eksende aynala (sol-sağ) ve karşılaştır."""
    H, W, _ = a.shape
    diff = 0
    mad = 0.0
    for y in range(0, H, CHUNK):
        blk = a[y:y + CHUNK].astype(np.int16)
        d = np.abs(blk - blk[:, ::-1]).max(axis=2)
        diff += int((d > TOL_SYM).sum())
        mad += float(d.sum())
    n = H * W
    return {"farkli_piksel_orani_%": round(100 * diff / n, 4), "ortalama_mutlak_fark": round(mad / n, 4)}


def sym_horizontal(a):
    """Yatay eksende aynala (üst-alt) ve karşılaştır."""
    H, W, _ = a.shape
    diff = 0
    mad = 0.0
    for y in range(0, (H + 1) // 2, CHUNK):
        y2 = min(y + CHUNK, (H + 1) // 2)
        top = a[y:y2].astype(np.int16)
        bot = a[H - y2:H - y][::-1].astype(np.int16)
        d = np.abs(top - bot).max(axis=2)
        diff += 2 * int((d > TOL_SYM).sum())
        mad += 2 * float(d.sum())
    n = H * W
    return {"farkli_piksel_orani_%": round(100 * diff / n, 4), "ortalama_mutlak_fark": round(mad / n, 4)}


def validate(k):
    a = load(k)
    res = {"dosya": f"tezhip_{k}.png", "boyut_px": [a.shape[1], a.shape[0]], "simetri_grubu": AXES[k]}
    res["kenar"] = margins(a)
    res["simetri_dikey_eksen"] = sym_vertical(a)
    if AXES[k] == "D2":
        res["simetri_yatay_eksen"] = sym_horizontal(a)
    m = res["kenar"]
    ok_m = m["fark_yatay_px"] <= 1 and m["fark_dikey_px"] <= 1
    ok_s = res["simetri_dikey_eksen"]["farkli_piksel_orani_%"] <= 0.5 and \
        res.get("simetri_yatay_eksen", {"farkli_piksel_orani_%": 0})["farkli_piksel_orani_%"] <= 0.5
    res["kenar_gecti"] = ok_m
    res["simetri_gecti"] = ok_s
    print(json.dumps(res, ensure_ascii=False), flush=True)
    return res


def contact_sheet(keys, out="contact_sheet.png"):
    tw, th = 472, 661          # 500x700 oranında küçük önizleme
    pad, lab = 30, 0
    cols = 4
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * pad, rows * th + (rows + 1) * pad), (60, 58, 54))
    for i, k in enumerate(keys):
        im = Image.open(f"tezhip_{k}.png")
        im.draft("RGB", (tw, th))
        im = im.convert("RGB").resize((tw, th), Image.LANCZOS)
        x = pad + (i % cols) * (tw + pad)
        y = pad + (i // cols) * (th + pad)
        sheet.paste(im, (x, y))
    sheet.save(out, dpi=(96, 96))


if __name__ == "__main__":
    keys = sys.argv[1:] or sorted(AXES)
    results = {}
    if os.path.exists("validation.json"):
        results = json.load(open("validation.json", encoding="utf-8"))
    for k in keys:
        results[k] = validate(k)
    json.dump(results, open("validation.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    done = [k for k in sorted(AXES) if os.path.exists(f"tezhip_{k}.png")]
    contact_sheet(done)
