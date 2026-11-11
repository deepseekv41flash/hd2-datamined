import collections
import csv
import os

ROOT = r"D:\mod\work\eac-audit"
rows = list(csv.DictReader(open(os.path.join(ROOT, "access-events.csv"), encoding="utf-8-sig")))
print("total events:", len(rows))


def name(r):
    return r["ObjectName"].rsplit("\\", 1)[-1]


def sec(r):
    h, m, s = r["Time"].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


for r in rows:
    r["_t"] = sec(r)
rows.sort(key=lambda r: r["_t"])

groups = collections.OrderedDict()
for r in rows:
    groups.setdefault(r["Time"][:8], []).append(name(r))

print("\n=== reads per second ===")
for k, v in groups.items():
    sample = v[0] if len(v) == 1 else f"{v[0]} … {v[-1]}"
    print(f"{k}  n={len(v):3d}  {sample}")

print("\nfirst read:", rows[0]["Time"], name(rows[0]))
print("last  read:", rows[-1]["Time"], name(rows[-1]))
print("distinct files:", len({r['ObjectName'] for r in rows}))
print("distinct pids :", {r["ProcessId"] for r in rows})
print("distinct masks:", {r["AccessMask"] for r in rows})

# the three reference timestamps of this run
WINDOW = "21:13:22.460"
POPUP = "21:14:02.085"


def t_of(stamp):
    h, m, s = stamp.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


w, p = t_of(WINDOW), t_of(POPUP)
print(f"\nwindow visible {WINDOW}   popup {POPUP}   -> popup at window +{p - w:.2f}s")

# split into "engine load" (before the popup) vs anything after
before = [r for r in rows if r["_t"] < p]
after = [r for r in rows if r["_t"] >= p]
print(f"reads before popup: {len(before)}   after popup: {len(after)}")
if after:
    print("  post-popup reads:", [(r['Time'], name(r)) for r in after][:12])

# last read before popup
last_before = max(before, key=lambda r: r["_t"])
print(f"last read before popup: {last_before['Time']} {name(last_before)} "
      f"-> popup is {p - last_before['_t']:.2f}s later")

# engine load completion: last read in the dense burst (< 21:13:50)
burst = [r for r in rows if r["_t"] < t_of("21:13:50")]
lb = max(burst, key=lambda r: r["_t"])
print(f"last read of the load burst: {lb['Time']} {name(lb)} "
      f"-> window +{lb['_t'] - w:.2f}s, popup {p - lb['_t']:.2f}s later")

# second pass over the same files? count reads per file
per_file = collections.Counter(name(r) for r in rows)
multi = {k: v for k, v in per_file.items() if v > 1}
print(f"\nfiles read more than once: {len(multi)} of {len(per_file)}")
for k, v in sorted(multi.items(), key=lambda kv: -kv[1])[:10]:
    print(f"  {k:52s} x{v}")
