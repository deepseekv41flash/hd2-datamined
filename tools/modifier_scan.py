#!/usr/bin/env python3
"""modifier_scan.py -- decode `generated_modifier_settings.dl_bin`（modifier 注册表）。

为什么要它
    2026-10-31 找「未发布的爆炸弹幕升级」时发现：`generated_entity_deltas` 里那些只被
    `generated_modifier_settings` 引用的 AddPath（EMS 120mm = `0xAE4D54F6CB8CC350`）不是孤立的 ——
    它们全都挂在这张表里。本表 = 「who → 打哪条补丁」的注册表：
        每行 = { modifier id（u32）, [目标实体哈希数组], [delta AddPath] }
    目标 = 战备的载荷实体（与 `generated_stratagem_settings +0x98` 的 payload 数组同空间），
    delta  = `generated_entity_deltas` 里的 ComponentEntityDeltaStorage 键。

读法（本 build 实测）
    `generated_modifier_settings.dl_bin` = u32 行数 + N × 行容器：
        LDLD | ver=1 | type=0xDCEA3AEF | payload 长度 | ...（24 B 头）| payload
    payload = u32 modifier_id + u32(=1) + 若干 (u64 数组偏移, u64 个数) 引用数组。
    常见 3 组：固定组（偏移 0x18）、**目标实体数组**、**delta AddPath 数组（1 个）**；
    200 B 的那行有 7 组（多目标多补丁），语义 ⚠ 未解，工具只打印原始数组。

输出
    modifier 行 → 目标战备（用 stratagem_settings 的 payload 实体反查 id/名字）→ delta 补丁
    （组件/偏移/值；`BombardmentComponentData +0x40` 会解成弹种表，并标注弹种是否带火）。

只读；不解封游戏目录、不启动游戏。
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ref_scan as R                      # noqa: E402
import stratagem_extra as S               # noqa: E402

BOMBARDMENT_COMP = 196
LOADOUT_PKG_COMP = 28
COMP_NAMES = {BOMBARDMENT_COMP: "BombardmentComponentData",
              LOADOUT_PKG_COMP: "LoadoutPackageComponentData"}


# ---------------------------------------------------------------- 基础读取
def modifier_rows(plain: pathlib.Path):
    data = (plain / "generated_modifier_settings.dl_bin").read_bytes()
    n = struct.unpack_from("<I", data, 0)[0]
    off, out = 4, []
    for i in range(n):
        if data[off:off + 4] != b"LDLD":
            raise SystemExit(f"✗ 行 {i} 头不是 LDLD @{off:#x}")
        ver, gid, size, _typ, _u = struct.unpack_from("<IIIII", data, off + 4)
        payload = data[off + 24: off + 24 + size]
        off += 24 + size
        pairs = []
        p = 8
        while p + 16 <= size:
            a, b = struct.unpack_from("<QQ", payload, p)
            if not (8 <= a < size and a % 8 == 0 and 0 < b <= 64):
                break
            pairs.append((a, b))
            p += 16
        out.append({"i": i, "size": size, "payload": payload, "pairs": pairs})
    return out


def stratagem_payloads(plain: pathlib.Path):
    """payload 实体哈希 -> (stratagem id, 显示名)。"""
    data = (plain / "generated_stratagem_settings.dl_bin").read_bytes()
    groups = S.groups(data)
    rows = []
    for g in groups:
        p = g["payload"]
        if len(p) < 16 or struct.unpack_from("<Q", p, 0)[0] != 0x10:
            continue
        cnt = struct.unpack_from("<Q", p, 8)[0]
        for i in range(cnt):
            r = 16 + i * S.STRIDE
            rows.append((p, p[r:r + S.STRIDE]))
    out = {}
    for k, (p, row) in enumerate(rows):
        sid = struct.unpack_from("<I", row, 0)[0]
        off = struct.unpack_from("<Q", row, 0x98)[0]
        cnt = struct.unpack_from("<Q", row, 0xA0)[0]
        label = ""
        try:
            import json
            nm = json.load(open(r"D:\mod\refs\stratagem-display-names.json", encoding="utf-8"))
            nr = nm.get("rows", [])
            if k < len(nr):
                label = nr[k].get("display_name") or nr[k].get("internal_name") or ""
        except Exception:                                          # noqa: BLE001
            pass
        if 0 < off < len(p) - 8:
            for j in range(cnt):
                h = struct.unpack_from("<Q", p, off + 8 * j)[0]
                if h:
                    out.setdefault(h, (sid, label))
    return out


def projectile_table(repo: pathlib.Path):
    rows = list(csv.reader(open(repo / "refs" / "exports" / "projectile_settings.csv",
                                encoding="utf-8")))
    hdr = rows[0]
    i0, i144 = hdr.index("+0"), hdr.index("+144")
    proj = {}
    for r in rows[1:]:
        tok = r[i0].split("/")[0].strip()
        if not tok.lower().startswith("0x"):
            continue
        t = int(tok, 16)
        tok2 = r[i144].split("/")[0].strip()
        proj[t] = int(tok2, 16) if tok2.lower().startswith("0x") else 0
    return proj


def fire_explosions(repo: pathlib.Path):
    rows = list(csv.reader(open(repo / "refs" / "exports" / "explosion_settings.csv",
                                encoding="utf-8")))
    hdr = rows[0]
    i0, i96 = hdr.index("+0"), hdr.index("+96")
    out = {}
    for r in rows[1:]:
        tok = r[i0].split("/")[0].strip()
        if not tok.lower().startswith("0x"):
            continue
        t = int(tok, 16)
        tok2 = r[i96].split("/")[0].strip()
        f = int(tok2, 16) if tok2.lower().startswith("0x") else 0
        if f:
            out[t] = f
    return out


def decode(patch: dict) -> str:
    b, s = patch["bytes"], patch["size"]
    if s == 4:
        u = struct.unpack("<I", b)[0]
        f = struct.unpack("<f", b)[0]
        return f"{u} (f32={f:.4g})"
    if s == 8:
        return f"0x{struct.unpack('<Q', b)[0]:016X}"
    return f"{s} B {b.hex()}"


def main() -> int:
    ap = argparse.ArgumentParser(description="解 modifier 注册表 → 目标战备 → delta 补丁")
    ap.add_argument("--plain", default=str(R.PLAIN))
    ap.add_argument("--repo", default=str(HERE.parent))
    a = ap.parse_args()
    plain = pathlib.Path(a.plain)
    repo = pathlib.Path(a.repo)

    store = R.load_delta_store(plain / "generated_entity_deltas.dl_bin")
    payloads = stratagem_payloads(plain)
    proj = projectile_table(repo)
    fire = fire_explosions(repo)
    mods = modifier_rows(plain)
    print(f"modifier 行 {len(mods)}；delta store {len(store['hashmap'])} 个 AddPath；"
          f"战备载荷实体 {len(payloads)} 个")

    for m in mods:
        pl = m["payload"]
        mid = struct.unpack_from("<I", pl, 0)[0]
        print(f"\n=== modifier {m['i']}  id=0x{mid:08X}  payload {m['size']} B  "
              f"引用数组 {len(m['pairs'])} 组 ===")
        if len(m["pairs"]) != 3:
            for off, cnt in m["pairs"]:
                vals = [hex(struct.unpack_from("<Q", pl, off + 8 * k)[0]) for k in range(min(cnt, 12))]
                print(f"   [{cnt:>2} @+0x{off:02X}] {vals}")
            print("   ⚠ 多引用数组行（语义未解），跳过补丁解码")
            continue
        t_off, t_cnt = m["pairs"][1]
        d_off, d_cnt = m["pairs"][2]
        targets = [struct.unpack_from("<Q", pl, t_off + 8 * k)[0] for k in range(t_cnt)]
        delta = struct.unpack_from("<Q", pl, d_off)[0]
        for h in targets:
            sid, label = payloads.get(h, (None, ""))
            tail = f" -> 战备 id {sid} {label!r}" if sid is not None else " -> 载荷实体不在战备表（悬空/未发布）"
            print(f"   目标 0x{h:016X}{tail}")
        if delta not in store["hashmap"]:
            print(f"   delta AddPath 0x{delta:016X} ✗ 不在 delta store")
            continue
        print(f"   delta AddPath 0x{delta:016X}")
        for p in R.delta_patches(store, delta):
            comp = f"{p['component']} {COMP_NAMES.get(p['component'], '?')}"
            line = f"     comp {comp:<34} +0x{p['member']:03X} size {p['size']:<3} = "
            if p["component"] == BOMBARDMENT_COMP and p["member"] == 0x40 and p["size"] == 32:
                types = struct.unpack("<8I", p["bytes"])
                shown = []
                for t in types:
                    if t == 0:
                        break
                    exp = proj.get(t, 0)
                    f = fire.get(exp)
                    shown.append(f"{t}(exp {exp}" + (f", FIRE={f}" if f else "") + ")")
                line += "[" + " ".join(shown) + "]"
            else:
                line += decode(p)
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
