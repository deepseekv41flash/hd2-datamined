#!/usr/bin/env python3
"""pod_loadout.py -- 投送舱换载荷 + **有限数量的跨包加载**的通用产出。

给「哪条 rack + 一件武器（+ 可选一件背包）」，自动算出要改哪些字节、跑门禁、出可安装文件。

为什么需要它
    换进去的物品若不在任何已加载的包里，引擎会画**紫色问号占位**。
    memmod 时代靠 HD2Runtime 调 `RefcountedPackageSystem::request` 现场请包；
    现在没有 runtime / ffi ⇒ 只能改数据，让引擎自己去加载。
    引擎加载的来源（本仓库 2026-10-23 实测）：

        战备行 +0xA8（物品的 toc 包）
          + 战备行 +0xF8（授予武器的 LoadoutEntry id → 该武器的包）
          + 原版物品自己的包

    ⇒ 两个声明口。所以：同包两件用 +0xA8；不同包用 +0xA8 + +0xF8。

解析链（全部现算，偏移不写死）
    rack 行        HellpodRackComponentData 0xA98BB156 → typelib 成员给哈希图/行数组
    物品实体键      rack 槽 +0 的 u64
    物品 → toc 包   LoadoutPackageComponentData 0x7A858691，行 +8 u64
    物品 → LOE id   LoadoutEntryComponentData 0x4F2CF417，哈希图键→行，行 +0 u32
    战备行          用「+0xF8 == 原版槽1武器的 LOE id」反查（唯一命中才用），或 --strat-row-base 指定

用法
    python tools/pod_loadout.py show  --rack 29
    python tools/pod_loadout.py plan  --rack 29 --weapon "LAS-44 Nova" --backpack "LIFT-182 Warp Pack"
    python tools/pod_loadout.py build --rack 29 --weapon "LAS-44 Nova" --backpack "LIFT-182 Warp Pack" \\
                                      --out-dir D:/mod/work/podload [--seal --pk <recipient.pk>]

只读 vs 写：`show` / `plan` 只读；`build` 只写 `--out-dir`，**不碰游戏目录**（部署交给 dlbin_deploy.py）。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import pickle
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from typelib import TypeLib                       # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                          # noqa: BLE001
        pass

PLAIN_DIR = pathlib.Path(r"D:\mod\refs\dlbin\plaintext-26251122")
ENT_PLAIN = PLAIN_DIR / "generated_entities.dl_bin"
STRAT_PLAIN = PLAIN_DIR / "generated_stratagem_settings.dl_bin"
TYPELIB = PLAIN_DIR / "dl_library.dl_typelib"
ENTITY_NAMES = pathlib.Path(r"D:\mod\work\repo-datamined\refs\entity-locid-names.json")
RESOURCE_INDEX = pathlib.Path(r"D:\mod\cache\resource_index.pkl")

# toc 条目里常见的资源类型 id（这 8 个是引擎类型名的 64 位哈希，跨 build 稳定；
# 只用于「包内容核验」这一行提示，不影响任何写入。装了 srkit 时其余类型交给它翻译。）
TOC_TYPE_NAMES = {
    0xCD4238C6A0C69E32: "texture",
    0xEAC0B497876ADEDF: "material",
    0xE0A48D0BE9A7453F: "mesh",
    0xA8193123526FAD64: "particles",
    0x931E336D7646CC26: "animation",
    0x5F7203C8F280DAB8: "physics",
    0xAB2F78E885F513C6: "prefab",
    0x504B55235D21440E: "wwise_stream",
}

RACK_TID = 0xA98BB156          # HellpodRackComponentData
LOEPKG_TID = 0x7A858691        # LoadoutPackageComponentData
LOE_TID = 0x4F2CF417           # LoadoutEntryComponentData
STRAT_ROW = 400                # StratagemSettings 行大小
OFF_A8 = 0xA8                  # 物品 toc 包
OFF_F8 = 0xF8                  # 授予武器的 LoadoutEntry id（低 32 位有效）


# ------------------------------------------------------------------ 容器
def blocks(data: bytes):
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
        out.append({"head": head, "tid": tid, "payload": payload, "body": head + 28})
        pos = head + 28 + payload
    return out


def strat_groups(data: bytes):
    """设置表：u32 组数 + 连续 24 B 块头。"""
    n = struct.unpack_from("<I", data, 0)[0]
    off, out = 4, []
    for _ in range(n):
        ver, tid, payload, wide = struct.unpack_from("<IIII", data, off + 4)
        out.append({"head": off, "tid": tid, "payload": payload, "body": off + 24})
        off += 24 + payload
    return out


class Data:
    def __init__(self):
        self.lib = TypeLib(open(TYPELIB, "rb").read())
        self.ent = open(ENT_PLAIN, "rb").read()
        self.strat = open(STRAT_PLAIN, "rb").read()
        self._bl = {b["tid"]: b for b in blocks(self.ent)}
        self._names = None
        self._res = None

    # ---- 实体名字
    def names(self):
        if self._names is None:
            ei = json.loads(ENTITY_NAMES.read_text(encoding="utf-8"))["entity_index"]
            self._names = {int(e["key"], 16): e for e in ei}
        return self._names

    def resolve_item(self, spec: str) -> int:
        spec = spec.strip()
        if spec.lower().startswith("0x"):
            return int(spec, 16)
        names = self.names()

        def labels(e):
            """一个条目可以有三种叫法：显示名 / 代号 / 「代号 显示名」。"""
            nm, code = e["name"] or "", e["code"] or ""
            out = {nm.lower()}
            if code:
                out |= {code.lower(), f"{code} {nm}".lower().strip()}
            return out

        low = spec.lower()
        # 背包条目常常没有 code，而用户习惯连代号一起写（"GL-28 Belt-Fed ... Backpack"）
        # ⇒ 若首段像代号（字母/斜杠 + 数字），再拿去掉首段后的剩余部分试一次。
        alts = [low]
        head, _, rest = low.partition(" ")
        if rest and any(ch.isdigit() for ch in head) and len(head) <= 8:
            alts.append(rest)
        exact = [k for k, e in names.items() if any(a in labels(e) for a in alts)]
        if len(exact) == 1:
            return exact[0]
        part = [k for k, e in names.items() if any(low in lab for lab in labels(e))]
        if len(part) == 1:
            return part[0]
        cand = exact or part
        if not cand:
            raise SystemExit(f"✗ 找不到物品 {spec!r}（entity_index 无匹配）")
        listing = "\n".join(
            f"    0x{k:016X}  {names[k]['name']:<28s} {names[k]['kind']:<14s} code={names[k]['code']!r}"
            for k in cand[:12])
        raise SystemExit(f"✗ 物品 {spec!r} 命中 {len(cand)} 个，请用实体键精确指定：\n{listing}")

    # ---- 物品 → toc 包
    def t(self, tid):
        b = self._bl.get(tid)
        if not b:
            raise SystemExit(f"✗ 实体库里没有块 0x{tid:08X}")
        ms = self.lib.members(tid)
        slots = ms[0]["size64"]
        stride = self.lib.desc(ms[1]["type_id"])[3]
        rows = ms[1]["size64"] // stride
        return b, slots, stride, rows, b["body"] + slots

    def hashmap(self, tid):
        b, slots, stride, rows, base = self.t(tid)
        m = {}
        for i in range(slots // 16):
            k, v = struct.unpack_from("<QI", self.ent, b["body"] + 16 * i)
            if k:
                m[k] = v
        return m, stride, rows, base

    def item_package(self, key: int):
        m, stride, rows, base = self.hashmap(LOEPKG_TID)
        r = m.get(key)
        if r is None or r >= rows:
            return None
        return struct.unpack_from("<Q", self.ent, base + r * stride + 8)[0]

    def item_loadout_id(self, key: int):
        m, stride, rows, base = self.hashmap(LOE_TID)
        r = m.get(key)
        if r is None or r >= rows:
            return None
        return struct.unpack_from("<I", self.ent, base + r * stride)[0]

    def package_census(self, pkg: int):
        if not RESOURCE_INDEX.exists():
            return None
        if self._res is None:
            self._res = pickle.load(open(RESOURCE_INDEX, "rb"))
        pidx = {p: i for i, p in enumerate(self._res["packages"])}
        i = pidx.get("%016x" % pkg)
        if i is None:
            return None
        cnt = {}
        for _fid, lst in self._res["entries"].items():
            for pi, t in lst:
                if pi == i:
                    cnt[t] = cnt.get(t, 0) + 1

        def name_of(h):
            if h in TOC_TYPE_NAMES:
                return TOC_TYPE_NAMES[h]
            try:                                            # 装了 srkit 就查它要全名
                from srkit.util.ids import type_name         # noqa: PLC0415
                return type_name(h)
            except Exception:                                # noqa: BLE001
                return "0x%016X" % h

        return {name_of(k): v for k, v in cnt.items()}

    # ---- rack
    def rack(self, row: int):
        b, slots, stride, rows, base = self.t(RACK_TID)
        if not 0 <= row < rows:
            raise SystemExit(f"✗ rack {row} 越界（本 build {rows} 条）")
        rms = self.lib.members(self.lib.members(RACK_TID)[1]["type_id"])
        slot_arr, attach = rms[0]["offset64"], rms[0]["type_id"]
        sstride = self.lib.desc(attach)[3]
        nslots = rms[0]["size64"] // sstride
        item_off = self.lib.members(attach)[0]["offset64"]
        o = base + row * stride
        items = [struct.unpack_from("<Q", self.ent, o + slot_arr + i * sstride + item_off)[0]
                 for i in range(nslots)]
        spawn = struct.unpack_from("<I", self.ent, o + 556)[0]
        rnd = struct.unpack_from("<I", self.ent, o + 552)[0]
        m, _, _, _ = self.hashmap(RACK_TID)
        key = next((k for k, v in m.items() if v == row), 0)
        return {"row": row, "key": key, "items": items, "spawn": spawn, "random": rnd,
                "slot_abs": o, "slot_off": slot_arr, "slot_stride": sstride, "item_off": item_off}

    # ---- 战备行
    def find_strat_row(self, rack_info):
        """用「+0xF8 == 原版槽1武器的 LOE id」反查战备行；再退回「+0xA8 == 槽1物品的包」。"""
        weapon = rack_info["items"][0] if rack_info["items"] else 0
        want_f8 = self.item_loadout_id(weapon) if weapon else None
        want_a8 = self.item_package(weapon) if weapon else None
        hits_f8, hits_a8 = [], []
        for (tid, body, count) in self._strat_tables():
            for i in range(count):
                o = body + i * STRAT_ROW
                if want_f8 and (struct.unpack_from("<Q", self.strat, o + OFF_F8)[0] & 0xFFFFFFFF) == want_f8:
                    hits_f8.append(o)
                if want_a8 and struct.unpack_from("<Q", self.strat, o + OFF_A8)[0] == want_a8:
                    hits_a8.append(o)
        if len(hits_f8) == 1:
            return hits_f8[0], f"+0xF8 == LOE id 0x{want_f8:08X}（唯一）"
        if len(hits_a8) == 1:
            return hits_a8[0], f"+0xA8 == 包 0x{want_a8:016X}（唯一）"
        return None, (f"反查失败：+0xF8 命中 {len(hits_f8)} 行、+0xA8 命中 {len(hits_a8)} 行"
                      f"（共用 rack 或已被改过），请用 --strat-row-base 指定")

    def _strat_tables(self):
        out = []
        for g in strat_groups(self.strat):
            ms = self.lib.members(g["tid"])
            if not (len(ms) == 1 and ms[0]["size64"] == 16):
                continue
            if self.lib.desc(ms[0]["type_id"])[3] != STRAT_ROW:
                continue
            count = struct.unpack_from("<Q", self.strat, g["body"] + 8)[0]
            out.append((g["tid"], g["body"] + 16, count))
        return out


# ------------------------------------------------------------------ 报告
def describe(d: Data, key: int) -> str:
    e = d.names().get(key)
    pkg = d.item_package(key)
    loe = d.item_loadout_id(key)
    nm = f"{e['name']} [{e['kind']}]" if e else "?"
    return (f"0x{key:016X}  {nm:<34s} 包={'0x%016X' % pkg if pkg else '(无)'}"
            f"  LOE={'0x%08X' % loe if loe else '(无)'}")


def cmd_show(a) -> int:
    d = Data()
    r = d.rack(a.rack)
    print(f"rack {r['row']}  key=0x{r['key']:016X}  spawn={r['spawn']}  random={r['random']}")
    print(f"  每槽 {r['slot_stride']} B，Item @ +{r['item_off']}")
    for i in range(r["spawn"]):
        print(f"  会生成的槽 {i + 1}: {describe(d, r['items'][i])}")
    for i in range(r["spawn"], len(r["items"])):
        if r["items"][i]:
            print(f"  authored 但不生成 槽 {i + 1}: {describe(d, r['items'][i])}")
    base, how = d.find_strat_row(r)
    print(f"  战备行: {'0x%X' % base if base else '(未定位)'}  ← {how}")
    if base:
        a8 = struct.unpack_from("<Q", d.strat, base + OFF_A8)[0]
        f8 = struct.unpack_from("<Q", d.strat, base + OFF_F8)[0] & 0xFFFFFFFF
        print(f"    当前 +0xA8=0x{a8:016X}  +0xF8=0x{f8:08X}")
    return 0


def make_plan(d: Data, rack_row: int, weapon_key: int, pack_key, strat_base):
    r = d.rack(rack_row)
    weapon = d.item_package(weapon_key)
    pack = d.item_package(pack_key) if pack_key else None
    loe_w = d.item_loadout_id(weapon_key)
    if weapon is None:
        raise SystemExit(f"✗ 武器 0x{weapon_key:016X} 没有 LoadoutPackage 行 ⇒ 无法确定要加载哪个包")
    if pack_key and pack is None:
        raise SystemExit(f"✗ 背包 0x{pack_key:016X} 没有 LoadoutPackage 行")

    sets = []            # [(绝对偏移, 新值, 说明)]
    if pack_key is None or pack == weapon:
        sets.append((strat_base + OFF_A8, weapon, "单包：+0xA8 = 武器包（背包留原版或同包）"))
        mode = "single-package"
    else:
        if loe_w is None:
            raise SystemExit(f"✗ 武器 0x{weapon_key:016X} 没有 LoadoutEntry 行 ⇒ 不能用 +0xF8 声明第二个包")
        sets.append((strat_base + OFF_A8, pack, "双包：+0xA8 = 背包的包"))
        sets.append((strat_base + OFF_F8, loe_w, "双包：+0xF8 = 武器的 LoadoutEntry id"))
        mode = "two-package"

    return {"mode": mode, "sets": sets, "weapon": weapon_key, "pack": pack_key,
            "weapon_pkg": weapon, "pack_pkg": pack, "loe_weapon": loe_w,
            "vanilla": (r["items"][0], r["items"][1] if len(r["items"]) > 1 else 0)}


def print_plan(d: Data, plan, strat_base):
    print(f"模式：{plan['mode']}")
    print(f"  武器 {describe(d, plan['weapon'])}")
    if plan["pack"]:
        print(f"  背包 {describe(d, plan['pack'])}")
    for off, val, why in plan["sets"]:
        width = 8
        old = struct.unpack_from("<Q", d.strat, off)[0]
        print(f"  {why}")
        print(f"    0x{off:X} ({width} B): 0x{old:016X} -> 0x{val:016X}")
    print("  资源核验（包内类型分布）：")
    for label, pkg in (("武器包", plan["weapon_pkg"]), ("背包包", plan["pack_pkg"])):
        if not pkg:
            continue
        c = d.package_census(pkg)
        if c is None:
            print(f"    {label} 0x{pkg:016X}: (无 resource_index，跳过)")
            continue
        need = {k: c.get(k, 0) for k in ("mesh", "material", "texture")}
        flag = "✓" if need["mesh"] and need["material"] else "⚠ 缺 mesh/material"
        print(f"    {label} 0x{pkg:016X}: mesh={need['mesh']} material={need['material']} "
              f"texture={need['texture']}  {flag}")


def _locate(a, d):
    r = d.rack(a.rack)
    if a.strat_row_base:
        base = int(str(a.strat_row_base), 0)
        return r, base, "命令行指定"
    base, how = d.find_strat_row(r)
    if not base:
        raise SystemExit(f"✗ {how}")
    return r, base, how


def cmd_plan(a) -> int:
    d = Data()
    r, base, how = _locate(a, d)
    print(f"rack {a.rack}  (spawn={r['spawn']})   战备行 0x{base:X}  ← {how}")
    weapon = d.resolve_item(a.weapon)
    pack = d.resolve_item(a.backpack) if a.backpack else None
    plan = make_plan(d, a.rack, weapon, pack, base)
    print_plan(d, plan, base)
    return 0


def cmd_build(a) -> int:
    d = Data()
    r, base, how = _locate(a, d)
    weapon = d.resolve_item(a.weapon)
    pack = d.resolve_item(a.backpack) if a.backpack else None
    plan = make_plan(d, a.rack, weapon, pack, base)
    out = pathlib.Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"rack {a.rack}   战备行 0x{base:X}  模式 {plan['mode']}")
    print_plan(d, plan, base)
    print()

    # ① rack 槽位
    old_w, old_b = plan["vanilla"]
    cmd = [sys.executable, str(HERE / "pod_rack_swap.py"), "edit",
           "--rack", str(a.rack),
           "--slot0", f"0x{weapon:016X}",
           "--expect-old", f"0x{old_w:016X},0x{old_b:016X}",
           "--out", str(out / "entities.plain")]
    if pack:
        cmd[cmd.index("--out"):cmd.index("--out")] = ["--slot1", f"0x{pack:016X}"]
    sys.stdout.flush()
    print("① rack 槽位：", " ".join(cmd[2:]))
    sys.stdout.flush()
    rc = subprocess.run(cmd).returncode
    if rc:
        raise SystemExit("✗ rack 改写门禁未过")

    # ② 战备声明
    sets = [f"{hex(off)}=u64:0x{val:016X}" for off, val, _ in plan["sets"]]
    cmd2 = [sys.executable, str(HERE / "plain_edit.py"),
            "--plain", str(STRAT_PLAIN), "--out", str(out / "stratagem.plain")]
    for s in sets:
        cmd2 += ["--set", s]
    print("\n② 战备声明：", " ".join(cmd2[2:]))
    rc = subprocess.run(cmd2).returncode
    if rc:
        raise SystemExit("✗ 战备改写门禁未过")

    # ③ 可选封装
    if a.seal:
        pk = pathlib.Path(a.pk)
        for src, dst in (("entities.plain", "generated_entities.dl_bin"),
                         ("stratagem.plain", "generated_stratagem_settings.dl_bin")):
            cmd3 = [sys.executable, str(HERE / "dlbin_seal.py"), "seal-key",
                    str(out / src), "--key", str(pk), "--out", str(out / dst)]
            print(f"\n③ 封装 {dst}")
            if subprocess.run(cmd3).returncode:
                raise SystemExit(f"✗ 封装 {dst} 失败")

    print(f"\n✓ 产物在 {out}")
    print("部署（确认游戏已关闭）：")
    print(f"  python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed {out / 'generated_entities.dl_bin'}")
    print(f"  python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin --sealed {out / 'generated_stratagem_settings.dl_bin'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="投送舱换载荷 + 有限数量的跨包加载（通用产出）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("show", "plan", "build"):
        p = sub.add_parser(name)
        p.add_argument("--rack", type=int, required=True, help="rack 行号（如 29 = StA-X3）")
        p.add_argument("--strat-row-base", default=None, help="战备行基址（反查失败时手工指定）")
        if name != "show":
            p.add_argument("--weapon", required=True, help="武器：名字或 0x 实体键")
            p.add_argument("--backpack", default=None, help="背包：名字或 0x 实体键（可选）")
        if name == "build":
            p.add_argument("--out-dir", required=True)
            p.add_argument("--seal", action="store_true")
            p.add_argument("--pk", default=r"D:\mod\refs\dlbin\keys\recipient.pk")
    a = ap.parse_args()
    return {"show": cmd_show, "plan": cmd_plan, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
