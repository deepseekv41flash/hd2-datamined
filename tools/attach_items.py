#!/usr/bin/env python3
"""从服务端物品目录里挑出「某把武器的附件解锁行」，生成可以直接喂给代理的 inventory 注入文件。

附件在服务端就是 inventory 里的一行（不是单独的「拥有」概念）：
  /api/Progression/items 中 progressionCategory == 2 且带 parentId 的记录 =
      { itemId: 附件 optionId, parentId: 武器 mixId, mixId: 该附件在这把枪上的库存键 }
解锁动作 = POST /api/Progression/ProgressionPackage/AcquireUnlockableItem
           { itemMixId: <mixId>, packageId32, targetLevel, expectedCost:[{mixId: 货币, amount}] }
           → 响应 inventoryChanges 里把该 mixId +1
所以「送附件」= 往 inventory.items[] 里加 { mixId, amount: 1 }，和武器注入同一条路。

用法：
  python tools/attach_items.py --catalog D:/mod/out/gwe/<items>.json \
      --weapon 0x45323D4A --out runtime/inventory_attach_inject.json [--enable] [--list]
"""
import argparse, json, sys
from pathlib import Path


def load_rows(path):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = doc if isinstance(doc, list) else (doc.get("items") or doc.get("data") or [])
    return [r for r in rows if isinstance(r, dict)]


def attachment_rows(rows):
    out = []
    for r in rows:
        try:
            if r.get("parentId") and int(r.get("progressionCategory") or 0) == 2:
                out.append({"itemId": int(r["itemId"]), "parentId": int(r["parentId"]),
                            "mixId": int(r["mixId"])})
        except (KeyError, TypeError, ValueError):
            continue
    return out


def owned_mixids(inventory_path):
    doc = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    return {int(i["mixId"]) for i in (doc.get("items") or []) if isinstance(i, dict)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True, help="api/Progression/items 抓包")
    ap.add_argument("--weapon", required=True, help="武器 mixId，十六进制(0x..)或十进制")
    ap.add_argument("--inventory", help="可选：已有 inventory 抓包，用于跳过已拥有的行")
    ap.add_argument("--out", required=True)
    ap.add_argument("--enable", action="store_true", help="直接写 enabled: true")
    ap.add_argument("--list", action="store_true", help="只打印不写文件")
    a = ap.parse_args()

    w = int(a.weapon, 16) if a.weapon.lower().startswith("0x") else int(a.weapon)
    rows = [r for r in attachment_rows(load_rows(a.catalog)) if r["parentId"] == w]
    if not rows:
        print("没有该武器的附件行：0x%08X" % w, file=sys.stderr)
        return 1
    owned = owned_mixids(a.inventory) if a.inventory else set()
    todo = [r for r in rows if r["mixId"] not in owned]

    print("武器 0x%08X：附件行 %d，已拥有 %d，待注入 %d"
          % (w, len(rows), len(rows) - len(todo), len(todo)))
    if a.list:
        for r in todo:
            print("  0x%08X  mixId=%d" % (r["itemId"], r["mixId"]))
        return 0

    doc = {"enabled": bool(a.enable),
           "_note": "附件解锁注入：武器 0x%08X 的 %d 条未拥有附件；由 tools/attach_items.py 生成"
                    % (w, len(todo)),
           "weapon": w,
           "items": [{"mixId": r["mixId"], "amount": 1, "isDiscovered": False} for r in todo]}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("写入 %s（enabled=%s）" % (a.out, doc["enabled"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
