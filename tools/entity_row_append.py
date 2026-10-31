#!/usr/bin/env python3
"""entity_row_append.py -- 给实体组件块**追加一行**并把它挂到指定实体键（保内容哈希）。

为什么需要它
    全表实测：组件块里「行」是**实体私有存储** —— 每个块的行数 == 键数，**零共享**
    （Interactable 562 行 / 562 键，Unit 1719/1719，Wieldable 515/515，Magazine 276/276）。
    2026-10-31 实机教训：把 P-41 的键指向 Peacemaker 的 Interactable 行（共享行）+ 蓝图加组件后，
    **舱落地瞬间引擎卡死**。所以给实体补组件必须给它**自己的新行**，不能借行。

做法
    1. 定位组件块（28 B 实体头变体），校验「成员0=哈希图 / 成员1=行数组」且尺寸与 payload 吻合
    2. 从源实体（或源行号）复制整行内容，追加到**块 payload 末尾**（行号 = 原行数）
    3. 哈希图线性探测找空槽，写 `(实体键 → 新行号)`
    4. 目标块 payload 尺寸 += stride（后续块整体平移，仍保持 4 对齐）
    5. tail 宿主：末块 payload += pad+8、文件尾补零、校正字把内容哈希拉回原值

用法
    # 给 P-41 复制一条 Peacemaker 的 Interactable 行（新行 562），并把它挂到 P-41
    python tools/entity_row_append.py --plain X.plain --block 0xFCCA29DB \\
        --key 0xBDE1F2534280300D --copy-row-from 0x05E4E5C2DB6E44A2 --out Y.plain

门禁
    G1 长度 = 原长 + stride + pad + 8      G2 差异 ⊆ 新行 ∪ 哈希槽 ∪ 目标块尺寸 ∪ 末块尺寸 ∪ 校正字
    G3 重算 Murmur == 锚点                G4 新键解析到新行、行内容 == 源行
    G5 全部旧键解析不变、行内容不变        G6 容器块数不变、只有目标块 payload +stride
    G7 新键原本不存在
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash        # noqa: E402
from pod_rack_swap import parse_blocks, check_container     # noqa: E402
from typelib import TypeLib                                 # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                       # noqa: BLE001
        pass

PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
ANCHOR = 0x8E49771B181FFAA1
TAIL = 8


def block_of(data: bytes, tid: int) -> dict:
    hits = [b for b in parse_blocks(data) if b["type_id"] == tid]
    if len(hits) != 1:
        raise SystemExit(f"✗ 期望恰好 1 个块 0x{tid:08X}，实际 {len(hits)}")
    return hits[0]


def geom(lib: TypeLib, tid: int, payload: int) -> dict:
    ms = lib.members(tid)
    if len(ms) != 2:
        raise SystemExit(f"✗ 块 0x{tid:08X} 不是「哈希图 + 行数组」形态（成员 {len(ms)}）")
    hm = ms[0]["size64"]
    stride = lib.desc(ms[1]["type_id"])[3]
    if hm % 16 or not stride:
        raise SystemExit(f"✗ 几何不合法：哈希图 {hm} B / stride {stride}")
    if hm + ms[1]["size64"] != payload:
        raise SystemExit(f"✗ payload {payload} != 哈希图 {hm} + 行数组 {ms[1]['size64']}")
    return {"hm": hm, "stride": stride, "slots": hm // 16, "rows": ms[1]["size64"] // stride}


def find_slot(data: bytes, body: int, slots: int, key: int) -> tuple[int | None, int | None]:
    """线性探测（起点 key % slots）；返回 (命中槽, 行号) 或 (空槽, None)。"""
    for step in range(slots):
        slot = (key % slots + step) % slots
        k, v = struct.unpack_from("<QI", data, body + 16 * slot)
        if k == 0:
            return slot, None
        if k == key:
            return slot, v
    raise SystemExit("✗ 哈希图已满")


def row_of(data: bytes, body: int, g: dict, key: int) -> int | None:
    _, row = find_slot(data, body, g["slots"], key)
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description="实体组件块追加行并挂键（保内容哈希）")
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--block", required=True, help="组件块类型 id，如 0xFCCA29DB")
    ap.add_argument("--key", required=True, help="要挂上去的实体键")
    ap.add_argument("--copy-row-from", required=True, help="复制哪条实体键的整行")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    original = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(pathlib.Path(a.typelib).read_bytes())
    h0 = murmur64(original)
    if h0 != ANCHOR:
        raise SystemExit(f"✗ 明文哈希 0x{h0:016X} != 锚点 0x{ANCHOR:016X}（base 不干净）")

    tid = int(str(a.block), 0)
    key = int(str(a.key), 0)
    src_key = int(str(a.copy_row_from), 0)
    b = block_of(original, tid)
    body = b["head"] + 28
    g = geom(lib, tid, b["payload"])
    print(f"块 0x{tid:08X}  行 {g['rows']}  槽 {g['slots']}  stride {g['stride']} B  payload {b['payload']:,}")

    if row_of(original, body, g, key) is not None:
        raise SystemExit(f"✗ 键 0x{key:016X} 已在哈希图里")
    src_row = row_of(original, body, g, src_key)
    if src_row is None:
        raise SystemExit(f"✗ 源键 0x{src_key:016X} 不在表里")
    new_row = g["rows"]
    src_bytes = original[body + g["hm"] + src_row * g["stride"]:
                         body + g["hm"] + (src_row + 1) * g["stride"]]
    print(f"源键 0x{src_key:016X} → 行 {src_row}；新行 {new_row}（追加）")

    slot, _ = find_slot(original, body, g["slots"], key)
    print(f"哈希槽 {slot}（起点 {key % g['slots']}，探测 {(slot - key % g['slots']) % g['slots']} 步）")

    # 1) 在目标块 payload 末尾插入新行；2) 平移后重解析，改尺寸字段；3) tail 宿主
    ins_at = body + b["payload"]
    grown = bytearray(original[:ins_at]) + src_bytes + bytearray(original[ins_at:])
    struct.pack_into("<I", grown, b["head"] + 16, b["payload"] + g["stride"])
    struct.pack_into("<QII", grown, body + 16 * slot, key, new_row, 0)

    blocks2 = parse_blocks(bytes(grown))
    if len(blocks2) != len(parse_blocks(original)):
        raise SystemExit("✗ 插入后块数变了")
    pad = (8 - len(grown) % 8) % 8
    last = blocks2[-1]
    out = bytearray(grown) + bytes(pad + TAIL)
    struct.pack_into("<I", out, last["head"] + 16, last["payload"] + pad + TAIL)
    word_at = len(grown) + pad
    out[word_at:word_at + TAIL] = padding_word_for_hash(bytes(out), word_at, h0)
    print(f"校正字 @0x{word_at:X}   长度 {len(original):,} -> {len(out):,}")

    checks = []

    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    shift = g["stride"]
    # 插入点之后的旧字节整体平移；逐字节 diff 不能用，改判「前缀只在声明区域变 / 后缀整体平移」
    prefix_allowed = set(range(body + 16 * slot, body + 16 * slot + 16)) \
        | set(range(b["head"] + 16, b["head"] + 20))
    prefix_bad = [i for i in range(ins_at) if out[i] != original[i] and i not in prefix_allowed]
    last_field = set(range(last["head"] + 16, last["head"] + 20))
    suffix_bad = [i for i in range(len(original) - ins_at)
                  if out[ins_at + shift + i] != original[ins_at + i]
                  and (ins_at + shift + i) not in last_field]
    tail_ok = all(x == 0 for i, x in enumerate(out[len(grown):]) if not (word_at <= len(grown) + i < word_at + TAIL))
    check("G1 长度 = 原长 + stride + pad + 8", len(out) == len(original) + shift + pad + TAIL)
    check("G2 插入点前只在声明区域变", not prefix_bad, f"越界 {[hex(i) for i in prefix_bad[:5]]}")
    check("G2b 插入点后整体平移", not suffix_bad, f"越界 {[hex(i) for i in suffix_bad[:5]]}")
    check("G2c 追加区除校正字外全零", tail_ok)
    check("G3 重算哈希 == 锚点", murmur64(bytes(out)) == h0, f"0x{murmur64(bytes(out)):016X}")
    b2 = block_of(bytes(out), tid)
    body2 = b2["head"] + 28
    # 追加行后 typelib 的成员尺寸是旧的 —— 行数改由 payload 现算（hm 固定、stride 固定）
    g2 = {"hm": g["hm"], "stride": g["stride"], "slots": g["slots"],
          "rows": (b2["payload"] - g["hm"]) // g["stride"]}
    got_row = row_of(bytes(out), body2, g2, key)
    got_bytes = bytes(out[body2 + g2["hm"] + (got_row or 0) * g2["stride"]:
                          body2 + g2["hm"] + ((got_row or 0) + 1) * g2["stride"]]) if got_row is not None else b""
    check("G4 新键→新行、行内容 == 源行", got_row == new_row and got_bytes == src_bytes,
          f"行 {got_row}")
    old_ok = True
    for s in range(g["slots"]):
        k, v = struct.unpack_from("<QI", original, body + 16 * s)
        if not k:
            continue
        if row_of(bytes(out), body2, g2, k) != v:
            old_ok = False
            break
    check("G5 全部旧键解析不变", old_ok)
    check("G6 目标块 payload +stride", b2["payload"] == b["payload"] + shift,
          f"{b['payload']:,} -> {b2['payload']:,}")
    try:
        n = check_container(bytes(out))
        check("G6b 容器重解析自洽", n == len(blocks2), f"{n} 块")
    except Exception as exc:                                   # noqa: BLE001
        check("G6b 容器重解析自洽", False, str(exc))
    check("G7 新键原本不存在", row_of(original, body, g, key) is None)

    if not all(c for _, c in checks):
        print("\n✗ 门禁未过，未写出")
        return 1
    p = pathlib.Path(a.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(bytes(out))
    print(f"\n✓ 全部门禁通过 → {p}（{len(out):,} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
