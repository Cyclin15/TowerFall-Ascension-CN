# -*- coding: utf-8 -*-
import struct, sys

def parse(path):
    data = open(path, "rb").read()
    print("=== %s size %d ===" % (path.split("\\")[-1], len(data)))
    assert data[:4] == b"XNBw" and data[4] == 5 and data[5] == 0
    assert struct.unpack_from("<I", data, 6)[0] == len(data)
    pos = 10
    def r7(p):
        v = 0; s = 0
        while True:
            b = data[p]; p += 1
            v |= (b & 0x7f) << s
            if not (b & 0x80): return v, p
            s += 7
    def rs32(p): return struct.unpack_from("<i", data, p)[0], p + 4
    rc, pos = r7(pos)
    readers = []
    for i in range(rc):
        slen, pos = r7(pos)
        readers.append(data[pos:pos+slen].decode("utf-8")); pos += slen
        _v, pos = rs32(pos)
    shared, pos = r7(pos)
    root, pos = r7(pos)
    tex, pos = r7(pos)
    fmt, pos = rs32(pos); w, pos = rs32(pos); h, pos = rs32(pos); mips, pos = rs32(pos)
    print("readers=%d shared=%d root=%d tex=%d | tex fmt=%d %dx%d mips=%d" % (rc, shared, root, tex, fmt, w, h, mips))
    assert (rc, shared, root, tex, fmt, mips) == (8, 0, 1, 2, 5, 1)
    sizes = []
    for m in range(mips):
        sz, pos = rs32(pos); sizes.append(sz)
    texdata = data[pos:pos+sizes[0]]; pos += sizes[0]
    def rects(p):
        idx, p = r7(p); cnt, p = rs32(p)
        out = []
        for i in range(cnt):
            out.append(struct.unpack_from("<4i", data, p)); p += 16
        return idx, out, p
    gi, glyphs, pos = rects(pos)
    ci, crops, pos = rects(pos)
    chi, pos = r7(pos); nchars, pos = rs32(pos)
    chars = []
    # UTF-8 variable-length chars via BinaryReader.ReadChar semantics
    end = pos
    # decode nchars UTF-8 chars
    p = pos
    for i in range(nchars):
        b0 = data[p]
        if b0 < 0x80: p += 1
        elif b0 < 0xE0: p += 2
        elif b0 < 0xF0: p += 3
        else: p += 4
    chars_bytes = data[pos:p]; pos = p
    chars = chars_bytes.decode("utf-8")
    lineSpacing, pos = rs32(pos)
    (spacing,) = struct.unpack_from("<f", data, pos); pos += 4
    ki, pos = r7(pos); nkern, pos = rs32(pos)
    kerns = []
    for i in range(nkern):
        kerns.append(struct.unpack_from("<3f", data, pos)); pos += 12
    print("listIdx: glyphs=%d crops=%d chars=%d kern=%d" % (gi, ci, chi, ki))
    print("counts: glyphs=%d crops=%d chars=%d kerns=%d" % (len(glyphs), len(crops), len(chars), len(kerns)))
    print("lineSpacing=%d spacing=%r" % (lineSpacing, spacing))
    flag = data[pos]; pos += 1
    if flag:
        # ReadChar = UTF-8
        b0 = data[pos]; n = 1 if b0 < 0x80 else (2 if b0 < 0xE0 else (3 if b0 < 0xF0 else 4))
        dc = data[pos:pos+n].decode("utf-8"); pos += n
    else:
        dc = None
    print("defaultChar:", repr(dc))
    print("consumed %d / %d remaining %d  %s" % (pos, len(data), len(data)-pos, "OK" if pos == len(data) else "MISMATCH"))
    assert pos == len(data)
    # sample char stats
    print("chars: %r .. %r" % (chars[:8], chars[-8:]))
    # glyph size stats
    hs = sorted(set(r[3] for r in glyphs))
    print("glyph heights:", hs)
    ys = sorted(set(r[1] for r in crops))
    print("crop Y range: %d..%d" % (ys[0], ys[-1]))
    return dict(readers=readers, fmt=fmt, w=w, h=h, texdata=texdata, glyphs=glyphs,
                crops=crops, chars=chars, kerns=kerns, lineSpacing=lineSpacing,
                spacing=spacing, defaultChar=dc)

for f in [r"D:\Steam\steamapps\common\TowerFall\CN_BACKUP\OpenSans.xnb",
          r"D:\Steam\steamapps\common\TowerFall\CN_BACKUP\MonocleDefault.xnb"]:
    parse(f)
