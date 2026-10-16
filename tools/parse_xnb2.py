# -*- coding: utf-8 -*-
"""Parse SpriteFont XNB with corrected layout:
  header(10) | 7bit readerCount | {7bit-len string + s32 version} * N | 7bit sharedCount
  | 7bit rootReaderIndex (1-based)
  | SpriteFont payload:
      7bit texReaderIndex -> s32 format,w,h,mips; per mip: s32 size + data
      7bit idx -> s32 count + rects (glyphs)
      7bit idx -> s32 count + rects (croppings)
      7bit idx -> s32 count + chars (u16?)
      7bit idx -> s32 count + 3f32 (kerning)
      nullable char (flag byte + char?), f32 spacing, s32 lineSpacing
  then shared resources (count 0 here) -> must land exactly on EOF
"""
import struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else r"D:\Steam\steamapps\common\TowerFall\CN_BACKUP\OpenSans.xnb"
data = open(path, "rb").read()
print("file:", path, "size:", len(data))
assert data[:3] == b"XNB" and data[3:4] == b"w" and data[4] == 5 and data[5] == 0
filesize = struct.unpack_from("<I", data, 6)[0]
assert filesize == len(data)

pos = 10
def r7(d, p):
    v = 0; s = 0
    while True:
        b = d[p]; p += 1
        v |= (b & 0x7f) << s
        if not (b & 0x80): return v, p
        s += 7

def rs32(d, p):
    return struct.unpack_from("<i", d, p)[0], p + 4

reader_count, pos = r7(data, pos)
readers = []
for i in range(reader_count):
    slen, pos = r7(data, pos)
    name = data[pos:pos+slen].decode("utf-8"); pos += slen
    ver, pos = rs32(data, pos)
    readers.append(name)
    print("reader[%d] v%d: %.70s..." % (i, ver, name))
shared, pos = r7(data, pos)
print("sharedCount:", shared)

# indexed hex window around object start
print("bytes %d..%d:" % (pos, pos+40))
print(" ".join("%02x" % b for b in data[pos:pos+40]))

root_idx, pos = r7(data, pos)
print("root readerIndex:", root_idx, "->", readers[root_idx-1].split(',')[0].split('.')[-1])
assert root_idx == 1

# texture
tex_idx, pos = r7(data, pos)
print("texture readerIndex:", tex_idx, "->", readers[tex_idx-1].split(',')[0].split('.')[-1])
assert tex_idx == 2
fmt, pos = rs32(data, pos); w, pos = rs32(data, pos); h, pos = rs32(data, pos); mips, pos = rs32(data, pos)
print("texture: format=%d w=%d h=%d mips=%d" % (fmt, w, h, mips))
for m in range(mips):
    sz, pos = rs32(data, pos)
    print("  mip[%d] size=%d (pos %d..%d)" % (m, sz, pos, pos+sz))
    pos += sz

def read_list_rects(tag):
    global pos
    idx, pos = r7(data, pos)
    cnt, pos = rs32(data, pos)
    out = []
    for i in range(cnt):
        x, y, ww, hh = struct.unpack_from("<4i", data, pos); pos += 16
        out.append((x, y, ww, hh))
    print("%s: idx=%d count=%d first=%s last=%s" % (tag, idx, cnt, out[0], out[-1]))
    return out

glyphs = read_list_rects("glyphs")
crops   = read_list_rects("croppings")

# chars
idx, pos = r7(data, pos)
cnt, pos = rs32(data, pos)
chars = []
for i in range(cnt):
    (c,) = struct.unpack_from("<H", data, pos); pos += 2
    chars.append(c)
print("chars: idx=%d count=%d first=%r last=%r" % (idx, cnt, chr(chars[0]), chr(chars[-1])))

# kerning
idx, pos = r7(data, pos)
cnt, pos = rs32(data, pos)
kerns = []
for i in range(cnt):
    l, wd, r = struct.unpack_from("<3f", data, pos); pos += 12
    kerns.append((l, wd, r))
print("kerning: idx=%d count=%d first=%s" % (idx, cnt, tuple(round(x, 2) for x in kerns[0])))
assert len(chars) == len(kerns) == len(glyphs)

# nullable default char
flag = data[pos]; pos += 1
print("defaultChar flag:", flag)
if flag == 1:
    (dc,) = struct.unpack_from("<H", data, pos); pos += 2
    print("  defaultChar:", repr(chr(dc)))
(spacing,) = struct.unpack_from("<f", data, pos); pos += 4
lineSpacing, pos = rs32(data, pos)
print("spacing:", spacing, "lineSpacing:", lineSpacing)
print("consumed %d / %d, remaining %d" % (pos, len(data), len(data) - pos))
if pos != len(data):
    print("tail hex:", " ".join("%02x" % b for b in data[pos:pos+64]))
