"""Motif sözlüğü test sayfası: her motif tek başına, büyük ölçekte."""
import cairosvg
from motifs import *

W, H = 500, 700
cells = []
def cell(i, j):  # 4 sütun x 6 satır, hücre 110x105
    return 30 + i * 112 + 56, 40 + j * 108 + 54

items = []
x, y = cell(0, 0); items.append(rumi(place(x - 35, y + 10, 70), C["altin"], kind="tek"))
x, y = cell(1, 0); items.append(rumi(place(x - 35, y + 10, 70), C["firuze"], kind="cift"))
x, y = cell(2, 0); items.append(rumi(place(x, y + 10, 45), C["kobalt"], kind="simetrik"))
x, y = cell(3, 0); items.append(penc(place(x, y, 38), C["mercan"], inner=C["astar"]))
x, y = cell(0, 1); items.append(hatayi(place(x, y, 80), C["kobalt"], inner=C["firuze"], calyx=C["zumrut"]))
x, y = cell(1, 1); items.append(gonca(place(x, y + 35, 75), C["mercan"]))
x, y = cell(2, 1); items.append(yaprak(place(x, y + 40, 80), C["zumrut"]))
x, y = cell(3, 1); items.append(yaprak(place(x, y + 40, 80), C["firuze"], serrated=True))
x, y = cell(0, 2); items.append(saz(place(x - 20, y + 48, 100), C["zumrut"], half=C["firuze"]))
x, y = cell(1, 2); items.append(bulut(place(x, y, 95), C["firuze"]))
x, y = cell(2, 2); items.append(cintemani(place(x, y, 80)))
x, y = cell(3, 2); items.append(muhr(x, y, 42, 4.0, C["altin"], C["tahrir"], 0.4))
x, y = cell(0, 3)
sp = lobed_ellipse(x, y, 36, 48, 16, 0.10, phase=0.5)
items.append(el(sp, C["lacivert"], C["altin"], 1.2))
items.append(el(semse_finial(x, y - 48, 12, 10), C["lacivert"], C["altin"], 0.8))
x, y = cell(1, 3); items.append(el(salbek_path(x, y + 30, 45, 60), C["lacivert"], C["altin"], 1.0))
x, y = cell(2, 3); items.append(el(kosebent_path(x - 50, y - 50, 90, 90, 6), C["lacivert"], C["altin"], 1.0))
x, y = cell(3, 3); items.append(muhr(x, y, 42, 4.0, C["firuze"], C["tahrir"], 0.4, n=8))
d = Defs()
x, y = cell(0, 4)
cid = d.clip(circle(x, y, 52))
s, _ = girih("488", x, y, 9, (x - 55, y - 55, x + 55, y + 55), 67.5, C["altin"], 0.8,
             {"oct": C["lacivert"], "sq": C["firuze"]}, C["kobalt"], edge=C["tahrir"], ew=0.3)
items.append(g(s, clip=cid))
x, y = cell(1, 4)
cid = d.clip(circle(x, y, 52))
s, _ = girih("4612", x, y, 7, (x - 55, y - 55, x + 55, y + 55), 60, C["altin"], 0.8,
             {"dod": C["lacivert"], "hex": C["firuze"], "sq": C["kobalt"]}, C["astar"], edge=C["tahrir"], ew=0.3)
items.append(g(s, clip=cid))
x, y = cell(2, 4)
cid = d.clip(circle(x, y, 52))
s, _ = girih("10", x, y, 22, (x - 55, y - 55, x + 55, y + 55), 54, C["altin"], 0.8,
             {"dec": C["lacivert"], "pent": C["firuze"]}, C["astar"], edge=C["tahrir"], ew=0.3)
items.append(g(s, clip=cid))
x, y = cell(3, 4)
items.append(rosette(x, y, 12, 50, C["altin"], C["lacivert"], C["altin_koyu"], 0.6, C["tahrir"], 0.2))
x, y = cell(0, 5)
items.append(zencerek(x - 50, y - 40, x + 160, y + 40, 9, 9, C["altin"], C["lacivert"], C["tahrir"], 0.25))
items.append(tig_frame(x + 230, y - 30, x + 380, y + 30, 10, 5, C["kobalt"], None, 0))
x, y = cell(2, 5)
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">'
       + d.svg() + f'<rect width="{W}" height="{H}" fill="{C["astar"]}"/>' + "".join(items) + "</svg>")
open("motif_test.svg", "w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to="motif_test.png", dpi=110)
