#!/usr/bin/env python3
"""unit_offset.py -- 给 `unit`（壳）里的某个节点加位移，做成 `.patch_N`（治"模型缩在车体里"）。

为什么需要它
    挂载槽 `MountInfo` 只有 24 B（`item` + 两个 anchor + side + 2 字节），**没有任何位移字段**；
    所以"把挂载件往上抬 N 米"只能改**壳自己**：`unit` 资源里有一套节点变换表
    （`transform_info` 段：`count u32 | 12 B | 每节点 {rot 9f, pos 3f, scale 3f, pad} | 矩阵 count×64 B | …`），
    把"内容容器"节点的 `position`/`matrix` 平移，整机就跟着走（muzzle 骨骼也在同一子树里，所以瞄具/开火点会一起动）。

    猎枪哨戒（`et_turret/rocket_turret`）的节点 3 是 `shadow_mesh / skeleton / collision / game_mesh` 的父节点，
    **动它一个就够**；`unit` 的 transform 段是"只读视图"，srkit 编码时会原样拷贝，
    所以这里直接做**等长二进制改写**（不重编、不碰 gpu），再打成补丁。

用法
    python tools/unit_offset.py shift --unit 0x37079568DC86E9C6 --package 11bbdf8ce39e5fc5 \\
        --host f6fb08cc02d24255 --index 2 --node 3 --dz 2.0 \\
        --out D:/mod/out/unit-offset [--install]

    # 只读：列出节点（名字/位置/父子），用于挑 node
    python tools/unit_offset.py show --unit 0x37079568DC86E9C6 --package 11bbdf8ce39e5fc5

门禁
    G1 段自洽：count == 解码 JSON 的节点数，且抽样节点的 position 与 JSON 一致
    G2 等长：改写前后字节数不变、只有目标 float 变
    G3 读回：重新解析，目标节点位移 == 期望，其它节点逐字节未变
    G4 补丁：条目数 / type / id 正确，gpu 跟源一致
    G5 sha256 打印

依赖：`srkit`（`python -m srkit`）+ 同目录 `resource_patch.py`（复用补丁构建器）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

DEFAULT_GAME = r"D:\SteamLibrary\steamapps\common\Helldivers 2\data"
SDK_CANDIDATES = [os.environ.get("HD2SDK", ""), r"C:\Users\Admin\HD2SDK-CommunityEdition"]
UNIT_TYPE = 0xE0A48D0BE9A7453F          # 注意：srkit 把它显示成 "mesh"，其实是 unit

NODE_STRIDE = 64                        # rot 9f + pos 3f + scale 3f + pad
POS_OFF = 36                            # 节点内 position 的偏移
MAT_STRIDE = 64
MAT_TZ_OFF = 14 * 4                     # 列主序：translation 在 12..14，取 z


def find_sdk() -> str:
    for root in SDK_CANDIDATES:
        if root and os.path.isfile(os.path.join(root, "srkit", "__init__.py")):
            return root
    raise SystemExit("✗ 找不到 HD2SDK 检出（设 HD2SDK=<path>）")


def run(argv: list[str], cwd: str) -> str:
    p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print((p.stdout or "")[-1500:])
        print((p.stderr or "")[-1500:], file=sys.stderr)
        raise SystemExit(f"✗ 命令失败：{' '.join(argv[:4])}…")
    return p.stdout or ""


def sha16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:16]


def fetch_unit(sdk: str, game: str, package: str, unit_id: int, outdir: str) -> tuple[str, str, dict]:
    """取 unit 的 toc + gpu（raw）与解码 JSON。返回 (toc_path, gpu_path, json)。"""
    os.makedirs(outdir, exist_ok=True)
    run([sys.executable, "-m", "srkit", "extract", "--id", hex(unit_id), "--type", hex(UNIT_TYPE),
         "--package", package, "--decoded", "-o", outdir, game], sdk)
    hexid = f"{unit_id:016X}"
    toc = os.path.join(outdir, f"mesh_{hexid}.toc.bin")
    gpu = os.path.join(outdir, f"mesh_{hexid}.gpu.bin")
    js = os.path.join(outdir, f"mesh_{hexid}.json")
    if not os.path.isfile(toc) or not os.path.isfile(js):
        raise SystemExit(f"✗ 没拿到 unit {hexid}（找 {toc}）")
    return toc, gpu, json.load(open(js, encoding="utf-8"))


def parse_section(b: bytes, tf: int) -> tuple[int, int]:
    count = struct.unpack_from("<I", b, tf)[0]
    if not 0 < count < 100000:
        raise SystemExit(f"✗ transform 段 count 异常：{count}")
    nodes_at = tf + 16
    mats_at = nodes_at + count * NODE_STRIDE
    return count, mats_at


def node_pos(b: bytes, tf: int, idx: int) -> list[float]:
    return list(struct.unpack_from("<3f", b, tf + 16 + idx * NODE_STRIDE + POS_OFF))


def cmd_show(args) -> int:
    sdk = args.sdk or find_sdk()
    toc_p, _gpu, js = fetch_unit(sdk, args.game, args.package, int(args.unit, 16), args.out)
    b = open(toc_p, "rb").read()
    tf = js["section_offsets"]["transform_info"]
    count, mats_at = parse_section(b, tf)
    print(f"unit {int(args.unit,16):#018x}  toc={len(b):,} B  transform 段 @0x{tf:X}  节点 {count}")
    print(f"{'idx':>4} {'parent':>6} {'name':<26} {'pos(x,y,z)':<32} {'matrix tz':>10}")
    for i, t in enumerate(js["transforms"]):
        mz = struct.unpack_from("<f", b, mats_at + i * MAT_STRIDE + MAT_TZ_OFF)[0]
        print(f"{i:>4} {t['parent_bone']:>6} {(t['name'] or t['name_hash'])[:26]:<26} "
              f"[{t['position'][0]:8.3f},{t['position'][1]:8.3f},{t['position'][2]:8.3f}]{'':<2} {mz:10.3f}")
    return 0


def cmd_shift(args) -> int:
    sdk = args.sdk or find_sdk()
    unit_id = int(args.unit, 16)
    out = os.path.abspath(args.out)
    toc_p, gpu_p, js = fetch_unit(sdk, args.game, args.package, unit_id, out)
    raw = open(toc_p, "rb").read()
    tf = js["section_offsets"]["transform_info"]
    count, mats_at = parse_section(raw, tf)

    # ---- G1 段自洽（与解码 JSON 对照）
    transforms = js["transforms"]
    if len(transforms) != count:
        raise SystemExit(f"✗ [G1] 段里 {count} 个节点、JSON 里 {len(transforms)} 个")
    for i in (0, min(3, count - 1), count - 1):
        seg = node_pos(raw, tf, i)
        ref = transforms[i]["position"]
        if any(abs(a - c) > 1e-5 for a, c in zip(seg, ref)):
            raise SystemExit(f"✗ [G1] 节点 {i} 的 position 与 JSON 不符：{seg} vs {ref}")
    print(f"[G1] transform 段自洽：{count} 节点，采样 position 与解码 JSON 一致 ✓")

    idx = args.node
    if not 0 <= idx < count:
        raise SystemExit(f"✗ --node {idx} 越界（0..{count-1}）")
    d = [args.dx, args.dy, args.dz]
    old = node_pos(raw, tf, idx)
    new = [old[k] + d[k] for k in range(3)]
    b = bytearray(raw)
    struct.pack_into("<3f", b, tf + 16 + idx * NODE_STRIDE + POS_OFF, *new)
    m_old = struct.unpack_from("<3f", raw, mats_at + idx * MAT_STRIDE + 12 * 4)
    struct.pack_into("<3f", b, mats_at + idx * MAT_STRIDE + 12 * 4,
                     m_old[0] + d[0], m_old[1] + d[1], m_old[2] + d[2])
    print(f"[..] 节点 {idx}（{transforms[idx]['name'] or transforms[idx]['name_hash']}）: "
          f"[{old[0]:.3f},{old[1]:.3f},{old[2]:.3f}] → [{new[0]:.3f},{new[1]:.3f},{new[2]:.3f}]")

    # ---- G2 等长 + 只有目标字节变
    if len(b) != len(raw):
        raise SystemExit("✗ [G2] 长度变了")
    diff = [i for i in range(len(raw)) if raw[i] != b[i]]
    allow = set()
    for k in range(3):
        allow.add(tf + 16 + idx * NODE_STRIDE + POS_OFF + 4 * k)      # 每个 float 的首字节所在区间
    # 允许落在目标 float 的 4 字节内
    def ok(i):
        p = tf + 16 + idx * NODE_STRIDE + POS_OFF
        q = mats_at + idx * MAT_STRIDE + 12 * 4
        return (p <= i < p + 12) or (q <= i < q + 12)
    bad = [i for i in diff if not ok(i)]
    if bad:
        raise SystemExit(f"✗ [G2] 目标以外有 {len(bad)} 字节变了（首个 @0x{bad[0]:X}）")
    print(f"[G2] 等长 {len(b):,} B，变动 {len(diff)} 字节且全在目标位移里 ✓")

    # ---- G3 读回
    chk = bytes(b)
    got = node_pos(chk, tf, idx)
    if any(abs(a - c) > 1e-4 for a, c in zip(got, new)):
        raise SystemExit(f"✗ [G3] 读回 {got} != {new}")
    for i in range(count):
        if i == idx:
            continue
        if node_pos(chk, tf, i) != node_pos(raw, tf, i):
            raise SystemExit(f"✗ [G3] 节点 {i} 也变了")
    print(f"[G3] 读回节点 {idx} = [{got[0]:.3f},{got[1]:.3f},{got[2]:.3f}]，其余节点未变 ✓")

    patched = os.path.join(out, f"unit_{unit_id:016X}.offset.bin")
    open(patched, "wb").write(chk)

    # ---- 打补丁
    name = f"{args.host}.patch_{args.index}"
    spec = [{"type": f"{UNIT_TYPE:016X}", "id": hex(unit_id), "file": patched}]
    if os.path.isfile(gpu_p) and os.path.getsize(gpu_p):
        spec[0]["gpu"] = os.path.abspath(gpu_p)
    spec_p = os.path.join(out, "spec_unit_offset.json")
    json.dump(spec, open(spec_p, "w", encoding="utf-8"), indent=1)
    run([sys.executable, os.path.join(HERE, "resource_patch.py"), "build", spec_p,
         "-o", out, "--index", str(args.index), "--base", args.host], HERE)

    patch = os.path.join(out, name)
    sys.path.insert(0, HERE)
    from resource_patch import open_patch, type_label        # noqa: E402
    entries = open_patch(patch)
    if len(entries) != 1:
        raise SystemExit(f"✗ [G4] 补丁条目 {len(entries)} != 1")
    e = entries[0]
    if int(e.type_id) != UNIT_TYPE or int(e.file_id) != unit_id:
        raise SystemExit(f"✗ [G4] 条目 type/id 不对：{type_label(e.type_id)} {int(e.file_id):#x}")
    if bytes(e.toc_data) != chk:
        raise SystemExit("✗ [G4] 补丁里的 toc 与改写结果不一致")
    gsz = os.path.getsize(gpu_p) if os.path.isfile(gpu_p) else 0
    csz = os.path.getsize(patch + ".gpu_resources") if os.path.isfile(patch + ".gpu_resources") else 0
    if gsz and gsz != csz:
        raise SystemExit(f"✗ [G4] gpu 尺寸 {csz:,} != 源 {gsz:,}")
    print(f"[G4] 补丁 1 条：{type_label(e.type_id)} {int(e.file_id):#018x}  "
          f"toc {len(chk):,} B  gpu {csz:,} B ✓")

    # ---- G5
    print(f"[G5] {patch}  sha256={sha16(patch)}")
    if csz:
        print(f"     {patch}.gpu_resources  sha256={sha16(patch + '.gpu_resources')}")

    if args.install:
        for src in (patch, patch + ".gpu_resources", patch + ".stream"):
            if os.path.isfile(src):
                dst = os.path.join(args.game, os.path.basename(src))
                with open(src, "rb") as fi, open(dst, "wb") as fo:
                    fo.write(fi.read())
                print(f"[install] {dst}  sha256={sha16(dst)}")
    else:
        print(f"  安装：把 {name} / .gpu_resources 拷到 <game>/data/（序号必须连续）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="改 unit 节点位移 → .patch_N")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--unit", required=True, help="unit 资源 id（= 壳 id）")
        p.add_argument("--package", required=True, help="源包 id")
        p.add_argument("--game", default=DEFAULT_GAME)
        p.add_argument("--sdk", default=None)
        p.add_argument("--out", default=r"D:\mod\out\unit-offset")

    p = sub.add_parser("show", help="列出节点（挑 node 用）")
    common(p); p.set_defaults(func=cmd_show)

    p = sub.add_parser("shift", help="平移一个节点 → 补丁")
    common(p)
    p.add_argument("--host", required=True, help="宿主包 id（补丁名前半段）")
    p.add_argument("--index", type=int, required=True, help="补丁序号（必须连续）")
    p.add_argument("--node", type=int, required=True, help="节点索引（见 show）")
    p.add_argument("--dx", type=float, default=0.0)
    p.add_argument("--dy", type=float, default=0.0)
    p.add_argument("--dz", type=float, default=0.0, help="Stingray 是 Z 向上，抬升就加 dz")
    p.add_argument("--install", action="store_true")
    p.set_defaults(func=cmd_shift)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
