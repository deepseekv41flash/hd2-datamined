#!/usr/bin/env python3
"""game_baseline.py -- 「盘面基线」(game-baseline.json)：记录 + 自检游戏 data 目录的部署状态。

WHY
    装过一堆补丁之后，"盘面现在是什么状态"只能靠记忆：哪个表被改过、哪个 `patch_N` 是谁的、
    游戏更新后哪些补丁过期了。第三方大型外观系统 HD2IAS 的做法是记录
    `bundle_database.data` / `bundles.nxa` 的 sha 基线 + `managed_bundle.json`，每次启动自检
    （见 docs/cases/RECON-HD2-INTEGRATED-ARMOR-SYSTEM.md §3.2）。本工具借这个思路做通用版：
    把 **data/game/*（数据表 + game.dll + typelib）**、少量关键数据文件、以及所有
    `*.patch_*` 补丁的 sha256 记成 JSON；核对时逐项比较并分类。

WHAT（三个子命令）
    snapshot  记录当前盘面 → baseline JSON
              `--override REL=FILE`：用"已知好文件"的 sha 覆盖某个路径（做 vanilla 基线用）
              `--no-patches`：期望盘面**没有**补丁（vanilla 基线的补丁清单 = 空）
    check     核对当前盘面 vs 基线：构建指纹 / 数据文件 changed|missing|new / 补丁清单 /
              大归档尺寸（只比 size，不读 20 GB）
              `--artifact REL=FILE`：额外断言"盘上这个文件 == 某个部署产物"（装盘证明）
    selftest  变异自检：临时夹具里证明 check 能抓到 changed / missing / new / 补丁漂移

EXIT CODE
    0 = 与基线完全一致；1 = 有漂移；2 = 用法 / IO 错误

判读（结论先行）
    * `game/dl_library.dl_typelib` 或 `game/game.dll` 与基线不符 ⇒ **不是同一个 build**
      （游戏更新了 / 基线不是这版）⇒ 先按 BUILDS.md 三步重建基线，别继续套补丁。
    * typelib/game.dll 相同、只有 `game/*.dl_bin` 变了 ⇒ 数据表补丁（我们这条路线）。
    * 多出 `*.patch_*` ⇒ 已部署的资源补丁（按 `<host>.patch_<N>` 分组列出）。
    * `bundles.NN.nxa` 尺寸变了 ⇒ 游戏内容更新（size-only 检查，因此只会粗报）。

用法
    python tools/game_baseline.py snapshot --out baselines/game-baseline-26251122-vanilla.json \
        --build 26251122 --label vanilla --no-patches \
        --override game/generated_entities.dl_bin=D:/mod/backups/spray-capsule/generated_entities.vanilla.dl_bin
    python tools/game_baseline.py check --baseline baselines/game-baseline-26251122-vanilla.json
    python tools/game_baseline.py check --baseline <b> --artifact game/generated_entities.dl_bin=out/x/generated_entities.dl_bin
    python tools/game_baseline.py selftest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                     # noqa: BLE001
        pass

SCHEMA = "HD2GameBaseline/1"
DEFAULT_DIR = r"D:\SteamLibrary\steamapps\common\Helldivers 2\data"

# 全量 sha256 的文件（除 game/ 下全部外，data 根的关键文件）
ROOT_HASHED = {"bundle_database.data", "bundles.nxa", "bundles.region_hints"}

# 只记 size 的大文件 / 安装物（bundles 单个数百 MB，读一遍 20 GB 没有意义）
RE_BUNDLE_CHUNK = re.compile(r"^bundles\.\d+\.nxa$")
RE_ROOT_BLOB = re.compile(r"^([0-9a-fA-F]{16})(\.stream|\.gpu_resources)?$")

# 补丁：<16hex>.patch_<N>[.gpu_resources|.stream]
RE_PATCH = re.compile(r"^([0-9a-fA-F]{16})\.patch_(\d+)(\.gpu_resources|\.stream)?$")

BUILD_KEYS = ("game/dl_library.dl_typelib", "game/game.dll")


# --------------------------------------------------------------------------- io
def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def guess_dir(arg: str | None) -> str:
    d = arg or os.environ.get("HD2_DATA") or DEFAULT_DIR
    if not os.path.isdir(os.path.join(d, "game")):
        raise SystemExit(f"✗ {d} 下没有 game/ 子目录（用 --dir 指定游戏 data 目录）")
    return d


# ------------------------------------------------------------------- scanning
def scan(data_dir: str, overrides: dict[str, str] | None = None,
         want_patches: bool = True) -> dict:
    """扫盘：返回 {files, inventory, patches, errors}。

    files     : relpath -> {size, sha256}（我们可能改的文件，全量哈希）
    inventory : relpath -> size（大归档 / 安装物，只记尺寸）
    patches   : group("<host>.patch_<N>") -> {main:{file,size,sha256}, sidecars:{...}}
    """
    overrides = overrides or {}
    files: dict[str, dict] = {}
    inventory: dict[str, int] = {}
    patches: dict[str, dict] = {}
    errors: list[str] = []

    def add_hash(rel: str, full: str) -> None:
        try:
            files[rel] = {"size": os.path.getsize(full), "sha256": sha256_file(full)}
        except OSError as exc:                            # noqa: BLE001
            errors.append(f"{rel}: {exc}")

    game_dir = os.path.join(data_dir, "game")
    for name in sorted(os.listdir(game_dir)):
        full = os.path.join(game_dir, name)
        if not os.path.isfile(full):
            continue
        rel = "game/" + name
        add_hash(rel, full)

    for name in sorted(os.listdir(data_dir)):
        full = os.path.join(data_dir, name)
        if not os.path.isfile(full):
            continue
        m = RE_PATCH.match(name)
        if m:
            if not want_patches:
                continue
            host, idx, suffix = m.group(1), m.group(2), m.group(3) or ""
            group = f"{host}.patch_{idx}"
            entry = patches.setdefault(group, {"main": None, "sidecars": {}})
            slot = f"main{suffix}" if suffix else "main"
            item = {"file": name, "size": os.path.getsize(full)}
            try:
                item["sha256"] = sha256_file(full)
            except OSError as exc:                        # noqa: BLE001
                errors.append(f"{name}: {exc}")
                continue
            if suffix:
                entry["sidecars"][suffix.lstrip(".")] = item
            else:
                entry["main"] = item
            continue
        if name in ROOT_HASHED:
            add_hash(name, full)
            continue
        if RE_BUNDLE_CHUNK.match(name):
            inventory[name] = os.path.getsize(full)
            continue
        if RE_ROOT_BLOB.match(name):
            inventory[name] = os.path.getsize(full)
            continue
        # 其它未归类文件：只记尺寸，避免漏掉安装物
        inventory[name] = os.path.getsize(full)

    # 显式覆盖（做 vanilla 基线时用"已知好文件"替换某路径）
    for rel, src in overrides.items():
        if not os.path.isfile(src):
            raise SystemExit(f"✗ --override 的源文件不存在：{src}")
        files[rel] = {"size": os.path.getsize(src), "sha256": sha256_file(src)}

    return {"files": files, "inventory": inventory, "patches": patches, "errors": errors}


def fingerprint(files: dict) -> dict:
    return {k: files.get(k, {}).get("sha256") for k in BUILD_KEYS}


# ---------------------------------------------------------------- subcommands
def cmd_snapshot(args) -> int:
    data_dir = guess_dir(args.dir)
    overrides = {}
    for spec in args.override:
        if "=" not in spec:
            raise SystemExit(f"✗ --override 需要 REL=FILE，收到 {spec!r}")
        rel, src = spec.split("=", 1)
        overrides[rel.replace("\\", "/")] = src
    snap = scan(data_dir, overrides=overrides, want_patches=not args.no_patches)
    if snap["errors"]:
        for e in snap["errors"]:
            print(f"  ⚠ {e}")
    doc = {
        "schema": SCHEMA,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "label": args.label or "",
        "build": args.build or "unknown",
        "dir_basename": os.path.basename(data_dir.rstrip("\\/")),
        "expect_patches": not args.no_patches,
        "files": snap["files"],
        "inventory": snap["inventory"],
        "patches": snap["patches"],
        "build_fingerprint": fingerprint(snap["files"]),
        "stats": {
            "files": len(snap["files"]),
            "inventory": len(snap["inventory"]),
            "patches": len(snap["patches"]),
            "hashed_bytes": sum(v["size"] for v in snap["files"].values()),
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    st = doc["stats"]
    print(f"✓ 基线已写入 {args.out}")
    print(f"  schema={SCHEMA}  build={doc['build']}  label={doc['label']!r}")
    print(f"  哈希文件 {st['files']} 个（{st['hashed_bytes']/1048576:.1f} MiB）"
          f" · 尺寸清单 {st['inventory']} 个 · 补丁组 {st['patches']} 个")
    fp = doc["build_fingerprint"]
    for k, v in fp.items():
        print(f"  {k}: {v or '（缺失）'}")
    return 0


def _load_baseline(path: str) -> dict:
    if not os.path.isfile(path):
        raise SystemExit(f"✗ 基线文件不存在：{path}")
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    if doc.get("schema") != SCHEMA:
        raise SystemExit(f"✗ 不是 {SCHEMA} 基线文件：{path}（schema={doc.get('schema')!r}）")
    return doc


def cmd_show(args) -> int:
    doc = _load_baseline(args.baseline)
    st = doc.get("stats") or {}
    print(f"基线 {args.baseline}")
    print(f"  schema={doc['schema']}  build={doc.get('build')}  label={doc.get('label')!r}"
          f"  created={doc.get('created_at')}")
    print(f"  哈希文件 {st.get('files', len(doc.get('files', {})))} 个"
          f"（{(st.get('hashed_bytes') or 0)/1048576:.1f} MiB）"
          f" · 尺寸清单 {st.get('inventory', len(doc.get('inventory', {})))} 个"
          f" · 补丁组 {st.get('patches', len(doc.get('patches', {})))} 个")
    fp = doc.get("build_fingerprint") or {}
    for k in BUILD_KEYS:
        print(f"  {k}: {fp.get(k) or '（基线未含）'}")
    return 0


def _fmt(n: int) -> str:
    return f"{n/1048576:.1f} MiB" if n >= 1048576 else f"{n} B"


def cmd_check(args) -> int:
    data_dir = guess_dir(args.dir)
    base = _load_baseline(args.baseline)
    overrides = {}
    for spec in args.override:
        rel, src = spec.split("=", 1)
        overrides[rel.replace("\\", "/")] = src
    # 期望盘面有没有补丁：vanilla 基线 = 期望没有；否则按基线清单核对
    cur = scan(data_dir, overrides=overrides,
               want_patches=True)
    exp_files = base.get("files") or {}
    exp_inv = base.get("inventory") or {}
    exp_pat = base.get("patches") or {}
    expect_patches = bool(base.get("expect_patches", True))

    changed, missing, new = [], [], []
    for rel, exp in sorted(exp_files.items()):
        got = cur["files"].get(rel)
        if got is None:
            missing.append(rel)
        elif got["sha256"] != exp["sha256"]:
            changed.append((rel, exp, got))
    for rel, got in sorted(cur["files"].items()):
        if rel not in exp_files:
            new.append((rel, got))

    inv_changed, inv_missing, inv_new = [], [], []
    for rel, size in sorted(exp_inv.items()):
        got = cur["inventory"].get(rel)
        if got is None:
            inv_missing.append(rel)
        elif got != size:
            inv_changed.append((rel, size, got))
    for rel, size in sorted(cur["inventory"].items()):
        if rel not in exp_inv:
            inv_new.append((rel, size))

    pat_extra, pat_missing, pat_changed = [], [], []
    for group, entry in sorted(cur["patches"].items()):
        if group not in exp_pat:
            if entry.get("main"):
                pat_extra.append((group, entry["main"]))
            else:
                pat_extra.append((group, None))
            continue
        e = exp_pat[group]
        if (entry.get("main") or {}).get("sha256") != (e.get("main") or {}).get("sha256"):
            pat_changed.append((group, (e.get("main") or {}).get("sha256"),
                                (entry.get("main") or {}).get("sha256")))
    for group in sorted(exp_pat):
        if group not in cur["patches"]:
            pat_missing.append(group)

    fp_exp = base.get("build_fingerprint") or {}
    fp_cur = {k: (cur["files"].get(k) or {}).get("sha256") for k in BUILD_KEYS}
    build_ok = all(fp_cur[k] and fp_exp.get(k) and fp_cur[k] == fp_exp[k] for k in BUILD_KEYS)

    artifact_fail = []
    for spec in args.artifact:
        if "=" not in spec:
            raise SystemExit(f"✗ --artifact 需要 REL=FILE，收到 {spec!r}")
        rel, src = spec.split("=", 1)
        rel = rel.replace("\\", "/")
        if not os.path.isfile(src):
            raise SystemExit(f"✗ --artifact 的文件不存在：{src}")
        want = sha256_file(src)
        got = (cur["files"].get(rel) or {}).get("sha256")
        ok = got == want
        print(f"  产物断言 {rel}: {'✓ 盘上文件 == 产物' if ok else '✗ 不一致'}")
        print(f"    盘上 {(got or '（缺失）')[:16]} · 产物 {want[:16]}")
        if not ok:
            artifact_fail.append(rel)

    drift = bool(changed or missing or new or inv_changed or inv_missing or inv_new
                 or pat_extra or pat_missing or pat_changed or artifact_fail)

    print(f"盘面自检：{data_dir}")
    print(f"基线：{args.baseline}  build={base.get('build')}  label={base.get('label')!r}")
    if build_ok:
        print(f"  ✓ 构建相同（typelib + game.dll 指纹一致）")
    else:
        print(f"  ✗ 构建不同！先按 BUILDS.md 三步复验，再考虑套补丁：")
        for k in BUILD_KEYS:
            mark = "✓" if (fp_cur[k] and fp_exp.get(k) and fp_cur[k] == fp_exp[k]) else "✗"
            print(f"    {mark} {k}")
            print(f"        盘上 {fp_cur[k] or '（缺失）'}")
            print(f"        基线 {fp_exp.get(k) or '（基线未含）'}")

    print(f"  数据/游戏文件：期望 {len(exp_files)} · 改动 {len(changed)} · 缺失 {len(missing)}"
          f" · 新增 {len(new)}")
    for rel, exp, got in changed[:args.max_list]:
        print(f"    ~ {rel}  {_fmt(exp['size'])} {exp['sha256'][:16]} → {_fmt(got['size'])} {got['sha256'][:16]}")
    if len(changed) > args.max_list:
        print(f"      …（还有 {len(changed)-args.max_list} 项）")
    for rel in missing[:args.max_list]:
        print(f"    - 缺失 {rel}")
    for rel, got in new[:args.max_list]:
        print(f"    + 新增 {rel} ({_fmt(got['size'])})")

    if inv_changed or inv_missing or inv_new:
        print(f"  大归档/安装物（size-only）：改尺寸 {len(inv_changed)} · 缺失 {len(inv_missing)}"
              f" · 新增 {len(inv_new)}")
        for rel, was, now in inv_changed[:args.max_list]:
            print(f"    ~ {rel}  {was} → {now} B  ⇒ 游戏内容/包体变过")
        for rel in inv_missing[:args.max_list]:
            print(f"    - 缺失 {rel}")
        for rel, size in inv_new[:args.max_list]:
            print(f"    + 新增 {rel} ({size} B)")
    else:
        print(f"  大归档/安装物：{len(exp_inv)} 项尺寸全部一致")

    if expect_patches and not exp_pat:
        print(f"  补丁清单：基线期望**空**（vanilla）· 盘上 {len(cur['patches'])} 组")
    elif expect_patches:
        print(f"  补丁清单：基线 {len(exp_pat)} 组 · 盘上 {len(cur['patches'])} 组"
              f" · 多出 {len(pat_extra)} · 缺失 {len(pat_missing)} · 改动 {len(pat_changed)}")
    else:
        print(f"  补丁清单：基线**不记录补丁**（vanilla 基线）· 盘上 {len(cur['patches'])} 组")
    for group, main in pat_extra[:args.max_list]:
        sha = (main or {}).get("sha256", "")[:16]
        size = _fmt((main or {}).get("size", 0))
        print(f"    + 已部署 {group}  {size}  {sha}")
    if len(pat_extra) > args.max_list:
        print(f"      …（还有 {len(pat_extra)-args.max_list} 组）")
    for group in pat_missing[:args.max_list]:
        print(f"    - 基线里的补丁不见了：{group}")
    for group, was, now in pat_changed[:args.max_list]:
        print(f"    ~ 补丁内容变了：{group}  {(was or '')[:16]} → {(now or '')[:16]}")

    print()
    if drift:
        print("✗ 有漂移：" + " · ".join(filter(None, [
            f"文件改动 {len(changed)}" if changed else "",
            f"文件缺失 {len(missing)}" if missing else "",
            f"文件新增 {len(new)}" if new else "",
            f"归档尺寸变 {len(inv_changed)}" if inv_changed else "",
            f"归档缺失 {len(inv_missing)}" if inv_missing else "",
            f"补丁多出 {len(pat_extra)}" if pat_extra else "",
            f"补丁缺失 {len(pat_missing)}" if pat_missing else "",
            f"补丁改动 {len(pat_changed)}" if pat_changed else "",
            f"产物不符 {len(artifact_fail)}" if artifact_fail else "",
        ])))
    else:
        print("✓ 盘面与基线完全一致（无漂移）")

    if args.json:
        report = {
            "verdict": "drift" if drift else "clean",
            "build_ok": build_ok,
            "changed": [{"path": r, "baseline": e, "current": c} for r, e, c in changed],
            "missing": missing,
            "new": [{"path": r, **c} for r, c in new],
            "inventory_changed": [{"path": r, "baseline": w, "current": c} for r, w, c in inv_changed],
            "inventory_missing": inv_missing,
            "inventory_new": [{"path": r, "size": s} for r, s in inv_new],
            "patches_extra": [{"group": g, "main": m} for g, m in pat_extra],
            "patches_missing": pat_missing,
            "patches_changed": [{"group": g, "baseline": w, "current": c} for g, w, c in pat_changed],
            "artifact_failed": artifact_fail,
        }
        print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if drift else 0


def cmd_selftest(args) -> int:
    """变异自检：在临时夹具里造盘 → 快照 → 变异 → 要求 check 精确抓到。"""
    ok = 0
    bad = 0

    def expect(cond: bool, msg: str) -> None:
        nonlocal ok, bad
        if cond:
            ok += 1
            print(f"  PASS {msg}")
        else:
            bad += 1
            print(f"  FAIL {msg}")

    root = tempfile.mkdtemp(prefix="hd2baseline-")
    try:
        data = os.path.join(root, "data")
        game = os.path.join(data, "game")
        os.makedirs(game)
        def w(path: str, data_bytes: bytes) -> None:
            with open(path, "wb") as f:
                f.write(data_bytes)
        w(os.path.join(game, "game.dll"), b"GAMEDLL-v1")
        w(os.path.join(game, "dl_library.dl_typelib"), b"TYPELIB-v1")
        w(os.path.join(game, "generated_entities.dl_bin"), b"ENTITIES-vanilla")
        w(os.path.join(game, "generated_damage_settings.dl_bin"), b"DAMAGE-vanilla")
        w(os.path.join(data, "bundle_database.data"), b"BUNDLEDB")
        w(os.path.join(data, "bundles.00.nxa"), b"X" * 1024)
        w(os.path.join(data, "02582f3da1f8daf5"), b"BLOB")
        w(os.path.join(data, "02582f3da1f8daf5.stream"), b"STREAM")

        base_path = os.path.join(root, "base.json")
        ns = argparse.Namespace(dir=data, out=base_path, label="selftest", build="test",
                                override=[], no_patches=False)
        expect(cmd_snapshot(ns) == 0, "snapshot 生成基线")
        base = json.load(open(base_path, encoding="utf-8"))
        expect(base["schema"] == SCHEMA, "schema 正确")
        expect(len(base["files"]) == 5, "game/ 4 个 + bundle_database=1 个被哈希")
        expect(base["inventory"].get("bundles.00.nxa") == 1024, "大归档只记尺寸")
        expect("02582f3da1f8daf5" in base["inventory"], "根 blob 进尺寸清单")

        def run_check(**kw) -> int:
            ns = argparse.Namespace(baseline=base_path, dir=data, json=False,
                                    max_list=20, override=[], artifact=[], **kw)
            return cmd_check(ns)

        expect(run_check() == 0, "未变异 → check exit 0（干净）")

        # 变异 1：改一个数据表
        w(os.path.join(game, "generated_entities.dl_bin"), b"ENTITIES-PATCHED")
        expect(run_check() == 1, "改动数据表 → check exit 1")
        w(os.path.join(game, "generated_entities.dl_bin"), b"ENTITIES-vanilla")

        # 变异 2：删一个文件
        os.remove(os.path.join(game, "generated_damage_settings.dl_bin"))
        expect(run_check() == 1, "缺失文件 → check exit 1")
        w(os.path.join(game, "generated_damage_settings.dl_bin"), b"DAMAGE-vanilla")

        # 变异 3：新增一个补丁组（基线期望没有补丁）
        w(os.path.join(data, "f6fb08cc02d24255.patch_0"), b"PATCH-PAYLOAD")
        w(os.path.join(data, "f6fb08cc02d24255.patch_0.stream"), b"")
        expect(run_check() == 1, "多出补丁 → check exit 1")
        os.remove(os.path.join(data, "f6fb08cc02d24255.patch_0"))
        os.remove(os.path.join(data, "f6fb08cc02d24255.patch_0.stream"))

        # 变异 4：归档尺寸变
        w(os.path.join(data, "bundles.00.nxa"), b"Y" * 2048)
        expect(run_check() == 1, "归档尺寸变 → check exit 1")
        w(os.path.join(data, "bundles.00.nxa"), b"X" * 1024)

        # 变异 5：构建指纹变（= 游戏更新）
        w(os.path.join(game, "dl_library.dl_typelib"), b"TYPELIB-v2")
        ns = argparse.Namespace(baseline=base_path, dir=data, json=True,
                                max_list=20, override=[], artifact=[])
        expect(cmd_check(ns) == 1, "构建指纹变 → check exit 1")
        w(os.path.join(game, "dl_library.dl_typelib"), b"TYPELIB-v1")

        # 产物断言：把基线里的 entities 换成"产物"路径不成立 → 失败；
        # 用同样的文件 → 通过
        art = os.path.join(root, "artifact.bin")
        w(art, b"ENTITIES-vanilla")
        ns = argparse.Namespace(baseline=base_path, dir=data, json=False,
                                max_list=20, override=[],
                                artifact=["game/generated_entities.dl_bin=" + art])
        expect(cmd_check(ns) == 0, "产物断言：完全一致 → exit 0")
        w(art, b"ENTITIES-OTHER")
        ns = argparse.Namespace(baseline=base_path, dir=data, json=False,
                                max_list=20, override=[],
                                artifact=["game/generated_entities.dl_bin=" + art])
        expect(cmd_check(ns) == 1, "产物断言：不一致 → exit 1")

        # vanilla 基线（--no-patches）+ 盘上已有补丁 → 仍报 extra
        vb = os.path.join(root, "vanilla.json")
        w(os.path.join(data, "9ba626afa44a3aa3.patch_0"), b"LUA")
        ns = argparse.Namespace(dir=data, out=vb, label="v", build="t",
                                override=[], no_patches=True)
        cmd_snapshot(ns)
        ns = argparse.Namespace(baseline=vb, dir=data, json=False, max_list=20,
                                override=[], artifact=[])
        expect(cmd_check(ns) == 1, "--no-patches 基线 + 盘上有补丁 → 漂移 exit 1")
        expect(len(json.load(open(vb, encoding="utf-8"))["patches"]) == 0,
               "--no-patches 基线补丁清单为空")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    print(f"\n自检：{ok} PASS / {bad} FAIL")
    return 0 if bad == 0 else 1


# --------------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser(description="盘面基线：记录 + 自检游戏 data 目录")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("snapshot", help="记录当前盘面 → baseline JSON")
    p.add_argument("--out", required=True)
    p.add_argument("--dir", default=None, help="游戏 data 目录")
    p.add_argument("--label", default="")
    p.add_argument("--build", default="")
    p.add_argument("--override", action="append", default=[], help="REL=FILE：用已知好文件覆盖某路径")
    p.add_argument("--no-patches", action="store_true", help="期望盘面无补丁（vanilla 基线）")
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("check", help="核对当前盘面 vs 基线")
    p.add_argument("--baseline", required=True)
    p.add_argument("--dir", default=None)
    p.add_argument("--override", action="append", default=[])
    p.add_argument("--artifact", action="append", default=[], help="REL=FILE：断言盘上文件 == 部署产物")
    p.add_argument("--json", action="store_true", help="末尾输出机器可读报告")
    p.add_argument("--max-list", type=int, default=20)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("show", help="打印基线摘要")
    p.add_argument("--baseline", required=True)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("selftest", help="变异自检（临时夹具）")
    p.set_defaults(func=cmd_selftest)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
