#!/usr/bin/env python3
"""stratagem_repair.py -- 把一条「载荷被删空」的战备行，借一条现役行的载荷 + package 修回来。

为什么需要这个
    本 build 里有几条战备行是**半删状态**：载荷实体已从 `generated_entities.dl_bin` 里删掉，
    同时 `+0xA8 package`（根包）也被清成 0。两者一起没了，引擎拿不到「载荷在哪个包里」。
    实机表现（2026-10-28）：

        id 106 Carpet Bomb  载荷悬空 + package=0 → 能按，投出瞬间**崩溃**
        id 135 Nuke         载荷悬空 + package=0 → 能按，投出后**静默什么都不发生**
        id 127 Reinforce    载荷在、package=0     → 有图标但**按不动**

    社区 2024-06 的历史快照 diff 已经证明：`0x6CCB976676EF6CC6`
    = `unit=shuttle_transport.bones / payload=EaglePayload_CarpetBombing`，**实体整个被删**，
    不是我们读错。

做法（抄 MrChengl11/hd2-lua-mod-skill 的 carpet-bomb 案例第 8 轮，已在该案例实机验证方向正确）
    别用「没人引用」的实体 —— **没人引用 ≠ 能用**，能被生成的实体必须处在**已加载的 package** 里。
    所以从一条**现役战备**（本 build 里正常工作的那条）抄两样东西到坏行上：

        payload 数组内容（`+0x98 {u64 偏移, u32 数量}` 指向的 u64 实体哈希）
        package（`+0xA8`）

    行的其余字段（category / origin / cooldown_type / icon / selectable / uses / cooldown）一律不动。

门禁（与 stratagem_extra.py 同一套）
    G1 长度 = 原长 + 对齐 + 8 · G2 差异 ⊆ 声明字段 ∪ 最后一组尺寸字段 ∪ 校正字
    G3 重算 Murmur64A == 输入哈希 · G4 目标字段读回 · G5 其余字节未动 · G6 容器自洽

用法
    python tools/stratagem_repair.py --plain A.plain --repair 18:106 --out B.plain --seal
    python tools/stratagem_repair.py --plain A.plain --repair 18:106 --repair 121:135 --out B.plain
    python tools/stratagem_repair.py --show            # 列出全部「package=0 或载荷悬空」的行
"""
from __future__ import annotations

import argparse
import os
import re
import pathlib
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "work", "devkit", "tools"))
from murmur64 import murmur64, padding_word_for_hash                 # noqa: E402
from stratagem_extra import load, u32, names_map, label, rebuild, groups, TAIL   # noqa: E402

MOD = pathlib.Path(HERE).resolve().parents[2]      # tools -> repo -> work -> D:/mod
BASE = MOD / "refs/dlbin/plaintext-26088801"
VANILLA = str(BASE / "generated_stratagem_settings.dl_bin")
ENTITIES = BASE / "generated_entities.dl_bin"
PKG_OFF = 0xA8
PAYLOAD_OFF = 0x98


def payload_of(row: bytes, payload: bytes):
    """(哈希数组, 数组在 payload 里的起始偏移, 数量)"""
    off = struct.unpack_from("<Q", row, PAYLOAD_OFF)[0]
    cnt = struct.unpack_from("<I", row, PAYLOAD_OFF + 8)[0]
    if not (0 < cnt <= 64) or not (0 <= off < len(payload) - 8) or off + cnt * 8 > len(payload):
        return [], 0, 0
    return [struct.unpack_from("<Q", payload, off + i * 8)[0] for i in range(cnt)], off, cnt


def status_table(plain: str):
    data, gs, rows = load(plain)
    nm = names_map()
    payloads = {gi: g["payload"] for gi, g in enumerate(gs)}
    ent = ENTITIES.read_bytes()
    out = []
    for k, r in enumerate(rows):
        row = r["row"]
        hs, _off, _cnt = payload_of(row, payloads[r["group"]])
        pkg = struct.unpack_from("<Q", row, PKG_OFF)[0]
        missing = [h for h in hs if ent.count(struct.pack("<Q", h)) == 0]
        if pkg == 0 or missing:
            out.append({"id": u32(row, 0), "name": label(k, nm), "pkg": pkg,
                        "hashes": [f"0x{h:016X}" for h in hs],
                        "missing": [f"0x{h:016X}" for h in missing], "row": r})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="战备行载荷/package 修复（保内容哈希）")
    ap.add_argument("--plain", default=VANILLA)
    ap.add_argument("--repair", action="append", default=[], metavar="DONOR:TARGET")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar="ID:OFF=VALUE",
                    help="顺手改一个 u32 字段，如 --set 135:0x94=0（cooldown_type 2->0）")
    ap.add_argument("--payload", action="append", default=[], metavar="TARGET:SLOT=VALUE",
                    help="直接写某一行的载荷槽，如 --payload 138:0=0x75F7E96AF7DCD303")
    ap.add_argument("--copy-package", action="store_true",
                    help="连 +0xA8 package 一起抄（默认不抄：本 build 里 package=0 的行大多正常工作）")
    ap.add_argument("--seal", action="store_true")
    ap.add_argument("--pk", default=str(MOD / "refs/dlbin/keys/recipient.pk"))
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    if a.show:
        print(f"{'id':>4} {'package':>22}  名字 / 悬空载荷")
        print("-" * 92)
        for rec in status_table(a.plain):
            miss = ("  缺 " + " ".join(rec["missing"])) if rec["missing"] else ""
            print(f"{rec['id']:>4} {('0' if rec['pkg'] == 0 else hex(rec['pkg'])):>22}  "
                  f"{rec['name'][:32]:32}{miss}")
        return 0

    if not a.repair and not a.set and not a.payload:
        raise SystemExit("✗ 要修就用 --repair DONOR:TARGET；只想看用 --show")

    data, gs, rows = load(a.plain)
    payloads = {gi: g["payload"] for gi, g in enumerate(gs)}
    by_id = {}
    for k, r in enumerate(rows):
        by_id.setdefault(u32(r["row"], 0), r)
    nm = names_map()

    pad8 = (8 - len(data) % 8) % 8
    tail_len = pad8 + TAIL
    edited = bytearray(rebuild(data, gs, tail_len))
    allowed = set()
    plan = []
    plan_sets = []
    plan_payload = []

    for spec in a.repair:
        if ":" not in spec:
            raise SystemExit(f"✗ --repair 形如 DONOR:TARGET，收到 {spec!r}")
        dh, th = (int(x, 0) for x in spec.split(":", 1))
        if dh not in by_id or th not in by_id:
            raise SystemExit(f"✗ id 不在表里：donor={dh} target={th}")
        donor, target = by_id[dh], by_id[th]
        dhs, doff, dcnt = payload_of(donor["row"], payloads[donor["group"]])
        ths, toff, tcnt = payload_of(target["row"], payloads[target["group"]])
        if not dhs:
            raise SystemExit(f"✗ donor {dh} 自己也没有载荷数组")
        if tcnt and dcnt > tcnt:
            raise SystemExit(f"✗ donor 有 {dcnt} 个载荷槽、target 只有 {tcnt} 个：不扩容（避免越界）")
        dpkg = struct.unpack_from("<Q", donor["row"], PKG_OFF)[0]
        if dpkg == 0:
            raise SystemExit(f"✗ donor {dh} 自己的 package 也是 0，不能当供体")

        # 载荷哈希：写进 target 自己的数组位置。数组在它所在组的 payload 里（payload 相对偏移 toff），
        # 而 payload 起点 = 组头 g.at + 24。
        tbase = gs[target["group"]]["at"] + 24 + toff
        for i, h in enumerate(dhs[:tcnt]):
            struct.pack_into("<Q", edited, tbase + i * 8, h)
            allowed |= set(range(tbase + i * 8, tbase + i * 8 + 8))
        if a.copy_package:
            pbase = target["abs"] + PKG_OFF
            struct.pack_into("<Q", edited, pbase, dpkg)
            allowed |= set(range(pbase, pbase + 8))
        plan.append((dh, th, dhs, tbase, tcnt, dpkg))

    for spec in a.payload:
        m = re.match(r"^(\d+):(\d+)=(0x[0-9A-Fa-f]+|\d+)$", spec.strip())
        if not m:
            raise SystemExit(f"✗ --payload 形如 TARGET:SLOT=VALUE，收到 {spec!r}")
        sid, slot, val = int(m.group(1)), int(m.group(2)), int(m.group(3), 0)
        if sid not in by_id:
            raise SystemExit(f"✗ id {sid} 不在表里")
        tgt = by_id[sid]
        p = payloads[tgt["group"]]
        off = struct.unpack_from("<Q", tgt["row"], PAYLOAD_OFF)[0]
        cnt = struct.unpack_from("<I", tgt["row"], PAYLOAD_OFF + 8)[0]
        if not (0 <= slot < cnt):
            raise SystemExit(f"✗ id {sid} 只有 {cnt} 个载荷槽，取不到 slot {slot}")
        base = gs[tgt["group"]]["at"] + 24 + off + slot * 8
        oldv = struct.unpack_from("<Q", edited, base)[0]
        struct.pack_into("<Q", edited, base, val)
        allowed |= set(range(base, base + 8))
        plan_payload.append((sid, slot, oldv, val))

    for spec in a.set:
        m = re.match(r"^(\d+):(0x[0-9A-Fa-f]+|\d+)=(-?\d+|0x[0-9A-Fa-f]+)$", spec.strip())
        if not m:
            raise SystemExit(f"✗ --set 形如 ID:OFF=VALUE（off 可写 0x94），收到 {spec!r}")
        sid, off, val = int(m.group(1)), int(m.group(2), 0), int(m.group(3), 0)
        if sid not in by_id:
            raise SystemExit(f"✗ id {sid} 不在表里")
        if not (0 <= off <= 400 - 4) or off % 4:
            raise SystemExit(f"✗ 偏移 {off:#x} 必须是 4 的倍数且在行内")
        base = by_id[sid]["abs"] + off
        wide = val > 0xFFFFFFFF                       # >32 位 → 当 u64 写（如 +0xA8 package）
        n = 8 if wide else 4
        old = struct.unpack_from("<Q" if wide else "<I", edited, base)[0]
        struct.pack_into("<Q" if wide else "<I", edited, base, val & (0xFFFFFFFFFFFFFFFF if wide else 0xFFFFFFFF))
        allowed |= set(range(base, base + n))
        plan_sets.append((sid, off, old, val, wide))

    word_at = len(data) + pad8
    h0 = murmur64(data)
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)
    allowed |= set(range(gs[-1]["at"] + 12, gs[-1]["at"] + 16)) | set(range(word_at, word_at + TAIL))

    diff = {i for i in range(min(len(data), len(edited))) if data[i] != edited[i]}
    ok = True

    def chk(tag, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    print(f"明文 {len(data):,} B → {len(edited):,} B  hash=0x{h0:016X}")
    for sid, slot, old, val in plan_payload:
        print(f"  id {sid} payload[{slot}]: 0x{old:016X} → 0x{val:016X}")
    for sid, off, old, val, wide in plan_sets:
        print(f"  id {sid} +0x{off:02X}: {old} → {val}" + ("  (u64)" if wide else ""))
    for dh, th, dhs, tbase, tcnt, dpkg in plan:
        print(f"  {dh} ({label(next(k for k,r in enumerate(rows) if u32(r['row'],0)==dh), nm)})"
              f" → {th} ({label(next(k for k,r in enumerate(rows) if u32(r['row'],0)==th), nm)})")
        print(f"      payload: {[f'0x{h:016X}' for h in dhs[:tcnt]]}"
              f"{f'   package: 0x{dpkg:016X}' if a.copy_package else '   package: 保持不动'}")
    chk("G1 长度", len(edited) == len(data) + tail_len, f"{len(data):,} -> {len(edited):,}")
    chk("G2 差异集合", diff <= allowed, f"diff={len(diff)}")
    got = murmur64(bytes(edited))
    chk("G3 哈希复原", got == h0, f"0x{got:016X}")
    rb = all(struct.unpack_from("<Q", edited, gs[by_id[sid]["group"]]["at"] + 24
                                + struct.unpack_from("<Q", by_id[sid]["row"], PAYLOAD_OFF)[0] + slot * 8)[0] == val
             for sid, slot, _o, val in plan_payload) and all(
             struct.unpack_from("<Q" if wide else "<I", edited, by_id[sid]["abs"] + off)[0]
             == (val & (0xFFFFFFFFFFFFFFFF if wide else 0xFFFFFFFF))
             for sid, off, _o, val, wide in plan_sets)
    for dh, th, dhs, tbase, tcnt, dpkg in plan:
        t = by_id[th]
        back = [struct.unpack_from("<Q", edited, tbase + i * 8)[0] for i in range(tcnt)]
        okp2 = back == dhs[:tcnt]
        if a.copy_package:
            okp2 = okp2 and struct.unpack_from("<Q", edited, t["abs"] + PKG_OFF)[0] == dpkg
        rb = rb and okp2
    chk("G4 读回", rb)
    chk("G5 其余未动", diff <= allowed)
    try:
        groups(bytes(edited))
        okp = True
    except Exception as exc:                                   # noqa: BLE001
        okp = False
        print("     ", exc)
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


if __name__ == "__main__":
    raise SystemExit(main())
