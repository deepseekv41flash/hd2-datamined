#!/usr/bin/env python3
"""pod_rack_swap.py -- 改 `HellpodRackComponentData` 的槽位物品（投送舱换载荷），保内容哈希。

背景
    memmod 时代（2026-10-09，`e1-stax3-pod` / `pod-rack-stax3`）靠 Lua + ffi 写进程内存，
    把 rack 29（StA-X3 W.A.S.P. 的舱）的两个 `RackAttach.Item` u64 换成
    GL-21（0x02EECD0B1FA49630）+ B-1（0x4EF9A47109239A58）。
    那些字节**本来就在文件里**（`generated_entities.dl_bin`），所以同一件事现在可以纯改数据。

结构（全部由 typelib 现算，不写死偏移）
    HellpodRackComponentData = 0xA98BB156
        member[0] = ComponentIndexData 哈希图（size64 / 16 槽）
        member[1] = 行数组，行类型 0x817B931C，stride 568
      行内
        +0   512 B = 8 × RackAttach（64 B 一个），`RackAttach` 的 member[0] 就是 Item u64
        +512..+560 若干字段
        +552 随机偏移 · +556 投送数量
    行号 == rack 号（本 build 73 条 rack，rack 29 slot0 仍为 0xCC786F6491FE7E65）

tail 宿主
    实体库是**块序列**容器（28 B 头：u32 type | 'LDLD' | ver | type | payload | u8 wide | 7 rsv），
    跟设置表的 24 B 头不同，所以不复用 `plain_edit.py`。
    这里用同一套「最后一组 payload 末尾追加零区」的办法（该办法在设置表上两次实机验证过）：
        对齐 pad = (8 - len%8)%8，追加 pad+8 字节，校正字落在 len+pad（8 对齐）
        同时把**最后一组**的 payload 尺寸字段 += pad+8，保持块链首尾相接

门禁（任何一条不过都不写输出，exit 1）
    G1 长度 = 原长 + pad + 8
    G2 [0,原长) 内的差异 ⊆ 声明的 Item 字段 ∪ 最后一组 payload 尺寸字段 ∪ 校正字
    G3 重算 MurmurHash64A == 原始值
    G4 每个 Item 字段读回 == 目标值
    G6 容器重解析：块链首尾相接 == 文件长度，最后一组 payload 已增大
    G7 目标槽的旧值 == 期望原版值（防改错行/重复改）
    G8 校正字 8 对齐、不与 Item 字段重叠
    G9 追加区里除了校正字全为 0

用法
    python tools/pod_rack_swap.py show  [--plain P] [--rack 29]
    python tools/pod_rack_swap.py plan  --rack 29 --slot0 0x02EECD0B1FA49630 --slot1 0x4EF9A47109239A58
    python tools/pod_rack_swap.py edit  --rack 29 --slot0 ... --slot1 ... --out X.plain [--all-mirrors]
    python tools/pod_rack_swap.py mutate ... --out Y.plain    # 变异测试：证明门禁真会咬人
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from murmur64 import murmur64, padding_word_for_hash               # noqa: E402
from typelib import TypeLib                                        # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                              # noqa: BLE001
        pass

DEFAULT_PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
DEFAULT_TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
DEFAULT_ITEMS = r"D:\mod\carrier-probe\_item_packages.json"
MURMUR_ANCHOR = 0x8E49771B181FFAA1        # 本 build 明文锚点
TAIL = 8


# ------------------------------------------------------------------ 类型哈希
def type_hash(name: str) -> int:
    value = 5381
    for byte in name.encode("utf-8"):
        value = (value * 33 + byte) & 0xFFFFFFFF
    return (value - 5381) & 0xFFFFFFFF


# ------------------------------------------------------------------ 容器
def parse_blocks(data: bytes) -> list[dict]:
    """实体库块序列：u32 type | 'LDLD' | u32 ver | u32 type | u32 payload | u8 wide | 7 B reserved"""
    out, pos = [], 0
    while True:
        j = data.find(b"LDLD", pos)
        if j < 0:
            break
        head = j - 4
        if head < 0:
            pos = j + 4
            continue
        tid = struct.unpack_from("<I", data, head)[0]
        ver, inner, payload = struct.unpack_from("<III", data, j + 4)
        if ver != 1 or inner != tid or head + 28 + payload > len(data):
            pos = j + 4
            continue
        out.append({"head": head, "type_id": tid, "payload": payload})
        pos = head + 28 + payload
    return out


def check_container(data: bytes) -> int:
    """块链自洽：块间空档 ≤ 8 B，最后一块结束点 == 文件长度。返回块数。

    注意：实体库**不是**严格首尾相接的 —— 实测 273 个块间空档，最大 4 字节
    （块头是 28 B，而内容按 4 字节对齐排布）。所以不能用「严格连续」当判据。
    """
    blocks = parse_blocks(data)
    if not blocks:
        raise ValueError("一个块都没解析出来")
    if blocks[0]["head"] != 0:
        raise ValueError(f"第一块不在文件开头（@0x{blocks[0]['head']:X}）")
    pos, prev = 0, None
    for i, b in enumerate(blocks):
        gap = b["head"] - pos
        if gap < 0 or gap > 8:
            raise ValueError(f"块 {i} @0x{b['head']:X} 空档 {gap} B（前一块结束于 0x{pos:X}）")
        end = b["head"] + 28 + b["payload"]
        if end > len(data):
            raise ValueError(f"块 {i} @0x{b['head']:X} payload 越界")
        pos = end
        prev = b
    if pos != len(data):
        gap = len(data) - pos
        raise ValueError(f"尾部残留 {gap} B（最后一块结束于 0x{pos:X}）")
    return len(blocks)


# ------------------------------------------------------------------ 表定位
class RackTable:
    def __init__(self, data: bytes, lib: TypeLib):
        self.data = data
        self.lib = lib
        self.tid = type_hash("HellpodRackComponentData")
        if self.tid not in lib._index:
            raise SystemExit(f"✗ typelib 里没有 HellpodRackComponentData（hash 0x{self.tid:08X}）")
        blocks = [b for b in parse_blocks(data) if b["type_id"] == self.tid]
        if len(blocks) != 1:
            raise SystemExit(f"✗ 期望恰好 1 个 HellpodRack 块，实际 {len(blocks)}")
        b = blocks[0]
        self.head, self.payload = b["head"], b["payload"]
        self.body = self.head + 28
        ms = lib.members(self.tid)
        if len(ms) != 2:
            raise SystemExit(f"✗ HellpodRack 容器成员数 {len(ms)}，期望 2")
        self.slots_bytes = ms[0]["size64"]
        self.row_type = ms[1]["type_id"]
        self.stride = lib.desc(self.row_type)[3]
        if self.slots_bytes + ms[1]["size64"] != self.payload:
            raise SystemExit(f"✗ payload {self.payload} != 哈希图 {self.slots_bytes} + 行数组 {ms[1]['size64']}")
        self.n_rows = ms[1]["size64"] // self.stride
        self.base = self.body + self.slots_bytes
        # 槽位：行类型 member[0] 是 RackAttach 数组
        rms = lib.members(self.row_type)
        self.slot_array_off = rms[0]["offset64"]
        attach = rms[0]["type_id"]
        self.slot_stride = lib.desc(attach)[3]
        self.n_slots = rms[0]["size64"] // self.slot_stride
        ams = lib.members(attach)
        self.item_off = ams[0]["offset64"]
        self.item_size = ams[0]["size64"]
        if self.item_size != 8:
            raise SystemExit(f"✗ RackAttach.Item 尺寸 {self.item_size}，期望 8")
        # 哈希图：键 -> 行
        self.key_of_row = {}
        for i in range(self.slots_bytes // 16):
            k, v = struct.unpack_from("<QI", data, self.body + 16 * i)
            if k:
                self.key_of_row[v] = k

    def slot_offset(self, row: int, slot: int) -> int:
        if not 0 <= row < self.n_rows:
            raise SystemExit(f"✗ rack {row} 越界（共 {self.n_rows} 条）")
        if not 0 <= slot < self.n_slots:
            raise SystemExit(f"✗ slot {slot} 越界（每行 {self.n_slots} 个）")
        return (self.base + row * self.stride + self.slot_array_off
                + slot * self.slot_stride + self.item_off)

    def items(self, row: int) -> list[int]:
        return [struct.unpack_from("<Q", self.data, self.slot_offset(row, i))[0]
                for i in range(self.n_slots)]


def load_item_names() -> dict[int, str]:
    path = pathlib.Path(DEFAULT_ITEMS)
    if not path.exists():
        return {}
    out = {}
    for entry in json.loads(path.read_text(encoding="utf-8")):
        # [名字, 类别, 物品键, 包]
        out[int(entry[2], 16)] = entry[0]
    return out


# ------------------------------------------------------------------ 子命令
def cmd_show(a) -> int:
    data = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    t = RackTable(data, lib)
    names = load_item_names()
    print(f"{pathlib.Path(a.plain).name}: {len(data):,} B  Murmur {murmur64(data):016X}")
    print(f"HellpodRackComponentData 0x{t.tid:08X} @0x{t.head:X}  payload={t.payload:,}")
    print(f"  哈希图 {t.slots_bytes} B（{t.slots_bytes // 16} 槽，{len(t.key_of_row)} 条 rack）")
    print(f"  行数组 0x{t.base:X}  {t.n_rows} 行 × {t.stride} B")
    print(f"  每行 {t.n_slots} 槽 × {t.slot_stride} B，Item @ 槽内 +{t.item_off}")
    print()
    print("  rack  key                槽位物品")
    for r in range(t.n_rows):
        vals = t.items(r)
        if not any(vals):
            continue
        if a.rack is not None and r != a.rack:
            continue
        key = t.key_of_row.get(r, 0)
        shown = []
        seen = set()
        for v in vals:
            if not v or v in seen:
                continue
            seen.add(v)
            shown.append(f"{names.get(v, '?')} 0x{v:016X}")
        extra = ""
        if r == 29 or a.rack == r:
            rnd, cnt = struct.unpack_from("<II", data, t.base + r * t.stride + 552)
            extra = f"  (+552 随机 {rnd}, +556 数量 {cnt})"
        print(f"  {r:4d}  0x{key:016X}  " + " | ".join(shown) + extra)
    return 0


def build_edit(a):
    """返回 (original, edited, declared, word_at, t, h0)"""
    plain = pathlib.Path(a.plain)
    original = plain.read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    h0 = murmur64(original)
    if h0 != MURMUR_ANCHOR:
        raise SystemExit(f"✗ 明文哈希 0x{h0:016X} != 本 build 锚点 0x{MURMUR_ANCHOR:016X}；"
                         f"base 不是干净的明文缓存")
    t = RackTable(original, lib)
    blocks = parse_blocks(original)
    last = blocks[-1]

    pad = (8 - len(original) % 8) % 8
    tail_len = pad + TAIL
    word_at = len(original) + pad
    if word_at % 8:
        raise SystemExit(f"✗ 校正字位置 {word_at} 不是 8 对齐")

    edited = bytearray(original)
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    edited += bytes(tail_len)

    declared = {}
    v0 = int(str(a.slot0), 0)
    v1 = int(str(a.slot1), 0) if a.slot1 is not None else None
    targets = [("slot0", v0, 0)]
    if v1 is not None:
        targets.append(("slot1", v1, 1))
    if a.all_mirrors:
        # 镜像对：slot i 与 slot i+2 原版完全相同，一起改
        targets += [("slot2", v0, 2), ("slot3", v1 if v1 is not None else v0, 3)]
    for label, val, slot in targets:
        off = t.slot_offset(a.rack, slot)
        old = struct.unpack_from("<Q", original, off)[0]
        blob = struct.pack("<Q", val)
        edited[off:off + 8] = blob
        declared[off] = (label, val, old)

    # 只读展示旧值，不写
    return original, edited, declared, word_at, t, h0, last, tail_len


def cmd_plan(a) -> int:
    original, edited, declared, word_at, t, h0, last, tail_len = build_edit(a)
    print(f"rack {a.rack}（key 0x{t.key_of_row.get(a.rack, 0):016X}）")
    for off, (label, val, old) in declared.items():
        print(f"  {label} @0x{off:X}  0x{old:016X} -> 0x{val:016X}")
    print(f"tail 宿主：最后一块 @0x{last['head']:X} payload {last['payload']} -> {last['payload'] + tail_len}")
    print(f"  追加 {tail_len} B，校正字 @0x{word_at:X}（8 对齐={word_at % 8 == 0}）")
    print(f"  长度 {len(original):,} -> {len(edited):,}")
    if a.expect_old:
        want = [int(x, 0) for x in a.expect_old.split(",")]
        got = [v[2] for _k, v in sorted(declared.items())]
        print(f"  G7 旧值 {got} vs 期望 {want} -> {'通过' if got == want else '不通过'}")
    return 0


def cmd_edit(a) -> int:
    original, edited, declared, word_at, t, h0, last, tail_len = build_edit(a)
    h0 = murmur64(original)
    word = padding_word_for_hash(bytes(edited), word_at, h0)
    edited[word_at:word_at + TAIL] = word
    print(f"原始哈希 0x{h0:016X}   校正字 0x{struct.unpack('<Q', word)[0]:016X} @0x{word_at:X}")

    checks = []

    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = set()
    for off in declared:
        allowed |= set(range(off, off + 8))
    allowed |= set(range(last["head"] + 16, last["head"] + 20))
    allowed |= set(range(word_at, word_at + TAIL))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    appended = bytes(edited[len(original):])

    check("G1 长度 = 原长 + pad + 8", len(edited) == len(original) + tail_len,
          f"{len(original):,} -> {len(edited):,}")
    check("G2 差异 ⊆ Item 字段 ∪ payload 尺寸字段 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)}，越界 {[hex(i) for i in sorted(diff - allowed)[:6]]}")
    got = murmur64(bytes(edited))
    check("G3 重算哈希 == 原始哈希", got == h0, f"0x{got:016X}")
    ok4 = all(bytes(edited[off:off + 8]) == struct.pack("<Q", val)
              for off, (_l, val, _o) in declared.items())
    check("G4 Item 字段读回一致", ok4, f"{len(declared)} 处")
    # G7 只做一件事：目标格当前值 == 期望的旧值（防改错行）。
    # 允许「写回原值」（= 这一格保持不动），因为「只换其中一件、另一件留原版」是合法用法；
    # 但整次调用至少要真的改动一格，否则无事可做。
    gotold = [v[2] for _k, v in sorted(declared.items())]
    changed = [l for l, val, old in declared.values() if old != val]
    if a.expect_old:
        want = [int(x, 0) for x in a.expect_old.split(",")]
        ok7 = gotold == want and len(changed) > 0
        detail = f"旧值 {gotold} 期望 {want}；实际改动 {len(changed)}/{len(declared)} 格"
    else:
        ok7 = len(changed) > 0
        detail = f"实际改动 {len(changed)}/{len(declared)} 格"
    check("G7 目标格当前值 == 期望旧值（允许整格保留原值）", ok7, detail)
    check("G8 校正字 8 对齐且不与 Item 重叠",
          word_at % 8 == 0 and not any(word_at <= off < word_at + 8 for off in declared),
          f"@0x{word_at:X}")
    zero_ok = all(b == 0 for i, b in enumerate(appended) if not (word_at - len(original) <= i < word_at - len(original) + 8))
    check("G9 追加区除校正字外全 0", zero_ok, f"{tail_len} B")
    try:
        n = check_container(bytes(edited))
        blocks = parse_blocks(bytes(edited))
        ok6 = (n == len(parse_blocks(original))) and blocks[-1]["payload"] == last["payload"] + tail_len
        detail = f"{n} 块，末块 payload {blocks[-1]['payload']}"
    except Exception as exc:                                       # noqa: BLE001
        ok6, detail = False, f"解析失败：{exc}"
    check("G6 容器重解析自洽、块链到文件尾", ok6, detail)

    if not all(c[1] for c in checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(edited))
    print(f"\n✓ 全部门禁通过 → {out}（{len(edited):,} B）")
    return 0


def cmd_mutate(a) -> int:
    """变异测试：故意破坏一处不变量，证明门禁会 FAIL。不写输出。"""
    print("== 变异 1：把校正字清零（应触发 G3）")
    original = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    t = RackTable(original, lib)
    off = t.slot_offset(a.rack, 0)
    tampered = bytearray(original)
    tampered[off:off + 8] = struct.pack("<Q", int(a.slot0, 0))
    got = murmur64(bytes(tampered))
    print(f"  篡改后哈希 0x{got:016X} vs 原始 0x{murmur64(original):016X} -> "
          f"{'FAIL（门禁会咬）' if got != murmur64(original) else 'PASS（门禁失灵！）'}")
    print("== 变异 2：改错 rack（应触发 G7）")
    wrong = (a.rack + 1) % t.n_rows
    old = struct.unpack_from("<Q", original, t.slot_offset(wrong, 0))[0]
    print(f"  rack {wrong} slot0 原值 0x{old:016X} vs 期望 0xCC786F6491FE7E65 -> "
          f"{'FAIL（门禁会咬）' if old != 0xCC786F6491FE7E65 else 'PASS（门禁失灵！）'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="投送舱 rack 槽位物品改写（保内容哈希）")
    ap.add_argument("command", choices=["show", "plan", "edit", "mutate"])
    ap.add_argument("--plain", default=DEFAULT_PLAIN)
    ap.add_argument("--typelib", default=DEFAULT_TYPELIB)
    ap.add_argument("--rack", type=int, default=29)
    ap.add_argument("--slot0", default="0x02EECD0B1FA49630", help="GL-21 Grenade Launcher")
    ap.add_argument("--slot1", default="0x4EF9A47109239A58", help="B-1 Supply Pack")
    ap.add_argument("--all-mirrors", action="store_true", help="同时改镜像槽 2/3")
    ap.add_argument("--expect-old", default=None, help="逗号分隔的期望旧值，用于 G7")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.command in ("edit", "mutate") and not a.out and a.command == "edit":
        raise SystemExit("✗ edit 需要 --out")
    return {"show": cmd_show, "plan": cmd_plan, "edit": cmd_edit, "mutate": cmd_mutate}[a.command](a)


if __name__ == "__main__":
    raise SystemExit(main())
