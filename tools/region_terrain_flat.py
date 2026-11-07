#!/usr/bin/env python3
"""region_terrain_flat.py — 改 `generated_region_settings` 的地形高度幅度（保哈希）。

背景
    `GenerationRegionSettings`（74 行 × 3272 B）里与「地形平坦程度」直接相关的字段（偏移已用
    类型库 + 线上 ZoneSettings/GenerationRegionSettings schema + 实测值三重对上）：

        +0x01C  subregion_generation_noise_frequency   f32  默认 4    子区域噪声频率
        +0x020  subregion_pure_randomness              f32  默认 0.1  纯随机占比
        +0x024  terrain_height_range                  f32  默认 25   主高度幅度（本 build 0..75）
        +0x028  global_terrain_height_noise_frequency  f32  默认 1
        +0x02C  global_terrain_height_range            f32  默认 0    宏观层幅度
        +0x030  zone_terrain_height_range              f32  默认 0    按 zone 的额外幅度
        +0x040  terrain_bottom_flat_margin             f32  默认 4    平地边缘余量
        +0x00C..+0x018  高/中/低/底部平原 四档权重

    把 `terrain_height_range` 压到很小（=1~2）就是「整张图削平」；不动别的字段是单变量实验。

链路
    game 文件 = sealed box(48 B) + 明文；明文 = u32 组数 + 74×LDLD(GenerationRegionSettings)
    + u32 0x0D + 13×LDLD(GenerationRegionGroup)。引擎校验的 `MurmurHash64A(明文)` 必须不变，
    所以借用**无主行**（不被任何 region 变体引用的行）里一个 8 字节对齐字做校正字。
    这里用 row 0 的 `+0x04C`（special_subregion_min_count/max_count，两 u32，无主行不读）。

用法
    # 只出明文（离线门禁）
    python tools/region_terrain_flat.py --plain <明文.dl_bin> --rows used --height 2 \\
        --out out/terrain/region_flat.plain.dl_bin

    # 顺带封装（需要 recipient.pk）
    python tools/region_terrain_flat.py --plain <明文.dl_bin> --rows used --height 2 \\
        --out out/terrain/region_flat.plain.dl_bin --seal refs/dlbin/keys/recipient.pk \\
        --sealed out/terrain/region_flat.sealed.dl_bin

    --rows 支持：`used`（46 行，被 34 个 region 变体列表引用的）、`all`（74 行）、
    以及逗号分隔的行号（如 `16,19,67`）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                       # noqa: BLE001
        pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from murmur64 import murmur64, padding_word_for_hash            # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROW_SIZE = 3272
LEVELGEN = ROOT / "out" / "planet" / "levelgen.json"

# 字段表（偏移都用 64-bit 记录布局，实测 size64 == 3272）
FIELDS = {
    "height": 0x024,          # terrain_height_range
    "global_range": 0x02C,    # global_terrain_height_range
    "zone_range": 0x030,      # zone_terrain_height_range
    "noise_freq": 0x01C,      # subregion_generation_noise_frequency
    "pure_rand": 0x020,       # subregion_pure_randomness
    "flat_margin": 0x040,     # terrain_bottom_flat_margin
    "water_ridge": 0x034,     # water_cutoff_ridge_level
    # 四档权重：高 / 中 / 低 / 底部平原
    "w_high": 0x00C, "w_mid": 0x010, "w_low": 0x014, "w_flat": 0x018,
    # 子区域高度档（SubRegionHeight 枚举，48 B 步长；权威布局见 filediver rawSubRegionSettings）
    "sub_type": 0x000, "sub_zone": 0x004, "sub_height_group": 0x010,
}

SUBREGION_BASE = 0x238
SUBREGION_STRIDE = 68
SUBREGION_COUNT = 16


def parse_blocks(data: bytes) -> tuple[list[dict], int]:
    """u32 组数 + 连续 LDLD 组；返回 (组表, 尾部起点)。尾部是第二个容器（13 组），不解析。"""
    if len(data) < 4:
        raise ValueError("太短")
    count = struct.unpack_from("<I", data, 0)[0]
    pos, blocks = 4, []
    for _ in range(count):
        if data[pos:pos + 4] != b"LDLD":
            raise ValueError(f"第 {len(blocks)} 组头不是 LDLD @0x{pos:X}")
        version, type_id, size = struct.unpack_from("<III", data, pos + 4)
        payload = pos + 24
        blocks.append({"at": pos, "payload": payload, "size": size, "type_id": type_id})
        pos = payload + size
    return blocks, pos


def used_rows() -> list[int]:
    """被 34 个 region 变体列表引用到的 GenerationRegionSettings 行号（= variant_type - 1）。"""
    levelgen = json.loads(LEVELGEN.read_text(encoding="utf-8"))
    rows = set()
    for lst in levelgen["region_settings"]["variant_lists"]:
        for entry in lst["sets"]:
            rows.add(entry["variant_type"] - 1)
    return sorted(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description="压平 region 地形高度（保 MurmurHash64A）")
    ap.add_argument("--plain", required=True, help="region_settings 明文（259,627 B）")
    ap.add_argument("--rows", default="used", help="used | all | 逗号分隔行号")
    ap.add_argument("--height", type=float, default=2.0, help="terrain_height_range 目标值")
    ap.add_argument("--global-range", type=float, default=None, help="可选：同时改 +0x02C")
    ap.add_argument("--zone-range", type=float, default=None, help="可选：同时改 +0x030")
    ap.add_argument("--pure-rand", type=float, default=None, help="可选：同时改 +0x020")
    ap.add_argument("--weights-flat", action="store_true",
                    help="四档权重改成 高0/中0/低0/底部平原2（逼生成器只用平原档）")
    ap.add_argument("--sub-height-group", type=int, default=None,
                    help="把所有 Type!=None 的子区域 HeightGroup 改成该值（1=Bottom_Flat）")
    ap.add_argument("--host-row", type=int, default=0, help="校正字宿主行（默认 0，无主行）")
    ap.add_argument("--out", required=True, help="输出明文")
    ap.add_argument("--seal", help="recipient.pk 路径；给了就顺带封装")
    ap.add_argument("--sealed", help="封装输出路径")
    ap.add_argument("--secret", help="recipient.sk 路径；给了就回读验证封装")
    args = ap.parse_args()

    original = pathlib.Path(args.plain).read_bytes()
    blocks, tail_start = parse_blocks(original)
    if len(blocks) != 74:
        raise SystemExit(f"✗ 期望 74 个 GenerationRegionSettings 组，读到 {len(blocks)}")
    for b in blocks:
        if b["size"] != ROW_SIZE:
            raise SystemExit(f"✗ 组 {b['at']:#x} payload={b['size']} != {ROW_SIZE}")

    if args.rows.strip().lower() == "used":
        rows = used_rows()
    elif args.rows.strip().lower() == "all":
        rows = list(range(74))
    else:
        rows = [int(x) for x in args.rows.split(",") if x.strip()]

    edits: dict[int, tuple[int, bytes, str]] = {}          # 绝对偏移 -> (宽, 新值, 名字)
    for row in rows:
        base = blocks[row]["payload"]
        plan = [("height", args.height)]
        if args.global_range is not None:
            plan.append(("global_range", args.global_range))
        if args.zone_range is not None:
            plan.append(("zone_range", args.zone_range))
        if args.pure_rand is not None:
            plan.append(("pure_rand", args.pure_rand))
        if args.weights_flat:
            plan += [("w_high", 0.0), ("w_mid", 0.0), ("w_low", 0.0), ("w_flat", 2.0)]
        for name, value in plan:
            off = base + FIELDS[name]
            edits[off] = (4, struct.pack("<f", value), f"row{row}.{name}")
        if args.sub_height_group is not None:
            for s in range(SUBREGION_COUNT):
                slot = base + SUBREGION_BASE + s * SUBREGION_STRIDE
                stype = struct.unpack_from("<I", original, slot + FIELDS["sub_type"])[0]
                if stype == 0:                     # SubRegionType_None：空槽，不动
                    continue
                off = slot + FIELDS["sub_height_group"]
                edits[off] = (4, struct.pack("<I", args.sub_height_group),
                              f"row{row}.sub{s}.height_group")

    edited = bytearray(original)
    for off, (width, blob, _) in edits.items():
        edited[off:off + width] = blob

    # 校正字：借用无主行里一个 8 字节对齐字
    host = blocks[args.host_row]["payload"] + 0x04C
    if host % 8:
        raise SystemExit(f"✗ 校正字位置 0x{host:X} 不是 8 对齐")
    h0 = murmur64(original)
    word = padding_word_for_hash(bytes(edited), host, h0)
    edited[host:host + 8] = word

    checks = []

    def check(tag: str, cond: bool, detail: str = "") -> None:
        checks.append(cond)
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = set()
    for off, (width, _, _) in edits.items():
        allowed |= set(range(off, off + width))
    allowed |= set(range(host, host + 8))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    check("G1 长度不变", len(edited) == len(original), f"{len(original):,} B")
    check("G2 差异 ⊆ 声明字段 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)} 越界={[hex(x) for x in sorted(diff - allowed)[:5]]}")
    got = murmur64(bytes(edited))
    check("G3 MurmurHash64A 不变", got == h0, f"0x{h0:016X}")
    readback = all(bytes(edited[o:o + w]) == blob for o, (w, blob, _) in edits.items())
    check("G4 声明字段读回一致", readback, f"{len(edits)} 处")
    try:
        b2, t2 = parse_blocks(bytes(edited))
        ok = len(b2) == 74 and t2 == tail_start
    except Exception as exc:                                   # noqa: BLE001
        ok = False
        print(f"      容器解析失败：{exc}")
    check("G5 容器结构自洽", ok, f"74 组，尾部 @0x{tail_start:X}")

    if not all(checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(edited))
    print(f"\n明文已写 {out} ({len(edited):,} B, sha256 {hashlib.sha256(bytes(edited)).hexdigest()[:16]})")
    print(f"  改动 {len(rows)} 行: {rows}")
    print(f"  校正字 @ record{args.host_row}+0x4C = {word.hex()}")

    if args.seal:
        from nacl.public import PrivateKey, PublicKey, SealedBox
        sealed = pathlib.Path(args.sealed or out.with_suffix(".sealed.dl_bin"))
        blob = SealedBox(PublicKey(pathlib.Path(args.seal).read_bytes())).encrypt(bytes(edited))
        sealed.write_bytes(blob)
        print(f"封装已写 {sealed} ({len(blob):,} B)")
        if args.secret:
            back = SealedBox(PrivateKey(pathlib.Path(args.secret).read_bytes())).decrypt(blob)
            check("G6 解封 == 改动后明文", back == bytes(edited))
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
