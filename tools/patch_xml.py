# -*- coding: utf-8 -*-
"""Patch questTips.xml / versusTips.xml with Chinese translations.
Reads originals from CN_BACKUP, writes translated copies into the game dir.
Preserves UTF-8 BOM and structure; only <text>...</text> contents change.
"""
import re, os, shutil
import translations

BAK = r"D:\Steam\steamapps\common\TowerFall\CN_BACKUP"
GAME = r"D:\Steam\steamapps\common\TowerFall\Content\Atlas\GameData"

for fname in ("questTips.xml", "versusTips.xml"):
    src = os.path.join(BAK, fname)
    dst = os.path.join(GAME, fname)
    with open(src, "rb") as f:
        raw = f.read()
    assert raw.startswith(b"\xef\xbb\xbf"), fname + " missing BOM"
    text = raw.decode("utf-8")

    table = dict(translations.XML_TIPS[fname])
    count = 0
    def repl(m):
        global count
        inner = m.group(1)
        if inner in table:
            count += 1
            return "<text>" + table[inner] + "</text>"
        return m.group(0)
    new = re.sub(r"<text>(.*?)</text>", repl, text, flags=re.S)

    miss = [e for e in table if e not in text]
    with open(dst, "wb") as f:
        f.write(new.encode("utf-8"))
    print(fname, "patched:", count, "of", len(table), "missing:", miss)
    assert not miss and count >= len(table), "not all tips patched"
    assert new.startswith("\ufeff")
print("done")
