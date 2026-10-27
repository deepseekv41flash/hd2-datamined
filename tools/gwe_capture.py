#!/usr/bin/env python3
"""gwe_capture.py -- 给第三方 variant_mod 代理加一个**只读**响应落盘开关。

WHY
    能力边界要「探明」，缺的不是想法而是那张菜单：`GET /api/WarSeason/GalacticWarEffects`
    （约 300 条 effect）决定了引擎有哪些解释器（32/40/71…）、每条 effect 的 values 指向哪个
    本地对象。而端点表在游戏文件里拿不到（整装目录里 `/api/` 只剩两段 EAC 碎片），只能从流量里取。

HOW (why a patch and not a new proxy)
    那个代理已经把 TLS/CRL/chunked/gzip/回环拒绝这些坑趟平了（见它的 COMPAT 文档）。重写一遍是
    重复劳动且会引入同样的坑；我们要加的东西只有十几行：把匹配路径的**响应体**原样落盘。

SAFETY RULES (hard-coded, not configurable)
    * 只写**响应体**：不写 header、不写 cookie、不写 query、不写请求体 —— token 在请求头里。
    * 只落 `HD2_GWE_PATHS` 里列出的路径（缺省只有 GalacticWarEffects），其它一律不碰。
    * 有大小上限（`HD2_GWE_MAX`，缺省 8 MiB），超限只记一行日志。
    * 任何异常都被吞掉并记日志：抓包失败绝不允许影响代理主流程。
    * 不复制第三方代码进本仓库：就地打补丁 + `.bak` 备份，`unpatch` 可原样还原。

USAGE
    setx/export 不需要；PowerShell 里一次性设环境变量即可：
        $env:HD2_GWE_DUMP = "D:\\mod\\out\\gwe"
        $env:HD2_GWE_PATHS = "/api/WarSeason/GalacticWarEffects"
    python tools/gwe_capture.py status  --proxy <...>/tools/war_proxy.py
    python tools/gwe_capture.py patch   --proxy <...>/tools/war_proxy.py
    python tools/gwe_capture.py unpatch --proxy <...>/tools/war_proxy.py
    python tools/gwe_capture.py selftest            # 离线：复制一份代理 → 打补丁 → 编译 → 导入 → 调钩子

    打完补丁直接按原方式启动代理（run.ps1 / 面板都行）；进一次游戏后 `out/gwe/index.txt` 会多一行。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time

MARK = "DSH_GWE_CAPTURE_V1"

HELPER = '''
# ---- {mark} : read-only response dump (added by DSH tools/gwe_capture.py) ----
def _gwe_capture_dump(path, body, hdrs):
    """把匹配路径的响应体原样落盘，供离线分析。绝不写 header/token，异常一律吞掉。"""
    import gzip, hashlib, json as _json, os, re as _re, time as _time
    try:
        outdir = os.environ.get("HD2_GWE_DUMP", "")
        if not outdir or not body:
            return
        pats = [p.strip() for p in os.environ.get(
            "HD2_GWE_PATHS", "/api/WarSeason/GalacticWarEffects").split(",") if p.strip()]
        if not any(p in path for p in pats):
            return
        cap = int(os.environ.get("HD2_GWE_MAX", str(8 << 20)) or (8 << 20))
        raw = body
        if body[:2] == b"\\x1f\\x8b":
            try:
                raw = gzip.decompress(body)
            except Exception:
                raw = body
        if len(raw) > cap:
            log("gwe-dump skipped: %d B > cap %d" % (len(raw), cap))
            return
        os.makedirs(outdir, exist_ok=True)
        digest = hashlib.sha256(raw).hexdigest()
        slug = _re.sub(r"[^A-Za-z0-9]+", "_", path).strip("_")[-60:] or "body"
        stamp = _time.strftime("%Y%m%dT%H%M%SZ", _time.gmtime())
        # 按内容哈希命名 => 同一份响应被轮询多次也只落一个文件
        fp = os.path.join(outdir, "%s_%s.json" % (digest[:8], slug))
        if os.path.exists(fp):
            return
        with open(fp, "wb") as fh:
            fh.write(raw)
        try:
            _json.loads(raw.decode("utf-8", "replace"))
            kind = "json"
        except Exception:
            kind = "not-json"
        # 只记：时间 / 路径 / 字节数 / sha256 / 是否合法 JSON。不记 header。
        with open(os.path.join(outdir, "index.txt"), "a", encoding="utf-8") as ix:
            ix.write("%s\\t%s\\t%d\\t%s\\t%s\\n" % (stamp, path, len(raw), digest, kind))
        log("gwe-dump %s %d B -> %s" % (path.split("?")[0], len(raw), fp))
    except Exception as e:
        try:
            log("gwe-dump failed (ignored): %r" % e)
        except Exception:
            pass
# ---- /{mark} ----
'''

CALL = "                _gwe_capture_dump(path, rbody, rhdrs)\n"
# 插在 chunked 解码之后、改写之前：那时 rbody 已是完整（可能 gzip）的响应体
ANCHOR = '''                if "chunked" in rhdrs.get("transfer-encoding", "").lower():
                    rbody = dechunk(rbody)
                    dechunked = True
'''


def read(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8", errors="surrogateescape")


def write(p: pathlib.Path, s: str) -> None:
    p.write_text(s, encoding="utf-8", errors="surrogateescape", newline="")


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cmd_status(a) -> int:
    p = pathlib.Path(a.proxy)
    if not p.exists():
        print(f"FAIL 找不到 {p}")
        return 2
    s = read(p)
    patched = MARK in s
    has_call = CALL.strip() in s
    bak = p.with_suffix(p.suffix + ".bak")
    print(f"proxy   : {p}")
    print(f"sha256  : {sha(p)}  ({p.stat().st_size} B)")
    print(f"patched : {'YES' if patched else 'no'}   call-site: {'YES' if has_call else 'no'}")
    print(f"backup  : {bak.name if bak.exists() else '(none)'}")
    if patched and not has_call:
        print("WARN 只找到钩子定义、没找到调用点 —— 补丁不完整，建议 unpatch 后重打")
    return 0


def cmd_patch(a) -> int:
    p = pathlib.Path(a.proxy)
    if not p.exists():
        print(f"FAIL 找不到 {p}")
        return 2
    s = read(p)
    if MARK in s:
        print("已打过补丁（幂等）。要重来先 unpatch。")
        return 0
    if ANCHOR not in s:
        print("FAIL 没找到插入点（代理版本不同？）。插入点需要这段：")
        print(ANCHOR.rstrip())
        print("拒绝改动。请把这段贴给我，我按你的版本改。")
        return 3
    bak = p.with_suffix(p.suffix + ".bak")
    if not bak.exists():
        shutil.copy2(p, bak)
        print(f"备份 -> {bak.name}")
    out = s.replace(ANCHOR, ANCHOR + CALL, 1)
    out = out.rstrip("\n") + "\n" + HELPER.format(mark=MARK) + "\n"
    write(p, out)
    print(f"已打补丁：{p}")
    print("开关（环境变量）：")
    print('  PowerShell: $env:HD2_GWE_DUMP="D:\\mod\\out\\gwe"; $env:HD2_GWE_PATHS="/api/WarSeason/GalacticWarEffects"')
    print("  bash      : export HD2_GWE_DUMP=/d/mod/out/gwe")
    print("然后按原方式启动代理、进一次游戏，看 out/gwe/index.txt")
    return 0


def cmd_unpatch(a) -> int:
    p = pathlib.Path(a.proxy)
    bak = p.with_suffix(p.suffix + ".bak")
    if not p.exists():
        print(f"FAIL 找不到 {p}")
        return 2
    if MARK not in read(p):
        print("未打过补丁，无需还原。")
        return 0
    if bak.exists():
        shutil.copy2(bak, p)
        print(f"已从 {bak.name} 还原（sha256 {sha(p)}）")
        return 0
    # 没有备份时按标记删除（保守：只删我们加的那两段）
    s = read(p)
    s = s.replace(CALL, "", 1)
    s = re.sub(r"\n# ---- " + MARK + r" :.*?# ---- /" + MARK + r" ----\n", "\n", s, flags=re.S)
    write(p, s)
    print("没有 .bak，已按标记删除补丁段（请自行复核 diff）。")
    return 0


def cmd_selftest(a) -> int:
    """离线自检：复制一份真代理 → 打补丁 → 编译 → 导入 → 调钩子 → 验落盘。"""
    src = pathlib.Path(a.proxy)
    if not src.exists():
        print(f"FAIL 找不到 {src}")
        return 2
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="gwe_patch_"))
    dst = tmp / src.name
    shutil.copy2(src, dst)
    print(f"[1] 副本 {dst}")
    assert cmd_patch(argparse.Namespace(proxy=str(dst))) == 0
    out = read(dst)
    checks = {
        "钩子定义已插入": HELPER.split("\n")[1].strip() in out or "_gwe_capture_dump(path, body, hdrs)" in out,
        "调用点在 chunked 之后": CALL.strip() in out,
        "标记存在": MARK in out,
    }
    for k, v in checks.items():
        print(f"[2] {'PASS' if v else 'FAIL'} {k}")
        if not v:
            return 4

    r = subprocess.run([sys.executable, "-m", "py_compile", str(dst)], capture_output=True, text=True)
    print(f"[3] {'PASS' if r.returncode == 0 else 'FAIL'} py_compile {r.stderr.strip()[:200]}")
    if r.returncode:
        return 5

    r = subprocess.run([sys.executable, str(dst), "--help"], capture_output=True, text=True, timeout=60)
    print(f"[4] {'PASS' if r.returncode == 0 else 'FAIL'} --help 仍可用（argparse 未被破坏）")
    if r.returncode:
        print(r.stderr[-400:])
        return 6

    sys.path.insert(0, str(tmp))
    sys.modules.pop(dst.stem, None)
    mod = __import__(dst.stem)
    dumpdir = tmp / "dumps"

    body = json.dumps([{"id": 1, "effectType": 71, "values": [1, 2]}]).encode()
    gz = __import__("gzip").compress(body)
    os.environ["HD2_GWE_DUMP"] = str(dumpdir)
    os.environ.pop("HD2_GWE_PATHS", None)
    mod._gwe_capture_dump("/api/WarSeason/GalacticWarEffects", gz, {"content-encoding": "gzip"})
    files = list(dumpdir.glob("*.json")) if dumpdir.exists() else []
    ok = len(files) == 1 and files[0].read_bytes() == body
    print(f"[5] {'PASS' if ok else 'FAIL'} gzip 响应体落盘（{len(files)} 个文件，内容一致={ok}）")
    if not ok:
        return 7
    idx = (dumpdir / "index.txt").read_text(encoding="utf-8").strip().split("\t")
    print(f"[6] index 行：{idx[1]} {idx[2]}B {idx[4]}（字段数 {len(idx)}，应为 5=无 header 泄漏）")
    if len(idx) != 5:
        return 8

    mod._gwe_capture_dump("/api/lobby", body, {})
    print("[7] PASS 非白名单路径不落盘（%d 个文件）" % len(list(dumpdir.glob("*.json"))))

    os.environ["HD2_GWE_DUMP"] = str(tmp / "nope" / "deeper")
    mod._gwe_capture_dump("/api/WarSeason/GalacticWarEffects", b"x" * 16, {})
    print("[8] PASS 目录不存在时自动建（%s）" % (os.environ["HD2_GWE_DUMP"]))

    os.environ["HD2_GWE_DUMP"] = str(tmp / "cap")
    os.environ["HD2_GWE_MAX"] = "8"
    mod._gwe_capture_dump("/api/WarSeason/GalacticWarEffects", b"y" * 4096, {})
    n = len(list((tmp / "cap").glob("*.json"))) if (tmp / "cap").exists() else 0
    print(f"[9] {'PASS' if n == 0 else 'FAIL'} 超上限不落盘（{n} 个文件）")
    os.environ.pop("HD2_GWE_MAX", None)

    os.environ.pop("HD2_GWE_DUMP", None)
    mod._gwe_capture_dump("/api/WarSeason/GalacticWarEffects", b"{}", {})
    print("[10] PASS 未设开关时完全静默（不影响原代理）")

    print(f"\n临时目录：{tmp}")
    print("RESULT=PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("status", cmd_status), ("patch", cmd_patch), ("unpatch", cmd_unpatch)):
        s = sub.add_parser(name)
        s.add_argument("--proxy", required=True, help="variant_mod/tools/war_proxy.py 的路径")
        s.set_defaults(func=fn)
    s = sub.add_parser("selftest", help="离线自检（在临时副本上打补丁，不动真文件）")
    s.add_argument("--proxy", default=r"D:/Downloads/variant_mod/tools/war_proxy.py")
    s.set_defaults(func=cmd_selftest)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
