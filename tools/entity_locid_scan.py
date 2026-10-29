#!/usr/bin/env python3
"""entity_locid_scan.py -- 在 `generated_entities.dl_bin` 里定位本地化 ID（locid）字段，产出「实体 → 游戏内名字」。

背景：为什么实体表需要单独一套工具
    `table_locid_scan.py` 面对的是「一张表 = 若干组、组内定长行数组」的 `generated_*.dl_bin`。
    实体库不是那种形状：它是 **275 个块**，每个块 = 一种组件类型，块内是
    `[ComponentIndexData 哈希图][行数组][可选尾数组]`。哈希图是
    `{u64 资源哈希, u32 行号, u32 pad}` 16 B 一条的开放寻址表，键 = `Murmur64A(资源路径)`。所以：

      * 没有「整张表一个 step」可以套 —— 每个块的行结构都不一样；
      * 但**块内**行数组是定长的，行结构由 `dl_library.dl_typelib` 给出
        （容器成员的 `ComponentIndexData` 给出哈希图大小，结构化成员给出行类型与行数）。

    这轮的关键发现就是这两个事实合起来够用：**先按块拆出（哈希图, 行数组, 行大小, 行数），
    再按 (块, 行内偏移) 聚合扫 4 字节槽**，判据与 `docs/LOCID-NAMES-25988413.md` 完全一致。

判据（照抄那套统计，不靠"看起来像"）
    `.strings` 里英文 18 个 blob / 24,834 条 ID → 随机 u32 命中概率 5.782e-6。
    一列 N 行的期望误报是 N × 5.782e-6（675 行 → 0.0039 次），所以「几十上百行命中」
    不可能是巧合。反过来也认：命中数够但去重数低（如 Interactable 的 'INTERACT' 562 行只有
    10 个去重），说明它是**共享 UI 文本**而不是名字字段 —— 本工具据此把它们归到
    `other_text_fields`，不进名字表。

    全表实测（本 build）：4 字节对齐窗口 11,814,849 个 → 命中 17,500 / 去重 2,124，
    随机期望 68.3，富集 256 倍；加上 3 种非 4 对齐窗口共 17,516（多出来的 16 个见 §块 0）。

三种块形态（都会遇到，必须都认）
    * 常规组件块（265 个）：payload = `[ComponentIndexData][行数组][0..7 B 8 对齐尾垫]`
    * 原生数组块（7 个）：行类型是原生类型（record_size 1），成员 size 就是行数
      （Backpack / Destructible / StaticPosition / OrbitalShip / LandingZoneBeacon / AiCover / Commander）
    * 带尾数组的块（1 个）：`LoadoutEntryComponentData` = `[6368 B 哈希图][199 行 × 32 B][796 B
      = 199×u32 原生数组 + 4 B 垫]`。行数必须取**成员自己的 size**（6368/32=199），
      不能用 `(payload-哈希图)//stride` —— 后者会算成 224 行（踩过的坑）。

块 0（EntitySettingsHashmap）里那 33 个「行数组外」命中
    17 个 4 对齐 + 16 个偏移 2 对齐。4 对齐的那 1 个是条目字段 `a`（绝对偏移 149,196）的
    数值恰好等于某个 locid；16 个偏移 2 对齐的是尾部 u16 数组里同一对 u16 反复出现，
    拼成同一个 u32（0x007C006F）16 次。两者都是**结构性巧合**，不是字段：
    去重数 1、且不在任何行数组内。工具把它们单独计数（`census.outside_row_arrays`）而不是混进槽统计。

用法
    python tools/entity_locid_scan.py \
        --plaintext refs/dlbin/plaintext-26251122 \
        --typelib   refs/dlbin/plaintext-26251122/dl_library.dl_typelib \
        --strings   refs/strings-probe/all \
        --out       refs/entity-locid-names.json

    # 只看某个槽的原始行（排查用）
    python tools/entity_locid_scan.py --dump-slot 56:0

只读：本工具只读明文缓存与 typelib，不碰游戏目录、不启动游戏、不写任何 `data/game` 文件。
"""
from __future__ import annotations

import argparse
import array
import bisect
import json
import math
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from table_dictionary import Dictionary, load_names                     # noqa: E402
from table_locid_scan import load_strings                              # noqa: E402

BUILD = "26088801"
DEFAULT_PLAIN = "refs/dlbin/plaintext-26251122"
DEFAULT_NAMES = "dl-type-names.json"
DEFAULT_RESNAMES = "refs/srkit-names.json"
INDEX_TYPE = "ComponentIndexData"        # 块内哈希图的类型名（typelib 自带）
UNKNOWN_LABEL = "未知"                    # 查不到名字时的占位标签（用户口径）
LOADOUT_ENTRY_TYPE = 0x4F2CF417          # typelib 给的行数组 + 尾数组特例
ENTITY_HASHMAP_SLOTS = 4096              # 块 0：4096 槽 × 32 B
ENTITY_HASHMAP_BYTES = ENTITY_HASHMAP_SLOTS * 32

# ---------------------------------------------------------------- 语义槽位表
# 每一项都由本工具的 census 输出支撑（命中数/去重数写进注释），不是猜的。
NAME_FIELDS = {
    # 675 行 × 56 B（块 56）。命中数/去重数（24,834 个 ID 的语料）：
    #   +0   609/675 命中 344 去重  'Liberator' / 'Bug Hole' / 'Terminal'   <- 单数名
    #   +4   179/675 命中  91 去重  'Bug Holes' / 'Troopers'                <- 复数名
    #   +8   495/675 命中 326 去重  'LIBERATOR' / 'BUG HOLE'                <- 大写名
    #   +20  217/675 命中 191 去重  长描述（不导出，用户要求只发名字）
    #   +36  211/675 命中 185 去重  'AR-23' / 'G-13' / 'M-105'             <- 物品代码
    #   +40   80/675 命中  30 去重  'NOT YET IMPLEMENTED' 等实现状态标记
    # 交叉验证：AR-23 的实体键 0x968211C0033DCE64 在这一块的行 561 → 'Liberator' / 'LIBERATOR' / 'AR-23'，
    # 与游戏内 AR-23「Liberator」逐字一致；'Charger' 的实体路径是 cha_charger、'Shrieker' 是 cha_shrieker。
    "EncyclopediaEntryComponentData": [
        (0, "name", True),
        (4, "name_plural", True),
        (8, "name_upper", True),
        (20, "description", False),
        (36, "code", True),
        (40, "implementation_note", False),
    ],
}
# LoadoutEntry（块 23）：199 行 × 32 B。+12 起是 `equipment_tags[5]`，**存的是标签名的 locid**
# 不是枚举值：+12 命中 139、+16 99、+20 42、+24 9、+28 1（共 290）。标签是通用名
# （'ANTI-TANK' / 'EXPLOSIVE' / 'ROUNDS RELOAD' / 'ONE HANDED' …），15~17 个去重。
LOADOUT_TAG_OFFSET = 12
LOADOUT_TAG_COUNT = 5
LOADOUT_TYPE_OFFSET = 4

# 其余「有 locid 但不是实体名」的槽：按容器给语义标签，只进 other_text_fields（不导出逐行文本）。
# 这些槽的命中/覆盖由 census 实测，见 docs/ENTITY-LOCID-26088801.md 的分块表。
TEXT_ROLES = {
    "InteractableComponentData": "interact_prompt",          # 562 行 18 槽，1~30 去重：'INTERACT'/'RELOAD'
    "InteractableMinigameComponentData": "hud_text",          # 76 行 118 槽，1~4 去重：HUD 提示
    "ObjectiveComponentData": "objective_text",               # 217 行 6 槽，+280 110/217，74 去重
    "ObjectiveCarryComponentData": "objective_text",          # 40 行 2 槽
    "ObjectiveSecureAreaComponentData": "objective_text",     # 5 行 3 槽
    "StoryInteractableComponentData": "story_text",           # 60 行 8 槽：海报标题/说明
    "CharacterNameComponentData": "character_label",          # 91 行 2 槽：'Civilian'/'SEAF Soldier'
    "HellpodRackComponentData": "stratagem_label",            # 73 行 +528：'RESUPPLY'/'JUMP PACK'
    "ShowOnMapComponentData": "map_label",                    # 26 行 +36：'Colony' 等地图标签
    "HealthComponentData": "status_text",                     # 507 行 +21996.. 3 槽：'Silo Status: …'
    "InteractableStateSwitchComponentData": "hud_text",       # 25 行 5 槽：'>> BLOCKED <<'
    "MinigameExternalSwitchesComponentData": "hud_text",      # 21 行 3 槽
    "UploadDiscoveryComponentData": "hud_text",               # 11 行 1 槽
    "WeaponDataComponentData": "caliber_label",               # 374 行 +176/+180 各 3 命中：'12MM'/'FLAMMABLE'
}

# 实体分类规则：用于给「实体 → 名字」加一个 kind 标签，也用于报告的按类型分布。
# **不能用「有没有 WeaponData」当武器判据**：实测 Gazer / Bile Titan / Caustic Spewer 这些
# 敌人也挂 WeaponDataComponentData（它们的攻击算武器），会把 148 个敌人误判成武器。
# 真正的武器判据是 LoadoutEntry 的 item_type（1=主武器 2=支援武器 3=副武器 4=投掷 6=背包）。
LOADOUT_ITEM_KINDS = {1: "primary_weapon", 2: "support_weapon", 3: "sidearm",
                      4: "throwable", 5: "other_item", 6: "backpack"}
KIND_RULES = [
    ("vehicle", ("VehicleComponentData",)),
    ("enemy", ("AiEnemyComponentData", "EnemyPackageComponentData")),
    ("objective", ("ObjectiveComponentData",)),
    ("interactable", ("InteractableComponentData",)),
    ("unit", ("UnitComponentData",)),
]


# ---------------------------------------------------------------- 容器解析
def parse_blocks(plain: bytes) -> list[dict]:
    """块序列：`u32 type | 'LDLD' | u32 ver | u32 type | u32 payload | u8 wide | 7 reserved`（28 B）。

    校验 version==1、内外 type 一致、payload 不越界；块之间偶尔有 4 字节对齐空当（实测 4 B）。
    """
    out, pos = [], 0
    while True:
        at = plain.find(b"LDLD", pos)
        if at < 0:
            return out
        head = at - 4
        if head < 0:
            pos = at + 4
            continue
        type_id = struct.unpack_from("<I", plain, head)[0]
        version, inner, payload = struct.unpack_from("<III", plain, at + 4)
        if version != 1 or inner != type_id or head + 28 + payload > len(plain):
            pos = at + 4
            continue
        out.append({"head": head, "type_id": type_id, "payload": payload,
                    "payload_at": head + 28})
        pos = head + 28 + payload


def geometry(dic: Dictionary, block: dict) -> dict | None:
    """把一个块拆成 (哈希图, 行数组, 行大小, 行数)。三种形态见模块 docstring。

    行数取**结构化成员自己的 size // stride**，不是 `(payload - 哈希图) // stride`：
    后者会把行数组后面的原生尾数组也算成行（LoadoutEntry 会从 199 行算成 224 行）。
    """
    tid = block["type_id"]
    try:
        members = dic.members(tid)
    except Exception:                                              # noqa: BLE001
        return None
    index = [m for m in members if m["type"] == INDEX_TYPE]
    if not index:
        return None
    index_member = index[0]
    others = [m for m in members if m is not index_member]
    structured = [m for m in others if (m["record_size"] or 0) > 1]
    if structured:
        row = structured[0]
        stride = row["record_size"]
        return {"index_offset": index_member["offset"], "index_size": index_member["size"],
                "rows": row["size"] // stride, "stride": stride,
                "row_type": dic.name(row["type_id"]), "layout": "typelib"}
    if others:                       # 原生（bool / u8）数组块：stride 1，成员 size = 行数
        row = max(others, key=lambda m: m["size"])
        return {"index_offset": index_member["offset"], "index_size": index_member["size"],
                "rows": row["size"], "stride": 1,
                "row_type": f"{row['type']}<native>", "layout": "native-array"}
    if tid == LOADOUT_ENTRY_TYPE:    # 兜底：typelib 完全没描述行数组时的手工几何
        return {"index_offset": index_member["offset"], "index_size": index_member["size"],
                "rows": (block["payload"] - index_member["size"]) // 32, "stride": 32,
                "row_type": "LoadoutEntryComponent(手工几何)", "layout": "manual"}
    return None


def check_geometry(plain: bytes, block: dict, geo: dict) -> dict:
    """用哈希图自证几何：行号必须 < 行数、pad 必须为 0、空槽必须全零、行数组不越界。

    这条自证很重要：typelib 是剥离过的（没有类型名字符串），容器成员大小一旦与本 build
    漂移，行数组就会切错，后面所有命中统计都不可信。所以几何必须过这一关才参与扫描。
    实测 273 个可拆块全部通过（块 14 的哈希图是空的，键数 0 —— 允许）。
    """
    slots = geo["index_size"] // 16
    rows = geo["rows"]
    used, max_value, bad_pad, bad_empty = 0, -1, 0, 0
    for s in range(slots):
        key, value, pad = struct.unpack_from(
            "<QII", plain, block["payload_at"] + geo["index_offset"] + 16 * s)
        if key:
            used += 1
            max_value = max(max_value, value)
            if pad:
                bad_pad += 1
        elif value or pad:
            bad_empty += 1
    tail = block["payload"] - geo["index_size"] - rows * geo["stride"]
    geo = dict(geo)
    geo.update({"slots": slots, "keys": used, "max_row": max_value, "tail": tail,
                "bad_pad": bad_pad, "bad_empty": bad_empty})
    geo["ok"] = (used <= rows and -1 <= max_value < rows and not bad_pad and not bad_empty
                 and 0 <= tail)
    return geo


def entity_index(plain: bytes) -> dict:
    """块 0 = EntitySettingsHashmap：4096 槽 × 32 B `{u64 键, u64 组件表偏移, u64 组件数, u32}`。

    尾部（131,072 之后）= `u16` 数组，按条目的 (偏移, 组件数) 切片（组件总数 27,050 =
    54,100 B / 2，与尾部长度逐字节吻合）。⚠ 这些 u16 不是块序号（实测最大 65535、1359 个
    实体越界），是引擎侧组件类型索引；本工具只用它算「实体总数」与「组件引用总数」。
    """
    if len(plain) < 28 + ENTITY_HASHMAP_BYTES:
        return {"slots": ENTITY_HASHMAP_SLOTS, "used": 0, "keys": set(),
                "component_refs": 0}
    used, refs = {}, 0
    for s in range(ENTITY_HASHMAP_SLOTS):
        key, offset, count, misc = struct.unpack_from("<QQQI", plain, 28 + 32 * s)
        if not key:
            continue
        used[key] = {"offset": offset, "count": count, "misc": misc}
        refs += count
    return {"slots": ENTITY_HASHMAP_SLOTS, "used": len(used), "keys": set(used),
            "component_refs": refs}


def hashmap(plain: bytes, block: dict, geo: dict) -> dict[int, int]:
    """块的 ComponentIndexData：键（资源路径 Murmur64A）→ 行号。空槽 = 全零。"""
    out = {}
    for s in range(geo["index_size"] // 16):
        key, value, _pad = struct.unpack_from(
            "<QII", plain, block["payload_at"] + geo["index_offset"] + 16 * s)
        if key:
            out[key] = value
    return out


# ---------------------------------------------------------------- 扫描
def census(plain: bytes, ids: dict[int, str], blocks: list[dict],
           geos: dict[int, dict], alignments: int = 4) -> dict:
    """全文件 4 字节窗口的 locid 命中，归因到 (块, 行内偏移)。

    为什么要扫 4 个对齐：块起点都是 4 对齐，行内字段可能是 +1/+2/+3（结构里有 bool/u8/u16），
    只扫 4 对齐会把它们漏掉。实测非 4 对齐命中 16 个、低于随机期望（68.3/4=17.1 × 3 组），
    说明真正的 locid 字段都是 4 对齐的 —— 但工具仍然扫全 4 种，把这件事变成可复核的数字。
    """
    starts = [b["head"] for b in blocks]
    slots: dict[tuple[int, int], dict] = {}
    outside: dict[int, int] = {}
    per_shift, distinct = [], set()
    for shift in range(alignments):
        usable = (len(plain) - shift) // 4
        words = array.array("I")
        words.frombytes(plain[shift:shift + usable * 4])
        hits_here = 0
        for i, value in enumerate(words):
            text = ids.get(value)
            if text is None:
                continue
            hits_here += 1
            distinct.add(value)
            pos = shift + 4 * i
            block_no = bisect.bisect_right(starts, pos) - 1
            geo = geos.get(block_no)
            if geo is None:
                outside[block_no] = outside.get(block_no, 0) + 1
                continue
            rel = pos - (blocks[block_no]["payload_at"] + geo["index_size"])
            if rel < 0:
                outside[block_no] = outside.get(block_no, 0) + 1
                continue
            row, offset = divmod(rel, geo["stride"])
            if row >= geo["rows"] or offset + 4 > geo["stride"]:
                outside[block_no] = outside.get(block_no, 0) + 1
                continue
            slot = slots.setdefault((block_no, offset), {"hits": 0, "texts": {}, "rows": set()})
            slot["hits"] += 1
            slot["texts"][text] = slot["texts"].get(text, 0) + 1
            slot["rows"].add(row)
        per_shift.append(hits_here)
    return {"slots": slots, "outside": outside, "hits": sum(per_shift),
            "distinct_ids": len(distinct), "per_shift": per_shift}


def poisson_tail_text(hits: int, lam: float) -> str:
    """P(X >= hits)，X~Poisson(lam)：命中数相对随机期望的显著性。

    lam = 行数 × 5.78e-6，很小；命中数一大，真实 p 小到 float 表示不了（609 命中时
    log10 p ≈ -2850）。所以先用 Poisson 尾部的对数形式算量级：
        log10 P(X>=n) ≈ n·log10(lam) − log10(n!)
    量级 < -20 时直接给 `1e-XXXX`，否则回退到数值法。
    """
    if lam <= 0 or hits <= 0:
        return "1"
    log10_p = hits * math.log10(lam) - math.lgamma(hits + 1) / math.log(10)
    if log10_p < -20:
        return f"1e{log10_p:.0f}"
    term = math.exp(-lam)                     # 数值法：p = 1 - P(X <= n-1)
    cdf = term
    for k in range(1, hits):
        term *= lam / k
        cdf += term
        if cdf >= 1.0:
            return "<1e-300"
    p = max(0.0, 1.0 - cdf)
    return f"{p:.1e}" if p > 0 else "<1e-300"


def slot_table(dic: Dictionary, ids: dict[int, str], blocks: list[dict],
               geos: dict[int, dict], cen: dict, min_hits: int) -> list[dict]:
    """把 census 的槽摊平成可排序的表，附覆盖率、随机期望、显著性、样本文本。"""
    out = []
    for (block_no, offset), slot in cen["slots"].items():
        hits = slot["hits"]
        if hits < min_hits:
            continue
        geo = geos[block_no]
        rows = geo["rows"]
        expected = rows * len(ids) / 2 ** 32
        samples = [t[:70] for t, _c in sorted(slot["texts"].items(), key=lambda kv: -kv[1])[:5]]
        out.append({
            "block": block_no,
            "container": name_of(dic, blocks[block_no]["type_id"]),
            "row_type": geo["row_type"],
            "stride": geo["stride"],
            "rows": rows,
            "offset": offset,
            "hits": hits,
            "distinct": len(slot["texts"]),
            "coverage": hits / rows if rows else 0.0,
            "random_expectation": expected,
            "p_value": poisson_tail_text(hits, expected),
            "samples": samples,
        })
    out.sort(key=lambda r: (-r["hits"], r["block"], r["offset"]))
    return out


_name_cache: dict[int, str] = {}


def name_of(dic: Dictionary, tid: int) -> str:
    if tid not in _name_cache:
        _name_cache[tid] = dic.name(tid)
    return _name_cache[tid]


def component_membership(plain: bytes, blocks: list[dict], geos: dict[int, dict],
                         dic: Dictionary) -> dict[str, set[int]]:
    """组件名 → 拥有该组件的实体键集合（每个块的哈希图就是一份隶属表）。"""
    out = {}
    for i, block in enumerate(blocks):
        geo = geos.get(i)
        if geo is None or not geo["keys"]:
            continue
        out[name_of(dic, block["type_id"])] = set(hashmap(plain, block, geo))
    return out


def classify(key: int, membership: dict[str, set[int]],
             loadout_type: dict[int, int] | None = None) -> str:
    """给实体一个粗分类。

    武器/投掷物/背包走 LoadoutEntry 的 item_type（实测 199 条：1:59 2:46 3:28 4:27 5:3 6:36）；
    其余按组件隶属关系判：载具 / 敌人 / 目标 / 可交互物 / 单位 / 其它。
    ⚠ 不能用「有没有 WeaponDataComponentData」当武器判据：Gazer、Bile Titan、Caustic Spewer
    这些敌人都挂 WeaponData（它们的攻击算武器），会把 148 个敌人误判成武器。
    """
    if loadout_type and key in loadout_type:
        return LOADOUT_ITEM_KINDS.get(loadout_type[key], "item")
    for kind, components in KIND_RULES:
        if any(key in membership.get(c, ()) for c in components):
            return kind
    return "other"


# ---------------------------------------------------------------- 名字导出
PLACEHOLDER_PREFIX = ("sample", "temp ", "test", "[not", "not yet")


def encyclopedia_entries(plain: bytes, ids: dict[int, str], block: dict, geo: dict,
                         row_to_key: dict[int, int], res_names: dict[int, str],
                         membership: dict[str, set[int]],
                         loadout_type: dict[int, int]) -> tuple[list[dict], dict]:
    """块 56：一行一个百科条目 = 一个实体（行 ↔ 哈希图键）。导出名字，不导出描述。"""
    base = block["payload_at"] + geo["index_size"]
    stride = geo["stride"]
    coverage = {role: 0 for _o, role, _e in NAME_FIELDS["EncyclopediaEntryComponentData"]}
    entries, unnamed = [], []
    for row in range(geo["rows"]):
        at = base + row * stride
        values = {role: struct.unpack_from("<I", plain, at + offset)[0]
                  for offset, role, _e in NAME_FIELDS["EncyclopediaEntryComponentData"]}
        text = {role: ids.get(value, "") for role, value in values.items()}
        for role, value in text.items():
            coverage[role] += 1 if value else 0
        key = row_to_key.get(row)
        if not (text["name"] or text["name_upper"]):
            unnamed.append({"row": row, "key": f"0x{key:016X}" if key else None})
            continue
        name = text["name"] or text["name_upper"]
        entries.append({
            "row": row,
            "key": f"0x{key:016X}" if key else None,
            "name": name,
            "name_source": "name" if text["name"] else "name_upper",
            "name_slot": ("EncyclopediaEntryComponentData+0" if text["name"]
                          else "EncyclopediaEntryComponentData+8"),
            "name_upper": text["name_upper"] or ("" if not text["name"].isupper() else text["name"]),
            "name_plural": text["name_plural"],
            "code": text["code"],
            "quality": "placeholder" if name.lower().startswith(PLACEHOLDER_PREFIX) else "ok",
            "kind": classify(key, membership, loadout_type) if key else "other",
            "dev_name": res_names.get(key) if key else None,
        })
    return entries, {"coverage": coverage, "unnamed_rows": unnamed}


def loadout_entries(plain: bytes, ids: dict[int, str], block: dict, geo: dict,
                    row_to_key: dict[int, int], res_names: dict[int, str],
                    enc_by_key: dict[int, dict], membership: dict[str, set[int]],
                    loadout_type: dict[int, int]) -> list[dict]:
    """块 23：199 个 LoadoutEntry（装备条目）。导出装备类型 + 标签名（locid）+ 开发名。"""
    base = block["payload_at"] + geo["index_size"]
    stride = geo["stride"]
    out = []
    for row in range(geo["rows"]):
        at = base + row * stride
        item_type = struct.unpack_from("<I", plain, at + LOADOUT_TYPE_OFFSET)[0]
        tags = []
        for t in range(LOADOUT_TAG_COUNT):
            value = struct.unpack_from("<I", plain, at + LOADOUT_TAG_OFFSET + 4 * t)[0]
            label = ids.get(value)
            if label:
                tags.append(label)
        key = row_to_key.get(row)
        enc = enc_by_key.get(key or 0) or {}
        out.append({
            "row": row,
            "key": f"0x{key:016X}" if key else None,
            "item_type": item_type,
            "item_kind": LOADOUT_ITEM_KINDS.get(item_type, "item"),
            "tags": tags,
            "name": enc.get("name") or "",
            "name_slot": enc.get("name_slot"),
            "code": enc.get("code") or "",
            "tags_slot": f"LoadoutEntryComponentData+{LOADOUT_TAG_OFFSET}..+{LOADOUT_TAG_OFFSET + 4 * (LOADOUT_TAG_COUNT - 1)}",
            "kind": classify(key, membership, loadout_type) if key else "other",
            "dev_name": res_names.get(key) if key else None,
            "has_encyclopedia_entry": bool(enc),
        })
    return out


def loadout_types(plain: bytes, block: dict, geo: dict) -> dict[int, int]:
    """块 23 的「实体键 → item_type」：武器/投掷物/背包的分类依据。"""
    base = block["payload_at"] + geo["index_size"]
    stride = geo["stride"]
    row_to_key = {row: key for key, row in
                  hashmap(plain, block, geo).items()}
    out = {}
    for row, key in row_to_key.items():
        out[key] = struct.unpack_from("<I", plain, base + row * stride + LOADOUT_TYPE_OFFSET)[0]
    return out


def load_res_names(path: pathlib.Path | None) -> dict[int, str]:
    """srkit 资源清单：file_id(64 位) → 资源路径/开发名。键空间与实体哈希图一致（已抽查命中）。

    ⚠ 这不是本地化文本，只是「开发名/资源路径」。导出里字段名叫 dev_name 以示区别。
    清单里有大量未解析条目（名字就是 16 位十六进制本身），这些一律丢掉，免得被当成名字。
    """
    if not path or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out = {}
    for item in data:
        try:
            key = int(item["file_id_hex"], 16)
        except (KeyError, TypeError, ValueError):
            continue
        name = (item.get("name") or "").strip()
        if not name or (len(name) == 16 and all(c in "0123456789ABCDEF" for c in name)):
            continue
        out[key] = name
    return out


# ---------------------------------------------------------------- 主流程
def main() -> int:
    ap = argparse.ArgumentParser(description="实体库本地化 ID 字段定位 / 实体→名字映射")
    ap.add_argument("--plaintext", default=DEFAULT_PLAIN,
                    help="明文缓存目录（含 generated_entities.dl_bin）")
    ap.add_argument("--typelib", default=None, help="dl_library.dl_typelib（缺省用明文目录里那份）")
    ap.add_argument("--names", default=DEFAULT_NAMES, help="type_id → 类型名 json")
    ap.add_argument("--resnames", default=DEFAULT_RESNAMES, help="srkit 资源清单 json（可选）")
    ap.add_argument("--strings", action="append", default=None, help="解开的 .strings 目录（可重复）")
    ap.add_argument("--language", default="us")
    ap.add_argument("--min-hits", type=int, default=2, help="槽位最少命中数")
    ap.add_argument("--min-coverage", type=float, default=0.10,
                    help="other_text_fields 的最少覆盖率（过滤每块只有 2~3 命中的巧合槽）")
    ap.add_argument("--out", default=None, help="写 names-only JSON")
    ap.add_argument("--dump-slot", default="", metavar="BLOCK:OFFSET",
                    help="打印某个槽的全部命中行（排查用）")
    ap.add_argument("--all-slots", action="store_true", help="打印全部槽（默认只打印大命中）")
    a = ap.parse_args()

    base = pathlib.Path(a.plaintext)
    plain = (base / "generated_entities.dl_bin").read_bytes()
    typelib = pathlib.Path(a.typelib) if a.typelib else base / "dl_library.dl_typelib"
    dic = Dictionary(typelib.read_bytes(), load_names(pathlib.Path(a.names)))
    roots = [pathlib.Path(p) for p in (a.strings or ["refs/strings-probe/all"])]
    ids, stats = load_strings(roots, a.language)
    print(f"strings: {stats['blobs_used']}/{stats['blobs_scanned']} 个 {a.language!r} blob, "
          f"{stats['ids']} 个 ID")
    if not ids:
        print("没有 ID 语料，先解 .strings", file=sys.stderr)
        return 1
    print(f"entities: {len(plain):,} B, typelib {dic.lib.nt} 类型 / {dic.lib.nm} 成员")

    blocks = parse_blocks(plain)
    ents = entity_index(plain)
    print(f"块: {len(blocks)}  实体: {ents['used']}（{ents['slots']} 槽）  "
          f"组件引用: {ents['component_refs']}")

    geos, skipped, bad = {}, [], []
    for i, block in enumerate(blocks):
        geo = geometry(dic, block)
        if geo is None:
            skipped.append((i, name_of(dic, block["type_id"])))
            continue
        geos[i] = check_geometry(plain, block, geo)
        if not geos[i]["ok"]:
            bad.append(i)
    print(f"可拆块: {len(geos)}  不可拆: {len(skipped)} {skipped}  几何异常: {len(bad)} {bad}")

    cen = census(plain, ids, blocks, geos)
    windows = len(plain) // 4
    expected_all = windows * len(ids) / 2 ** 32
    print(f"census: 4 字节窗口 {windows:,}  命中 {cen['hits']:,}  去重 {cen['distinct_ids']:,}  "
          f"随机期望 {expected_all:.1f}  富集 {cen['hits'] / max(expected_all, 1e-9):.0f}×")
    inside = cen["hits"] - sum(cen["outside"].values())
    print(f"  行数组内 {inside:,}  行数组外 {sum(cen['outside'].values()):,} "
          f"{dict(sorted(cen['outside'].items()))}")
    print(f"  各对齐命中 {cen['per_shift']}（首项 4 对齐；其余 3 项随机期望各 "
          f"{expected_all / 4:.1f}）")

    rows = slot_table(dic, ids, blocks, geos, cen, a.min_hits)
    print(f"\n命中 ≥{a.min_hits} 的槽: {len(rows)} 个，分布在 "
          f"{len({r['block'] for r in rows})} 个块")
    print(f"{'blk':>3} {'container':<42} {'rows':>5} {'str':>5} {'off':>5} {'hits':>5} "
          f"{'uniq':>5} {'cov':>7} {'p':>9}  样本")
    for row in rows:
        if not a.all_slots and row["hits"] < 20 and row["coverage"] < 0.5:
            continue
        print(f"{row['block']:>3} {row['container'][:42]:<42} {row['rows']:>5} "
              f"{row['stride']:>5} {row['offset']:>5} {row['hits']:>5} {row['distinct']:>5} "
              f"{row['coverage'] * 100:>6.1f}% {row['p_value']:>10}  {row['samples'][:2]}")

    if a.dump_slot:
        block_no, offset = (int(x) for x in a.dump_slot.split(":"))
        geo = geos[block_no]
        start = blocks[block_no]["payload_at"] + geo["index_size"] + offset
        print(f"\n=== dump 块 {block_no} ({name_of(dic, blocks[block_no]['type_id'])}) +{offset} ===")
        for r in range(geo["rows"]):
            value = struct.unpack_from("<I", plain, start + r * geo["stride"])[0]
            text = ids.get(value)
            if text:
                print(f"  行 {r:>4} 0x{value:08X} {text!r}")
        return 0

    # ---- 名字导出
    res_names = load_res_names(pathlib.Path(a.resnames) if a.resnames else None)
    membership = component_membership(plain, blocks, geos, dic)
    slot_stats = {(r["block"], r["offset"]): r for r in rows}
    lo_block = next((i for i, b in enumerate(blocks)
                     if b["type_id"] == LOADOUT_ENTRY_TYPE), None)
    lo_types = loadout_types(plain, blocks[lo_block], geos[lo_block]) \
        if lo_block is not None and lo_block in geos else {}
    report = {
        "build": BUILD,
        "tool": "tools/entity_locid_scan.py",
        "source": {
            "plaintext": str(base / "generated_entities.dl_bin"),
            "plain_bytes": len(plain),
            "typelib": str(typelib),
            "strings": stats,
        },
        "census": {
            "blocks": len(blocks),
            "decomposed_blocks": len(geos),
            "u32_windows": windows,
            "hits": cen["hits"],
            "distinct_ids": cen["distinct_ids"],
            "random_expectation": round(expected_all, 1),
            "enrichment": round(cen["hits"] / max(expected_all, 1e-9), 1),
            "in_row_arrays": inside,
            "outside_row_arrays": sum(cen["outside"].values()),
            "outside_detail": {str(k): v for k, v in sorted(cen["outside"].items())},
            "hits_per_alignment": cen["per_shift"],
            "slots_with_any_hit": len(cen["slots"]),
            "slots_ge_min_hits": len(rows),
        },
        "entities": {"hashmap_slots": ents["slots"], "used": ents["used"],
                     "component_refs": ents["component_refs"]},
        "name_tables": [],
        "other_text_fields": [],
        "entity_index": [],
    }

    enc_block = next((i for i, b in enumerate(blocks)
                      if name_of(dic, b["type_id"]) == "EncyclopediaEntryComponentData"), None)
    enc_by_key: dict[int, dict] = {}
    enc_without_name: set[int] = set()
    if enc_block is not None and enc_block in geos:
        geo = geos[enc_block]
        keys = hashmap(plain, blocks[enc_block], geo)
        row_to_key = {row: key for key, row in keys.items()}
        entries, extra = encyclopedia_entries(plain, ids, blocks[enc_block], geo, row_to_key,
                                              res_names, membership, lo_types)
        enc_by_key = {int(e["key"], 16): e for e in entries if e["key"]}
        # 有百科条目但名字槽是 0 的实体 —— 单独记下来，它们和"根本没有名字字段"不是一回事
        enc_without_name = {int(u["key"], 16) for u in extra["unnamed_rows"] if u["key"]}
        rows_n = geo["rows"]
        fields = []
        for offset, role, export in NAME_FIELDS["EncyclopediaEntryComponentData"]:
            stat = slot_stats.get((enc_block, offset), {})
            fields.append({
                "offset": offset, "role": role, "exported": export,
                "hits": stat.get("hits", 0), "distinct": stat.get("distinct", 0),
                "coverage": round(extra["coverage"][role] / rows_n, 4) if rows_n else 0.0,
                "p_value": stat.get("p_value", "1"),
            })
        by_kind: dict[str, int] = {}
        for entry in entries:
            by_kind[entry["kind"]] = by_kind.get(entry["kind"], 0) + 1
        report["name_tables"].append({
            "block": enc_block,
            "container": "EncyclopediaEntryComponentData",
            "role": "entity_name",
            "row_type": geo["row_type"],
            "stride": geo["stride"],
            "rows": rows_n,
            "geometry": {"index_size": geo["index_size"], "keys": geo["keys"],
                         "tail": geo["tail"], "ok": geo["ok"]},
            "entities_with_entry": len(keys),
            "named": len(entries),
            "by_kind": by_kind,
            "fields": fields,
            "entries": entries,
        })

    if lo_block is not None and lo_block in geos:
        geo = geos[lo_block]
        keys = hashmap(plain, blocks[lo_block], geo)
        row_to_key = {row: key for key, row in keys.items()}
        entries = loadout_entries(plain, ids, blocks[lo_block], geo, row_to_key, res_names,
                                  enc_by_key, membership, lo_types)
        report["name_tables"].append({
            "block": lo_block,
            "container": "LoadoutEntryComponentData",
            "role": "loadout_entry",
            "row_type": geo["row_type"],
            "stride": geo["stride"],
            "rows": geo["rows"],
            "geometry": {"index_size": geo["index_size"], "keys": geo["keys"],
                         "tail": geo["tail"], "ok": geo["ok"]},
            "entries": entries,
        })

    # 其余「有 locid 但不是实体名」的槽：只给统计与短样本（<=70 字符），不导出逐行文本
    for row in rows:
        if row["block"] in (enc_block, lo_block):
            continue
        if row["coverage"] < a.min_coverage:
            continue
        report["other_text_fields"].append({
            "block": row["block"], "container": row["container"],
            "role": TEXT_ROLES.get(row["container"], "text"),
            "row_type": row["row_type"], "rows": row["rows"], "offset": row["offset"],
            "hits": row["hits"], "distinct": row["distinct"],
            "coverage": round(row["coverage"], 3), "p_value": row["p_value"],
        })

    # 完整实体索引：每个实体一条，有名字就带名字，没有就 null
    loadout_by_key = {}
    for table in report["name_tables"]:
        if table["container"] == "LoadoutEntryComponentData":
            for entry in table["entries"]:
                if entry["key"]:
                    loadout_by_key[int(entry["key"], 16)] = entry
    for key in sorted(ents["keys"]):
        enc = enc_by_key.get(key)
        lo = loadout_by_key.get(key)
        # 名字查不到时统一写 UNKNOWN_LABEL（"未知"），并保留 name_status 区分"有百科条目但没填名"
        # 与"根本没有名字字段"——发布数据里不留空洞，但也不能让两种缺失看起来一样。
        resolved = (enc or {}).get("name") or ""
        report["entity_index"].append({
            "key": f"0x{key:016X}",
            "name": resolved or UNKNOWN_LABEL,
            "name_status": ("known" if resolved else
                            "unknown-has-entry" if key in enc_without_name
                            else "unknown-no-entry"),
            "name_slot": (enc or {}).get("name_slot"),
            "name_upper": (enc or {}).get("name_upper"),
            "name_plural": (enc or {}).get("name_plural"),
            "code": (enc or {}).get("code"),
            "kind": classify(key, membership, lo_types),
            "has_encyclopedia_entry": bool(enc),
            "loadout_type": (lo or {}).get("item_type"),
            "loadout_tags": (lo or {}).get("tags") or [],
            "dev_name": res_names.get(key),
        })

    named_kinds: dict[str, int] = {}
    unnamed_kinds: dict[str, int] = {}
    for item in report["entity_index"]:
        bucket = named_kinds if item["name_status"] == "known" else unnamed_kinds
        bucket[item["kind"]] = bucket.get(item["kind"], 0) + 1
    report["coverage"] = {
        "entities": ents["used"],
        "with_encyclopedia_entry": len(enc_by_key),
        "with_name": len(enc_by_key),
        "with_loadout_entry": len(loadout_by_key),
        "loadout_with_name": sum(1 for e in loadout_by_key.values() if e["name"]),
        "entities_with_dev_name": sum(1 for key in ents["keys"] if key in res_names),
        "named_by_kind": dict(sorted(named_kinds.items(), key=lambda kv: -kv[1])),
        "unnamed_by_kind": dict(sorted(unnamed_kinds.items(), key=lambda kv: -kv[1])),
    }

    if a.out:
        dest = pathlib.Path(a.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n写入 {dest}（{dest.stat().st_size / 1024:.0f} KB，只含名字，不含描述）")

    print("\n覆盖率：")
    for key, value in report["coverage"].items():
        print(f"  {key:<28} {value}")
    if enc_by_key:
        print("\n百科名字样本：")
        for entry in list(enc_by_key.values())[:10]:
            print(f"  {entry['name']!r:<30} upper={entry['name_upper']!r:<26} "
                  f"code={entry['code']!r:<9} kind={entry['kind']:<12} key={entry['key']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
