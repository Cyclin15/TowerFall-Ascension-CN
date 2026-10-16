# -*- coding: utf-8 -*-
"""Empirically parse a SpriteFont XNB (XNA4, uncompressed, platform 'w').

Layout hypothesis (to be verified by exact byte consumption):
  0..2  "XNB"
  3     platform 'w'
  4     version 5
  5     flags 0x00 (uncompressed)
  6..9  u32 file size
  10..  7bit readerCount; each reader: 7bit-len string + u32 version
        7bit sharedResourceCount
        then SpriteFontReader payload:
          Texture2D: u32 surfaceFormat, u32 w, u32 h, u32 mipCount,
                     per mip: u32 dataSize + bytes
          s32 glyphCount + rects (x,y,w,h s32)
          s32 cropCount  + rects
          s32 charCount  + chars (u16 each)
          s32 kernCount  + (u16 char, 3 floats) triples  [or 3 lists?]
          u16 defaultChar, f32 spacing, s32 lineSpacing
"""
import struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\Steam\steamapps\common\TowerFall\CN_BACKUP\OpenSans.xnb"
data = open(path, "rb").read()
print("file:", path)
print("size on disk:", len(data))

assert data[:3] == b"XNB"
platform = data[3:4]
version, flags = data[4], data[5]
filesize = struct.unpack_from("<I", data, 6)[0]
print("platform %r version %d flags 0x%02x filesize %d" % (platform, version, flags, filesize))
assert filesize == len(data), "size field mismatch"

pos = 10

def read_7bit(d, p):
    v = 0; shift = 0
    while True:
        b = d[p]; p += 1
        v |= (b & 0x7f) << shift
        if not (b & 0x80): return v, p
        shift += 7

reader_count, pos = read_7bit(data, pos)
print("readerCount: %d" % reader_count)
for i in range(reader_count):
    slen, pos = read_7bit(data, pos)
    name = data[pos:pos+slen].decode("utf-8")
    pos += slen
    rv = struct.unpack_from("<i", data, pos)[0]; pos += 4
    print("  reader[%d] v%d: %s" % (i, rv, name))

shared, pos = read_7bit(data, pos)
print("sharedResourceCount:", shared)

# --- Texture2D ---
sf, w, h, mips = struct.unpack_from("<4I", data, pos); pos += 16
print("texture: format=%d w=%d h=%d mips=%d" % (sf, w, h, mips))
total_tex = 0
for m in range(mips):
    (sz,) = struct.unpack_from("<I", data, pos); pos += 4
    print("  mip[%d]: %d bytes" % (m, sz))
    pos += sz
    total_tex += sz
    if m == 0:
        assert sz == w * h * 4, "not 32bpp color"

# --- glyph rects ---
def read_rect(d, p):
    x, y, ww, hh = struct.unpack_from("<4i", d, p)
    return (x, y, ww, hh), p + 16

(n,) = struct.unpack_from("<i", data, pos); pos += 4
glyphs = []
for i in range(n):
    r, pos = read_rect(data, pos); glyphs.append(r)
print("glyphs:", n, "first:", glyphs[0], "last:", glyphs[-1])

(n,) = struct.unpack_from("<i", data, pos); pos += 4
crops = []
for i in range(n):
    r, pos = read_rect(data, pos); crops.append(r)
print("croppings:", n, "first:", crops[0])

# characters: try u16 each
(n,) = struct.unpack_from("<i", data, pos); pos += 4
chars = []
for i in range(n):
    (c,) = struct.unpack_from("<H", data, pos); pos += 2
    chars.append(c)
print("chars:", n)
print("first 16:", [chr(c) for c in chars[:16]])
print("last 16:", [chr(c) for c in chars[-16:]])

# kerning: try (count, then triples of u16+3f)
(n,) = struct.unpack_from("<i", data, pos); pos += 4
kerns = []
for i in range(n):
    (c,) = struct.unpack_from("<H", data, pos); pos += 2
    l, wd, r = struct.unpack_from("<3f", data, pos); pos += 12
    kerns.append((c, l, wd, r))
print("kerning:", n, "first:", (chr(kerns[0][0]),) + tuple(round(x,2) for x in kerns[0][1:]))

(dc,) = struct.unpack_from("<H", data, pos); pos += 2
(spacing,) = struct.unpack_from("<f", data, pos); pos += 4
(lineSpacing,) = struct.unpack_from("<i", data, pos); pos += 4
print("defaultChar: %r spacing: %r lineSpacing: %d" % (chr(dc) if dc else None, spacing, lineSpacing))

print("consumed: %d / %d  remaining: %d" % (pos, len(data), len(data) - pos))
