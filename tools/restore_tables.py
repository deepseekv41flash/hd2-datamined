#!/usr/bin/env python3
"""restore_tables.py — 把被改过的 dl_bin 恢复成基线明文，并建立「原版基线」目录。

做三件事：
  1. 对 `data/game/*.dl_bin` 逐个解密，和 `refs/dlbin/plaintext-<build>/` 的基线明文比 sha256；
  2. 被改过的文件先备份到 `refs/dlbin/modded-<tag>/`，再用基线明文**重新封装**写回（内容 = 原版）；
  3. 建立 `refs/dlbin/baseline-<build>/`：未被改过的表直接复制 Steam 原文件，被改过的表存
     「基线明文重新封装」的 sealed 文件，并写 manifest.json（sealed/plaintext 双 sha256 + 来源）。

注意：重新封装过的文件与 Steam 原文件**字节不同、明文相同**（引擎校验的是明文哈希），
      所以「基线」以 manifest 里的 plaintext sha256 为准。

用法：
    python tools/restore_tables.py --build 26251122            # 只审计，不改
    python tools/restore_tables.py --build 26251122 --write    # 恢复 + 建基线
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

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

GAME = pathlib.Path(r"D:\SteamLibrary\steamapps\common\Helldivers 2\data\game")
REFS = pathlib.Path(r"D:\mod\refs\dlbin")
SK = pathlib.Path(r"D:\mod\refs\dlbin\keys\recipient.sk")
PK = pathlib.Path(r"D:\mod\refs\dlbin\keys\recipient.pk")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", required=True)
    ap.add_argument("--write", action="store_true", help="真正执行恢复与建基线")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    tag = args.tag or time.strftime("%Y%m%d-%H%M%S")

    from nacl.public import PrivateKey, PublicKey, SealedBox
    opener = SealedBox(PrivateKey(SK.read_bytes()))
    sealer = SealedBox(PublicKey(PK.read_bytes()))

    plain_dir = REFS / f"plaintext-{args.build}"
    if not plain_dir.is_dir():
        print(f"✗ 基线明文目录不存在: {plain_dir}")
        return 1

    base_dir = REFS / f"baseline-{args.build}"
    modded_dir = REFS / f"modded-{tag}"

    files = sorted(GAME.glob("*.dl_bin"))
    same, modified, missing_ref = [], [], []
    for path in files:
        try:
            plain = opener.decrypt(path.read_bytes())
        except Exception as exc:                             # noqa: BLE001
            print(f"  ✗ 解密失败 {path.name}: {str(exc)[:70]}")
            continue
        ref = plain_dir / path.name
        if not ref.exists():
            missing_ref.append(path.name)
            continue
        if sha(plain) == sha(ref.read_bytes()):
            same.append(path.name)
        else:
            modified.append(path.name)

    print(f"表 {len(files)} 个：与基线一致 {len(same)}，被改过 {len(modified)}，无基线 {len(missing_ref)}")
    if missing_ref:
        print("  无基线：" + ", ".join(missing_ref))
    if modified:
        print("  被改过：" + ", ".join(modified))

    if not args.write:
        print("\n（只审计，未改动；加 --write 执行恢复 + 建基线）")
        return 0

    modded_dir.mkdir(parents=True, exist_ok=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"build": args.build, "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "note": "baseline = 原版明文重新封装（字节不同于 Steam 原件，明文相同）", "tables": {}}

    for path in files:
        name = path.name
        ref = plain_dir / name
        if not ref.exists():
            continue
        cur = path.read_bytes()
        cur_plain = opener.decrypt(cur)
        is_same = sha(cur_plain) == sha(ref.read_bytes())
        if is_same:
            target = base_dir / name
            if not target.exists():
                shutil.copy2(path, target)
            manifest["tables"][name] = {"state": "steam-original", "sealed_sha256": sha(cur)}
            continue
        # 被改过：备份当前版本；优先找同目录里「明文等于基线」的 .bak-* 原件
        shutil.copy2(path, modded_dir / name)
        sealed = None
        for cand in sorted(GAME.glob(name + ".bak-*")):
            try:
                if sha(opener.decrypt(cand.read_bytes())) == sha(ref.read_bytes()):
                    sealed = cand.read_bytes()
                    print(f"  用 Steam 原件 {cand.name} 恢复 {name}")
                    break
            except Exception:                                # noqa: BLE001
                continue
        if sealed is None:
            sealed = sealer.encrypt(ref.read_bytes())
        if not args.write:
            continue
        if path.exists():
            path.unlink()
        path.write_bytes(sealed)
        back = opener.decrypt(path.read_bytes())
        ok = sha(back) == sha(ref.read_bytes())
        (base_dir / name).write_bytes(sealed)
        manifest["tables"][name] = {
            "state": "resealed-from-baseline-plaintext",
            "sealed_sha256": sha(sealed),
            "plaintext_sha256": sha(ref.read_bytes()),
            "modded_backup": str(modded_dir / name),
            "writeback_verified": ok,
        }
        print(f"  {'PASS' if ok else 'FAIL'}  恢复 {name}")

    (base_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n基线目录: {base_dir}（{len(manifest['tables'])} 个表 + manifest.json）")
    print(f"改动前版本备份: {modded_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
