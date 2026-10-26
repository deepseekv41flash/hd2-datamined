#!/usr/bin/env python3
"""state_machine_edit.py -- 读/改 Stingray `state_machine` 资源（换 `layer.DefaultState` 等）。

为什么需要它
    「空投舱炮塔」类的壳（`aa_turret` / `turret_machinegun_gpmg` …）有一套**部署状态机**：
    落地后由状态机切到"展开"姿态。把它当**载具挂载件**时不会跑部署流程 ⇒ 永远停在默认（折叠）态，
    表现为：模型陷进车里、开火点在炮管外空中。
    **把 layer0 的 `DefaultState` 改成"展开"那一档，就能在挂载状态直接以展开形态出场**
    （2026-10-26 ✓✓ 实机：AC-8 哨戒挂 M-102 炮手位，展开形态 + 原点/开火点/开火动画全对）。

格式来源
    xypwn/filediver `stingray/state_machine`（BSD-3）：`rawStateMachine` 头 15×u32 →
    组偏移表 → 每层 `{Magic, DefaultState, Count, Offsets[]}` → 每个 state：
    `Name(Hash64) | Type | 动画哈希表 | 权重表 | Unk01 | Loop(bool) | Additive(bool)
     | AnimationEvent{n,off} | StateTransitionLinks{n,off} | … | EmitEndEvent(u32) | EndTransitionTime(f32) | …`
    `AnimationEvent = {EventName(ThinHash u32), LinkIndex(i32)}`，
    `Link = {Index(u32), BlendTime(f32), Type(u32), Beat(u32)}`。

    ⇒ **"部署过渡结束事件"（EmitEndEvent）在该 state 的 AnimationEvent 表里查到的 Link，
       就是"部署完成态"**。这条规则在 AC-8 上已被实机证实（EmitEndEvent=DeployDone → state2，
       把默认态改成 state2 后哨戒以展开形态出场）。`--decode` 就是打印这条链。

用法
    python tools/state_machine_edit.py --show  sm.bin
    python tools/state_machine_edit.py --show  sm.bin --layer 0
    python tools/state_machine_edit.py --decode sm.bin            # 事件/过渡/部署完成态
    python tools/state_machine_edit.py --decode --names <csv> sm.bin
    python tools/state_machine_edit.py --set 0=2 --out sm_new.bin  sm.bin     # layer0 的默认态改成 2

配套（改完怎么用）
    它是**资源**（不是 .dl_bin）：改完用 `tools/resource_patch.py build` 打成
    `data/9ba626afa44a3aa3.patch_<N>`（entry type=`A486D4045106165C`，id=该 SM 的 file_id）。
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import struct
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

HDR = ["unk00", "group_count", "groups_off", "event_hash_count", "event_hash_off",
       "var_count", "var_map_off", "opacity_count", "opacity_off",
       "unk0_count", "unk0_off", "unk1_count", "unk1_off", "unk2_count", "unk2_off"]
STATE_TYPES = {0: "Clip", 1: "Empty", 2: "Blend", 3: "Time", 4: "Unknown", 5: "Ragdoll"}
LINK_TYPES = {0: "Immediate", 1: "WaitEnd", 2: "SyncBeatClosestImmediate",
              3: "WaitUntilBeat", 4: "SyncPercentageImmediate", 5: "SyncInversePercentageImmediate"}


def header(b: bytes) -> dict:
    v = struct.unpack_from("<15I", b, 0)
    return dict(zip(HDR, v))


def layers(b: bytes, h: dict) -> list[dict]:
    out = []
    if not h["group_count"] or not h["groups_off"]:
        return out
    go = h["groups_off"]
    cnt = struct.unpack_from("<I", b, go)[0]
    offs = struct.unpack_from("<%dI" % cnt, b, go + 4)
    for i, o in enumerate(offs):
        base = go + o
        magic, default = struct.unpack_from("<II", b, base)
        n = struct.unpack_from("<I", b, base + 8)[0]
        st_offs = struct.unpack_from("<%dI" % n, b, base + 12)
        states = []
        for j, so in enumerate(st_offs):
            sb = base + so
            name = struct.unpack_from("<Q", b, sb)[0]
            typ = struct.unpack_from("<I", b, sb + 8)[0]
            acnt = struct.unpack_from("<I", b, sb + 12)[0]
            aoff = struct.unpack_from("<I", b, sb + 16)[0]
            loop = b[sb + 32]
            additive = b[sb + 36]
            evcnt, evoff = struct.unpack_from("<II", b, sb + 40)
            lcnt, loff = struct.unpack_from("<II", b, sb + 48)
            emit = struct.unpack_from("<I", b, sb + 72)[0]
            endt = struct.unpack_from("<f", b, sb + 76)[0]
            anims = [struct.unpack_from("<Q", b, sb + aoff + k * 8)[0] for k in range(min(acnt, 3))] if aoff else []
            links = []
            for k in range(lcnt):
                if not loff:
                    break
                links.append(struct.unpack_from("<IfII", b, sb + loff + k * 16))
            trans = {}
            for k in range(evcnt):
                if not evoff:
                    break
                ev, idx = struct.unpack_from("<Ii", b, sb + evoff + k * 8)
                trans[ev] = idx
            states.append({"idx": j, "at": sb, "name": name, "type": typ, "loop": loop,
                           "additive": additive, "anims": anims, "anim_count": acnt,
                           "events": evcnt, "links": lcnt, "emit": emit, "end_t": endt,
                           "link_list": links, "trans": trans})
        out.append({"idx": i, "at": base, "magic": magic, "default": default, "states": states,
                    "default_at": base + 4})
    return out


def event_table(b: bytes, h: dict) -> list[int]:
    if not h["event_hash_count"] or not h["event_hash_off"]:
        return []
    return [struct.unpack_from("<I", b, h["event_hash_off"] + i * 4)[0]
            for i in range(h["event_hash_count"])]


def load_names(path: str | None) -> dict[int, str]:
    """hashlist-normalized.csv: hash_dec,0xHEX,64,name,..."""
    if not path:
        return {}
    out: dict[int, str] = {}
    with open(path, encoding="utf-8", errors="replace") as f:
        for row in csv.reader(f):
            if len(row) >= 4 and row[1].startswith("0x"):
                try:
                    out[int(row[1], 16)] = row[3]
                except ValueError:
                    continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="读/改 state_machine 资源的 layer.DefaultState")
    ap.add_argument("file")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--decode", action="store_true", help="打印事件→过渡→状态 与 部署完成态")
    ap.add_argument("--names", default=None, help="hashlist-normalized.csv，用于反查事件/状态名")
    ap.add_argument("--layer", type=int, default=None)
    ap.add_argument("--set", action="append", default=[], help="层=默认态索引，可重复")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    b = pathlib.Path(a.file).read_bytes()
    h = header(b)
    ls = layers(b, h)
    names = load_names(a.names)

    def nm(x: int) -> str:
        return ("=" + names[x]) if x in names else ""

    if a.show or a.decode or not a.set:
        print(f"{a.file}  {len(b):,} B")
        print("header: " + "  ".join(f"{k}={v}" for k, v in h.items()))
        if a.decode:
            ev = event_table(b, h)
            print("event 表: " + ", ".join(f"0x{e:08X}{nm(e)}" for e in ev))
        print(f"layers: {len(ls)}")
        for L in ls:
            if a.layer is not None and L["idx"] != a.layer:
                continue
            print(f"  layer{L['idx']} @0x{L['at']:X} magic=0x{L['magic']:X} "
                  f"default={L['default']}(@0x{L['default_at']:X}) states={len(L['states'])}")
            for s in L["states"]:
                tag = "  <-- DEFAULT" if s["idx"] == L["default"] else ""
                print(f"    state{s['idx']} type={STATE_TYPES.get(s['type'], s['type'])} "
                      f"loop={s['loop']} add={s['additive']} anims={s['anim_count']} "
                      f"{[hex(x) for x in s['anims']]} events={s['events']} links={s['links']} "
                      f"emit=0x{s['emit']:X}{nm(s['emit'])} endT={s['end_t']:.2f} "
                      f"name=0x{s['name']:016X}{nm(s['name'])}{tag}")
                if not a.decode:
                    continue
                if s["emit"]:
                    tgt = s["trans"].get(s["emit"])
                    if tgt is not None and 0 <= tgt < len(s["link_list"]):
                        ix, bl, ty, _beat = s["link_list"][tgt]
                        print(f"        * EmitEndEvent -> state {ix} "
                              f"({LINK_TYPES.get(ty, ty)}, blend {bl:.2f})  <== 部署完成态")
                for ev, tgt in s["trans"].items():
                    if not (0 <= tgt < len(s["link_list"])):
                        continue
                    ix, bl, ty, _beat = s["link_list"][tgt]
                    print(f"        on 0x{ev:08X}{nm(ev):<18s} -> state {ix} "
                          f"({LINK_TYPES.get(ty, ty)}, blend {bl:.2f})")

    if not a.set:
        return 0

    data = bytearray(b)
    for spec in a.set:
        if "=" not in spec:
            raise SystemExit(f"✗ --set 需要 层=索引，收到 {spec!r}")
        li, vi = (int(x, 0) for x in spec.split("=", 1))
        L = next((x for x in ls if x["idx"] == li), None)
        if L is None:
            raise SystemExit(f"✗ 没有 layer{li}（共 {len(ls)} 层）")
        if not 0 <= vi < len(L["states"]):
            raise SystemExit(f"✗ layer{li} 只有 {len(L['states'])} 个状态，索引 {vi} 越界")
        old = struct.unpack_from("<I", data, L["default_at"])[0]
        struct.pack_into("<I", data, L["default_at"], vi)
        print(f"  layer{li}.DefaultState @0x{L['default_at']:X}: {old} -> {vi}")
    if not a.out:
        raise SystemExit("✗ 要写文件请给 --out")
    pathlib.Path(a.out).write_bytes(bytes(data))
    print(f"✓ 已写 {a.out}（{len(data):,} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
