#!/usr/bin/env python3
"""analyze_proxy_log.py — 从 variant_mod 的 proxy.log 里切出「本次会话」并汇总。

proxy.log 每行形如：
    18:58:03 REQ GET /api/Stats/profile/801/summary 0B
    18:58:05 RESP 200 19176B
    18:28:35 proxy pid 46628 -> ...
    ============  ← 每次启动的分隔线

用法：
    python tools/analyze_proxy_log.py                       # 最近一次会话
    python tools/analyze_proxy_log.py --since "18:28:35"
    python tools/analyze_proxy_log.py --all                 # 整个日志
"""
from __future__ import annotations

import argparse
import collections
import io
import pathlib
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

LOG = pathlib.Path(r"D:\Downloads\variant_mod\logs\proxy.log")
REQ = re.compile(r"^(\d\d:\d\d:\d\d) REQ (\w+) (\S+)(?: (\d+)B)?$")
RESP = re.compile(r"^(\d\d:\d\d:\d\d) RESP (\d{3}) (\d+)B$")
MARK = re.compile(r"^=+$")


def load(path: pathlib.Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def session_bounds(lines: list[str]) -> tuple[int, int]:
    """最后一个启动标记之后算本次会话。"""
    start = 0
    for i, line in enumerate(lines):
        if MARK.match(line.strip()) and i + 1 < len(lines):
            start = i
    return start, len(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(LOG))
    ap.add_argument("--since", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    lines = load(pathlib.Path(args.log))
    if args.all:
        lo, hi = 0, len(lines)
    elif args.since:
        lo, hi = 0, len(lines)
        for i, line in enumerate(lines):
            if line.startswith(args.since):
                lo = i
                break
    else:
        lo, hi = session_bounds(lines)

    reqs = []          # (time, method, path, body)
    resps = []         # (time, code, bytes)
    for line in lines[lo:hi]:
        m = REQ.match(line)
        if m:
            reqs.append((m.group(1), m.group(2), m.group(3), int(m.group(4) or 0)))
            continue
        m = RESP.match(line)
        if m:
            resps.append((m.group(1), int(m.group(2)), int(m.group(3))))

    if not reqs:
        print("这段时间没有请求记录")
        return 0

    print(f"会话窗口：{lines[lo][:8] if lines[lo][:8].count(':') == 2 else '?'} … "
          f"{reqs[-1][0]}")
    print(f"请求 {len(reqs)} 条 · 响应 {len(resps)} 条 · 响应总量 {sum(r[2] for r in resps):,} B"
          f" · 请求体总量 {sum(r[3] for r in reqs):,} B")

    codes = collections.Counter(r[1] for r in resps)
    print("状态码：" + "  ".join(f"{k}×{v}" for k, v in sorted(codes.items())))

    # 按端点聚合
    agg = collections.defaultdict(lambda: [0, 0, 0])   # count, req_bytes, resp_bytes(近似)
    for _, method, path, body in reqs:
        key = f"{method} {path.split('?')[0]}"
        agg[key][0] += 1
        agg[key][1] += body
    # 响应无法一一对应端点（日志只有状态+大小），这里按顺序配对
    for (t, code, size), (_, method, path, _b) in zip(resps, reqs):
        key = f"{method} {path.split('?')[0]}"
        agg[key][2] += size

    print(f"\n{'次数':>4} {'请求B':>8} {'响应B':>10}  端点")
    for key, (n, rb, pb) in sorted(agg.items(), key=lambda kv: -kv[1][2])[:args.top]:
        print(f"{n:>4} {rb:>8,} {pb:>10,}  {key}")

    print("\n首 20 条（登录流程顺序）：")
    for t, method, path, body in reqs[:20]:
        print(f"  {t} {method:6} {path}  {body}B")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
