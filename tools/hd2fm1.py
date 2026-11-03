#!/usr/bin/env python3
"""hd2fm1.py -- inspect / extract the `HD2FM1` file-mod container used by Chef-style HD2 mods.

What it is
    Some third-party mods ship a *whole settings-file replacement* as a Lua resource payload:
        resource body = u32 length | u32 kind | "HD2FM1" | u32 header_len | header lines | sealed .dl_bin
    Header lines (key=value):
        name=…  version=…  target=data/game/<table>.dl_bin  size=<sealed bytes>
        stock=<len>:<hex fp>          fingerprint of the known stock file (len + first/mid/last 32 B)
        mod=<len>:<hex fp>            fingerprint of the sealed payload shipped here
    The companion "installer" Lua (Chef Shared Loader) scans the mod's resource archives when the game
    EXITS, matches the fingerprints and swaps the named game file (backup + state + log on disk).

usage
    # from an extracted lua resource payload (e.g. srkit extract … -o dir → dir/lua_<ID>.toc.bin)
    python tools/hd2fm1.py show    <payload.bin>
    python tools/hd2fm1.py extract <payload.bin> --out payload.sealed.dl_bin
    # optionally unseal (needs the game's recipient secret key, as recovered in this project)
    python tools/hd2fm1.py extract <payload.bin> --out p.sealed --unseal refs/dlbin/keys/recipient.sk --plain p.plain

Notes
    - The payload itself is already sealed for the game: writing it over data/game/<table>.dl_bin is
      exactly what the installer does, so our plain deploy route (tools/dlbin_deploy.py install --sealed)
      reproduces the mod without Chef/Lua.
    - `stock` fingerprints are of the SEALED stock file (sealing is randomised, so compare by fp, not sha).
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import struct
import subprocess
import sys

MAGIC = b"HD2FM1"


def read_payload(path: pathlib.Path):
    raw = path.read_bytes()
    # lua resource payload: u32 length, u32 kind, body
    if len(raw) >= 8:
        n, kind = struct.unpack_from("<II", raw, 0)
        body = raw[8:8 + n]
    else:
        body, kind = raw, None
    if body[:6] != MAGIC:                       # maybe a raw body was given
        body, kind = raw, None
        if body[:6] != MAGIC:
            raise SystemExit("✗ 不是 HD2FM1 载荷（既不是 lua resource wrapper，也不是裸载荷）")
    hlen = struct.unpack_from("<I", body, 6)[0]
    head = body[10:10 + hlen].decode("utf-8", "replace")
    meta = {}
    for line in head.splitlines():
        k, _, v = line.partition("=")
        if k:
            meta.setdefault(k, []).append(v)
    size = int(meta["size"][0])
    start = 10 + hlen
    sealed = body[start:start + size]
    if len(sealed) != size:
        raise SystemExit(f"✗ 载荷被截断：声明 {size} B，实际 {len(sealed)} B")
    return {"kind": kind, "body_len": n if kind is not None else len(raw), "meta": meta,
            "sealed": sealed, "magic_at": 0}


def fp(b: bytes) -> str:
    m = len(b) // 2
    h = lambda x: x.hex().upper()                    # noqa: E731
    return "%d:%s%s%s" % (len(b), h(b[:32]), h(b[m:m + 32]), h(b[-32:]))


def main() -> int:
    ap = argparse.ArgumentParser(description="查看/抽取 Chef 系 mod 的 HD2FM1 文件载荷")
    ap.add_argument("cmd", choices=["show", "extract"])
    ap.add_argument("payload")
    ap.add_argument("--out", default=None, help="extract: 写出的 sealed .dl_bin")
    ap.add_argument("--unseal", default=None, help="extract: recipient.sk，顺便解封")
    ap.add_argument("--plain", default=None, help="extract: 解封输出路径")
    a = ap.parse_args()

    p = read_payload(pathlib.Path(a.payload))
    meta = p["meta"]
    sealed = p["sealed"]
    print(f"kind={p['kind']}  body_len={p['body_len']:,}")
    for k, vals in meta.items():
        for v in vals:
            print(f"  {k:8s} = {v}")
    print(f"  sealed   = {len(sealed):,} B  sha256 {hashlib.sha256(sealed).hexdigest()[:16]}")
    print(f"  fp       = {fp(sealed)}")
    if meta.get("mod") and meta["mod"][0] != fp(sealed):
        print("  ⚠ 自带 mod= 指纹与实测 sealed 指纹不一致（载荷可能被改过）")

    if a.cmd == "show":
        return 0
    if not a.out:
        raise SystemExit("✗ extract 需要 --out")
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(sealed)
    print(f"✓ sealed -> {out}（{len(sealed):,} B）")
    if a.unseal:
        plain = pathlib.Path(a.plain or (str(out) + ".plain"))
        r = subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "dlbin_seal.py"),
                            "open-key", str(out), "--key", a.unseal, "--out", str(plain)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("✗ 解封失败：" + (r.stdout + r.stderr)[-300:])
        data = plain.read_bytes()
        print(f"✓ plain  -> {plain}（{len(data):,} B，sha256 {hashlib.sha256(data).hexdigest()[:16]}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
