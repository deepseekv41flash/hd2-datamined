#!/usr/bin/env python3
"""turret_shell_survey.py -- 普查「哪些炮塔壳像 AC-8 一样自带姿态、挂上去不用调位置」。

判据（来自 2026-10-26 的 AC-8 vs 火箭实测）
    AC-8 挂上就能用：它的 **展开态 clip 是全身姿态**（14/16 骨骼有键，含 `elevator`），
    所以把 `layer0.DefaultState` 设成展开态 = 整机一次摆到位。
    火箭挂了就沉：它的展开态 clip 是**空壳**（0 骨骼有键），升降骨骼停在 bind。
    ⇒ **判据 = 展开态 clip 的有键骨骼数 / 骨架骨骼数**。

它做的事
    ① 从 `refs/entity-components.json` 取「五件套」实体（Turret + Wieldable + WeaponWielder
       + ProjectileWeapon + Unit）——这些才是能被装到载具上的件
    ② 每个实体读 `Unit +0` == 壳 id（多数实体壳就是自己，AC-8 例外：壳是 `aa_turret`）
    ③ 壳 id 在 `state_machine` 全库清单（`--sm-index`）里找同 id 的 SM → 取其所在包
    ④ `srkit extract` 出 SM / bones / 展开态 clip，判定：
         A 全身姿态（keyed ≥ 60%）→ **自带姿态，不用调位置**
         B 半身（0 < keyed < 60%）→ 可能要调
         C 空 clip（0 键）→ 要调位置（用 `unit_offset.py` +dz）
         D 没有 state_machine → 静态站（多半也不用调，但挂点未验）

用法
    python tools/turret_shell_survey.py survey                       # 打表
    python tools/turret_shell_survey.py survey --json out.json       # 机器可读
    python tools/turret_shell_survey.py survey --limit 10 --verbose  # 先跑一小批看流程

依赖：`srkit`（`python -m srkit`）、同目录 `entity_field_set.row_of` / `typelib` /
      `animation_probe` / `state_machine_edit`；参考清单 `refs/entity-components.json`。
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

from entity_field_set import row_of                          # noqa: E402
from typelib import TypeLib                                   # noqa: E402
import animation_probe as AP                                  # noqa: E402
import state_machine_edit as SME                              # noqa: E402

UNIT_BLOCK = 0x4437574D
TYPE_BONES, TYPE_SM, TYPE_ANIM = 0x18DEAD01056B72E9, 0xA486D4045106165C, 0x931E336D7646CC26
ST_DEPLOYED = 0x823905BD6B62BA3E      # 「展开态」状态名（模板 A）
ST_FOLDED = 0x330CA356421F7ADA
ST_DEPLOY = 0x79DE1870039A1A7E        # 「部署过渡」状态名

import re                                                    # noqa: E402
LIFT_RE = re.compile(r"elevator|elevation|slider|lift", re.I)

# 能被装到载具上的判据：Turret + Wieldable + WeaponWielder + Unit + **任一武器组件**
#   投射武器 = ProjectileWeapon；火焰 = SprayWeapon；激光 = BeamWeapon ⇒ 只认 ProjectileWeapon 会漏人
FIVE = ["TurretComponentData", "WieldableComponentData", "WeaponWielderComponentData",
        "UnitComponentData", "WeaponDataComponentData"]

DEFAULT_PLAIN = r"D:\mod\refs\dlbin\plaintext-26088801\generated_entities.dl_bin"
DEFAULT_TYPELIB = r"D:\mod\refs\dlbin\plaintext-26088801\dl_library.dl_typelib"
DEFAULT_SMINDEX = r"D:\mod\out\sm-all.json"
DEFAULT_GAME = r"D:\SteamLibrary\steamapps\common\Helldivers 2\data"


def find_sdk() -> str:
    for root in (os.environ.get("HD2SDK", ""), r"C:\Users\Admin\HD2SDK-CommunityEdition"):
        if root and os.path.isfile(os.path.join(root, "srkit", "__init__.py")):
            return root
    raise SystemExit("✗ 找不到 HD2SDK 检出")


def srkit_extract(sdk: str, game: str, package: str, type_id: int, file_id: int, outdir: str,
                  decoded: bool = False) -> str | None:
    """抽出 (type,id) 的 toc；**每个提取用自己的子目录**，避免同 id 不同类型撞名。"""
    sub = os.path.join(outdir, f"{type_id:016x}_{file_id:016x}")
    os.makedirs(sub, exist_ok=True)
    argv = [sys.executable, "-m", "srkit", "extract", "--id", f"{file_id:#018x}",
            "--type", f"{type_id:#018x}", "--package", package, "-o", sub]
    if decoded:
        argv.append("--decoded")
    p = subprocess.run(argv + [game],
                       cwd=sdk, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return None
    tocs = [os.path.join(sub, n) for n in os.listdir(sub) if n.lower().endswith(".toc.bin")]
    return tocs[0] if len(tocs) == 1 else None


def load_names(path: str) -> dict[str, str]:
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:                                            # noqa: BLE001
        return {}
    return {r["key"]: f"{r.get('code') or ''} {r.get('name') or ''}".strip()
            for r in d.get("entity_index", [])}


def deployed_clip(sm_path: str) -> tuple[int | None, str]:
    """返回 (展开态 clip id, 说明)。规则见 SENTRY-TURRET-FIELDS §3.8.4.1。"""
    b = open(sm_path, "rb").read()
    h = SME.header(b)
    ls = SME.layers(b, h)
    if not ls:
        return None, "no-layer"
    L0 = ls[0]
    by_name = {s["name"]: s for s in L0["states"]}
    if ST_DEPLOYED in by_name and by_name[ST_DEPLOYED]["anims"]:
        return by_name[ST_DEPLOYED]["anims"][0], "state-823905BD"
    if 0xE954AED4871D630A in by_name:            # 模板 B 的 idle 态
        return None, "template-B"
    if ST_DEPLOY in by_name:
        dep = by_name[ST_DEPLOY]
        tgt = dep["trans"].get(dep["emit"]) if dep["emit"] else None
        if tgt is not None and 0 <= tgt < len(dep["link_list"]):
            ix = dep["link_list"][tgt][0]
            if 0 <= ix < len(L0["states"]) and L0["states"][ix]["anims"]:
                return L0["states"][ix]["anims"][0], "emit-target"
    return None, "no-deploy-state"


def main() -> int:
    ap = argparse.ArgumentParser(description="普查炮塔壳的展开态姿态完整度")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("survey")
    p.add_argument("--plain", default=DEFAULT_PLAIN)
    p.add_argument("--typelib", default=DEFAULT_TYPELIB)
    p.add_argument("--components", default=str(HERE.parent / "refs" / "entity-components.json"))
    p.add_argument("--sm-index", default=DEFAULT_SMINDEX)
    p.add_argument("--names", default=str(HERE.parent / "refs" / "entity-locid-names.json"))
    p.add_argument("--game", default=DEFAULT_GAME)
    p.add_argument("--sdk", default=None)
    p.add_argument("--out", default=r"D:\mod\out\shell-survey")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--json", default=None)
    p.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    sdk = a.sdk or find_sdk()
    data = open(a.plain, "rb").read()
    lib = TypeLib(open(a.typelib, "rb").read())
    comps = json.load(open(a.components, encoding="utf-8"))["components"]
    sm_index = json.load(open(a.sm_index, encoding="utf-8"))
    names = load_names(a.names)
    devent = {r["key"]: r.get("dev_name") for r in json.load(
        open(a.names, encoding="utf-8")).get("entity_index", [])}

    sms: dict[str, list[str]] = {}
    for e in sm_index:
        if e["type"] == "state_machine":
            sms.setdefault(e["file_id_hex"].lower(), []).append(e["package"])

    # ---- ① 五件套实体
    cands = []
    for key, clist in comps.items():
        s = set(clist)
        if all(n in s for n in FIVE):
            cands.append(key)
    cands.sort()
    print(f"五件套实体 {len(cands)} 个")

    # ---- ② 壳 id（按壳去重）
    shells: dict[int, list[str]] = {}
    for key in cands:
        try:
            off, _stride, _row = row_of(data, lib, UNIT_BLOCK, int(key, 16))
        except SystemExit:
            continue
        lo, hi = struct.unpack_from("<II", data, off)
        shell = (hi << 32) | lo
        if shell == 0:                       # 没有 Unit 组件的实体（Unit+0=0）
            continue
        shells.setdefault(shell, []).append(key)
    print(f"去重后壳 {len(shells)} 个")
    if a.limit:
        shells = dict(list(shells.items())[: a.limit])

    rows = []
    for i, (shell, ents) in enumerate(sorted(shells.items()), 1):
        sid = f"{shell:016x}"
        pkgs = sms.get("0x" + sid)
        rec = dict(shell=f"0x{shell:016X}", entities=ents,
                   names=[names.get(e, "") for e in ents],
                   sm_package=pkgs[0] if pkgs else None, kind=None,
                   deployed_clip=None, bone_count=None, keyed=None, rule=None,
                   dev=next((devent.get(e) for e in ents if devent.get(e)), None))
        if not pkgs:
            rec.update(kind="D 无状态机（静态站）", rule="no-sm")
            rows.append(rec)
            print(f"[{i}/{len(shells)}] {sid}  无 SM")
            continue
        outdir = os.path.join(os.path.abspath(a.out), sid)
        sm_p = srkit_extract(sdk, a.game, pkgs[0], TYPE_SM, shell, outdir)
        if not sm_p:
            rec.update(kind="? SM 取不到")
            rows.append(rec)
            continue
        try:
            clip, rule = deployed_clip(sm_p)
        except Exception as e:                                    # noqa: BLE001
            clip, rule = None, f"parse-error({type(e).__name__})"
        rec.update(rule=rule)
        if clip is None:
            kind = "E 模板B（族不同，未验）" if rule == "template-B" else "D 无部署族（静态/其它）"
            rec.update(kind=kind)
            rows.append(rec)
            print(f"[{i}/{len(shells)}] {sid}  {rule} -> {kind}")
            continue
        rec["deployed_clip"] = f"0x{clip:016X}"
        # 骨架骨骼数
        b_p = srkit_extract(sdk, a.game, pkgs[0], TYPE_BONES, shell, outdir, decoded=True)
        bone_count = None
        bone_names: list[str] = []
        if b_p:
            bj = json.load(open(b_p.replace(".toc.bin", ".json"), encoding="utf-8")) \
                if os.path.isfile(b_p.replace(".toc.bin", ".json")) else None
            if bj:
                bone_count = bj.get("bone_count")
                bone_names = [x.get("name") or "" for x in sorted(bj.get("bones", []), key=lambda x: x["index"])]
        # 展开态 clip 的有键骨骼
        c_p = srkit_extract(sdk, a.game, pkgs[0], TYPE_ANIM, clip, outdir)
        keyed = None
        if c_p:
            try:
                pr = AP.probe(c_p, bone_names)
                keyed = len(pr["tracks"])
            except Exception as e:                                # noqa: BLE001
                if a.verbose:
                    print("   clip 解析失败:", e)
        rec.update(bone_count=bone_count, keyed=keyed)
        if keyed is None or not bone_count:
            rec.update(kind="? 读不到 clip/骨架")
        else:
            ratio = keyed / bone_count
            lift = [n for n in bone_names if LIFT_RE.search(n or "")]
            lift_keyed = None
            if c_p:
                pr = AP.probe(c_p, bone_names)
                idxs = set(pr["tracks"])
                lift_idx = [i for i, n in enumerate(bone_names) if LIFT_RE.search(n or "")]
                lift_keyed = bool(lift_idx) and all(i in idxs for i in lift_idx)
            rec.update(ratio=round(ratio, 3), has_lift=bool(lift), lift_keyed=lift_keyed,
                       lift_bones=lift[:6])
            if ratio >= 0.6 and (not lift or lift_keyed):
                rec.update(kind="A 全身姿态（自带，不用调）")
            elif keyed == 0 and not lift:
                rec.update(kind="C0 空 clip 但无升降机构（bind 或许就行，未验）")
            elif keyed == 0:
                rec.update(kind="C 空 clip（要调位置）")
            else:
                rec.update(kind="B 半身/升降没被打到（要调）")
        rows.append(rec)
        print(f"[{i}/{len(shells)}] {sid}  {rec['kind']}  keyed={keyed}/{bone_count}  clip={rec['deployed_clip']}")

    # ---- 打表
    print()
    print(f"{'类':<22} {'壳 id':<20} {'clip':<20} {'有键/骨架':>9}  名称")
    for r in sorted(rows, key=lambda x: (x["kind"] or "", x["shell"])):
        kk = f"{r.get('keyed')}/{r.get('bone_count')}" if r.get("keyed") is not None else "-"
        nm = "; ".join([x for x in r["names"] if x])[:40]
        print(f"{(r['kind'] or '?'):<22} {r['shell']:<20} {(r['deployed_clip'] or '-'):<20} {kk:>9}  {nm}")
    if a.json:
        json.dump(rows, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n→ {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
