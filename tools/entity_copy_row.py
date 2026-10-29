#!/usr/bin/env python3
"""entity_copy_row.py -- 把**一个组件行**从一份 entities 明文整行拷到另一份（保内容哈希）。

为什么需要
    `entity_field_set.py` 一次只写一个 u32；`entity_batch_set.py` 要逐字段列出。
    做第三方 mod 的单变量移植时，经常是"把 A 文件里某实体某组件的**整行**搬过来" ——
    比如把 APC 版的 `InteractableComponentData` 搬到原版 TD-220 上。
    逐字段写既慢又容易漏，整行拷贝才是单变量。

做法（与 entity_field_set 同一套 tail 宿主）
    ① 两份文件都按 `LDLD` 解析块，`--block` 定位组件块，哈希图定位行
    ② 把 src 行的 stride 字节整段写到 dst 行
    ③ 末块 payload 尺寸 += pad+8、文件尾补零、校正字落在 len+pad（8 对齐）把内容哈希拉回原值

门禁
    G1 长度 = 原长 + pad + 8            G2 差异 ⊆ 目标行 ∪ 末块尺寸字段 ∪ 校正字
    G3 重算 Murmur == 原值              G4 目标行逐字节 == src 行
    G6 容器重解析自洽

用法
    python tools/entity_copy_row.py --src APC/entities-template.bin \\
        --block 0xFCCA29DB --key 0x16474112801385B6 --out dst.plain
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
TAIL = 8


def row_of(data: bytes, lib: TypeLib, tid: int, key: int):
    blocks = [b for b in parse_blocks(data) if b["type_id"] == tid]
    if len(blocks) != 1:
        raise SystemExit(f"✗ 期望 1 个块 0x{tid:08X}，实际 {len(blocks)}")
    b = blocks[0]
    ms = lib.members(tid)
    if len(ms) != 2:
        raise SystemExit(f"✗ 块 0x{tid:08X} 不是「哈希图 + 行数组」形态")
    slots = ms[0]["size64"]
    stride = lib.desc(ms[1]["type_id"])[3]
    body = b["head"] + 28
    for i in range(slots // 16):
        k, v = struct.unpack_from("<QI", data, body + 16 * i)
        if k == key:
            if v >= ms[1]["size64"] // stride:
                raise SystemExit(f"✗ 行号 {v} 越界")
            return body + slots + v * stride, stride, v
    raise SystemExit(f"✗ 键 0x{key:016X} 不在块 0x{tid:08X} 的哈希图里")


def main() -> int:
    ap = argparse.ArgumentParser(description="组件行整行拷贝（保内容哈希）")
    ap.add_argument("--src", required=True, help="来源 entities 明文（如 APC 模板）")
    ap.add_argument("--dst", default=PLAIN, help="目标 entities 明文（默认本 build 原版）")
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--block", required=True, help="组件类型 id")
    ap.add_argument("--key", required=True, help="实体键")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    lib = TypeLib(open(a.typelib, "rb").read())
    tid = int(str(a.block), 0)
    key = int(str(a.key), 0)
    src = pathlib.Path(a.src).read_bytes()
    original = pathlib.Path(a.dst).read_bytes()

    soff, stride, srow = row_of(src, lib, tid, key)
    off, stride2, drow = row_of(original, lib, tid, key)
    if stride != stride2:
        raise SystemExit(f"✗ stride 不一致 {stride} vs {stride2}")
    payload = src[soff:soff + stride]
    h0 = murmur64(original)

    pad = (8 - len(original) % 8) % 8
    tail_len = pad + TAIL
    word_at = len(original) + pad
    blocks = parse_blocks(original)
    last = blocks[-1]
    edited = bytearray(original)
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    edited += bytes(tail_len)
    edited[off:off + stride] = payload
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)

    checks = []
    checks.append(("G1 长度", len(edited) == len(original) + pad + TAIL,
                   f"{len(original)} -> {len(edited)}"))
    bad = [i for i in range(len(edited)) if i < len(original) and original[i] != edited[i]
           and not (off <= i < off + stride)]
    allowed = set(range(word_at, word_at + TAIL)) | {last["head"] + 16 + k for k in range(4)}
    bad = [i for i in bad if i not in allowed]
    checks.append(("G2 差异 ⊆ 目标行/尺寸/校正字", not bad, f"越界 {len(bad)}"))
    h1 = murmur64(bytes(edited))
    checks.append(("G3 内容哈希", h1 == h0, f"0x{h1:016X} vs 0x{h0:016X}"))
    got = bytes(edited[off:off + stride])
    checks.append(("G4 目标行 == src 行", got == payload, f"row {drow}"))
    try:
        n = check_container(bytes(edited))
        checks.append(("G6 容器自洽", True, f"{n} 块"))
    except Exception as exc:                                # noqa: BLE001
        checks.append(("G6 容器自洽", False, str(exc)))
    for name, ok, note in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {note}")
    if not all(ok for _, ok, _ in checks):
        raise SystemExit("✗ 门禁未过")
    pathlib.Path(a.out).write_bytes(bytes(edited))
    print(f"✓ {a.out}（{len(edited):,} B，块 0x{tid:08X} 实体 0x{key:016X} 行 {drow}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
