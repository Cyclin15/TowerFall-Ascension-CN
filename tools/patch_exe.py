# -*- coding: utf-8 -*-
"""
TowerFall.exe 原位汉化补丁：
直接在 .NET #US（User Strings）堆中替换字符串。
约束：新字符串的 UTF-16 字符数必须 <= 原字符串（堆槽位足够）。
除 #US 堆内容外，exe 逐字节不变 —— 不重写元数据、不动 IL。
"""
import struct, sys, shutil
from translations import T

EXE = r"D:\Steam\steamapps\common\TowerFall\TowerFall.exe"
BAK = r"D:\Steam\steamapps\common\TowerFall\CN_BACKUP\TowerFall.exe"

data = bytearray(open(BAK, 'rb').read())

# ---------- PE -> CLI -> metadata -> #US ----------
e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
opt_off = e_lfanew + 24
magic = struct.unpack_from('<H', data, opt_off)[0]
assert magic == 0x10b, 'not PE32'
num_sections = struct.unpack_from('<H', data, e_lfanew + 6)[0]
opt_size = struct.unpack_from('<H', data, e_lfanew + 20)[0]
dd_off = opt_off + 96  # data directories start (PE32)
cli_rva, cli_size = struct.unpack_from('<II', data, dd_off + 14 * 8)

sections = []
sec_off = opt_off + opt_size
for i in range(num_sections):
    o = sec_off + i * 40
    name = bytes(data[o:o+8]).rstrip(b'\0').decode()
    vsize, vaddr, rsize, roff = struct.unpack_from('<IIII', data, o + 8)
    sections.append((vaddr, max(vsize, rsize), roff))

def rva2off(rva):
    for vaddr, size, roff in sections:
        if vaddr <= rva < vaddr + size:
            return roff + (rva - vaddr)
    raise ValueError('bad rva %x' % rva)

cli_off = rva2off(cli_rva)
md_rva, md_size = struct.unpack_from('<II', data, cli_off + 8)
md_off = rva2off(md_rva)
assert struct.unpack_from('<I', data, md_off)[0] == 0x424A5342, 'bad metadata sig'

# metadata root: sig(4) + majver(2)+minver(2) + reserved(4) + version_len(4)
ver_len = struct.unpack_from('<I', data, md_off + 12)[0]
p = md_off + 16 + ver_len
p += 2  # flags
nstreams = struct.unpack_from('<H', data, p)[0]
p += 2
streams = {}
for i in range(nstreams):
    off, size = struct.unpack_from('<II', data, p)
    p += 8
    name_start = p
    while data[p] != 0:
        p += 1
    name = bytes(data[name_start:p]).decode()
    p += 1
    p = (p + 3) & ~3  # align
    streams[name] = (md_off + off, size)

us_off, us_size = streams['#US']
print('#US at file offset 0x%x size 0x%x' % (us_off, us_size))

# ---------- walk #US blobs ----------
def read_compressed(d, p):
    b0 = d[p]
    if b0 & 0x80 == 0:
        return b0, p + 1
    if b0 & 0x40 == 0:
        return ((b0 & 0x3f) << 8) | d[p+1], p + 2
    return ((b0 & 0x1f) << 24) | (d[p+1] << 16) | (d[p+2] << 8) | d[p+3], p + 4

def write_compressed(n):
    if n < 0x80:
        return bytes([n])
    if n < 0x4000:
        return bytes([0x80 | (n >> 8), n & 0xFF])
    return bytes([0xC0 | (n >> 24), (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF])

blobs = []  # (offset_of_length_prefix, total_len, old_prefix_len, string)
p = us_off + 1  # offset 0 is unused (empty entry)
end = us_off + us_size
while p < end:
    start = p
    n, q = read_compressed(data, p)
    if n == 0:
        blobs.append((start, 0, q - p, ''))
        p = q
        continue
    raw = bytes(data[q:q + n])
    flag = raw[-1]
    try:
        s = raw[:-1].decode('utf-16-le')
    except Exception:
        s = None
    blobs.append((start, n, q - p, s))
    p = q + n

print('blobs:', len(blobs))

# ---------- replace ----------
patched = 0
too_long = []
untranslated_hits = {}
for start, n, plen, s in blobs:
    if s is None or s == '':
        continue
    if s not in T:
        untranslated_hits[s] = untranslated_hits.get(s, 0) + 1
        continue
    new = T[s]
    raw = new.encode('utf-16-le')
    flag = 0x01 if any(ord(c) > 0x7f for c in new) else 0x00
    newblob = write_compressed(len(raw) + 1) + raw + bytes([flag])
    old_total = plen + n
    if len(newblob) > old_total:
        too_long.append((s, new, len(s), len(new)))
        continue
    data[start:start + old_total] = newblob + b'\x00' * (old_total - len(newblob))
    patched += 1

print('patched strings:', patched)
if too_long:
    print('!! TOO LONG (skipped):')
    for en, zh, le, lz in too_long:
        print('   %r (%d chars) -> %r (%d chars)' % (en, le, zh, lz))

# key check: which table entries were never used?
used = {s for _, _, _, s in blobs if s}
missing = [k for k in T if k not in used]
if missing:
    print('table entries NOT found in exe (no-op):')
    for m in missing:
        print('   %r' % m)

open(EXE, 'wb').write(data)
print('written:', EXE)

# leftover untranslated display-ish strings (for review)
import re
def displayish(s):
    if not s or any(ord(c) > 0x7e for c in s) or ord(s[0]) < 0x21: return False
    if len(s) < 3: return False
    if re.search(r'[/\\_.:<>{}\[\]"]', s): return False
    if '_' in s: return False
    if re.match(r'^[0-9A-F]{6}$', s): return False
    words = s.split()
    if len(words) == 1 and not (s.isupper() and s.isalpha()): return False
    return s.isupper() or (' ' in s and s[0].isupper())
left = sorted({s for _, _, _, s in blobs if s and displayish(s) and s not in T})
print('\n--- untranslated display-ish strings left (%d) ---' % len(left))
for s in left:
    print('   %r' % s)
