# -*- coding: utf-8 -*-
"""Validate generated XNB: re-parse mirroring XNA read path exactly; render
preview images simulating SpriteFont.InternalDraw (glyph at pen+kern.X+crop.X,
line_y+crop.Y; advance kern.X+Y+Z+spacing)."""
import struct, sys, os
from PIL import Image

def parse(path):
    data = open(path, "rb").read()
    assert data[:4] == b"XNBw" and data[4] == 5 and data[5] == 0
    assert struct.unpack_from("<I", data, 6)[0] == len(data), "filesize field"
    pos = [10]
    def r7():
        v = 0; s = 0
        while True:
            b = data[pos[0]]; pos[0] += 1
            v |= (b & 0x7f) << s
            if not (b & 0x80): return v
            s += 7
    def rs32():
        v = struct.unpack_from("<i", data, pos[0])[0]; pos[0] += 4; return v
    rc = r7(); readers = []
    for i in range(rc):
        slen = r7(); readers.append(data[pos[0]:pos[0]+slen].decode()); pos[0] += slen
        assert rs32() == 0
    assert r7() == 0 and r7() == 1 and r7() == 2
    fmt, w, h, mips = rs32(), rs32(), rs32(), rs32()
    assert (fmt, mips) == (0, 1), (fmt, mips)
    sz = rs32(); assert sz == w * h * 4
    px = data[pos[0]:pos[0]+sz]; pos[0] += sz
    def rl(idx):
        assert r7() == idx
        n = rs32()
        out = [struct.unpack_from("<4i", data, pos[0] + 16*i) for i in range(n)]
        pos[0] += 16 * n
        return out
    glyphs = rl(3); crops = rl(3)
    assert r7() == 5; nch = rs32()
    chars = []; p = pos[0]
    for i in range(nch):
        b0 = data[p]
        n = 1 if b0 < 0x80 else (2 if b0 < 0xE0 else (3 if b0 < 0xF0 else 4))
        chars.append(data[p:p+n].decode("utf-8")); p += n
    pos[0] = p
    lineSpacing = rs32()
    spacing = struct.unpack_from("<f", data, pos[0])[0]; pos[0] += 4
    assert r7() == 7; nk = rs32()
    kerns = [struct.unpack_from("<3f", data, pos[0] + 12*i) for i in range(nk)]
    pos[0] += 12 * nk
    flag = data[pos[0]]; pos[0] += 1
    dc = None
    if flag:
        b0 = data[pos[0]]
        n = 1 if b0 < 0x80 else (2 if b0 < 0xE0 else (3 if b0 < 0xF0 else 4))
        dc = data[pos[0]:pos[0]+n].decode(); pos[0] += n
    assert pos[0] == len(data), "trailing %d" % (len(data) - pos[0])
    assert len(glyphs) == len(crops) == len(chars) == len(kerns)
    # sorted for binary search
    cps = [ord(c) for c in chars]
    assert cps == sorted(cps), "chars not sorted!"
    assert len(set(cps)) == len(cps), "dup chars"
    # glyph rects inside atlas
    for g in glyphs:
        assert 0 <= g[0] and 0 <= g[1] and g[0]+g[2] <= w and g[1]+g[3] <= h, g
    atlas = Image.frombytes("RGBA", (w, h), px)
    cmap = {c: i for i, c in enumerate(chars)}
    return dict(atlas=atlas, glyphs=glyphs, crops=crops, chars=chars,
                kerns=kerns, cmap=cmap, lineSpacing=lineSpacing, spacing=spacing,
                defaultChar=dc)

def get_index(f, ch):
    i = f["cmap"].get(ch)
    if i is not None: return i
    d = f["defaultChar"]
    assert d is not None, "no default char and missing " + repr(ch)
    return f["cmap"][d]

def measure(f, text):
    x = 0.0; prev_z = 0.0; first = True
    for ch in text:
        k = f["kerns"][get_index(f, ch)]
        if not first:
            x += f["spacing"] + prev_z
        if first:
            x += max(k[0], 0.0)
        else:
            x += k[0]
        x += k[1]
        prev_z = k[2]
        first = False
    x += max(prev_z, 0.0)
    return x

def draw_text(f, text, x0=4, y0=2, scale=1):
    """Simulate InternalDraw. Returns RGBA image."""
    lines = text.split("\n")
    ls = f["lineSpacing"]
    W = int(max(measure(f, ln) for ln in lines)) + 12
    H = ls * len(lines) + 8
    img = Image.new("RGBA", (W, H), (16, 16, 28, 255))
    al = img.load()
    atlas = f["atlas"].load()
    for li, ln in enumerate(lines):
        x = 0.0; prev_z = 0.0; first = True
        y = li * ls
        for ch in ln:
            i = get_index(f, ch)
            k = f["kerns"][i]
            if not first:
                x += f["spacing"] + prev_z
            x += max(k[0], 0.0) if first else k[0]
            g = f["glyphs"][i]; c = f["crops"][i]
            dx = int(round(x)) + c[0] + x0
            dy = y + c[1] + y0
            for yy in range(g[3]):
                for xx in range(g[2]):
                    r, gg, b, a = atlas[g[0]+xx, g[1]+yy]
                    if a:
                        px_, py = dx+xx, dy+yy
                        if 0 <= px_ < W and 0 <= py < H:
                            # alpha blend over bg (white text)
                            na = a + (255 - a) * 0  # simple: paint white*alpha
                            al[px_, py] = (255 - a + (al[px_,py][0] * (255-a))//255,
                                           255 - a + (al[px_,py][1] * (255-a))//255,
                                           255 - a + (al[px_,py][2] * (255-a))//255, 255)
            x += k[1]
            prev_z = k[2]
            first = False
    return img

if __name__ == "__main__":
    samples = [
        "开始游戏",
        "继续 (3)",
        "箭矢寥寥无几|从墙壁和尸体上取回它们",
        "长按射击键瞄准|下蹲可取消",
        "ARCHER SELECT (Abc XYZ 0123)",
        "击杀：12  胜场：3  关卡 4-2",
        "队伍死斗模式！确定要清除数据吗？",
        "KILLS: 12  WINS: 3  LEVEL 4-2",
    ]
    for name in ("OpenSans", "MonocleDefault"):
        path = os.path.join(r"D:\Steam\tf_cn_work\out", name + ".xnb")
        f = parse(path)
        print("%s OK: atlas=%s glyphs=%d lineSpacing=%d spacing=%r default=%r"
              % (name, f["atlas"].size, len(f["chars"]), f["lineSpacing"], f["spacing"], f["defaultChar"]))
        # charset completeness vs all translated strings
        import translations
        need = set()
        for v in translations.T.values(): need |= set(v)
        for fn, tips in translations.XML_TIPS.items():
            for e, z in tips: need |= set(z)
        have = set(f["chars"])
        missing = {c for c in need if c not in have and c not in "\r\n\t"}
        assert not missing, "missing glyphs: %r" % missing
        # preview strip
        imgs = [draw_text(f, s) for s in samples]
        W = max(i.size[0] for i in imgs)
        H = sum(i.size[1] + 4 for i in imgs)
        strip = Image.new("RGBA", (W, H), (10, 10, 18, 255))
        y = 0
        for i in imgs:
            strip.paste(i, (0, y)); y += i.size[1] + 4
        strip = strip.resize((W*3, H*3), Image.NEAREST)
        outp = r"D:\Steam\tf_cn_work\out\preview_%s.png" % name
        strip.save(outp)
        print("  preview:", outp)
    # also render the atlas itself for inspection
    f = parse(r"D:\Steam\tf_cn_work\out\OpenSans.xnb")
    f["atlas"].resize((512, 256)).save(r"D:\Steam\tf_cn_work\out\atlas_preview.png")
    print("atlas preview saved")
