#!/usr/bin/env python3
"""resdep.py -- 资源依赖自动追踪：从"改动目标"找到它真正依赖的粒子/实体/声音资源，并给出驻留计划。

为什么要它（社区同行的坑，2026-10-27）
    * 「资源驻留原来只按**射弹所属装备**猜测来源包，会漏掉实际**粒子**依赖」 —— 猜包必漏；
    * 「缺失粒子阻止安装，未定位音效明确提示，**不把写入成功等同于游戏音效已验证**」——三级结论不能混；
    * 「按当前射弹、爆炸及破片链引用定位粒子/实体资源，并读取声音库 HIRC 事件目录」；
    * 「反查装备归属使用**原始基准**，避免用户已修改的数据污染归属」。
    这个工具把四件事做成一条命令：**扫引用 → 解析到资源 → 资源落到包 → 出驻留计划 → 缺失即拦**。

做法（不猜字段：能解析到资源才算命中）
    1. `index`：`srkit list --json` 拉全档清单（本 build 实测 322,810 行 / 62,915 个去重 id / 3,427 包 / 约 20 秒），
       建 `资源 id → {类型, 名字, 宿主包列表}` 索引。**这是唯一真相源**：一个 u64 能在索引里命中，它就是这个资源，
       不需要先知道"这个字段是粒子"。
    2. `chain`：从起点走引用链，并对每一行做**全 u64 扫描** —— 漏不掉"藏在第 17 个字段里的粒子"。
       已证字段再单独标注：实体 `Unit+0x00`、`EffectReference`（粒子/生成单位/震屏）、爆炸行 `+0x38` 粒子、`+0x28` 震屏表。
    3. `plan`：用**目标件自己声明的包**（`LoadoutPackageComponentData+0x08`）当基准，把叶子分成
       「同包」/「**跨包**」/「缺失」三类 —— 跨包那批正是社区漏掉的那批；缺失默认拒绝出计划。
    4. `sound-catalog` / `sound`：解 wwise bank（跳过 16 B 包装头 → BKHD/DIDX/DATA/**HIRC**）建事件目录；
       `chain` 会标注哪一列是已登记的 Wwise 事件。**未定位音效只提示，不算验证通过**。

用法
    python tools/resdep.py index [--reuse]
    python tools/resdep.py chain --explosion 213
    python tools/resdep.py chain --weapon "Machine Gun" [--json out.json]
    python tools/resdep.py plan  --weapon "Machine Gun"          # 出 plan.sh（驻留命令）
    python tools/resdep.py sound-catalog --limit 5               # 先小样本验证
    python tools/resdep.py sound --event 0x153E8DE

门禁
    G1 清单行 > 100,000 且去重 id > 40,000        G2 叶子资源全部能解析到包
    G3 缺失资源 → 拒绝出驻留计划（--allow-missing 降级）
    G4 补丁序号连续 + 伴生文件齐全
    G5 声音目录缺省不阻塞；命中才标注"事件已登记"
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

BASE = pathlib.Path(r"D:/mod/refs/dlbin/plaintext-26251122")
INDEX_DEFAULT = pathlib.Path(r"D:/mod/refs/resdep/resdep-index-26088801.json")
SOUND_DEFAULT = INDEX_DEFAULT.with_name("resdep-sound-26088801.json")
BANKS_DEFAULT = pathlib.Path(r"D:/mod/refs/resdep/banks")
GAME_DEFAULT = r"D:/SteamLibrary/steamapps/common/Helldivers 2/data"
HOST_PKG = "f6fb08cc02d24255"          # 常驻基础包（载具线 P1–P4 实测）
BASE_SHARED = {HOST_PKG}
EXPL_BASE, EXPL_STRIDE, EXPL_PAYLOAD = 44, 152, 28   # EXPLOSION-VISUAL §0

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                              # noqa: BLE001
        pass


def _k(v: int) -> str:
    return f"0x{v:016x}"


def find_sdk() -> pathlib.Path:
    for cand in (os.environ.get("HD2SDK"), r"C:/Users/Admin/HD2SDK-CommunityEdition"):
        if cand and (pathlib.Path(cand) / "srkit").is_dir():
            return pathlib.Path(cand)
    raise SystemExit("✗ 找不到 HD2SDK 检出；用 --sdk 指定（含 srkit/ 的目录）")


# ---------------------------------------------------------------- 索引
def cmd_index(a) -> int:
    out = pathlib.Path(a.out)
    if a.reuse and out.is_file():
        d = json.loads(out.read_text(encoding="utf-8"))
        print(f"复用索引 {out}（{d.get('unique')} 条去重 id）")
        return 0
    sdk = find_sdk()
    print("扫描全档资源清单（srkit list --json）…")
    proc = subprocess.run([sys.executable, "-m", "srkit", "list", a.game, "--json"],
                          cwd=str(sdk), capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        print("✗ srkit list 失败:", proc.stderr[-600:])
        return 1
    rows = json.loads(proc.stdout)
    res: dict[str, dict] = {}
    for r in rows:
        key = _k(int(r["file_id_hex"], 16))
        ent = res.setdefault(key, {"type": r["type"], "name": r["name"], "pkgs": []})
        if r["package"] not in ent["pkgs"]:
            ent["pkgs"].append(r["package"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"build": "26088801", "rows": len(rows),
                               "unique": len(res), "resources": res},
                              ensure_ascii=False), encoding="utf-8")
    ok = len(rows) > 100_000 and len(res) > 40_000
    print(f"G1 清单行 {len(rows):,} > 100,000 且去重 id {len(res):,} > 40,000 → "
          f"{'PASS' if ok else 'FAIL'}")
    print(f"写入 {out}")
    return 0 if ok else 1


def load_index(path: str | None) -> dict:
    p = pathlib.Path(path or INDEX_DEFAULT)
    if not p.is_file():
        raise SystemExit(f"✗ 索引不存在：{p}（先跑 resdep.py index）")
    return json.loads(p.read_text(encoding="utf-8"))["resources"]


def resolve(idx: dict, rid: int | None) -> dict | None:
    return idx.get(_k(rid)) if rid else None


# ---------------------------------------------------------------- 声音目录（HIRC）
def parse_bank_ids(blob: bytes) -> dict[int, list[int]]:
    """BNK：16 B 包装头之后是 BKHD/DIDX/DATA/HIRC → {对象类型: [对象 id]}（0x04 = Event）。"""
    off, hirc = 16, None
    while off + 8 <= len(blob):
        magic, size = blob[off:off + 4], struct.unpack_from("<I", blob, off + 4)[0]
        if not all(32 <= c < 127 for c in magic) or off + 8 + size > len(blob):
            break
        if magic == b"HIRC":
            hirc = blob[off + 8:off + 8 + size]
            break
        off += 8 + size
    if hirc is None:
        return {}
    count, out, j = struct.unpack_from("<I", hirc, 0)[0], {}, 4
    for _ in range(count):
        if j + 5 > len(hirc):
            break
        typ, ln = hirc[j], struct.unpack_from("<I", hirc, j + 1)[0]
        if j + 5 + ln > len(hirc):
            break
        out.setdefault(typ, []).append(struct.unpack_from("<I", hirc, j + 5)[0])
        j += 5 + ln
    return out


def cmd_sound_catalog(a) -> int:
    idx = load_index(a.index)
    banks = [k for k, v in idx.items() if v["type"] == "wwise_bank"]
    if a.limit:
        banks = banks[: a.limit]
    sdk, cache = find_sdk(), pathlib.Path(a.banks)
    cache.mkdir(parents=True, exist_ok=True)
    catalog: dict[str, list[str]] = {}
    for n, key in enumerate(banks, 1):
        pkg = idx[key]["pkgs"][0]
        # srkit extract 把资源写进 -o 指定的目录：<dir>/wwise_bank_<ID大写>.toc.bin
        dst = cache / key / f"wwise_bank_{key[2:].upper()}.toc.bin"
        if not dst.is_file():
            subprocess.run([sys.executable, "-m", "srkit", "extract", a.game, "--id", key,
                            "--type", "wwise_bank", "--package", pkg, "-o", str(cache / key)],
                           cwd=str(sdk), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if not dst.is_file():
            print(f"  [{n}/{len(banks)}] {key} 提取失败，跳过")
            continue
        for eid in parse_bank_ids(dst.read_bytes()).get(0x04, []):
            catalog.setdefault(f"0x{eid:08X}", []).append(key)
        if n % 25 == 0 or n == len(banks):
            print(f"  [{n}/{len(banks)}] 已登记事件 {len(catalog)}")
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"build": "26088801", "banks": len(banks),
                               "events": catalog}, ensure_ascii=False), encoding="utf-8")
    print(f"声音目录：{len(catalog)} 个事件 / {len(banks)} 个 bank → {out}")
    print("⚠ 事件 id 存在只说明'库里登记了'，不等于游戏里音效正确")
    return 0


def load_sound_catalog(path: str | None) -> dict:
    p = pathlib.Path(path or SOUND_DEFAULT)
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8")).get("events", {})


def cmd_sound(a) -> int:
    cat = load_sound_catalog(a.sound_index)
    if not cat:
        print("⚠ 声音目录不存在（先跑 sound-catalog）；无法判定事件是否登记")
        return 1
    ev = f"0x{int(a.event, 16):08X}"
    banks = cat.get(ev)
    if banks:
        print(f"✓ 事件 {ev} 已登记在 {len(banks)} 个 bank：{', '.join(banks[:4])}")
        return 0
    print(f"⚠ 事件 {ev} 未在任何已扫描 bank 里找到（只说明本目录没登记，不等于游戏没声音）")
    return 2


# ---------------------------------------------------------------- 表读取
def open_tables():
    from table_dictionary import Dictionary                        # noqa: E402
    import entity_locid_scan as scan                               # noqa: E402
    names_json = HERE / "dl-type-names.json"
    if not names_json.is_file():
        names_json = pathlib.Path(r"D:/mod/dl-type-names.json")
    dic = Dictionary((BASE / "dl_library.dl_typelib").read_bytes(), scan.load_names(names_json))
    ent = (BASE / "generated_entities.dl_bin").read_bytes()
    blocks = {}
    for b in scan.parse_blocks(ent):
        g = scan.geometry(dic, b)
        if g is None:
            continue
        g = scan.check_geometry(ent, b, g)
        if not g.get("ok"):
            continue
        blocks[scan.name_of(dic, b["type_id"])] = (b, g, scan.hashmap(ent, b, g))
    return ent, blocks, dic


def sweep_ids(blob: bytes, idx: dict) -> list[tuple[int, int, dict]]:
    hits = []
    for off in range(0, len(blob) - 7, 8):
        val = struct.unpack_from("<Q", blob, off)[0]
        got = resolve(idx, val)
        if got:
            hits.append((off, val, got))
    return hits


def item_packages(key: int) -> list[str]:
    ent, blocks, _ = open_tables()
    b, g, hmap = blocks["LoadoutPackageComponentData"]
    r = hmap.get(key)
    if r is None:
        return []
    at = b["payload_at"] + g["index_size"] + r * g["stride"]
    pk = struct.unpack_from("<Q", ent, at + 8)[0]
    return [f"{pk:016x}"] if pk else []


def projectile_types_of(key: int) -> list[int]:
    ent, blocks, _ = open_tables()
    b, g, hmap = blocks["ProjectileWeaponComponentData"]
    r = hmap.get(key)
    if r is None:
        return []
    at = b["payload_at"] + g["index_size"] + r * g["stride"]
    row = ent[at:at + g["stride"]]
    out = []
    for off in (0x000, 0x240):
        if off + 4 <= len(row):
            out.append(struct.unpack_from("<I", row, off)[0])
    return [x for x in out if x]


# ---------------------------------------------------------------- 引用链
def chain_entity(idx: dict, key: int) -> tuple[dict, list]:
    ent, blocks, _ = open_tables()
    node, out = {"kind": "entity", "id": _k(key), "components": []}, []
    for comp, (b, g, hmap) in sorted(blocks.items()):
        r = hmap.get(key)
        if r is None:
            continue
        at = b["payload_at"] + g["index_size"] + r * g["stride"]
        row = ent[at:at + g["stride"]]
        leaves = []
        for off, val, got in sweep_ids(row, idx):
            leaves.append({"offset": f"+0x{off:03X}", "id": _k(val), "type": got["type"],
                           "name": got["name"][:48], "pkgs": got["pkgs"]})
            out.append((comp, off, val, got))
        if leaves:
            node["components"].append({"component": comp.replace("ComponentData", ""),
                                       "stride": g["stride"], "leaves": leaves})
    return node, out


def explosion_row_at(etype: int) -> tuple[bytes, int]:
    plain = (BASE / "generated_explosion_settings.dl_bin").read_bytes()
    for i in range((len(plain) - EXPL_BASE) // EXPL_STRIDE):
        at = EXPL_BASE + i * EXPL_STRIDE
        if struct.unpack_from("<I", plain, at)[0] == etype:
            return plain, at
    raise SystemExit(f"✗ 爆炸表里没有 type {etype} 的行")


def chain_explosion(idx: dict, etype: int, snd: dict) -> tuple[dict, list]:
    plain, at = explosion_row_at(etype)
    row = plain[at:at + EXPL_STRIDE]
    node, out = {"kind": "explosion", "type": etype, "leaves": [], "shake": []}, []
    pid = struct.unpack_from("<Q", row, 0x38)[0]
    got = resolve(idx, pid)
    node["leaves"].append({"offset": "+0x038", "id": _k(pid), "why": "粒子特效 file_id",
                           "type": (got or {}).get("type", "缺失"),
                           "name": (got or {}).get("name", "")[:48],
                           "pkgs": (got or {}).get("pkgs", [])})
    out.append(("Explosion", 0x38, pid, got or {"type": "缺失", "name": "", "pkgs": []}))
    h = struct.unpack_from("<I", row, 0x40)[0]
    node["leaves"].append({"offset": "+0x040", "id": f"0x{h:08X}", "why": "未知 32 位哈希（疑似音效事件）",
                           "type": "sound?" if snd.get(f"0x{h:08X}") else "未定位", "name": "", "pkgs": []})
    rel, cnt = struct.unpack_from("<I", row, 0x28)[0], struct.unpack_from("<I", row, 0x30)[0]
    if 0 < cnt < 64 and rel and EXPL_PAYLOAD + rel + cnt * 8 <= len(plain):
        for i in range(cnt):
            val = struct.unpack_from("<Q", plain, EXPL_PAYLOAD + rel + i * 8)[0]
            got = resolve(idx, val)
            node["shake"].append({"id": _k(val), "type": (got or {}).get("type", "缺失"),
                                  "pkgs": (got or {}).get("pkgs", [])})
            out.append(("Explosion.shake", i, val, got or {"type": "缺失", "name": "", "pkgs": []}))
    for off, val, got in sweep_ids(row, idx):
        if off == 0x38:
            continue
        node["leaves"].append({"offset": f"+0x{off:03X}", "id": _k(val), "why": "全行扫描命中",
                               "type": got["type"], "name": got["name"][:48], "pkgs": got["pkgs"]})
        out.append(("Explosion.sweep", off, val, got))
    return node, out


def find_entity(name_or_id: str) -> tuple[int, str]:
    if name_or_id.lower().startswith("0x"):
        return int(name_or_id, 16), name_or_id
    p = pathlib.Path(r"D:/mod/work/repo-datamined/refs/entity-locid-names.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    q = name_or_id.strip().lower()
    ents = data["entity_index"]
    # 优先级：code 精确 > 名字精确 > 名字子串（否则 "Machine Gun" 会先命中 "Heavy Machine Gun"）
    for pred in (lambda e: (e.get("code") or "").lower() == q,
                 lambda e: (e.get("name") or "").lower() == q,
                 lambda e: q in ((e.get("name") or "") + " " + (e.get("code") or "")).lower()):
        hits = [e for e in ents if pred(e)]
        if hits:
            e = hits[0]
            tip = f"（同名/相近 {len(hits)} 个，取第一个" + (f"：{hits[1].get('code')}" if len(hits) > 1 else "") + "）"
            return int(e["key"], 16), f"{e.get('name')} ({e.get('code')}){tip if len(hits) > 1 else ''}"
    raise SystemExit(f"✗ 名字表里没有 {name_or_id!r}")


def collect(a) -> tuple[list, list[str], str]:
    idx = load_index(a.index)
    snd = load_sound_catalog(a.sound_index)
    if a.explosion:
        node, out = chain_explosion(idx, a.explosion, snd)
        return out, [], f"explosion {a.explosion}"
    key, label = (int(a.entity, 16), a.entity) if a.entity else find_entity(a.weapon)
    node, out = chain_entity(idx, key)
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(node, ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    return out, item_packages(key), label


def cmd_chain(a) -> int:
    out, roots, label = collect(a)
    print(json.dumps({"target": label, "declared_packages": roots,
                      "leaves": [{"component": c, "offset": f"+0x{o:03X}", "id": _k(v),
                                  **g} for c, o, v, g in out]},
                     ensure_ascii=False, indent=1)[:6000])
    miss = [x for x in out if x[3]["type"] == "缺失"]
    print(f"\n目标 {label}｜叶子 {len(out)}｜包 {len({p for _,_,_,g in out for p in g['pkgs']})}｜缺失 {len(miss)}")
    return 0 if not miss else 2


# ---------------------------------------------------------------- 驻留计划
def patch_state(game: str, host: str) -> tuple[int, bool, list[str]]:
    d = pathlib.Path(game)
    nums, missing = [], []
    for p in d.glob(f"{host}.patch_*"):
        tail = p.name.split("patch_")[-1]
        if tail.isdigit():
            nums.append(int(tail))
            for ext in (".gpu_resources", ".stream"):
                if not (d / (p.name + ext)).is_file():
                    missing.append(p.name + ext)
    nums.sort()
    contiguous = nums == list(range(max(nums) + 1)) if nums else True
    return (max(nums) + 1 if nums else 0), contiguous, missing


def cmd_plan(a) -> int:
    out, roots, label = collect(a)
    game = pathlib.Path(a.game)
    installed = {p.name.split(".patch_")[0] for p in game.glob("*.patch_*")}
    assume = set(a.assume.split(",")) if a.assume else set(BASE_SHARED)
    same, cross, miss = {}, {}, []
    for comp, off, val, got in out:
        if got["type"] == "缺失" or not got["pkgs"]:
            miss.append((comp, off, val))
            continue
        pkgs = got["pkgs"]
        hit = [p for p in pkgs if p in roots]
        if hit:
            same.setdefault(hit[0], []).append((got["type"], _k(val)))
            continue
        pick = next((p for p in pkgs if p in assume or p in installed), pkgs[0])
        cross.setdefault(pick, []).append((got["type"], _k(val), got["name"][:36]))
    nxt, contiguous, companions = patch_state(a.game, HOST_PKG)
    print(f"目标：{label}")
    print(f"声明包（LoadoutPackage）：{', '.join(roots) or '—（无声明）'}")
    print(f"同包 {sum(len(v) for v in same.values())} 条（{len(same)} 包）｜"
          f"跨包 {sum(len(v) for v in cross.values())} 条（{len(cross)} 包）｜缺失 {len(miss)}")
    print(f"G4 补丁序号连续 {'PASS' if contiguous else 'FAIL'}（下一个 {nxt}）｜伴生缺失 {len(companions)}")
    for pkg, items in sorted(cross.items(), key=lambda kv: -len(kv[1]))[:12]:
        kinds: dict[str, int] = {}
        for t, _, _ in items:
            kinds[t] = kinds.get(t, 0) + 1
        tag = "已常驻" if pkg in assume or pkg in installed else "需驻留"
        print(f"  [{tag}] {pkg}: {len(items)} 条 {kinds}")
    if len(cross) > 12:
        print(f"  … 另有 {len(cross) - 12} 个跨包包")
    if miss:
        print(f"\nG3 缺失资源 {len(miss)} 个（索引里解析不到 → 装进去会变灰块/占位）:")
        for comp, off, val in miss[:10]:
            print(f"   {comp} +0x{off:03X} = {_k(val)}")
        if not a.allow_missing:
            print("✗ 拒绝出驻留计划（对应『缺失粒子阻止安装』）——确认为占位再加 --allow-missing")
            return 2
    need = [p for p in cross if p not in assume and p not in installed]
    order = sorted(need, key=lambda q: -len(cross[q]))
    plan_pkgs = ([roots[0]] if roots and roots[0] not in installed else []) + order
    if a.max_pkgs:
        plan_pkgs = plan_pkgs[: a.max_pkgs]
    if not plan_pkgs:
        print("✓ 不需要新增驻留：跨包资源都已常驻")
        return 0
    pdir = pathlib.Path(a.out)
    pdir.mkdir(parents=True, exist_ok=True)
    # —— plan.sh（命令清单，可人工核对）
    idx_next = nxt
    lines = [f"# resdep 驻留计划：{label}",
             f"# 声明包 {', '.join(roots) or '-'}｜host {HOST_PKG}｜起始序号 {nxt}", ""]
    for i, pkg in enumerate(plan_pkgs):
        note = "# ① 目标件自己的包" if roots and pkg == roots[0] else "# ② 跨包依赖"
        lines.append(note + chr(10) + f"python tools/whole_package_patch.py build --package {pkg} "
                     f"--host {HOST_PKG} --index {idx_next + i} --out {pdir / pkg} --install")
    (pdir / "plan.sh").write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    print(chr(10) + f"写入 {pdir / 'plan.sh'}（{len(plan_pkgs)} 个包）")
    # —— 实机验证清单
    kinds = {}
    for comp, off, val, got in out:
        kinds[got["type"]] = kinds.get(got["type"], 0) + 1
    vlines = [f"# 实机验证清单：{label}", "",
              f"- 驻留包：{len(plan_pkgs)} 个（host `{HOST_PKG}`，序号 {nxt}–{nxt + len(plan_pkgs) - 1}）",
              "- 跨包资源：" + ("、".join(f"{kk}×{vv}" for kk, vv in sorted(kinds.items())) or "—"),
              f"- 缺失资源：{len(miss)}（G3 {'拦下' if miss else '通过'}）", "",
              "## 三级结论（不要混）",
              "1. **资源解析到**（resdep 保证）→ 2. **驻留写进去**（whole_package_patch G1–G8 保证）→ 3. **游戏里对**（只有下面这张表能证）", "",
              "## 验证表（逐条打勾，全绿才算过）", "",
              "| # | 检查项 | 期望 | 结果 | 备注 |", "|---:|---|---|---|---|"]
    rows = []
    if "particles" in kinds:
        rows.append(("粒子特效", "触发时出现预期特效，**不是灰块/半透明方块**（灰块=粒子资源仍没加载）"))
    if "camera_shake" in kinds:
        rows.append(("震屏", "命中/爆炸时有震屏"))
    if any(k.startswith("wwise") for k in kinds):
        rows.append(("音效", "有声音；**没声音不等于装失败，但也不等于通过**（事件可能未登记）"))
    if any(k in kinds for k in ("mesh", "physics", "bones", "animation", "state_machine")):
        rows.append(("模型", "外观正确、不紫问号、不悬空不缩地"))
    rows += [("开火", "能正常开火，弹道/伤害符合预期"),
             ("装填/弹药", "能装填且备弹显示正常（若该武器有弹匣）"),
             ("稳定性", "连续使用 30 秒不崩溃、不掉帧到不可玩")]
    for i, (item, expect) in enumerate(rows, 1):
        vlines.append(f"| {i} | {item} | {expect} | ☐ | |")
    vlines += ["", "## 回滚",
               "```bash",
               f"# 删掉本次驻留补丁（{len(plan_pkgs)} 个包 × 3 个文件）"]
    for i in range(len(plan_pkgs)):
        n = nxt + i
        vlines.append(f'rm -f "{{game}}/{HOST_PKG}.patch_{n}"{{,.gpu_resources,.stream}}')
    vlines += ["```", "",
               f"> 目标件本身的字段改动回滚：用你改之前的那份 `.plain` 重新封包装盘"]
    (pdir / "VERIFY.md").write_text(chr(10).join(vlines) + chr(10), encoding="utf-8")
    print(f"写入 {pdir / 'VERIFY.md'}（{len(rows)} 条验证项）")
    if not a.apply:
        print("（只生成了计划；加 --apply 才会真正装盘）")
        return 0
    # —— 一键装盘（失败整体回滚）
    nxt2, contiguous2, companions2 = patch_state(a.game, HOST_PKG)
    if not contiguous2 or companions2:
        print(f"✗ 装盘前检查失败：序号连续={contiguous2} 伴生缺失={len(companions2)} —— 先修盘再装")
        return 3
    root = HERE.parent
    made: list[tuple[str, int]] = []
    for i, pkg in enumerate(plan_pkgs):
        idx_use = nxt2 + i
        print(f"[{i+1}/{len(plan_pkgs)}] 驻留 {pkg} → patch_{idx_use} …")
        proc = subprocess.run([sys.executable, str(HERE / "whole_package_patch.py"), "build",
                               "--package", pkg, "--host", HOST_PKG, "--index", str(idx_use),
                               "--out", str(pdir / pkg), "--install"],
                              cwd=str(root), capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            print(f"✗ 失败：{proc.stdout[-500:]}{proc.stderr[-300:]}")
            print("↩ 整体回滚本次已装的补丁…")
            for done_pkg, n in made:
                for ext in ("", ".gpu_resources", ".stream"):
                    q = pathlib.Path(a.game) / f"{HOST_PKG}.patch_{n}{ext}"
                    if q.is_file():
                        q.unlink()
                print(f"   删除 patch_{n}（{done_pkg}）")
            print("✗ 已回滚到装盘前状态")
            return 4
        made.append((pkg, idx_use))
    nxt3, contiguous3, companions3 = patch_state(a.game, HOST_PKG)
    print(chr(10) + f"✓ 装盘完成：{len(made)} 个补丁（patch_{nxt2}–patch_{nxt2 + len(made) - 1}）")
    print(f"G4 复检：序号连续 {'PASS' if contiguous3 else 'FAIL'}；伴生缺失 {len(companions3)}")
    print(f"→ 下一步：按 {pdir / 'VERIFY.md'} 进游戏逐条打勾")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("index", help="拉全档资源清单并建 id→包 索引")
    p.add_argument("--game", default=GAME_DEFAULT)
    p.add_argument("--out", default=str(INDEX_DEFAULT))
    p.add_argument("--reuse", action="store_true")
    p.set_defaults(func=cmd_index)

    for name, func in (("chain", cmd_chain), ("plan", cmd_plan)):
        p = sub.add_parser(name)
        p.add_argument("--entity")
        p.add_argument("--weapon")
        p.add_argument("--explosion", type=lambda v: int(v, 0))
        p.add_argument("--index", default=None)
        p.add_argument("--sound-index", default=None)
        p.add_argument("--allow-missing", action="store_true")
        p.add_argument("--game", default=GAME_DEFAULT)
        p.add_argument("--assume", default="")
        p.add_argument("--out", default="D:/mod/out/resdep/plan")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--apply", action="store_true", help="plan: 真正装盘（失败整体回滚）")
        p.add_argument("--max-pkgs", type=int, default=0, help="plan: 最多装几个包（自测用）")
        p.add_argument("--json", default=None)
        p.set_defaults(func=func)

    p = sub.add_parser("sound-catalog", help="解 wwise bank 的 HIRC，建事件目录")
    p.add_argument("--game", default=GAME_DEFAULT)
    p.add_argument("--index", default=None)
    p.add_argument("--banks", default=str(BANKS_DEFAULT))
    p.add_argument("--out", default=str(SOUND_DEFAULT))
    p.add_argument("--limit", type=int, default=0)
    p.set_defaults(func=cmd_sound_catalog)

    p = sub.add_parser("sound", help="查一个 Wwise 事件 id 是否已登记")
    p.add_argument("--event", required=True)
    p.add_argument("--sound-index", default=None)
    p.set_defaults(func=cmd_sound)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
