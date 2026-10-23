"""Tezhip motif kütüphanesi (SVG, birim: mm).

Bütün organik motifler kübik Bézier eğrileriyle kurulur; her motif
dolgu rengi (fill), tahrir rengi (stroke) ve tahrir kalınlığı (sw, mm)
parametrelerini alır. Motifler birim koordinatlarda tasarlanır ve bir
afin yerleştirme matrisiyle (place) dünyaya taşınır; nokta dönüşümü
Python'da yapıldığından tahrir kalınlığı ölçekten bağımsızdır.

Koordinat kuralı: SVG ekseni (y aşağı). Motiflerin "yukarı" yönü -y'dir.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "palette.json"), encoding="utf-8") as _fh:
    PALETTE = json.load(_fh)
C = {k: v["hex"] for k, v in PALETTE["colors"].items()}

PAGE_W, PAGE_H, MARGIN = 500.0, 700.0, 50.0
AREA = (MARGIN, MARGIN, PAGE_W - MARGIN, PAGE_H - MARGIN)  # x0, y0, x1, y1
CX, CY = PAGE_W / 2, PAGE_H / 2

K = 0.5522847498  # çeyrek daire Bézier sabiti


# ---------------------------------------------------------------- geometri
def num(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def mat(A, B):
    """A∘B : önce B, sonra A uygulanır."""
    a1, b1, c1, d1, e1, f1 = A
    a2, b2, c2, d2, e2, f2 = B
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def T(x, y):
    return (1, 0, 0, 1, x, y)


def R(deg):
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return (c, s, -s, c, 0, 0)


def S(sx, sy=None):
    return (sx, 0, 0, sx if sy is None else sy, 0, 0)


ID = (1, 0, 0, 1, 0, 0)


def place(x, y, s=1.0, rot=0.0, flip=False, sy=None):
    """Birim motifi (x,y) noktasına s ölçeğinde, rot derece döndürerek
    yerleştir. flip=True motifi kendi dikey ekseninde aynalar."""
    sx = -s if flip else s
    return mat(T(x, y), mat(R(rot), S(sx, s if sy is None else sy)))


def ap(A, p):
    a, b, c, d, e, f = A
    return (a * p[0] + c * p[1] + e, b * p[0] + d * p[1] + f)


def lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def dist(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


class Path:
    """M/L/C/Z komutlarından oluşan yol; afin dönüşüm altında kapalı."""

    def __init__(self, segs=None):
        self.segs = list(segs or [])

    def M(self, p):
        self.segs.append(("M", [tuple(p)]))
        return self

    def L(self, p):
        self.segs.append(("L", [tuple(p)]))
        return self

    def C(self, p1, p2, p3):
        self.segs.append(("C", [tuple(p1), tuple(p2), tuple(p3)]))
        return self

    def Z(self):
        self.segs.append(("Z", []))
        return self

    def tf(self, A):
        return Path([(c, [ap(A, p) for p in pts]) for c, pts in self.segs])

    def __add__(self, other):
        return Path(self.segs + other.segs)

    def d(self):
        out = []
        for c, pts in self.segs:
            out.append(c + " ".join(f"{num(x)},{num(y)}" for x, y in pts))
        return "".join(out)

    def points(self):
        return [p for _, pts in self.segs for p in pts]


def bez(*pts):
    """bez(p0, p1, p2, p3, p4, p5, p6, ...) -> M p0 C p1 p2 p3 C p4 p5 p6 ..."""
    p = Path().M(pts[0])
    for i in range(1, len(pts) - 2, 3):
        p.C(pts[i], pts[i + 1], pts[i + 2])
    return p


def smooth(pts, closed=False, tension=1.0):
    """Catmull-Rom noktalarını kübik Bézier'e çevirir."""
    n = len(pts)
    path = Path().M(pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        k = tension / 6.0
        c1 = (p1[0] + (p2[0] - p0[0]) * k, p1[1] + (p2[1] - p0[1]) * k)
        c2 = (p2[0] - (p3[0] - p1[0]) * k, p2[1] - (p3[1] - p1[1]) * k)
        path.C(c1, c2, p2)
    if closed:
        path.Z()
    return path


def circle(cx, cy, r):
    k = K * r
    return (Path().M((cx + r, cy))
            .C((cx + r, cy + k), (cx + k, cy + r), (cx, cy + r))
            .C((cx - k, cy + r), (cx - r, cy + k), (cx - r, cy))
            .C((cx - r, cy - k), (cx - k, cy - r), (cx, cy - r))
            .C((cx + k, cy - r), (cx + r, cy - k), (cx + r, cy)).Z())


def ellipse(cx, cy, rx, ry):
    return circle(0, 0, 1).tf(mat(T(cx, cy), S(rx, ry)))


def polygon(pts):
    p = Path().M(pts[0])
    for q in pts[1:]:
        p.L(q)
    return p.Z()


def rect(x0, y0, x1, y1):
    return polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def cubic_pt(p0, p1, p2, p3, t):
    u = 1 - t
    return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])


def cubic_tan(p0, p1, p2, p3, t):
    u = 1 - t
    dx = 3 * u * u * (p1[0] - p0[0]) + 6 * u * t * (p2[0] - p1[0]) + 3 * t * t * (p3[0] - p2[0])
    dy = 3 * u * u * (p1[1] - p0[1]) + 6 * u * t * (p2[1] - p1[1]) + 3 * t * t * (p3[1] - p2[1])
    L = math.hypot(dx, dy) or 1.0
    return (dx / L, dy / L)


# ---------------------------------------------------------------- SVG yazımı
def el(path, fill="none", stroke=None, sw=0.3, extra=""):
    s = f'<path d="{path.d()}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{num(sw)}" stroke-linejoin="round" stroke-linecap="round"'
    return s + extra + "/>"


def g(content, transform=None, clip=None, extra=""):
    attrs = ""
    if transform:
        attrs += f' transform="{transform}"'
    if clip:
        attrs += f' clip-path="url(#{clip})"'
    body = "".join(content) if isinstance(content, (list, tuple)) else content
    return f"<g{attrs}{extra}>{body}</g>"


class Defs:
    """Belge düzeyinde clipPath ve gradyan tanımlarını toplar."""

    def __init__(self):
        self.items = []
        self.n = 0

    def clip(self, path, prefix="c", rule=None):
        self.n += 1
        cid = f"{prefix}{self.n}"
        r = f' clip-rule="{rule}"' if rule else ""
        self.items.append(f'<clipPath id="{cid}"><path d="{path.d()}"{r}/></clipPath>')
        return cid

    def add(self, s):
        self.items.append(s)

    def svg(self):
        return "<defs>" + "".join(self.items) + "</defs>"


def mirror_x(content, ax):
    """Dikey eksende (x = ax) ayna kopyası."""
    return g(content, transform=f"matrix(-1,0,0,1,{num(2 * ax)},0)")


def mirror_y(content, ay):
    return g(content, transform=f"matrix(1,0,0,-1,0,{num(2 * ay)})")


def sym_v(content, ax=CX):
    """Dikey eksende ayna simetrisi: içerik + aynası."""
    c = "".join(content) if isinstance(content, (list, tuple)) else content
    return c + mirror_x(c, ax)


def sym_d2(content, ax=CX, ay=CY):
    c = sym_v(content, ax)
    return c + mirror_y(c, ay)


def rotate_copies(content, n, cx, cy, mirror=True):
    """Dn simetrisi: içerik n kez döndürülür; mirror=True ise ayrıca
    0° ekseninde aynalanır (içerik bir temel bölgeye ait olmalıdır)."""
    c = "".join(content) if isinstance(content, (list, tuple)) else content
    if mirror:
        c = c + g(c, transform=f"matrix(1,0,0,-1,0,{num(2 * cy)})")
    out = []
    for i in range(n):
        out.append(g(c, transform=f"rotate({num(360.0 * i / n)},{num(cx)},{num(cy)})"))
    return "".join(out)


# ---------------------------------------------------------------- yardımcı
def ribbon(spine, widths, n=40, tip0=True, tip1=True, serrate=None, teeth=0,
           tooth_depth=0.0, lobes=0, lobe_amp=0.0):
    """Bir omurga Bézier eğrisi (p0..p3) boyunca kalınlık profilli kapalı
    şerit/yaprak yolu üretir (Catmull-Rom -> Bézier).
    widths(t) -> yarı kalınlık; serrate in (None,'L','R','B') tırtıl yönü."""
    p0, p1, p2, p3 = spine
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        c = cubic_pt(p0, p1, p2, p3, t)
        tx, ty = cubic_tan(p0, p1, p2, p3, t)
        nx, ny = -ty, tx
        w = widths(t)
        wl = wr = w
        if teeth and 0.08 < t < 0.92:
            saw = (t * teeth) % 1.0
            dent = tooth_depth * w * (saw ** 1.6)
            if serrate in ("L", "B"):
                wl = w - dent
            if serrate in ("R", "B"):
                wr = w - dent
        if lobes:
            bump = lobe_amp * abs(math.sin(math.pi * t * lobes))
            wl += bump * w
        left.append((c[0] + nx * wl, c[1] + ny * wl))
        right.append((c[0] - nx * wr, c[1] - ny * wr))
    pts = left + right[::-1]
    # uçlarda tekrar eden noktaları ayıkla
    clean = [pts[0]]
    for q in pts[1:]:
        if dist(q, clean[-1]) > 1e-4:
            clean.append(q)
    return smooth(clean, closed=True, tension=0.9)


def spine_pts(spine, n):
    return [cubic_pt(*spine, i / n) for i in range(n + 1)]


# ================================================================ MOTİFLER
# Her motif fonksiyonu (A, fill, stroke, sw, ...) alır ve SVG parçası döndürür.

# ---- Rûmî ----------------------------------------------------------------
def _rumi_unit():
    """Tek rûmî: taban (0,0), gövde +x yönünde, uç -y (yukarı) kıvrılır.
    Dış sırt düz akar; iç kenarda bir tırnak (çentik) ikinci ucu doğurur."""
    return bez(
        (0.0, 0.10),
        (0.30, 0.16), (0.70, 0.10), (0.90, -0.14),   # dış sırt
        (1.02, -0.30), (0.98, -0.52), (0.80, -0.66),  # baş ucuna
        (0.86, -0.50), (0.80, -0.36), (0.62, -0.30),  # uçtan tırnağa
        (0.62, -0.44), (0.54, -0.54), (0.40, -0.58),  # ikinci uç (tırnak)
        (0.46, -0.40), (0.30, -0.14), (0.0, -0.10),   # iç kenar tabana
    ).Z()


def _rumi_eye():
    """Rûmînin içindeki ince iç tahrir (göz) çizgisi."""
    return bez((0.12, 0.0), (0.36, 0.04), (0.66, -0.02), (0.80, -0.26))


def rumi(A, fill, stroke=C["tahrir"], sw=0.3, kind="tek", eye=True, eye_color=None):
    """kind: 'tek' | 'cift' (sırtından ikinci rûmî çıkan) | 'simetrik'
    (sağ-sol aynalı çift; tabanları ortada birleşir)."""
    parts = []
    units = []
    if kind == "tek":
        units = [ID]
    elif kind == "cift":
        units = [ID, mat(T(0.34, 0.06), mat(R(28), S(0.62, -0.62)))]
    elif kind == "simetrik":
        units = [T(0.02, 0), mat(T(-0.02, 0), S(-1, 1))]
    for U in units:
        M_ = mat(A, U)
        parts.append(el(_rumi_unit().tf(M_), fill, stroke, sw))
        if eye:
            parts.append(el(_rumi_eye().tf(M_), "none", eye_color or stroke, sw * 0.6))
    if kind == "simetrik":
        # birleşme noktasında küçük düğüm (kopça)
        parts.append(el(ellipse(0, 0, 0.07, 0.13).tf(A), fill, stroke, sw))
    return "".join(parts)


# ---- Hatâyî grubu ----------------------------------------------------------
def _petal(a0, a1, r0, r1, notch=0.0, cx=0.0, cy=0.0, pointed=False):
    """Merkez (cx,cy) etrafında a0..a1 derece aralığında yaprak (taç yaprağı)."""
    am = (a0 + a1) / 2
    b0 = polar(cx, cy, r0, a0 + (a1 - a0) * 0.30)
    b1 = polar(cx, cy, r0, a1 - (a1 - a0) * 0.30)
    s0 = polar(cx, cy, r1 * 0.92, a0)
    s1 = polar(cx, cy, r1 * 0.92, a1)
    tip = polar(cx, cy, r1 * (1.06 if pointed else 1.0) - notch * r1, am)
    l0 = polar(cx, cy, r1, a0 + (a1 - a0) * 0.22)
    l1 = polar(cx, cy, r1, a1 - (a1 - a0) * 0.22)
    p = Path().M(b0)
    p.C(polar(cx, cy, (r0 + r1) * 0.5, a0 - 2), s0, s0)
    p.C(polar(cx, cy, r1 * 1.12, a0 + 2), l0, l0)
    if pointed:
        p.C(polar(cx, cy, r1 * 1.08, am - (a1 - a0) * 0.1), tip, tip)
        p.C(tip, polar(cx, cy, r1 * 1.08, am + (a1 - a0) * 0.1), l1)
    else:
        p.C(polar(cx, cy, r1 * 1.08, am - (a1 - a0) * 0.12), tip, tip)
        p.C(tip, polar(cx, cy, r1 * 1.08, am + (a1 - a0) * 0.12), l1)
    p.C(l1, polar(cx, cy, r1 * 1.12, a1 - 2), s1)
    p.C(s1, polar(cx, cy, (r0 + r1) * 0.5, a1 + 2), b1)
    p.Z()
    return p


def penc(A, fill, stroke=C["tahrir"], sw=0.3, n=5, inner=None, center=None, rot=-90):
    """Penç: üstten görünen n taç yapraklı çiçek (birim yarıçap 1)."""
    out = []
    step = 360.0 / n
    for i in range(n):
        a = rot + i * step
        out.append(el(_petal(a - step * 0.5 + 3, a + step * 0.5 - 3, 0.18, 1.0, notch=0.12).tf(A),
                      fill, stroke, sw))
    inner = inner or fill
    for i in range(n):
        a = rot + i * step
        out.append(el(_petal(a - step * 0.32, a + step * 0.32, 0.12, 0.58, notch=0.0, pointed=True).tf(A),
                      inner, stroke, sw * 0.8))
    out.append(el(circle(0, 0, 0.22).tf(A), center or C["altin"], stroke, sw * 0.8))
    for i in range(n):
        p = polar(0, 0, 0.11, rot + i * step + step / 2)
        out.append(el(circle(p[0], p[1], 0.035).tf(A), stroke, None))
    return "".join(out)


def gonca(A, fill, stroke=C["tahrir"], sw=0.3, sepal=None, inner=None):
    """Gonca (tomurcuk): taban (0,0), uç (0,-1)."""
    body = bez((0, -1.0), (0.18, -0.78), (0.40, -0.52), (0.36, -0.30),
               (0.33, -0.12), (0.16, -0.04), (0, -0.04),
               (-0.16, -0.04), (-0.33, -0.12), (-0.36, -0.30),
               (-0.40, -0.52), (-0.18, -0.78), (0, -1.0)).Z()
    inner_p = bez((0, -0.80), (0.10, -0.64), (0.20, -0.46), (0.16, -0.30),
                  (0.12, -0.18), (0.05, -0.14), (0, -0.14),
                  (-0.05, -0.14), (-0.12, -0.18), (-0.16, -0.30),
                  (-0.20, -0.46), (-0.10, -0.64), (0, -0.80)).Z()
    sep = sepal or C["zumrut"]
    sl = bez((0, 0.08), (-0.30, 0.04), (-0.46, -0.20), (-0.44, -0.46),
             (-0.30, -0.30), (-0.18, -0.16), (0, -0.10)).Z()
    sr = sl.tf(S(-1, 1))
    stem = bez((0, 0.24), (0.02, 0.16), (0.02, 0.10), (0, 0.04)).Z()
    out = [el(body.tf(A), fill, stroke, sw),
           el(inner_p.tf(A), inner or C["astar"], stroke, sw * 0.7),
           el(sl.tf(A), sep, stroke, sw), el(sr.tf(A), sep, stroke, sw)]
    return "".join(out)


def hatayi(A, fill, stroke=C["tahrir"], sw=0.3, inner=None, calyx=None, center=None, petals=7):
    """Hatâyî: yandan görünen, yelpaze biçimli, katmanlı çiçek.
    Taban (0,0.5), tepe (0,-0.5) civarında; dikey eksende simetrik."""
    inner = inner or C["astar"]
    calyx = calyx or fill
    center = center or C["altin"]
    ocx, ocy = 0, 0.12
    out = []
    # dış taç yaprakları: -200..20 derece yelpaze (yukarı -90)
    span0, span1 = -205.0, 25.0
    step = (span1 - span0) / petals
    for i in range(petals):
        a0 = span0 + i * step
        out.append(el(_petal(a0 + 1.5, a0 + step - 1.5, 0.20, 0.56, notch=0.0, pointed=True,
                             cx=ocx, cy=ocy).tf(A), fill, stroke, sw))
    # iç katman
    s0, s1, m = -175.0, -5.0, 5
    st = (s1 - s0) / m
    for i in range(m):
        a0 = s0 + i * st
        out.append(el(_petal(a0 + 2, a0 + st - 2, 0.14, 0.40, notch=0.05,
                             cx=ocx, cy=ocy).tf(A), inner, stroke, sw * 0.8))
    # orta taç (göbekten yükselen sivri yaprak)
    mid = bez((0, -0.50), (0.10, -0.36), (0.14, -0.20), (0.10, -0.06),
              (0.04, 0.02), (-0.04, 0.02), (-0.10, -0.06),
              (-0.14, -0.20), (-0.10, -0.36), (0, -0.50)).Z()
    out.append(el(mid.tf(A), fill, stroke, sw * 0.8))
    # kadeh (çanak)
    cup = bez((-0.30, 0.16), (-0.24, 0.34), (-0.10, 0.44), (0, 0.50),
              (0.10, 0.44), (0.24, 0.34), (0.30, 0.16),
              (0.18, 0.22), (0.10, 0.20), (0, 0.24),
              (-0.10, 0.20), (-0.18, 0.22), (-0.30, 0.16)).Z()
    out.append(el(cup.tf(A), calyx, stroke, sw))
    # göbek
    out.append(el(ellipse(ocx, ocy, 0.17, 0.11).tf(A), center, stroke, sw * 0.8))
    for i in range(5):
        p = (ocx + (i - 2) * 0.06, ocy - 0.01)
        out.append(el(circle(p[0], p[1], 0.022).tf(A), stroke))
    return "".join(out)


def yaprak(A, fill, stroke=C["tahrir"], sw=0.3, vein=True, serrated=False, curve=0.15):
    """Basit sivri uçlu yaprak: sap (0,0), uç (0,-1)."""
    c = curve
    spine = ((0, 0), (c, -0.3), (c, -0.7), (0, -1.0))
    w = lambda t: 0.22 * math.sin(math.pi * min(1, t * 1.05)) ** 0.8 + 0.01
    path = ribbon(spine, w, n=32, serrate="B" if serrated else None,
                  teeth=7 if serrated else 0, tooth_depth=0.35)
    out = [el(path.tf(A), fill, stroke, sw)]
    if vein:
        out.append(el(bez(*spine[:1], spine[1], spine[2], lerp(spine[2], spine[3], 0.7)).tf(A),
                      "none", stroke, sw * 0.6))
    return "".join(out)


# ---- Saz yolu --------------------------------------------------------------
def saz(A, fill, stroke=C["tahrir"], sw=0.35, half=None, curl=0.45, teeth=11, vein=True):
    """Saz yaprağı (hançer yaprak, Şahkulu/Kara Memi üslûbu): uzun, kıvrık,
    dış kenarı tırtıllı; damar boyunca iki renkli. Sap (0,0), uç (0,-1)."""
    spine = ((0, 0), (curl * 0.2, -0.40), (curl * 1.10, -0.70), (curl * 0.55, -1.0))
    w = lambda t: 0.13 * (math.sin(math.pi * t) ** 0.75) * (1.0 - 0.25 * t) + 0.012
    full = ribbon(spine, w, n=70, serrate="R", teeth=teeth, tooth_depth=0.55)
    out = [el(full.tf(A), fill, stroke, sw)]
    if half:
        # damarın iç tarafındaki yarıyı farklı renkle doldur
        w2 = lambda t: w(t) * 0.5
        spine2 = tuple((p[0] + 0.0, p[1]) for p in spine)
        hp = ribbon(spine2, w2, n=60)
        # yarı şeridi damarın sol tarafına kaydır
        pts = spine_pts(spine, 60)
        left = []
        for i, p in enumerate(pts):
            t = i / 60
            tx, ty = cubic_tan(*spine, t)
            nx, ny = -ty, tx
            left.append((p[0] + nx * w(t) * 0.82, p[1] + ny * w(t) * 0.82))
        poly = [pts[0]] + left[1:-1] + [pts[-1]] + pts[-2:0:-1]
        out.append(el(smooth(poly, closed=True, tension=0.8).tf(A), half, stroke, sw * 0.6))
    if vein:
        out.append(el(bez(*spine).tf(A), "none", stroke, sw * 0.7))
    return "".join(out)


# ---- Bulut -----------------------------------------------------------------
def ribbon_pts(pts, widths, lobes=0, lobe_amp=0.0, lobe_range=(0.25, 0.75)):
    """Nokta dizisi omurgası boyunca kalınlık profilli kapalı şerit.
    widths(s) yay uzunluğu oranı s'ye göre yarı kalınlık."""
    lens = [0.0]
    for a, b in zip(pts, pts[1:]):
        lens.append(lens[-1] + dist(a, b))
    tot = lens[-1]
    left, right = [], []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        nx, ny = -ty / L, tx / L
        s = lens[i] / tot
        w = widths(s)
        wl = w
        if lobes and lobe_range[0] < s < lobe_range[1]:
            u = (s - lobe_range[0]) / (lobe_range[1] - lobe_range[0])
            wl = w * (1 + lobe_amp * abs(math.sin(math.pi * u * lobes)))
        left.append((p[0] + nx * wl, p[1] + ny * wl))
        right.append((p[0] - nx * w, p[1] - ny * w))
    return smooth(left + right[::-1], closed=True, tension=0.9)


def _cloud_spine():
    c1 = (-0.30, 0.0)
    sp = []
    for i in range(26):
        t = i / 25
        r = 0.02 + 0.115 * t
        a = math.radians(-90 - 400 * (1 - t))
        sp.append((c1[0] + r * math.cos(a), c1[1] + r * math.sin(a)))
    sp += [(-0.20, -0.135), (-0.10, -0.095)]
    half = sp + [(0.0, 0.0)]
    other = [(-x, -y) for x, y in reversed(sp)]
    return half + other


def bulut(A, fill, stroke=C["tahrir"], sw=0.3, lobes=4, inner=True):
    """Çin bulutu (ebrî bulut şeridi): iki ucu zıt yönde helezonla kıvrılan,
    ortası loblu S-şerit; merkeze göre nokta simetrik (C2).
    Birim boy 1 (x: -0.45..0.45)."""
    pts = _cloud_spine()
    w = lambda s: 0.010 + 0.052 * math.sin(math.pi * s) ** 0.8
    body = ribbon_pts(pts, w, lobes=lobes, lobe_amp=0.55, lobe_range=(0.3, 0.7))
    out = [el(body.tf(A), fill, stroke, sw)]
    if inner:
        mid = pts[10:-10]
        out.append(el(smooth(mid).tf(A), "none", stroke, sw * 0.5))
    return "".join(out)


# ---- Çintemani -------------------------------------------------------------
def cintemani(A, ball=None, wave=None, stroke=C["tahrir"], sw=0.3, waves=True):
    """Çintemani: üçgen dizilişte üç benek (birim) + altında çift dalgalı
    çizgi (kaplan çizgisi). Merkez (0,0), yükseklik ~1."""
    ball = ball or C["mercan"]
    wave = wave or C["kobalt"]
    out = []
    r = 0.17
    for (x, y) in ((0, -0.36), (-0.20, -0.02), (0.20, -0.02)):
        out.append(el(circle(x, y, r).tf(A), ball, stroke, sw * 1.15))
        # iç hilal
        cres = bez((x - r * 0.55, y - r * 0.05), (x - r * 0.45, y + r * 0.55), (x + r * 0.45, y + r * 0.55),
                   (x + r * 0.55, y - r * 0.05),
                   (x + r * 0.30, y + r * 0.25), (x - r * 0.30, y + r * 0.25), (x - r * 0.55, y - r * 0.05)).Z()
        out.append(el(cres.tf(A), C["astar"], None))
    if waves:
        for dy in (0.30, 0.46):
            spine = ((-0.46, dy), (-0.18, dy - 0.18), (0.18, dy + 0.16), (0.46, dy - 0.02))
            w = lambda t: 0.045 * math.sin(math.pi * t) ** 0.7 + 0.004
            out.append(el(ribbon(spine, w, n=40).tf(A), wave, stroke, sw))
    return "".join(out)


# ---- Şemse, salbek, köşebent ----------------------------------------------
def lobed_ellipse(cx, cy, rx, ry, n, bulge=0.08, pointed_ends=0.0, phase=0.0):
    """n dilimli (loblu) oval yol. pointed_ends>0 ise dikey uçlarda sivri
    tepelik (ry'ye oranla) oluşturulur."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * (i + phase) / n - math.pi / 2
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    p = Path().M(pts[0])
    for i in range(n):
        a0 = 2 * math.pi * (i + phase) / n - math.pi / 2
        a1 = 2 * math.pi * (i + 1 + phase) / n - math.pi / 2
        am = (a0 + a1) / 2
        q0, q1 = pts[i], pts[(i + 1) % n]
        b = 1 + bulge
        mid = (cx + rx * b * math.cos(am), cy + ry * b * math.sin(am))
        c0 = lerp(q0, mid, 0.75)
        c1 = lerp(q1, mid, 0.75)
        c0 = (c0[0] + (mid[0] - (q0[0] + q1[0]) / 2) * 0.35, c0[1] + (mid[1] - (q0[1] + q1[1]) / 2) * 0.35)
        c1 = (c1[0] + (mid[0] - (q0[0] + q1[0]) / 2) * 0.35, c1[1] + (mid[1] - (q0[1] + q1[1]) / 2) * 0.35)
        p.C(c0, c1, q1)
    p.Z()
    return p


def semse_path(cx, cy, rx, ry, n=16, bulge=0.10, tip=0.0, phase=0.5):
    """Şemse dış hattı: dilimli oval; tip>0 ise iki dikey uca sivri tepelik
    (tepelik yüksekliği ry*tip) eklenir."""
    base = lobed_ellipse(cx, cy, rx, ry, n, bulge, phase=phase)
    if tip <= 0:
        return base
    return base  # tepelikler ayrı şekil olarak eklenir (semse_finial)


def semse_finial(cx, cy, w, h, up=True):
    """Şemse/salbek ucundaki sivri tepelik (alem): taban genişliği w, boy h."""
    s = -1 if up else 1
    return bez((cx - w / 2, cy), (cx - w * 0.45, cy + s * h * 0.45), (cx - w * 0.12, cy + s * h * 0.70),
               (cx, cy + s * h),
               (cx + w * 0.12, cy + s * h * 0.70), (cx + w * 0.45, cy + s * h * 0.45), (cx + w / 2, cy)).Z()


def salbek_path(cx, cy, w, h, up=True, lobes=5):
    """Salbek (şemse ucundaki sarkıt): tabanı (cx,cy)'de düz, ucu sivri,
    kenarı dilimli damla biçimi. up=True ise yukarı doğru uzanır."""
    s = -1 if up else 1
    # sağ yarı kontrol noktaları; sonra aynalanır
    right = [(cx + w * 0.50, cy), (cx + w * 0.56, cy + s * h * 0.22), (cx + w * 0.46, cy + s * h * 0.46),
             (cx + w * 0.30, cy + s * h * 0.66), (cx + w * 0.13, cy + s * h * 0.84)]
    tipp = (cx, cy + s * h)
    p = Path().M((cx - w * 0.50, cy))
    left = [(2 * cx - x, y) for x, y in right]
    seq = left + [tipp] + right[::-1]
    for a, b in zip(seq[:-1], seq[1:]):
        mid = lerp(a, b, 0.5)
        # dışa bombe
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = dy / L, -dx / L
        # dış normal yönünü merkezden uzaklaşacak şekilde seç
        ref = (cx, cy + s * h * 0.45)
        if (mid[0] - ref[0]) * nx + (mid[1] - ref[1]) * ny < 0:
            nx, ny = -nx, -ny
        bb = L * 0.28
        p.C((a[0] + dx * 0.2 + nx * bb, a[1] + dy * 0.2 + ny * bb),
            (b[0] - dx * 0.2 + nx * bb, b[1] - dy * 0.2 + ny * bb), b)
    p.Z()
    return p


def kosebent_path(x, y, w, h, n=6, bulge=0.12, sx=1, sy=1):
    """Köşebent: (x,y) köşesinden içe doğru w×h boyutunda, iç kenarı
    dilimli çeyrek-oval. sx, sy köşenin yönü (+1/-1)."""
    pts = []
    for i in range(n + 1):
        a = (math.pi / 2) * i / n
        pts.append((x + sx * w * math.cos(a), y + sy * h * math.sin(a)))
    p = Path().M((x, y)).L(pts[0])
    for i in range(n):
        q0, q1 = pts[i], pts[i + 1]
        am = (math.pi / 2) * (i + 0.5) / n
        mid = (x + sx * w * (1 + bulge) * math.cos(am), y + sy * h * (1 + bulge) * math.sin(am))
        c0 = lerp(q0, mid, 0.8)
        c1 = lerp(q1, mid, 0.8)
        p.C(c0, c1, q1)
    p.L((x, y)).Z()
    return p


def tig_ring(path_pts, normal_out, length, width, color, stroke, sw, every=1):
    """Bir kontur noktaları listesi boyunca dışa bakan ince tığlar."""
    out = []
    for i, (p, nrm) in enumerate(zip(path_pts, normal_out)):
        if i % every:
            continue
        L = length * (1.0 if i % 2 == 0 else 0.6)
        out.append(el(tig_path(p, nrm, L, width), color, stroke, sw))
    return "".join(out)


def tig_path(p, nrm, L, w):
    """Tek tığ: p tabanında, nrm yönüne bakan, iç bükey kenarlı sivri iğne."""
    nx, ny = nrm
    tx, ty = -ny, nx
    b0 = (p[0] + tx * w / 2, p[1] + ty * w / 2)
    b1 = (p[0] - tx * w / 2, p[1] - ty * w / 2)
    tip = (p[0] + nx * L, p[1] + ny * L)
    m0 = (p[0] + nx * L * 0.35 + tx * w * 0.12, p[1] + ny * L * 0.35 + ty * w * 0.12)
    m1 = (p[0] + nx * L * 0.35 - tx * w * 0.12, p[1] + ny * L * 0.35 - ty * w * 0.12)
    return Path().M(b0).C(m0, lerp(m0, tip, 0.6), tip).C(lerp(m1, tip, 0.6), m1, b1).Z()


def sample_closed(path, n, start=None):
    """Kapalı Bézier yolunu yaklaşık eşit aralıklı n noktaya böler;
    (nokta, dış normal) listesi döndürür (yol saat yönünde varsayılmaz,
    normal merkeze göre dışa çevrilir)."""
    segs = []
    cur = None
    for c, pts in path.segs:
        if c == "M":
            cur = pts[0]
        elif c == "C":
            segs.append((cur, pts[0], pts[1], pts[2]))
            cur = pts[2]
        elif c == "L":
            segs.append((cur, lerp(cur, pts[0], 1 / 3), lerp(cur, pts[0], 2 / 3), pts[0]))
            cur = pts[0]
    dense = []
    for s in segs:
        for i in range(30):
            dense.append((cubic_pt(*s, i / 30), cubic_tan(*s, i / 30)))
    lens = [0.0]
    for a, b in zip(dense, dense[1:] + dense[:1]):
        lens.append(lens[-1] + dist(a[0], b[0]))
    total = lens[-1]
    cxm = sum(p[0] for p, _ in dense) / len(dense)
    cym = sum(p[1] for p, _ in dense) / len(dense)
    # örnekleme, simetri ekseninin konturu üst yarıda kestiği noktadan başlar
    if start is None:
        s_ax = None
        for i in range(len(dense)):
            (x_a, y_a), (x_b, y_b) = dense[i][0], dense[(i + 1) % len(dense)][0]
            if (x_a - cxm) * (x_b - cxm) <= 0 and x_a != x_b and min(y_a, y_b) < cym:
                f = (cxm - x_a) / (x_b - x_a)
                if s_ax is None or y_a < s_ax[1]:
                    s_ax = (lens[i] + f * (lens[i + 1] - lens[i]), y_a)
        s0 = s_ax[0] if s_ax else 0.0
    else:
        s0 = lens[start]
    out = []
    j = 0
    for k in range(n):
        target = (s0 + total * k / n) % total
        j = 0
        while lens[j + 1] < target:
            j += 1
        f = (target - lens[j]) / max(1e-12, lens[j + 1] - lens[j])
        p = lerp(dense[j][0], dense[(j + 1) % len(dense)][0], f)
        tx, ty = dense[j][1]
        nx, ny = ty, -tx
        if (p[0] - cxm) * nx + (p[1] - cym) * ny < 0:
            nx, ny = -nx, -ny
        out.append((p, (nx, ny)))
    return out


# ---- Mühr-i Süleyman --------------------------------------------------------
def interlace(segments, bw, fill, edge, ew, overs):
    """Düz şerit ağı için geçme (alttan-üstten) çizimi.
    segments: [(p,q), ...]; overs: [(seg_index, point)] üstte kalan parça.
    Şerit: koyu kenar (edge) + iç dolgu (fill)."""
    out = []
    W = bw + 2 * ew
    for p, q in segments:
        d = f"M{num(p[0])},{num(p[1])}L{num(q[0])},{num(q[1])}"
        out.append(f'<path d="{d}" stroke="{edge}" stroke-width="{num(W)}" stroke-linecap="square" fill="none"/>')
    for p, q in segments:
        d = f"M{num(p[0])},{num(p[1])}L{num(q[0])},{num(q[1])}"
        out.append(f'<path d="{d}" stroke="{fill}" stroke-width="{num(bw)}" stroke-linecap="square" fill="none"/>')
    for si, x in overs:
        p, q = segments[si]
        L = dist(p, q)
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        h = W * 1.3
        a = (x[0] - ux * h, x[1] - uy * h)
        b = (x[0] + ux * h, x[1] + uy * h)
        d = f"M{num(a[0])},{num(a[1])}L{num(b[0])},{num(b[1])}"
        out.append(f'<path d="{d}" stroke="{edge}" stroke-width="{num(W)}" stroke-linecap="butt" fill="none"/>')
        out.append(f'<path d="{d}" stroke="{fill}" stroke-width="{num(bw)}" stroke-linecap="butt" fill="none"/>')
    return "".join(out)


def seg_intersect(p, q, r, s):
    d = (q[0] - p[0]) * (s[1] - r[1]) - (q[1] - p[1]) * (s[0] - r[0])
    if abs(d) < 1e-12:
        return None
    t = ((r[0] - p[0]) * (s[1] - r[1]) - (r[1] - p[1]) * (s[0] - r[0])) / d
    u = ((r[0] - p[0]) * (q[1] - p[1]) - (r[1] - p[1]) * (q[0] - p[0])) / d
    if 1e-6 < t < 1 - 1e-6 and 1e-6 < u < 1 - 1e-6:
        return (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])), t, u
    return None


def weave(segments):
    """Düz şerit kümesinde bütün kesişimleri bulur ve klasik geçme kuralını
    (her şerit boyunca bir üstten, bir alttan) kısıt yayılımıyla kurar.
    Döndürür: [(üstteki şerit indeksi, kesişim noktası), ...]"""
    from collections import deque
    hits = {i: [] for i in range(len(segments))}
    xs = []
    for i in range(len(segments)):
        for j in range(i + 1, len(segments)):
            r = seg_intersect(*segments[i], *segments[j])
            if r:
                pt, t, u = r
                k = len(xs)
                xs.append((i, j, pt))
                hits[i].append((t, k))
                hits[j].append((u, k))
    order = {i: [k for _, k in sorted(h)] for i, h in hits.items()}
    pos = {}
    for i, ks in order.items():
        for n_, k in enumerate(ks):
            pos[(i, k)] = n_
    over = [None] * len(xs)
    for k0 in range(len(xs)):
        if over[k0] is not None:
            continue
        over[k0] = xs[k0][0]
        dq = deque([k0])
        while dq:
            k = dq.popleft()
            for line in xs[k][:2]:
                ks = order[line]
                n_ = pos[(line, k)]
                for m in (n_ - 1, n_ + 1):
                    if 0 <= m < len(ks):
                        kk = ks[m]
                        if over[kk] is not None:
                            continue
                        a, b = xs[kk][:2]
                        other = b if a == line else a
                        over[kk] = other if over[k] == line else line
                        dq.append(kk)
    return [(over[k], xs[k][2]) for k in range(len(xs))]


def muhr_segments(cx, cy, r, n=6, rot=-90):
    """Mühr-i Süleyman: n=6 için iki üçgen (hexagram {6/2}); n=8 için
    iki kare (Mağrib-Endülüs kullanımındaki sekiz köşeli hâtem {8/2})."""
    k = n // 2 if n in (6, 8) else 2
    m = n // (n // k) if False else None
    segs = []
    if n == 6:
        for off in (0, 60):
            pts = [polar(cx, cy, r, rot + off + 120 * i) for i in range(3)]
            segs += [(pts[i], pts[(i + 1) % 3]) for i in range(3)]
    elif n == 8:
        for off in (0, 45):
            pts = [polar(cx, cy, r, rot + off + 90 * i) for i in range(4)]
            segs += [(pts[i], pts[(i + 1) % 4]) for i in range(4)]
    return segs


def muhr(cx, cy, r, bw, fill, edge, ew, n=6, rot=-90, double=True):
    """Geçmeli/şeritli Mühr-i Süleyman. double=True: çift çizgili şerit
    (şeridin ortasında ince tahrir)."""
    segs = muhr_segments(cx, cy, r, n, rot)
    # köşelerde düzgün birleşim için kapalı poligonları yol olarak çiz
    polys = []
    per = 3 if n == 6 else 4
    for k in range(2):
        pts = [segs[k * per + i][0] for i in range(per)]
        polys.append(pts)
    out = []
    W = bw + 2 * ew
    for pts in polys:
        out.append(f'<path d="{polygon(pts).d()}" fill="none" stroke="{edge}" stroke-width="{num(W)}" stroke-linejoin="miter" stroke-miterlimit="10"/>')
    for pts in polys:
        out.append(f'<path d="{polygon(pts).d()}" fill="none" stroke="{fill}" stroke-width="{num(bw)}" stroke-linejoin="miter" stroke-miterlimit="10"/>')
    if double:
        for pts in polys:
            out.append(f'<path d="{polygon(pts).d()}" fill="none" stroke="{edge}" stroke-width="{num(ew * 0.6)}" stroke-linejoin="miter" stroke-miterlimit="10"/>')
    # geçme: kesişimlerde dönüşümlü üst parça
    overs = weave(segs)
    for si, x in overs:
        p, q = segs[si]
        L = dist(p, q)
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        h = W * 1.25
        a = (x[0] - ux * h, x[1] - uy * h)
        b = (x[0] + ux * h, x[1] + uy * h)
        d = f"M{num(a[0])},{num(a[1])}L{num(b[0])},{num(b[1])}"
        out.append(f'<path d="{d}" stroke="{edge}" stroke-width="{num(W)}" stroke-linecap="butt" fill="none"/>')
        out.append(f'<path d="{d}" stroke="{fill}" stroke-width="{num(bw)}" stroke-linecap="butt" fill="none"/>')
        if double:
            out.append(f'<path d="{d}" stroke="{edge}" stroke-width="{num(ew * 0.6)}" stroke-linecap="butt" fill="none"/>')
    return "".join(out)


# ---- Geometrik yıldız-poligon ağı (Hankin "temas eden poligonlar") ---------
def reg_poly(cx, cy, n, s, rot):
    R_ = s / (2 * math.sin(math.pi / n))
    return [polar(cx, cy, R_, rot + 360.0 * i / n) for i in range(n)]


def tiling(kind, cx, cy, s, bbox):
    """kind: '488' (sekizgen+kare, 8'li yıldız), '4612' (onikigen+altıgen+kare,
    12'li yıldız), '10' (ongen + beşgen halkası, 10'lu rozet yaması).
    (cx,cy) merkezde bir 8/12/10-gen bulunur; poligonlar bbox içinde."""
    x0, y0, x1, y1 = bbox
    polys = []
    if kind == "488":
        a = s * (1 + math.sqrt(2))
        ni = int((x1 - x0) / a) + 3
        nj = int((y1 - y0) / a) + 3
        for i in range(-ni, ni + 1):
            for j in range(-nj, nj + 1):
                ox, oy = cx + i * a, cy + j * a
                if x0 - a < ox < x1 + a and y0 - a < oy < y1 + a:
                    polys.append(("oct", reg_poly(ox, oy, 8, s, 22.5)))
                qx, qy = ox + a / 2, oy + a / 2
                if x0 - a < qx < x1 + a and y0 - a < qy < y1 + a:
                    polys.append(("sq", reg_poly(qx, qy, 4, s, 0)))
    elif kind == "4612":
        r12 = s * (2 + math.sqrt(3)) / 2
        L = 2 * r12 + s
        v1 = (L, 0)
        v2 = (L / 2, L * math.sqrt(3) / 2)
        n = int(max(x1 - x0, y1 - y0) / L) + 3
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                ox = cx + i * v1[0] + j * v2[0]
                oy = cy + i * v1[1] + j * v2[1]
                if not (x0 - L < ox < x1 + L and y0 - L < oy < y1 + L):
                    continue
                polys.append(("dod", reg_poly(ox, oy, 12, s, 15)))
                for ang in (0, 60, 120):
                    q = polar(ox, oy, L / 2, ang)
                    polys.append(("sq", reg_poly(q[0], q[1], 4, s, ang + 45)))
                for ang in (30, 90):
                    h = polar(ox, oy, L / math.sqrt(3), ang)
                    polys.append(("hex", reg_poly(h[0], h[1], 6, s, ang)))
    elif kind == "10":
        polys.append(("dec", reg_poly(cx, cy, 10, s, 18)))
        dec = reg_poly(cx, cy, 10, s, 18)
        for i in range(10):
            p, q = dec[i], dec[(i + 1) % 10]
            m = lerp(p, q, 0.5)
            ang = math.degrees(math.atan2(m[1] - cy, m[0] - cx))
            rin = s / (2 * math.tan(math.pi / 5))
            c5 = polar(m[0], m[1], rin, ang)
            polys.append(("pent", reg_poly(c5[0], c5[1], 5, s, ang + 180)))
    return polys


def hankin(poly, theta):
    """Bir poligon için Hankin yıldız noktaları: her kenar ortasından
    kenarla theta açısı yapan iki ışın; komşu ışınların kesişimi.
    Döndürür: (yıldız poligonu noktaları, çizgi parçaları)."""
    n = len(poly)
    mids = [lerp(poly[i], poly[(i + 1) % n], 0.5) for i in range(n)]
    star = []
    segs = []
    for i in range(n):
        # i. kenar ve (i+1). kenarın paylaştığı köşe: poly[i+1]
        m0, m1 = mids[i], mids[(i + 1) % n]
        v = poly[(i + 1) % n]
        # m0'dan v'ye doğru kenar yönü, içe theta kadar döndür
        e0 = (v[0] - m0[0], v[1] - m0[1])
        e1 = (v[0] - m1[0], v[1] - m1[1])
        cxp = sum(p[0] for p in poly) / n
        cyp = sum(p[1] for p in poly) / n

        def inward(m, e):
            L = math.hypot(*e)
            ux, uy = e[0] / L, e[1] / L
            th = math.radians(theta)
            cands = []
            for sg in (1, -1):
                rx = ux * math.cos(sg * th) - uy * math.sin(sg * th)
                ry = ux * math.sin(sg * th) + uy * math.cos(sg * th)
                score = (cxp - m[0]) * rx + (cyp - m[1]) * ry
                cands.append((score, (rx, ry)))
            return max(cands)[1]

        r0 = inward(m0, e0)
        r1 = inward(m1, e1)
        d = r0[0] * r1[1] - r0[1] * r1[0]
        if abs(d) < 1e-12:
            continue
        t = ((m1[0] - m0[0]) * r1[1] - (m1[1] - m0[1]) * r1[0]) / d
        X = (m0[0] + r0[0] * t, m0[1] + r0[1] * t)
        star += [m0, X]
        segs += [(m0, X), (X, m1)]
    return star, segs


def girih(kind, cx, cy, s, bbox, theta, line, lw, fills, ground, edge=None, ew=0.0,
          interlaced=False, star_fill_kinds=None):
    """Yıldız-poligon ağı. fills: {poligon türü: dolgu rengi} yıldız dolguları.
    interlaced=True: çizgiler şerit (geçmeli) olarak çizilir."""
    polys = tiling(kind, cx, cy, s, bbox)
    out = []
    x0, y0, x1, y1 = bbox
    out.append(el(rect(x0, y0, x1, y1), ground))
    all_segs = []
    for kname, poly in polys:
        star, segs = hankin(poly, theta)
        col = fills(kname, poly) if callable(fills) else fills.get(kname)
        if col:
            out.append(el(polygon(star), col, None))
        all_segs += segs
    if interlaced:
        out.append(interlace_net(all_segs, lw, line, edge or C["tahrir"], ew))
    else:
        d = "".join(f"M{num(p[0])},{num(p[1])}L{num(q[0])},{num(q[1])}" for p, q in all_segs)
        if edge:
            out.append(f'<path d="{d}" stroke="{edge}" stroke-width="{num(lw + 2 * ew)}" stroke-linecap="round" fill="none"/>')
        out.append(f'<path d="{d}" stroke="{line}" stroke-width="{num(lw)}" stroke-linecap="round" fill="none"/>')
    return "".join(out), polys


def _merge_collinear(segs, tol=1e-3):
    """Hankin parçalarını (komşu poligonlarda devam eden) uzun doğrulara
    birleştirir; geçmede alt-üst dönüşümü doğru sayılsın diye gereklidir."""
    def key(p):
        return (round(p[0] / tol), round(p[1] / tol))
    from collections import defaultdict
    adj = defaultdict(list)
    for i, (p, q) in enumerate(segs):
        adj[key(p)].append(i)
        adj[key(q)].append(i)
    used = [False] * len(segs)
    lines = []

    def direction(p, q):
        L = dist(p, q) or 1
        return ((q[0] - p[0]) / L, (q[1] - p[1]) / L)

    for i in range(len(segs)):
        if used[i]:
            continue
        used[i] = True
        p, q = segs[i]
        u = direction(p, q)
        # ileri uzat
        changed = True
        while changed:
            changed = False
            for j in adj[key(q)]:
                if used[j]:
                    continue
                a, b = segs[j]
                if key(a) != key(q):
                    a, b = b, a
                v = direction(a, b)
                if abs(u[0] * v[0] + u[1] * v[1] - 1) < 1e-6:
                    used[j] = True
                    q = b
                    changed = True
                    break
        changed = True
        while changed:
            changed = False
            for j in adj[key(p)]:
                if used[j]:
                    continue
                a, b = segs[j]
                if key(b) != key(p):
                    a, b = b, a
                v = direction(a, b)
                if abs(u[0] * v[0] + u[1] * v[1] - 1) < 1e-6:
                    used[j] = True
                    p = a
                    changed = True
                    break
        lines.append((p, q))
    return lines


def interlace_net(segs, bw, fill, edge, ew):
    lines = _merge_collinear(segs)
    # dedupe
    seen = set()
    uniq = []
    for p, q in lines:
        k = tuple(sorted([(round(p[0], 3), round(p[1], 3)), (round(q[0], 3), round(q[1], 3))]))
        if k not in seen and dist(p, q) > 1e-3:
            seen.add(k)
            uniq.append((p, q))
    overs = weave(uniq)
    return interlace(uniq, bw, fill, edge, ew, overs)


def rosette(cx, cy, n, R_, fill_star, fill_petal, line, lw, edge, ew, rot=-90, ground=None):
    """Klasik n kollu rozet: merkezde {n}-yıldız, çevresinde n adet altıgen
    yaprak (petal) halkası; Hankin yöntemiyle değil doğrudan kurulur."""
    out = []
    step = 360.0 / n
    a = R_            # yaprak dış uçları yarıçapı
    r_tip = R_ * 0.56  # yıldız uçları
    r_in = r_tip * math.cos(math.pi / n * 2) / math.cos(math.pi / n) * 0.98
    tips = [polar(cx, cy, r_tip, rot + i * step) for i in range(n)]
    inn = [polar(cx, cy, r_in, rot + (i + 0.5) * step) for i in range(n)]
    star = []
    for i in range(n):
        star += [tips[i], inn[i]]
    if ground:
        out.append(el(circle(cx, cy, R_ * 1.02), ground, None))
    # yapraklar: yıldızın iki ucu arasındaki girintiden dışa uzanan altıgenler
    petals = []
    for i in range(n):
        t0, t1 = tips[i], tips[(i + 1) % n]
        vin = inn[i]
        out_pt = polar(cx, cy, a, rot + (i + 0.5) * step)
        s0 = polar(cx, cy, R_ * 0.80, rot + (i + 0.5) * step - step * 0.36)
        s1 = polar(cx, cy, R_ * 0.80, rot + (i + 0.5) * step + step * 0.36)
        petals.append([vin, t0, s0, out_pt, s1, t1])
    for pp in petals:
        out.append(el(polygon(pp), fill_petal, None))
    out.append(el(polygon(star), fill_star, None))
    segs = []
    for pp in petals:
        segs += [(pp[k], pp[(k + 1) % 6]) for k in range(6)]
    d = "".join(f"M{num(p[0])},{num(p[1])}L{num(q[0])},{num(q[1])}" for p, q in segs)
    out.append(f'<path d="{d}" stroke="{edge}" stroke-width="{num(lw + 2 * ew)}" stroke-linejoin="round" stroke-linecap="round" fill="none"/>')
    out.append(f'<path d="{d}" stroke="{line}" stroke-width="{num(lw)}" stroke-linejoin="round" stroke-linecap="round" fill="none"/>')
    return "".join(out)


# ---- Zencerek ve tığ (kenar suyu) ------------------------------------------
def zencerek(x0, y0, x1, y1, bw, unit, fill, ground, stroke, sw, rule=C["altin_koyu"]):
    """Dikdörtgen bant (dış kenar x0..x1, y0..y1; genişlik bw) boyunca
    zincir (zencerek) dizisi: iç içe geçmiş badem halkalar + boncuk.
    Her kenarda birim sayısı tam sayıya yuvarlanır (simetri için)."""
    out = []
    outer = rect(x0, y0, x1, y1)
    inner = rect(x0 + bw, y0 + bw, x1 - bw, y1 - bw)
    out.append(f'<path d="{(outer + inner).d()}" fill="{ground}" fill-rule="evenodd"/>')

    def side(p, q, nrm):
        L = dist(p, q)
        nunit = max(2, int(round(L / unit)))
        u = L / nunit
        ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
        nx, ny = nrm
        res = []
        h = bw * 0.30
        for i in range(nunit):
            c = (p[0] + ux * u * (i + 0.5) + nx * bw / 2, p[1] + uy * u * (i + 0.5) + ny * bw / 2)
            # badem (mandorla) halka: yatay uzunluk u*0.62
            A = (c[0] - ux * u * 0.55, c[1] - uy * u * 0.55)
            B = (c[0] + ux * u * 0.55, c[1] + uy * u * 0.55)
            up = (nx * h, ny * h)
            ring = Path().M(A).C((A[0] + ux * u * 0.25 + up[0], A[1] + uy * u * 0.25 + up[1]),
                                 (B[0] - ux * u * 0.25 + up[0], B[1] - uy * u * 0.25 + up[1]), B) \
                .C((B[0] - ux * u * 0.25 - up[0], B[1] - uy * u * 0.25 - up[1]),
                   (A[0] + ux * u * 0.25 - up[0], A[1] + uy * u * 0.25 - up[1]), A).Z()
            res.append((0, f'<path d="{ring.d()}" fill="none" stroke="{stroke}" stroke-width="{num(sw * 3.2)}"/>'))
            res.append((1, f'<path d="{ring.d()}" fill="none" stroke="{fill}" stroke-width="{num(sw * 1.9)}"/>'))
            res.append((2, el(circle(c[0], c[1], bw * 0.11), fill, stroke, sw * 0.8)))
        return res

    # kenarlar: halkalar zincir gibi birleşsin diye önce bütün koyu
    # kenarlar, sonra altın iç çizgiler, en son boncuklar (sıra simetrik)
    parts = []
    parts += side((x0 + bw, y0), (x1 - bw, y0), (0, 1))
    parts += side((x0 + bw, y1 - bw), (x1 - bw, y1 - bw), (0, 1))
    parts += side_v(x0, y0 + bw, y1 - bw, bw, unit, fill, stroke, sw)
    parts += side_v(x1 - bw, y0 + bw, y1 - bw, bw, unit, fill, stroke, sw)
    for layer in (0, 1, 2):
        out += [s for l_, s in parts if l_ == layer]
    # köşe rozetleri
    for (qx, qy) in ((x0, y0), (x1 - bw, y0), (x0, y1 - bw), (x1 - bw, y1 - bw)):
        cxk, cyk = qx + bw / 2, qy + bw / 2
        out.append(el(rect(qx, qy, qx + bw, qy + bw), ground))
        out.append(penc_small(cxk, cyk, bw * 0.42, fill, stroke, sw))
    # cetveller
    out.append(f'<path d="{outer.d()}" fill="none" stroke="{rule}" stroke-width="{num(sw * 1.6)}"/>')
    out.append(f'<path d="{inner.d()}" fill="none" stroke="{rule}" stroke-width="{num(sw * 1.6)}"/>')
    return "".join(out)


def side_v(x, ya, yb, bw, unit, fill, stroke, sw):
    """zencerek: dikey kenar (bant sol kenarı x, genişlik bw)."""
    L = yb - ya
    nunit = max(2, int(round(L / unit)))
    u = L / nunit
    res = []
    h = bw * 0.30
    for i in range(nunit):
        c = (x + bw / 2, ya + u * (i + 0.5))
        A = (c[0], c[1] - u * 0.55)
        B = (c[0], c[1] + u * 0.55)
        ring = Path().M(A).C((A[0] + h, A[1] + u * 0.25), (B[0] + h, B[1] - u * 0.25), B) \
            .C((B[0] - h, B[1] - u * 0.25), (A[0] - h, A[1] + u * 0.25), A).Z()
        res.append((0, f'<path d="{ring.d()}" fill="none" stroke="{stroke}" stroke-width="{num(sw * 3.2)}"/>'))
        res.append((1, f'<path d="{ring.d()}" fill="none" stroke="{fill}" stroke-width="{num(sw * 1.9)}"/>'))
        res.append((2, el(circle(c[0], c[1], bw * 0.11), fill, stroke, sw * 0.8)))
    return res


def penc_small(cx, cy, r, fill, stroke, sw, n=4, rot=45):
    """Kenar suyu köşeleri için küçük dört yapraklı çiçek."""
    out = []
    for i in range(n):
        a = rot + i * 360.0 / n
        p = polar(cx, cy, r, a)
        l0 = polar(cx, cy, r * 0.55, a - 32)
        l1 = polar(cx, cy, r * 0.55, a + 32)
        leaf = Path().M((cx, cy)).C(l0, polar(cx, cy, r * 0.95, a - 18), p) \
            .C(polar(cx, cy, r * 0.95, a + 18), l1, (cx, cy)).Z()
        out.append(el(leaf, fill, stroke, sw))
    out.append(el(circle(cx, cy, r * 0.22), C["astar"], stroke, sw))
    return "".join(out)


def tig_frame(x0, y0, x1, y1, depth, pitch, color, stroke, sw, tip_dot=True):
    """Dikdörtgen (x0..x1 dış sınır değil; tığların dibi) çevresinde dışa
    bakan tığlar. Tığlar depth kadar dışa uzanır (uzun-kısa dönüşümlü)."""
    out = []

    def run(p, q, nrm):
        L = dist(p, q)
        n = max(2, 2 * int(round(L / (2 * pitch))))
        # n çift: uzun-kısa sırası kenar ortasına göre aynalı kalır
        for i in range(1, n):
            t = i / n
            b = lerp(p, q, t)
            long_ = (i % 2 == 0)
            Ld = depth * (1.0 if long_ else 0.62)
            w = pitch * (0.34 if long_ else 0.26)
            out.append(el(tig_path(b, nrm, Ld, w), color, stroke, sw))
            if tip_dot and long_:
                tp = (b[0] + nrm[0] * (Ld * 0.82), b[1] + nrm[1] * (Ld * 0.82))
        return

    run((x0, y0), (x1, y0), (0, -1))
    run((x0, y1), (x1, y1), (0, 1))
    run((x0, y0), (x0, y1), (-1, 0))
    run((x1, y0), (x1, y1), (1, 0))
    # köşe tığları (köşegen)
    s2 = math.sqrt(0.5)
    for (px, py, nx, ny) in ((x0, y0, -s2, -s2), (x1, y0, s2, -s2), (x0, y1, -s2, s2), (x1, y1, s2, s2)):
        out.append(el(tig_path((px, py), (nx, ny), depth * 1.2, pitch * 0.4), color, stroke, sw))
    return "".join(out)


def outer_frame(defs, tig_color, zen_fill, zen_ground, rule=C["altin_koyu"],
                tig_depth=9.0, tig_pitch=5.0, zen_w=8.0, zen_unit=8.0, gap=1.6):
    """Her kompozisyonda ortak dış düzen (dıştan içe):
    dış cetvel (tezhip alanı sınırı) -> tığ kuşağı -> zencerek kenar suyu.
    Döndürür: (svg, iç dikdörtgen)."""
    x0, y0, x1, y1 = AREA
    out = []
    lw = 0.5
    out.append(f'<path d="{rect(x0 + lw / 2, y0 + lw / 2, x1 - lw / 2, y1 - lw / 2).d()}" fill="none" stroke="{rule}" stroke-width="{num(lw)}"/>')
    zx0 = x0 + tig_depth + gap + 1.2
    zy0 = y0 + tig_depth + gap + 1.2
    zx1 = x1 - (tig_depth + gap + 1.2)
    zy1 = y1 - (tig_depth + gap + 1.2)
    out.append(tig_frame(zx0, zy0, zx1, zy1, tig_depth, tig_pitch, tig_color, None, 0))
    out.append(zencerek(zx0, zy0, zx1, zy1, zen_w, zen_unit, zen_fill, zen_ground, C["tahrir"], 0.25, rule))
    return "".join(out), (zx0 + zen_w, zy0 + zen_w, zx1 - zen_w, zy1 - zen_w)


# ---------------------------------------------------------------- helezon dolgu
def spiral_pts(c, start, turns, r_end_ratio, sense, n=48):
    """c merkezli, start noktasından başlayıp içe kıvrılan helezon noktaları."""
    r0 = dist(c, start)
    a0 = math.atan2(start[1] - c[1], start[0] - c[0])
    pts = []
    for i in range(n + 1):
        t = i / n
        r = r0 * (1 - (1 - r_end_ratio) * (t ** 0.85))
        a = a0 + sense * 2 * math.pi * turns * t
        pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    return pts


def scroll_field(bbox, d, stem_color, sw_stem, motif_fn, rows_offset=True, seed=0,
                 turns=1.05, leaf_fn=None, leaf_every=(0.22, 0.45, 0.68), skip=None, phase=(0, 0)):
    """Helezonî kıvrım dolgu: tuğla düzeninde helezon merkezleri; her satırda
    komşu merkezler S-kıvrımlarla bağlanır. motif_fn(center, size, k) her
    helezon merkezine çiçek; leaf_fn(point, angle, size, k) helezon üzerine
    yaprak/rûmî/gonca koyar. Döndürür: (gövde svg, motif svg)."""
    x0, y0, x1, y1 = bbox
    rowh = d * 0.86
    stems, motifs, leaves = [], [], []
    j = 0
    y = y0 + phase[1] - rowh
    while y < y1 + rowh:
        off = (d / 2 if (j % 2 and rows_offset) else 0) + phase[0]
        xs = []
        x = x0 + off - d
        while x < x1 + d:
            xs.append(x)
            x += d
        for i, xc in enumerate(xs):
            c = (xc, y)
            sense = 1 if (i + j) % 2 == 0 else -1
            k = (i * 7 + j * 3 + seed)
            if skip and skip(c):
                continue
            # S bağlantısı: sağdaki orta noktadan merkeze helezon
            m = (xc + d / 2, y)
            pts = spiral_pts(c, m, turns, 0.30, sense)
            stems.append(smooth(pts))
            m2 = (xc - d / 2, y)
            pts2 = spiral_pts(c, m2, turns * 0.55, 0.62, sense)
            stems.append(smooth(pts2))
            pa, pb = pts[-3], pts[-1]
            ang_end = math.degrees(math.atan2(pb[1] - pa[1], pb[0] - pa[0]))
            motifs.append(motif_fn(pts[-1], d, k, ang_end))
            if leaf_fn:
                for t in leaf_every:
                    idx = int(t * (len(pts) - 1))
                    p, q = pts[idx], pts[idx + 1]
                    ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
                    # helezonun dışına bakacak şekilde yön
                    leaves.append(leaf_fn(p, ang - sense * 70, d, k + idx))
        y += rowh
        j += 1
    stem_svg = "".join(f'<path d="{s.d()}" fill="none" stroke="{stem_color}" stroke-width="{num(sw_stem)}" stroke-linecap="round"/>' for s in stems)
    return stem_svg, "".join(leaves) + "".join(motifs)


# ---------------------------------------------------------------- bordür
def odd(n):
    n = max(1, int(round(n)))
    return n if n % 2 else n + 1


def band_scroll(L, w, k, stem, sw, flower_fn, leaf_fn=None, amp=0.24):
    """Kenar suyu için koşan helezon (S-dal) dizisi, yerel koordinatta:
    x 0..L, y -w/2..w/2. k (tek sayı) yarım dalga; böylece dizi kenar
    ortasına göre aynalı simetriktir. Çiçekler dalga koylarına, tepe
    noktasına oturur ve karşı kenara bakar."""
    A = amp * w
    N = 40 * k
    pts = [(L * i / N, A * math.sin(math.pi * k * i / N)) for i in range(N + 1)]
    out = [f'<path d="{smooth(pts).d()}" fill="none" stroke="{stem}" stroke-width="{num(sw)}" stroke-linecap="round"/>']
    items = []
    for m in range(k):
        s = (m + 0.5) / k
        sign = 1 if m % 2 == 0 else -1
        x = L * s
        y = A * sign
        # çiçek: tabanı dal tepesinde, ucu karşı kenara (−sign yönü)
        rot = 0 if sign > 0 else 180
        items.append(flower_fn((x, y), rot, w, m))
        if leaf_fn:
            for side in (-1, 1):
                xl = x + side * L / k * 0.42
                yl = A * math.sin(math.pi * k * xl / L)
                items.append(leaf_fn((xl, yl), rot + 180 + side * (-40 if sign > 0 else 40), w, m, side))
    return "".join(out) + "".join(items)


def frame_band(x0, y0, x1, y1, w, ground, content_fn, corner_fn, rule, rule_w=0.5):
    """Dikdörtgen kuşak (dış kenar x0..x1, y0..y1; genişlik w). content_fn(L)
    yerel (0..L, -w/2..w/2) içerik döndürür; üst ve sol kenar üretilir, alt
    ve sağ kenar aynalanır (D2). Köşe kareleri corner_fn(cx, cy, w)."""
    out = []
    outer = rect(x0, y0, x1, y1)
    inner = rect(x0 + w, y0 + w, x1 - w, y1 - w)
    out.append(f'<path d="{(outer + inner).d()}" fill="{ground}" fill-rule="evenodd"/>')
    ax, ay = (x0 + x1) / 2, (y0 + y1) / 2
    Lh = x1 - x0 - 2 * w
    Lv = y1 - y0 - 2 * w
    top = g(content_fn(Lh), transform=f"translate({num(x0 + w)},{num(y0 + w / 2)})")
    left = g(content_fn(Lv), transform=f"matrix(0,1,1,0,{num(x0 + w / 2)},{num(y0 + w)})")
    out.append(top + mirror_y(top, ay))
    out.append(left + mirror_x(left, ax))
    out.append(sym_d2(corner_fn(x0 + w / 2, y0 + w / 2, w), ax, ay))
    out.append(f'<path d="{outer.d()}" fill="none" stroke="{rule}" stroke-width="{num(rule_w)}"/>')
    out.append(f'<path d="{inner.d()}" fill="none" stroke="{rule}" stroke-width="{num(rule_w)}"/>')
    d = f"M{num(x0)},{num(y0)}L{num(x0 + w)},{num(y0 + w)}"
    return "".join(out)


def sym_bez(segs, ax=CX):
    """Sağ yarı Bézier parçalarından (eksen üstünden eksen altına) dikey
    eksene göre simetrik kapalı yol kurar. segs: [(p0,c1,c2,p3), ...]"""
    m = lambda p: (2 * ax - p[0], p[1])
    p = Path().M(segs[0][0])
    for s in segs:
        if len(s) == 2:
            p.L(s[1])
        else:
            p.C(s[1], s[2], s[3])
    for s in reversed(segs):
        if len(s) == 2:
            p.L(m(s[0]))
        else:
            p.C(m(s[2]), m(s[1]), m(s[0]))
    return p.Z()


def sym_band_items(L, n, item_fn, between_fn=None):
    """Kenar suyu için ayna simetrik birim dizisi (yerel x 0..L). n çift;
    sol yarı üretilir, L/2 eksenine göre aynalanır."""
    n = max(2, n + (n % 2))
    u = L / n
    out = []
    for i in range(n // 2):
        out.append(item_fn((i + 0.5) * u, u, i))
    if between_fn:
        for i in range(1, n // 2 + 1):
            out.append(between_fn(i * u, u, i))
    c = "".join(out)
    return c + mirror_x(c, L / 2)
