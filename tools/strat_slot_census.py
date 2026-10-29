#!/usr/bin/env python3
"""strat_slot_census.py -- 战备表 153 行的「资源加载声明口」存量普查（只读）。

要回答的问题
    `StratagemSettings` 每一行有两个能装包 id 的字段：`+0xA8`（u64，自由包 id）与
    `+0xF8`（u32，ObjectLoadout 条目 id ⇒ 间接指到那把武器的包）。原版 153 行里
    **大部分只用了其中一个、甚至一个都没用**。这些没用上的就是**空槽**：
    可以把我们要加载的包填进去，不占用任何已有物品的声明。

怎么判定「装包口」
    不是靠「值 ∈ 包集合」猜（那样永远看不见空槽），而是**按结构穷举**：
    用 typelib 取出该行类型的全部成员，逐个 8 字节对齐字段扫 153 行，
    统计「非零 / 互异 / 值落在 LoadoutPackageComponentData 的 307 个包集合里」。
    结果只有 `+0xA8` 一个字段出现过包 id（114 行），其余 u64 字段 0 命中 ⇒ 装包口只有两个。

三个输入
    plaintext            D:\\mod\\refs\\dlbin\\plaintext-26251122\\generated_stratagem_settings.dl_bin
    typelib              同目录 dl_library.dl_typelib（判行类型 / 行大小）
    行名                 refs/stratagem-display-names.json（153 条，**按行序**对齐）

用法
    python tools/strat_slot_census.py                # 153 行全表
    python tools/strat_slot_census.py --free         # 只看有空槽的行
    python tools/strat_slot_census.py --free --both  # 只看两个槽全空的行
    python tools/strat_slot_census.py --row 57       # 单行详情
    python tools/strat_slot_census.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pod_loadout import (                                       # noqa: E402
    Data, LOEPKG_TID, LOE_TID, STRAT_ROW, OFF_A8, OFF_F8,
)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                           # noqa: BLE001
        pass

ROW_NAMES = HERE.parent / "refs" / "stratagem-display-names.json"
OFF_ID = 0x00          # u32 战备 id（本 build 是 1..153 的一个排列）
OFF_DUP = 0x04         # u32 多半等于 +0xF8（29/37），语义未定
OFF_NAME = 0x10        # u64 payload 相对偏移 → 内部名（"TEAM WEAPONS. RAILGUN"）
OFF_KEY = 0x18         # u64 payload 相对偏移 → 本地化键（"nui_weapon_support_railgun_name"）
OFF_DEAD = 0x88        # u64 成员，153 行全 0 —— 结构上存在但原版从不使用


def _cstr(buf: bytes, at: int, limit: int = 160) -> str:
    if at <= 0 or at >= len(buf):
        return ""
    end = buf.find(b"\0", at, min(len(buf), at + limit))
    if end <= at:
        return ""
    raw = buf[at:end]
    return raw.decode("ascii", "replace")


def internal_names(d: Data, rows: list[tuple[int, int]]) -> tuple[list[str], list[str]]:
    """行内 `+0x10` / `+0x18` 是 **payload 相对**的字符串偏移，指向这一行自己的内部名与本地化键。

    这比 `refs/stratagem-display-names.json` 可靠：那份是**按行序**贴上去的，个别行贴错了
    （本 build 里 `MISSIONS. EXTRACTION` 被贴成 "Extraction Beacon"、`MISSIONS. EXTRACTION BEACON`
    被贴成 "Extraction"，正好错位）。名字用于 `--fill` 选择目标时，错位会改错行。
    """
    names, keys = [], []
    for base, body in rows:
        names.append(_cstr(d.strat, body + struct.unpack_from("<Q", d.strat, base + OFF_NAME)[0]))
        keys.append(_cstr(d.strat, body + struct.unpack_from("<Q", d.strat, base + OFF_KEY)[0]))
    return names, keys


# ------------------------------------------------------------------ 行枚举
def strat_rows(d: Data) -> list[tuple[int, int]]:
    """按表顺序给出 153 个 (行基址, 所属块的 payload 起点)。"""
    out = []
    for _tid, rbase, count in d._strat_tables():
        out.extend((rbase + i * STRAT_ROW, rbase - 16) for i in range(count))
    return out


def load_names() -> list[dict]:
    if not ROW_NAMES.exists():
        return []
    return json.loads(ROW_NAMES.read_text(encoding="utf-8"))["rows"]


# ------------------------------------------------------------------ 反查
def reverse_maps(d: Data):
    """包 id → 物品键集合；Loadout 条目 id → 物品键集合。"""
    pm, pstride, prows, pbase = d.hashmap(LOEPKG_TID)
    pkg2item: dict[int, list[int]] = {}
    for key, r in pm.items():
        if r < prows:
            pkg = struct.unpack_from("<Q", d.ent, pbase + pstride * r + 8)[0]
            pkg2item.setdefault(pkg, []).append(key)
    lm, lstride, lrows, lbase = d.hashmap(LOE_TID)
    loe2item: dict[int, list[int]] = {}
    for key, r in lm.items():
        if r < lrows:
            lid = struct.unpack_from("<I", d.ent, lbase + lstride * r)[0]
            loe2item.setdefault(lid, []).append(key)
    return pkg2item, loe2item


def item_label(d: Data, key: int) -> str:
    e = d.names().get(key)
    return e["name"] if e else "0x%016X" % key


# ------------------------------------------------------------------ 普查
def census(d: Data) -> list[dict]:
    names = load_names()
    pkg2item, loe2item = reverse_maps(d)
    rws = strat_rows(d)
    internals, keys = internal_names(d, rws)
    rows = []
    for idx, (base, _body) in enumerate(rws):
        sid = struct.unpack_from("<I", d.strat, base + OFF_ID)[0]
        dup = struct.unpack_from("<I", d.strat, base + OFF_DUP)[0]
        a8 = struct.unpack_from("<Q", d.strat, base + OFF_A8)[0]
        f8 = struct.unpack_from("<I", d.strat, base + OFF_F8)[0]
        dead = struct.unpack_from("<Q", d.strat, base + OFF_DEAD)[0]
        a8_items = [item_label(d, k) for k in pkg2item.get(a8, [])] if a8 else []
        f8_items = [item_label(d, k) for k in loe2item.get(f8, [])] if f8 else []
        display = ""
        if idx < len(names):
            display = names[idx].get("display_name") or names[idx].get("internal_name") or ""
        rows.append({
            "idx": idx, "row_base": base, "strat_id": sid,
            "name": internals[idx],          # 行内自带，最可靠
            "display": display,              # 外部名单，个别行贴错
            "key": keys[idx],
            "a8": a8, "a8_items": a8_items, "f8": f8, "f8_items": f8_items,
            "dup04": dup, "dead88": dead,
            "a8_free": a8 == 0, "f8_free": f8 == 0,
        })
    return rows


def slot_class(r: dict) -> str:
    if r["a8_free"] and r["f8_free"]:
        return "both_free"
    if r["a8_free"]:
        return "a8_free"
    if r["f8_free"]:
        return "f8_free"
    return "full"


CLASS_CN = {"both_free": "两槽全空", "a8_free": "仅 +0xA8 空",
            "f8_free": "仅 +0xF8 空", "full": "两槽已满"}


def item_names(r: dict) -> str:
    parts = []
    if r["a8"]:
        parts.append("包→" + ("/".join(r["a8_items"]) if r["a8_items"] else "?"))
    if r["f8"]:
        parts.append("武器→" + ("/".join(r["f8_items"]) if r["f8_items"] else "?"))
    return " ".join(parts) or "（无物品）"


# ------------------------------------------------------------------ 输出
def print_table(rows: list[dict]) -> None:
    print(f"{'idx':>3} {'行基址':>7} {'id':>4} {'+0xA8':<19} {'+0xF8':<11} {'类别':<12} 名字  /  已占用")
    print("-" * 132)
    for r in rows:
        a8 = f"0x{r['a8']:016X}" if r["a8"] else "0".rjust(18)
        f8 = f"0x{r['f8']:08X}" if r["f8"] else "0".rjust(10)
        print(f"{r['idx']:>3} {r['row_base']:#7x} {r['strat_id']:>4} {a8:<19} {f8:<11} "
              f"{CLASS_CN[slot_class(r)]:<12} {r['name']}  /  {item_names(r)}")


def print_summary(rows: list[dict]) -> None:
    from collections import Counter
    c = Counter(slot_class(r) for r in rows)
    print()
    print(f"共 {len(rows)} 行")
    print(f"  两槽已满   {c['full']:>3} 行   ← 原版已经把两个口都用了")
    print(f"  仅 +0xA8 空 {c['a8_free']:>3} 行   ← 可再塞一个**任意包**")
    print(f"  仅 +0xF8 空 {c['f8_free']:>3} 行   ← 可再指一个**有 Loadout 条目的物品**（间接装它的包）")
    print(f"  两槽全空   {c['both_free']:>3} 行   ← 一件物品都不送的战备（增援/撤离/任务目标…）")
    dead = sum(1 for r in rows if r["dead88"] == 0)
    print(f"\n结构旁证：+0x88 是 u64 成员，{dead}/{len(rows)} 行全 0 —— 原版从不使用（未验证能否当第三口）")


def cmd_row(d: Data, rows: list[dict], idx: int) -> int:
    if not 0 <= idx < len(rows):
        raise SystemExit(f"✗ idx 必须在 0..{len(rows) - 1}")
    r = rows[idx]
    print(f"第 {idx} 行  基址 {r['row_base']:#x}  战备 id {r['strat_id']}  {r['name']}")
    print(f"  +0x00 id      = {r['strat_id']}")
    print(f"  +0x04 ?       = 0x{r['dup04']:08X}")
    print(f"  +0x88 死槽    = 0x{r['dead88']:016X}")
    print(f"  +0xA8 包      = 0x{r['a8']:016X}   {'（空）' if r['a8_free'] else ''}"
          f"{'→ ' + '/'.join(r['a8_items']) if r['a8_items'] else ''}")
    print(f"  +0xF8 条目 id = 0x{r['f8']:08X}   {'（空）' if r['f8_free'] else ''}"
          f"{'→ ' + '/'.join(r['f8_items']) if r['f8_items'] else ''}")
    print(f"  绝对偏移：+0xA8 = {r['row_base'] + OFF_A8:#x}   +0xF8 = {r['row_base'] + OFF_F8:#x}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="战备表资源加载声明口普查（只读）")
    ap.add_argument("--free", action="store_true", help="只看有空槽的行")
    ap.add_argument("--both", action="store_true", help="只看两槽全空的行")
    ap.add_argument("--row", type=int, default=None, help="单行详情")
    ap.add_argument("--json", default=None, help="把普查结果写到 JSON")
    a = ap.parse_args()

    d = Data()
    rows = census(d)

    if a.json:
        pathlib.Path(a.json).write_text(
            json.dumps({"count": len(rows), "rows": rows}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"✓ 写入 {a.json}")

    if a.row is not None:
        return cmd_row(d, rows, a.row)

    sel = rows
    if a.both:
        sel = [r for r in rows if slot_class(r) == "both_free"]
    elif a.free:
        sel = [r for r in rows if slot_class(r) != "full"]
    print_table(sel)
    if not a.json:
        print_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
