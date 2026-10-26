#!/usr/bin/env python3
"""boot_manifest.py -- 谁才是"必然常驻"的包？直接问游戏自己的 `data/settings.ini`。

为什么需要它
    Stingray 引擎在 `settings.ini` 里用**资源路径**指定启动包：
        pre_boot_package = "packages/pre_boot"
        boot_package     = "packages/boot"
        fallback_resource_package = "packages/fallback_resources"
    包 id = `murmur64(路径)`。于是"必然常驻"这件事**可以离线枚举**，不需要运行时探针。
    每个包的 `.package` 资源（type `0xAD9C6D9ED1E5E77A`）就是它的**清单**：
        u32 version | u32 unk | u64 count | count × (u64 type_id, u64 file_id)
    这些清单本身都躺在 **boot 包**里（本 build：`9ba626afa44a3aa3` = `packages/boot`）。

    ⚠ 关键事实（本 build 实测）：**`packages/boot` 的 id 就是 `9ba626afa44a3aa3`** ——
    也就是所有 mod 补丁挂的那个"注册表包"。`.patch_N` 挂它 = 往**启动包**里塞资源，
    这就是"补丁永远在内存里"的真正原因。

用法
    python tools/boot_manifest.py                      # 读默认游戏目录，列 settings.ini 指定的包
    python tools/boot_manifest.py --game "<...>/data" --verbose
    python tools/boot_manifest.py --package 9ba626afa44a3aa3   # 顺便看某个包的组成

依赖：`srkit`（`python -m srkit extract`）。离线，不需要游戏在跑。
"""
from __future__ import annotations

import argparse
import os
import re
import struct
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

DEFAULT_GAME = r"D:\SteamLibrary\steamapps\common\Helldivers 2\data"
SDK_CANDIDATES = [os.environ.get("HD2SDK", ""), r"C:\Users\Admin\HD2SDK-CommunityEdition"]
TYPE_PACKAGE = 0xAD9C6D9ED1E5E77A

TYPE_NAMES = {
    0x18DEAD01056B72E9: "bones", 0x5F7203C8F280DAB8: "physics", 0x931E336D7646CC26: "animation",
    0xA486D4045106165C: "state_machine", 0xA8193123526FAD64: "particles",
    0xE0A48D0BE9A7453F: "unit", 0xCD4238C6A0C69E32: "texture", 0xEAC0B497876ADEDF: "material",
    0x0D972BAB10B40FD3: "strings", TYPE_PACKAGE: "package", 0xA14E8DFA2CD117E2: "lua",
    0x27862FE24795319C: "render_config", 0x9EFE0A916AAE7880: "font",
    0x05106B81DCD58A13: "runtime_font", 0x82645835E6B73232: "config",
    0x2A690FD348FE9AC5: "level", 0xAB2F78E885F513C6: "prefab", 0x9831CA893B0D087D: "entity",
    0x7910103158FC1DE9: "renderable", 0x250E0A11AC8E26F8: "shading_env_mapping",
    0xFE73C7DCFF8A7CA5: "shading_environment", 0x535A7BD3E650D799: "wwise_bank",
    0xAF32095C82F2B070: "wwise_dep", 0xD50A8B7E1C82B110: "wwise_metadata",
    0x5FDD5FE391076F9F: "wwise_properties", 0xE3F2851035957AF5: "hash_lookup",
    0xB8FD4D2CEDE20ED7: "geleta", 0x2A0A70ACFE476E1D: "ah_bin",
    0x3B1FA9E8F6BAC374: "network_config", 0x6592B918E67F082C: "havok_ai_properties",
    0xF7A09F8BB35A1D49: "havok_physics_properties", 0x92D3EE038EEB610D: "flow",
}


def find_sdk() -> str:
    for root in SDK_CANDIDATES:
        if root and os.path.isfile(os.path.join(root, "srkit", "__init__.py")):
            return root
    raise SystemExit("✗ 找不到 HD2SDK 检出（设 HD2SDK=<path>）")


def murmur64(data: bytes) -> int:
    sys.path.insert(0, find_sdk())
    from srkit.util.hashing import murmur64_hash          # noqa: PLC0415
    return murmur64_hash(data)


def read_settings(game: str) -> dict[str, str]:
    ini = os.path.join(game, "settings.ini")
    if not os.path.isfile(ini):
        raise SystemExit(f"✗ 没有 {ini}")
    out = {}
    for line in open(ini, encoding="utf-8", errors="replace"):
        m = re.match(r'\s*([a-z_]*package[a-z_]*)\s*=\s*"([^"]+)"', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def extract_manifest(sdk: str, game: str, pkg_id: int, host: str, outdir: str) -> str | None:
    os.makedirs(outdir, exist_ok=True)
    p = subprocess.run([sys.executable, "-m", "srkit", "extract", "--id", f"{pkg_id:#018x}",
                        "--type", f"{TYPE_PACKAGE:#018x}", "--package", host, "-o", outdir, game],
                       cwd=sdk, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        return None
    for name in os.listdir(outdir):
        if name.lower().endswith(".toc.bin"):
            return os.path.join(outdir, name)
    return None


def parse_manifest(path: str) -> list[tuple[int, int]]:
    b = open(path, "rb").read()
    ver, _unk, cnt = struct.unpack_from("<IIQ", b, 0)
    if not 0 < cnt < 1_000_000 or 16 + cnt * 16 != len(b):
        raise SystemExit(f"✗ {path}: 清单格式不符（ver={ver} count={cnt} len={len(b)}）")
    return [struct.unpack_from("<QQ", b, 16 + i * 16) for i in range(cnt)]


def hist(recs) -> dict[str, int]:
    out: dict[str, int] = {}
    for t, _f in recs:
        k = TYPE_NAMES.get(t, f"0x{t:016x}")
        out[k] = out.get(k, 0) + 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="枚举 settings.ini 指定的启动包及其清单")
    ap.add_argument("--game", default=DEFAULT_GAME)
    ap.add_argument("--sdk", default=None)
    ap.add_argument("--out", default=r"D:\mod\out\boot-manifest")
    ap.add_argument("--host", default="9ba626afa44a3aa3", help="清单资源所在的包（本 build = boot 包）")
    ap.add_argument("--package", default=None, help="额外看某个包的清单（如 9ba626afa44a3aa3）")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    sdk = a.sdk or find_sdk()
    game = a.game
    settings = read_settings(game)
    print(f"settings.ini 里的包设置（{len(settings)} 项）：")
    for k, v in settings.items():
        print(f"  {k:<28} = {v!r}   id = {murmur64(v.encode()):#018x}")

    targets = list(settings.items())
    if a.package:
        targets.append(("--package", a.package))
    print()
    for key, path in targets:
        pid = int(path, 16) if path.startswith("0x") else murmur64(path.encode())
        mf = extract_manifest(sdk, game, pid, a.host, os.path.join(a.out, f"{pid:016x}"))
        if not mf:
            print(f"{key:<28} {pid:#018x}  清单取不到（该包可能没有 .package 清单）")
            continue
        recs = parse_manifest(mf)
        h = hist(recs)
        top = ", ".join(f"{k}×{v}" for k, v in sorted(h.items(), key=lambda kv: -kv[1])[:8])
        print(f"{key:<28} {pid:#018x}  清单 {len(recs):>5} 条  [{top}]")
        if a.verbose:
            for t, f in recs[:40]:
                print(f"    {TYPE_NAMES.get(t, hex(t)):<14} {f:016X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
