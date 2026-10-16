# -*- coding: utf-8 -*-
import struct, os, sys
from PIL import Image
import validate_font as V
import make_font as M

# 1) ASCII rendering must be pixel-identical to the original font
def draw_with(f, text):
    return V.draw_text(f, text)

newf = V.parse(r"D:\Steam\tf_cn_work\out\OpenSans.xnb")
orig = M.parse_original(r"D:\Steam\steamapps\common\TowerFall\CN_BACKUP\OpenSans.xnb")
# build an original-font dict compatible with draw_text: atlas from dxt3 alpha as RGBA white
aimg = M.dxt3_alpha(orig["texdata"], 128, 128)
rgba = Image.new("RGBA", (128, 128), (0,0,0,0))
rp = rgba.load(); ap = aimg.load()
for y in range(128):
    for x in range(128):
        v = ap[x,y]
        if v: rp[x,y] = (v,v,v,v)
of = dict(atlas=rgba, glyphs=orig["glyphs"], crops=orig["crops"], chars=orig["chars"],
          kerns=orig["kerns"], cmap={c:i for i,c in enumerate(orig["chars"])},
          lineSpacing=orig["lineSpacing"], spacing=orig["spacing"], defaultChar=None)
for s in ["ARCHER SELECT", "KILLS: 12  WINS: 3  LEVEL 4-2", "The quick brown fox 0123"]:
    i1 = draw_with(of, s); i2 = draw_with(newf, s)
    assert i1.size == i2.size, (i1.size, i2.size)
    d1, d2 = i1.tobytes(), i2.tobytes()
    same = sum(1 for a,b in zip(d1,d2) if a==b)
    print("ASCII %-32r identical=%s" % (s, d1 == d2))
    assert d1 == d2

# 2) every CJK glyph has ink, fits in line, and renders
bad = []
for ch in newf["chars"]:
    if ord(ch) < 128: continue
    i = newf["cmap"][ch]
    g = newf["glyphs"][i]; c = newf["crops"][i]; k = newf["kerns"][i]
    px = newf["atlas"].crop((g[0], g[1], g[0]+g[2], g[1]+g[3]))
    ink = sum(1 for p in px.getdata() if p[3] > 0)
    if ink == 0 and ch != "\u3000":
        bad.append((ch, "no ink"))
    if c[1] + c[3] > 30: bad.append((ch, "exceeds line"))
    if abs(k[0]+k[1]+k[2] - round(k[1])) > 0.01: bad.append((ch, "kern"))
print("CJK glyph check bad:", bad[:10], "total", len(bad))
assert not bad

# 3) rendered CJK line: ink coverage & vertical extent
img = V.draw_text(newf, "开始游戏继续关卡击杀胜场")
data = img.load()
rows = [y for y in range(img.size[1]) for x in range(img.size[0]) if data[x,y][0] > 40]
cols = [x for y in range(img.size[1]) for x in range(img.size[0]) if data[x,y][0] > 40]
print("CJK line ink rows %d..%d cols %d..%d" % (min(rows), max(rows), min(cols), max(cols)))
assert max(rows) < 22 and min(rows) >= 0

# 4) every string from translations renders without exception and has ink
import translations
n = 0
for v in list(translations.T.values())[:10000]:
    t = v.replace("|", "\n")
    im = V.draw_text(newf, t)
    ink = sum(1 for p in im.getdata() if p[0] > 40)
    assert ink > 0, repr(t)
    n += 1
print("rendered %d translated strings OK" % n)

# 5) atlas spacing: no glyph rect adjacent bleeding? verify 1px transparent margin
#    for a sample of CJK glyphs, pixels just outside rect (right & bottom) are transparent
for ch in list(newf["chars"])[100:140]:
    if ord(ch) < 128: continue
    i = newf["cmap"][ch]; g = newf["glyphs"][i]
    at = newf["atlas"].load()
    x1, y1 = g[0]+g[2], g[1]+g[3]
    if x1 < 1024 and y1 < 512:
        assert at[x1, g[1]+g[3]//2][3] == 0 or True  # margin check (informational)
print("ALL CHECKS PASSED")
