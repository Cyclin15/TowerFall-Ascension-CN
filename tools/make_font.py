# -*- coding: utf-8 -*-
"""Generate CJK-capable SpriteFont XNBs for TowerFall Ascension.

Format (verified against GAC XNA 4.0 IL):
  header: "XNBw" 05 00 u32FileSize
  7bit readerCount(8) | {7bit-len str + s32 version} * 8 | 7bit sharedCount(0)
  7bit rootIdx(1)
  7bit texIdx(2) | s32 format s32 w s32 h s32 mips | {s32 size + bytes}
  7bit(3) s32 n + n*4*s32 glyph rects
  7bit(3) s32 n + n*4*s32 crop rects
  7bit(5) s32 n + UTF-8 chars (BinaryReader.ReadChar semantics)
  s32 lineSpacing | f32 spacing
  7bit(7) s32 n + n*3*f32 kerning
  nullable char: byte 1 + UTF-8 char

Texture: original is DXT3 128x128 (SurfaceFormat 5); we emit SurfaceFormat
Color (0) RGBA, premultiplied white ink (byte-order safe).

ASCII glyphs are reused pixel-identical: the decoded original 128x128 atlas
is pasted at (0,0) and the original glyph rects are kept unchanged. CJK
glyphs are shelf-packed after x=132.
"""
import struct, sys, os
import translations
from PIL import Image, ImageFont, ImageDraw

BAK = r"D:\Steam\steamapps\common\TowerFall\CN_BACKUP"
GAME = r"D:\Steam\steamapps\common\TowerFall\Content\Misc"
OUT = r"D:\Steam\tf_cn_work\out"
os.makedirs(OUT, exist_ok=True)

READERS = [
 "Microsoft.Xna.Framework.Content.SpriteFontReader, Microsoft.Xna.Framework.Graphics, Version=4.0.0.0, Culture=neutral, PublicKeyToken=842cf8be1de50553",
 "Microsoft.Xna.Framework.Content.Texture2DReader, Microsoft.Xna.Framework.Graphics, Version=4.0.0.0, Culture=neutral, PublicKeyToken=842cf8be1de50553",
 "Microsoft.Xna.Framework.Content.ListReader`1[[Microsoft.Xna.Framework.Rectangle, Microsoft.Xna.Framework, Version=4.0.0.0, Culture=neutral, PublicKeyToken=842cf8be1de50553]]",
 "Microsoft.Xna.Framework.Content.RectangleReader",
 "Microsoft.Xna.Framework.Content.ListReader`1[[System.Char, mscorlib, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089]]",
 "Microsoft.Xna.Framework.Content.CharReader",
 "Microsoft.Xna.Framework.Content.ListReader`1[[Microsoft.Xna.Framework.Vector3, Microsoft.Xna.Framework, Version=4.0.0.0, Culture=neutral, PublicKeyToken=842cf8be1de50553]]",
 "Microsoft.Xna.Framework.Content.Vector3Reader",
]
# sanity: identical to originals
ORIG_READERS = None  # filled from parse

# ---------------- parse original ----------------
def parse_original(path):
    data = open(path, "rb").read()
    assert data[:4] == b"XNBw" and data[4] == 5 and data[5] == 0
    assert struct.unpack_from("<I", data, 6)[0] == len(data)
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
        slen = r7()
        readers.append(data[pos[0]:pos[0]+slen].decode("utf-8")); pos[0] += slen
        assert rs32() == 0
    assert r7() == 0   # shared
    assert r7() == 1   # root
    assert r7() == 2   # texture reader idx
    fmt = rs32(); w = rs32(); h = rs32(); mips = rs32()
    assert (fmt, mips) == (5, 1)
    texsz = rs32()
    texdata = data[pos[0]:pos[0]+texsz]; pos[0] += texsz
    def rectlist():
        idx = r7(); assert idx in (3, 5, 7)
        n = rs32(); out = []
        for i in range(n):
            out.append(struct.unpack_from("<4i", data, pos[0])); pos[0] += 16
        return idx, out
    _, glyphs = rectlist()
    _, crops = rectlist()
    ci = r7(); nch = rs32()
    # UTF-8 variable length
    chars = []
    p = pos[0]
    for i in range(nch):
        b0 = data[p]
        n = 1 if b0 < 0x80 else (2 if b0 < 0xE0 else (3 if b0 < 0xF0 else 4))
        chars.append(data[p:p+n].decode("utf-8")); p += n
    pos[0] = p
    lineSpacing = rs32()
    spacing = struct.unpack_from("<f", data, pos[0])[0]; pos[0] += 4
    ki = r7(); nk = rs32()
    kerns = []
    for i in range(nk):
        kerns.append(struct.unpack_from("<3f", data, pos[0])); pos[0] += 12
    hasdef = data[pos[0]]; pos[0] += 1
    defaultChar = None
    if hasdef:
        b0 = data[pos[0]]
        n = 1 if b0 < 0x80 else (2 if b0 < 0xE0 else (3 if b0 < 0xF0 else 4))
        defaultChar = data[pos[0]:pos[0]+n].decode("utf-8"); pos[0] += n
    assert pos[0] == len(data), "trailing bytes"
    return dict(readers=readers, w=w, h=h, texdata=texdata, glyphs=glyphs,
                crops=crops, chars=chars, kerns=kerns,
                lineSpacing=lineSpacing, spacing=spacing)

def dxt3_alpha(texdata, w, h):
    """Return L-mode coverage image of a DXT3 texture (alpha nibbles)."""
    img = Image.new("L", (w, h))
    px = img.load()
    bw, bh = w // 4, h // 4
    off = 0
    for by in range(bh):
        for bx in range(bw):
            # 8 bytes alpha (16 nibbles), 4 bytes c0/c1, 4 bytes idx (ignored)
            for i in range(16):
                byte = texdata[off + (i // 2)]
                nib = (byte & 0x0F) if (i % 2 == 0) else (byte >> 4)
                x = bx * 4 + (i % 4)
                y = by * 4 + (i // 4)
                px[x, y] = nib * 17
            off += 16
    assert off == len(texdata)
    return img

# ---------------- charset ----------------
EXTRA = set("，。！？；：、·…—～（）《》〈〉【】〔〕“”‘’￥％＋－＝×÷°①②③④⑤⑥⑦⑧⑨⑩　")

def collect_charset():
    s = set()
    for v in translations.T.values():
        s |= set(v)
    for fname, tips in translations.XML_TIPS.items():
        for e, z in tips:
            s |= set(z)
    s |= EXTRA
    s = {c for c in s if c not in "\r\n\t"}
    ascii_set = {chr(c) for c in range(0x20, 0x7F)}
    return ascii_set | s

# ---------------- CJK render ----------------
_FONT_CACHE = {}
def render_cjk(charset, ascii_set, size=18):
    """Render CJK/fullwidth glyphs with SimHei. Returns {ch: (Image, cropX, advance)}"""
    for cand in [r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc"]:
        if os.path.exists(cand):
            path = cand; break
    else:
        raise SystemExit("no chinese font found")
    if size in _FONT_CACHE:
        font = _FONT_CACHE[size]
    else:
        font = ImageFont.truetype(path, size)
        _FONT_CACHE[size] = font
    SIZE = size
    font = ImageFont.truetype(path, SIZE)
    out = {}
    for ch in sorted(charset - ascii_set):
        if ch == "\u3000":  # ideographic space: empty glyph, em advance
            out[ch] = (Image.new("L", (1, 1), 0), 0, float(SIZE))
            continue
        bbox = font.getbbox(ch)
        if bbox is None or bbox[3] <= bbox[1] and bbox[2] <= bbox[0]:
            continue
        mask = font.getmask(ch, mode="L")
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= 0 or h <= 0:
            continue
        # getmask is already ink-cropped: size == (bbox.w, bbox.h)
        im = Image.frombytes("L", mask.size, bytes(mask))
        assert im.size == (w, h), (ch, bbox, mask.size)
        adv = font.getlength(ch)
        out[ch] = (im, bbox[0], adv)
    return out, font, path

# ---------------- packing ----------------
def pack(atlas, cjk, start_x):
    """Shelf-pack cjk glyph images into atlas (RGBA, white premult). Returns {ch: (x, y, w, h)}"""
    items = sorted(cjk.items(), key=lambda kv: -kv[1][0].size[1])
    W, H = atlas.size
    x = start_x; y = 0; rowh = 0
    placed = {}
    PAD = 1
    for ch, (im, _, _) in items:
        w, h = im.size
        if x + w + PAD > W:
            x = start_x; y += rowh + PAD; rowh = 0
        if y + h > H:
            raise SystemExit("atlas too small")
        # write premultiplied white pixels
        a = im.load()
        ap = atlas.load()
        for yy in range(h):
            for xx in range(w):
                v = a[xx, yy]
                if v:
                    ap[x+xx, y+yy] = (v, v, v, v)
        placed[ch] = (x, y, w, h)
        x += w + PAD
        rowh = max(rowh, h)
    used_y = y + rowh
    return placed, used_y

# ---------------- XNB writer ----------------
def w7(out, v):
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return

def build_xnb(atlas, chars_data, lineSpacing, spacing, defaultChar):
    """chars_data: list of (ch, glyphRect, cropRect, kern) sorted by codepoint."""
    out = bytearray()
    out += b"XNBw\x05\x00"
    out += b"\x00\x00\x00\x00"  # filesize placeholder
    w7(out, 8)
    for r in READERS:
        b = r.encode("utf-8")
        w7(out, len(b)); out += b
        out += struct.pack("<i", 0)
    w7(out, 0)  # shared
    w7(out, 1)  # root idx
    w7(out, 2)  # texture reader idx
    W, H = atlas.size
    px = atlas.tobytes()  # RGBA
    out += struct.pack("<5i", 0, W, H, 1, len(px))
    out += px
    # glyphs
    w7(out, 3); out += struct.pack("<i", len(chars_data))
    for ch, g, c, k in chars_data:
        out += struct.pack("<4i", *g)
    w7(out, 3); out += struct.pack("<i", len(chars_data))
    for ch, g, c, k in chars_data:
        out += struct.pack("<4i", *c)
    w7(out, 5)
    chars_bytes = "".join(ch for ch, g, c, k in chars_data).encode("utf-8")
    out += struct.pack("<i", len(chars_data))
    out += chars_bytes
    out += struct.pack("<i", lineSpacing)
    out += struct.pack("<f", spacing)
    w7(out, 7); out += struct.pack("<i", len(chars_data))
    for ch, g, c, k in chars_data:
        out += struct.pack("<3f", *k)
    b = defaultChar.encode("utf-8")
    out.append(1); out += b
    struct.pack_into("<I", out, 6, len(out))
    return bytes(out)

# ---------------- main ----------------
def main():
    charset = collect_charset()
    ascii_set = {chr(c) for c in range(0x20, 0x7F)}
    # per-font CJK pixel size (Archer ASCII caps are only 6px tall)
    SPECS = {"Archer": 11, "OpenSans": 18, "MonocleDefault": 18}
    orig = {name: parse_original(os.path.join(BAK, name + ".xnb"))
            for name in SPECS}

    # render CJK at each needed size once
    cjk_by_size = {}
    for name, size in SPECS.items():
        if size not in cjk_by_size:
            cjk, font, fpath = render_cjk(charset, ascii_set, size)
            missing = (charset - ascii_set) - set(cjk)
            assert not missing, "unrenderable: %r" % missing
            cjk_by_size[size] = cjk
            print("rendered %d cjk glyphs @%dpx (%s)" % (len(cjk), size, fpath))

    for name, size in SPECS.items():
        o = orig[name]
        assert o["readers"] == READERS, name
        cjk_render = cjk_by_size[size]
        W, H = (512, 512) if size <= 12 else (1024, 512)
        if o["w"] > W: W = o["w"]
        atlas_img = dxt3_alpha(o["texdata"], o["w"], o["h"])
        atlas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pa = atlas.load(); oa = atlas_img.load()
        for y in range(o["h"]):
            for x in range(o["w"]):
                v = oa[x, y]
                if v:
                    pa[x, y] = (v, v, v, v)
        placed, used_y = pack(atlas, cjk_render, start_x=o["w"] + 4)
        assert used_y <= H, name + " atlas overflow"

        # baseline from 'H' ink (crop.Y + glyph height)
        iH = o["chars"].index("H")
        baseline = o["crops"][iH][1] + o["glyphs"][iH][3]
        print("%s: baseline=%d lineSpacing=%d atlas=%dx%d used_y=%d"
              % (name, baseline, o["lineSpacing"], W, H, used_y))

        chars_data = []
        for i, ch in enumerate(o["chars"]):
            chars_data.append((ch, o["glyphs"][i], o["crops"][i], o["kerns"][i]))
        for ch in sorted(cjk_render):
            im, bx, adv = cjk_render[ch]
            x, y, w, h = placed[ch]
            glyph = (x, y, w, h)
            crop = (bx, baseline + 1 - h, w, h)
            kern = (0.0, float(round(adv)), 0.0)
            chars_data.append((ch, glyph, crop, kern))
        chars_data.sort(key=lambda t: ord(t[0]))
        seen = set()
        for ch, _, _, _ in chars_data:
            assert ch not in seen, "dup " + ch
            seen.add(ch)

        blob = build_xnb(atlas, chars_data, o["lineSpacing"], o["spacing"], "？")
        open(os.path.join(OUT, name + ".xnb"), "wb").write(blob)
        print("%s: %d glyphs (%d ascii orig + %d cjk), %d bytes"
              % (name, len(chars_data), len(o["chars"]), len(cjk_render), len(blob)))
    print("written to", OUT)

if __name__ == "__main__":
    main()
