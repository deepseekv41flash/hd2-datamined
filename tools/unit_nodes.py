#!/usr/bin/env python3
"""unit_nodes.py -- 秒读一个 unit（「壳」）资源的**节点表**：名字 / 父子 / 位移。

为什么需要
    `srkit extract --decoded` 会把 GPU 里每个 mesh 拆成顶点 JSON（几十到上百 MB），
    只为回答"这个壳里有没有 `cargo_attach` 这个节点"完全不值那个代价。
    srkit 的顶点视图是**可选**的（`options{"decode_vertices": True}` 才建），
    不传就只解头部与 transform 段 —— 一次 1–3 秒。

节点名存在哪
    transform 段的定长布局（`count u32 | 12 B pad | 节点 64 B×n | 矩阵 64 B×n |
    父子 4 B×n | 名字哈希 4 B×n`），名字就是 **murmur32**，解析靠 hashlists。
    默认用 SDK 的 `hashlists/friendlynames.txt`；解析不出来就显示 `0xXXXXXXXX`，
    再用 `--find cargo_attach,boss` 按候选名反查（不依赖 hashlist 是否覆盖）。

用法
    python tools/unit_nodes.py --unit 0x75BE82ED8592A6B3 --package f6fb08cc02d24255
    python tools/unit_nodes.py --unit 0x2D85BFE3D8717FE5 --find cargo_attach,boss,attach_turret
    python tools/unit_nodes.py --unit 0x... --full --json-out D:/mod/out/nodes.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                          # noqa: BLE001
        pass

GAME = r"D:\SteamLibrary\steamapps\common\Helldivers 2\data"
SDK_CANDIDATES = [os.environ.get("HD2SDK", ""), r"C:\Users\Admin\HD2SDK-CommunityEdition"]
HASHLISTS = r"C:\Users\Admin\HD2SDK-CommunityEdition\hashlists"


def find_sdk() -> str:
    for root in SDK_CANDIDATES:
        if root and os.path.isfile(os.path.join(root, "srkit", "__init__.py")):
            return root
    raise SystemExit("✗ 找不到 HD2SDK 检出（设 HD2SDK=<path> 或 --sdk）")


def load_friendly(path: str) -> dict[int, str]:
    sdk = find_sdk()
    if sdk not in sys.path:
        sys.path.insert(0, sdk)
    from srkit.util.hashing import murmur32_hash               # noqa: E402
    table: dict[int, str] = {}
    for name in ("friendlynames.txt", "hashlist-all.txt"):
        f = os.path.join(path, name)
        if not os.path.isfile(f):
            continue
        with open(f, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                table.setdefault(murmur32_hash(line), line)
    return table


def main() -> int:
    ap = argparse.ArgumentParser(description="unit 节点表速读")
    ap.add_argument("--unit", required=True, help="unit 资源 id（= 壳 id，十六进制）")
    ap.add_argument("--package", default=None, help="限定包 id（省掉遍历全库）")
    ap.add_argument("--game", default=GAME)
    ap.add_argument("--sdk", default=None)
    ap.add_argument("--hashlists", default=HASHLISTS)
    ap.add_argument("--find", default="", help="逗号分隔候选名：只报命中")
    ap.add_argument("--full", action="store_true", help="打印全部节点")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    sdk = a.sdk or find_sdk()
    if sdk not in sys.path:
        sys.path.insert(0, sdk)
    from srkit.workspace import Repository                      # noqa: E402
    from srkit.resources.base import get_codec                  # noqa: E402
    from srkit.util.ids import NameTable                        # noqa: E402
    from srkit.util.hashing import murmur32_hash                # noqa: E402

    unit = int(a.unit, 16)
    repo = Repository.open(a.game)
    names = NameTable()
    friendly = load_friendly(a.hashlists) if a.hashlists else {}

    # 第一遍：只读**元数据**（load_blobs=False，不解包体）找包；第二遍只取这一条的字节。
    # 直接 load_blobs=True 扫全库会解压几十 GB，这就是第一版超时的原因。
    unit_type = 0xE0A48D0BE9A7453F
    package_name = a.package
    if package_name is None:
        for candidate_name in repo.package_names():
            try:
                package = repo.load_package(candidate_name, load_blobs=False)
            except Exception:                                  # noqa: BLE001
                continue
            if any(e.file_id == unit and e.type_id == unit_type for e in package.entries):
                package_name = candidate_name
                break
    if package_name is None:
        raise SystemExit(f"✗ 全库找不到类型为 mesh 的 unit {unit:#018x}")

    entry = repo.load_entry(package_name, unit, unit_type)
    print(f"unit {unit:#018x} ← 包 {package_name}  类型 0x{entry.type_id:016X}")

    codec = get_codec(entry.type_id)
    decoded = codec.decode(entry, names, {})           # 不建顶点视图 —— 这就是快的原因
    ir = decoded.ir
    tf = ir["section_offsets"]["transform_info"]
    transforms = ir["transforms"]
    print(f"transform 段 @0x{tf:X}  节点 {len(transforms)}  "
          f"toc {len(entry.toc_data):,} B  gpu {len(entry.gpu_data):,} B")

    want = {s.strip() for s in a.find.split(",") if s.strip()}
    targets = {murmur32_hash(w): w for w in want}
    hits = []
    for t in transforms:
        h = int(t["name_hash"])
        label = friendly.get(h) or targets.get(h) or f"0x{h:08X}"
        if want:
            if h in targets:
                hits.append((t, label))
                print(f"  命中 {label:<16} 节点 {t['index']:>4} 父 {t['parent_bone']:>4} "
                      f"pos=[{t['position'][0]:.3f},{t['position'][1]:.3f},{t['position'][2]:.3f}]")
        elif a.full:
            print(f"{t['index']:>4} p{t['parent_bone']:<4} {label:<30} "
                  f"[{t['position'][0]:8.3f},{t['position'][1]:8.3f},{t['position'][2]:8.3f}]")
    if want:
        print(f"→ {len(hits)}/{len(want)} 个候选命中")
        missing = [w for h, w in targets.items() if not any(int(t["name_hash"]) == h for t in transforms)]
        if missing:
            print(f"  缺席：{', '.join(missing)}")
    if a.json_out:
        out = [{"index": t["index"], "parent": t["parent_bone"],
                "name_hash": t["name_hash"],
                "name": friendly.get(int(t["name_hash"]), ""),
                "position": t["position"]} for t in transforms]
        open(a.json_out, "w", encoding="utf-8").write(json.dumps(out, indent=1, ensure_ascii=False))
        print(f"→ {a.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
