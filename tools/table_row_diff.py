#!/usr/bin/env python3
"""table_row_diff.py -- 同一张 `generated_*.dl_bin` 在**两个 build** 之间的差异（组 + 字节 + 行）。

为什么需要
    `build_diff.py` 只到"哪张表变了、哪一组大小变了"这一层（结构层）。
    真正落地要回答"改了哪个数、从多少改到多少"，所以补这一层：
      · 组层：`u32 组数 + 每组 LDLD(24B 头) + payload` —— `generated_*` 表的通用容器
      · 字节层：逐 4 字节报 旧u32/旧f32 → 新u32/新f32（值域可一键按补丁说明里的数字过滤）
      · 行层：给了 `--stride` 就把偏移换算成行号（`offset // stride`）

容器的两种形态
    A. `generated_*` 表：`u32 组数` + 每组 `"LDLD"|ver|gid|size|typ|unk`(24 B) + payload（本工具默认）
    B. 实体库：`u32 type | "LDLD" | ver | type | payload ...` 首尾相接（走 `--style chain`）

用法
    python tools/table_row_diff.py \
        --old refs/dlbin/plaintext-26251122/generated_projectile_settings.dl_bin \
        --new refs/dlbin/plaintext-26251122/generated_projectile_settings.dl_bin \
        [--stride 92] [--match 60,20,405,486] [--max 40] [--json-out x.json]

    --match 逗号分隔的数字：命中任一（旧值/新值/旧f32/新f32）就在输出里标 ★
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

HEAD = 24


def groups(data: bytes) -> list[dict]:
    n = struct.unpack_from("<I", data, 0)[0]
    off, out = 4, []
    for _ in range(n):
        if data[off:off + 4] != b"LDLD":
            raise SystemExit(f"✗ 组头不是 LDLD @{off:#x}")
        ver, gid, size, typ, unk = struct.unpack_from("<IIIII", data, off + 4)
        out.append({"at": off, "gid": gid, "size": size,
                    "payload": data[off + HEAD:off + HEAD + size]})
        off += HEAD + size
    if off != len(data):
        raise SystemExit(f"✗ 尾部残留 {len(data) - off} B")
    return out


def chain(data: bytes) -> list[dict]:
    out, pos = [], 0
    while True:
        j = data.find(b"LDLD", pos)
        if j < 0:
            break
        head = j - 4
        if head < 0:
            pos = j + 4
            continue
        tid = struct.unpack_from("<I", data, head)[0]
        ver, inner, payload = struct.unpack_from("<III", data, j + 4)
        if ver != 1 or inner != tid or head + 28 + payload > len(data):
            pos = j + 4
            continue
        out.append({"at": head, "gid": tid, "size": payload,
                    "payload": data[j + 16:j + 16 + payload]})
        pos = head + 28 + payload
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="同一张表两个 build 的组/字节/行级差异")
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--style", choices=("groups", "chain"), default="groups")
    ap.add_argument("--stride", type=int, default=0, help="行步长：用于把偏移换算成行号")
    ap.add_argument("--match", default="", help="逗号分隔数字：命中就标 ★")
    ap.add_argument("--max", type=int, default=40, help="每组最多展开多少处差异")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                  # noqa: BLE001
            pass

    old = pathlib.Path(a.old).read_bytes()
    new = pathlib.Path(a.new).read_bytes()
    parse = groups if a.style == "groups" else chain
    go, gn = parse(old), parse(new)
    print(f"旧 {len(old):,} B / {len(go)} 组    新 {len(new):,} B / {len(gn)} 组")
    want = {float(x) for x in a.match.split(",") if x.strip()}
    report = []
    for i in range(max(len(go), len(gn))):
        if i >= len(go) or i >= len(gn):
            print(f"[组 {i}] 组数不同")
            continue
        o, n = go[i], gn[i]
        same_size = o["size"] == n["size"]
        if same_size and o["payload"] == n["payload"]:
            continue
        print(f"\n[组 {i}] gid=0x{o['gid']:08X}  payload {o['size']:,} → {n['size']:,}")
        po, pn = o["payload"], n["payload"]
        rows = []
        for off in range(0, min(len(po), len(pn)) - 3, 4):
            uo = struct.unpack_from("<I", po, off)[0]
            un = struct.unpack_from("<I", pn, off)[0]
            if uo == un:
                continue
            fo = struct.unpack_from("<f", po, off)[0]
            fn = struct.unpack_from("<f", pn, off)[0]
            hit = bool(want & {float(uo), float(un), round(fo, 6), round(fn, 6)})
            row = (off // a.stride) if a.stride else None
            rows.append({"off": f"0x{off:05X}", "row": row, "old_u32": uo, "new_u32": un,
                         "old_f32": round(fo, 6), "new_f32": round(fn, 6), "hit": hit})
            if len(rows) <= a.max:
                loc = f" 行{row}" if row is not None else ""
                print(f"   +0x{off:05X}{loc}: {uo:#010x}({fo:.6g}) → {un:#010x}({fn:.6g})"
                      + ("  ★" if hit else ""))
        if len(rows) > a.max:
            print(f"   …（共 {len(rows)} 处，只展开前 {a.max} 处）")
        if not same_size:
            print(f"   长度 {len(po):,} → {len(pn):,}（{len(pn) - len(po):+,} B）")
        report.append({"group": i, "gid": f"0x{o['gid']:08X}",
                       "size_old": o["size"], "size_new": n["size"], "diffs": rows})
    if a.json_out:
        pathlib.Path(a.json_out).write_text(json.dumps(report, indent=1, ensure_ascii=False),
                                            encoding="utf-8")
        print(f"\n→ {a.json_out}")
    if not report:
        print("→ 两文件在组层与字节层完全一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
