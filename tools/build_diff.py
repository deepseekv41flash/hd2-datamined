#!/usr/bin/env python3
"""build_diff.py -- 游戏更新后，逐张表回答"到底改了什么"。

为什么需要
    Steam 每次更新都会替换 `data/game/generated_*.dl_bin`。我们所有的字段偏移、行号、
    导出数据都建立在这些明文之上，所以更新的第一件事不是改工具，而是**证明哪几张表变了**：
    大小变了不等于内容变了，内容变了不等于行数变了。逐层分开看，后面的工作才有依据。

做法（三层，由便宜到贵）
    1. 文件层：size / mtime / sha256。用 `refs/dlbin/plaintext-<上一个build>` 里缓存的旧明文做对照。
    2. 封装层：用 recipient.sk 解封，比较**明文**的 sha256 —— 这一层能区分
       "密封盒换了" 和 "表内容换了"，也能证明密钥是否还有效。
    3. 结构层：对变了的表解出 LDLD 组/行数/步长，和旧明文逐组对比，指出哪几组的行数或步长变了。

    全程只读：不改游戏目录、不碰进程内存、不需要启动游戏。

用法
    python tools/build_diff.py --sk refs/dlbin/keys/recipient.sk \\
        --old refs/dlbin/plaintext-26088801 --out refs/build-diff-<新build>.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

HEADER = 48


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def groups(plain: bytes) -> list[dict]:
    """只看 LDLD 组头：版本 / 类型 / payload。行数与步长留给调用方结合 typelib 判断。"""
    out, start = [], 0
    while True:
        at = plain.find(b"LDLD", start)
        if at < 0:
            return out
        start = at + 4
        if at + 24 > len(plain):
            continue
        version, type_id, payload, wide = struct.unpack_from("<IIII", plain, at + 4)
        if version in (1, 2) and payload > 0 and at + 24 + payload <= len(plain):
            marker, count = struct.unpack_from("<QQ", plain, at + 24)
            out.append({"at": at, "version": version, "type_id": type_id,
                        "payload": payload, "wide": wide,
                        "marker": marker, "count": count})


def describe(plain: bytes) -> dict:
    gs = groups(plain)
    return {"bytes": len(plain), "groups": len(gs),
            "group_spec": [[g["type_id"], g["payload"], g["count"]] for g in gs],
            "group_types": sorted({g["type_id"] for g in gs})}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sk", required=True, help="recipient.sk（解封用，仓库不含密钥材料）")
    ap.add_argument("--game", default=r"D:\SteamLibrary\steamapps\common\Helldivers 2")
    ap.add_argument("--old", default="refs/dlbin/plaintext-26088801",
                    help="旧 build 的明文缓存目录（文件名与 generated_*.dl_bin 对应）")
    ap.add_argument("--fingerprint", default="build-snapshot-25988413-post-update/fingerprint.json",
                    help="旧 build 的 fingerprint.json（可选，用来对 exe/dll）")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    from nacl.public import PrivateKey, SealedBox
    box = SealedBox(PrivateKey(pathlib.Path(a.sk).read_bytes().ljust(32, b"\0")[:32]))

    gamedir = pathlib.Path(a.game) / "data" / "game"
    olddir = pathlib.Path(a.old)

    # ---- 文件层：exe / game.dll / 表 --------------------------------------------------
    report: dict = {"tables": {}, "binaries": {}, "summary": {}}
    fps = {}
    fp_path = pathlib.Path(a.fingerprint)
    if fp_path.is_file():
        fps = json.loads(fp_path.read_text(encoding="utf-8")).get("files", {})

    for rel in ("bin/helldivers2.exe", "data/game/game.dll", "data/bundle_database.data",
                "data/bundles.nxa"):
        path = pathlib.Path(a.game) / rel
        if not path.is_file():
            report["binaries"][rel] = {"missing": True}
            continue
        raw = path.read_bytes()
        entry = {"size": len(raw), "sha256": sha256(raw)}
        old = fps.get(rel)
        if old:
            entry["old_size"] = old.get("size")
            entry["old_sha256"] = old.get("sha256")
            entry["changed"] = entry["sha256"] != old.get("sha256")
        report["binaries"][rel] = entry

    # ---- 封装层 + 结构层：每张表 -------------------------------------------------------
    changed, unchanged, failed, missing = [], [], [], []
    for path in sorted(gamedir.glob("generated_*.dl_bin")):
        name = path.name
        raw = path.read_bytes()
        old_path = olddir / name
        entry = {"size": len(raw)}
        if not old_path.is_file():
            entry["status"] = "no-old-copy"
            missing.append(name)
            report["tables"][name] = entry
            continue
        old_raw = old_path.read_bytes()
        entry["old_size"] = len(old_raw)
        try:
            new_plain = box.decrypt(raw) if len(raw) > HEADER else raw
        except Exception as exc:                              # noqa: BLE001
            entry["status"] = "decrypt-failed"
            entry["error"] = str(exc)[:120]
            failed.append(name)
            report["tables"][name] = entry
            continue
        new_hash = sha256(new_plain)
        old_hash = sha256(old_raw)
        entry["plaintext_sha256"] = new_hash
        entry["old_plaintext_sha256"] = old_hash
        # 密封盒本身变没变：拿密文减去明文长度的部分比一比（48 字节头 = 32 epk + 16 tag）
        entry["seal_bytes"] = len(raw) - len(new_plain)
        if new_hash == old_hash:
            entry["status"] = "same"
            unchanged.append(name)
        else:
            entry["status"] = "changed"
            new_desc, old_desc = describe(new_plain), describe(old_raw)
            entry["new"] = {"bytes": new_desc["bytes"], "groups": new_desc["groups"]}
            entry["old"] = {"bytes": old_desc["bytes"], "groups": old_desc["groups"]}
            old_spec, new_spec = old_desc["group_spec"], new_desc["group_spec"]
            entry["groups_added"] = len(new_spec) - len(old_spec)
            diffs = [(i, o, n) for i, (o, n) in enumerate(zip(old_spec, new_spec)) if o != n]
            entry["groups_differing"] = len(diffs)
            entry["group_diff_sample"] = [
                {"group": i, "old": {"type_id": o[0], "payload": o[1], "count": o[2]},
                 "new": {"type_id": n[0], "payload": n[1], "count": n[2]}}
                for i, o, n in diffs[:6]]
            changed.append(name)
        report["tables"][name] = entry

    report["summary"] = {"changed": changed, "unchanged": len(unchanged),
                         "decrypt_failed": failed, "no_old_copy": missing}
    print(f"表：{len(report['tables'])} 张，变了 {len(changed)} 张，未变 {len(unchanged)} 张，"
          f"解封失败 {len(failed)} 张")
    if failed:
        print("  ✗ 解封失败（说明密封盒/密钥变了，不只是内容变了）: " + ", ".join(failed))
    for name in changed:
        e = report["tables"][name]
        print(f"  ！{name}: {e['old_size']} -> {e['size']} B，组 {e['old']['groups']} -> "
              f"{e['new']['groups']}，组定义变化 {e['groups_differing']} 处")
        for d in e["group_diff_sample"][:2]:
            print(f"      group{d['group']}: old={d['old']} new={d['new']}")
    for rel, e in report["binaries"].items():
        if e.get("changed"):
            print(f"  ！{rel}: sha256 {e['old_sha256'][:12]}… -> {e['sha256'][:12]}… "
                  f"({e['old_size']} -> {e['size']} B)")
        elif e.get("size") and "changed" in e:
            print(f"  = {rel}: 未变")

    if a.out:
        dest = pathlib.Path(a.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n写入 {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
