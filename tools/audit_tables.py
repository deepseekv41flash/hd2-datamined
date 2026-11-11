#!/usr/bin/env python3
"""audit_tables.py — 对比 data/game/*.dl_bin 与 refs 明文基线，列出被改过的表。

用途：更新前/更新后核对「哪些 dl_bin 被我们改过」，以及恢复原版后确认与基线一致。

用法：
    python tools/audit_tables.py [--refs DIR] [--game DIR] [--json OUT]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

DEFAULT_GAME = pathlib.Path(r"D:\SteamLibrary\steamapps\common\Helldivers 2\data\game")
DEFAULT_REFS = pathlib.Path(r"D:\mod\refs\dlbin\plaintext-26251122")
SK = pathlib.Path(r"D:\mod\refs\dlbin\keys\recipient.sk")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                                    # noqa: BLE001
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=str(DEFAULT_GAME))
    ap.add_argument("--refs", default=str(DEFAULT_REFS))
    ap.add_argument("--json", default="")
    args = ap.parse_args()

    from nacl.public import PrivateKey, SealedBox
    box = SealedBox(PrivateKey(SK.read_bytes()))

    game = pathlib.Path(args.game)
    refs = pathlib.Path(args.refs)
    rows, modified, unknown = [], [], []
    for path in sorted(game.glob("*.dl_bin")):
        name = path.name
        try:
            plain = box.decrypt(path.read_bytes())
            sha = hashlib.sha256(plain).hexdigest()
        except Exception as exc:                             # noqa: BLE001
            rows.append({"file": name, "state": "decrypt-fail", "detail": str(exc)[:80]})
            unknown.append(name)
            continue
        ref = refs / name
        if not ref.exists():
            rows.append({"file": name, "state": "no-ref", "sha256": sha[:16], "size": len(plain)})
            unknown.append(name)
            continue
        want = hashlib.sha256(ref.read_bytes()).hexdigest()
        state = "SAME" if want == sha else "MODIFIED"
        rows.append({"file": name, "state": state, "sha256": sha[:16],
                     "ref": want[:16], "size": len(plain)})
        if state == "MODIFIED":
            modified.append(name)

    for r in rows:
        if r["state"] == "SAME":
            continue
        print(f"  {r['state']:12} {r['file']}")
    print(f"\n总计 {len(rows)} 个表：SAME {sum(1 for r in rows if r['state']=='SAME')}，"
          f"MODIFIED {len(modified)}，未比 {len(unknown)}")
    if modified:
        print("  被改过：" + ", ".join(modified))
    if unknown:
        print("  未比：" + ", ".join(unknown))
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  明细写入 {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
