#!/usr/bin/env python3
"""block_rows.py -- 把 `generated_entities.dl_bin` 里**某个组件块的全部行**打出来。

与 `entity_dump.py` 互补：
    entity_dump  给**实体键** → 它挂了哪些组件
    block_rows   给**组件类型** → 这个组件有哪几行、每行每字段的原始值（含 f32 读法）

为什么需要
    判断"某字段是不是节点名哈希/资源 id"要靠**整表对照**：同一个字段在 14 行里
    出现 2 个不同的值、且这两个值都等于某 unit 里的节点名 murmur32，才算证完。
    逐行 `entity_field_set.py show` 太慢，整表一次打出来才是对的粒度。

用法
    python tools/block_rows.py --block 0x67B29FFA [--width 10] [--json-out out/x.json]
    python tools/block_rows.py --block 0x67B29FFA --keys-only
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pod_rack_swap import parse_blocks          # noqa: E402
from typelib import TypeLib                     # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                            # noqa: BLE001
        pass

PLAIN = r"D:\mod\refs\dlbin\plaintext-26088801\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26088801\dl_library.dl_typelib"


def main() -> int:
    ap = argparse.ArgumentParser(description="组件块整表行值")
    ap.add_argument("--block", required=True, help="组件类型 id，如 0x67B29FFA = TransportComponentData")
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--width", type=int, default=10, help="每行显示多少个 4 字节槽")
    ap.add_argument("--keys-only", action="store_true")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    data = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    tid = int(str(a.block), 0)
    blocks = [b for b in parse_blocks(data) if b["type_id"] == tid]
    if len(blocks) != 1:
        raise SystemExit(f"✗ 期望恰好 1 个块 0x{tid:08X}，实际 {len(blocks)}")
    b = blocks[0]
    members = lib.members(tid)
    if len(members) != 2:
        raise SystemExit(f"✗ 块 0x{tid:08X} 不是「哈希图 + 行数组」形态")
    slots = members[0]["size64"]
    stride = lib.desc(members[1]["type_id"])[3]
    body = b["head"] + 28
    rows = members[1]["size64"] // stride

    keys = []
    for i in range(slots // 16):
        k, v = struct.unpack_from("<QI", data, body + 16 * i)
        if k:
            keys.append((k, v))
    print(f"块 0x{tid:08X}  槽 {slots // 16}  有效键 {len(keys)}  行 {rows}  stride {stride}")
    if a.keys_only:
        for k, v in sorted(keys, key=lambda kv: kv[1]):
            print(f"  row {v:<4} 0x{k:016X}")
        return 0

    head = "  " + " ".join(f"+0x{o:02X}".ljust(20) for o in range(0, min(stride, a.width * 4), 4))
    print(head)
    out = []
    for k, v in sorted(keys, key=lambda kv: kv[1]):
        off = body + slots + v * stride
        cells = []
        for o in range(0, min(stride, a.width * 4), 4):
            u = struct.unpack_from("<I", data, off + o)[0]
            f = struct.unpack_from("<f", data, off + o)[0]
            cells.append(f"{u}/{f:.4g}".ljust(20))
        print(f"row {v:<3} 0x{k:016X} " + " ".join(cells))
        out.append({"row": v, "key": f"0x{k:016X}", "raw": data[off:off + stride].hex()})
    if a.json_out:
        pathlib.Path(a.json_out).write_text(
            json.dumps({"block": f"0x{tid:08X}", "stride": stride, "rows": out},
                       indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"→ {a.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
