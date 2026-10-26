#!/usr/bin/env python3
"""whole_package_patch.py -- 把**一个包的整包资源**打成 `<宿主包>.patch_<N>`（资源层驻留）。

为什么需要它
    「有限跨包加载」只有 `+0xA8` / `+0xF8` 几十个口子，而 `.patch_N` 是把**资源**塞进
    **已经常驻**的包、按 `file_id` 全局可查 —— 不受口数限制。整包（mesh / bones / texture(GPU) /
    animation / state_machine / … 全套）也能这样驻留，已实测多轮（见
    docs/engine/RESOURCE-RESIDENCY-26088801.md 的 P1–P4）。
    以前每做一次都要手工 `srkit unpack --raw` → 改文件 → 改 `resource.json` 的 sha → `srkit pack`，
    这个工具把四步串成一条命令，并加 G1–G8 门禁。

它做的事
    ① `srkit list --package`：拿到源包清单（G1），记下类型直方图与 toc/gpu/stream 总量
    ② `srkit unpack --raw`：整包解到工作区
    ③ `--edit <type>:<id>=<file>`：把工作区里该资源的 `toc.bin` 换掉，并**同步改 `resource.json`
       里的 size/sha256**（两个地方：`blobs.toc` 与 `payloads[name=toc.bin]`）—— 这一步是手工流程里
       最容易漏的
    ④ `srkit pack --name <宿主>.patch_<N>`：出 `<patch>` + `.gpu_resources` + `.stream`
    ⑤ 复核：补丁能解析、条目数 == G1、每个 `--edit` 的载荷从补丁里 dump 回来**逐字节相等**（G4）、
       伴生文件该有就有（G5）、序号连续（G6）、sha256（G7）

用法
    # 只解包看看包里有什么
    python tools/whole_package_patch.py list --package 11bbdf8ce39e5fc5

    # 整包 → 宿主包第 N 条补丁（默认自动取下一个连续序号）
    python tools/whole_package_patch.py build \
        --package 11bbdf8ce39e5fc5 --host f6fb08cc02d24255 \
        --out D:/mod/out/rocket-res-patch

    # 整包 + 顺手改一个资源（例如把改好的 state_machine 带进去）
    python tools/whole_package_patch.py build \
        --package 11bbdf8ce39e5fc5 --host f6fb08cc02d24255 \
        --edit state_machine:0x37079568DC86E9C6=D:/mod/out/sm-patch8/sm_rocket.bin \
        --out D:/mod/out/rocket-res-patch

    # 复核一个已经做出来的补丁
    python tools/whole_package_patch.py check D:/mod/out/rocket-res-patch/f6fb08cc02d24255.patch_1 \
        --edit state_machine:0x37079568DC86E9C6=D:/mod/out/sm-patch8/sm_rocket.bin

门禁
    G1 源包可列且条目数 > 0        G2 --edit 的资源在工作区里找得到（且 type/id 都对得上）
    G3 补丁可解析、条目数 == G1    G4 改过的载荷 dump 回来逐字节相等
    G5 伴生文件齐全（有 gpu/stream 才要求）   G6 序号连续（该宿主的下一个空位）
    G7 sha256 打印                  G8 `resource.json` 的 size/sha256 与写入一致

依赖
    `srkit`（HD2SDK 检出，`python -m srkit`）；同目录的 `resource_patch.py`（复用它的补丁解析器）。
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from resource_patch import TYPE_NAMES, open_patch, type_label          # noqa: E402

DEFAULT_GAME = r"D:\SteamLibrary\steamapps\common\Helldivers 2\data"
SDK_CANDIDATES = [
    os.environ.get("HD2SDK", ""),
    r"C:\Users\Admin\HD2SDK-CommunityEdition",
]

NAME_OF_TYPE = {v: k for k, v in TYPE_NAMES.items()}


def find_sdk() -> str:
    for root in SDK_CANDIDATES:
        if root and os.path.isfile(os.path.join(root, "srkit", "__init__.py")):
            return root
    raise SystemExit("✗ 找不到 HD2SDK 检出（设 HD2SDK=<path> 或 --sdk）")


def sha16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def run_srkit(sdk: str, argv: list[str], quiet: bool = True) -> str:
    cmd = [sys.executable, "-m", "srkit"] + argv
    proc = subprocess.run(cmd, cwd=sdk, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        print("".join((proc.stdout or "")[-2000:]))
        print("".join((proc.stderr or "")[-2000:]), file=sys.stderr)
        raise SystemExit(f"✗ srkit {' '.join(argv[:2])} 失败（exit {proc.returncode}）")
    if not quiet:
        print((proc.stdout or "").strip())
    return proc.stdout or ""


def srkit_entries(sdk: str, game: str, package: str) -> list[dict]:
    """srkit list --json → 条目列表（类型名、file_id_hex、toc/gpu/stream 尺寸、可选 name）。"""
    proc = subprocess.run([sys.executable, "-m", "srkit", "list", game,
                           "--package", package, "--json",
                           "--hashlists", os.path.join(sdk, "hashlists")],
                          cwd=sdk, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(f"✗ srkit list 失败：{(proc.stderr or '')[-800:]}")
    return json.loads(proc.stdout)


def parse_edit(spec: str) -> tuple[int, int, str]:
    """'state_machine:0x37079568DC86E9C6=path' -> (type_id, file_id, path)"""
    if "=" not in spec or ":" not in spec:
        raise SystemExit(f"✗ --edit 需要 <type>:<id>=<file>，收到 {spec!r}")
    head, path = spec.split("=", 1)
    tname, fid = head.split(":", 1)
    tname = tname.strip()
    if tname not in NAME_OF_TYPE:
        raise SystemExit(f"✗ 不认识的资源类型 {tname!r}（可用：{', '.join(sorted(NAME_OF_TYPE))}）")
    try:
        file_id = int(fid, 16)
    except ValueError:
        raise SystemExit(f"✗ id 不是十六进制：{fid!r}")
    if not os.path.isfile(path):
        raise SystemExit(f"✗ 载荷文件不存在：{path}")
    return NAME_OF_TYPE[tname], file_id, os.path.abspath(path)


def find_resource_dir(pkgdir: str, type_id: int, file_id: int) -> str | None:
    for res in sorted(glob.glob(os.path.join(pkgdir, "resources", "*"))):
        meta = os.path.join(res, "resource.json")
        if not os.path.isfile(meta):
            continue
        try:
            j = json.load(open(meta, encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            continue
        if int(j.get("type_id", -1)) == type_id and int(j.get("file_id", -1)) == file_id:
            return res
    return None


def apply_edit(res_dir: str, payload: str) -> dict:
    toc = os.path.join(res_dir, "toc.bin")
    if not os.path.isfile(toc):
        names = [n for n in os.listdir(res_dir) if n.endswith(".bin")]
        raise SystemExit(f"✗ {res_dir} 里没有 toc.bin（有 {names}）")
    old = open(toc, "rb").read()
    new = open(payload, "rb").read()
    diff = sum(1 for a, b in zip(old, new) if a != b) + abs(len(old) - len(new))
    with open(toc, "wb") as f:
        f.write(new)
    h = hashlib.sha256(new).hexdigest()
    meta_path = os.path.join(res_dir, "resource.json")
    meta = json.load(open(meta_path, encoding="utf-8"))
    if "blobs" in meta and "toc" in meta["blobs"]:
        meta["blobs"]["toc"]["size"] = len(new)
        meta["blobs"]["toc"]["sha256"] = h
    changed_meta = False
    for p in meta.get("payloads", []):
        if p.get("name") == "toc.bin":
            p["size"] = len(new)
            p["sha256"] = h
            changed_meta = True
    if not changed_meta and "blobs" in meta:
        changed_meta = True
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(meta, indent=1, ensure_ascii=False))
    return {"old_size": len(old), "new_size": len(new), "diff_bytes": diff,
            "sha256": h, "meta_updated": changed_meta}


def next_index(host: str, *dirs: str) -> int:
    idx = -1
    pat = re.compile(re.escape(host) + r"\.patch_(\d+)$")
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            m = pat.match(name)
            if m:
                idx = max(idx, int(m.group(1)))
    return idx + 1


def cmd_list(args) -> int:
    sdk = args.sdk or find_sdk()
    entries = srkit_entries(sdk, args.game, args.package)
    hist: dict[str, int] = {}
    toc = gpu = stream = 0
    for e in entries:
        hist[e["type"]] = hist.get(e["type"], 0) + 1
        toc += e["toc_size"]; gpu += e["gpu_size"]; stream += e["stream_size"]
    print(f"包 {args.package}: {len(entries)} 条资源  "
          f"toc={toc:,} B  gpu={gpu:,} B  stream={stream:,} B")
    print("  类型：" + "  ".join(f"{k}×{v}" for k, v in sorted(hist.items(), key=lambda kv: -kv[1])))
    if args.verbose:
        for e in entries:
            print(f"  {e['type']:<14} {e['file_id_hex']}  toc={e['toc_size']:>9,} "
                  f"gpu={e['gpu_size']:>9,} stream={e['stream_size']:>8,}  {e.get('name') or ''}")
    return 0


def cmd_build(args) -> int:
    sdk = args.sdk or find_sdk()
    game = args.game
    if not os.path.isdir(game):
        raise SystemExit(f"✗ 游戏 data 目录不存在：{game}")
    edits = [parse_edit(s) for s in args.edit]
    out = os.path.abspath(args.out or os.path.join(r"D:\mod\out\wholepkg", args.package))
    work = os.path.abspath(args.work or os.path.join(out, "_ws"))
    os.makedirs(out, exist_ok=True)

    # ---- G6 序号（先判，免得白干）
    index = args.index if args.index is not None else next_index(args.host, out, game)
    pat_name = f"{args.host}.patch_{index}"
    print(f"[G6] 补丁名 {pat_name}（该宿主下一个连续序号）")

    # ---- G1 源包清单
    entries = srkit_entries(sdk, game, args.package)
    if not entries:
        raise SystemExit("✗ [G1] 源包没有任何资源")
    toc_tot = sum(e["toc_size"] for e in entries)
    gpu_tot = sum(e["gpu_size"] for e in entries)
    str_tot = sum(e["stream_size"] for e in entries)
    print(f"[G1] 源包 {args.package}: {len(entries)} 条  toc={toc_tot:,} B  "
          f"gpu={gpu_tot:,} B  stream={str_tot:,} B")

    # ---- 解包
    if os.path.isdir(work) and not args.reuse_work:
        shutil.rmtree(work)
    if not os.path.isdir(work):
        print(f"[..] srkit unpack -> {work}")
        run_srkit(sdk, ["unpack", game, "-o", work, "--package", args.package, "--raw"],
                  quiet=False)
    pkgdir = os.path.join(work, args.package)
    if not os.path.isdir(pkgdir):
        cand = [d for d in os.listdir(work) if os.path.isdir(os.path.join(work, d))]
        if len(cand) == 1:
            pkgdir = os.path.join(work, cand[0])
        else:
            raise SystemExit(f"✗ 工作区里找不到包目录（有 {cand}）")

    # ---- G2 + ③ 改资源
    edited = []
    for type_id, file_id, payload in edits:
        res_dir = find_resource_dir(pkgdir, type_id, file_id)
        if res_dir is None:
            raise SystemExit(f"✗ [G2] 工作区里没有 {type_label(type_id)} {file_id:#018x}")
        info = apply_edit(res_dir, payload)
        edited.append({"type_id": type_id, "file_id": file_id, "payload": payload, **info})
        print(f"[G2] 改了 {type_label(type_id)} {file_id:#018x}: "
              f"{info['old_size']:,} → {info['new_size']:,} B（diff {info['diff_bytes']} B）"
              f"  resource.json sha={info['sha256'][:16]}"
              f"{'  ✓' if info['meta_updated'] else '  ⚠ 没找到 payloads/toc.bin 项'}")

    if args.no_pack:
        print("（--no-pack：只解包/改资源，不打包）")
        return 0

    # ---- ④ 打包
    print(f"[..] srkit pack -> {pat_name}")
    run_srkit(sdk, ["pack", work, "-o", out, "--name", pat_name], quiet=False)

    patch = os.path.join(out, pat_name)
    gpu_p, str_p = patch + ".gpu_resources", patch + ".stream"
    if not os.path.isfile(patch):
        raise SystemExit(f"✗ 没有产出 {patch}")

    # ---- G3 补丁可解析 + 条目数
    got = open_patch(patch)
    if len(got) != len(entries):
        raise SystemExit(f"✗ [G3] 补丁条目 {len(got)} != 源包 {len(entries)}")
    print(f"[G3] 补丁可解析，条目数 {len(got)} == 源包 {len(entries)} ✓")

    # ---- G4 改过的载荷回读
    for item in edited:
        hit = next((e for e in got if int(e.type_id) == item["type_id"]
                    and int(e.file_id) == item["file_id"]), None)
        if hit is None:
            raise SystemExit(f"✗ [G4] 补丁里没有 {type_label(item['type_id'])} {item['file_id']:#018x}")
        blob = bytes(hit.toc_data)
        want = open(item["payload"], "rb").read()
        if blob != want:
            raise SystemExit(f"✗ [G4] {type_label(item['type_id'])} {item['file_id']:#018x} "
                             f"回读 {len(blob):,} B != 载荷 {len(want):,} B")
        print(f"[G4] {type_label(item['type_id'])} {item['file_id']:#018x} 回读逐字节相等 ✓")

    # ---- G5 伴生文件
    gpu_sz = os.path.getsize(gpu_p) if os.path.isfile(gpu_p) else -1
    str_sz = os.path.getsize(str_p) if os.path.isfile(str_p) else -1
    if gpu_tot > 0 and gpu_sz <= 0:
        raise SystemExit("✗ [G5] 源包有 GPU 负载，但 .gpu_resources 缺失/为空")
    if str_tot > 0 and str_sz <= 0:
        raise SystemExit("✗ [G5] 源包有 stream 负载，但 .stream 缺失/为空")
    print(f"[G5] 伴生文件：.gpu_resources={max(gpu_sz,0):,} B  .stream={max(str_sz,0):,} B ✓")

    # ---- G7 sha256
    print(f"[G7] toc={os.path.getsize(patch):,} B sha256={sha16(patch)}")
    if gpu_sz > 0:
        print(f"     gpu={gpu_sz:,} B sha256={sha16(gpu_p)}")
    if str_sz > 0:
        print(f"     stream={str_sz:,} B sha256={sha16(str_p)}")

    # ---- G8 resource.json 复核（重新读一遍工作区，确认落盘的是新 sha）
    if edited:
        for item in edited:
            res_dir = find_resource_dir(pkgdir, item["type_id"], item["file_id"])
            meta = json.load(open(os.path.join(res_dir, "resource.json"), encoding="utf-8"))
            h = meta.get("blobs", {}).get("toc", {}).get("sha256")
            if h != item["sha256"]:
                raise SystemExit(f"✗ [G8] resource.json sha 不一致：{h} != {item['sha256'][:16]}")
        print("[G8] resource.json 的 size/sha256 与写入一致 ✓")

    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)
        print(f"（工作区已删：{work}；要留请加 --keep-work）")

    if args.install:
        for src in (patch, gpu_p, str_p):
            if not os.path.isfile(src):
                continue
            dst = os.path.join(game, os.path.basename(src))
            shutil.copyfile(src, dst)
            print(f"[install] {dst}  sha256={sha16(dst)}")
        installed = open_patch(patch)
        print(f"[install] 复核：目录里那份 {pat_name} 可解析、{len(installed)} 条 ✓")

    print(f"\n✓ 完成：{patch}")
    print(f"  安装：把 {pat_name} / .gpu_resources / .stream 三件拷到 <game>/data/")
    return 0


def cmd_check(args) -> int:
    patch = args.patch
    if not os.path.isfile(patch):
        raise SystemExit(f"✗ 没有 {patch}")
    entries = open_patch(patch)
    hist: dict[str, int] = {}
    for e in entries:
        hist[type_label(e.type_id)] = hist.get(type_label(e.type_id), 0) + 1
    print(f"{patch}: {len(entries)} 条  toc={os.path.getsize(patch):,} B")
    print("  类型：" + "  ".join(f"{k}×{v}" for k, v in sorted(hist.items(), key=lambda kv: -kv[1])))
    for p in (patch + ".gpu_resources", patch + ".stream"):
        print(f"  {os.path.basename(p)}: {os.path.getsize(p) if os.path.isfile(p) else '（缺）'}")
    for spec in args.edit:
        type_id, file_id, payload = parse_edit(spec)
        hit = next((e for e in entries if int(e.type_id) == type_id and int(e.file_id) == file_id), None)
        if hit is None:
            print(f"  ✗ {type_label(type_id)} {file_id:#018x} 不在补丁里")
            return 2
        ok = bytes(hit.toc_data) == open(payload, "rb").read()
        print(f"  {'✓' if ok else '✗'} {type_label(type_id)} {file_id:#018x} "
              f"{len(bytes(hit.toc_data)):,} B {'==' if ok else '!='} {os.path.basename(payload)}")
        if not ok:
            return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="整包资源 → <宿主包>.patch_<N>（资源层驻留）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--game", default=DEFAULT_GAME, help="游戏 data 目录")
        p.add_argument("--sdk", default=None, help="HD2SDK 检出（默认自动找）")

    p = sub.add_parser("list", help="列出一个包里的资源（不解包）")
    p.add_argument("--package", required=True)
    p.add_argument("--verbose", action="store_true")
    common(p); p.set_defaults(func=cmd_list)

    p = sub.add_parser("build", help="整包 → 补丁（可顺手改资源）")
    p.add_argument("--package", required=True, help="源包 id")
    p.add_argument("--host", required=True, help="宿主包 id（补丁文件名前半段）")
    p.add_argument("--index", type=int, default=None, help="补丁序号（默认自动取下一个连续值）")
    p.add_argument("--edit", action="append", default=[], help="<type>:<id>=<file>，可重复")
    p.add_argument("--out", default=None, help="输出目录（默认 D:/mod/out/wholepkg/<包 id>）")
    p.add_argument("--work", default=None, help="工作区目录（默认 <out>/_ws）")
    p.add_argument("--reuse-work", action="store_true", help="复用已有工作区（不重新解包）")
    p.add_argument("--keep-work", action="store_true", help="保留工作区")
    p.add_argument("--no-pack", action="store_true", help="只解包/改资源，不打包")
    p.add_argument("--install", action="store_true", help="打包后拷进 <game>/data（部署）")
    common(p); p.set_defaults(func=cmd_build)

    p = sub.add_parser("check", help="复核一个补丁（可核对改过的载荷）")
    p.add_argument("patch")
    p.add_argument("--edit", action="append", default=[])
    common(p); p.set_defaults(func=cmd_check)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
