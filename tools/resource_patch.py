#!/usr/bin/env python3
"""Build / inspect resource patches (`.patch_N`) for ANY Stingray resource type.

Why this exists
    `srkit.modkit.build_patch()` only knows how to wrap *Lua source* (type 0xa14e8dfa2cd117e2,
    envelope `[len][mode][source]`).  The FRV anti-flip mod (build 25988413) proved that a plain
    `.patch_N` can replace **any** resource type with **raw bytes** — its three entries are `physics`
    resources whose `toc_data` is the resource file (16-byte header + plain float32 payload).
    Codecs are needed to *understand* a format, not to *ship* one.

What this tool does
    list    <patch>                     entries inside a patch (type, id, size, head bytes)
    dump    <patch> <file_id> -o FILE   write one entry's toc_data out verbatim
    repack  <patch> -o DIR              rebuild the patch from its own entries (regression test)
    build   <spec.json> -o DIR --index N    build a patch from (type_id, file_id, payload file)

    A spec is a JSON list:  [{"type": "5f7203c8f280dab8", "id": "0xcc21...", "file": "frv.bin"}]
    `type` and `id` accept hex strings; `file` is relative to the spec.

Verification discipline
    `repack` + `cmp` is the regression that proves this writer reproduces a known-good community
    patch byte for byte. Run it before trusting `build`.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

SDK_CANDIDATES = [
    os.environ.get("HD2SDK", ""),
    r"C:\Users\Admin\HD2SDK-CommunityEdition",
]


def find_sdk() -> str:
    for root in SDK_CANDIDATES:
        if root and os.path.isfile(os.path.join(root, "srkit", "__init__.py")):
            return root
    raise SystemExit("resource_patch: cannot find the HD2SDK checkout (set HD2SDK=<path>)")


sys.path.insert(0, find_sdk())
from srkit.container.package import Package, TocEntry          # noqa: E402
from srkit.container.repo import Repository                    # noqa: E402

BASE = "9ba626afa44a3aa3"
TYPE_NAMES = {
    0x5F7203C8F280DAB8: "physics",
    0xE0A48D0BE9A7453F: "unit",
    0xA14E8DFA2CD117E2: "lua",
    0x18DEAD01056B72E9: "bones",
    0xCD4238C6A0C69E32: "texture",
    0xEAC0B497876ADEDF: "material",
    0x82645835E6B73232: "config",
    0x0D972BAB10B40FD3: "strings",
    0x3B1FA9E8F6BAC374: "network_config",
    0xAF32095C82F2B070: "wwise_dep",
    0x535A7BD3E650D799: "wwise_bank",
    0x504B55235D21440E: "wwise_stream",
    0x2A690FD348FE9AC5: "level",
    0xAB2F78E885F513C6: "prefab",
    0x931E336D7646CC26: "animation",
    0xA8193123526FAD64: "particles",
    0xA486D4045106165C: "state_machine",
    0x9EFE0A916AAE7880: "font",
    0x05106B81DCD58A13: "runtime_font",
    0xF7505933166D6755: "vector_field",
    0x92D3EE038EEB610D: "flow",
    0x27862FE24795319C: "render_config",
    0xAD9C6D9ED1E5E77A: "package",
    0xB277B11FE4A61D37: "mouse_cursor",
    0x7910103158FC1DE9: "renderable",
    0xE5EE32A477239A93: "shader_library",
    0x9E5C3CC74575AEB5: "shader_library_group",
    0x1D59BD6687DB6B33: "ragdoll_profile",
}


def type_label(type_id: int) -> str:
    return TYPE_NAMES.get(int(type_id), f"{int(type_id):016x}")


def open_patch(path: str) -> list[TocEntry]:
    repo = Repository.open(path)
    entries: list[TocEntry] = []
    for name in repo.package_names():
        entries.extend(repo.load_package(name).entries)
    return entries


def cmd_list(args) -> int:
    entries = open_patch(args.patch)
    print(f"{args.patch}: {len(entries)} entrie(s)")
    for i, e in enumerate(entries):
        blob = bytes(e.toc_data)
        print(f"  [{i}] id={e.file_id:#018x} type={type_label(e.type_id):<14} {len(blob):>9,} B  head={blob[:12].hex(' ')}")
    return 0


def cmd_dump(args) -> int:
    entries = open_patch(args.patch)
    target = None
    for i, e in enumerate(entries):
        if (args.which.isdigit() and int(args.which) == i) or e.file_id == int(args.which, 16):
            target = e
            break
    if target is None:
        print(f"no entry {args.which!r}")
        return 2
    blob = bytes(target.toc_data)
    with open(args.output, "wb") as handle:
        handle.write(blob)
    print(f"wrote {args.output} ({len(blob):,} B) type={type_label(target.type_id)} id={target.file_id:#018x}")
    return 0


def cmd_repack(args) -> int:
    """Rebuild the patch from its own entries — the byte-for-byte regression.

    ✗ 旧版是"新建一个 Package 再塞条目"，那会丢掉三样东西：头里的 unknown 字段、
    偏移 16 起的 56 字节未知元数据、以及每条目原始的 toc/stream/gpu 偏移提示
    （后者会让重建结果重排对齐、长度差几十字节）。patch_3 就是这么被重建错的。
    ✓ 正确做法是 Package.parse 原样读进来再 to_bytes —— 实测三个补丁都逐字节一致。
    """
    toc_raw = open(args.patch, "rb").read()
    gpu_path, stream_path = args.patch + ".gpu_resources", args.patch + ".stream"
    gpu_raw = open(gpu_path, "rb").read() if os.path.isfile(gpu_path) else b""
    stream_raw = open(stream_path, "rb").read() if os.path.isfile(stream_path) else b""
    package = Package.parse(toc_raw, gpu_raw, stream_raw, name=os.path.basename(args.patch))
    toc, gpu, stream = package.to_bytes()
    os.makedirs(args.output, exist_ok=True)
    out = os.path.join(args.output, f"{getattr(args, 'base', None) or BASE}.patch_{args.index}")
    with open(out, "wb") as handle:
        handle.write(toc)
    with open(out + ".gpu_resources", "wb") as handle:
        handle.write(gpu)
    with open(out + ".stream", "wb") as handle:
        handle.write(stream)
    original = open(args.patch, "rb").read()
    print(f"rebuilt {out}  ({len(toc):,} B)")
    print(f"original {args.patch}  ({len(original):,} B)")
    print("IDENTICAL" if toc == original else f"DIFFERS (first {sum(1 for a, b in zip(toc, original) if a != b)} differing bytes)")
    return 0 if toc == original else 1


def cmd_build(args) -> int:
    spec = json.load(open(args.spec, encoding="utf-8"))
    if not isinstance(spec, list) or not spec:
        print("spec must be a non-empty JSON list")
        return 2
    root = os.path.dirname(os.path.abspath(args.spec))
    package = Package(name=getattr(args, "base", None) or BASE)
    for item in spec:
        type_id = int(str(item["type"]), 16)
        file_id = int(str(item["id"]), 16)
        path = item["file"] if os.path.isabs(item["file"]) else os.path.join(root, item["file"])
        blob = open(path, "rb").read()
        entry = TocEntry(file_id=file_id, type_id=type_id, toc_data=bytearray(blob))
        gpu_rel = item.get("gpu")
        stream_rel = item.get("stream")
        if gpu_rel:
            gpu_path = gpu_rel if os.path.isabs(gpu_rel) else os.path.join(root, gpu_rel)
            entry.gpu_data = bytearray(open(gpu_path, "rb").read())
        if stream_rel:
            stream_path = stream_rel if os.path.isabs(stream_rel) else os.path.join(root, stream_rel)
            entry.stream_data = bytearray(open(stream_path, "rb").read())
        package.add_entry(entry)
        extra = ""
        if gpu_rel:
            extra += f" gpu={len(entry.gpu_data):,} B"
        if stream_rel:
            extra += f" stream={len(entry.stream_data):,} B"
        print(f"  + {type_label(type_id):<14} id={file_id:#018x} {len(blob):>9,} B{extra}  <- {os.path.basename(path)}")
    toc, gpu, stream = package.to_bytes()
    os.makedirs(args.output, exist_ok=True)
    out = os.path.join(args.output, f"{getattr(args, 'base', None) or BASE}.patch_{args.index}")
    open(out, "wb").write(toc)
    open(out + ".gpu_resources", "wb").write(gpu)
    open(out + ".stream", "wb").write(stream)
    print(f"built {out}  toc={len(toc):,} B  gpu={len(gpu):,} B  stream={len(stream):,} B")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list"); p.add_argument("patch"); p.set_defaults(func=cmd_list)
    p = sub.add_parser("dump"); p.add_argument("patch"); p.add_argument("which"); p.add_argument("-o", "--output", required=True); p.set_defaults(func=cmd_dump)
    p = sub.add_parser("repack"); p.add_argument("patch"); p.add_argument("-o", "--output", required=True); p.add_argument("--index", type=int, default=0); p.add_argument("--base", default=None, help="宿主包 id（默认注册表包）"); p.set_defaults(func=cmd_repack)
    p = sub.add_parser("build"); p.add_argument("spec"); p.add_argument("-o", "--output", required=True); p.add_argument("--index", type=int, default=0); p.add_argument("--base", default=None, help="宿主包 id（默认注册表包 9ba626afa44a3aa3）"); p.set_defaults(func=cmd_build)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
