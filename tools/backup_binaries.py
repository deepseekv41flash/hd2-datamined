#!/usr/bin/env python3
"""backup_binaries.py — 备份「非资源类」安装文件（game.dll / exe / 关键 dll / typelib）作为基线。

资源类（`data/game/*.dl_bin`）由 restore_tables.py 的 baseline-<build> 负责；
本工具只收 executable / library / typelib，并写 manifest（sha256 + 大小 + mtime）。

刻意排除：`libxess.dll`(78 MB) / `nvngx_dlss.dll`(55 MB) / `amd_fidelityfx_*`(22 MB)
——第三方 GPU 库，与逆向无关，白占 155 MB。

用法：
    python tools/backup_binaries.py --build 26251122            # 预览
    python tools/backup_binaries.py --build 26251122 --write    # 真备份
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import shutil
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

GAME = pathlib.Path(r"D:\SteamLibrary\steamapps\common\Helldivers 2")
OUT_ROOT = pathlib.Path(r"D:\mod\refs")

INCLUDE = [
    # 核心逆向目标
    "data/game/game.dll",
    "data/game/dl_library.dl_typelib",
    # 主程序与运行时
    "bin/helldivers2.exe",
    "start_protected_game.exe",
    "bin/runtime.dll",
    "bin/EOSSDK-Win64-Shipping.dll",
    "bin/plugins/level_generation_pluginw64_release.dll",
    "bin/plugins/wwise_pluginw64_release.dll",
    # 小体积但有用的依赖
    "bin/preloader.dll",
    "bin/steam_api64.dll",
    "bin/PlayFabMultiplayerWin.dll",
    "bin/PartyWin.dll",
    "bin/libcurl.dll",
    "bin/bink2w64.dll",
    "bin/dstorage.dll",
    "bin/dstoragecore.dll",
    "bin/crs-client.dll",
    "bin/crs-handler.exe",
    "bin/WinPixEventRuntime.dll",
]


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    out = OUT_ROOT / f"bin-baseline-{args.build}"

    rows, total = [], 0
    for rel in INCLUDE:
        src = GAME / rel
        if not src.exists():
            print(f"  ✗ 缺失 {rel}")
            continue
        size = src.stat().st_size
        total += size
        digest = sha256(src)
        rel_out = pathlib.Path(rel).name if rel.startswith("bin/") else str(pathlib.Path(rel))
        rows.append({"source": rel, "out": rel_out, "size": size, "sha256": digest,
                     "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(src.stat().st_mtime))})
        print(f"  {size:>12,}  {rel}  {digest[:16]}")

    print(f"\n共 {len(rows)} 个文件，{total/1048576:.1f} MiB → {out}")
    if not args.write:
        print("（预览；加 --write 执行）")
        return 0

    out.mkdir(parents=True, exist_ok=True)
    for r in rows:
        src = GAME / r["source"]
        dst = out / r["out"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        if sha256(dst) != r["sha256"]:
            print(f"  ✗ 校验失败 {r['out']}")
            return 1
    (out / "manifest.json").write_text(
        json.dumps({"build": args.build, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "game_dir": str(GAME), "files": rows}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("✓ 备份完成并逐个 sha256 校验通过；manifest.json 已写")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
