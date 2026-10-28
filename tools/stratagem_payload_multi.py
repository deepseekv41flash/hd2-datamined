#!/usr/bin/env python3
"""stratagem_payload_multi.py -- 把一条战备行的载荷数组**整表替换成任意多条**（保内容哈希）。

为什么要它
    `stratagem_extra.py` 只会改 `+0xC8` 额外战备、`stratagem_repair.py --payload` 只能**原地**写已有槽位。
    想一次投出「一支小队」（多个不同实体）就必须**扩数组**：数量从 2 变成 N。

做法
    1. 定位目标行所在的组 `gi`，把新的 `N × 8 字节`哈希数组**追加到该组 payload 末尾**；
    2. 重建容器：组 `gi` 的 size += N*8（其余组不变），最后一组再追加 pad+8 的哈希校正区；
    3. 行内 `+0x98`（u64，payload 相对偏移）指向新数组、`+0xA0`（u32）写成数量；
    4. 用 Murmur64A 反解校正字，把整表内容哈希复原成原值。

    因为追加在 payload 末尾，**同一个组里所有既有行的位置不变**，目标行的 `abs` 仍然有效；
    其它偏移都是 payload 相对，所以扩组不影响任何行的语义。

门禁
    G1 长度 = 原长 + N*8 + pad + 8
    G2 差异 ⊆ 新数组 ∪ 目标行 +0x98/+0xA0 ∪ 目标组 size 字段 ∪ 末组 size 字段 ∪ 校正字
    G3 重算 Murmur64A == 输入哈希
    G4 新数组读回 == 声明值，且 +0x98/+0xA0 读回一致
    G6 容器重解析自洽

用法
    python tools/stratagem_payload_multi.py --plain A.plain \
        --row 138=0x75F7E96AF7DCD303,0x6B22AE8E5F669D4F,0x75BE82ED8592A6B3 \
        --out B.plain --seal
"""
from __future__ import annotations

import argparse
import os
import pathlib
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "work", "devkit", "tools"))
from murmur64 import murmur64, padding_word_for_hash                  # noqa: E402
from stratagem_extra import load, u32, names_map, label, TAIL        # noqa: E402

PAYLOAD_OFF = 0x98


def rebuild_grow(data: bytes, gs: list, grow_group: int, extra: bytes, tail_len: int) -> bytes:
    """按组重建；第 grow_group 组的 payload 末尾插 extra，最后一组再加 tail_len 校正区。"""
    out = [struct.pack("<I", len(gs))]
    last = len(gs) - 1
    for i, g in enumerate(gs):
        body = data[g["at"] + 24: g["at"] + 24 + g["size"]]
        if i == grow_group:
            body += extra
        if i == last:
            body += bytes(tail_len)
        out.append(b"LDLD")
        out.append(struct.pack("<IIIII", 1, g["gid"], len(body), 1, 0))
        out.append(body)
    return b"".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="战备行载荷数组整表替换（可扩容）")
    ap.add_argument("--plain", required=True)
    ap.add_argument("--row", required=True, metavar="ID=H1,H2,...")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seal", action="store_true")
    ap.add_argument("--pk", default=str(pathlib.Path(HERE).resolve().parents[2]
                                       / "refs/dlbin/keys/recipient.pk"))
    a = ap.parse_args()

    sid_s, _, hs_s = a.row.partition("=")
    sid = int(sid_s, 0)
    hashes = [int(x, 16) for x in hs_s.split(",") if x.strip()]

    data, gs, rows = load(a.plain)
    nm = names_map()
    by_id = {}
    for k, r in enumerate(rows):
        by_id.setdefault(u32(r["row"], 0), k)
    if sid not in by_id:
        raise SystemExit(f"✗ 战备 id {sid} 不在表里")
    k = by_id[sid]
    row_rec = rows[k]
    gi = row_rec["group"]
    old_off = struct.unpack_from("<Q", row_rec["row"], PAYLOAD_OFF)[0]
    old_cnt = struct.unpack_from("<I", row_rec["row"], PAYLOAD_OFF + 8)[0]

    # ★ 载荷数组的偏移必须是 8 的倍数 —— vanilla 全表 145 行无一例外。
    #   直接追加在旧 payload 末尾常常是 4 mod 8，会导致整行失效（运输机根本不生成，已实机踩过）。
    body_len = gs[gi]["size"]
    lead = (8 - body_len % 8) % 8
    new_off = body_len + lead                     # 追加点（payload 相对，8 对齐）
    extra = bytes(lead) + b"".join(struct.pack("<Q", h) for h in hashes)
    pad8 = (8 - (len(data) + len(extra)) % 8) % 8
    tail_len = pad8 + TAIL
    edited = bytearray(rebuild_grow(data, gs, gi, extra, tail_len))

    # 数组本体在文件里的绝对位置：组头 + 24 + 旧 payload 长度
    arr_at = gs[gi]["at"] + 24 + new_off
    # 目标行的 +0x98 / +0xA0
    struct.pack_into("<Q", edited, row_rec["abs"] + PAYLOAD_OFF, new_off)
    struct.pack_into("<I", edited, row_rec["abs"] + PAYLOAD_OFF + 8, len(hashes))

    word_at = len(edited) - TAIL
    h0 = murmur64(data)
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)

    allowed = set(range(arr_at, arr_at + len(extra)))
    allowed |= set(range(row_rec["abs"] + PAYLOAD_OFF, row_rec["abs"] + PAYLOAD_OFF + 12))
    allowed |= set(range(gs[gi]["at"] + 12, gs[gi]["at"] + 16))          # 目标组 size
    allowed |= set(range(gs[-1]["at"] + 12, gs[-1]["at"] + 16))          # 末组 size
    allowed |= set(range(word_at, word_at + TAIL))

    diff = {i for i in range(min(len(data), len(edited))) if data[i] != edited[i]}
    ok = True

    def chk(tag, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    print(f"id {sid} ({label(k, nm)}) 组 {gi}  载荷 {old_cnt} → {len(hashes)}（偏移 0x{old_off:X} → 0x{new_off:X}）")
    for i, h in enumerate(hashes):
        print(f"    slot{i}: 0x{h:016X}")
    print(f"明文 {len(data):,} B → {len(edited):,} B  hash=0x{h0:016X}")
    chk("G1 长度", len(edited) == len(data) + len(extra) + tail_len,
        f"{len(data):,} -> {len(edited):,}")
    chk("G2 差异集合", diff <= allowed, f"diff={len(diff)} 越界={sorted(diff - allowed)[:4]}")
    got = murmur64(bytes(edited))
    chk("G3 哈希复原", got == h0, f"0x{got:016X}")
    back = [struct.unpack_from("<Q", edited, arr_at + i * 8)[0] for i in range(len(hashes))]
    chk("G4 读回", back == hashes
        and struct.unpack_from("<Q", edited, row_rec["abs"] + PAYLOAD_OFF)[0] == new_off
        and struct.unpack_from("<I", edited, row_rec["abs"] + PAYLOAD_OFF + 8)[0] == len(hashes))
    try:
        from stratagem_extra import groups as parse_groups
        gs2 = parse_groups(bytes(edited))
        okp = len(gs2) == len(gs)
    except Exception as exc:                                   # noqa: BLE001
        okp = False
        gs2 = []
        print("     ", exc)
    chk("G6 容器自洽", okp, f"{len(gs2) if okp else '?'} 组")
    chk("G7 数组偏移 8 对齐", new_off % 8 == 0, f"off={new_off} mod8={new_off % 8}")
    if not ok:
        return 1
    open(a.out, "wb").write(bytes(edited))
    print(f"✓ 明文 {a.out}")
    if a.seal:
        sealed = a.out[:-6] + ".dl_bin" if a.out.endswith(".plain") else a.out + ".dl_bin"
        subprocess.run([sys.executable, os.path.join(HERE, "dlbin_seal.py"), "seal-key", a.out,
                        "--key", a.pk, "--out", sealed], check=True)
        print(f"✓ 封包 {sealed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
