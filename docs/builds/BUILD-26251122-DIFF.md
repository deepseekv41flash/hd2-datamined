# BUILD-26251122（2026-10-29，7.2.2 "Devoid of Liberty"）

> 一句话：**密钥没变、类型库逐字节相同、55 张表只动 4 张**；
> 变更全部能与官方 notes 对上，且 **`generated_entities.dl_bin` 逐字节未变** —— 与载具/座位相关的结论照旧。
> 值级明细见 [BUILD-DIFF-26251122（cases）](../cases/BUILD-DIFF-26251122.md) 与 `refs/row-diff-*.json`。
> 升级前的停机/备份/卸载流程见 [PRE-UPDATE](../cases/BUILD-26251122-PRE-UPDATE.md)。

## 1 三层验证（`✓ 离线`）

| 层 | 结果 |
|---|---|
| **密钥** | 现有 `recipient.sk` 解开新 build **56/56** 个文件（55 张表 + typelib），0 失败；封包头仍是 48 B（`epk 32 / tag 16`） ⇒ **密钥未变**，封/解封链路与全部部署工具继续可用 |
| **类型库** | `dl_library.dl_typelib` 1,080,024 B，sha `a2392b58c80a2a70…`，与 26088801 **逐字节相同** ⇒ 所有字段偏移、`TransitionId`（46 值）等枚举结论继续有效 |
| **表内容** | 55 张中 **51 张逐字节相同**，4 张变化（见 §2） |

## 2 变了什么（值级）

| 表 | 变化 | 值级结论 | 官方 notes 对应 |
|---|---|---|---|
| `generated_projectile_settings` | 1 处 u32 | `+0x10F18`: **60.0 → 20.0** | AMW-20 APEX 口径 60→20 |
| `generated_damage_settings` | 1 处 u32 | `+0x3FB4`: **15 → 30** | APEX 拆除强度 → 30 |
| `generated_stratagem_settings` | 名字表 1 条（整组 −8 B 重排） | `$TEAM WEAPONS. LASER RIFLE ION` → `TEAM WEAPONS. LASER RIFLE ION` | 显示名修正（notes 未写） |
| `generated_video_flow_settings` | −120 B | 两条音乐流程被删 | "Removed two music tracks" |

**交叉验证**：APEX 两处数值对上了；LAS-44 NOVA 无数据变化（与"只修显示"一致）；
SG-22 BUSHWACKER 405→486 / 108→135 在 damage 表里**没有**第二处改动 —— 正好印证 notes 里
"这是上一版算错的**更正**"（属文档更正，不是本版数据变化）。

`⚠ 未证（内容级）`：`generated_generation_settings.dl_bin` 旧明文集漏收（历史 dump 缺这一张），无法做**内容**对比。
但**几何对照**（`build_geometry_diff.py` 用 25988413 的 `table-geometry.json` 当基线）给出：
明文 10,396 B / 1 组 / 行数与步长**全同** ⇒ **结构未变**；本版 notes 也未涉及该表。

## 3 对既有结论的影响

| 结论类别 | 影响 |
|---|---|
| 实体 / 载具 / 座位 / 挂载（TD-220、Maelstrom、GATER、`SeatCollection +0x00`、`Mount`、`Health`、`Vehicle`） | **无影响**：`generated_entities.dl_bin` 逐字节未变 |
| 字段偏移 / 枚举 / 行结构 | **无影响**：typelib 逐字节未变 |
| 依赖"整表明文哈希"的锚点 | **必须换新值**（4 张表内容/尺寸变了；锚点在 `refs/build-diff-26251122.json` 与 `meta/fingerprint-26251122-vanilla.json` 里） |
| 旧 `.patch_N` 与旧封包 | **一律作废**，按新明文重封包 |

## 4 产物

| 文件 | 内容 |
|---|---|
| `refs/dlbin/plaintext-26251122/` | 56 个新明文（55 表 + typelib） |
| `refs/build-diff-26251122.json` | 结构层 diff（`build_diff.py`） |
| `refs/row-diff-generated_{projectile,damage,stratagem,video_flow}_settings.json` | 值级 diff |
| `tools/table_row_diff.py` | 新工具：组 / 字节 / 值级 diff（`--style groups\|chain`、`--stride`、`--match`） |
| `refs/build-geometry-diff-26251122.json` | 几何对照（基线 = 25988413 `table-geometry.json`）：55 张 → **53 张结构同**、2 张结构变（stratagem / video_flow） |
| 备份目录 `meta/fingerprint-26251122-vanilla.json` | 新 build 指纹（exe/runtime/plugins/bundles 头尾/55 表全 sha/buildid） |

## 5 遗留 TODO

1. `refs/table-geometry.json` 等**由旧 build 生成的缓存**要重跑（4 张表尺寸/内容变了）：
   `python tools/build_geometry_diff.py --sk refs/dlbin/keys/recipient.sk`。
2. 工具默认路径已切到 `refs/dlbin/plaintext-26251122/`（29 个 tool）。
3. 需要装回 mod 前，先按新明文重封包（旧封包不可复用）。
