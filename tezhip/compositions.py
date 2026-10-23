"""Yedi tezhip kompozisyonu. Her fonksiyon tam SVG metni döndürür."""
import math

from motifs import *

TAH = C["tahrir"]
SEAM = 0.05  # ayna kopyaları eksende üst üste biner: kenar yumuşatma dikişi oluşmaz


def doc(body, defs, title):
    x0, y0, x1, y1 = AREA
    area_clip = f'<clipPath id="tezhip_alani"><path d="{rect(x0, y0, x1, y1).d()}"/></clipPath>'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(PAGE_W)}mm" height="{num(PAGE_H)}mm" '
        f'viewBox="0 0 {num(PAGE_W)} {num(PAGE_H)}">'
        f"<title>{title}</title>"
        f"<defs>{area_clip}{''.join(defs.items)}</defs>"
        f'<rect x="0" y="0" width="{num(PAGE_W)}" height="{num(PAGE_H)}" fill="{C["astar"]}"/>'
        f'<g clip-path="url(#tezhip_alani)">{body}</g>'
        "</svg>"
    )


def quad(defs, content, x0, y0, x1, y1):
    """D2: içerik yalnız sağ-üst çeyrekte (CX..x1, y0..CY) tutulur, iki eksende
    aynalanır. (x0, y0, x1, y1) bütün alanın sınırı."""
    cid = defs.clip(rect(CX - SEAM, y0 - 1, x1 + 1, CY + SEAM))
    return sym_d2(g(content, clip=cid))


def half(defs, content, y0, x1, y1):
    """Dikey ayna: içerik yalnız sağ yarıda (CX..x1) tutulur ve aynalanır."""
    cid = defs.clip(rect(CX - SEAM, y0 - 1, x1 + 1, y1 + 1))
    return sym_v(g(content, clip=cid))


def clipped(defs, content, path):
    return g(content, clip=defs.clip(path))


# ---- dolgu yardımcıları ------------------------------------------------------
def flower_set(pal, sw=0.25, scale=0.46):
    """Helezon merkezlerine çiçek: hatâyî / penç / gonca dönüşümlü."""
    def fn(p, d, k, ang):
        s = d * scale
        tx, ty = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        kind = k % 3
        if kind == 0:
            c = (p[0] + tx * s * 0.35, p[1] + ty * s * 0.35)
            return hatayi(place(c[0], c[1], s, ang + 90), pal["f1"], pal.get("t", TAH), sw,
                          inner=pal["f2"], calyx=pal.get("cal", pal["f1"]), center=pal.get("c", C["altin"]))
        if kind == 1:
            return penc(place(p[0], p[1], s * 0.42, ang), pal["p1"], pal.get("t", TAH), sw,
                        inner=pal["p2"], center=pal.get("c", C["altin"]))
        c = (p[0] + tx * s * 0.1, p[1] + ty * s * 0.1)
        return gonca(place(c[0], c[1], s * 0.62, ang + 90), pal["g1"], pal.get("t", TAH), sw,
                     sepal=pal.get("gs", pal["l1"]), inner=pal.get("gi", C["astar"]))
    return fn


def leaf_set(pal, sw=0.22, scale=0.30, rumi_too=True):
    def fn(p, ang, d, k):
        s = d * scale
        if rumi_too and k % 2:
            return rumi(place(p[0], p[1], s * 0.9, ang + 90 - 90), pal.get("r1", pal["l1"]), pal.get("t", TAH), sw,
                        eye_color=pal.get("t", TAH))
        return yaprak(place(p[0], p[1], s, ang + 90), pal["l1"], pal.get("t", TAH), sw)
    return fn


def scroll(bbox, d, pal, sw_stem=0.6, sw=0.25, fscale=0.46, lscale=0.30, rumi_too=True, seed=0,
           phase=(0, 0), turns=1.05):
    stems, motifs_ = scroll_field(bbox, d, pal["stem"], sw_stem, flower_set(pal, sw, fscale),
                                  leaf_fn=leaf_set(pal, sw * 0.9, lscale, rumi_too), seed=seed,
                                  phase=phase, turns=turns)
    return stems + motifs_


def corner_penc(fill, inner, ground=None, n=5):
    def fn(cx, cy, w):
        out = ""
        if ground:
            out += el(rect(cx - w / 2, cy - w / 2, cx + w / 2, cy + w / 2), ground)
        return out + penc(place(cx, cy, w * 0.40), fill, TAH, 0.25, n=n, inner=inner)
    return fn


def band_content(pal, k_per=1.7, amp=0.24, sw_stem=0.6, fscale=0.62, lscale=0.30):
    def content(L):
        w = pal["w"]
        k = odd(L / (w * k_per))

        def flower(p, rot, w_, m):
            # rot==0: dal tepesi alt kenarda, çiçek yukarı (karşı kenara) bakar
            up = -1 if rot == 0 else 1
            s = w_ * fscale
            if m % 2 == 0:
                return hatayi(place(p[0], p[1] + up * s * 0.42, s, 0 if up < 0 else 180),
                              pal["f1"], TAH, 0.25, inner=pal["f2"], calyx=pal.get("cal", pal["f1"]))
            c = (p[0], p[1] + up * w_ * 0.30)
            return penc(place(c[0], c[1], w_ * 0.22), pal["p1"], TAH, 0.25, inner=pal["p2"])

        def leaf(p, rot, w_, m, side):
            if m % 2:
                return rumi(place(p[0], p[1], w_ * 0.30, rot + side * 90, flip=side > 0), pal.get("r1", pal["l1"]), TAH, 0.2)
            return yaprak(place(p[0], p[1], w_ * 0.30, rot, flip=side > 0), pal["l1"], TAH, 0.2)

        return band_scroll(L, w, k, pal["stem"], sw_stem, flower, leaf, amp)
    return content


def tig_around(path, n, L, w, color, keep=None):
    out = []
    for i, (p, nrm) in enumerate(sample_closed(path, n)):
        if keep and not keep(p):
            continue
        Ld = L if i % 2 == 0 else L * 0.6
        q = (p[0] + nrm[0] * 0.6, p[1] + nrm[1] * 0.6)
        out.append(el(tig_path(q, nrm, Ld, w if i % 2 == 0 else w * 0.75), color))
    return "".join(out)


HAT = {}  # kompozisyon -> hat alanı tanımı (rapor için)


def _inside(poly, p):
    x, y = p
    ins = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def safe_rect(poly, margin=4.0):
    """Hat alanına (dikey eksene simetrik) sığan, kenardan margin mm uzak,
    alanı en büyük eksen-paralel dikdörtgen: (genişlik, yükseklik)."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    W, H = (max(xs) - min(xs)) / 2, (max(ys) - min(ys)) / 2
    best = (0, 0, 0)
    for i in range(1, 80):
        w = W * i / 80
        for oy in [H * k / 20 for k in range(-6, 7)]:
            lo, hi = 0.0, H
            for _ in range(30):
                h = (lo + hi) / 2
                ok = all(_inside(poly, (cx + sx * (w + margin), cy + oy + sy * (h + margin)))
                         for sx in (-1, 0, 1) for sy in (-1, 0, 1) if sx or sy) and \
                    all(_inside(poly, (cx + (w + margin) * t, cy + oy + sy * (h + margin)))
                        for t in (-0.75, -0.5, -0.25, 0.25, 0.5, 0.75) for sy in (-1, 1)) and \
                    all(_inside(poly, (cx + sx * (w + margin), cy + oy + (h + margin) * t))
                        for t in (-0.75, -0.5, -0.25, 0.25, 0.5, 0.75) for sx in (-1, 1))
                lo, hi = (h, hi) if ok else (lo, h)
            if 4 * w * lo > best[0]:
                best = (4 * w * lo, 2 * w, 2 * lo)
    return best[1], best[2]


def hat_alani(key, path, label, rule=C["altin"], rule_w=1.2, inset_rule=True):
    """Hat (kitâbe) için boş, astar renkli merkez alanı: içi tamamen boş
    bırakılır; kenarında altın cetvel ve ince tahrir. Ölçüler rapora yazılır."""
    poly = [p for p, _ in sample_closed(path, 720)]
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    w_s, h_s = safe_rect(poly)
    HAT[key] = {"bicim": label, "genislik_mm": round(max(xs) - min(xs), 1), "yukseklik_mm": round(max(ys) - min(ys), 1),
                "guvenli_dikdortgen_mm": [round(w_s, 1), round(h_s, 1)],
                "merkez_mm": [round((max(xs) + min(xs)) / 2, 1), round((max(ys) + min(ys)) / 2, 1)]}
    out = [el(path, C["astar"], rule, rule_w), el(path, "none", TAH, 0.3)]
    return "".join(out)


# ============================================================ 01 Osmanlı klasik
def comp01():
    defs = Defs()
    body = []
    frame, (ix0, iy0, ix1, iy1) = outer_frame(defs, C["lacivert"], C["altin"], C["lacivert"])
    body.append(frame)
    # ana bordür: lacivert zemin, altın koşan helezon, firuze ara renk
    bx0, by0, bx1, by1 = ix0 + 2.5, iy0 + 2.5, ix1 - 2.5, iy1 - 2.5
    bw = 24
    pal_b = {"w": bw, "stem": C["altin"], "f1": C["altin"], "f2": C["firuze"], "cal": C["altin"],
             "p1": C["firuze"], "p2": C["altin"], "l1": C["altin"], "r1": C["firuze"]}
    body.append(frame_band(bx0, by0, bx1, by1, bw, C["lacivert"], band_content(pal_b),
                           corner_penc(C["altin"], C["firuze"], C["lacivert"]), C["altin"], 0.8))
    fx0, fy0, fx1, fy1 = bx0 + bw + 2.5, by0 + bw + 2.5, bx1 - bw - 2.5, by1 - bw - 2.5
    body.append(f'<path d="{rect(fx0 - 1.2, fy0 - 1.2, fx1 + 1.2, fy1 + 1.2).d()}" fill="none" stroke="{C["altin"]}" stroke-width="0.8"/>')
    field = rect(fx0, fy0, fx1, fy1)
    # zemin: halkâr (astar üzerine ince altın helezon)
    pal_h = {"stem": C["altin"], "f1": C["altin"], "f2": C["altin"], "cal": C["altin"], "p1": C["altin"],
             "p2": C["altin"], "g1": C["altin"], "gs": C["altin"], "gi": C["altin"], "l1": C["altin"],
             "r1": C["altin"], "t": C["altin_koyu"], "c": C["altin"]}
    halkar = scroll((CX, fy0, fx1, CY), 30, pal_h, sw_stem=0.45, sw=0.22, phase=(0, 6))
    body.append(clipped(defs, quad(defs, halkar, fx0, fy0, fx1, fy1), field))

    # şemse
    rx, ry = 90, 138
    semse = lobed_ellipse(CX, CY, rx, ry, 22, 0.075, phase=0.5)
    pal_s = {"stem": C["altin"], "f1": C["altin"], "f2": C["firuze"], "cal": C["altin"], "p1": C["firuze"],
             "p2": C["altin"], "g1": C["altin"], "gs": C["firuze"], "gi": C["firuze"], "l1": C["firuze"],
             "r1": C["altin"]}
    # salbekler (dikey uçlarda) ve tepelikler
    sal_h, sal_w = 46, 58
    sal_top = salbek_path(CX, CY - ry + 6, sal_w, sal_h, up=True)
    fin_top = semse_finial(CX, CY - ry - sal_h + 8, 10, 14, up=True)
    # üst salbek kurulur, alttaki yatay eksende aynasıdır (D2)
    st = [el(fin_top, C["lacivert"], C["altin"], 1.0),
          tig_around(sal_top, 34, 5.0, 1.5, C["lacivert"]),
          el(sal_top, C["lacivert"], C["altin"], 2.2), el(sal_top, "none", TAH, 0.3)]
    y_b = CY - ry + 6
    cont = [rumi(place(CX + 2, y_b - 8, 18, 10), C["altin"], TAH, 0.25),
            rumi(place(CX + 1, y_b - 18, 14, -8), C["firuze"], TAH, 0.25),
            penc(place(CX, y_b - 31, 6.5), C["firuze"], TAH, 0.25, inner=C["altin"])]
    st.append(clipped(defs, half(defs, "".join(cont), y_b - 60, CX + 40, y_b + 1), sal_top))
    st = "".join(st)
    body.append(st + mirror_y(st, CY))
    body.append(tig_around(semse, 120, 6.5, 1.7, C["lacivert"]))
    body.append(el(semse, C["lacivert"], C["altin"], 2.6))
    body.append(el(semse, "none", TAH, 0.35))
    inner_s = lobed_ellipse(CX, CY, rx - 3.2, ry - 3.2, 22, 0.075, phase=0.5)
    fill_s = scroll((CX, CY - ry, CX + rx, CY), 27, pal_s, sw_stem=0.7, sw=0.25, seed=1, phase=(0, 4))
    body.append(clipped(defs, quad(defs, fill_s, CX - rx, CY - ry, CX + rx, CY + ry), inner_s))
    # hat alanı: şemsenin içinde dilimli boş oval
    body.append(hat_alani("01", lobed_ellipse(CX, CY, rx - 22, ry - 24, 22, 0.075, phase=0.5), "dilimli oval (şemse içi)"))
    # köşebentler
    kw, kh = 108, 124
    kos = kosebent_path(fx1, fy0, kw, kh, 7, 0.10, sx=-1, sy=1)
    kos_in = kosebent_path(fx1, fy0, kw - 3, kh - 3, 7, 0.10, sx=-1, sy=1)
    kq = []
    kq.append(tig_around(kos, 70, 5.5, 1.5, C["lacivert"],
                         keep=lambda p: p[0] < fx1 - 2 and p[1] > fy0 + 2))
    kq.append(el(kos, C["lacivert"], C["altin"], 2.2))
    pal_k = dict(pal_s)
    pal_k["f1"] = C["firuze"]
    pal_k["f2"] = C["altin"]
    fill_k = scroll((fx1 - kw, fy0, fx1, fy0 + kh), 25, pal_k, sw_stem=0.6, sw=0.25, seed=2, phase=(4, 6))
    kq.append(clipped(defs, fill_k, kos_in))
    kq.append(el(kos, "none", TAH, 0.3))
    body.append(clipped(defs, sym_d2("".join(kq)), field))
    # köşebentlerin kendi tığları alan dışına taşmasın: alan klipi ile kes
    return doc("".join(body), defs, "Tezhip 01 - Osmanli klasik")


COMPS = {"01": comp01}


def stem(spine, color=C["zumrut"], w=1.3, edge=TAH, ew=0.3):
    d = bez(*spine).d()
    return (f'<path d="{d}" fill="none" stroke="{edge}" stroke-width="{num(w + 2 * ew)}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{num(w)}" stroke-linecap="round"/>')


def at(spine, t):
    p = cubic_pt(*spine, t)
    tx, ty = cubic_tan(*spine, t)
    return p, math.degrees(math.atan2(ty, tx))


def standard_border(frame_inner, w, gap=2.5):
    ix0, iy0, ix1, iy1 = frame_inner
    b = (ix0 + gap, iy0 + gap, ix1 - gap, iy1 - gap)
    f = (b[0] + w + gap, b[1] + w + gap, b[2] - w - gap, b[3] - w - gap)
    return b, f


# ============================================================ 02 Saz yolu
def comp02():
    defs = Defs()
    body = []
    frame, fin = outer_frame(defs, C["kobalt"], C["firuze"], C["kobalt"])
    body.append(frame)
    bw = 26
    (bx0, by0, bx1, by1), (fx0, fy0, fx1, fy1) = standard_border(fin, bw)

    def cint_item(x, u, i):
        return cintemani(place(x, 0, bw * 0.74), C["mercan"], C["kobalt"], TAH, 0.28)

    def between(x, u, i):
        return penc(place(x, 0, bw * 0.17), C["firuze"], TAH, 0.22, inner=C["astar"], center=C["mercan"])

    def content(L):
        return sym_band_items(L, int(round(L / 32)), cint_item, between)

    body.append(frame_band(bx0, by0, bx1, by1, bw, C["astar"], content,
                           corner_penc(C["mercan"], C["astar"], C["astar"]), C["kobalt"], 0.9))
    body.append(f'<path d="{rect(fx0 - 1.2, fy0 - 1.2, fx1 + 1.2, fy1 + 1.2).d()}" fill="none" stroke="{C["kobalt"]}" stroke-width="0.9"/>')
    field = rect(fx0, fy0, fx1, fy1)
    h = []
    sw = 0.3
    yb = fy1 - 10           # vazo tabanı
    vtop = yb - 104
    # --- gövdeler (dallar)
    S_main = ((CX, vtop + 2), (CX, vtop - 120), (CX, fy0 + 160), (CX, fy0 + 52))
    S1 = ((CX + 4, vtop + 6), (CX + 60, vtop - 20), (CX + 120, vtop - 60), (CX + 104, vtop - 150))
    S2 = ((CX + 3, vtop - 40), (CX + 70, vtop - 90), (CX + 46, vtop - 200), (CX + 92, vtop - 268))
    S3 = ((CX + 2, fy0 + 210), (CX + 40, fy0 + 190), (CX + 90, fy0 + 150), (CX + 112, fy0 + 70))
    S4 = ((CX + 6, vtop + 10), (CX + 60, vtop + 20), (CX + 110, vtop + 30), (CX + 128, vtop - 6))
    S5 = ((CX + 104, vtop - 150), (CX + 118, vtop - 175), (CX + 134, vtop - 190), (CX + 128, vtop - 222))
    for s in (S1, S2, S3, S4, S5, S_main):
        h.append(stem(s, C["zumrut"], 1.2))
    # --- saz yaprakları (büyük, kıvrık, dallara binen)
    h.append(saz(place(CX + 18, vtop - 4, 150, 38), C["zumrut"], TAH, 0.35, half=C["firuze"], curl=0.42))
    h.append(saz(place(CX + 70, vtop - 92, 118, -22, flip=True), C["kobalt"], TAH, 0.35, half=C["firuze"], curl=0.40))
    h.append(saz(place(CX + 8, fy0 + 236, 110, 52), C["zumrut"], TAH, 0.35, half=C["firuze"], curl=0.45))
    h.append(saz(place(CX + 96, vtop + 24, 64, 118, flip=True), C["kobalt"], TAH, 0.3, half=C["firuze"], curl=0.35, teeth=8))
    # --- küçük yapraklar
    for s, ts in ((S1, (0.35, 0.7)), (S2, (0.3, 0.62, 0.85)), (S3, (0.4, 0.75)), (S4, (0.5,)), (S_main, (0.25, 0.55, 0.8))):
        for i, t in enumerate(ts):
            p, a = at(s, t)
            side = 1 if i % 2 == 0 else -1
            if s is S_main:
                side = 1
            h.append(yaprak(place(p[0], p[1], 17, a + 90 + side * 55), C["zumrut"], TAH, 0.25, curve=0.12 * side))
    # --- çiçekler
    p, a = at(S1, 1.0)
    h.append(hatayi(place(p[0] + 6, p[1] - 22, 56, 12), C["mercan"], TAH, sw, inner=C["kobalt"],
                    calyx=C["zumrut"], center=C["firuze"]))
    p, a = at(S2, 1.0)
    h.append(penc(place(p[0] + 4, p[1] - 10, 18), C["kobalt"], TAH, sw, inner=C["firuze"], center=C["mercan"]))
    p, a = at(S3, 1.0)
    h.append(hatayi(place(p[0] + 2, p[1] - 16, 44, 8), C["kobalt"], TAH, sw, inner=C["mercan"],
                    calyx=C["zumrut"], center=C["firuze"]))
    p, a = at(S4, 1.0)
    h.append(gonca(place(p[0] + 3, p[1] + 2, 30, 20), C["mercan"], TAH, sw, sepal=C["zumrut"], inner=C["firuze"]))
    p, a = at(S5, 1.0)
    h.append(gonca(place(p[0], p[1] + 2, 26, 4), C["kobalt"], TAH, sw, sepal=C["zumrut"], inner=C["mercan"]))
    p, a = at(S2, 0.48)
    h.append(gonca(place(p[0] + 6, p[1], 22, 62), C["mercan"], TAH, sw, sepal=C["zumrut"], inner=C["astar"]))
    h.append(penc(place(CX + 132, fy0 + 26, 13), C["mercan"], TAH, sw, inner=C["astar"], center=C["kobalt"]))
    h.append(penc(place(CX + 138, vtop - 108, 11), C["firuze"], TAH, sw, inner=C["astar"], center=C["mercan"]))
    h.append(gonca(place(CX + 140, vtop + 62, 22, 30), C["kobalt"], TAH, sw, sepal=C["zumrut"], inner=C["firuze"]))
    h.append(penc(place(CX + 56, fy0 + 36, 10), C["kobalt"], TAH, sw, inner=C["firuze"], center=C["mercan"]))
    # üst ve orta boşluklar için ikincil saz yaprakları, goncalar ve pençler
    h.append(saz(place(CX + 24, fy0 + 168, 92, 28), C["kobalt"], TAH, 0.3, half=C["firuze"], curl=0.40, teeth=9))
    h.append(saz(place(CX + 110, fy0 + 330, 78, -8, flip=True), C["zumrut"], TAH, 0.3, half=C["firuze"], curl=0.38, teeth=8))
    h.append(gonca(place(CX + 82, fy0 + 104, 22, 24), C["mercan"], TAH, sw, sepal=C["zumrut"], inner=C["astar"]))
    h.append(penc(place(CX + 34, fy0 + 116, 9.5), C["firuze"], TAH, sw, inner=C["astar"], center=C["mercan"]))
    h.append(penc(place(CX + 126, fy0 + 232, 10.5), C["mercan"], TAH, sw, inner=C["astar"], center=C["kobalt"]))
    h.append(gonca(place(CX + 58, fy0 + 296, 20, 14), C["kobalt"], TAH, sw, sepal=C["zumrut"], inner=C["firuze"]))
    h.append(penc(place(CX + 36, vtop - 30, 9), C["mercan"], TAH, sw, inner=C["astar"], center=C["firuze"]))
    h.append(penc(place(CX + 130, fy0 + 440, 9.5), C["kobalt"], TAH, sw, inner=C["firuze"], center=C["mercan"]))
    h.append(gonca(place(CX + 104, fy0 + 256, 18, 40), C["firuze"], TAH, sw, sepal=C["zumrut"], inner=C["mercan"]))
    for (x, y, r_, sx) in ((CX + 60, fy0 + 66, 14, 1), (CX + 112, fy0 + 118, 15, -1), (CX + 140, fy0 + 290, 14, 1),
                           (CX + 30, fy0 + 268, 13, -1), (CX + 84, vtop - 4, 14, 1), (CX + 140, vtop - 40, 13, -1)):
        h.append(yaprak(place(x, y, r_, sx * 35), C["zumrut"], TAH, 0.25, curve=0.12 * sx))
    # eksen üstündeki çiçekler
    h.append(hatayi(place(CX, fy0 + 40, 64), C["mercan"], TAH, sw, inner=C["kobalt"], calyx=C["zumrut"], center=C["firuze"]))
    # --- vazo
    vase = sym_bez([
        ((CX, vtop), (CX + 10, vtop), (CX + 20, vtop), (CX + 24, vtop)),
        ((CX + 24, vtop), (CX + 24, vtop + 8), (CX + 14, vtop + 9), (CX + 13, vtop + 16)),
        ((CX + 13, vtop + 16), (CX + 12, vtop + 28), (CX + 20, vtop + 34), (CX + 36, vtop + 42)),
        ((CX + 36, vtop + 42), (CX + 64, vtop + 56), (CX + 68, vtop + 84), (CX + 44, vtop + 94)),
        ((CX + 44, vtop + 94), (CX + 34, vtop + 98), (CX + 22, vtop + 97), (CX + 20, vtop + 98)),
        ((CX + 20, vtop + 98), (CX + 28, vtop + 104)),
        ((CX + 28, vtop + 104), (CX, vtop + 104)),
    ])
    h.append(el(vase, C["kobalt"], TAH, 0.45))
    band = sym_bez([
        ((CX, vtop + 30), (CX + 10, vtop + 30), (CX + 18, vtop + 34), (CX + 28, vtop + 38)),
        ((CX + 28, vtop + 38), (CX + 40, vtop + 44), (CX + 48, vtop + 48), (CX + 52, vtop + 52)),
        ((CX + 52, vtop + 52), (CX + 40, vtop + 52), (CX + 20, vtop + 46), (CX, vtop + 46)),
    ])
    h.append(el(band, C["firuze"], TAH, 0.3))
    h.append(el(ellipse(CX, vtop + 4, 21, 3.2), C["firuze"], TAH, 0.3))
    h.append(penc(place(CX, vtop + 72, 15), C["mercan"], TAH, sw, inner=C["astar"], center=C["firuze"]))
    for sx in (-1, 1):
        h.append(yaprak(place(CX + sx * 30, vtop + 80, 16, sx * 70), C["astar"], TAH, 0.25, curve=0.1 * sx))
        h.append(el(circle(CX + sx * 22, vtop + 58, 2.2), C["mercan"], TAH, 0.25))
    for i in range(-2, 3):
        h.append(el(circle(CX + i * 6.5, vtop + 41, 1.4), C["mercan"], TAH, 0.2))
    body.append(clipped(defs, half(defs, "".join(h), fy0, fx1, fy1), field))
    # hat alanı: ağacın gövdesi önünde dilimli kartuş; dallar arkasından dolaşır
    kcy, krx, kry = fy0 + 222, 90, 120
    body.append(el(lobed_ellipse(CX, kcy, krx + 6, kry + 6, 26, 0.07), C["kobalt"], TAH, 0.45))
    for i in range(52):
        p = polar(CX, kcy, 1, -90 + i * 360 / 52)
        q = (CX + (p[0] - CX) * (krx + 3), kcy + (p[1] - kcy) * (kry + 3))
        body.append(el(circle(q[0], q[1], 0.9), C["mercan"] if i % 2 else C["firuze"]))
    body.append(hat_alani("02", lobed_ellipse(CX, kcy, krx, kry, 26, 0.07), "dilimli oval kartuş", rule=C["firuze"]))
    return doc("".join(body), defs, "Tezhip 02 - Osmanli saz yolu ve cintemani")


# ============================================================ 03 Memlük
def comp03():
    defs = Defs()
    body = []
    frame, fin = outer_frame(defs, C["lacivert"], C["altin"], C["lacivert"])
    body.append(frame)
    bw = 24
    (bx0, by0, bx1, by1), (fx0, fy0, fx1, fy1) = standard_border(fin, bw)
    ring = rect(bx0, by0, bx1, by1) + rect(bx0 + bw, by0 + bw, bx1 - bw, by1 - bw)
    s_b, _ = girih("488", CX, CY, 3.6, (bx0, by0, bx1, by1), 67.5, C["altin"], 0.55,
                   {"oct": C["altin"], "sq": C["firuze"]}, C["lacivert"], edge=TAH, ew=0.18)
    body.append(g(s_b, clip=defs.clip(ring, rule="evenodd")))
    for r_ in (rect(bx0, by0, bx1, by1), rect(bx0 + bw, by0 + bw, bx1 - bw, by1 - bw)):
        body.append(el(r_, "none", C["altin"], 1.0))
        body.append(el(r_, "none", TAH, 0.25))
    field = rect(fx0, fy0, fx1, fy1)
    s = 10.5
    sf, polys = girih("4612", CX, CY, s, (fx0, fy0, fx1, fy1), 60, C["astar"], 0.8,
                      {"dod": C["lacivert"], "hex": C["lacivert"], "sq": C["firuze"]}, C["altin"],
                      edge=TAH, ew=0.22)
    extra = []
    for kname, poly in polys:
        if kname == "dod":
            cx_ = sum(p[0] for p in poly) / 12
            cy_ = sum(p[1] for p in poly) / 12
            if dist((cx_, cy_), (CX, CY)) < 10:
                continue
            extra.append(rosette(cx_, cy_, 12, s * 0.95, C["altin"], C["lacivert"], C["altin"], 0.35, TAH, 0.12))
            extra.append(el(circle(cx_, cy_, 1.6), C["firuze"], TAH, 0.2))
    body.append(clipped(defs, sf + "".join(extra), field))
    body.append(el(field, "none", C["altin"], 1.0))
    # merkez rozet madalyonu (D12)
    R0 = 122
    med = []
    lob = lobed_ellipse(CX, CY, R0, R0, 36, 0.05)
    med.append(tig_around(lob, 72, 7, 1.7, C["lacivert"]))
    med.append(el(lob, C["altin"], TAH, 0.4))
    med.append(el(circle(CX, CY, R0 - 5), C["lacivert"], TAH, 0.35))
    for i in range(48):
        p = polar(CX, CY, R0 - 9, -90 + i * 7.5)
        med.append(el(circle(p[0], p[1], 1.5 if i % 2 else 2.1), C["altin"] if i % 2 else C["firuze"], TAH, 0.2))
    med.append(el(circle(CX, CY, R0 - 13), C["altin"], TAH, 0.35))
    # iç halka: lacivert bant üzerinde 12 küçük 12'li rozet (D12)
    med.append(el(circle(CX, CY, R0 - 16), C["lacivert"], TAH, 0.3))
    for i in range(12):
        p = polar(CX, CY, R0 - 26, -90 + i * 30)
        med.append(rosette(p[0], p[1], 12, 8.5, C["altin"], C["firuze"], C["altin"], 0.3, TAH, 0.1))
        q = polar(CX, CY, R0 - 26, -90 + i * 30 + 15)
        med.append(el(circle(q[0], q[1], 2.4), C["altin"], TAH, 0.25))
    med.append(el(circle(CX, CY, R0 - 36), C["altin"], TAH, 0.35))
    med.append(hat_alani("03", circle(CX, CY, R0 - 39), "daire", rule=C["altin_koyu"], rule_w=0.6))
    body.append("".join(med))
    return doc("".join(body), defs, "Tezhip 03 - Memluk")


# ============================================================ 04 Nasrî
def comp04():
    defs = Defs()
    body = []
    frame, fin = outer_frame(defs, C["kobalt"], C["altin"], C["zumrut"])
    body.append(frame)
    bw = 22
    (bx0, by0, bx1, by1), (fx0, fy0, fx1, fy1) = standard_border(fin, bw)

    def tile(x, u, i):
        col = C["kobalt"] if i % 2 == 0 else C["zumrut"]
        r = bw * 0.36
        out = []
        pts = []
        for k in range(16):
            pts.append(polar(x, 0, r if k % 2 == 0 else r * 0.72, -90 + k * 22.5))
        out.append(el(polygon(pts), col, TAH, 0.3))
        out.append(el(polygon([polar(x, 0, r * 0.42, -90 + k * 45) for k in range(8)]), C["altin"], TAH, 0.25))
        return "".join(out)

    def between(x, u, i):
        r = bw * 0.2
        return (el(polygon([(x, -r), (x + r, 0), (x, r), (x - r, 0)]), C["mercan"], TAH, 0.3) +
                el(circle(x, 0, r * 0.3), C["astar"], TAH, 0.2))

    def content(L):
        return sym_band_items(L, int(round(L / 22)), tile, between)

    def corner(cx, cy, w):
        return (el(rect(cx - w / 2, cy - w / 2, cx + w / 2, cy + w / 2), C["altin"]) +
                muhr(cx, cy, w * 0.38, 1.6, C["astar"], TAH, 0.3, n=8, double=False))

    body.append(frame_band(bx0, by0, bx1, by1, bw, C["astar"], content, corner, C["zumrut"], 1.0))
    field = rect(fx0, fy0, fx1, fy1)
    s = 9.0
    a = s * (1 + math.sqrt(2))

    def fills(kname, poly):
        cx_ = sum(p[0] for p in poly) / len(poly)
        cy_ = sum(p[1] for p in poly) / len(poly)
        if kname == "oct":
            i, j = round((cx_ - CX) / a), round((cy_ - CY) / a)
            return C["kobalt"] if (i + j) % 2 == 0 else C["zumrut"]
        return C["mercan"]

    sf, polys = girih("488", CX, CY, s, (fx0, fy0, fx1, fy1), 67.5, C["astar"], 2.0, fills, C["altin"],
                      edge=TAH, ew=0.35)
    extra = []
    for kname, poly in polys:
        if kname == "oct":
            cx_ = sum(p[0] for p in poly) / 8
            cy_ = sum(p[1] for p in poly) / 8
            extra.append(el(polygon([polar(cx_, cy_, s * 0.42, -90 + k * 45 + 22.5) for k in range(8)]),
                            C["altin"], TAH, 0.3))
            extra.append(el(circle(cx_, cy_, s * 0.14), C["astar"], TAH, 0.2))
    body.append(clipped(defs, sf + "".join(extra), field))
    body.append(el(field, "none", TAH, 0.5))
    # merkez: kare çerçeve (D4) içinde sekiz köşeli hâtem-i Süleymân (D8)
    H = 130
    sq_o = rect(CX - H, CY - H, CX + H, CY + H)
    sq_i = rect(CX - H + 7, CY - H + 7, CX + H - 7, CY + H - 7)
    body.append(el(sq_o, C["zumrut"], TAH, 0.5))
    # kare çerçeve bandında küçük dilimler
    body.append(el(sq_i, C["astar"], TAH, 0.5))
    s2 = 5.2
    a2 = s2 * (1 + math.sqrt(2))

    def fills2(kname, poly):
        if kname == "oct":
            cx_ = sum(p[0] for p in poly) / 8
            cy_ = sum(p[1] for p in poly) / 8
            i, j = round((cx_ - CX) / a2), round((cy_ - CY) / a2)
            return C["mercan"] if (i + j) % 2 == 0 else C["kobalt"]
        return C["zumrut"]

    m_in, _ = girih("488", CX, CY, s2, (CX - H, CY - H, CX + H, CY + H), 67.5, C["altin"], 1.0, fills2,
                    C["astar"], edge=TAH, ew=0.25)
    body.append(clipped(defs, m_in, sq_i))
    for k in range(-8, 9):
        for (x, y) in ((CX + k * 15.5, CY - H + 3.5), (CX + k * 15.5, CY + H - 3.5),
                       (CX - H + 3.5, CY + k * 15.5), (CX + H - 3.5, CY + k * 15.5)):
            body.append(el(polygon([(x, y - 2.4), (x + 2.4, y), (x, y + 2.4), (x - 2.4, y)]), C["altin"], TAH, 0.2))
    # kare köşelerinde mercan çeyrek rozetler
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = CX + sx * (H - 7), CY + sy * (H - 7)
            body.append(el(kosebent_path(x, y, 38, 38, 4, 0.14, sx=-sx, sy=-sy), C["mercan"], TAH, 0.4))
            body.append(el(kosebent_path(x, y, 24, 24, 3, 0.14, sx=-sx, sy=-sy), C["altin"], TAH, 0.3))
    # büyük sekiz kollu yıldız zemin (zellige)
    R8 = 122
    star = []
    for k in range(16):
        star.append(polar(CX, CY, R8 if k % 2 == 0 else R8 * 0.765, -90 + k * 22.5))
    body.append(el(polygon(star), C["kobalt"], TAH, 0.5))
    # kollar içinde mercan damlalar
    for k in range(8):
        p = polar(CX, CY, R8 * 0.85, -90 + k * 45)
        body.append(el(polygon([polar(p[0], p[1], 6.5, -90 + k * 45 + j * 90) for j in range(4)]), C["mercan"], TAH, 0.3))
    rm = R8 * 0.93
    # hat alanı: iki karenin kesişiminden doğan düzgün sekizgen
    r_oct = (rm * math.cos(math.radians(45)) - 3.2) / math.cos(math.radians(22.5))
    body.append(hat_alani("04", polygon([polar(CX, CY, r_oct, -90 + 22.5 + k * 45) for k in range(8)]),
                          "düzgün sekizgen (hâtem içi)", rule=C["zumrut"], rule_w=1.0))
    body.append(muhr(CX, CY, rm, 5.0, C["astar"], TAH, 0.45, n=8, rot=-90))
    return doc("".join(body), defs, "Tezhip 04 - Nasri Endulus")


# ============================================================ 05 Timurlu
def comp05():
    defs = Defs()
    body = []
    frame, fin = outer_frame(defs, C["lacivert"], C["altin"], C["lacivert"])
    body.append(frame)
    bw = 20
    (bx0, by0, bx1, by1), (fx0, fy0, fx1, fy1) = standard_border(fin, bw)
    pal_b = {"w": bw, "stem": C["lacivert"], "f1": C["lacivert"], "f2": C["firuze"], "cal": C["lacivert"],
             "p1": C["firuze"], "p2": C["astar"], "l1": C["lacivert"], "r1": C["firuze"]}
    body.append(frame_band(bx0, by0, bx1, by1, bw, C["altin"], band_content(pal_b, k_per=1.5, fscale=0.6),
                           corner_penc(C["lacivert"], C["firuze"], C["altin"]), TAH, 0.6))
    field = rect(fx0, fy0, fx1, fy1)
    body.append(el(field, C["lacivert"]))
    # mihrabiye (sivri kemer)
    ax0, ax1 = fx0 + 9, fx1 - 9
    spring, apex, bot = fy0 + 150, fy0 + 14, fy1 - 56
    xw = ax1 - CX

    def arch(inset):
        x1 = ax1 - inset
        return sym_bez([
            ((CX, apex + inset * 1.25), (CX + xw * 0.30, apex + 38 + inset), (x1, spring - 90 + inset * 0.3), (x1, spring)),
            ((x1, spring), (x1, bot - inset)),
            ((x1, bot - inset), (CX, bot - inset)),
        ])

    A0, A1, A2 = arch(0), arch(5.5), arch(7.5)
    # köşelik (kemer dışı) zemini: altın üzerine lacivert ince helezon
    spand = rect(fx0, fy0, fx1, bot) + A0
    pal_sp = {"stem": C["lacivert"], "f1": C["lacivert"], "f2": C["firuze"], "cal": C["lacivert"], "p1": C["firuze"],
              "p2": C["lacivert"], "g1": C["lacivert"], "gs": C["firuze"], "gi": C["astar"], "l1": C["lacivert"],
              "r1": C["firuze"], "c": C["astar"]}
    sp_fill = el(rect(fx0, fy0, fx1, bot), C["altin"]) + scroll((CX, fy0, fx1, bot), 16, pal_sp, sw_stem=0.35, sw=0.16, seed=3)
    body.append(g(half(defs, sp_fill, fy0, fx1, bot), clip=defs.clip(spand, rule="evenodd")))
    body.append(el(A0, C["altin"], TAH, 0.4))
    body.append(el(A1, C["firuze"], TAH, 0.3))
    body.append(el(A2, C["lacivert"], TAH, 0.3))
    # kemer içi: çok ince ölçekli hatâyî + bulut
    pal_in = {"stem": C["altin"], "f1": C["altin"], "f2": C["firuze"], "cal": C["altin"], "p1": C["firuze"],
              "p2": C["altin"], "g1": C["altin"], "gs": C["firuze"], "gi": C["astar"], "l1": C["altin"],
              "r1": C["altin"], "c": C["astar"]}
    inner = scroll((CX, fy0, fx1, bot), 15, pal_in, sw_stem=0.32, sw=0.15, seed=5, fscale=0.42)
    clouds = []
    j = 0
    y = fy0 + 40
    while y < bot:
        x = CX + (22 if j % 2 else 0)
        while x < fx1 + 20:
            col = C["firuze"] if (j + int((x - CX) / 44)) % 2 else C["altin"]
            clouds.append(bulut(place(x, y, 18, 15 if j % 2 else -15), col, TAH, 0.18))
            x += 48
        y += 34
        j += 1
    body.append(clipped(defs, half(defs, inner + "".join(clouds), fy0, fx1, bot), A2))
    # hat alanı: iç içe kemer; dış kuşak ince hatâyî-bulut dolgulu kalır
    body.append(el(arch(24), C["altin"], TAH, 0.35))
    body.append(el(arch(25.5), C["firuze"], TAH, 0.25))
    body.append(hat_alani("05", arch(27.5), "sivri kemerli pano (mihrabiye)", rule=C["altin"], rule_w=0.8))
    body.append(penc(place(CX, apex + 16, 6), C["firuze"], TAH, 0.22, inner=C["astar"], center=C["altin"]))
    # alt kartuş: bulut şeridi
    cy2 = (bot + fy1) / 2
    body.append(el(rect(fx0 + 9, bot + 5, fx1 - 9, fy1 - 5), C["altin"], TAH, 0.4))
    cart = lobed_ellipse(CX, cy2, 118, 15, 26, 0.12)
    body.append(el(cart, C["lacivert"], TAH, 0.4))
    cl = []
    for i in range(3):
        x = CX + 18 + i * 34
        cl.append(bulut(place(x, cy2, 30, 0), C["altin"], TAH, 0.22))
    cl.append(penc(place(CX, cy2, 7.5), C["firuze"], TAH, 0.22, inner=C["astar"]))
    body.append(clipped(defs, half(defs, "".join(cl), bot, fx1, fy1), cart))
    for sx in (-1, 1):
        body.append(penc(place(CX + sx * 133, cy2, 8), C["lacivert"], TAH, 0.22, inner=C["firuze"], center=C["astar"]))
    return doc("".join(body), defs, "Tezhip 05 - Timurlu Herat")


# ============================================================ 06 Safevî
def comp06():
    defs = Defs()
    defs.add(f'<radialGradient id="varak" cx="{num(CX)}" cy="{num(CY)}" r="330" gradientUnits="userSpaceOnUse">'
             f'<stop offset="0" stop-color="#D2AC33"/><stop offset="1" stop-color="{C["altin"]}"/></radialGradient>')
    body = []
    frame, fin = outer_frame(defs, C["lacivert"], C["altin"], C["lacivert"])
    body.append(frame)
    bw = 30
    (bx0, by0, bx1, by1), (fx0, fy0, fx1, fy1) = standard_border(fin, bw)

    def content(L):
        Lc, Lr = 48.0, 20.0
        nc = max(1, int(round((L + Lr) / (Lc + Lr + 6))))
        unit = L / (nc * (Lc + Lr) - Lr) if nc > 0 else 1
        out = []
        x = 0
        for i in range(nc):
            lc = Lc * unit
            cx_ = x + lc / 2
            cart = lobed_ellipse(cx_, 0, lc / 2 - 1.5, bw * 0.36, 18, 0.10)
            out.append(el(cart, C["altin"], TAH, 0.35))
            out.append(el(lobed_ellipse(cx_, 0, lc / 2 - 4, bw * 0.36 - 2.5, 18, 0.10), "none", C["altin_koyu"], 0.3))
            out.append(penc(place(cx_, 0, 4.6), C["mercan"], TAH, 0.22, inner=C["astar"], center=C["firuze"]))
            for sx in (-1, 1):
                out.append(hatayi(place(cx_ + sx * lc * 0.26, 0, bw * 0.40, sx * 90), C["lacivert"], TAH, 0.22,
                                  inner=C["firuze"], calyx=C["lacivert"]))
                out.append(yaprak(place(cx_ + sx * lc * 0.07, -bw * 0.12, 6, sx * 60, flip=sx > 0), C["zumrut"], TAH, 0.2))
                out.append(yaprak(place(cx_ + sx * lc * 0.07, bw * 0.12, 6, 180 - sx * 60, flip=sx < 0), C["zumrut"], TAH, 0.2))
            x += lc
            if i < nc - 1:
                lr = Lr * unit
                rx_ = x + lr / 2
                out.append(el(circle(rx_, 0, bw * 0.26), C["firuze"], TAH, 0.35))
                out.append(penc(place(rx_, 0, bw * 0.19), C["mercan"], TAH, 0.22, inner=C["altin"], center=C["lacivert"]))
                x += lr
        return "".join(out)

    body.append(frame_band(bx0, by0, bx1, by1, bw, C["lacivert"], content,
                           corner_penc(C["altin"], C["mercan"], C["lacivert"]), C["altin"], 0.9))
    field = rect(fx0, fy0, fx1, fy1)
    body.append(el(field, "url(#varak)"))
    pal_g = {"stem": C["altin_koyu"], "f1": C["lacivert"], "f2": C["firuze"], "cal": C["zumrut"], "p1": C["mercan"],
             "p2": C["astar"], "g1": C["mercan"], "gs": C["zumrut"], "gi": C["astar"], "l1": C["zumrut"],
             "r1": C["lacivert"], "c": C["astar"]}
    gf = scroll((CX, fy0, fx1, CY), 25, pal_g, sw_stem=0.55, sw=0.22, seed=4, phase=(0, 3))
    body.append(clipped(defs, quad(defs, gf, fx0, fy0, fx1, fy1), field))
    # köşebentler: çeyrek dairesel, lacivert
    kr = 96
    kos = kosebent_path(fx1, fy0, kr, kr, 6, 0.12, sx=-1, sy=1)
    kos_in = kosebent_path(fx1, fy0, kr - 4, kr - 4, 6, 0.12, sx=-1, sy=1)
    pal_l = {"stem": C["altin"], "f1": C["altin"], "f2": C["firuze"], "cal": C["altin"], "p1": C["firuze"],
             "p2": C["altin"], "g1": C["altin"], "gs": C["firuze"], "gi": C["mercan"], "l1": C["altin"],
             "r1": C["firuze"], "c": C["mercan"]}
    kq = [el(kos, C["altin_koyu"], TAH, 0.4), el(kos_in, C["lacivert"], TAH, 0.3)]
    kq.append(clipped(defs, scroll((fx1 - kr, fy0, fx1, fy0 + kr), 21, pal_l, sw_stem=0.5, sw=0.2, seed=6, phase=(3, 2)), kos_in))
    body.append(clipped(defs, sym_d2("".join(kq)), field))
    # şemse (toranj): uzun dilimli oval, iki uçta tepelik ve küçük sarkıt
    rx, ry = 84, 152
    sem = lobed_ellipse(CX, CY, rx, ry, 30, 0.06)
    sem_in = lobed_ellipse(CX, CY, rx - 4.5, ry - 4.5, 30, 0.06)
    for up in (True, False):
        sg = -1 if up else 1
        body.append(el(salbek_path(CX, CY + sg * (ry + 12), 30, 26, up=up), C["lacivert"], TAH, 0.4))
        body.append(el(salbek_path(CX, CY + sg * (ry + 14), 21, 18, up=up), C["mercan"], TAH, 0.3))
        body.append(el(semse_finial(CX, CY + sg * (ry - 2), 22, 18, up=up), C["lacivert"], TAH, 0.4))
    body.append(el(sem, C["altin_koyu"], TAH, 0.45))
    body.append(el(sem_in, C["lacivert"], TAH, 0.3))
    sf = scroll((CX, CY - ry, CX + rx, CY), 22, pal_l, sw_stem=0.55, sw=0.2, seed=7, phase=(0, 2))
    body.append(clipped(defs, quad(defs, sf, CX - rx, CY - ry, CX + rx, CY + ry), sem_in))
    # hat alanı: şemse içinde altın cetvelli boş dilimli oval
    body.append(el(lobed_ellipse(CX, CY, rx - 23, ry - 27, 20, 0.05), C["altin"], TAH, 0.4))
    body.append(el(lobed_ellipse(CX, CY, rx - 25, ry - 29, 20, 0.05), C["mercan"], TAH, 0.25))
    body.append(hat_alani("06", lobed_ellipse(CX, CY, rx - 27, ry - 31, 20, 0.05), "dilimli oval (turunç içi)",
                          rule=C["altin"], rule_w=0.8))
    return doc("".join(body), defs, "Tezhip 06 - Safevi")


# ============================================================ 07 Sentez
def comp07():
    defs = Defs()
    body = []
    frame, fin = outer_frame(defs, C["kobalt"], C["altin"], C["lacivert"])
    body.append(frame)
    bw = 24
    (bx0, by0, bx1, by1), (fx0, fy0, fx1, fy1) = standard_border(fin, bw)

    def item(x, u, i):
        return bulut(place(x, 0, u * 0.92, 0), C["firuze"] if i % 2 == 0 else C["altin"], TAH, 0.22)

    def between(x, u, i):
        return penc(place(x, 0, bw * 0.18), C["mercan"], TAH, 0.22, inner=C["astar"], center=C["altin"])

    def content(L):
        return sym_band_items(L, int(round(L / 34)), item, between)

    body.append(frame_band(bx0, by0, bx1, by1, bw, C["lacivert"], content,
                           corner_penc(C["mercan"], C["altin"], C["lacivert"]), C["altin"], 0.9))
    field = rect(fx0, fy0, fx1, fy1)
    s = 8.0
    sf, polys = girih("488", CX, CY, s, (fx0, fy0, fx1, fy1), 67.5, C["altin"], 0.9,
                      {"oct": C["kobalt"], "sq": C["firuze"]}, C["lacivert"], edge=TAH, ew=0.22)
    body.append(clipped(defs, sf, field))
    # köşebent: Osmanlı hatâyî (astar zemin)
    kw, kh = 100, 112
    kos = kosebent_path(fx1, fy0, kw, kh, 6, 0.12, sx=-1, sy=1)
    kos_in = kosebent_path(fx1, fy0, kw - 4, kh - 4, 6, 0.12, sx=-1, sy=1)
    pal_o = {"stem": C["zumrut"], "f1": C["mercan"], "f2": C["kobalt"], "cal": C["zumrut"], "p1": C["kobalt"],
             "p2": C["firuze"], "g1": C["mercan"], "gs": C["zumrut"], "gi": C["astar"], "l1": C["zumrut"],
             "r1": C["kobalt"], "c": C["altin"]}
    kq = [el(kos, C["altin"], TAH, 0.4), el(kos_in, C["astar"], TAH, 0.3)]
    kq.append(clipped(defs, scroll((fx1 - kw, fy0, fx1, fy0 + kh), 24, pal_o, sw_stem=0.6, sw=0.22, seed=8, phase=(5, 4)), kos_in))
    body.append(clipped(defs, sym_d2("".join(kq)), field))
    # merkez madalyon
    R0 = 138
    lob = lobed_ellipse(CX, CY, R0, R0, 32, 0.05)
    body.append(tig_around(lob, 96, 7, 1.7, C["altin"]))
    body.append(el(lob, C["altin"], TAH, 0.45))
    body.append(el(circle(CX, CY, R0 - 5), C["lacivert"], TAH, 0.35))
    # 8 kollu rozet halkası (D8) + Safevî bulutları
    ring = []
    rr = 104
    ring.append(g(rosette(CX + rr, CY, 8, 25, C["altin"], C["firuze"], C["astar"], 0.8, TAH, 0.22, rot=0, ground=None)))
    ring.append(el(circle(CX + rr, CY, 4), C["mercan"], TAH, 0.3))
    p = polar(CX, CY, 122, 15)
    ring.append(bulut(place(p[0], p[1], 22, 15 + 90), C["mercan"], TAH, 0.22))
    p = polar(CX, CY, 84, 13)
    ring.append(bulut(place(p[0], p[1], 18, 13 + 90), C["firuze"], TAH, 0.2))
    body.append(rotate_copies("".join(ring), 8, CX, CY, mirror=True))
    body.append(el(circle(CX, CY, 76), C["altin"], TAH, 0.4))
    body.append(hat_alani("07", circle(CX, CY, 72), "daire", rule=C["firuze"], rule_w=1.0))
    # mühr-i Süleyman: madalyonun üstünde ve altında geçmeli hexagram madalyonları
    ym = CY - R0 - 30
    md = [el(lobed_ellipse(CX, ym, 27, 27, 12, 0.10), C["altin"], TAH, 0.4),
          el(circle(CX, ym, 23), C["astar"], TAH, 0.3)]
    for k in range(6):
        a = -90 + k * 60
        p = polar(CX, ym, 13.5, a)
        md.append(hatayi(place(p[0], p[1], 7.5, a + 90), C["mercan"], TAH, 0.15, inner=C["kobalt"],
                         calyx=C["zumrut"], center=C["altin"]))
    md.append(muhr(CX, ym, 21, 2.2, C["altin"], TAH, 0.28, n=6))
    md.append(penc(place(CX, ym, 5.5), C["mercan"], TAH, 0.2, n=6, inner=C["astar"], center=C["kobalt"]))
    md = "".join(md)
    body.append(md + mirror_y(md, CY))
    return doc("".join(body), defs, "Tezhip 07 - Sentez")


def rot_about(path, deg, cx=CX, cy=CY):
    return path.tf(mat(T(cx, cy), mat(R(deg), T(-cx, -cy))))


def star_medallion(cx, cy, r, ground, line, accent):
    """{8/3} geçmeli yıldız madalyonu (dilimli çerçeve içinde)."""
    out = [el(lobed_ellipse(cx, cy, r, r, 8, 0.16), C["altin"], TAH, 0.4),
           el(lobed_ellipse(cx, cy, r - 2.6, r - 2.6, 8, 0.16), ground, TAH, 0.3)]
    pts = [polar(cx, cy, r * 0.80, -90 + 22.5 + k * 45) for k in range(8)]
    segs = [(pts[k], pts[(k + 3) % 8]) for k in range(8)]
    star = []
    for k in range(16):
        star.append(polar(cx, cy, r * 0.80 if k % 2 == 0 else r * 0.80 * 0.54, -90 + 22.5 + k * 22.5))
    out.append(el(polygon(star), accent, None))
    out.append(interlace(segs, r * 0.07, line, TAH, r * 0.018, weave(segs)))
    out.append(rosette(cx, cy, 8, r * 0.30, C["altin"], C["mercan"], C["altin_koyu"], 0.2, TAH, 0.08, rot=-90 + 22.5))
    return "".join(out)


def pendant(x, y0, L, up=False):
    """Sarkan zincirli salbek (ince altın tel, boncuklar, lacivert badem
    damla ve uçta tığ). up=True ise alttan yukarı uzanır."""
    s = -1 if up else 1
    out = [f'<path d="M{num(x)},{num(y0)}L{num(x)},{num(y0 + s * L)}" stroke="{C["altin_koyu"]}" stroke-width="0.45"/>']
    for f in (0.18, 0.42):
        out.append(el(circle(x, y0 + s * L * f, 1.3), C["altin"], TAH, 0.2))
    yc = y0 + s * L * 0.68
    drop = lobed_ellipse(x, yc, 6.5, 10.5, 10, 0.10)
    out.append(el(drop, C["altin"], TAH, 0.3))
    out.append(el(lobed_ellipse(x, yc, 4.6, 8.4, 10, 0.10), C["lacivert"], TAH, 0.25))
    out.append(penc(place(x, yc, 2.6), C["mercan"], TAH, 0.12, inner=C["astar"], center=C["altin"]))
    out.append(el(polygon([(x, yc - 13.5), (x + 2.3, yc - 11), (x, yc - 8.5), (x - 2.3, yc - 11)]) if not up else
                  polygon([(x, yc + 13.5), (x + 2.3, yc + 11), (x, yc + 8.5), (x - 2.3, yc + 11)]), C["kobalt"], TAH, 0.2))
    out.append(el(tig_path((x, yc + s * 10.4), (0, s), L * 0.30, 2.2), C["lacivert"]))
    # tele bağlı ince altın filizler
    for sx in (-1, 1):
        yy = y0 + s * L * 0.30
        out.append(yaprak(place(x + sx * 1.0, yy, 6.5, sx * 55 + (180 if up else 0), flip=sx < 0), C["altin"], C["altin_koyu"], 0.15))
    return "".join(out)


# ============================================================ 08 Kitap kapağı / levha (boş merkezli halka)
def comp08():
    defs = Defs()
    body = []
    frame, fin = outer_frame(defs, C["lacivert"], C["altin"], C["lacivert"])
    body.append(frame)
    bw = 20
    (bx0, by0, bx1, by1), (fx0, fy0, fx1, fy1) = standard_border(fin, bw, gap=6)
    pal_b = {"w": bw, "stem": C["altin"], "f1": C["mercan"], "f2": C["firuze"], "cal": C["altin"],
             "p1": C["astar"], "p2": C["mercan"], "l1": C["altin"], "r1": C["firuze"]}
    body.append(frame_band(bx0, by0, bx1, by1, bw, C["kobalt"], band_content(pal_b, k_per=1.3, fscale=0.58),
                           corner_penc(C["altin"], C["firuze"], C["kobalt"]), C["altin"], 1.0))
    # bordür üzerinde kenar ortası ve köşe madalyonları (firuze, dilimli)
    def bmed(x, y, r):
        return (el(lobed_ellipse(x, y, r, r, 10, 0.14), C["altin"], TAH, 0.4) +
                el(lobed_ellipse(x, y, r - 2.4, r - 2.4, 10, 0.14), C["firuze"], TAH, 0.3) +
                penc(place(x, y, r * 0.48), C["kobalt"], TAH, 0.2, inner=C["astar"], center=C["mercan"]))
    bm = [bmed(CX, by0 + bw / 2, 15), bmed(bx0 + bw / 2, CY, 15), bmed(bx0 + bw / 2, by0 + bw / 2, 15)]
    body.append(sym_d2("".join(bm)))
    field = rect(fx0, fy0, fx1, fy1)
    body.append(el(rect(fx0 - 2.5, fy0 - 2.5, fx1 + 2.5, fy1 + 2.5), "none", C["altin"], 1.4))
    body.append(el(rect(fx0 - 2.5, fy0 - 2.5, fx1 + 2.5, fy1 + 2.5), "none", TAH, 0.25))
    # köşebentler: kobalt zemin, altın helezon + mercan hatâyî
    kw, kh = 82, 92
    kos = kosebent_path(fx1, fy0, kw, kh, 6, 0.12, sx=-1, sy=1)
    kos_in = kosebent_path(fx1, fy0, kw - 3, kh - 3, 6, 0.12, sx=-1, sy=1)
    pal_k = {"stem": C["altin"], "f1": C["mercan"], "f2": C["firuze"], "cal": C["altin"], "p1": C["astar"],
             "p2": C["mercan"], "g1": C["mercan"], "gs": C["altin"], "gi": C["firuze"], "l1": C["altin"],
             "r1": C["firuze"], "c": C["altin"]}
    kq = [tig_around(kos, 70, 5.0, 1.4, C["kobalt"], keep=lambda p: p[0] < fx1 - 2 and p[1] > fy0 + 2),
          el(kos, C["kobalt"], C["altin"], 2.0)]
    kq.append(clipped(defs, scroll((fx1 - kw, fy0, fx1, fy0 + kh), 24, pal_k, sw_stem=0.55, sw=0.22, seed=9,
                                   phase=(4, 5)), kos_in))
    kq.append(el(kos, "none", TAH, 0.3))
    body.append(clipped(defs, sym_d2("".join(kq)), field))
    # sarkan zincirli salbekler (üstten aşağı, alttan yukarı)
    pend = []
    for (dx, L) in ((60, 68),):
        pend.append(pendant(CX + dx, fy0, L))
    pend.append(pendant(fx1 - 10, fy0 + kh + 4, 60))
    pend.append(pendant(fx1 - 34, fy0 + kh - 14, 52))
    pd = "".join(pend)
    pd = pd + mirror_x(pd, CX)
    body.append(clipped(defs, pd + mirror_y(pd, CY), field))
    # halka madalyon
    Ro, Ri = 118, 86
    # dört eksende dilimli çıkıntılar (salbek-tepelik) ve çaprazlarda firuze madalyonlar
    pal_m = {"stem": C["altin"], "f1": C["mercan"], "f2": C["firuze"], "cal": C["altin"], "p1": C["astar"],
             "p2": C["mercan"], "g1": C["mercan"], "gs": C["altin"], "gi": C["astar"], "l1": C["altin"],
             "r1": C["firuze"], "c": C["altin"]}
    lobes = []
    # dikey eksende uzun, yatay eksende kısa çıkıntı (dikey sayfa oranı; D2)
    lh = {0: 62, 180: 62, 90: 34, 270: 34}
    for a in (0, 90, 180, 270):
        lobes.append(rot_about(salbek_path(CX, CY - Ro + 16, 96 if lh[a] > 40 else 78, lh[a], up=True), a))
    for a in (45, 135, 225, 315):
        q = polar(CX, CY, Ro + 2, a - 90)
        body.append(el(lobed_ellipse(q[0], q[1], 19, 19, 12, 0.14), C["altin"], TAH, 0.4))
        body.append(el(lobed_ellipse(q[0], q[1], 16.5, 16.5, 12, 0.14), C["firuze"], TAH, 0.3))
        body.append(hatayi(place(q[0], q[1] + 1, 20, 0 if a in (45, 315) else 180), C["kobalt"], TAH, 0.2,
                           inner=C["astar"], calyx=C["altin"], center=C["mercan"]))
    for a, lp in zip((0, 90, 180, 270), lobes):
        r_tip = Ro - 16 + lh[a]
        u = polar(0, 0, 1, a - 90)
        body.append(el(tig_path(polar(CX, CY, r_tip - 2, a - 90), u, 12 if lh[a] > 40 else 8, 3.6), C["kobalt"], TAH, 0.25))
        body.append(el(lp, C["kobalt"], C["altin"], 2.0))
    ring = circle(CX, CY, Ro)
    body.append(el(ring, C["kobalt"], C["altin"], 2.2))
    mfill = scroll((CX, CY - Ro - 50, CX + Ro + 50, CY), 23, pal_m, sw_stem=0.55, sw=0.22, seed=10, phase=(0, 2))
    mq = quad(defs, mfill, CX - Ro - 50, CY - Ro - 50, CX + Ro + 50, CY + Ro + 50)
    for lp in lobes:
        inner_lp = lp
        body.append(clipped(defs, mq, inner_lp))
    body.append(clipped(defs, mq, circle(CX, CY, Ro - 1.5)))
    for lp in lobes:
        body.append(el(lp, "none", TAH, 0.3))
    body.append(el(ring, "none", TAH, 0.3))
    # dört eksende yıldız madalyonları (halkanın üzerinde)
    rm = (Ro + Ri) / 2
    for a in (0, 90, 180, 270):
        q = polar(CX, CY, rm, a - 90)
        body.append(star_medallion(q[0], q[1], 21, C["lacivert"], C["altin"], C["kobalt"]))
    body.append(el(circle(CX, CY, Ri + 2.5), C["altin"], TAH, 0.35))
    body.append(hat_alani("08", circle(CX, CY, Ri), "daire (halka madalyon içi)", rule=C["altin_koyu"], rule_w=0.6))
    return doc("".join(body), defs, "Tezhip 08 - Bos merkezli halka madalyon")


COMPS.update({"02": comp02, "03": comp03, "04": comp04, "05": comp05, "06": comp06, "07": comp07, "08": comp08})
