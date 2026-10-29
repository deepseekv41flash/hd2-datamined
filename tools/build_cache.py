#!/usr/bin/env python3
"""build_cache.py -- 把当前 build 的 55 张表 + 类型库解封成明文缓存，按 buildid 分目录存。

为什么要有这一步
    游戏一更新，`refs/dlbin/plaintext-all/` 里那份缓存就变成了"上一个 build 的副本"。
    继续用它做对照会得出错误的"改了什么"，这轮就踩过：缓存里的
    `customization_passive_bonuses` 是 4992 B，而同一安装的 18:49 全表字典记录是 4016 B ——
    两个来源对不上，最后只能靠字典裁决。

    所以每确认一个新 build，就把明文缓存**按 buildid 另存一份**，以后任何 diff 都有干净的基线。

用法
    python tools/build_cache.py --sk refs/dlbin/keys/recipient.sk
    python tools/build_cache.py --sk <sk> --out refs/dlbin/plaintext-26251122
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import struct

HEADER = 48


def buildid(acf: pathlib.Path) -> str:
    text = acf.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'"buildid"\s+"(\d+)"', text)
    return m.group(1) if m else "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sk", required=True)
    ap.add_argument("--game", default=r"D:\SteamLibrary\steamapps\common\Helldivers 2")
    ap.add_argument("--appmanifest", default=r"D:\SteamLibrary\steamapps\appmanifest_553850.acf")
    ap.add_argument("--out", default=None, help="缺省 refs/dlbin/plaintext-<buildid>")
    a = ap.parse_args()

    from nacl.public import PrivateKey, SealedBox
    box = SealedBox(PrivateKey(pathlib.Path(a.sk).read_bytes().ljust(32, b"\0")[:32]))

    bid = buildid(pathlib.Path(a.appmanifest))
    dest = pathlib.Path(a.out or f"refs/dlbin/plaintext-{bid}")
    dest.mkdir(parents=True, exist_ok=True)

    gamedir = pathlib.Path(a.game) / "data" / "game"
    index, wrote, failed = {}, 0, []
    for path in sorted(gamedir.iterdir()):
        if not path.is_file():
            continue
        if not (path.name.startswith("generated_") or path.name.endswith(".dl_typelib")):
            continue
        raw = path.read_bytes()
        try:
            plain = box.decrypt(raw) if len(raw) > HEADER else raw
        except Exception as exc:                              # noqa: BLE001
            failed.append({"file": path.name, "error": str(exc)[:100]})
            continue
        (dest / path.name).write_bytes(plain)
        index[path.name] = {"sealed_bytes": len(raw), "plain_bytes": len(plain),
                            "sha256": hashlib.sha256(plain).hexdigest()}
        wrote += 1

    (dest / "_index.json").write_text(
        json.dumps({"buildid": bid, "files": index}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"build {bid}: 解封 {wrote} 个文件 -> {dest}"
          + (f"，失败 {len(failed)} 个" if failed else ""))
    for f in failed:
        print(f"  ✗ {f['file']}: {f['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
