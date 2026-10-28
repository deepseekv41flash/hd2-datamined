#!/usr/bin/env python3
"""未发布内容盘点：本 build 的战备表/实体表 × SHODAN 4.1.0 名称表 × 本地 wiki 镜像。

四路输入（全部本地、只读）：

  1. `generated_stratagem_settings.dl_bin` 的 153 行 —— 通过 `tools/stratagem_extra.py --show` 拿到
     行号 `#` 与表内 id，再用 `refs/stratagem-display-names.json` 取内部名与 name_id/upper_id。
  2. `refs/strings-en-26088801.json` —— 本 build 的英文 locid 表，用来判定某行到底有没有名字。
  3. `refs/entity-locid-names.json` 的 `entity_index` —— `generated_entities.dl_bin` 里 1939 个实体，
     其中 219 个带 loadout_type（可装备）。
  4. 本地 wiki 镜像：
       `wiki/index.json`              370 页 + 分类（2026-09-30）
       `refs/wiki/cat_*.json`         分类成员（2026-10-22）
       `refs/wiki/pages/*.wikitext`   764 页原始 wikitext，`{{Infobox ...}}` 的 `source` 字段是
                                      wiki 自己给的「怎么获得」——`N/A` 就是「游戏里有、但不提供」。
  5. SHODAN Stat Editor 4.1.0 `stat_editor.lua` —— 3480 条 EN→ZH 名称对，外加决定性的
     `settings.UNLOCKS`（作者注释："items the game has but does not offer"）。

判定：
  * `released`         wiki 里有页面，且 infobox 的 source 不是 N/A
  * `unobtainable`     wiki 有页面但 source = N/A（例：M-104 Incinerator FRV）
  * `no-wiki`          wiki 里一页都没有（正文全文也搜不到）
  * `no-name`          name_id 与 upper_id 在本 build 的字符串表里都不存在 —— 真无名行

用法：
    python tools/unreleased_inventory.py                 # 打印报告
    python tools/unreleased_inventory.py --json-out out/unreleased/inventory-26088801.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MOD = REPO.parent.parent                      # D:/mod
REFS = MOD / "refs"
WIKI = MOD / "wiki"
WIKI_REFS = REFS / "wiki"
SHODAN = MOD / "recon/shodan-stat-editor/v4.1.0/SHODAN Stat Editor Offline/app/stat_editor.lua"

# ---------------------------------------------------------------- helpers
DESIG_RE = re.compile(r"^(?:[A-Z0-9]{1,4}/)?[A-Z0-9]{1,5}-\d{1,4}[A-Za-z]{0,3}\s+")
NON_ITEM_PAGES = {"Stratagems", "Weapons", "Weapons/zh-tw", "Damage Comparison", "Equipment Traits",
                  "Exosuit (disambiguation)", "FRV (disambiguation)", "Mines (disambiguation)"}


def norm(s: str) -> str:
    """lowercase / drop parentheticals, quoted qualifiers, punctuation"""
    if not s:
        return ""
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r'"[^"]*"', " ", s)
    s = s.split("#")[0].lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- 1. stratagem rows
def stratagem_rows():
    """153 rows with their table id, internal name and locid resolution"""
    out = subprocess.run([sys.executable, str(REPO / "tools/stratagem_extra.py"), "--show"],
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise SystemExit(f"stratagem_extra.py --show failed: {out.stderr[-400:]}")
    id_of = {}
    for line in out.stdout.splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) < 2:
            continue
        try:
            id_of[int(parts[0])] = int(parts[1])
        except ValueError:
            continue
    rows = load_json(REFS / "stratagem-display-names.json")["rows"]
    strings = load_json(REFS / "strings-en-26088801.json")
    result = []
    for idx, r in enumerate(rows):
        nid, uid = r.get("name_id"), r.get("upper_id")
        name = strings.get(str(nid)) if nid else None
        upper = strings.get(str(uid)) if uid else None
        result.append({
            "row": idx,
            "id": id_of.get(idx),
            "internal": r["internal_name"],
            "name_id": nid, "upper_id": uid,
            "name_en": name, "upper_en": upper,
            "has_name": bool(name or upper),
            "display": name or upper or "",
        })
    return result


# ---------------------------------------------------------------- 2. wiki mirror
INFOBOX = re.compile(r"\{\{\s*Infobox\s+([A-Za-z ]+)", re.I)
FIELD = re.compile(r"^\s*\|\s*([a-z_0-9]+)\s*=\s*(.*)$")


def _infobox(text):
    m = INFOBOX.search(text)
    if not m:
        return None, {}
    kind = m.group(1).strip()
    depth, i = 0, m.start()
    while i < len(text) - 1:
        if text[i:i + 2] == "{{":
            depth += 1
            i += 2
        elif text[i:i + 2] == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                break
        else:
            i += 1
    fields = {}
    for line in text[m.start():i].splitlines():
        fm = FIELD.match(line)
        if fm:
            fields[fm.group(1)] = fm.group(2).strip()
    return kind, fields


def _clean(v: str) -> str:
    v = re.sub(r"<ref.*?(/>|</ref>)", "", v, flags=re.S)
    v = re.sub(r"\{\{[^}]*\}\}", "", v)
    v = re.sub(r"<!--.*?-->", "", v, flags=re.S)
    return v.strip()


def wiki_pages():
    """{norm(title): page record} for the wikitext mirror, plus full-text index"""
    pages = {}
    for p in sorted((WIKI_REFS / "pages").glob("*.wikitext")):
        text = p.read_text(encoding="utf-8", errors="replace")
        kind, fields = _infobox(text)
        title = _clean(fields.get("title", "")) or p.stem
        source = _clean(fields.get("source", ""))
        rec = {
            "page": p.stem, "title": title, "infobox": kind, "source": source,
            "type": _clean(fields.get("stratagem_type", "")) or _clean(fields.get("type", "")),
            "permit_type": _clean(fields.get("permit_type", "")),
            "obtainable": True if source and source.upper() not in ("N/A", "TBA", "UNKNOWN")
                          else (False if source.upper() == "N/A" else None),
            "text": text,
        }
        pages.setdefault(norm(title), rec)
        pages.setdefault(norm(p.stem), rec)
    return pages


def wiki_index_titles():
    """titles the wiki knows at all (page cache + category members)"""
    rel = {}
    for p in load_json(WIKI / "index.json"):
        rel.setdefault(norm(p["title"]), (p["title"], f"index/{p.get('category')}"))
    for fn, tag in (("cat_stratagems.json", "cat/Stratagems"), ("cat_weapons.json", "cat/Weapons")):
        for m in load_json(WIKI_REFS / fn)["query"]["categorymembers"]:
            if m["ns"] == 0 and m["title"] not in NON_ITEM_PAGES:
                rel.setdefault(norm(m["title"]), (m["title"], tag))
    return rel


def match_wiki(name, rel, pages):
    """(title, method, obtainable) for a display name against the wiki mirror"""
    n = norm(name)
    if not n:
        return None, None, None
    for key in (n, norm(DESIG_RE.sub("", name))):
        if key and key in rel:
            title = rel[key][0]
            rec = pages.get(norm(title))
            return title, "exact", (rec["obtainable"] if rec else None)
    for key, (title, _src) in rel.items():
        if key.endswith(" " + n):
            rec = pages.get(norm(title))
            return title, "suffix", (rec["obtainable"] if rec else None)
    return None, None, None


# ---------------------------------------------------------------- 3. SHODAN
_ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", "'": "'", '"': '"'}
RE_EXACT = re.compile(r"^\s*\[\s*'(.*?)'\s*\]\s*=\s*'(.*?)'\s*,?\s*$")
RE_PAIR = re.compile(r"^\s*\{\s*'(.*?)'\s*,\s*'(.*?)'\s*\}\s*,\s*$")


def _unescape(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append(_ESCAPES.get(s[i + 1], "\\" + s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def shodan_dictionary():
    """EN -> ZH name pairs out of the zh-Hans language block"""
    lines = SHODAN.read_text(encoding="utf-8", errors="replace").splitlines()
    pairs, seen = [], set()
    for n in range(734, min(4275, len(lines))):
        line = lines[n]
        m = RE_EXACT.match(line) or RE_PAIR.match(line)
        if not m:
            continue
        en, zh = _unescape(m.group(1)), _unescape(m.group(2))
        if en == zh or en in seen:
            continue
        seen.add(en)
        pairs.append({"en": en, "zh": zh, "line": n + 1})
    return pairs


def shodan_unlocks():
    """settings.UNLOCKS -- the author's list of "items the game has but does not offer" """
    text = SHODAN.read_text(encoding="utf-8", errors="replace")
    block = text.split("settings.UNLOCKS", 1)[-1].split("settings.unlocks", 1)[0]
    out = []
    for m in re.finditer(r"\{ id = '([a-z_0-9]+)', name = '([^']+)', config = '([^']+)',(.*?)\},",
                         block, re.S):
        tail = " ".join(m.group(4).split())
        out.append({"id": m.group(1), "name": m.group(2), "config": m.group(3), "spec": tail})
    return out


# ---------------------------------------------------------------- 4. entities
ITEM_KINDS = {"primary_weapon", "support_weapon", "backpack", "sidearm", "throwable", "vehicle",
              "other_item"}
# entity names that are sub-components, not standalone items
COMPONENT_RE = re.compile(r"\bBackpack\b|^BACKPACK$|Targeting Remote$|Container$|^Cargo Truck$")


def entities():
    ei = load_json(REFS / "entity-locid-names.json")
    out = []
    for e in ei["entity_index"]:
        kind = e.get("kind")
        if kind not in ITEM_KINDS:
            continue
        code = (e.get("code") or "").strip()
        name = (e.get("name") or "").strip()
        out.append({
            "key": e.get("key"), "kind": kind, "code": code, "name": name,
            "display": f"{code} {name}".strip() if code else name,
            "loadout_type": e.get("loadout_type"), "tags": e.get("loadout_tags"),
            "component": bool(COMPONENT_RE.search(name)),
        })
    return out


# ---------------------------------------------------------------- 5. assemble
def build():
    rows = stratagem_rows()
    pages = wiki_pages()
    rel = wiki_index_titles()
    ents = entities()
    pairs = shodan_dictionary()
    unlocks = shodan_unlocks()
    shodan_norm = {norm(p["en"]): p for p in pairs}
    unlock_names = {norm(u["name"]) for u in unlocks}

    # stratagem rows
    for r in rows:
        disp = r["display"] or ""
        title, meth, obtain = match_wiki(disp, rel, pages)
        if not title:
            tail = r["internal"].split(".", 1)[-1].strip() if "." in r["internal"] else ""
            title, meth, obtain = match_wiki(tail, rel, pages)
        r["wiki_title"] = title
        r["wiki_match"] = meth
        r["obtainable"] = obtain
        r["player_facing"] = not r["internal"].upper().startswith(
            ("MISSIONS.", "MISSIONS CLAN STATION.", "TANK.", "[TUTORIAL]", "TUTORIAL"))
        r["shodan"] = shodan_norm.get(norm(disp)) or shodan_norm.get(norm(r["display"]))
        if not title:
            r["verdict"] = "no-name" if not r["has_name"] else "no-wiki"
        elif obtain is False:
            r["verdict"] = "unobtainable"
        else:
            r["verdict"] = "released"

    # equipment entities
    for e in ents:
        title, meth, obtain = match_wiki(e["display"], rel, pages)
        if not title:
            title, meth, obtain = match_wiki(e["name"], rel, pages)
        e["wiki_title"], e["wiki_match"], e["obtainable"] = title, meth, obtain
        e["shodan"] = (shodan_norm.get(norm(e["display"])) or shodan_norm.get(norm(e["name"])) or {}).get("en")
        e["shodan_unlock"] = norm(e["display"]) in unlock_names
        e["verdict"] = ("released" if title and obtain is not False else
                        "unobtainable" if obtain is False else "no-wiki")
        # placeholder-named entities are SEAF / AI-run copies of a player item, not new content
        e["placeholder"] = e["name"] in ("", "未知", "Unknown")
        # full-text: does any wiki page body mention it?
        e["wiki_mention"] = bool(title is None and len(e["name"]) > 3 and
                                 any(e["name"].lower() in p["text"].lower()
                                     for p in pages.values() if p))

    summary = {
        "stratagem_rows": len(rows),
        "player_facing_unreleased": sum(1 for r in rows if r["player_facing"] and r["verdict"] in
                                        ("no-wiki", "no-name", "unobtainable")),
        "rows_no_name": sum(1 for r in rows if r["verdict"] == "no-name"),
        "equipment_entities": len(ents),
        "equipment_no_wiki": sum(1 for e in ents if e["verdict"] == "no-wiki"),
        "equipment_no_wiki_real": sum(1 for e in ents if e["verdict"] == "no-wiki"
                                      and not e["component"] and not e["placeholder"]),
        "shodan_pairs": len(pairs),
        "shodan_unlocks": len(unlocks),
        "wiki_pages_parsed": len({p['page'] for p in pages.values() if p}),
    }
    return {"build": load_json(REFS / "entity-locid-names.json")["build"],
            "summary": summary, "stratagem_rows": rows, "equipment": ents,
            "shodan_unlocks": unlocks,
            "shodan_pairs": pairs}


def report(data):
    L = []
    A = L.append
    s = data["summary"]
    A("=" * 104)
    A(f"未发布内容盘点  build {data['build']}")
    A("=" * 104)
    for k, v in s.items():
        A(f"  {k:28} {v}")
    A("")
    A("--- 玩家向、未发布的战备行 ---")
    for r in data["stratagem_rows"]:
        if r["player_facing"] and r["verdict"] in ("no-wiki", "no-name", "unobtainable"):
            A(f"  id={r['id']:>4} row#{r['row']:>3} {r['internal'][:46]:46} "
              f"display={r['display'] or '(无名)':34} {r['verdict']:12} wiki={r['wiki_title']}")
    A("")
    A("--- 无名字行（name_id 与 upper_id 都不在本 build 字符串表）---")
    for r in data["stratagem_rows"]:
        if r["verdict"] == "no-name":
            A(f"  id={r['id']:>4} row#{r['row']:>3} {r['internal']}")
    A("")
    A("--- 实体层：build 有、wiki 无（已排除子部件）---")
    for e in data["equipment"]:
        if e["verdict"] == "no-wiki" and not e["component"] and not e["placeholder"]:
            A(f"  {e['display']:34} kind={e['kind']:15} key={e['key']} tags={e['tags']}"
              f"{'  <== SHODAN unlocks' if e['shodan_unlock'] else ''}"
              f"{'  (正文有提及)' if e['wiki_mention'] else ''}")
    A("")
    A("--- SHODAN settings.UNLOCKS（游戏有、不提供）---")
    for u in data["shodan_unlocks"]:
        A(f"  {u['name']:28} config={u['config']:18} {u['spec'][:90]}")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out", default="")
    a = ap.parse_args()
    data = build()
    print(report(data))
    if a.json_out:
        p = Path(a.json_out)
        if not p.is_absolute():
            p = REPO / p
        p.parent.mkdir(parents=True, exist_ok=True)
        slim = {k: v for k, v in data.items() if k != "shodan_pairs"}
        slim["shodan_pairs_count"] = len(data["shodan_pairs"])
        slean = json.dumps(slim, ensure_ascii=False, indent=1)
        # drop the bulky wikitext bodies before writing
        p.write_text(rean := re.sub(r'\s*"text": ".*?(?<!\\)"', ' "text_len": 0', slean, flags=re.S),
                     encoding="utf-8")
        print(f"\n-> {p}")


if __name__ == "__main__":
    main()
