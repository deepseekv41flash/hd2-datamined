#!/usr/bin/env python3
"""entity_hashmap_insert.py -- 给一个实体键**新增**一条哈希图记录（指向已有行或复制出来的行）。

为什么要它
    实体表里「某实体挂了某组件」的判据，就是**该组件的哈希图里有没有它的键**。
    所以「给 GL-28 加一条 `WeaponMagazineComponentData` 行」这件事，本质是往哈希图里插一条
    `(GL-28 实体键 → 行号)`。以前没有这个能力，只能改已存在的行。

哈希图结构（本 build 全部实体组件块一致）
    `[u64 键 | u32 行号 | u32 保留] × 槽数`，**开放寻址 + 线性探测**，探测起点 `槽 = 键 % 槽数`。
    这条不是猜的：用三个表验证过 ——
        Magazine      276/276 键可达，最长 3 步
        Rounds         25/25  键可达，最长 2 步
        背包弹药       30/30  键可达，最长 4 步
    载入率都是 50%（槽数 = 2×行数），空槽充足，插入到「探测链上的第一个空槽」不会破坏任何已有查询。

用法
    # 把 GL-21 的武器弹匣行整行复制给 GL-28（= 让 GL-28 长出一条普通弹匣行）
    python tools/entity_hashmap_insert.py --block 0xFB8D88A3 \\
        --key 0x88C2D09AD85A7C9F --copy-row-from 0x02EECD0B1FA49630 \
        --out out/gl28_mag.plain

    # 只指向一条**没有键指向**的孤儿行（不改行内容）
    python tools/entity_hashmap_insert.py --block 0xFB8D88A3 --key 0x... --row 276 --out out/x.plain

门禁
    G1 长度 = 原长 + pad + 8            G2 差异 ⊆ 声明区域 ∪ 末块尺寸字段 ∪ 校正字
    G3 重算 Murmur == 原值              G4 新键查得到且行号正确、行内容 == 源行
    G5 全部旧键仍可查（探测链未被破坏）  G6 目标键原本不存在
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash       # noqa: E402
from pod_rack_swap import parse_blocks, check_container    # noqa: E402
from typelib import TypeLib                                # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                      # noqa: BLE001
        pass

DEFAULT_PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
DEFAULT_LIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
TAIL = 8


def geometry(d, tid: int) -> dict:
    """哈希图几何：槽数、行数、行跨距、哈希图起点、行数组起点。

    几何一律走 `pod_loadout.Data.t()`（它按「哈希图 + 行数组」两段解释块），
    不要自己从 typelib 的第一个成员推 —— 那个成员可能是结构体，`desc()[3]` 给的是
    结构体大小（16），当成行跨距就全错。
    """
    blk, hm_size, stride, rows, row_base = d.t(tid)
    return {"blk": blk, "hm": blk["body"], "slots": hm_size // 16, "stride": stride,
            "row_base": row_base, "rows": rows, "hm_size": hm_size}


def lookup(data: bytes, g: dict, key: int):
    """线性探测查询：返回 (槽号, 行号) 或 (None, None)。"""
    start = key % g["slots"]
    for step in range(g["slots"]):
        slot = (start + step) % g["slots"]
        k, v = struct.unpack_from("<QI", data, g["hm"] + 16 * slot)
        if k == 0:
            return None, None
        if k == key:
            return slot, v
    return None, None


def free_slot(data: bytes, g: dict, key: int) -> int:
    start = key % g["slots"]
    for step in range(g["slots"]):
        slot = (start + step) % g["slots"]
        k, _ = struct.unpack_from("<QI", data, g["hm"] + 16 * slot)
        if k == 0:
            return slot
    raise SystemExit("✗ 哈希图已满（不该发生：本 build 载入率 50%）")


def rebuild(original: bytes, blocks, extra: int) -> bytes:
    """把最后一组 payload 加 extra 字节、把它的尺寸字段同步，尾部补零。"""
    out = bytearray(original) + b"\0" * extra
    last = blocks[-1]
    size_off = last["head"] + 16          # u32 type | 'LDLD' | ver | 内部 type | ★payload
    struct.pack_into("<I", out, size_off, last["payload"] + extra)
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="实体组件哈希图插入（保内容哈希）")
    ap.add_argument("--plain", default=DEFAULT_PLAIN)
    ap.add_argument("--typelib", default=DEFAULT_LIB)
    ap.add_argument("--block", required=True, help="组件块类型 id，如 0xFB8D88A3")
    ap.add_argument("--key", required=True, help="要新增的实体键")
    ap.add_argument("--row", type=lambda v: int(v, 0), default=None, help="指向这条已有行")
    ap.add_argument("--delete", action="store_true",
                    help="删除这个键（线性探测后移填补，不破坏其它键的探测链）")
    ap.add_argument("--copy-row-from", default=None,
                    help="把这条键所在行整行复制到目标行（与 --row 互斥）")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    original = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(pathlib.Path(a.typelib).read_bytes())
    tid = int(a.block, 0)
    key = int(a.key, 0)
    from pod_loadout import Data as _Data
    _d = _Data()
    _d.ent = original
    g = geometry(_d, tid)
    print(f"块 0x{tid:08X}  槽 {g['slots']}  行 {g['rows']}  行跨距 {g['stride']} B")

    writes: list[tuple[int, bytes]] = []      # (文件偏移, 新字节) —— 只允许改这些区域

    if a.delete:
        slot, row = lookup(original, g, key)
        if slot is None:
            raise SystemExit(f"✗ 键 0x{key:016X} 不在表里，无法删除")
        print(f"  删除：槽 {slot}（行 {row}）—— 用**后移填补**（线性探测的标准删法）")
        hm = bytearray(original[g["hm"]:g["hm"] + g["slots"] * 16])

        def k_at(i):
            return struct.unpack_from("<Q", hm, 16 * i)[0]

        def v_at(i):
            return struct.unpack_from("<I", hm, 16 * i + 8)[0]

        hole, nxt, moved = slot, slot, 0
        while True:
            nxt = (nxt + 1) % g["slots"]
            kk = k_at(nxt)
            if kk == 0:
                break
            h = kk % g["slots"]
            # 只有当 hole 落在它的探测路径上（比它自己更靠近起点）才搬
            if (hole - h) % g["slots"] < (nxt - h) % g["slots"]:
                struct.pack_into("<QII", hm, 16 * hole, kk, v_at(nxt), 0)
                struct.pack_into("<QII", hm, 16 * nxt, 0, 0, 0)
                hole = nxt
                moved += 1
        struct.pack_into("<QII", hm, 16 * hole, 0, 0, 0)      # 最后把空位显式清零
        writes.append((g["hm"], bytes(hm)))
        print(f"    搬移 {moved} 条后续记录，最终空槽 {hole}")
        dst_row = row
    else:
        if lookup(original, g, key)[0] is not None:
            raise SystemExit(f"✗ 键 0x{key:016X} 已经在哈希图里（新增请换一个键；删除请加 --delete）")
        if a.copy_row_from and a.row is not None:
            raise SystemExit("✗ --row 与 --copy-row-from 只能给一个")

        if a.copy_row_from:
            src_key = int(a.copy_row_from, 0)
            sslot, src_row = lookup(original, g, src_key)
            if sslot is None:
                raise SystemExit(f"✗ 源键 0x{src_key:016X} 不在表里")
            used = {struct.unpack_from("<I", original, g["hm"] + 16 * i + 8)[0]
                    for i in range(g["slots"])
                    if struct.unpack_from("<Q", original, g["hm"] + 16 * i)[0]}
            orphans = [r for r in range(g["rows"]) if r not in used]
            if not orphans:
                raise SystemExit("✗ 没有孤儿行可放拷贝")
            dst_row = orphans[0]
            writes.append((g["row_base"] + dst_row * g["stride"],
                           original[g["row_base"] + src_row * g["stride"]:
                                    g["row_base"] + (src_row + 1) * g["stride"]]))
            print(f"  源键 0x{src_key:016X} → 行 {src_row}；目标行 = 孤儿行 {dst_row}")
        else:
            if a.row is None:
                raise SystemExit("✗ 需要 --row / --copy-row-from / --delete")
            dst_row = a.row
            if not 0 <= dst_row < g["rows"]:
                raise SystemExit(f"✗ 行号 {dst_row} 越界（0..{g['rows'] - 1}）")
            print(f"  目标行 = {dst_row}（只插键，不改行内容）")

        slot = free_slot(original, g, key)
        print(f"  插入位置：槽 {slot}（起点 {key % g['slots']}，探测 "
              f"{(slot - key % g['slots']) % g['slots']} 步）")
        writes.append((g["hm"] + 16 * slot, struct.pack("<QII", key, dst_row, 0)))

    blocks = parse_blocks(original)
    pad8 = (8 - len(original) % 8) % 8
    edited = bytearray(rebuild(original, blocks, pad8 + TAIL))
    for off, blob in writes:
        edited[off:off + len(blob)] = blob

    word_at = len(original) + pad8
    h0 = murmur64(original)
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)
    print(f"原始哈希 0x{h0:016X}   校正字 @ 0x{word_at:X}")

    checks = []
    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    last_at = blocks[-1]["head"]
    allowed = set()
    for off, blob in writes:
        allowed |= set(range(off, off + len(blob)))
    allowed |= set(range(last_at + 16, last_at + 20))   # 末块 payload 尺寸字段
    allowed |= set(range(word_at, word_at + TAIL))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    check("G1 长度 = 原长 + 对齐 + 8", len(edited) == len(original) + pad8 + TAIL,
          f"{len(original)} -> {len(edited)}")
    check("G2 差异 ⊆ 声明区域 ∪ 尺寸字段 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)}，越界 {sorted(diff - allowed)[:5]}")
    check("G3 重算哈希 == 原始哈希", murmur64(bytes(edited)) == h0, f"0x{h0:016X}")
    got_slot, got_row = lookup(bytes(edited), g, key)
    if a.delete:
        check("G4 键已消失", got_slot is None)
    else:
        check("G4 新键查得到且行号正确", got_row == dst_row, f"槽 {got_slot} 行 {got_row}")
        for off, blob in writes:
            if off == g["row_base"] + dst_row * g["stride"]:
                check("G4b 目标行内容 == 源行", bytes(edited[off:off + len(blob)]) == blob)
    ok_old = True
    for i in range(g["slots"]):
        k, v = struct.unpack_from("<QI", original, g["hm"] + 16 * i)
        if not k or (a.delete and k == key):
            continue
        if lookup(bytes(edited), g, k)[1] != v:
            ok_old = False
            break
    check("G5 全部旧键仍可查", ok_old)
    check("G6 容器重解析自洽", check_container(bytes(edited)))

    if not all(c for _, c in checks):
        raise SystemExit("✗ 门禁未过，未写出")
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_bytes(bytes(edited))
    print(f"\n✓ 全部门禁通过 → {a.out}（{len(edited):,} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
