"""在 `generated_explosion_settings.dl_bin` 上写爆炸行字段，并保内容哈希。

表：`data/game/generated_explosion_settings.dl_bin`
  明文 68,156 B = u32 组数(1) + LDLD 头(24) + 数组描述符(16) + 424 行 × 152 B（存在尾部附加块）
  行基址 = 44（≡ 4 mod 8）· 步长 152（≡ 0 mod 8）
  已知字段：
    +0   type id（爆炸类型枚举，★ type 不是行号）
    +4   伤害行 id
    +16/+20/+24  半径三元组（float，内/中/外，米）
    +80  破片数量            ★ 破片实验的关键格
    +84  破片射弹 type id    ★ 同上
  内容哈希：与其它 dl_bin 同一道 Murmur64A 闸门（game.dll 烘焙）⇒ 用「无主爆炸行里的
  8 字节对齐空字」承载校正字（同伤害表做法）。

用法：
  python expl_set.py --plain <vanilla_explosion_plain> --type 178 \
      --set 0x50:30 --set 0x54:204 \
      --host-type 275 --host-offset 0x34 --out <out_plain>
"""
from __future__ import annotations

import argparse
import struct
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

sys.path.insert(0, r"D:\mod\work\devkit\tools")
from murmur64 import murmur64, padding_word_for_hash  # noqa: E402

STRIDE = 152
BASE = 44


def main() -> int:
    ap = argparse.ArgumentParser(description="爆炸行字段写入（保内容哈希）")
    ap.add_argument("--plain", required=True)
    ap.add_argument("--type", type=int, required=True, help="目标爆炸 type（行 +0）")
    ap.add_argument("--set", action="append", required=True, metavar="OFF:VALUE",
                    help="行内偏移:新值（u32），可重复，如 0x50:30")
    ap.add_argument("--host-type", type=int, required=True, help="付校正字的无主爆炸 type")
    ap.add_argument("--host-offset", required=True, help="宿主行内的 8 对齐偏移（≡4 mod 8）")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = open(args.plain, "rb").read()
    if data[4:8] != b"LDLD":
        raise SystemExit("✗ 组头 magic 不对")
    count = struct.unpack_from("<I", data, 0)[0]
    if count != 1:
        raise SystemExit(f"✗ 期望 1 组，实际 {count}")
    array_off, rows, pad = struct.unpack_from("<QII", data, 28)
    if pad != 0 or 28 + array_off != BASE:
        raise SystemExit("✗ 数组描述符与预期不符")
    h0 = murmur64(data)
    print(f"明文 {len(data):,} B  rows={rows}  hash=0x{h0:016X}")

    index = {}
    for i in range(rows):
        index[struct.unpack_from("<I", data, BASE + i * STRIDE)[0]] = i
    if args.type not in index:
        raise SystemExit(f"✗ 爆炸 type {args.type} 不存在")
    if args.host_type not in index:
        raise SystemExit(f"✗ 宿主爆炸 type {args.host_type} 不存在")
    if args.type == args.host_type:
        raise SystemExit("✗ 目标与宿主不能同一行")

    tgt = BASE + index[args.type] * STRIDE
    edited = bytearray(data)
    touched = []
    for spec in args.set:
        off_s, val_s = spec.split(":")
        off, val = int(off_s, 0), int(val_s, 0)
        if off % 4 or not (0 <= off <= STRIDE - 4) or off == 0:
            raise SystemExit(f"✗ --set 偏移 {off:#x} 非法（4 对齐、行内、非 +0）")
        old = struct.unpack_from("<I", edited, tgt + off)[0]
        struct.pack_into("<I", edited, tgt + off, val)
        touched.append((off, old, val))
        print(f"  爆炸 {args.type} 行内 +{off:#x}: {old} -> {val}")

    host_off = int(args.host_offset, 0)
    if host_off % 8 != 4:
        raise SystemExit(f"✗ 宿主行内偏移必须 ≡ 4 (mod 8)，收到 {host_off:#x}")
    host = BASE + index[args.host_type] * STRIDE + host_off
    if struct.unpack_from("<Q", data, host)[0] != 0:
        raise SystemExit("✗ 宿主那个 8 字节字不是全零")
    word = padding_word_for_hash(bytes(edited), host, h0)
    edited[host:host + 8] = word
    edited = bytes(edited)

    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")
        ok = ok and cond

    check("G1 长度不变", len(edited) == len(data), f"{len(data):,}")
    expected = set(range(tgt, tgt + STRIDE)) | set(range(host, host + 8))
    diff = {i for i in range(len(data)) if data[i] != edited[i]}
    check("G2 差异 ⊆ 目标行 ∪ 校正字", diff <= expected, f"diff={len(diff)}")
    got = murmur64(edited)
    check("G3 重算哈希 == 原始哈希", got == h0, f"0x{got:016X}")
    allset = all(struct.unpack_from("<I", edited, tgt + o)[0] == v for o, _old, v in touched)
    check("G4 目标行读回", allset, str([(hex(o), v) for o, _o, v in touched]))
    # 宿主行除校正字外未变
    hs = host - host_off
    check("G5 宿主行其余未变",
          edited[hs:host] == data[hs:host] and edited[host + 8:hs + STRIDE] == data[host + 8:hs + STRIDE])
    # 目标行的非 --set 字段未变
    setoffs = {o for o, _o, _v in touched}
    extra = [o for o in range(0, STRIDE, 4)
             if o not in setoffs and edited[tgt + o:tgt + o + 4] != data[tgt + o:tgt + o + 4]]
    check("G6 目标行其它字段未变", not extra, f"漂移 {extra[:6]}")

    if not ok:
        print("✗ 门禁未过，不写文件")
        return 1
    open(args.out, "wb").write(edited)
    print(f"✓ 已写 {args.out}（{len(edited):,} B, hash=0x{murmur64(edited):016X}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
