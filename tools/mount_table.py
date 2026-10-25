#!/usr/bin/env python3
"""mount_table.py -- `MountComponentData` / `SeatCollectionComponentData`：读、查、换件（保内容哈希）。

为什么单独一个工具
    "给载具换武器"在过去是**进程内存**路线（memmod，build 25480438）：写 Mount 记录槽里的
    item 8 字节。本 build 的实体库把同一张表原样带着，所以这件事现在可以走**纯数据文件**路线。
    但换件不是"改 8 字节"就完事：换完还要过内容哈希、要能判"这件东西装上去会不会是紫问号 /
    能不能瞄 / 能不能开火 / 玩家能不能操作"。这个工具把这三段合成一条命令。

表布局（**由 typelib 成员算出来，不写死**；`--explain` 会把推导打出来）
    `MountComponentData` = `0x3845B1E0`：
        payload = ComponentIndexData(328 槽 × 16 B) + 165 × MountComponent(120 B)
        索引装载率 0.50（164 键 / 328 槽），165 行里有 1 行没人引用
        `MountComponent` = 5 × `MountInfo`(24 B)   <- 一条记录 = 5 个挂载槽
        `MountInfo` = { u64 item @0, u32 anchor_a @8, `MountSide` @12, u32 anchor_c @16,
                        u8 @20, u8 @21, 2 B pad }
    `SeatCollectionComponentData` = `0x4AEAFc86`：
        payload = ComponentIndexData(112 槽 × 16 B) + 56 × SeatCollectionComponent(424 B)
        `SeatCollectionComponent` = { `TransitionId` @0, `Passenger`[16] @8, u8[8] @264,
                                      22 B @272, u32 @296, u32 @300, u8[4] @304,
                                      `ActiveAimConstraint`[22] @308, u8[22] @396 }

    `MountSide` 枚举名来自公开 hash 清单：`Common / Right / Left`（槽里实测取值 0/1/2 正好三档）。
    ⚠ 旧文档说的 "Mount 前面 64 B 前缀" 是误读：那是哈希图前 4 个槽（全零），索引从 +0 开始。

换件的物理含义（memmod 已实测的判据，这里实现成离线检查）
    只写 `MountInfo.item` 的 8 字节，`MountSide` / 两个 anchor / 两个 flag 一律不动。
    装上去是否可用 = 五件套：几何（mesh）/ 包驻留 / Turret 行 / Wieldable+WeaponWielder / ProjectileWeapon。
    另有两条否决项：敌阵营件（Faction 位掩码 4/8）与 AI 索敌三件套（SensorEye+Targeting+Detector）。

哈希宿主（与 `entity_field_set.py` / `pod_rack_swap.py` 同一套，实体库上已实机验证）
    末块 payload += pad+8、文件尾追加 pad+8 个零、Murmur64A 校正字落在 len+pad（8 对齐）。

用法
    python tools/mount_table.py list                      # 全部挂载记录（含载具名/槽/件名）
    python tools/mount_table.py list --kind vehicle --json
    python tools/mount_table.py show --entity "TD-220"    # 一条记录的槽位解码 + 五件套
    python tools/mount_table.py seats                     # SeatCollection 56 行 → 实体
    python tools/mount_table.py find 40mm                 # 按名字找可换的件
    python tools/mount_table.py swap --entity "TD-110" --slot 1 --item "40 mm" \\
        --out out/mount-swap/x.plain                      # 保哈希写入
    python tools/mount_table.py verify out/mount-swap/x.plain   # 复核：差异/哈希/容器/记录

只读命令不碰游戏目录；`swap` 只写 `--out` 指定的文件。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash        # noqa: E402
from pod_rack_swap import parse_blocks, check_container     # noqa: E402
from typelib import TypeLib                                 # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                        # noqa: BLE001
        pass

# ---- 默认路径（本工作区约定：明文缓存与参考数据在 D:\\mod\\refs 下）
PLAIN = r"D:\mod\refs\dlbin\plaintext-26088801\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26088801\dl_library.dl_typelib"
ENTITY_NAMES = r"D:\mod\refs\entity-locid-names.json"
COMPONENTS = r"D:\mod\refs\entity-components.json"
CATALOG = r"D:\mod\refs\srkit-names.json"
TYPE_NAMES = r"D:\mod\dl-type-names.json"

# ---- 组件类型 id（djb2("data/components/<Name>.json")，由 dl-type-names.json 复核）
MOUNT = 0x3845B1E0
SEAT = 0x4AEAFc86
UNIT = 0x4437574D
TURRET = 0x1EBA7593
PROJECTILE_WEAPON = 0x45171B68
WIELDABLE = 0x3BF780F6
WEAPON_WIELDER = 0x1F5AB323
FACTION = 0x5653EA91
LOADOUT_PACKAGE = 0x7A858691
MOUNT_COMPONENT = 0x8BC6DEA6
MOUNT_INFO = 0xA367FD7F
SEAT_COMPONENT = 0xE014C64C

ANCHOR_HASH = 0x8E49771B181FFAA1      # vanilla `generated_entities.dl_bin` 明文 Murmur64A
SHARED_BASE_PACKAGE = "f6fb08cc02d24255"   # hellpod / shuttle_transport / weapon_rack / sos_beacon
TAIL = 8
AI_BRAIN = ("SensorEyeComponentData", "TargetingComponentData", "DetectorComponentData")
FACTION_NAMES = {0: "inherit", 1: "super-earth", 2: "?", 4: "illuminate", 8: "automaton"}
SIDE_NAMES = {0: "Common", 1: "Right", 2: "Left"}
FMT = {"u32": ("<I", 4), "u64": ("<Q", 8)}
# `TurretComponent`（76 B）在本 build 的四项限位偏移：pitch_min / pitch_max / yaw_min / yaw_max
# （旧 build 是 +0/+4/+8/+12；本 build 那四个位置是小浮点，限位整体后移 —— 见文档 §4.6）
TURRET_LIMITS = (0x14, 0x18, 0x1C, 0x20)

# 人工别名：**每一条都有出处**，不是猜的。来源缩写：
#   [实机] = memmod 时代在 build 25480438 上装过/打过（见 docs/VEHICLE-MOUNT-ITEMS.md）
#   [几何] = 本 build 离线核对：mesh gpu_size 与旧文档记的字节数吻合（见 §4 交叉验证）
#   [wiki] = Helldivers Wiki 的正式编号/名称
ALIASES = {
    # 载具（实体名 → 游戏内编号名）
    0x16474112801385B6: "TD-220 Bastion MK XVI",          # [wiki]
    0xB0C9FAF4AF8903F9: "TD-110 Maelstrom",               # [wiki]
    0x79E4B3D2DA5E45E3: "EXO-45 Patriot",                 # [wiki]
    0xC2D449ECF7FACAB1: "EXO-49 Emancipator",             # [wiki]
    0x7B2326F6FD9C8069: "EXO-51 Lumberer",                # [wiki]
    0x35DBF54F016F3624: "EXO-55 Breakthrough",            # [wiki]
    0xCC21C7FFD3EBEFB9: "M-102 Gunner FRV",               # [wiki]
    0xE9CD1D0D118886AF: "M-102 Gunner FRV (duplicate)",   # [wiki]
    0x9B2140378640432E: "M-103 Supply FRV",               # [wiki]
    0x2D85BFE3D8717FE5: "M-104 Incinerator FRV",          # [wiki]
    0x423FF97D57AB04F5: "GROUND ALL-TERRAIN EXTRACTION RIG",   # [百科] 原始名
    0x0801B6B3C5D12EBC: "GROUND ALL-TERRAIN EXTRACTION RIG (duplicate)",  # [百科]
    # 挂载件
    0x9872EEB31A5F88FD: "40 mm 炮塔站",                    # [实机] memmod: 40 mm 站
    0xC25DC40EDE0E2D16: "孤儿炮塔站",                      # [实机] memmod: 孤儿站
    0x8365609B35EF6672: "运输机炮塔",                      # [实机] memmod: 运输机炮塔/251 KB
    0x439F9E65C18567DA: "TD-220 同轴机枪",                 # [实机] memmod: 无几何、±20°
    0x1FA1F596769225C2: "TD-220 主炮",                     # [实机] memmod: 同轴机枪的 bones_ref 指向它
    0xD58AE6A04EDB10DE: "TD-110 主炮",                     # [几何] mesh 1,836,154 B ≈ 旧文档 1.84 MB
    0xCD28A27A79BE53D5: "地堡 HMG（自动化军团）",           # [实机] memmod: 敌阵营否决样本
    0x9926876B2375A1BB: "自动化军团小口径自动炮",           # [实机] memmod: 跨阵营换件成功样本
    0x4DF41F84668D07FB: "M-103 AI 炮塔",                   # [实机] memmod: 自带索敌大脑
    0x5D142C3A73EBC634: "车顶火箭炮塔 (tank_turret_rocketlauncher)",   # [实机] memmod §6.0b
    0x085C1EDB038EC24E: "MG-206 重机枪（M-102 枪手位）",    # [离线] unit 名 + 载具槽位
    0x444880F62CA7EAE8: "B/FLAM-80 Cremator（M-104 喷火位）",  # [wiki] 实体百科名
}


# ---------------------------------------------------------------- 读取层
class Env:
    """明文 + typelib + 三份参考 JSON 的懒加载集合。"""

    def __init__(self, plain: str, typelib: str, entity_names: str, components: str,
                 catalog: str, type_names: str):
        self.plain_path = pathlib.Path(plain)
        self.data = self.plain_path.read_bytes()
        self.lib = TypeLib(pathlib.Path(typelib).read_bytes())
        self.blocks = parse_blocks(self.data)
        self._by_type = {}
        for i, b in enumerate(self.blocks):
            self._by_type.setdefault(b["type_id"], []).append(i)
        self.type_names = self._load_type_names(type_names)
        self.entity = self._load_entity(entity_names)
        self.components = self._load_components(components)
        self.catalog = self._load_catalog(catalog)
        self._unit_cache: dict[int, dict] = {}
        self._idx_cache: dict[int, dict[int, int]] = {}
        self._faction_cache: dict[int, int] | None = None
        self._pkg_cache: dict[int, int] | None = None

    # -- JSON
    @staticmethod
    def _load_type_names(path: str) -> dict[int, str]:
        p = pathlib.Path(path)
        if not p.is_file():
            return {}
        try:
            return {int(x["id_hex"], 16): x["name"]
                    for x in json.loads(p.read_text(encoding="utf-8")).get("fields", [])}
        except (OSError, ValueError, KeyError):
            return {}

    @staticmethod
    def _load_entity(path: str) -> dict[int, dict]:
        p = pathlib.Path(path)
        if not p.is_file():
            return {}
        d = json.loads(p.read_text(encoding="utf-8"))
        return {int(e["key"], 16): e for e in d.get("entity_index", [])}

    @staticmethod
    def _load_components(path: str) -> dict[int, list[str]]:
        p = pathlib.Path(path)
        if not p.is_file():
            return {}
        d = json.loads(p.read_text(encoding="utf-8"))
        return {int(k, 16): v for k, v in d.get("components", {}).items()}

    @staticmethod
    def _load_catalog(path: str) -> dict[int, dict]:
        p = pathlib.Path(path)
        if not p.is_file():
            return {}
        out: dict[int, dict] = {}
        for e in json.loads(p.read_text(encoding="utf-8")):
            fid = int(e["file_id_hex"], 16)
            slot = out.setdefault(fid, {"name": None, "packages": [], "types": {}})
            if slot["name"] is None:
                slot["name"] = e.get("name")
            if e["package"] not in slot["packages"]:
                slot["packages"].append(e["package"])
            slot["types"].setdefault(e.get("type"), []).append(
                {"package": e["package"], "gpu_size": e.get("gpu_size", 0),
                 "toc_size": e.get("toc_size", 0)})
        return out

    def clone(self, data: bytes) -> "Env":
        """同一套参考数据 + 换过的明文：不重读 95 MB 目录，只重建块表。"""
        import copy
        e = copy.copy(self)
        e.data = data
        e.blocks = parse_blocks(data)
        e._by_type = {}
        for i, b in enumerate(e.blocks):
            e._by_type.setdefault(b["type_id"], []).append(i)
        e._unit_cache, e._idx_cache, e._faction_cache, e._pkg_cache = {}, {}, None, None
        return e

    # -- 容器
    def block(self, tid: int) -> dict:
        idx = self._by_type.get(tid) or []
        if len(idx) != 1:
            raise SystemExit(f"✗ 期望恰好 1 个块 0x{tid:08X}，实际 {len(idx)}")
        return self.blocks[idx[0]]

    def container(self, tid: int) -> dict:
        """块 = 哈希图 + 行数组；槽数/行数/步长全部由 typelib 成员算。"""
        b = self.block(tid)
        ms = self.lib.members(tid)
        if len(ms) != 2:
            raise SystemExit(f"✗ 块 0x{tid:08X} 不是「哈希图 + 行数组」形态（成员数 {len(ms)}）")
        idx_bytes, row_bytes = ms[0]["size64"], ms[1]["size64"]
        stride = self.lib.desc(ms[1]["type_id"])[3]
        if idx_bytes % 16 or row_bytes % stride:
            raise SystemExit(f"✗ 几何不整：idx={idx_bytes} rows={row_bytes} stride={stride}")
        return {"type": tid, "head": b["head"], "payload": b["payload"],
                "body": b["head"] + 28, "index_bytes": idx_bytes, "slots": idx_bytes // 16,
                "rows": row_bytes // stride, "stride": stride, "row_type": ms[1]["type_id"]}

    def index_map(self, tid: int) -> dict[int, int]:
        if tid in self._idx_cache:
            return self._idx_cache[tid]
        c = self.container(tid)
        out = {}
        for i in range(c["slots"]):
            key, row, pad = struct.unpack_from("<QII", self.data, c["body"] + 16 * i)
            if key:
                out[key] = row
        self._idx_cache[tid] = out
        return out

    def row_map(self, tid: int) -> dict[int, int]:
        return {row: key for key, row in self.index_map(tid).items()}

    def row_offset(self, tid: int, row: int) -> int:
        c = self.container(tid)
        return c["body"] + c["index_bytes"] + row * c["stride"]

    # -- 组件取值
    def u64_at(self, tid: int, key: int, field: int) -> int | None:
        row = self.index_map(tid).get(key)
        if row is None:
            return None
        return struct.unpack_from("<Q", self.data, self.row_offset(tid, row) + field)[0]

    def unit_of(self, key: int) -> int | None:
        return self.u64_at(UNIT, key, 0)

    def faction_of(self, key: int) -> int | None:
        if self._faction_cache is None:
            self._faction_cache = {}
            c = self.container(FACTION)
            for i in range(c["slots"]):
                k, row, _pad = struct.unpack_from("<QII", self.data, c["body"] + 16 * i)
                if k:
                    self._faction_cache[k] = struct.unpack_from(
                        "<I", self.data, c["body"] + c["index_bytes"] + row * c["stride"])[0]
        return self._faction_cache.get(key)

    def package_of(self, key: int) -> int | None:
        """`LoadoutPackageComponentData` 行内 +8 = 该件声明的 toc 包（POD-RACK 已实机）。"""
        if self._pkg_cache is None:
            self._pkg_cache = {}
            c = self.container(LOADOUT_PACKAGE)
            for i in range(c["slots"]):
                k, row, _pad = struct.unpack_from("<QII", self.data, c["body"] + 16 * i)
                if k:
                    self._pkg_cache[k] = struct.unpack_from(
                        "<Q", self.data, c["body"] + c["index_bytes"] + row * c["stride"] + 8)[0]
        return self._pkg_cache.get(key)


# ---------------------------------------------------------------- 语义层
def name_of(env: Env, key: int) -> str:
    e = env.entity.get(key) or {}
    return e.get("name") or ""


def is_named(env: Env, key: int) -> bool:
    n = name_of(env, key)
    return bool(n) and n != "未知"


def best_name(env: Env, key: int) -> str:
    """别名 → 实体名 → 开发名 → 资源后缀名 → 十六进制。

    挂载件大多**没有百科条目**（甲：载具炮塔/机甲臂），所以名字主要靠资源目录——
    目录里的 `name` 是资源路径的**尾部 24 字符**（目录部分被截断），例如
    `ttle_gunship_turret_hmg` 就是 `.../shuttle_gunship_turret_hmg`。
    """
    if key in ALIASES:
        return ALIASES[key]
    e = env.entity.get(key) or {}
    if e.get("name") and e["name"] != "未知":
        return e["name"]
    if e.get("dev_name"):
        return pathlib.PurePosixPath(e["dev_name"]).name
    for fid in (key, env.unit_of(key) or 0):
        res = (env.catalog.get(fid) or {}).get("name")
        if res and not _looks_hex(str(res)):
            return pathlib.PurePosixPath(str(res)).name
    return f"0x{key:016X}"


def _looks_hex(text: str) -> bool:
    t = text.strip()
    return len(t) == 16 and all(c in "0123456789ABCDEF" for c in t.upper())


def turret_limits(env: Env, key: int) -> dict | None:
    """件的 `Turret` 行四项限位（本 build：+0x14/+0x18/+0x1C/+0x20，f32）。"""
    row = env.index_map(TURRET).get(key)
    if row is None:
        return None
    base = env.row_offset(TURRET, row)
    pmin, pmax, ymin, ymax = (struct.unpack_from("<f", env.data, base + o)[0]
                              for o in TURRET_LIMITS)
    return {"row": row, "pitch_min": pmin, "pitch_max": pmax, "yaw_min": ymin, "yaw_max": ymax}


def item_info(env: Env, key: int) -> dict:
    """一个挂载件的全部离线判据（五件套 + 两条否决项 + 包）。

    ⚠ 资源 id == 实体键：`UnitComponentData` 行 +0 读出来就是实体键本身（1720/1720 行自指），
    所以"实体键 → unit 资源"这一跳在本 build 里是恒等的；资源目录（srkit-names.json）直接按
    **实体键** 查即可（mesh/bones/physics/state_machine 都在同一个 file_id 下、按包分多条）。
    """
    e = env.entity.get(key) or {}
    unit = env.unit_of(key)
    cat = env.catalog.get(unit or 0) or env.catalog.get(key, {})
    meshes = cat.get("types", {}).get("mesh", [])
    gpu = [m["gpu_size"] for m in meshes]
    comps = env.components.get(key, [])
    faction = env.faction_of(key)
    if not meshes:
        geometry = "none"                     # 没有 mesh（骨骼引用型 / 压根不是件）
    elif max(gpu or [0]) > 0:
        geometry = "inline"                   # ① 自带内联几何
    else:
        geometry = "streaming"                # ② 流式几何：顶点在同包 geometry_group
    packages = cat.get("packages", [])
    return {
        "key": f"0x{key:016X}",
        "display_name": best_name(env, key),
        "alias": ALIASES.get(key),
        "entity_name": e.get("name"),
        "kind": e.get("kind"),
        "dev_name": e.get("dev_name"),
        "unit_id": f"0x{unit:016X}" if unit else None,
        "unit_name": cat.get("name"),
        "packages": packages,
        "shared_package": SHARED_BASE_PACKAGE in packages,
        "declared_package": (f"0x{env.package_of(key):016X}" if env.package_of(key) else None),
        "mesh_count": len(meshes),
        "mesh_gpu": gpu,
        "geometry": geometry,
        "bones": len(cat.get("types", {}).get("bones", [])),
        "has_turret": env.index_map(TURRET).get(key) is not None,
        "turret_limits": turret_limits(env, key),
        "has_projectile_weapon": env.index_map(PROJECTILE_WEAPON).get(key) is not None,
        "has_wieldable": env.index_map(WIELDABLE).get(key) is not None,
        "has_weapon_wielder": env.index_map(WEAPON_WIELDER).get(key) is not None,
        "faction": faction,
        "faction_name": FACTION_NAMES.get(faction, str(faction)) if faction is not None else None,
        "ai_brain": all(c in comps for c in AI_BRAIN),
        "components": comps,
    }


def five_piece(info: dict) -> dict:
    """把 item_info 折成一张判定表：缺哪一条、会不会紫问号 / 不能瞄 / 不能打。"""
    return {
        "geometry": info["geometry"],
        "package_ok": info["shared_package"] or bool(info["packages"]),
        "turret": info["has_turret"],
        "player_control": info["has_wieldable"] and info["has_weapon_wielder"],
        "fire": info["has_projectile_weapon"],
        "veto_enemy_faction": info["faction"] in (4, 8),
        "veto_ai_brain": info["ai_brain"],
    }


def mount_records(env: Env) -> list[dict]:
    c = env.container(MOUNT)
    row2key = env.row_map(MOUNT)
    out = []
    for row in range(c["rows"]):
        base = c["body"] + c["index_bytes"] + row * c["stride"]
        slots = []
        for s in range(c["stride"] // 24):
            item, anchor_a, side, anchor_c, f20, f21 = struct.unpack_from(
                "<QIIIBB", env.data, base + s * 24)
            if not (item or anchor_a or anchor_c):
                continue
            slots.append({"slot": s, "item": f"0x{item:016X}", "anchor_a": anchor_a,
                          "side": side, "side_name": SIDE_NAMES.get(side, str(side)),
                          "anchor_c": anchor_c, "byte20": f20, "byte21": f21})
        key = row2key.get(row)
        out.append({"row": row, "key": f"0x{key:016X}" if key else None,
                    "name": best_name(env, key) if key else None,
                    "kind": (env.entity.get(key) or {}).get("kind") if key else None,
                    "slots": slots})
    return out


def seat_records(env: Env) -> list[dict]:
    c = env.container(SEAT)
    row2key = env.row_map(SEAT)
    out = []
    for row in range(c["rows"]):
        base = c["body"] + c["index_bytes"] + row * c["stride"]
        transition = struct.unpack_from("<I", env.data, base)[0]
        pax = []
        for p in range(16):
            a, b, ent = struct.unpack_from("<IIQ", env.data, base + 8 + p * 16)
            if a or b or ent:
                pax.append({"index": p, "u32a": a, "u32b": b,
                            "entity": f"0x{ent:016X}" if ent else None,
                            "entity_name": name_of(env, ent) if ent else None})
        flags = list(env.data[base + 264:base + 272])
        tail_flags = list(env.data[base + 396:base + 418])
        aim = list(struct.unpack_from("<22I", env.data, base + 308))
        key = row2key.get(row)
        out.append({"row": row, "key": f"0x{key:016X}" if key else None,
                    "name": best_name(env, key) if key else None,
                    "kind": (env.entity.get(key) or {}).get("kind") if key else None,
                    "transition_id": transition, "passengers": pax,
                    "flags": flags, "tail_flags": tail_flags,
                    "aim_constraints": aim,
                    "u296": struct.unpack_from("<I", env.data, base + 296)[0],
                    "u300": struct.unpack_from("<I", env.data, base + 300)[0]})
    return out


# ---------------------------------------------------------------- 名字解析
def _norm(text: str) -> str:
    """名字匹配口径：小写 + 去掉空白与 `- _ .`（`40mm`→`40 mm 炮塔站`，`td220`→`TD-220 Bastion MK XVI`）。"""
    return "".join(ch for ch in str(text).lower() if not ch.isspace() and ch not in "-_.")


def resolve_entity(env: Env, text: str) -> tuple[int, int]:
    """实体键或名字 → (key, mount row)。名字支持子串，必须唯一。"""
    t = text.strip()
    if t.lower().startswith("0x"):
        key = int(t, 16)
        row = env.index_map(MOUNT).get(key)
        if row is None:
            raise SystemExit(f"✗ 0x{key:016X} 不在 Mount 哈希图里（没有挂载记录）")
        return key, row
    low = _norm(t)
    hits = []
    for key, row in env.index_map(MOUNT).items():
        if low in _norm(best_name(env, key)):
            hits.append((key, row))
    if not hits:
        raise SystemExit(f"✗ 没有名字含 {t!r} 的挂载记录；先跑 `list` 或 `find`")
    if len(hits) > 1:
        names = ", ".join(f"{best_name(env, k)} (0x{k:016X})" for k, _ in hits[:8])
        raise SystemExit(f"✗ {t!r} 命中 {len(hits)} 条记录：{names} … 请用 0x 键或更长的名字")
    return hits[0]


def resolve_item(env: Env, text: str) -> int:
    """件 → 实体键。允许 0x 键 / none / 名字子串（在 Mount 里出现过的件 + 全实体表里都有）。"""
    t = text.strip()
    if t.lower() in ("none", "0", "-"):
        return 0
    if t.lower().startswith("0x"):
        key = int(t, 16)
        if not any(s["item"] == f"0x{key:016X}"
                   for r in mount_records(env) for s in r["slots"]):
            # 允许"新引入的件"（不在任何现有槽里），但要求它在实体表里存在
            if key not in env.entity and key not in env.components:
                raise SystemExit(f"✗ 0x{key:016X} 既不在任何挂载槽里，也不是实体表里的实体")
        return key
    low = _norm(t)
    pool = {}
    for rec in mount_records(env):
        for s in rec["slots"]:
            if s["item"] == "0x0000000000000000":
                continue
            pool[int(s["item"], 16)] = True
    for key in list(env.entity.keys()):
        if key in env.components:
            pool.setdefault(key, True)
    hits = [k for k in pool if low in _norm(best_name(env, k))]
    if not hits:
        raise SystemExit(f"✗ 没有名字含 {t!r} 的件；先跑 `find {t}`")
    if len(hits) > 1:
        names = ", ".join(f"{best_name(env, k)} (0x{k:016X})" for k in hits[:8])
        raise SystemExit(f"✗ {t!r} 命中 {len(hits)} 个件：{names} … 请用 0x 键")
    return hits[0]


# ---------------------------------------------------------------- 写入层
def swap(env: Env, entity: str, slot: int, item_text: str, out: str,
         expect_old: str | None, dry_run: bool) -> int:
    key, row = resolve_entity(env, entity)
    item = resolve_item(env, item_text)
    c = env.container(MOUNT)
    per_record = c["stride"] // 24
    if not 0 <= slot < per_record:
        raise SystemExit(f"✗ 槽号 {slot} 越界（0..{per_record - 1}）")
    target = env.row_offset(MOUNT, row) + slot * 24
    original = env.data
    h0 = murmur64(original)
    if h0 != ANCHOR_HASH:
        print(f"⚠ 输入明文哈希 0x{h0:016X} != 锚点 0x{ANCHOR_HASH:016X}"
              f"（不是 vanilla，按'输入即基线'继续；G3 仍要求输出==输入）")
    old_item = struct.unpack_from("<Q", original, target)[0]
    print(f"实体 {best_name(env, key)} (0x{key:016X}) 记录行 {row} 槽 {slot}")
    print(f"  件: 0x{old_item:016X} {best_name(env, old_item) if old_item else '(空槽)'}"
          f"  →  0x{item:016X} {best_name(env, item) if item else '(清空)'}")
    if expect_old is not None:
        want = int(expect_old, 16) if expect_old.lower().startswith("0x") else int(expect_old)
        if old_item != want:
            print(f"✗ G7 旧值 0x{old_item:016X} != 期望 0x{want:016X}")
            return 1

    old_lim = turret_limits(env, old_item) if old_item else None
    info = item_info(env, item) if item else None
    if info:
        fp = five_piece(info)
        print(f"  五件套: 几何={fp['geometry']} 包={'共享基包' if info['shared_package'] else info['packages'][:2]} "
              f"Turret={fp['turret']} 玩家可操作={fp['player_control']} 开火={fp['fire']}")
        print(f"          unit={info['unit_name']} mesh={info['mesh_count']}/{info['mesh_gpu'][:2]} "
              f"faction={info['faction_name']}")
        if fp["veto_enemy_faction"]:
            print("  ⚠ 否决项：敌阵营件（Faction=4/8）—— 本工具不写 Faction 表，装上会被宿主阵营处理掉")
        if fp["veto_ai_brain"]:
            print("  ⚠ 否决项：AI 索敌三件套齐（SensorEye+Targeting+Detector）—— 它会自己开火，玩家抢不到")
        lim = info["turret_limits"]
        if lim or old_lim:
            def _yaw(x):
                return f"±{x['yaw_max']:g}" if x and abs(x['yaw_min'] + x['yaw_max']) < 1e-3                     else (f"{x['yaw_min']:g}…{x['yaw_max']:g}" if x else "无 Turret")
            print(f"  射界(yaw): 原 {_yaw(old_lim)} → 新 {_yaw(lim)}")
        if fp["geometry"] == "none":
            print("  ⚠ 几何：没有 mesh（骨骼引用型或非武器件）—— 装上看不到模型，但可能能瞄/能打")

    pad = (8 - len(original) % 8) % 8
    tail_len = pad + TAIL
    word_at = len(original) + pad
    blocks = env.blocks
    last = blocks[-1]
    edited = bytearray(original)
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    edited += bytes(tail_len)
    struct.pack_into("<Q", edited, target, item)
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)
    print(f"  写入 @0x{target:X}  校正字 @0x{word_at:X}  长度 {len(original):,} → {len(edited):,}")

    checks = []

    def check(tag: str, cond: bool, detail: str = "") -> None:
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = (set(range(target, target + 8)) | set(range(last["head"] + 16, last["head"] + 20))
               | set(range(word_at, word_at + TAIL)))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    got = murmur64(bytes(edited))
    check("G1 长度 = 原长 + pad + 8", len(edited) == len(original) + tail_len)
    check("G2 差异 ⊆ 目标 8 B ∪ 末块 payload 尺寸 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)}")
    check("G3 重算 Murmur64A == 输入哈希", got == h0, f"0x{got:016X}")
    check("G4 item 读回 == 目标", struct.unpack_from("<Q", edited, target)[0] == item)
    check("G5 同记录其它槽逐字节未变",
          all(edited[env.row_offset(MOUNT, row) + s * 24:env.row_offset(MOUNT, row) + s * 24 + 24]
              == original[env.row_offset(MOUNT, row) + s * 24:env.row_offset(MOUNT, row) + s * 24 + 24]
              for s in range(per_record) if s != slot))
    check("G8 校正字 8 对齐且不与目标重叠",
          word_at % 8 == 0 and not (target < word_at + TAIL and word_at < target + 8))
    check("G9 追加区除校正字外全 0",
          all(b == 0 for i, b in enumerate(edited[len(original):]) if len(original) + i < word_at
              or len(original) + i >= word_at + TAIL))
    try:
        n = check_container(bytes(edited))
        check("G6 容器重解析自洽", n == len(blocks), f"{n} 块")
    except Exception as exc:                                     # noqa: BLE001
        check("G6 容器重解析自洽", False, str(exc))
    # G10：从输出重新解析这张表，确认"只有这一个槽变了"。
    # 用 (row, slot) 当键而不是按顺序 zip —— 空槽在前后两次列表里的条数不同，zip 会错位。
    env2 = env.clone(bytes(edited))
    before = {(r["row"], s["slot"]): s["item"] for r in mount_records(env) for s in r["slots"]}
    after = {(r["row"], s["slot"]): s["item"] for r in mount_records(env2) for s in r["slots"]}
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    check("G10 全表只有目标槽变了", changed == [(row, slot)],
          f"changed={[(r, sl, before.get((r, sl)), after.get((r, sl))) for r, sl in changed]}")

    if not all(c[1] for c in checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1
    if dry_run or not out:
        print("\n✓ 门禁全过（--dry-run / 未给 --out，不落盘）")
        return 0
    dest = pathlib.Path(out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(bytes(edited))
    print(f"\n✓ 全部门禁通过 → {dest}（{len(edited):,} B）")
    return 0


def verify(env_ref: Env, path: str) -> int:
    """把输出文件与 vanilla 对比：哈希、容器、表几何、到底哪几个槽变了。"""
    out = Env(path, str(pathlib.Path(TYPELIB)), str(pathlib.Path(ENTITY_NAMES)),
              str(pathlib.Path(COMPONENTS)), str(pathlib.Path(CATALOG)),
              str(pathlib.Path(TYPE_NAMES)))
    h_ref, h_out = murmur64(env_ref.data), murmur64(out.data)
    ok = True

    def line(tag: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        ok &= cond
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    print(f"vanilla {len(env_ref.data):,} B  输出 {len(out.data):,} B")
    line("哈希 == vanilla", h_ref == h_out, f"0x{h_out:016X}")
    try:
        line("容器链自洽", check_container(out.data) == len(out.blocks), f"{len(out.blocks)} 块")
    except Exception as exc:                                     # noqa: BLE001
        line("容器链自洽", False, str(exc))
    try:
        cm, cs = out.container(MOUNT), out.container(SEAT)
        line("Mount 几何", (cm["slots"], cm["rows"], cm["stride"]) == (328, 165, 120),
             f"{cm['slots']} 槽 / {cm['rows']} 行 × {cm['stride']}")
        line("Seat 几何", (cs["slots"], cs["rows"], cs["stride"]) == (112, 56, 424),
             f"{cs['slots']} 槽 / {cs['rows']} 行 × {cs['stride']}")
    except SystemExit as exc:
        line("表几何", False, str(exc))
    ref_m = {(r["row"], s["slot"]): s["item"] for r in mount_records(env_ref) for s in r["slots"]}
    out_m = {(r["row"], s["slot"]): s["item"] for r in mount_records(out) for s in r["slots"]}
    changed = sorted(k for k in set(ref_m) | set(out_m) if ref_m.get(k) != out_m.get(k))
    print(f"  变化的槽: {[(r, s, ref_m.get((r, s)), out_m.get((r, s))) for r, s in changed] or '无'}")
    line("变化的槽 ≤ 1", len(changed) <= 1, f"{len(changed)} 个")
    return 0 if ok else 1


# ---------------------------------------------------------------- 命令
def cmd_list(env: Env, args) -> int:
    recs = mount_records(env)
    if args.kind:
        recs = [r for r in recs if (r["kind"] or "") == args.kind]
    if args.json:
        print(json.dumps(recs, ensure_ascii=False, indent=1))
        return 0
    print(f"Mount 记录 {len(recs)} 条（每行 = 5 槽；只列非空槽）")
    for r in recs:
        if not r["slots"]:
            continue
        print(f"row {r['row']:>3} {str(r['name'])[:34]:<34} {(r['kind'] or '?'):<12} {r['key']}")
        for s in r["slots"]:
            key = int(s["item"], 16)
            nm = best_name(env, key) if key else "(空)"
            print(f"      槽{s['slot']} [{s['side_name']:<6}] {s['item']}  {nm[:46]}")
    return 0


def cmd_show(env: Env, args) -> int:
    key, row = resolve_entity(env, args.entity) if args.entity else (-1, args.row)
    if args.entity is None:
        rev = env.row_map(MOUNT)
        key = rev.get(row, 0)
    c = env.container(MOUNT)
    base = c["body"] + c["index_bytes"] + row * c["stride"]
    print(f"实体 {best_name(env, key) if key else '(无引用行)'}  0x{key:016X}  记录行 {row}")
    print(f"行基址 0x{base:X}  5 槽 × 24 B")
    print(f"{'槽':>2} {'side':<7} {'item':<20} {'anchor_a':>10} {'anchor_c':>10} b20 b21  件名/判据")
    for s in range(c["stride"] // 24):
        item, anchor_a, side, anchor_c, f20, f21 = struct.unpack_from(
            "<QIIIBB", env.data, base + s * 24)
        nm = best_name(env, item) if item else ""
        print(f"{s:>2} {SIDE_NAMES.get(side, side):<7} 0x{item:016X} {anchor_a:>10} {anchor_c:>10} "
              f"{f20:>3} {f21:>3}  {nm[:40]}")
    print("\n非空槽的五件套：")
    any_slot = False
    for s in range(c["stride"] // 24):
        item = struct.unpack_from("<Q", env.data, base + s * 24)[0]
        if not item:
            continue
        any_slot = True
        info = item_info(env, item)
        fp = five_piece(info)
        print(f"  槽{s} 0x{item:016X} {best_name(env, item)}")
        print(f"      unit={info['unit_name']} pkg={info['packages']} "
              f"declared={info['declared_package']}")
        print(f"      几何={fp['geometry']} mesh={info['mesh_count']}/{info['mesh_gpu'][:3]} "
              f"bones={info['bones']}")
        print(f"      Turret={fp['turret']} Wieldable={info['has_wieldable']} "
              f"WeaponWielder={info['has_weapon_wielder']} ProjectileWeapon={fp['fire']} "
              f"Faction={info['faction_name']} AI大脑={fp['veto_ai_brain']}")
        lim = info["turret_limits"]
        if lim:
            print(f"      射界: pitch {lim['pitch_min']:g}…{lim['pitch_max']:g}  "
                  f"yaw {lim['yaw_min']:g}…{lim['yaw_max']:g}（Turret 行 {lim['row']}）")
    if not any_slot:
        print("  （空记录：5 个槽全 0）")
    return 0


def cmd_seats(env: Env, args) -> int:
    recs = seat_records(env)
    if args.json:
        print(json.dumps(recs, ensure_ascii=False, indent=1))
        return 0
    print(f"SeatCollection 记录 {len(recs)} 条（112 槽哈希图 / 56 行 × 424 B；装载率 0.50）")
    for r in recs:
        pax = "".join(f" p{p['index']}={p['entity_name']}" for p in r["passengers"])
        aim = sum(1 for v in r["aim_constraints"] if v)
        print(f"row {r['row']:>2} {str(r['name'])[:34]:<34} {(r['kind'] or '?'):<12} "
              f"transition={r['transition_id']:>2} flags={''.join(map(str, r['flags']))} "
              f"aim={'on' if aim else '--'} tail={r['tail_flags'][0]}{pax}")
    return 0


def cmd_find(env: Env, args) -> int:
    low = _norm(args.text)
    pool = {}
    for rec in mount_records(env):
        for s in rec["slots"]:
            if s["item"] != "0x0000000000000000":
                pool[int(s["item"], 16)] = True
    for key in env.components:
        pool.setdefault(key, True)
    hits = [k for k in pool if low in _norm(best_name(env, k))]
    if not hits:
        print(f"没有名字含 {args.text!r} 的件")
        return 1
    print(f"命中 {len(hits)} 个：")
    for key in sorted(hits):
        info = item_info(env, key)
        fp = five_piece(info)
        print(f"  0x{key:016X} {best_name(env, key)[:40]:<40} 几何={fp['geometry']:<9} "
              f"T{int(fp['turret'])}P{int(fp['fire'])}W{int(info['has_wieldable'])}"
              f"WW{int(info['has_weapon_wielder'])} pkg={','.join(info['packages'][:2])[:34]}")
    return 0


def cmd_explain(env: Env, args) -> int:
    names = env.type_names
    for tid, label in ((MOUNT, "MountComponentData"), (SEAT, "SeatCollectionComponentData")):
        c = env.container(tid)
        print(f"{label} 0x{tid:08X} @0x{c['head']:X} payload={c['payload']:,}")
        print(f"  哈希图 {c['index_bytes']:,} B = {c['slots']} 槽 × 16 B（占用 {len(env.index_map(tid))}）")
        print(f"  行数组 {c['rows']} × {c['stride']} B   行类型 {names.get(c['row_type'], hex(c['row_type']))}")
        ms = env.lib.members(tid)
        print(f"  成员: {[(m['offset64'], m['size64'], names.get(m['type_id'], hex(m['type_id']))) for m in ms]}")
        sub = env.lib.members(c["row_type"])
        print(f"  行内成员（{len(sub)}）:")
        for m in sub:
            t = names.get(m["type_id"], f"0x{m['type_id']:08X}")
            print(f"    +0x{m['offset64']:03X} {m['size64']:>4} B  {t}")
        print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Mount / SeatCollection 表：读、查、换件（保内容哈希）")
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--entities", default=ENTITY_NAMES)
    ap.add_argument("--components", default=COMPONENTS)
    ap.add_argument("--catalog", default=CATALOG)
    ap.add_argument("--type-names", default=TYPE_NAMES)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="全部挂载记录")
    p.add_argument("--kind", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="一条记录 / 一行的槽位解码")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--entity")
    g.add_argument("--row", type=int)
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("seats", help="SeatCollection 全表")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_seats)

    p = sub.add_parser("find", help="按名字找件")
    p.add_argument("text")
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("explain", help="打印两表的几何推导（typelib）")
    p.set_defaults(func=cmd_explain)

    p = sub.add_parser("swap", help="换件（保内容哈希）")
    p.add_argument("--entity", required=True)
    p.add_argument("--slot", type=int, required=True)
    p.add_argument("--item", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--expect-old", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=lambda env, a: swap(env, a.entity, a.slot, a.item, a.out,
                                            a.expect_old, a.dry_run))

    p = sub.add_parser("verify", help="复核一个输出文件")
    p.add_argument("path")
    p.set_defaults(func=lambda env, a: verify(env, a.path))

    a = ap.parse_args()
    env = Env(a.plain, a.typelib, a.entities, a.components, a.catalog, a.type_names)
    return a.func(env, a)


if __name__ == "__main__":
    raise SystemExit(main())
