#!/usr/bin/env python3
"""lua_payload_dump.py -- 把一个第三方 `.patch_N`（或它所在的 zip / 文件夹）里的 **lua 载荷** 全取出来，
可读源码直接落盘；**LuaJIT 字节码**（`loadstring("\\27LJ…")` 那一层壳）解出来并导出字符串常量。

为什么需要
    侦察老版本 Lua mod 的第一步永远是"它到底写了什么"，而这一步有两个坑：
      ① 载荷要先用 srkit 从 patch_0 里抽出来（`--decoded` 才会给明文脚本）；
      ② 一半以上的成品 mod **不发行源码**，主脚本是
         `return assert(loadstring("<转义后的 LuaJIT 字节码>", "@mods/x"))(…)` ——
         肉眼看就是一行乱码。字节码里仍留着**常量表**（表名、字段名、报错文本），
         把它解出来就能判断"改的是哪张表/哪个字段"。

它做什么
    1. `srkit list` 列条目；
    2. 每条 `lua` 条目 `srkit extract --id … --type lua --decoded`；
    3. 抽到的脚本若是 bytecode 壳，就地解码 → `<entry>.luac` + `<entry>.strings.txt`；
    4. 打印一张"载荷清单"（类型 / 源码还是字节码 / 大小 / 关键字命中）。

用法
    python tools/lua_payload_dump.py --patch  D:/mod/x/Addon/9ba626afa44a3aa3.patch_0 --out D:/mod/recon/x
    python tools/lua_payload_dump.py --zip    "D:/Downloads/SomeMod.zip" --member Sticky --out D:/mod/recon/x
    python tools/lua_payload_dump.py --patch  … --keywords ComponentData,Settings,offset,rva

依赖
    `python -m srkit`（HD2SDK-CommunityEdition 检出）；用 `--sdk` 或环境变量 `HD2SDK` 指定。
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:                                              # noqa: BLE001
        pass

BSLASH = chr(92)
DEFAULT_SDK = os.environ.get('HD2SDK', r'C:\Users\Admin\HD2SDK-CommunityEdition')

DEFAULT_KEYWORDS = [
    'ComponentData', 'Settings', 'component', 'settings', 'offset', 'rva',
    'WriteProcessMemory', 'ReadProcessMemory', 'DamageInfo', 'Throwable',
    'Sticky', 'WeaponData', 'Projectile', 'Explosion', 'StatusEffect',
    'material', 'hknp', 'record', 'table',
]


# --------------------------------------------------------------------------- srkit
def srkit(sdk: pathlib.Path, *args: str) -> str:
    cmd = [sys.executable, '-m', 'srkit', *args]
    done = subprocess.run(cmd, cwd=str(sdk), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if done.returncode != 0:
        raise RuntimeError(f'srkit {args[0]} failed ({done.returncode}):\n{done.stdout}\n{done.stderr}')
    return done.stdout


def list_entries(sdk: pathlib.Path, patch: pathlib.Path) -> list[dict]:
    text = srkit(sdk, 'list', str(patch))
    out = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 6 or parts[0].startswith('--'):
            continue
        kind, file_id, name = parts[0], parts[1], parts[2]
        toc = parts[3]
        out.append({'type': kind, 'id': file_id, 'name': name, 'toc': int(toc) if toc.isdigit() else 0})
    return out


def extract(sdk: pathlib.Path, patch: pathlib.Path, entry: dict, out_dir: pathlib.Path) -> pathlib.Path:
    dst = out_dir / entry['id']
    dst.mkdir(parents=True, exist_ok=True)
    srkit(sdk, 'extract', '--id', entry['id'], '--type', entry['type'], '--decoded',
          '-o', str(dst), str(patch))
    found = sorted(dst.rglob('*.lua'))
    if not found:
        raise RuntimeError(f'no decoded script for {entry["id"]}')
    return found[0]


# ------------------------------------------------------------------- bytecode shell
def unescape_lua(text: str) -> bytes:
    """Decode a Lua double-quoted string body into bytes (\\ddd / \\xNN / short escapes)."""
    simple = {'n': 10, 't': 9, 'r': 13, 'a': 7, 'b': 8, 'f': 12, 'v': 11, BSLASH: 92,
              '"': 34, "'": 39, '\n': 10}
    out = bytearray()
    i = 0
    while i < len(text):
        c = text[i]
        if c != BSLASH:
            out.extend(c.encode('latin-1', 'replace'))
            i += 1
            continue
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if nxt.isdigit():
            j, num = i + 1, ''
            while j < len(text) and text[j].isdigit() and len(num) < 3:
                num += text[j]
                j += 1
            out.append(int(num) & 0xFF)
            i = j
            continue
        if nxt == 'x':
            out.append(int(text[i + 2:i + 4], 16))
            i += 4
            continue
        if nxt in simple:
            out.append(simple[nxt])
            i += 2
            continue
        i += 2
    return bytes(out)


def unwrap(script: pathlib.Path) -> tuple[bytes | None, str]:
    """If the script is a `loadstring("…")` shell, return (bytecode, 'bytecode'); else (None, 'source')."""
    text = script.read_text(encoding='utf-8', errors='replace')
    m = re.search(r'loadstring\("(.*?)"', text, re.S)
    if not m:
        return None, 'source'
    blob = unescape_lua(m.group(1))
    if blob[:4] != bytes([0x1B, 0x4C, 0x4A, 0x02]):
        return None, 'source'
    return blob, 'bytecode'


def strings_of(blob: bytes, min_len: int = 4) -> list[str]:
    runs = [x.decode('ascii', 'replace') for x in re.findall(rb'[\x20-\x7e]{%d,}' % min_len, blob)]
    uniq: list[str] = []
    for r in runs:
        if r not in uniq:
            uniq.append(r)
    return uniq


# ------------------------------------------------------------------------- driver
def main() -> int:
    ap = argparse.ArgumentParser(description='抽取 patch_0 里的 lua 载荷；字节码壳自动解码并导出字符串')
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--patch', type=pathlib.Path, help='.patch_N 文件')
    src.add_argument('--zip', type=pathlib.Path, help='包含 patch_N 的 zip（配合 --member 选一个）')
    ap.add_argument('--member', default='', help='--zip 时，选名字含该子串的 patch_0（不唯一会报错）')
    ap.add_argument('--out', type=pathlib.Path, required=True)
    ap.add_argument('--sdk', type=pathlib.Path, default=pathlib.Path(DEFAULT_SDK))
    ap.add_argument('--keywords', default=','.join(DEFAULT_KEYWORDS),
                    help='在字符串常量里高亮的关键词，逗号分隔')
    ap.add_argument('--min-len', type=int, default=4)
    a = ap.parse_args()

    if not (a.sdk / 'srkit').is_dir():
        print(f'!! 找不到 srkit（{a.sdk}）；用 --sdk 或 HD2SDK 指定 HD2SDK-CommunityEdition 检出')
        return 2

    patch = a.patch
    tmp_dir = None
    if a.zip:
        a.out.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(a.zip) as zf:
            hits = [n for n in zf.namelist() if n.endswith('.patch_0') and a.member.lower() in n.lower()]
            if len(hits) != 1:
                print(f'!! --member "{a.member}" 命中 {len(hits)} 个 patch_0：{hits[:6]}')
                return 2
            tmp_dir = a.out / '_unpacked'
            tmp_dir.mkdir(parents=True, exist_ok=True)
            zf.extract(hits[0], tmp_dir)
            patch = tmp_dir / hits[0]
    if not patch or not patch.is_file():
        print(f'!! no patch: {patch}')
        return 2

    a.out.mkdir(parents=True, exist_ok=True)
    entries = list_entries(a.sdk, patch)
    print(f'{patch.name}: {len(entries)} 条')
    if not entries:
        return 2

    keywords = [k.strip() for k in a.keywords.split(',') if k.strip()]
    rows = []
    for entry in entries:
        script = extract(a.sdk, patch, entry, a.out)
        blob, kind = unwrap(script)
        note = ''
        hits: list[str] = []
        if blob is not None:
            luac = script.with_suffix('.luac')
            luac.write_bytes(blob)
            strs = strings_of(blob, a.min_len)
            (script.parent / (script.stem + '.strings.txt')).write_text('\n'.join(strs), encoding='utf-8')
            hits = [s for s in strs if any(k.lower() in s.lower() for k in keywords) and len(s) <= 70]
            note = f'{len(blob):,} B 字节码 → {luac.name} + strings.txt（{len(strs)} 条常量）'
        else:
            text = script.read_text(encoding='utf-8', errors='replace')
            hits = [ln.strip() for ln in text.splitlines()
                    if any(k.lower() in ln.lower() for k in keywords)][:12]
            note = f'{len(text):,} B 可读源码（{text.count(chr(10)) + 1} 行）'
        rows.append({'entry': entry, 'script': script, 'kind': kind, 'note': note, 'hits': hits})

    print()
    print('| 条目 | 类型 | 形态 | 说明 |')
    print('|---|---|---|---|')
    for r in rows:
        print(f'| `{r["entry"]["id"]}` | {r["entry"]["type"]} | {r["kind"]} | {r["note"]} |')

    for r in rows:
        if r['hits']:
            print(f'\n== {r["entry"]["id"]} 关键词命中（{len(r["hits"])}）:')
            for h in r['hits'][:24]:
                print('   ', h[:110])
    print(f'\n产物在 {a.out}')
    if tmp_dir and shutil.which('true') is None:      # pragma: no cover - 仅提示
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
