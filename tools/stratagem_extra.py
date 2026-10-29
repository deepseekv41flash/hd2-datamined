#!/usr/bin/env python3
"""stratagem_extra.py -- 战备表的「额外战备」字段（`+0xC8 additional_stratagem`），保内容哈希。

背景
    原版每套配装最多 4 个战备位，但 `StratagemInfo +0xC8` 是「带上这条战备时**额外附赠**的
    另一条战备」：Eagle 全家都写着 51（`EAGLE. REARM`）。附赠的不占配装位，而且引擎会
    顺着 extras 一路跟下去（**成环会崩**，见 SHODAN-Stat-Editor issue #64 的实测注释）。
    于是把任意现成战备的 +0xC8 指向一条「未发布/想试」的战备，就能在不改配装位的前提下
    把它带进任务（例如 M-104 Incinerator FRV = 战备 id 138）。

判据 / 门禁
    G1 长度 = 原长 + 对齐 + 8 · G2 差异 ⊆ 声明字段 ∪ 最后一组尺寸字段 ∪ 校正字
    G3 重算 Murmur64A == 原值 · G4 目标字段读回 · G5 其余字节未动 · G6 容器自洽
    G7 环检测（host → extra 链不得回到 host；引擎跟环会崩）

用法
    python tools/stratagem_extra.py --show                     # 153 行全表（id / 名字 / 当前 extra）
    python tools/stratagem_extra.py --find FRV                 # 按名字找 id
    python tools/stratagem_extra.py --host 121 --extra 138 --out out/x.plain
    python tools/stratagem_extra.py --host 121 --extra 138 --out out/x.plain --seal --pk refs/dlbin/keys/recipient.pk
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "work", "devkit", "tools"))
from murmur64 import murmur64, padding_word_for_hash            # noqa: E402

VANILLA = r"D:\mod\refs\dlbin\plaintext-26251122\generated_stratagem_settings.dl_bin"
NAMES = r"D:\mod\refs\stratagem-display-names.json"
STRIDE = 400
EXTRA_OFF = 0xC8          # +200 additional_stratagem（SHODAN v4.1.0 源码 MOD.extra.row）
TAIL = 8


def groups(data: bytes):
    """u32 块数 + 每块 `LDLD|ver|id|size|wide|extra`(24) + payload。"""
    n = struct.unpack_from("<I", data, 0)[0]
    off, out = 4, []
    for _ in range(n):
        if data[off:off + 4] != b"LDLD":
            raise SystemExit(f"✗ 块头不是 LDLD @{off:#x}")
        ver, gid, size, typ, unk = struct.unpack_from("<IIIII", data, off + 4)
        out.append({"at": off, "gid": gid, "size": size, "payload": data[off + 24:off + 24 + size]})
        off += 24 + size
    if off != len(data):
        raise SystemExit(f"✗ 尾部残留 {len(data) - off} B")
    return out


def load(path: str):
    data = open(path, "rb").read()
    gs = groups(data)
    rows = []
    for gi, g in enumerate(gs):
        p = g["payload"]
        if len(p) < 16 or struct.unpack_from("<Q", p, 0)[0] != 0x10:
            continue
        cnt = struct.unpack_from("<Q", p, 8)[0]
        for i in range(cnt):
            r = 16 + i * STRIDE
            rows.append({"group": gi, "index": i, "abs": g["at"] + 24 + r, "row": p[r:r + STRIDE]})
    return data, gs, rows


def u32(row: bytes, off: int) -> int:
    return struct.unpack_from("<I", row, off)[0]


def names_map():
    if not os.path.exists(NAMES):
        return {}
    d = json.load(open(NAMES, encoding="utf-8"))
    return {i: r for i, r in enumerate(d.get("rows", []))}


def label(k: int, nm: dict) -> str:
    r = nm.get(k) or {}
    return r.get("display_name") or r.get("internal_name") or f"row#{k}"


def rebuild(data: bytes, gs: list[dict], tail_len: int) -> bytes:
    out = [struct.pack("<I", len(gs))]
    last = len(gs) - 1
    for i, g in enumerate(gs):
        size = g["size"] + (tail_len if i == last else 0)
        out.append(b"LDLD")
        out.append(struct.pack("<IIIII", 1, g["gid"], size, 1, 0))
        out.append(data[g["at"] + 24:g["at"] + 24 + g["size"]])
        if i == last and tail_len:
            out.append(bytes(tail_len))
    return b"".join(out)


def find_extra_of(rows, by_id, sid):
    """sid 的 +0xC8 值（不存在返回 None）。"""
    hit = by_id.get(sid)
    return None if hit is None else u32(hit[1]["row"], EXTRA_OFF)


def main() -> int:
    ap = argparse.ArgumentParser(description="战备表额外战备（+0xC8）写入，保内容哈希")
    ap.add_argument("--plain", default=VANILLA)
    ap.add_argument("--show", action="store_true", help="列出全表：id / 名字 / 当前额外战备")
    ap.add_argument("--find", metavar="NAME", help="按名字子串找 id")
    ap.add_argument("--chain", metavar="HOST:A,B,C",
                    help="一次挂一整条链：HOST 的额外=A、A 的额外=B、B 的额外=C（测试多件时一局看完）")
    ap.add_argument("--host", type=int, help="宿主战备 id（带上它时送额外）")
    ap.add_argument("--host-name", help="宿主战备名字子串（与 --host 二选一）")
    ap.add_argument("--extra", type=int, help="额外战备 id（0 = 清除）")
    ap.add_argument("--extra-name", help="额外战备名字子串")
    ap.add_argument("--out")
    ap.add_argument("--seal", action="store_true")
    ap.add_argument("--pk", default=r"D:\mod\refs\dlbin\keys\recipient.pk")
    a = ap.parse_args()

    data, gs, rows = load(a.plain)
    nm = names_map()
    by_id = {}
    for k, r in enumerate(rows):
        by_id.setdefault(u32(r["row"], 0), (k, r))

    if a.show:
        print(f"{'#':>3} {'id':>4} {'+0xC8':>5} {'extra':<28} host")
        for k, r in enumerate(rows):
            sid = u32(r["row"], 0)
            ex = u32(r["row"], EXTRA_OFF)
            exl = '-' if ex == 0 else (f"{ex} {label(by_id[ex][0], nm)}" if ex in by_id else f"{ex} ?")
            print(f"{k:>3} {sid:>4} {ex:>5} {exl:<28} {label(k, nm)}")
        return 0

    if a.find:
        needle = a.find.lower()
        for k, r in enumerate(rows):
            if needle in label(k, nm).lower():
                print(f"  id={u32(r['row'], 0):>3} row#{k:>3}  {label(k, nm)}")
        return 0

    def resolve(v, name):
        if v is not None:
            return v
        if not name:
            raise SystemExit("✗ 需要 id 或名字")
        needle = name.lower()
        hit = [u32(r["row"], 0) for k, r in enumerate(rows) if needle in label(k, nm).lower()]
        if not hit:
            raise SystemExit(f"✗ 名字子串 {name!r} 没匹配到战备")
        if len(hit) > 1:
            raise SystemExit(f"✗ 名字子串 {name!r} 匹配多行：{hit}，请用 --find 看清后给 id")
        return hit[0]

    if a.chain:
        # --chain 34:119,138 → 34→119→138（链式；一局能带出多件）
        head, _, rest = a.chain.partition(":")
        ids = [int(x, 0) for x in rest.split(",") if x.strip()]
        if not ids:
            raise SystemExit("✗ --chain 形如 HOST:A,B,C")
        first = resolve(int(head, 0), None)
        seq = [first] + [resolve(i, None) for i in ids]
        for i, sid in enumerate(seq):
            if sid not in by_id:
                raise SystemExit(f"✗ 战备 id {sid} 不在表里")
        # 环检测：seq 里不得有重复
        if len(set(seq)) != len(seq):
            raise SystemExit(f"✗ G7 环：链里有重复 id {seq}")
        tgt_list = [(seq[i], seq[i + 1]) for i in range(len(seq) - 1)]
        pad8 = (8 - len(data) % 8) % 8
        tail_len = pad8 + TAIL
        edited = bytearray(rebuild(data, gs, tail_len))
        for host, extra in tgt_list:
            struct.pack_into("<I", edited, by_id[host][1]["abs"] + EXTRA_OFF, extra)
        word_at = len(data) + pad8
        h0 = murmur64(data)
        edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)
        print(f"明文 {len(data):,} B → {len(edited):,} B  hash=0x{h0:016X}")
        for host, extra in tgt_list:
            print(f"  {host} ({label(by_id[host][0], nm)}) +0xC8: {u32(by_id[host][1]['row'], EXTRA_OFF)} → {extra} ({label(by_id[extra][0], nm)})")
        diff = {i for i in range(min(len(data), len(edited))) if data[i] != edited[i]}
        allowed = set()
        for host, _e in tgt_list:
            t0 = by_id[host][1]["abs"] + EXTRA_OFF
            allowed |= set(range(t0, t0 + 4))
        allowed |= set(range(gs[-1]["at"] + 12, gs[-1]["at"] + 16)) | set(range(word_at, word_at + TAIL))
        ok = True
        def chk(tag, cond, detail=""):
            nonlocal ok
            ok = ok and bool(cond)
            print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")
        chk("G1 长度", len(edited) == len(data) + tail_len, f"{len(data):,} -> {len(edited):,}")
        chk("G2 差异集合", diff <= allowed, f"diff={len(diff)}")
        got = murmur64(bytes(edited))
        chk("G3 哈希复原", got == h0, f"0x{got:016X}")
        chk("G4 读回", all(struct.unpack_from("<I", edited, by_id[h][1]["abs"] + EXTRA_OFF)[0] == e for h, e in tgt_list))
        chk("G5 其余未动", diff <= allowed)
        try:
            groups(bytes(edited)); okp = True
        except Exception as exc:                              # noqa: BLE001
            okp = False; print("     ", exc)
        chk("G6 容器自洽", okp)
        if not ok:
            return 1
        if not a.out:
            raise SystemExit("✗ 门禁全过，但缺 --out")
        open(a.out, "wb").write(bytes(edited))
        print(f"✓ 明文 {a.out}")
        if a.seal:
            sealed = a.out[:-6] + ".dl_bin" if a.out.endswith(".plain") else a.out + ".dl_bin"
            subprocess.run([sys.executable, os.path.join(HERE, "dlbin_seal.py"), "seal-key", a.out,
                            "--key", a.pk, "--out", sealed], check=True)
            print(f"✓ 封包 {sealed}")
        return 0

    if a.host is None and not a.host_name:
        raise SystemExit("✗ 要写就用 --host/--host-name；只想看用 --show")
    host = resolve(a.host, a.host_name)
    extra = resolve(a.extra, a.extra_name) if (a.extra is not None or a.extra_name) else None
    if host not in by_id:
        raise SystemExit(f"✗ 宿主战备 id {host} 不在表里")
    if extra is None:
        raise SystemExit("✗ 需要 --extra（0 = 清除）")
    if extra != 0 and extra not in by_id:
        raise SystemExit(f"✗ 额外战备 id {extra} 不在表里")
    if extra == host:
        raise SystemExit("✗ 不能指向自己（引擎会跟环直到崩溃）")

    # G7 环检测：从 extra 顺着 +0xC8 走 64 跳，碰到 host 就拒绝
    seen, t = {extra}, extra
    for _ in range(64):
        nxt = find_extra_of(rows, by_id, t) or 0
        if nxt == 0:
            break
        if nxt == host:
            raise SystemExit(f"✗ G7 环：{host} → {extra} → … → 回到 {host}（引擎跟环会崩）")
        if nxt in seen:
            break
        seen.add(nxt)
        t = nxt

    tgt = by_id[host][1]["abs"] + EXTRA_OFF
    old = struct.unpack_from("<I", data, tgt)[0]
    pad8 = (8 - len(data) % 8) % 8
    tail_len = pad8 + TAIL
    edited = bytearray(rebuild(data, gs, tail_len))
    struct.pack_into("<I", edited, tgt, extra)
    word_at = len(data) + pad8
    h0 = murmur64(data)
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)

    print(f"明文 {len(data):,} B → {len(edited):,} B（对齐 {pad8} + 宿主 {TAIL}）  hash=0x{h0:016X}")
    print(f"  战备 {host} ({label(by_id[host][0], nm)}) +0xC8: {old} → {extra}"
          + (f" ({label(by_id[extra][0], nm)})" if extra else " (清除)"))

    checks = []
    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    diff = {i for i in range(min(len(data), len(edited))) if data[i] != edited[i]}
    allowed = set(range(tgt, tgt + 4)) | set(range(gs[-1]["at"] + 12, gs[-1]["at"] + 16)) | set(range(word_at, word_at + TAIL))
    check("G1 长度 = 原长 + 对齐 + 8", len(edited) == len(data) + tail_len, f"{len(data):,} -> {len(edited):,}")
    check("G2 差异 ⊆ 声明字段 ∪ 尺寸 ∪ 校正字", diff <= allowed, f"diff={len(diff)}")
    got = murmur64(bytes(edited))
    check("G3 重算哈希 == 原始哈希", got == h0, f"0x{got:016X}")
    check("G4 目标字段读回", struct.unpack_from("<I", edited, tgt)[0] == extra, str(extra))
    check("G5 其余字节未动", diff <= allowed)
    try:
        groups(bytes(edited))
        ok = True
    except Exception as exc:                                 # noqa: BLE001
        ok = False
        print(f"      解析失败：{exc}")
    check("G6 容器自洽、无尾部残留", ok)

    if not all(c[1] for c in checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1
    if not a.out:
        raise SystemExit("✗ 门禁全过，但没有 --out")
    out = a.out
    open(out, "wb").write(bytes(edited))
    print(f"✓ 明文 {out}")
    if a.seal:
        sealed = out[:-6] + ".dl_bin" if out.endswith(".plain") else out + ".dl_bin"
        cmd = [sys.executable, os.path.join(HERE, "dlbin_seal.py"), "seal-key", out, "--key", a.pk, "--out", sealed]
        subprocess.run(cmd, check=True)
        print(f"✓ 封包 {sealed} → 装盘：python tools/dlbin_deploy.py install "
              f"--file generated_stratagem_settings.dl_bin --sealed {sealed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
