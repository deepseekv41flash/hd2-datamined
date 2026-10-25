"""示例解析脚本（只依赖 Python 标准库）。

⚠ 本示例写于 build 25988413（表结构与解析方式跨 build 稳定）；
当前 build `26088801` 的示例见 examples/stratagem_extra_demo.py，完整案例见 docs/cases/。

用法：
    python parse_examples.py --projectile generated_projectile_settings.dl_bin
    python parse_examples.py --blocks   generated_entities.dl_bin
    python parse_examples.py --slots    generated_entities.dl_bin 0x193CCE8

注释里的可信度标记：
    [实测] 在本机 build 25988413 上逐字节验证过
    [推断] 由取值范围/社区资料推断，未逐字节验证
"""
from __future__ import annotations

import argparse
import struct

# ---------------------------------------------------------------- 通用小工具
MURMUR_M = 0xC6A4A7935BD1E995
MURMUR_SEED = 0xDEADBEEFABAD1DEA
MASK64 = (1 << 64) - 1


def murmur64(data: bytes, seed: int = MURMUR_SEED) -> int:
    """MurmurHash64A。[实测] 资源的“路径哈希”就是它，例如
    murmur64(b"content/.../assault_rifle_patriot/...") 会命中实体表里的键。"""
    h = (seed ^ (len(data) * MURMUR_M)) & MASK64
    body = len(data) // 8 * 8
    for offset in range(0, body, 8):
        k = struct.unpack_from("<Q", data, offset)[0]
        k = (k * MURMUR_M) & MASK64
        k ^= k >> 47
        k = (k * MURMUR_M) & MASK64
        h = ((h ^ k) * MURMUR_M) & MASK64
    tail = data[body:]
    if tail:
        h = ((h ^ int.from_bytes(tail, "little")) * MURMUR_M) & MASK64
    h ^= h >> 47
    h = (h * MURMUR_M) & MASK64
    h ^= h >> 47
    return h


def read_ldld_groups(data: bytes, start: int = 0):
    """依次走 LDLD 块，返回 (块起点, 类型 id, payload 起点, payload 长度)。

    存在两种容器布局，这里都处理：
      A) 以 `u32 组数` 开头，之后直接是 LDLD 头（`data/game/generated_*.dl_bin` 的设置表）
         头部 24 字节：'LDLD' | ver | type | payload | wide | 7 reserved
      B) 「块序列」，每块前面多一个 u32 类型 id（`generated_entities` / `generated_entity_deltas`）
         头部 28 字节：u32 type | 'LDLD' | ver | type | payload | wide | 7 reserved
    [实测] 两种都在本版本验证过。
    """
    position = start
    while position + 24 <= len(data):
        if data[position:position + 4] == b"LDLD":
            head, body = position + 24, position + 24
            version, type_id, payload = struct.unpack_from("<III", data, position + 4)
        elif data[position + 4:position + 8] == b"LDLD":
            head, body = position + 28, position + 28
            type_id = struct.unpack_from("<I", data, position)[0]
            version, inner, payload = struct.unpack_from("<III", data, position + 8)
            if inner != type_id:
                return
        else:
            return
        if version != 1:
            return
        if body + payload > len(data):
            return
        yield position, type_id, body, payload
        position = body + payload


# ---------------------------------------------------------------- projectile
PROJECTILE_STRIDE = 272  # [实测] 96,604 B = 4 + 24 + 16 + 355*272


def dump_projectile(path: str, limit: int) -> None:
    data = open(path, "rb").read()
    count = struct.unpack_from("<I", data, 0)[0]
    print(f"{path}: {len(data):,} B, {count} group(s)")
    for group, type_id, body, payload in read_ldld_groups(data, 4):
        array_offset, records, pad = struct.unpack_from("<QII", data, body)
        base = body + array_offset
        print(f"  group {group} type=0x{type_id:08X} array_at=+{array_offset} rows={records}")
        for index in range(min(limit, records)):
            row = base + index * PROJECTILE_STRIDE
            ptype = struct.unpack_from("<I", data, row + 0)[0]
            calibre = struct.unpack_from("<f", data, row + 24)[0]
            num = struct.unpack_from("<I", data, row + 28)[0]
            speed, mass, drag, gravity = struct.unpack_from("<4f", data, row + 32)
            life = struct.unpack_from("<f", data, row + 56)[0]
            damage_type = struct.unpack_from("<I", data, row + 60)[0]
            penetration_slowdown = struct.unpack_from("<f", data, row + 64)[0]
            print(f"    [{index:3d}] type={ptype:4d} calibre={calibre:6.2f} num={num} "
                  f"speed={speed:7.1f} mass={mass:6.2f} drag={drag:6.3f} "
                  f"gravity={gravity:5.2f} life={life:5.2f} "
                  f"damageType={damage_type:4d} penSlow={penetration_slowdown:5.2f}")


# ---------------------------------------------------------------- entities
def dump_blocks(path: str) -> None:
    data = open(path, "rb").read()
    print(f"{path}: {len(data):,} B")
    for index, (position, type_id, body, payload) in enumerate(read_ldld_groups(data, 0)):
        print(f"  [{index:3d}] 0x{position:08X} type=0x{type_id:08X} payload={payload:>10,}")
        if index > 300:
            break


def dump_slots(path: str, position: int, limit: int) -> None:
    """组件块 = 槽位表：16 字节一条 {u64 路径哈希, u32 值, u32 填充}。[实测]"""
    data = open(path, "rb").read()
    type_id = struct.unpack_from("<I", data, position)[0]
    version, inner_type, payload = struct.unpack_from("<III", data, position + 8)
    body = position + 28
    rows = []
    offset = 0
    while offset + 16 <= payload:
        key, value = struct.unpack_from("<QI", data, body + offset)
        offset += 16
        if key:
            rows.append((key, value))
    print(f"block 0x{position:X}: type=0x{type_id:08X} version={version} payload={payload:,}")
    print(f"  {len(rows)} slot(s), 前 {min(limit, len(rows))} 条：")
    for key, value in rows[:limit]:
        print(f"    key=0x{key:016X} value={value}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--projectile", metavar="FILE")
    parser.add_argument("--blocks", metavar="FILE")
    parser.add_argument("--slots", nargs=2, metavar=("FILE", "OFFSET"))
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    if args.projectile:
        dump_projectile(args.projectile, args.limit)
    elif args.blocks:
        dump_blocks(args.blocks)
    elif args.slots:
        dump_slots(args.slots[0], int(args.slots[1], 0), args.limit)
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
