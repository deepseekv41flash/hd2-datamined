#!/usr/bin/env python3
"""stratagem_tune.py -- 改战备表里的冷却 / 调用时间 / 次数，**保住内容哈希**。

为什么这条线先开
    `generated_stratagem_settings.dl_bin` 的字段是现在最清楚的一张表：
    `+80` max_uses、`+84` call-in 秒、`+104` cooldown 秒、`+392` 面板格 —— 后三个都和
    wiki 数值对过（34/35 一致），Airburst 的 90/100 差异也被 1.007.200 补丁说明解释掉。
    改完的效果在战备面板上**直接能看见数字**，不用进任务就能验。

哈希怎么保住（和爆炸/伤害表同一套做法）
    明文被 `game.dll` 里烘焙的 MurmurHash64A 校验（seed 0xDEADBEEFABAD1DEA）。改字节后
    必须把哈希解回原值：在一个**语义惰性的 8 字节对齐字**里放校正字。
    战备表每行只有 13 段 ≤7 B 的结构空隙，凑不出 8 字节，所以**拿一整行"未使用"的战备当宿主**：
    本 build 里确有两行名字自带 `(NOT USED)`（`EAGLE. (NOT USED) ADDITIONAL STRAFING RUNS`、
    `EAGLE. (NOT USED) AIR-TO-AIR MISSLES`），它们 cell 与真实战备共用 7 号格、显示名 ID 是死引用，
    不会被面板渲染 —— 整行 400 B 都是惰性区。

门禁（任一条不过就拒绝输出）
    G1 长度不变
    G2 差异 ⊆ 目标行 ∪ 校正字那 8 字节
    G3 重算哈希 == 原始哈希
    G4 目标字段读回等于新值
    G5 宿主行除校正字外一字节未变
    G6 目标行除被改字段外一字节未变
    G7 目标行身份字段（+0 type、+40/+44/+48 本地化 ID）未变

用法
    python tools/stratagem_tune.py --plain refs/dlbin/plaintext-26251122/generated_stratagem_settings.dl_bin \
        --name "380mm HE Barrage" --set cooldown=60 --out out/stratagem_380mm_cd60.plain.dl_bin
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# Windows 控制台默认 GBK，不含 ⚠/✗ —— 不重配会在打印时崩掉
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

from murmur64 import murmur64, padding_word_for_hash            # noqa: E402
from table_dictionary import Dictionary                          # noqa: E402

STRIDE = 400
FIELDS = {"uses": (80, "u32"), "callin": (84, "f32"), "cooldown": (104, "f32")}
IDENTITY = (0, 40, 44, 48, 52, 56)          # type enum + 五个本地化 ID：不许动


def groups(plain: bytes, dic: Dictionary) -> list[dict]:
    """`LDLD` 组：数组型组头 `u64 0x10 | u64 count`，行起点 = payload+16。"""
    out, start = [], 0
    while True:
        at = plain.find(b"LDLD", start)
        if at < 0:
            return out
        start = at + 4
        if at + 24 > len(plain):
            continue
        version, type_id, payload, _wide = struct.unpack_from("<IIII", plain, at + 4)
        if version not in (1, 2) or payload <= 0 or at + 24 + payload > len(plain):
            continue
        marker, count = struct.unpack_from("<QQ", plain, at + 24)
        if marker != 16 or count == 0:
            continue
        try:
            _elem, stride = dic.element_of(type_id)
        except Exception:                                          # noqa: BLE001
            continue
        if stride != STRIDE or 16 + count * STRIDE > payload:
            continue
        out.append({"at": at, "payload_at": at + 24, "count": count,
                    "rows_at": at + 24 + 16, "payload": payload})


def row_name(plain: bytes, group: dict, row_at: int) -> str:
    target = struct.unpack_from("<Q", plain, row_at + 16)[0]
    if not 0 < target < group["payload"]:
        return ""
    at = group["payload_at"] + target
    end = plain.find(b"\0", at, at + 250)
    if end <= at:
        return ""
    try:
        return plain[at:end].decode("ascii")
    except UnicodeDecodeError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="战备表字段写入（保内容哈希）")
    ap.add_argument("--plain", required=True, help="明文 .dl_bin（缓存或解封后的）")
    ap.add_argument("--name", default="", help="按内部名子串找行，如 '380mm HE Barrage'")
    ap.add_argument("--type", type=lambda v: int(v, 0), default=None, help="按 +0 type 枚举找行")
    ap.add_argument("--set", action="append", default=[],
                    help="字段=值，字段取 uses / callin / cooldown，可重复")
    ap.add_argument("--set-type", type=lambda v: int(v, 0), default=None,
                    help="【边界实验】把目标行的 +0 type 改成这个值。它同时是身份字段，"
                         "G7 会相应放宽并单独报告「是否制造了重复 key」")
    ap.add_argument("--host-mode", choices=["tail", "row"], default="tail",
                    help="校正字放哪。tail（默认）= 在最后一组 payload 末尾加 8 字节零区当宿主，"
                         "**不碰任何记录**；row = 借用一条 '(NOT USED)' 行的开头 8 字节"
                         "（⚠ 那 8 字节正是该行的 +0 type 与 +4 name_id，实机已验证会崩）")
    ap.add_argument("--host-name", default="NOT USED",
                    help="校正字宿主行的内部名子串（默认用 '(NOT USED)' 的行）")
    ap.add_argument("--edit", action="append", default=[],
                    help="多目标写法，可重复：'内部名子串::字段=值'，如 "
                         "\"EAGLE. REARM::cooldown=5\"。一次封装改多行（哈希锚点仍是"
                         "原始明文，串两次会失效）；给了 --edit 就忽略 --name/--set")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if not a.set and not a.edit and a.set_type is None:
        raise SystemExit("✗ --set / --edit / --set-type 至少给一个")
    if a.edit and (a.set or a.set_type is not None):
        raise SystemExit("✗ --edit 不能和 --set / --set-type 混用")
    data = pathlib.Path(a.plain).read_bytes()
    # typelib 路径允许跟明文同目录
    typelib = pathlib.Path(a.plain).with_name("dl_library.dl_typelib")
    if not typelib.is_file():
        raise SystemExit(f"✗ 找不到 typelib（{typelib}），它应与明文在同一目录")
    dic = Dictionary(typelib.read_bytes(), {})

    gs = groups(data, dic)
    if not gs:
        raise SystemExit("✗ 一个战备组都没解析出来")
    rows = []
    for gi, g in enumerate(gs):
        for r in range(g["count"]):
            at = g["rows_at"] + r * STRIDE
            rows.append({"group": gi, "row": r, "at": at,
                         "type": struct.unpack_from("<I", data, at)[0],
                         "name": row_name(data, g, at)})
    print(f"明文 {len(data):,} B  组 {len(gs)}  行 {len(rows)}")

    # ---- 找目标行（--edit 支持多目标）----
    def pick(needle: str):
        """精确名优先，否则子串。'EAGLE. AIRSTRIKE' 若按子串会连
        'EAGLE. AIRSTRIKE SMOKE' 一起命中，精确名可以把它区分开。"""
        n = needle.strip().lower()
        exact = [x for x in rows if x["name"].lower() == n]
        if exact:
            return exact
        return [x for x in rows if n and n in x["name"].lower()]

    def resolve(cands, what):
        if len(cands) != 1:
            print(f"✗ 目标不唯一（{what}）：命中 {len(cands)} 行 -> "
                  f"{[x['name'] for x in cands][:5]}")
            return None
        x = cands[0]
        print(f"目标：组{x['group']} 行{x['row']} type={x['type']:#x} {x['name']!r}")
        return x

    def parse_field(spec):
        if "=" not in spec:
            print(f"✗ 需要 字段=值，收到 {spec!r}")
            return None
        f, v = spec.split("=", 1)
        f = f.strip()
        if f not in FIELDS:
            print(f"✗ 未知字段 {f!r}，可选 {list(FIELDS)}")
            return None
        return (f, v.strip())

    targets = []                     # [(row, [(field, raw_value)])]
    if a.edit:
        for spec in a.edit:
            if "::" not in spec:
                print(f"✗ --edit 需要 '名字::字段=值'，收到 {spec!r}")
                return 2
            nm, fv = spec.split("::", 1)
            row = resolve(pick(nm), nm)
            if row is None:
                return 2
            fld = parse_field(fv)
            if fld is None:
                return 2
            slot = next((t for t in targets if t[0]["at"] == row["at"]), None)
            if slot is None:
                targets.append((row, [fld]))
            else:
                slot[1].append(fld)
    else:
        if a.type is not None:
            cands = [x for x in rows if x["type"] == a.type]
        else:
            cands = pick(a.name)
        row = resolve(cands, a.name or str(a.type))
        if row is None:
            return 2
        specs = []
        for s in a.set:
            fld = parse_field(s)
            if fld is None:
                return 2
            specs.append(fld)
        targets.append((row, specs))
    target = targets[0][0]           # 兼容 --set-type / 宿主选择
    target_rows = [t[0] for t in targets]

    if a.set_type is not None:
        before_types = collections.Counter(x["type"] for x in rows)
        print(f"现有 {len(before_types)} 个不同 +0 type（{len(rows)} 行）")
        if a.set_type in before_types:
            print(f"⚠ 新 type {a.set_type:#04x} 已存在 {before_types[a.set_type]} 行 "
                  f"⇒ 这次改动会**制造重复 key**")

    # ---- 校正字宿主 ----
    # ⚠ 实机教训（2026-10-22 23:5x）：row 模式的 word_at 落在宿主行**开头**，
    #   而那 8 字节正是该行的 `+0` type 和 `+4` name_id —— 写进去就把主键改成了随机值，
    #   引擎在读表时崩在 game.dll+0x1083a45。所以默认改用 tail。
    host_start = None
    if a.host_mode == "tail":
        if len(data) % 8:
            print(f"✗ 明文长度 {len(data)} 不是 8 的倍数，尾部宿主无法对齐")
            return 2
        word_at = len(data)                        # 追加区紧接文件末尾
        print(f"宿主：最后一组 payload 末尾追加 8 字节零区 @ {word_at}（不碰任何记录）")
    else:
        hosts = [x for x in rows if a.host_name.lower() in x["name"].lower()
                 and x["at"] != target["at"]]
        if not hosts:
            print(f"✗ 找不到宿主行（名字含 {a.host_name!r}）")
            return 2
        host = hosts[-1]
        host_start = host["at"]
        word_at = (host_start + 7) // 8 * 8        # 宿主行内第一个 8 对齐字
        if not (host_start <= word_at <= host_start + STRIDE - 8):
            print("✗ 宿主行内找不到 8 对齐字")
            return 2
        print(f"宿主：组{host['group']} 行{host['row']} {host['name']!r}  校正字 @ {word_at}")

    h0 = murmur64(data)
    print(f"原始哈希 0x{h0:016X}")

    edited = bytearray(data)
    touched = []                     # [(row, off, field, old, new)]
    for row, specs in targets:
        for field, value in specs:
            off, kind = FIELDS[field]
            at = row["at"] + off
            if kind == "u32":
                old = struct.unpack_from("<I", edited, at)[0]
                struct.pack_into("<I", edited, at, int(value, 0))
                new = struct.unpack_from("<I", edited, at)[0]
            else:
                old = struct.unpack_from("<f", edited, at)[0]
                struct.pack_into("<f", edited, at, float(value))
                new = struct.unpack_from("<f", edited, at)[0]
            touched.append((row, off, field, old, new))
            print(f"  {row['name']}  {field} +{off}: {old!r} -> {new!r}")

    type_changed = None
    if a.set_type is not None:
        at = target["at"]
        old_type = struct.unpack_from("<I", edited, at)[0]
        struct.pack_into("<I", edited, at, a.set_type & 0xFFFFFFFF)
        type_changed = (old_type, a.set_type)
        print(f"  type +0: {old_type:#04x} -> {a.set_type:#04x}")

    if a.host_mode == "tail":
        # 把 8 个零字节塞进**最后一组**的 payload（不能裸追加到文件尾，
        # 否则容器的 payload 长度字段与实际不符，解析会报"尾部残留"）
        last_at = max(g["at"] for g in gs)
        old_len = struct.unpack_from("<I", edited, last_at + 12)[0]
        struct.pack_into("<I", edited, last_at + 12, old_len + 8)
        edited += bytes(8)

    word = padding_word_for_hash(bytes(edited), word_at, h0)
    edited[word_at:word_at + 8] = word

    checks = []

    def check(name, cond, detail=""):
        checks.append((name, bool(cond), detail))
        print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + detail) if detail else ''}")

    # 允许改动的绝对偏移集合：目标行 + 校正字 8 字节 (+ tail 模式的 payload 尺寸字段)
    expected = set(range(word_at, word_at + 8))
    for tr in target_rows:
        expected |= set(range(tr["at"], tr["at"] + STRIDE))
    if a.host_mode == "tail":
        expected |= set(range(last_at + 12, last_at + 16))
    diff = {i for i in range(len(data)) if data[i] != edited[i]}
    check("G1 长度", len(edited) == len(data) + (8 if a.host_mode == "tail" else 0),
          f"{len(data):,} -> {len(edited):,}")
    check("G2 差异 ⊆ 目标行 ∪ 校正字 (+尺寸字段)", diff <= expected,
          f"diff={len(diff)}  目标行 {len(target_rows)}")
    got = murmur64(bytes(edited))
    check("G3 重算哈希 == 原始哈希", got == h0, f"0x{got:016X}")

    def g4_ok() -> bool:
        for row, o, f, _old, v in touched:
            at = row["at"] + o
            cur = (struct.unpack_from("<I", edited, at)[0] if FIELDS[f][1] == "u32"
                   else struct.unpack_from("<f", edited, at)[0])
            if FIELDS[f][1] == "u32":
                if cur != v:
                    return False
            elif abs(cur - v) > 1e-6:
                return False
        return True

    check("G4 目标字段读回", g4_ok(),
          str([(r["name"], f, v) for r, _o, f, _ov, v in touched]))
    if a.host_mode == "row":
        hs = host_start
        check("G5 宿主行除校正字外未变",
              edited[hs:word_at] == data[hs:word_at]
              and edited[word_at + 8:hs + STRIDE] == data[word_at + 8:hs + STRIDE])
    else:
        # tail：除了目标行、尺寸字段和追加的 8 字节，**任何记录的任何一个字节都不许动**
        def in_a_target(i: int) -> bool:
            return any(tr["at"] <= i < tr["at"] + STRIDE for tr in target_rows)

        untouched = [i for i in range(len(data))
                     if not in_a_target(i)
                     and not (last_at + 12 <= i < last_at + 16)
                     and edited[i] != data[i]]
        check("G5 其它记录一字节未动", not untouched,
              f"越界改动 {[hex(i) for i in untouched[:6]]}")
    # G6：每个目标行内，除了显式改的字段，其余 4 字节槽必须原封不动
    extra = []
    for tr in target_rows:
        offs = {o for r2, o, _f, _ov, _v in touched if r2["at"] == tr["at"]}
        if tr is target and type_changed is not None:
            offs.add(0)                  # type 是显式声明要改的，不算"越界"
        for o in range(0, STRIDE, 4):
            if o in offs:
                continue
            if (edited[tr["at"] + o:tr["at"] + o + 4]
                    != data[tr["at"] + o:tr["at"] + o + 4]):
                extra.append((tr["name"], hex(o)))
    check("G6 目标行其余字段未变", not extra, f"越界改动的偏移 {extra[:6]}")
    if type_changed is None:
        ident_ok = all(
            edited[tr["at"] + o:tr["at"] + o + 4] == data[tr["at"] + o:tr["at"] + o + 4]
            for tr in target_rows for o in IDENTITY)
        check("G7 身份字段未变", ident_ok, f"offsets={IDENTITY}")
    else:
        # 显式声明要改 type：G7 改为「只允许 type 变，五个 locid 槽必须原封不动」
        locids_ok = all(
            edited[target["at"] + o:target["at"] + o + 4]
            == data[target["at"] + o:target["at"] + o + 4] for o in IDENTITY if o != 0)
        check("G7' 只改 type，locid 槽未变", locids_ok,
              f"locid offsets={[o for o in IDENTITY if o != 0]}")
        after_types = collections.Counter(
            struct.unpack_from("<I", edited, x["at"])[0] for x in rows)
        dup_now = sorted(t for t, c in after_types.items() if c > 1)
        check("G8 报告重复 key（只是记录，不是失败）", True,
              f"改动后仍有 {len(after_types)} 个不同 type；重复的 type: "
              f"{[hex(t) for t in dup_now] if dup_now else '无'}")

    if not all(c[1] for c in checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1
    dest = pathlib.Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(bytes(edited))
    print(f"\n✓ 全部门禁通过，明文写入 {dest}（{len(edited):,} B）")
    print("下一步：用 tools/dlbin_seal.py 以 recipient.pk 重新封装，再写入 data/game/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
