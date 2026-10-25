#!/usr/bin/env python3
"""战备表「额外战备」示例（build `26088801`，纯标准库，只读）。

这张表是**仓库自带明文** `tables/generated_stratagem_settings.dl_bin`（82,384 B）：
    u32 块数(12) + 每块 `"LDLD" | ver | id | payload_size | wide | extra`(24) + payload
    payload = u64 0x10 | u64 行数 | 行×400 B | 块尾字符串池
    行内：+0x00 条目 id · +0x04 物品 key · +0x10/+0x14 内部名字符串指针（相对块 payload）
          +0x50 使用次数（Eagle 行 = 每次 Rearm 后的次数）· +0x68 冷却 f32
          +0x98/+0xA0 载荷实体数组（payload 偏移 / 个数）
          +0xC8 **额外战备**（带上本战备时附赠的另一条战备 id；0 = 无）

这个字段就是「把未发布战备带进任务」的入口（不占配装位、不进军械库、引擎会顺着链跟、成环会崩）。
写入请用 `tools/stratagem_extra.py`（保哈希 + G1–G7 门禁），本示例只做读与自检。

用法：
    python examples/stratagem_extra_demo.py                     # 打印 153 行摘要 + 未发布候选
    python examples/stratagem_extra_demo.py --verify            # 自检，非 0 退出码 = 不符
    python examples/stratagem_extra_demo.py --table <别的明文>   # 换一张同结构表
"""
from __future__ import annotations

import argparse
import os
import struct
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

STRIDE = 400
EXTRA_OFF = 0xC8
USES_OFF = 0x50
CD_OFF = 0x68
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TABLE = os.path.join(HERE, "..", "tables", "generated_stratagem_settings.dl_bin")

# 本 build 逐条实机验证过的「可用」清单（编号 = 行 +0x00 条目 id）
VERIFIED = {
    138: "M-104 Incinerator FRV（车辆）",
    36: "EAGLE. (NOT USED) ADDITIONAL STRAFING RUNS（额外扫射，4 次充能）",
    150: "EAGLE. (NOT USED) AIR-TO-AIR MISSLES（会锁地面目标）",
    64: "ORBITAL. WALKING BARRAGE SMOKE（烟幕行走弹幕）",
    145: "ORBITAL CONFETTI（纸屑彩蛋）",
    50: "EAGLE FLY BY（飞鹰掠过，纯演出）",
    5: "MISSIONS. ORBITAL ILLUMINATION FLARE（照明弹）",
}
HALF_BAKED = {119: "SEAF Squad（能叫但运输机投下空的）"}


def load(path: str):
    data = open(path, "rb").read()
    n = struct.unpack_from("<I", data, 0)[0]
    off, blocks = 4, []
    for _ in range(n):
        if data[off:off + 4] != b"LDLD":
            raise SystemExit(f"✗ 块头不是 LDLD @{off:#x}")
        _ver, gid, size, _wide, _extra = struct.unpack_from("<IIIII", data, off + 4)
        blocks.append((gid, data[off + 24:off + 24 + size]))
        off += 24 + size
    rows = []
    for gi, (_gid, p) in enumerate(blocks):
        if len(p) < 16 or struct.unpack_from("<Q", p, 0)[0] != 0x10:
            continue
        cnt = struct.unpack_from("<Q", p, 8)[0]
        for i in range(cnt):
            rows.append((gi, i, p[16 + i * STRIDE:16 + (i + 1) * STRIDE]))
    return blocks, rows


def u32(row: bytes, off: int) -> int:
    return struct.unpack_from("<I", row, off)[0]


def f32(row: bytes, off: int) -> float:
    return struct.unpack_from("<f", row, off)[0]


def text(blocks, gi: int, row: bytes) -> str:
    """内部名：`+0x10`/`+0x14` 是块 payload 内的字符串偏移。"""
    p = blocks[gi][1]
    at = u32(row, 0x10) + u32(row, 0x14) * (1 << 32)
    if not (0 <= at < len(p)):
        return ""
    end = p.find(b"\0", at)
    return p[at:end].decode("utf-8", "replace") if end > at else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="战备表 +0xC8 额外战备 只读示例")
    ap.add_argument("--table", default=DEFAULT_TABLE)
    ap.add_argument("--verify", action="store_true", help="自检并返回退出码")
    a = ap.parse_args()

    blocks, rows = load(a.table)
    print(f"表：{os.path.normpath(a.table)}")
    print(f"块 {len(blocks)} · 行 {len(rows)} · 行宽 {STRIDE} B")
    width = max(len(text(blocks, gi, r)) for gi, _i, r in rows)

    if not a.verify:
        print(f"\n{'id':>4} {'额外':>5} {'次数':>10} {'冷却':>6}  {'内部名'}")
        for gi, _i, r in rows:
            sid, extra, uses = u32(r, 0), u32(r, EXTRA_OFF), u32(r, USES_OFF)
            uses_txt = "∞" if uses >= 0xFFFFFFFF else str(uses)
            name = text(blocks, gi, r)
            mark = " ★" if sid in VERIFIED else (" ⚠" if sid in HALF_BAKED else "")
            if sid in VERIFIED or sid in HALF_BAKED or extra:
                print(f"{sid:>4} {extra:>5} {uses_txt:>10} {f32(r, CD_OFF):>6.0f}  {name}{mark}")

    # ---------------- 自检 ----------------
    checks = []
    def check(tag, cond, detail=""):
        checks.append(bool(cond))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    if a.verify:
        print("\n== 自检 ==")
        check("行数 153、块数 12", len(rows) == 153 and len(blocks) == 12, f"{len(rows)} 行 / {len(blocks)} 块")
        by = {u32(r, 0): (gi, r) for gi, _i, r in rows}
        check("M-104 = id 138，key 0xA9A97CD7", 138 in by and u32(by[138][1], 0x4) == 0xA9A97CD7)
        check("M-104 内部名含 Ramming Flamethrower",
              "Ramming Flamethrower" in text(blocks, by[138][0], by[138][1]))
        eagles = [sid for sid in by if text(blocks, by[sid][0], by[sid][1]).startswith("EAGLE.")]
        check("所有 EAGLE.* 行的 +0xC8 都是 51（EAGLE. REARM）",
              all(u32(by[s][1], EXTRA_OFF) in (0, 51) for s in eagles) and
              all(u32(by[s][1], EXTRA_OFF) == 51 for s in eagles if s != 51),
              f"{len(eagles)} 行")
        check("7 条已验证 id 都在表里", all(sid in by for sid in VERIFIED))
        check("119 仍在表里（半成品，空投为空）", 119 in by)

    bad = checks and not all(checks)
    if a.verify:
        print("\n" + ("✗ 有检查不过" if bad else "✓ 全部通过"))
        print("写入入口：python tools/stratagem_extra.py --host 34 --extra 138 --out x.plain --seal")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
