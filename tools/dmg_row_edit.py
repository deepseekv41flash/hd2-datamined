#!/usr/bin/env python3
"""dmg_row_edit.py -- 伤害行（DamageSettings，76 B）**任意字段**编辑，保住内容哈希。

为什么需要
    `dmg_edit.py` 只会写 `damage / durable`。但真正要改行为时，落在同一行上的还有
    **`element`（+40）** 和 **4 个状态槽（+44 起，每个 = {u32 status_type, f32 value}）** ——
    第三方 Sterilizer-Heal 改的就是这几个（见 docs/cases/RECON-STERILIZER-HEAL-26088801.md）。
    本工具是 dmg_edit 的超集：一次调用可以改任意组合，仍按同一套「空状态槽当校正字」保哈希。

行结构（76 B，本 build 实测 + 第三方 mod 双证）
    +0  u32 type            +4  i32 damage        +8  i32 durable
    +12 u32 ap[4]           +28 u32 demo          +32 u32 force(硬直)
    +36 u32 impulse(推力)   +40 u32 element       +44 4x{u32 type, f32 value}

用法
    # 看一行
    python tools/dmg_row_edit.py show --type 35

    # 列可当哈希宿主的行（带 --refs 时会标出没人引用的）
    python tools/dmg_row_edit.py hosts --refs out/dmgrefs.json

    # 把 TX-41（damage type 35）改成治疗喷流
    python tools/dmg_row_edit.py set --type 35 --damage 0 --durable 0 --element 0 \
        --slot 0:29:1.0 --slot 1:0:0 --host-type 537 --out out/heal.plain \
        --seal --pk D:/mod/refs/dlbin/keys/recipient.pk --sk D:/mod/refs/dlbin/keys/recipient.sk

门禁
    G1 长度不变            G2 差异 ⊆ 声明字段 ∪ 校正字
    G3 重算哈希 == 原值    G4 字段读回 == 目标
    G5 宿主行除校正字外未变 G6 目标行未声明字节未变
    G7 校正字 8 对齐且落在宿主的**空**状态槽里
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash, SEED          # noqa: E402
from dmg_edit import parse_ldld, damage_array, diff_ranges          # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:                                            # noqa: BLE001
        pass


DAMAGE_TYPE = 0xE0A72CF0
STRIDE = 76
OFF_TYPE, OFF_DMG, OFF_DUR = 0, 4, 8
OFF_AP, OFF_DEMO, OFF_FORCE, OFF_IMP, OFF_ELEM = 12, 28, 32, 36, 40
OFF_SLOT = 44
SLOT_SIZE = 8


def read_row(data: bytes, offset: int) -> dict:
    t, dmg, dur = struct.unpack_from('<Iii', data, offset)
    ap = list(struct.unpack_from('<4I', data, offset + OFF_AP))
    demo, force, imp, elem = struct.unpack_from('<4I', data, offset + OFF_DEMO)
    slots = [list(struct.unpack_from('<If', data, offset + OFF_SLOT + SLOT_SIZE * k))
             for k in range(4)]
    return {'type': t, 'damage': dmg, 'durable': dur, 'ap': ap, 'demo': demo,
            'force': force, 'impulse': imp, 'element': elem, 'slots': slots}


def all_rows(data: bytes) -> list[dict]:
    base, count = damage_array(data)
    out = []
    for i in range(count):
        off = base + i * STRIDE
        row = read_row(data, off)
        row['index'] = i
        row['offset'] = off
        out.append(row)
    return out


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for s, e in sorted(ranges):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def covers(needle: tuple[int, int], ranges: list[tuple[int, int]]) -> bool:
    return any(s <= needle[0] and needle[1] <= e for s, e in merge_ranges(ranges))


def field_ranges(row: dict, decl: dict) -> list[tuple[int, int]]:
    """Declared edits -> (start, end) byte ranges inside the container."""
    o = row['offset']
    out = []
    if 'damage' in decl:
        out.append((o + OFF_DMG, o + OFF_DMG + 4))
    if 'durable' in decl:
        out.append((o + OFF_DUR, o + OFF_DUR + 4))
    if 'ap' in decl:
        out.append((o + OFF_AP, o + OFF_AP + 16))
    for key, off in (('demo', OFF_DEMO), ('force', OFF_FORCE),
                     ('impulse', OFF_IMP), ('element', OFF_ELEM)):
        if key in decl:
            out.append((o + off, o + off + 4))
    for slot in sorted(decl.get('slot', {})):
        base = o + OFF_SLOT + SLOT_SIZE * slot
        out.append((base, base + SLOT_SIZE))
    return out


def apply_decl(edited: bytearray, row: dict, decl: dict) -> None:
    o = row['offset']
    if 'damage' in decl:
        struct.pack_into('<i', edited, o + OFF_DMG, decl['damage'])
    if 'durable' in decl:
        struct.pack_into('<i', edited, o + OFF_DUR, decl['durable'])
    if 'ap' in decl:
        struct.pack_into('<4I', edited, o + OFF_AP, *decl['ap'])
    for key, off in (('demo', OFF_DEMO), ('force', OFF_FORCE),
                     ('impulse', OFF_IMP), ('element', OFF_ELEM)):
        if key in decl:
            struct.pack_into('<I', edited, o + off, decl[key])
    for slot, (stype, sval) in decl.get('slot', {}).items():
        base = o + OFF_SLOT + SLOT_SIZE * slot
        struct.pack_into('<If', edited, base, stype, sval)


def empty_aligned_slots(row: dict) -> list[dict]:
    out = []
    for k, (t, v) in enumerate(row['slots']):
        pos = row['offset'] + OFF_SLOT + SLOT_SIZE * k
        if t == 0 and v == 0.0 and pos % 8 == 0:
            out.append({'offset': pos, 'slot': k})
    return out


def covered(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(a <= pos < b for a, b in ranges)


def refs_index(path: pathlib.Path | None) -> dict[int, dict]:
    if not path:
        return {}
    blob = json.loads(path.read_text(encoding='utf-8'))
    out = {}
    for row in blob.get('damage', []):
        out[int(row['type'])] = row
    return out


def cmd_show(args) -> int:
    data = args.plain.read_bytes()
    rows = {r['type']: r for r in all_rows(data)}
    target = rows.get(args.type)
    if target is None:
        print(f'!! no row with DamageInfoType {args.type}')
        return 2
    names = {5: 'Fire', 6: 'Fire_Panic', 68: 'FlamerSlowed', 43: 'Gas', 44: 'Gas',
             45: 'Gas_Confusion', 46: 'Gas_Confusion', 28: 'Stim Heal',
             29: 'Stim Pistol Heal', 26: 'Stim Fx', 27: 'Stim Stamina',
             30: 'Stim Combat Drugs', 31: 'Stim Cooldown'}
    r = target
    print(f'type {r["type"]}  (record {r["index"]}, offset 0x{r["offset"]:X})')
    print(f'  +0x004 damage   {r["damage"]}')
    print(f'  +0x008 durable  {r["durable"]}')
    print(f'  +0x00C ap[4]    {r["ap"]}')
    print(f'  +0x01C demo     {r["demo"]}')
    print(f'  +0x020 force    {r["force"]}')
    print(f'  +0x024 impulse  {r["impulse"]}')
    print(f'  +0x028 element  {r["element"]}')
    for k, (t, v) in enumerate(r['slots']):
        tag = names.get(t, '') if t else ''
        print(f'  slot{k} +0x{OFF_SLOT + SLOT_SIZE * k:03X}  type {t:<4} value {v:<8g} {tag}')
    return 0


def cmd_hosts(args) -> int:
    data = args.plain.read_bytes()
    idx = refs_index(args.refs)
    print('type  idx  empty-slots  referenced_by  damage')
    rows = []
    for r in all_rows(data):
        words = empty_aligned_slots(r)
        if not words:
            continue
        info = idx.get(r['type'])
        refs = None
        if info is not None:
            refs = int(len(info.get('referenced_by_projectile', []))
                       + len(info.get('referenced_by_explosion', [])))
        rows.append((refs if refs is not None else 999, r['type'], r['index'],
                     len(words), refs, r['damage']))
    rows.sort()
    for refs_sort, t, i, nwords, refs, dmg in rows[:40]:
        refs_txt = '—' if refs is None else str(refs)
        print(f'{t:<5} {i:<4} {nwords:<12} {refs_txt:<14} {dmg}')
    print('\n（referenced_by = 0 且 slot 数多者最适合当哈希宿主；未给 --refs 时该列显示 —）')
    return 0


def parse_slot(text: str) -> tuple[int, tuple[int, float]]:
    parts = text.split(':')
    if len(parts) != 3:
        raise argparse.ArgumentTypeError('slot must look like N:TYPE:VALUE, e.g. 0:29:1.0')
    slot = int(parts[0], 0)
    if not 0 <= slot <= 3:
        raise argparse.ArgumentTypeError('slot must be 0..3')
    return slot, (int(parts[1], 0), float(parts[2]))


def cmd_set(args) -> int:
    original = args.plain.read_bytes()
    h0 = murmur64(original)
    print(f'plaintext {args.plain.name}: {len(original):,} B  hash {h0:016X}')

    table = all_rows(original)
    by_type = {r['type']: r for r in table}
    target = by_type.get(args.type)
    if target is None:
        print(f'!! no row with DamageInfoType {args.type}')
        return 2
    host = by_type.get(args.host_type)
    if host is None:
        print(f'!! no row with DamageInfoType {args.host_type}')
        return 2
    if host['index'] == target['index']:
        print('!! host row must differ from the edited row')
        return 2

    decl: dict = {}
    for key in ('damage', 'durable', 'demo', 'force', 'impulse', 'element'):
        val = getattr(args, key)
        if val is not None:
            decl[key] = val
    if args.ap is not None:
        decl['ap'] = [int(x, 0) for x in args.ap.split(',')]
        if len(decl['ap']) != 4:
            print('!! --ap needs 4 comma separated values')
            return 2
    if args.slot:
        decl['slot'] = dict(args.slot)
    if not decl:
        print('!! nothing to change (give at least one field)')
        return 2

    words = empty_aligned_slots(host)
    if not words:
        print(f'!! host row {args.host_type} has no empty 8-byte aligned status slot')
        return 2
    word = words[0]
    # G7 (pre-check): the correction word must live in an EMPTY slot and must not be a
    # declared target range.
    ranges = field_ranges(target, decl)
    if covered(word['offset'], ranges):
        print('!! correction word would land inside the edited ranges; pick another host')
        return 2

    edited = bytearray(original)
    apply_decl(edited, target, decl)

    print(f'target   : type {target["type"]} (record {target["index"]}, 0x{target["offset"]:X})')
    for key, val in decl.items():
        if key == 'slot':
            for s, (t, v) in sorted(val.items()):
                old_t, old_v = target['slots'][s]
                print(f'  slot{s}   {old_t}/{old_v:g}  ->  {t}/{v:g}')
        else:
            old = target[key]
            print(f'  {key:<9}{old}  ->  {val}')
    print(f'host     : type {host["type"]} (record {host["index"]}), '
          f'correction word at 0x{word["offset"]:X} (slot {word["slot"]}, '
          f'{word["offset"] % 8} mod 8)')

    solved = padding_word_for_hash(bytes(edited), word['offset'], h0, SEED)
    struct.pack_into('<Q', edited, word['offset'], struct.unpack('<Q', solved)[0])
    h1 = murmur64(bytes(edited))

    gates = []
    gates.append(('G1 长度不变', len(edited) == len(original)))
    ranges = field_ranges(target, decl)
    w_lo, w_hi = word['offset'], word['offset'] + 8
    bad = [a for a in diff_ranges(original, bytes(edited))
           if not (covers(a, ranges) or (w_lo <= a[0] and a[1] <= w_hi))]
    gates.append(('G2 差异 ⊆ 声明字段 ∪ 校正字', not bad))
    if bad:
        print('    未覆盖差异:', [('0x%X' % s, '0x%X' % e) for s, e in bad])
    gates.append(('G3 重算哈希 == 原值', h1 == h0))
    after = read_row(bytes(edited), target['offset'])
    ok4 = all(after[k] == decl[k] for k in decl if k != 'slot')
    ok4 = ok4 and all(after['slots'][s] == [t, struct.unpack('<f', struct.pack('<f', v))[0]]
                      for s, (t, v) in decl.get('slot', {}).items())
    gates.append(('G4 字段读回 == 目标', ok4))
    host_after = read_row(bytes(edited), host['offset'])
    host_before = host
    hdiff = [(a, b) for a, b in diff_ranges(original, bytes(edited))
             if host['offset'] <= a < host['offset'] + STRIDE]
    gates.append(('G5 宿主行除校正字外未变',
                  all(a[0] >= word['offset'] and a[1] <= word['offset'] + 8 for a in hdiff)))
    tdiff = [(a, b) for a, b in diff_ranges(original, bytes(edited))
             if target['offset'] <= a < target['offset'] + STRIDE]
    gates.append(('G6 目标行未声明字节未变', all(covers(a, ranges) for a in tdiff)))
    gates.append(('G7 校正字落在新宿主空槽（8 对齐）',
                  word['offset'] % 8 == 0
                  and host_before['slots'][word['slot']] == [0, 0.0]))
    for name, ok in gates:
        print(f'  {"PASS" if ok else "FAIL"}  {name}')
    if not all(ok for _, ok in gates):
        return 3

    print(f'\nchanged ranges:')
    for a, b in diff_ranges(original, bytes(edited)):
        print(f'  0x{a:05X}..0x{b:05X} ({b - a} B)  {original[a:b].hex()} -> {edited[a:b].hex()}')

    out = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(edited))
    print(f'\nwrote {out}')

    report = {
        'source': str(args.plain), 'target_type': args.type,
        'target_record': target['index'], 'host_type': args.host_type,
        'original_hash': f'{h0:016X}', 'final_hash': f'{h1:016X}',
        'declared': {k: v for k, v in decl.items() if k != 'slot'},
        'slots': {str(k): v for k, v in decl.get('slot', {}).items()},
        'correction': {'offset': f'0x{word["offset"]:X}', 'slot': word['slot'],
                       'value': f'0x{struct.unpack("<Q", solved)[0]:016X}'},
        'gates': {n: ok for n, ok in gates},
        'changed_ranges': [[f'0x{a:X}', f'0x{b:X}'] for a, b in diff_ranges(original, bytes(edited))],
    }
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'wrote {args.json}')

    if args.seal:
        sealed = out.with_name(out.stem.replace('.plain', '') + '.sealed.dl_bin')
        sealed = out.parent / (out.name.replace('.plain', '') + '.dl_bin')
        cmd = [sys.executable, str(HERE / 'dlbin_seal.py'), 'seal-key',
               '--key', str(args.pk), '--out', str(sealed), str(out)]
        print('\nsealing:', ' '.join(cmd[1:]))
        done = subprocess.run(cmd, capture_output=True, text=True)
        sys.stdout.write(done.stdout)
        if done.returncode != 0:
            sys.stderr.write(done.stderr)
            return 4
        back = out.parent / 'roundtrip.plain'
        cmd2 = [sys.executable, str(HERE / 'dlbin_seal.py'), 'open-key',
                '--key', str(args.sk), '--out', str(back), str(sealed)]
        done2 = subprocess.run(cmd2, capture_output=True, text=True)
        if done2.returncode != 0:
            sys.stderr.write(done2.stderr)
            return 4
        same = back.read_bytes() == bytes(edited)
        print(f'  roundtrip identical: {"PASS" if same else "FAIL"}')
        if not same:
            return 5
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description='伤害行任意字段编辑（保内容哈希）')
    ap.add_argument('--plain', type=pathlib.Path,
                    default=pathlib.Path('D:/mod/refs/dlbin/plaintext-26251122/'
                                         'generated_damage_settings.dl_bin'))
    sub = ap.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('show', help='打印一行的全部字段')
    s.add_argument('--type', type=int, required=True)
    s.set_defaults(fn=cmd_show)

    h = sub.add_parser('hosts', help='列可当哈希宿主的行')
    h.add_argument('--refs', type=pathlib.Path,
                   help='dmg_refs.py 输出的 json（给了才能标出"没人引用"）')
    h.set_defaults(fn=cmd_hosts)

    e = sub.add_parser('set', help='改字段并保哈希')
    e.add_argument('--type', type=int, required=True)
    e.add_argument('--damage', type=int)
    e.add_argument('--durable', type=int)
    e.add_argument('--ap', help='4 个 u32，逗号分隔，如 5,5,5,0')
    e.add_argument('--demo', type=lambda v: int(v, 0))
    e.add_argument('--force', type=lambda v: int(v, 0))
    e.add_argument('--impulse', type=lambda v: int(v, 0))
    e.add_argument('--element', type=lambda v: int(v, 0))
    e.add_argument('--slot', type=parse_slot, action='append',
                   help='N:TYPE:VALUE，可重复（N=0..3）')
    e.add_argument('--host-type', type=int, required=True)
    e.add_argument('--out', type=pathlib.Path, required=True)
    e.add_argument('--json', type=pathlib.Path)
    e.add_argument('--seal', action='store_true')
    e.add_argument('--pk', type=pathlib.Path,
                   default=pathlib.Path('D:/mod/refs/dlbin/keys/recipient.pk'))
    e.add_argument('--sk', type=pathlib.Path,
                   default=pathlib.Path('D:/mod/refs/dlbin/keys/recipient.sk'))
    e.set_defaults(fn=cmd_set)

    args = ap.parse_args()
    # 全局 --plain 要写在子命令**前面**（argparse 的父子解析顺序）
    return args.fn(args)


if __name__ == '__main__':
    raise SystemExit(main())
