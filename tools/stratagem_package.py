#!/usr/bin/env python3
"""stratagem_package.py -- 改战备行的 **`+0xA8` / `+0xF8` 包声明字段**（u64），保住内容哈希。

为什么单独一个工具
    `stratagem_tune.py` 只认 `uses / callin / cooldown` 三个字段（都在 `+80/+84/+104`）。
    而「有限数量的跨包加载」要写的是 **`+0xA8` = toc 包 id（u64）** 与
    **`+0xF8` = 授予武器的 LoadoutEntry id（低 32 位有效）** —— 见
    `docs/engine/LIMITED-CROSS-PACKAGE-LOADING-26088801.md`。

哈希怎么保
    与 `stratagem_tune.py` 同一套：目标行改完后，在一个**语义惰性的 8 字节对齐零字**里
    解出校正字，使整份明文的 MurmurHash64A 回到原值。默认拿带 `(NOT USED)` 的战备行当宿主。

用法
    python tools/stratagem_package.py \\
        --plain refs/dlbin/plaintext-26251122/generated_stratagem_settings.dl_bin \\
        --row "REINFORCEMENT BEACON" --set-a8 0xB779A2F9D0928E03 \\
        --out out/stratagem_reinforce_gp20.plain

门禁
    G1 长度不变   G2 差异 ⊆ 目标行 ∪ 校正字 8 字节   G3 重算哈希 == 原值
    G4 字段读回 == 目标   G5 宿主行其余未变   G6 目标行其余未变
    G7 目标行身份字段（+0 type、+40/+44/+48 本地化 ID）未变
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

from murmur64 import murmur64, padding_word_for_hash      # noqa: E402
from stratagem_tune import STRIDE, groups, row_name      # noqa: E402
from table_dictionary import Dictionary                  # noqa: E402

IDENTITY = (0, 40, 44, 48, 52, 56)


def main() -> int:
    ap = argparse.ArgumentParser(description="战备行包声明字段写入（保内容哈希）")
    ap.add_argument("--plain", required=True)
    ap.add_argument("--row", required=True, help="目标行内部名子串，如 REINFORCEMENT BEACON")
    ap.add_argument("--set-a8", default=None, help="新的 +0xA8（u64 toc 包 id）")
    ap.add_argument("--set-f8", default=None, help="新的 +0xF8（u64，低 32 位有效）")
    ap.add_argument("--host", default="NOT USED", help="承载校正字的惰性行内部名子串")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    data = pathlib.Path(a.plain).read_bytes()
    typelib = pathlib.Path(a.plain).with_name("dl_library.dl_typelib")
    if not typelib.is_file():
        raise SystemExit(f"✗ 找不到 typelib（{typelib}）")
    dic = Dictionary(typelib.read_bytes(), {})
    h0 = murmur64(data)
    print(f"明文 {len(data):,} B  哈希=0x{h0:016X}")

    gs = groups(data, dic)
    rows = []
    for gi, g in enumerate(gs):
        for r in range(g["count"]):
            at = g["rows_at"] + r * STRIDE
            rows.append({"group": gi, "row": r, "at": at,
                         "type": struct.unpack_from("<I", data, at)[0],
                         "name": row_name(data, g, at)})

    def pick(needle, what):
        n = needle.strip().lower()
        exact = [x for x in rows if x["name"].lower() == n]
        cands = exact or [x for x in rows if n and n in x["name"].lower()]
        if len(cands) != 1:
            raise SystemExit(f"✗ {what} 不唯一/未命中：{len(cands)} 行 -> "
                             f"{[x['name'] for x in cands][:6]}")
        x = cands[0]
        print(f"  {what}：组{x['group']} 行{x['row']} type=0x{x['type']:X} {x['name']!r}")
        return x

    tgt = pick(a.row, "目标行")
    host = pick(a.host, "宿主行")
    if tgt["at"] == host["at"]:
        raise SystemExit("✗ 目标与宿主同一行")

    touched = []
    edited = bytearray(data)
    if a.set_a8 is not None:
        new = int(a.set_a8, 0)
        old = struct.unpack_from("<Q", edited, tgt["at"] + 0xA8)[0]
        struct.pack_into("<Q", edited, tgt["at"] + 0xA8, new)
        touched.append((0xA8, 8, old, new))
        print(f"  +0xA8 : 0x{old:016X} -> 0x{new:016X}")
    if a.set_f8 is not None:
        new = int(a.set_f8, 0)
        old = struct.unpack_from("<Q", edited, tgt["at"] + 0xF8)[0]
        struct.pack_into("<Q", edited, tgt["at"] + 0xF8, new)
        touched.append((0xF8, 8, old, new))
        print(f"  +0xF8 : 0x{old:016X} -> 0x{new:016X}")
    if not touched:
        raise SystemExit("✗ --set-a8 / --set-f8 至少给一个")

    # 找宿主行里 8 字节对齐的全零字
    word_at = None
    for o in range(0, STRIDE - 7, 4):
        pos = host["at"] + o
        if pos % 8 == 0 and struct.unpack_from("<Q", edited, pos)[0] == 0:
            word_at = pos
            break
    if word_at is None:
        raise SystemExit("✗ 宿主行里找不到 8 字节对齐的零字")
    word = padding_word_for_hash(bytes(edited), word_at, h0)
    edited[word_at:word_at + 8] = word
    print(f"  校正字 @0x{word_at:X}（宿主行 +0x{word_at - host['at']:X}）")
    edited = bytes(edited)

    ok = True

    def check(tag, cond, detail=""):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")
        ok = ok and cond

    allowed = set(range(tgt["at"], tgt["at"] + STRIDE)) | set(range(word_at, word_at + 8))
    diff = {i for i in range(len(data)) if data[i] != edited[i]}
    got = murmur64(edited)
    check("G1 长度不变", len(edited) == len(data), f"{len(data):,}")
    check("G2 差异 ⊆ 目标行 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)} 越界={[hex(i) for i in sorted(diff - allowed)[:6]]}")
    check("G3 重算哈希 == 原值", got == h0, f"0x{got:016X}")
    rd_ok = all(struct.unpack_from("<Q", edited, tgt["at"] + off)[0] == new
                for off, _w, _o, new in touched)
    check("G4 字段读回 == 目标", rd_ok)
    hs = host["at"]
    check("G5 宿主行其余未变",
          edited[hs:word_at] == data[hs:word_at] and
          edited[word_at + 8:hs + STRIDE] == data[word_at + 8:hs + STRIDE])
    setoffs = {o + k for o, w, _o2, _n in touched for k in range(w)}
    drift = [o for o in range(0, STRIDE, 4)
             if o not in setoffs and edited[tgt["at"] + o:tgt["at"] + o + 4]
             != data[tgt["at"] + o:tgt["at"] + o + 4]]
    check("G6 目标行其余未变", not drift, f"漂移={drift[:6]}")
    check("G7 身份字段未变",
          all(edited[tgt["at"] + o:tgt["at"] + o + 4] == data[tgt["at"] + o:tgt["at"] + o + 4]
              for o in IDENTITY))

    if not ok:
        print("\n✗ 门禁未全过，不写输出")
        return 1
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(edited)
    print(f"\n✓ 已写 {out}（{len(edited):,} B，哈希 0x{murmur64(edited):016X}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
