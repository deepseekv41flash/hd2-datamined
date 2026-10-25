#!/usr/bin/env python3
"""block_payload_append.py -- 给「中间块」的 payload 追加字节（整容器重排 + 尾字校正，保内容哈希）。

为什么需要
    战备表的呼叫码是「payload 相对偏移 + 个数」指向 payload 里的一段数组。要把码变长，
    必须在 payload 尾部塞一段新数组，于是**这一块的 payload 变长**、后面所有块的绝对偏移全部平移 ——
    `plain_edit.py` 只能在**文件末尾**加字节，改不了这种结构。
    这套「整容器重排 + 尾字校正」已在护甲被动叠行上 **✓✓ 实机**
    （`tools/passive_bonus_edit.py` + [ARMOR-KIT-WEIGHTS §9.5]）；本工具把它抽成通用版：
    只管"往第 N 块 payload 尾部追加 N 字节，再按 `--set` 改任意绝对偏移"，表结构无关。

容器假设（普通表布局，战备设置/爆炸/弹丸都是这种）
    `u32 块数` + 连续 N 个：`'LDLD' | ver | type_id | payload | wide | extra | payload`（24 B 头）
    注意：**实体库是 28 B 头的变体**（`u32 type|'LDLD'|ver|type|payload|...`，payload 尺寸在 head+16），
    本工具会拒绝那种容器（要求 `'LDLD'` 在块头 0 字节处）。

门禁
    G1 块数不变、每块 type/ver/wide/extra 不变、payload 长度只有目标块 +K、末块 +(pad+8)
    G2 目标块原 payload 前缀逐字节未动（追加在尾部）
    G3 其余块 payload 逐字节未动
    G4 每块 payload 的**相对偏移**仍能解析（抽查 name/key/desc 三个指针落在 payload 内）
    G5 重算 Murmur64A == 原值
    G6 `--set` 字段读回一致

用法
    python tools/block_payload_append.py --plain in.dl_bin --out out.dl_bin \\
        --row 0x11168 --append-hex 0300000003000000 \\
        --set 0x111A8=u64:4860 --set 0x111B0=u32:10
    # --row 只是为了找出它属于哪一块；--set 是普通的「绝对偏移=类型:值」
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash      # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

TAIL = 8
HEAD = 24


def parse_blocks(data: bytes) -> list[dict]:
    if len(data) < 4:
        raise SystemExit("✗ 文件太短")
    count = struct.unpack_from("<I", data, 0)[0]
    pos, blocks = 4, []
    for i in range(count):
        if data[pos:pos + 4] != b"LDLD":
            raise SystemExit(f"✗ 第 {i} 块头不是 LDLD（@{pos:#x}）——不是普通表容器（实体库是 28 B 头变体）")
        ver, tid, payload, wide, extra = struct.unpack_from("<IIIII", data, pos + 4)
        if ver not in (1, 2) or payload <= 0 or pos + HEAD + payload > len(data):
            raise SystemExit(f"✗ 第 {i} 块头非法 ver={ver} payload={payload}")
        blocks.append({"head": pos, "ver": ver, "type": tid, "size": payload,
                       "wide": wide, "extra": extra, "body": pos + HEAD})
        pos += HEAD + payload
    if pos != len(data):
        raise SystemExit(f"✗ 尾部残留 {len(data) - pos} B")
    return blocks


def parse_set(spec: str) -> tuple[int, bytes]:
    off_s, val_s = spec.split("=", 1)
    kind, _, raw = val_s.partition(":")
    kind = kind.strip().lower()
    if kind == "u32":
        return int(off_s, 0), struct.pack("<I", int(raw, 0) & 0xFFFFFFFF)
    if kind == "f32":
        return int(off_s, 0), struct.pack("<f", float(raw))
    if kind == "u64":
        return int(off_s, 0), struct.pack("<Q", int(raw, 0) & 0xFFFFFFFFFFFFFFFF)
    if kind == "hex":
        return int(off_s, 0), bytes.fromhex(raw.strip())
    raise SystemExit(f"✗ 不支持的 --set 类型 {kind!r}（u32/f32/u64/hex）")


def main() -> int:
    ap = argparse.ArgumentParser(description="给中间块 payload 追加字节（整容器重排，保内容哈希）")
    ap.add_argument("--plain", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--row", required=True, help="目标块里的任意行绝对偏移（用来定位块号）")
    ap.add_argument("--append-hex", required=True, help="追加到该块 payload 尾部的字节（hex）")
    ap.add_argument("--set", action="append", default=[], help="绝对偏移=类型:值，可重复")
    a = ap.parse_args()

    data = pathlib.Path(a.plain).read_bytes()
    blocks = parse_blocks(data)
    h0 = murmur64(data)
    row = int(a.row, 0)
    tgt = next((i for i, b in enumerate(blocks) if b["body"] <= row < b["body"] + b["size"]), None)
    if tgt is None:
        raise SystemExit(f"✗ 行 0x{row:X} 不在任何块的 payload 里")
    extra = bytes.fromhex(a.append_hex)
    if not extra:
        raise SystemExit("✗ --append-hex 为空")
    append_at = blocks[tgt]["size"]           # 追加在旧 payload 末尾 ⇒ payload 相对偏移
    print(f"明文 {len(data):,} B  块 {len(blocks)}  目标块 {tgt}（payload {blocks[tgt]['size']:,} B）")
    print(f"追加 {len(extra)} B -> 该块 payload {blocks[tgt]['size']:,} → {blocks[tgt]['size'] + len(extra):,}"
          f"，新数组 payload 相对偏移 = {append_at}")
    print(f"原始哈希 0x{h0:016X}")

    # 1) 重建容器（除目标块与末块尾字外，payload 逐字节照抄）
    out = bytearray(struct.pack("<I", len(blocks)))
    last = len(blocks) - 1
    pad = (8 - (len(data) + len(extra)) % 8) % 8   # 让校正字 8 对齐
    tail_len = pad + TAIL
    bodies_before = []
    for i, b in enumerate(blocks):
        payload = bytearray(data[b["body"]:b["body"] + b["size"]])
        bodies_before.append(len(out))
        if i == tgt:
            payload += extra
        if i == last:
            payload += bytes(tail_len)          # 尾字宿主：末块 payload 变长
        out += b"LDLD" + struct.pack("<IIIII", b["ver"], b["type"], len(payload), b["wide"], b["extra"])
        out += payload
    word_at = len(out) - tail_len
    if word_at % 8:
        raise SystemExit(f"✗ 校正字位置 {word_at} 不是 8 对齐")

    # 2) --set 改字段
    declared = {}
    for spec in a.set:
        off, blob = parse_set(spec)
        if off + len(blob) > len(out):
            raise SystemExit(f"✗ --set 偏移 0x{off:X} 越界")
        declared[off] = blob
        out[off:off + len(blob)] = blob
        print(f"  0x{off:06X} ({len(blob)} B) -> {blob.hex()}")

    # 3) 校正字
    out[word_at:word_at + TAIL] = padding_word_for_hash(bytes(out), word_at, h0)
    out = bytes(out)

    # 4) 门禁
    checks = []

    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    b2 = parse_blocks(out)
    ok_meta = (len(b2) == len(blocks) and
               all(x["type"] == y["type"] and x["ver"] == y["ver"] and
                   x["wide"] == y["wide"] and x["extra"] == y["extra"]
                   for x, y in zip(b2, blocks)))
    grows = [len(b2[i]["payload_text"]) if "payload_text" in b2[i] else b2[i]["size"] - blocks[i]["size"]
             for i in range(len(blocks))]
    check("G1 块数/元数据不变", ok_meta, f"{len(b2)} 块")
    check("G1b payload 增长只在目标块(+K) 与末块(+pad+8)",
          all(g == 0 for i, g in enumerate(grows) if i not in (tgt, last)) and
          grows[tgt] == len(extra) and grows[last] == tail_len,
          f"grows={grows}")

    ok_prefix = all(out[b2[i]["body"]:b2[i]["body"] + blocks[i]["size"]] ==
                    data[blocks[i]["body"]:blocks[i]["body"] + blocks[i]["size"]]
                    for i in range(len(blocks)) if i not in (tgt, last))
    check("G3 其余块 payload 逐字节未动", ok_prefix)

    declared_bytes = {o + k for o, blob in declared.items() for k in range(len(blob))}
    tgt_ok = True
    tb, ob = b2[tgt]["body"], blocks[tgt]["body"]
    for k in range(blocks[tgt]["size"]):
        if ob + k in declared_bytes:
            continue
        if out[tb + k] != data[ob + k]:
            tgt_ok = False
            break
    check("G2 目标块原 payload 前缀未动（除 --set 字段）", tgt_ok)
    check("G2b 追加区就在旧 payload 末尾",
          out[tb + blocks[tgt]["size"]:tb + blocks[tgt]["size"] + len(extra)] == extra)

    pay_new = out[tb:tb + b2[tgt]["size"]]
    rel = row - ob
    ptrs = [struct.unpack_from("<Q", pay_new, rel + f)[0] for f in (0x10, 0x18, 0x20)]
    ok_ptr = all(p in (0, 0xFFFFFFFFFFFFFFFF) or 0 < p < len(pay_new) for p in ptrs)
    check("G4 目标行 payload 相对指针仍落在 payload 内", ok_ptr,
          f"ptrs={[hex(p) for p in ptrs]} payload={len(pay_new)}")

    got = murmur64(out)
    check("G5 重算 Murmur == 原值", got == h0, f"0x{got:016X}")
    ok_set = all(out[o:o + len(n)] == n for o, n in declared.items())
    check("G6 --set 读回一致", ok_set, f"{len(declared)} 处")

    if not all(c[1] for c in checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1
    dest = pathlib.Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(out)
    print(f"\n✓ 已写 {dest}（{len(out):,} B，哈希 0x{murmur64(out):016X}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
