#!/usr/bin/env python3
"""res_index.py -- offline lookup over D:\\mod\\index\\all_entries.json (resource id -> package).

Why
    When a swapped attachment / weapon / particle resource has no model in game, the usual
    cause is that the resource's **package is not resident**. Finding the owning package is
    the first step of the "donor package" fix (Reinforce +0xA8 on a stratagem row).

Index format (built once by tools/../index build, 322k entries / 3.4k packages):
    [{"package": "52b63b45c7a6dbac", "file_id": "18429449806859828280",
      "file_id_hex": "0xFFC28EF4B7C57C38", "type_id": "...", "type": "unit",
      "name": "...", "toc_size": 0, "gpu_size": 0, "stream_size": 0, "codec": "..."}]

Usage
    python tools/res_index.py id 0x19FC5C5B031A4AF2        # who owns this resource id
    python tools/res_index.py pkg 52b63b45c7a6dbac         # list a package's entries
    python tools/res_index.py find scope                   # name substring search (units only unless --all)
    python tools/res_index.py find scope --type unit --limit 40
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

INDEX = pathlib.Path(r"D:\mod\index\all_entries.json")

_ENTRY_RE = re.compile(
    r'\{\s*"package":\s*"([0-9a-f]+)",\s*'
    r'"file_id":\s*"(\d+)",\s*'
    r'"file_id_hex":\s*"(0x[0-9A-Fa-f]+)",\s*'
    r'"type_id":\s*"(\d+)",\s*'
    r'"type":\s*"([^"]*)",\s*'
    r'"name":\s*"([^"]*)",'
)


def load(path: pathlib.Path | None = None) -> list[dict]:
    path = path or INDEX
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in _ENTRY_RE.finditer(text):
        pkg, fid, fid_hex, tid, typ, name = m.groups()
        out.append({"package": pkg, "file_id": int(fid), "file_id_hex": fid_hex,
                    "type_id": int(tid), "type": typ, "name": name})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="resource index lookup")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("id", help="resolve a resource id to its package(s)")
    p.add_argument("ids", nargs="+")

    p = sub.add_parser("pkg", help="list entries of a package")
    p.add_argument("package")
    p.add_argument("--type", default=None)

    p = sub.add_parser("find", help="search by name substring")
    p.add_argument("needle")
    p.add_argument("--type", default=None)
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--show-all-types", action="store_true")

    a = ap.parse_args(argv)
    entries = load()
    print(f"index: {len(entries):,} entries, {len({e['package'] for e in entries}):,} packages", file=sys.stderr)

    if a.cmd == "id":
        want = {int(x, 16) & 0xFFFFFFFFFFFFFFFF for x in a.ids}
        hits = collections.defaultdict(list)
        for e in entries:
            if e["file_id"] in want:
                hits[e["file_id"]].append(e)
        for i in sorted(want):
            group = hits.get(i) or []
            if not group:
                print(f"0x{i:016X}: 未在索引里")
                continue
            print(f"0x{i:016X}:")
            for e in group:
                print(f"   package={e['package']}  type={e['type']:<12} name={e['name']}")
        return 0

    if a.cmd == "pkg":
        rows = [e for e in entries if e["package"].lower() == a.package.lower()]
        if a.type:
            rows = [e for e in rows if e["type"] == a.type]
        print(f"package {a.package}: {len(rows)} 条")
        for e in rows:
            print(f"  {e['type']:<12} {e['file_id_hex']}  {e['name']}")
        return 0

    needle = a.needle.lower()
    rows = [e for e in entries if needle in e["name"].lower()]
    if a.type:
        rows = [e for e in rows if e["type"] == a.type]
    print(f"命中 {len(rows)} 条（显示前 {a.limit}）")
    for e in rows[: a.limit]:
        print(f"  {e['package']}  {e['type']:<12} {e['file_id_hex']}  {e['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
