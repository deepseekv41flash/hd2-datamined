#!/usr/bin/env python3
"""deploy_region_flat.py — 把改写后的 region_settings 装盘（带备份 / 回读校验 / 回滚说明）。

安全闸门
    G0 游戏进程未运行（文件被占用时 Windows 会拒绝写）
    G1 目标文件先备份成 `generated_region_settings.dl_bin.bak-<tag>`
    G2 写入后立刻用 recipient.sk 解封回读，必须逐字节等于要装的那份明文
    G3 打印回滚命令

用法
    python tools/deploy_region_flat.py --sealed out/terrain/region_flat_h2.sealed.dl_bin \\
        --plain  out/terrain/region_flat_h2.plain.dl_bin --tag terrain-flat-h2
    python tools/deploy_region_flat.py --restore generated_region_settings.dl_bin.bak-terrain-flat-h2
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import shutil
import struct
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass
import time

GAME = pathlib.Path(r"D:\SteamLibrary\steamapps\common\Helldivers 2")
SK = pathlib.Path(r"D:\mod\refs\dlbin\keys\recipient.sk")
DEFAULT_TARGET = "generated_region_settings.dl_bin"


def game_running() -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq helldivers2.exe"],
                             capture_output=True, text=True, timeout=20).stdout
        return "helldivers2.exe" in out.lower()
    except Exception:                                        # noqa: BLE001
        return False


def open_sealed(blob: bytes) -> bytes:
    from nacl.public import PrivateKey, SealedBox
    return SealedBox(PrivateKey(SK.read_bytes())).decrypt(blob)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sealed")
    ap.add_argument("--plain")
    ap.add_argument("--tag", default="terrain-flat")
    ap.add_argument("--target", default=DEFAULT_TARGET, help="data/game 下的文件名")
    ap.add_argument("--restore", help="备份文件名（仅文件名，位于 data/game/）")
    args = ap.parse_args()

    target = GAME / "data" / "game" / args.target

    if game_running():
        print("✗ helldivers2.exe 正在运行 —— 先完全退出游戏")
        return 1

    if args.restore:
        backup = target.parent / args.restore
        if not backup.exists():
            print(f"✗ 备份不存在 {backup}")
            return 1
        cur = target.parent / f"{args.target}.bak-before-restore-{time.strftime('%Y%m%d-%H%M%S')}"
        if target.exists():
            shutil.copy2(target, cur)
        shutil.copy2(backup, target)
        print(f"✓ 已回滚 {backup.name} -> {target.name}")
        print(f"  回滚前那份已存 {cur.name}")
        return 0

    if not args.sealed or not args.plain:
        print("✗ 需要 --sealed 与 --plain（或用 --restore）")
        return 1

    sealed = pathlib.Path(args.sealed)
    plain = pathlib.Path(args.plain)
    if not sealed.exists() or not plain.exists():
        print("✗ 输入文件不存在")
        return 1

    want = plain.read_bytes()
    blob = sealed.read_bytes()
    got = open_sealed(blob)
    if got != want:
        print("✗ 封装解回来 != 目标明文，拒绝装盘")
        return 1
    print(f"  G2 解封校验 PASS  ({len(want):,} B, sha256 {hashlib.sha256(want).hexdigest()[:16]})")

    backup = target.parent / f"{target.name}.bak-{args.tag}"
    if not backup.exists():
        shutil.copy2(target, backup)
        print(f"  G1 备份 {backup.name}  ({backup.stat().st_size:,} B)")
    else:
        print(f"  G1 备份已存在 {backup.name}（保留最早那份）")

    target.write_bytes(blob)
    back = open_sealed(target.read_bytes())
    ok = back == want
    print(f"  G2' 装盘回读 {'PASS' if ok else 'FAIL'}  {target} ({target.stat().st_size:,} B)")
    print(f"\n回滚：python tools/deploy_region_flat.py --target {args.target} --restore {backup.name}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
