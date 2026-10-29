#!/usr/bin/env python3
"""passive_bonus_edit.py -- 改 `generated_customization_passive_bonuses.dl_bin`（护甲被动表），保内容哈希。

为什么单独写一个工具
    这张表是「每个被动一个 LDLD 块」，块内有两个**变长数组**（pm 16 B / sm 12 B）。
    往里加一行会让**中间某一块的 payload 变长**，后面所有块的偏移全部平移 ——
    `plain_edit.py` 只会在文件尾追加，改不了这种结构。所以这里做的是**整容器重排 + 尾字校正**。

数据结构（本 build 与第三方 `护甲多被动` 的 boot.lua 独立印证，见
`docs/cases/RECON-ARMOR-MULTI-PASSIVE.md`）

    u32 组数（=33）
    每组：24 B 头 ['LDLD'][ver][type=0x63CE0FEB][payload_size][wide=1][4 B]
          payload：+0 id(u32) +4 name_id(u32) +16 pm_off(u64) +24 pm_cnt(u64)
                   +32 sm_off(u64，空 = -1) +40 sm_cnt(u64) +48 保留 8 B
                   pm 行 16 B = {stat 键 u32, 类型 u32, 数值 f32, 描述 loc id u32}
                   sm 行 12 B = {stat 槽位 u32, 标志 u32, 数值 f32}

用法
    python tools/passive_bonus_edit.py --show
    python tools/passive_bonus_edit.py \\
        --add-pm "16:0xC8CCB6FA:1:30.0:text=0x3415CAF3" --out out/x.plain

    --add-pm 的语法：`<perk>:<key>:<type>:<value>[:text=0x..]`，可重复。

坑（e15 那次的教训）
    * **只看 key 的 reader**：`description-only` 的键（`CC530B21` `35F17BEC` `B4F88129`
      `33C9C713` `AD5289FE` `22035F3C`）叠了也不生效，加了只是多一行文案。
    * pm 是「描述/声明」、sm 是「引擎真正给的数值」；本轮只动 pm 里的 `direct` 键。
    * 文本 id 给 0 = 不在护甲卡片上显示（第三方 mod 隐藏额外描述就是这么做的）。

门禁
    G1 容器重解析自洽、组数不变        G2 目标块行数与内容 == 预期
    G3 其余块 payload 逐字节未动       G4 重算 Murmur == 原版哈希
    G5 校正字 8 对齐、落在尾部追加区
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash        # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                       # noqa: BLE001
        pass

DEFAULT = r"D:\mod\refs\dlbin\plaintext-26251122\generated_customization_passive_bonuses.dl_bin"
PASSIVE_TYPE = 0x63CE0FEB
HEADER = 24
TAIL = 8
PM_W, SM_W = 16, 12


def parse(data: bytes) -> list[dict]:
    count = struct.unpack_from("<I", data, 0)[0]
    pos, out = 4, []
    for _ in range(count):
        hdr = data[pos:pos + HEADER]
        if hdr[:4] != b"LDLD":
            raise SystemExit(f"✗ 块头不是 LDLD @{pos:#x}")
        ver, tid, size, wide = struct.unpack_from("<IIII", hdr, 4)
        if tid != PASSIVE_TYPE:
            raise SystemExit(f"✗ 块类型 0x{tid:08X} ≠ 0x{PASSIVE_TYPE:08X} @{pos:#x}")
        out.append({"head": pos, "payload": bytearray(data[pos + HEADER:pos + HEADER + size])})
        pos += HEADER + size
    if pos != len(data):
        raise SystemExit(f"✗ 尾部残留 {len(data) - pos} B")
    return out


def decode(p: bytearray) -> dict:
    pid, name_id = struct.unpack_from("<II", p, 0)
    pm_off, pm_cnt, sm_off, sm_cnt = struct.unpack_from("<QQQQ", p, 16)
    pm = [bytes(p[pm_off + i * PM_W: pm_off + (i + 1) * PM_W]) for i in range(pm_cnt)] if pm_cnt else []
    sm = [bytes(p[sm_off + i * SM_W: sm_off + (i + 1) * SM_W]) for i in range(sm_cnt)] if sm_cnt else []
    tail8 = bytes(p[48:56])
    return {"id": pid, "name_id": name_id, "pm": pm, "sm": sm, "tail8": tail8}


def encode(rec: dict) -> bytearray:
    out = bytearray(56)
    struct.pack_into("<II", out, 0, rec["id"], rec["name_id"])
    pm_off = 56 if rec["pm"] else 0
    sm_off = (56 + len(rec["pm"]) * PM_W) if rec["sm"] else 0xFFFFFFFFFFFFFFFF
    struct.pack_into("<QQQQ", out, 16, pm_off, len(rec["pm"]), sm_off, len(rec["sm"]))
    out[48:56] = rec["tail8"]
    for r in rec["pm"]:
        out += r
    for r in rec["sm"]:
        out += r
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="护甲被动表：加/看 pm 行（保内容哈希）")
    ap.add_argument("--plain", default=DEFAULT)
    ap.add_argument("--out", default=None)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--add-pm", action="append", default=[],
                    help="<perk>:<key>:<type>:<value>[:text=0x..]")
    ap.add_argument("--add-sm", action="append", default=[],
                    help="<perk>:<stat 槽位>:<value>[:flag]（sm 才是引擎真正施加的数值）")
    a = ap.parse_args()

    original = pathlib.Path(a.plain).read_bytes()
    vanilla_hash = murmur64(original)
    blocks = parse(original)
    recs = [decode(b["payload"]) for b in blocks]
    print(f"容器 {len(blocks)} 组  type 0x{PASSIVE_TYPE:08X}  原版 Murmur 0x{vanilla_hash:016X}")

    if a.show or (not a.add_pm and not a.add_sm):
        print(f"{'id':>3} {'块':>7} {'pm':>3} {'sm':>3}  pm 行")
        for b, r in zip(blocks, recs):
            desc = " ".join(
                f"[0x{struct.unpack_from('<I', row, 0)[0]:08X} t{struct.unpack_from('<I', row, 4)[0]} "
                f"{struct.unpack_from('<f', row, 8)[0]:g}]" for row in r["pm"])
            print(f"{r['id']:>3} {b['head']:#7x} {len(r['pm']):>3} {len(r['sm']):>3}  {desc}")
        return 0

    by_id = {r["id"]: r for r in recs}
    touched = set()
    for spec in a.add_pm:
        parts = spec.split(":")
        if len(parts) < 4:
            raise SystemExit(f"✗ --add-pm 语法：<perk>:<key>:<type>:<value>[:text=0x..]，收到 {spec!r}")
        perk, key, typ, val = int(parts[0], 0), int(parts[1], 0), int(parts[2], 0), float(parts[3])
        text = 0
        if len(parts) >= 5 and parts[4].startswith("text="):
            text = int(parts[4][5:], 0)
        rec = by_id.get(perk)
        if rec is None:
            raise SystemExit(f"✗ 没有 perk {perk}")
        row = struct.pack("<IIfI", key, typ, val, text)
        # 去重键 = 前 12 字节（键 + 类型 + 数值），与第三方 mod 同口径
        if any(r[:12] == row[:12] for r in rec["pm"]):
            print(f"  (perk {perk} 已有同样的 0x{key:08X} t{typ} {val:g}，跳过)")
            continue
        rec["pm"].append(row)
        touched.add(perk)
        print(f"  perk {perk}: +pm 0x{key:08X} type={typ} value={val:g} text=0x{text:08X}"
              f"（该 perk pm 行数 {len(rec['pm'])}）")

    for spec in a.add_sm:
        parts = spec.split(":")
        if len(parts) < 3:
            raise SystemExit(f"✗ --add-sm 语法：<perk>:<stat>:<value>[:flag]，收到 {spec!r}")
        perk, stat, val = int(parts[0], 0), int(parts[1], 0), float(parts[2])
        flag = int(parts[3], 0) if len(parts) >= 4 else 0
        rec = by_id.get(perk)
        if rec is None:
            raise SystemExit(f"✗ 没有 perk {perk}")
        row = struct.pack("<IIf", stat, flag, val)
        # 去重口径与第三方一致：整行 12 B（stat + flag + value）。
        # 早期我按前 8 B（stat+flag）去重，会连带挡掉「同一 stat 换一个值」这种加行 —— 语义更窄，已改回。
        if any(r[:12] == row[:12] for r in rec["sm"]):
            print(f"  (perk {perk} 已有完全相同的 sm stat={stat} {val:g}，跳过)")
            continue
        if any(r[:8] == row[:8] for r in rec["sm"]):
            print(f"  ⚠ perk {perk} 已有 stat={stat} 的另一条（值不同），按第三方的口径允许并存")
        rec["sm"].append(row)
        touched.add(perk)
        print(f"  perk {perk}: +sm stat={stat} value={val:g} flag={flag}（该 perk sm 行数 {len(rec['sm'])}）")

    if not touched:
        raise SystemExit("✗ 没有实际改动")

    # 重排容器
    out = bytearray(struct.pack("<I", len(blocks)))
    heads, last_payload = [], b""
    for b, r in zip(blocks, recs):
        payload = encode(r) if r["id"] in touched else bytes(b["payload"])
        heads.append(len(out))                 # ★ 记录每块**重建后**的块头位置
        last_payload = payload
        out += bytes(b"\x4c\x44\x4c\x44") + struct.pack("<III", 1, PASSIVE_TYPE, len(payload))
        out += bytes([1]) + b"\0" * 7
        out += payload
    before_tail = len(out)
    pad8 = (8 - len(out) % 8) % 8
    out += b"\0" * (pad8 + TAIL)
    # 末块 payload 尺寸同步：尾字（pad8+TAIL）寄宿在**末块**的 payload 里。
    # ★ 2026-10-24 修：原来用「原末块 payload 长度」倒推块头位置 —— 一旦**被改的正是末块**
    #   （perk 0 就是容器最后一块）就会算错、parse 走飞（报「尾部残留」）。
    #   现在直接用重建时记下的块头位置 + 该块重建后的真实 payload 长度。
    last_head = heads[-1]
    last_payload_len = len(last_payload)
    struct.pack_into("<I", out, last_head + 12,   # 设置表头：'LDLD'|ver|type|★payload|wide|4B
                     last_payload_len + pad8 + TAIL)
    word_at = before_tail + pad8
    if word_at % 8:
        raise SystemExit("✗ 校正字未对齐")
    out[word_at:word_at + TAIL] = padding_word_for_hash(bytes(out), word_at, vanilla_hash)

    checks = []
    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    blocks2 = parse(bytes(out))
    check("G1 容器重解析自洽、组数不变", len(blocks2) == len(blocks), f"{len(blocks2)} 组")
    ok = True
    for b, b2, r in zip(blocks, blocks2, recs):
        r2 = decode(b2["payload"])
        if r["id"] in touched:
            if len(r2["pm"]) != len(r["pm"]) or r2["pm"] != [bytes(x) for x in r["pm"]]:
                ok = False
        else:
            # 末块 payload 会被尾字撑大，所以只比原长度那一段
            if bytes(b2["payload"])[:len(b["payload"])] != bytes(b["payload"]):
                ok = False
    check("G2 目标块 == 预期、其余块逐字节未动", ok)
    check("G4 重算 Murmur == 原版哈希", murmur64(bytes(out)) == vanilla_hash, f"0x{vanilla_hash:016X}")
    check("G5 校正字 8 对齐且在尾部追加区", word_at % 8 == 0 and word_at >= before_tail)

    if not all(c for _, c in checks):
        raise SystemExit("✗ 门禁未过，未写出")
    if not a.out:
        raise SystemExit("✗ 要写文件请给 --out")
    pathlib.Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.out).write_bytes(bytes(out))
    print(f"\n✓ 全部门禁通过 → {a.out}（{len(original):,} → {len(out):,} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
