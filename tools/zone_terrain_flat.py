#!/usr/bin/env python3
"""zone_terrain_flat.py — 改 `generated_zone_data` 里 height generator 的 amplitude（保哈希）。

为什么是这里
    地形起伏的「生成层」不在 region_settings，而在 **每个 zone 的 `height_generators`（+0x080）**：
        ShaderProperties[24 B] = { shader u64, settings DLArray{offset i64, count u64} }
    每个生成器的 settings 是 28 B/条：{ name ThinHash u32, value f32, Vector(Vec4 + count) }，
    其中已爆破出名字的三条：
        0x53D111F6 = noise_scale   （25..375，噪声特征尺度）
        0x21E1CDE6 = power         （1..3）
        0xE0EC70A9 = amplitude     （0.1..3.5，高度倍率 ← 本工具改它）
        0x8A8534A7 = 未爆（-0.2..-0.5）
    旁证：城市 zone（10/15/20/25）**完全没有 height generator**，所以城市是平的。

保哈希
    文件形如 `u32 3 | u32 88 | 88 × LDLD(zone 记录 + 组尾) | 段1 | 段2`。
    校正字借用**无主 zone**（不被任何 region 子区域引用的 zone，如 zone 0）payload 内一个 8 字节对齐字。

用法
    python tools/zone_terrain_flat.py --plain <zone_data 明文> --amplitude 0.01 \\
        --out out/terrain/zone_flat.plain.dl_bin \\
        [--seal refs/dlbin/keys/recipient.pk --sealed out/terrain/zone_flat.sealed.dl_bin \\
         --secret refs/dlbin/keys/recipient.sk]
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import struct
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from murmur64 import murmur64, padding_word_for_hash            # noqa: E402

ZONE_COUNT = 88
HEIGHT_ARRAY = 0x080
NL_SCALE, NL_POWER, NL_AMP = 0x53D111F6, 0x21E1CDE6, 0xE0EC70A9
GEN_STRIDE = 24                                                  # ShaderProperties: hash + DLArray
SET_STRIDE = 28                                                  # ShaderSetting: name + value + Vec4 + count


def parse(data: bytes) -> tuple[list[tuple[int, int]], int]:
    """返回 [(group_at, payload_size)], 88 组结束位置。"""
    if len(data) < 8:
        raise ValueError("太短")
    sections, count = struct.unpack_from("<II", data, 0)
    pos, groups = 8, []
    for _ in range(count):
        if data[pos:pos + 4] != b"LDLD":
            raise ValueError(f"第 {len(groups)} 组头不是 LDLD @0x{pos:X}")
        size = struct.unpack_from("<I", data, pos + 12)[0]
        groups.append((pos, size))
        pos += 24 + size
    return groups, pos


def gens(data: bytes, payload: int, size: int) -> list[tuple[int, int]]:
    """[(settings_offset_abs, settings_count)]；offset 是 payload 相对，转成绝对。"""
    if HEIGHT_ARRAY + 16 > size:
        return []
    off, cnt = struct.unpack_from("<qQ", data, payload + HEIGHT_ARRAY)
    out = []
    if off < 0 or not cnt or off + GEN_STRIDE * cnt > size:
        return out
    for i in range(cnt):
        so, sc = struct.unpack_from("<qQ", data, payload + off + GEN_STRIDE * i + 8)
        if 0 <= so and sc and so + SET_STRIDE * sc <= size:
            out.append((payload + so, sc))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="改 zone height generator 的 amplitude（保 MurmurHash64A）")
    ap.add_argument("--plain", required=True)
    ap.add_argument("--amplitude", type=float, default=0.01, help="amplitude 目标值（默认 0.01）")
    ap.add_argument("--also-noise-scale", type=float, default=None, help="可选：同时改 noise_scale")
    ap.add_argument("--host-zone", type=int, default=0, help="校正字宿主 zone（须为无主 zone）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seal")
    ap.add_argument("--sealed")
    ap.add_argument("--secret")
    args = ap.parse_args()

    original = pathlib.Path(args.plain).read_bytes()
    groups, tail = parse(original)
    if len(groups) != ZONE_COUNT:
        raise SystemExit(f"✗ 期望 {ZONE_COUNT} 个 zone 组，读到 {len(groups)}")

    edits: dict[int, tuple[int, bytes, str]] = {}
    per_zone = {}
    for z, (at, size) in enumerate(groups):
        payload = at + 24
        n = 0
        for so, sc in gens(original, payload, size):
            for j in range(sc):
                name = struct.unpack_from("<I", original, so + SET_STRIDE * j)[0]
                if name == NL_AMP:
                    edits[so + SET_STRIDE * j + 4] = (4, struct.pack("<f", args.amplitude), f"zone{z}.amplitude")
                    n += 1
                elif args.also_noise_scale is not None and name == NL_SCALE:
                    edits[so + SET_STRIDE * j + 4] = (4, struct.pack("<f", args.also_noise_scale), f"zone{z}.noise_scale")
        if n:
            per_zone[z] = n

    edited = bytearray(original)
    for off, (width, blob, _) in edits.items():
        edited[off:off + width] = blob

    # 校正字：无主 zone 的 payload 起点（8 对齐已核对）
    host = groups[args.host_zone][0] + 24
    if host % 8:
        raise SystemExit(f"✗ 宿主 0x{host:X} 未 8 对齐")
    h0 = murmur64(original)
    word = padding_word_for_hash(bytes(edited), host, h0)
    edited[host:host + 8] = word

    checks = []

    def check(tag, cond, detail=""):
        checks.append(bool(cond))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = set()
    for off, (w, _, _) in edits.items():
        allowed |= set(range(off, off + w))
    allowed |= set(range(host, host + 8))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    check("G1 长度不变", len(edited) == len(original), f"{len(original):,} B")
    check("G2 差异 ⊆ 声明字段 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)} 越界={[hex(x) for x in sorted(diff - allowed)[:5]]}")
    got = murmur64(bytes(edited))
    check("G3 MurmurHash64A 不变", got == h0, f"0x{h0:016X}")
    check("G4 字段读回一致", all(bytes(edited[o:o + w]) == blob for o, (w, blob, _) in edits.items()),
          f"{len(edits)} 处")
    g2, t2 = parse(bytes(edited))
    check("G5 结构自洽", len(g2) == ZONE_COUNT and t2 == tail, f"88 组，尾部 @0x{tail:X}")
    if not all(checks):
        print("\n✗ 门禁未全过")
        return 1

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(edited))
    print(f"\n明文已写 {out} ({len(edited):,} B, sha256 {hashlib.sha256(bytes(edited)).hexdigest()[:16]})")
    print(f"  改了 {sum(per_zone.values())} 个 amplitude，覆盖 {len(per_zone)} 个 zone: {sorted(per_zone)}")
    print(f"  校正字 @ zone{args.host_zone} payload+0 = {word.hex()}")

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
