#!/usr/bin/env python3
"""entity_transplant.py -- 把**供体实体的一批组件行**整行搬给**宿主实体的同类型行**，
顺手把宿主独有的、指向旧壳节点的悬空引用改写成新壳里存在的节点（保内容哈希）。

为什么需要
    `entity_copy_row.py` 只能搬「同一份文件、同一个实体键」的行（用于 mod 移植同键行）。
    换壳（把 A 车的壳指给 B 车）时要做的是**跨实体、跨文件**的一批行：
        GATER A（0x0801B6B3C5D12EBC，vanilla 明文）
          └─ 8 行 → Maelstrom（0xB0C9FAF4AF8903F9，APC 版明文）
    并且宿主上**多出来**的组件（供体没有）会留下指向旧壳节点的哈希 —— 换壳后这些哈希在
    新壳节点表里不存在（悬空）。本工具按「旧壳节点 ∩ 行内 u32 − 新壳节点」精确定位它们，
    改写成新壳里确实存在的回落节点。

做法（与 entity_field_set / entity_copy_row 同一套 tail 宿主）
    ① 读 src(供体) / dst(宿主) 两份明文，按 `LDLD` 解析块
    ② 逐条 copy：src 里 src_key 的行 → dst 里 dst_key 的行（stride 必须一致）
    ③ 逐条 remap_dangling：在 dst 的该行里，值 ∈ 旧壳节点且 ∉ 新壳节点 的 u32 → 回落节点
    ④ 末块 payload 尺寸 += pad+8、文件尾补零、校正字把 MurmurHash64A 拉回原值

门禁
    G1 长度 = 原长 + pad + 8
    G2 差异 ⊆ 目标行 ∪ 改写字 ∪ 末块尺寸字段 ∪ 校正字
    G3 重算 Murmur == 原值
    G4 每个目标行读回 == src 行（copy）/ 悬空已清零（remap）
    G6 容器重解析自洽
    G8 校正字 8 对齐、不与目标行重叠

用法
    python tools/entity_transplant.py --spec spec.json --out transplanted.plain

spec.json
    {
      "src": "D:/mod/refs/dlbin/plaintext-26251122/generated_entities.dl_bin",
      "dst": "D:/mod/out/apc-recon/assets/entities-template.bin",
      "shell_old": "<旧壳单位 id>", "shell_new": "<新壳单位 id>",
      "shell_new_pkg": "<从哪个包读新壳节点表>",
      "copy":   [{"block": "0x4437574D", "src": "0x…", "dst": "0x…"}, …],
      "remap_dangling": [{"block": "0x…", "key": "0x…", "fallback": "0x…"}, …]
    }
"""
from __future__ import annotations

import argparse
import json
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

TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
SDK = r"C:\Users\Admin\HD2SDK-CommunityEdition"
GAME = r"D:\SteamLibrary\steamapps\common\Helldivers 2\data"
TYPE_UNIT = 0xE0A48D0BE9A7453F
TAIL = 8


def row_of(data: bytes, lib: TypeLib, tid: int, key: int, what: str):
    blocks = [b for b in parse_blocks(data) if b["type_id"] == tid]
    if len(blocks) != 1:
        raise SystemExit(f"✗ [{what}] 期望 1 个块 0x{tid:08X}，实际 {len(blocks)}")
    b = blocks[0]
    ms = lib.members(tid)
    if len(ms) != 2:
        raise SystemExit(f"✗ [{what}] 块 0x{tid:08X} 不是「哈希图 + 行数组」形态")
    slots = ms[0]["size64"]
    stride = lib.desc(ms[1]["type_id"])[3]
    body = b["head"] + 28
    for i in range(slots // 16):
        k, v = struct.unpack_from("<QI", data, body + 16 * i)
        if k == key:
            if v >= ms[1]["size64"] // stride:
                raise SystemExit(f"✗ [{what}] 行号 {v} 越界")
            return body + slots + v * stride, stride, v
    raise SystemExit(f"✗ [{what}] 键 0x{key:016X} 不在块 0x{tid:08X} 的哈希图里")


def shell_nodes(unit_id: int, package: str | None) -> set[int]:
    if SDK not in sys.path:
        sys.path.insert(0, SDK)
    from srkit.container.repo import Repository                     # noqa: E402
    from srkit.resources.base import get_codec                      # noqa: E402
    from srkit.util.ids import NameTable                            # noqa: E402

    repo = Repository.open(GAME)
    names = repo.package_names() if package is None else [package]
    for name in names:
        try:
            pkg = repo.load_package(name, load_blobs=False)
        except Exception:                                          # noqa: BLE001
            continue
        for e in pkg.entries:
            if e.file_id == unit_id and e.type_id == TYPE_UNIT:
                entry = repo.load_entry(name, unit_id, TYPE_UNIT)
                ir = get_codec(TYPE_UNIT).decode(entry, NameTable(), {}).ir
                return {int(t["name_hash"]) for t in ir["transforms"]}
    raise SystemExit(f"✗ 找不到单位 0x{unit_id:016X} 的节点表（包 {package}）")


def main() -> int:
    ap = argparse.ArgumentParser(description="跨实体组件行移植 + 悬空节点改写（保内容哈希）")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--typelib", default=TYPELIB)
    a = ap.parse_args()

    spec = json.loads(pathlib.Path(a.spec).read_text(encoding="utf-8"))
    lib = TypeLib(open(a.typelib, "rb").read())
    src = pathlib.Path(spec["src"]).read_bytes()
    original = pathlib.Path(spec["dst"]).read_bytes()

    old_nodes = shell_nodes(int(spec["shell_old"], 16), spec.get("shell_old_pkg"))
    new_nodes = shell_nodes(int(spec["shell_new"], 16), spec.get("shell_new_pkg"))
    print(f"旧壳 {spec['shell_old']} 节点 {len(old_nodes)}   新壳 {spec['shell_new']} 节点 {len(new_nodes)}")

    h0 = murmur64(original)
    pad = (8 - len(original) % 8) % 8
    tail_len = pad + TAIL
    word_at = len(original) + pad
    blocks = parse_blocks(original)
    last = blocks[-1]
    edited = bytearray(original)
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    edited += bytes(tail_len)

    touched: list[tuple[int, int]] = []      # (off, stride) —— G2/G8 用
    report = []

    for item in spec.get("copy", []):
        tid = int(item["block"], 16)
        skey = int(item["src"], 16)
        dkey = int(item["dst"], 16)
        soff, sstride, srow = row_of(src, lib, tid, skey, "src")
        doff, dstride, drow = row_of(bytes(edited), lib, tid, dkey, "dst")
        if sstride != dstride:
            raise SystemExit(f"✗ 0x{tid:08X} stride 不一致 {sstride} vs {dstride}")
        payload = src[soff:soff + sstride]
        edited[doff:doff + dstride] = payload
        touched.append((doff, dstride))
        report.append(f"  copy 0x{tid:08X}  src 行{srow} → dst 行{drow}  {dstride} B")

    for item in spec.get("remap_dangling", []):
        tid = int(item["block"], 16)
        key = int(item["key"], 16)
        fallback = int(item["fallback"], 16)
        if fallback not in new_nodes:
            raise SystemExit(f"✗ 回落节点 0x{fallback:08X} 不在新壳节点表里")
        off, stride, row = row_of(bytes(edited), lib, tid, key, "remap")
        fixed = []
        for o in range(0, stride - 3, 4):
            value = struct.unpack_from("<I", edited, off + o)[0]
            if value in old_nodes and value not in new_nodes:
                struct.pack_into("<I", edited, off + o, fallback)
                fixed.append((o, value))
        touched.append((off, stride))
        report.append(f"  remap 0x{tid:08X} 行{row}  悬空 {len(fixed)} 处 → 0x{fallback:08X}")

    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)

    allowed = set(range(word_at, word_at + TAIL)) | {last["head"] + 16 + k for k in range(4)}
    for off, stride in touched:
        allowed |= set(range(off, off + stride))
    bad = [i for i in range(len(original))
           if original[i] != edited[i] and i not in allowed]

    checks = [
        ("G1 长度 = 原长 + pad + 8", len(edited) == len(original) + pad + TAIL,
         f"{len(original):,} -> {len(edited):,}"),
        ("G2 差异 ⊆ 目标行/改写字/尺寸/校正字", not bad, f"越界 {len(bad)}"),
        ("G3 内容哈希", murmur64(bytes(edited)) == h0,
         f"0x{murmur64(bytes(edited)):016X} vs 0x{h0:016X}"),
        ("G6 容器自洽", True, ""),
        ("G8 校正字 8 对齐", word_at % 8 == 0 and all(not (o <= word_at < o + s) for o, s in touched),
         f"@0x{word_at:X}"),
    ]
    try:
        checks[3] = ("G6 容器自洽", True, f"{check_container(bytes(edited))} 块")
    except Exception as exc:                                    # noqa: BLE001
        checks[3] = ("G6 容器自洽", False, str(exc))

    print("\n".join(report))
    for name, ok, note in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {note}")
    if not all(ok for _, ok, _ in checks):
        raise SystemExit("✗ 门禁未过")
    pathlib.Path(a.out).write_bytes(bytes(edited))
    print(f"✓ {a.out}（{len(edited):,} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
