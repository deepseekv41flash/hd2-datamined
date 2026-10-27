# `generated_planet_data.dl_bin` 字段图 — build 26088801
> 入库版：本文由并行解码产出，已提升进 `docs/tables/`；批量探针脚本留在 `out/planet/`（可重跑、不入库），
> 一键复算脚本在 `tools/probes/planet/analyze_levelgen.py`。


> 只读侦察产物。输入是已解密的明文缓存 `D:/mod/refs/dlbin/plaintext-26088801/`，未启动游戏、未改任何文件。
> 行类型 `LevelGenerationPlanetData` = typelib id `0x08C2B982`，41 成员，size64 = 624，`438 组 × 1 行 + 每组 96~280 B 字符串尾`。
> 字段**名字与声明顺序**来自 filediver `datalibrary/planet_data.go` 的 Go 结构 `rawPlanetData`；
> 字节**偏移/宽度**来自本 build 的 typelib 成员表；两者用**真实行字节 + 4 段 padding + 4 个数组头 + 876 个 region join** 交叉验证。

三态口径：`✓ 离线` = 布局与语义都被本 build 数据独立证明（有可复现计数）；`⚠ 未证` = 布局已证，但语义只能靠上游命名或推断。

---

## 1. 容器形状（先认这个，否则解不出来）

```
file   = u32 group_count, then group_count × group
group  = 'LDLD' u32 version, u32 type_id, u32 payload_size, u32 wide, u32 flags   (24 B) + payload
payload= 1 行(624 B) + 字符串/数组尾巴          # 每个行星一个 group，438 个 group
行内指针 = payload 内偏移（不是文件偏移，也不是 VA）
数组    = (u64 offset, u64 count)；空数组编码为 offset = 0xFFFFFFFFFFFFFFFF, count = 0
```

* typelib 未覆盖的 4 段 padding 与 filediver 的 `_ [n]uint8` **完全对上**，这是对齐成功的第一证据：
  `[28,32)` ← `PlanetLayoutId` 后的 `[4]`、`[417,424)` ← `UnkEnum` 后的 `[7]`、`[468,472)` ← `ScatterSettings` 后的 `[4]`、`[620,624)` ← `UnknownFloat` 后的 `[4]`。
* payload 长度 720–904 B，尾巴里 3–5 个可见字符串（303 行 4 个、109 行 5 个、26 行 3 个）。

---

## 2. 41 成员逐字段表

| 偏移 | 宽 | 字段 | kind | 证据（本 build 实测） | 三态 |
|---:|---:|---|---|---|---|
| +0x000 | 8 | `Inherits` | 字符串指针 → `content/level_generation_settings/planet_settings/planet_setup/planet_<生态>` | 406/438 解析成功（例：`.../planet_homeworld_superearth`）；**32 行为 NULL**，恰是行 390–421 的模板行 | ✓ 离线 |
| +0x008 | 4 | `PlanetNameLoc` | locid (u32) | 438/438 非零；399/438 命中 `refs/locid-names.json` 的英文名；该文件 index→id 与本列 **0 处不符**（行 0 = 1441504339 = `SUPER EARTH`） | ✓ 离线 |
| +0x00C | 4 | `PlanetDescriptionLoc` | locid (u32) | **436/438 为 0**（本 build 无长描述），仅 2 行非零 | ✓ 离线 |
| +0x010 | 4 | `PlanetDescriptionShortLoc` | locid (u32) | 438/438 非零（无字符串索引可反查 → 内容未解） | ⚠ 未证 |
| +0x014 | 4 | `PlanetSystemNameLoc` | locid (u32) | 438/438 非零（同上，只有 id 没有串） | ⚠ 未证 |
| +0x018 | 4 | `PlanetLayoutId` | thin hash | 11 个不同值；**11/11 在同一 build 的 `generated_planet_territory_graphs` 字节流里出现** → 指向领土图 | ✓ 离线 |
| +0x020 | 8 | `MaterialLookupUnit1` | hash64 | 12 个不同值；在 54 张明文表里**只出现在本表** → 资源哈希，离线不可解析 | ⚠ 未证 |
| +0x028 | 8 | `MaterialLookupUnit2` | hash64 | 19 个不同值；同上 | ⚠ 未证 |
| +0x030 | 8 | `MaterialLookupUnit3` | hash64 | **只有 1 个值（438/438 相同）**；同上 | ⚠ 未证 |
| +0x038 | 16 | `OperationTags` | 数组 (u32, 4 B) | 430 行空；8 行各 1 项，值**恒为 3**（`OperationTag` 枚举，typelib 类型名 0xA73A9FED） | ✓ 离线 |
| +0x048 | 16 | `ResourceOverrides` | 数组 (3×hash64 = 24 B) | 430 行空；8 行各 3 项，且 24 个元素**只有 1 种取值**（`type` 恒 `0x0`）；typelib 类型名 `ResourceOverride` 0xB950E768 | ✓ 离线 |
| +0x058 | 8 | `DebugName` | 字符串指针 | 438/438 解析；**387/438 恰好 == `planet_{index:03d}`**；432 个不同值（32 个模板行用 setup 名） | ✓ 离线 |
| +0x060 | 40 | `RegionLowland` | 内嵌 `LevelGenerationRegion` (40 B) | 438/438 名字解析；见 §3 的 876/876 join | ✓ 离线 |
| +0x088 | 40 | `RegionHighland` | 内嵌 `LevelGenerationRegion` (40 B) | **与 lowland 438/438 完全相同**（名字/id/type/权重/未知浮点全等） | ✓ 离线 |
| +0x0B0 | 112 | `PaletteGroupLowland` | 内嵌 `LevelGenerationPaletteGroup` (112 B) | 438/438 解出 5 个哈希 + 1 thin hash + 15 个 float；15 个颜色分量全部落在 [0,1]；`color_set_internal_id` 恒 0；112 B 恰好用满（40+4+64+4） | ✓ 离线 |
| +0x120 | 112 | `PaletteGroupHighland` | 同上 | **与 lowland 438/438 完全相同** | ✓ 离线 |
| +0x190 | 8 | `ScenarioSettingsLowland` | hash64 | 33 个不同值；**33/33 在 `generated_scenario_settings` 出现** | ✓ 离线 |
| +0x198 | 8 | `ScenarioSettingsHighland` | hash64 | 与 lowland **438/438 相等** | ✓ 离线 |
| +0x1A0 | 1 | `UnkEnum` | u8 枚举（typelib 类型 0x12FDF387，无名字） | 只有 2 个值：1 → 334 行，2 → 104 行；**36/36 个 setup 内取值唯一**（每个 `Inherits` leaf 只对应一个值） | ⚠ 未证 |
| +0x1A8 | 16 | `GameplayModifiers` | 数组 (hash64, 8 B) | 222 行空 / **216 行各 1 项**；**只有 8 个不同 hash**；8/8 是 `generated_entities` 的 entity key；其中 6 个以连续 8 B 数组出现在 `galactic_presence_settings` | ⚠ 未证 |
| +0x1B8 | 4 | `PlanetType` | 枚举 `PlanetType` (0x29EED886) | **12 个值，与 filediver 枚举名 1:1**（2=arctic … 16=rift）；**36/36 setup 内唯一** | ✓ 离线 |
| +0x1BC | 4 | `Unknown` | thin hash | 33 个不同值；203/438 与 `ScatterSettings` 相等；25/33 出现在 `planet_override_settings` | ⚠ 未证 |
| +0x1C0 | 16 | `NatureLocationTags` | 数组 (u32, 4 B) | **438/438 全空**（`-1:0`）→ 本 build 死字段 | ✓ 离线 |
| +0x1D0 | 4 | `ScatterSettings` | thin hash | 23 个不同值；11/23 在 `environment_settings`、12/23 在 `planet_override_settings`（无唯一归属 → 语义未证） | ⚠ 未证 |
| +0x1D8 | 8 | `MissionPlanetUnit` | hash64 | 25 个不同值；54 张表里只出现在本表 | ⚠ 未证 |
| +0x1E0 | 8 | `MissionPlanetHologramUnit` | hash64 | 26 个不同值；同上 | ⚠ 未证 |
| +0x1E8 | 8 | `MissionPlanetUnitPackage` | hash64 | 25 个不同值；同上 | ⚠ 未证 |
| +0x1F0 | 8 | `MissionPlanetHologramUnitPackage` | hash64 | 26 个不同值；同上 | ⚠ 未证 |
| +0x1F8 | 8 | `SolarSystemSettings` | hash64 | **438/438 同值 `0x257c4a1807d825fc`**，且 == `generated_solar_system_settings` 的 `payload[0:8]`（该表只有 1 条记录）→ 全局配置引用，非按行星 | ✓ 离线 |
| +0x200 | 16 | `SolarSystemIdSelections` | 数组 (hash64, 8 B) | 每行 1~3 项（183/169/86）；47 个不同值，**47/47 在 `solar_system_settings` 出现** | ✓ 离线 |
| +0x210 | 16 | `SampleTypes` | 数组 (u32, 4 B) | **438/438 每行 2 项**；437 行 == `[9,9]`（`SampleType` 9 = Uranium）；唯一例外 #420 `planet_tutorial` == `[7,6]`（Oil, Artifact） | ✓ 离线 |
| +0x220 | 4 | `AmbienceSoundIdStart` | u32（Wwise id） | 26 个不同值；非哈希空间，无可 join 的表 | ⚠ 未证 |
| +0x224 | 4 | `AmbienceSoundIdStop` | u32（Wwise id） | 10 个不同值；同上 | ⚠ 未证 |
| +0x228 | 8 | `HologramPlanetMaterial` | hash64 | 29 个不同值；只在本表 | ⚠ 未证 |
| +0x230 | 8 | `PlanetPreviewImage` | hash64 | 32 个不同值；只在本表 | ⚠ 未证 |
| +0x238 | 16 | `ResourceRegionOverrides` | 数组 `{thin hash, u32 flag}` (8 B) | 每行 1~3 项（10/276/152）；44 种组合；flag 只有 0(866) / 3(152)；两个分量都未解析 | ⚠ 未证 |
| +0x248 | 8 | `ShadingEnvironmentEntity` | hash64 | 30 个不同值；9/30 在 `environment_settings` 出现（其余只在实体/本表） | ⚠ 未证 |
| +0x250 | 8 | `WaterEntity` | hash64 | 30 个不同值；只在本表 | ⚠ 未证 |
| +0x258 | 8 | `HeathazeEntity` | hash64 | **342 行为 0**，96 行同 1 个值 `0xe413e7ce9aae27b4` → 二值资源开关 | ✓ 离线 |
| +0x260 | 8 | `PackagePath` | hash64 | 31 个不同值；只在本表；`planet-data.json` 里按仓库惯例以 `addpath` 输出 | ⚠ 未证 |
| +0x268 | 4 | `UnknownFloat` | f32 | **438/438 == 1.0**（常量），字段名与"未知"一致但实际是常数字段 | ✓ 离线 |

`RegionLowland/Highland` 内层（40 B，逐字节验证）：`+0 Name(8) | +8 Id(4) | +12 Type(4) | +16 Variants(8, 恒 -1=null) | +24 Weight(f32, 恒 1.0) | +28 UnknownFloat(f32, 恒 1.0) | +32 UnknownInt(u32, 恒 0) | +36 pad(4)` → 876/876 侧全部符合。

`PaletteGroup` 内层（112 B）：`5×hash64(asset/sky/day/night/sunset grading, 40 B) | thin hash(planet_color_set, 4) | 内部 color set {thin hash id(4) + 5×Vec3(60)} | pad(4)`；5 组颜色按 filediver 命名依次是 main / secondary / **bugs** / **bots** / **illuminate**（注意后三个是**雾色**，与敌人无关，见 §6）。

---

## 3. 关联表 join 全景（本 build 实证）

| 本表字段 | 目标表 | join key | 命中 |
|---|---|---|---|
| `RegionLowland/Highland.Name` | — | 名字字符串（同 payload 内指针） | 876/876 |
| `RegionLowland/Highland.Id` | **`generated_region_settings` 的第二个容器** | 4 B thin hash | **876/876 命中 34 条 region 记录中的 32 条** |
| `RegionLowland/Highland.Type` | 同上 | 4 B = 该记录在 region 表里的 **1-based 序号** | **876/876 相等**（`LevelGenerationRegionType` 枚举 0–34，值 8 与 31 对应两条"没有任何行星引用"的记录：`region_sandy_cyborg_factory` / `region_swamp_variant_02`） |
| `PlanetType` | 无（纯枚举） | — | 12/18 个枚举值被使用（0/1/4/5/7/17 未用） |
| `PlanetLayoutId` | `generated_planet_territory_graphs` | 4 B thin hash | 11/11 |
| `ScenarioSettings*` | `generated_scenario_settings` | hash64 | 33/33 |
| `SolarSystemSettings` | `generated_solar_system_settings` | hash64（全局 1 条） | 438/438 |
| `SolarSystemIdSelections[]` | `generated_solar_system_settings` | hash64 | 47/47 |
| `GameplayModifiers[]` | `generated_entities`（entity key） | hash64 | 8/8（其中 6 个也在 `galactic_presence_settings`） |
| `Unknown` / `ScatterSettings` | `planet_override_settings` / `environment_settings` | thin hash | 25/33、11–12/23（归属不唯一 → 未证） |
| `MissionPlanet*`、`PackagePath`、`WaterEntity`… | 无（bundle 资源哈希） | — | 0 命中 |

**region 表在哪里（最关键的一条）**：`generated_region_settings.dl_bin` 不是单容器，而是**两个 LDLD 容器首尾相接**：
前 74 组 = `GenerationRegionSettings`（每行 3272 B，工具正常解析），紧随其后 `u32 0x0D` + 13 组 `GenerationRegionGroup`（0x8F1179FD，**共 15,719 B**）。
工具报的 `! 15719 B after the last group` 就是这 13 组。每组 = `64 B 头 + 组名(如 region_sandy) + 子 region 数组(48 B/项)`：

```
GenerationRegionGroup(64 B): +0 组名指针 | +8 组 id | +0x10/+0x18 hash | +0x20 thin hash
                             | +0x24 3×f32 | +0x30 (offset,count) 子 region 数组
子 region(48 B): +0 名字指针 | +8 id | +12 (恒 0) | +0x10/+0x18 hash
                 | +0x20 (offset,count) 孙级子区域（mountain_islands/shared_city 等）
```

13 个族：`region_generation_testing / sandy / primordial / magma / rift / coniferous / arctic / moor / superearth / deciduous / swamp / oasis / bug_hiveworld`，共 34 条子 region；行星引用其中 32 条。

---

## 4. `PlanetType` 分布（12 个值 ↔ 12 组生态，1:1）

| 值 | 枚举名（filediver） | 行数 | 对应 `Inherits` setup 家族 |
|---:|---|---:|---|
| 2 | `arctic` | 48 | arctic_glacier_base / coldrocky / cyberstan / tien_kwan |
| 3 | `sandy` | 101 | desert_sandy_base / acid / mineral / moon / spiky / klen_dahth_2 |
| 6 | `swamp` | 32 | forest_swamp_base / haunted |
| 8 | `primordial` | 88 | forest_primordial_base / blue / purple / dead / base_bug |
| 9 | `moor` | 94 | forest_moor_base / tundra / red / arid / hellmire |
| 10 | `superearth` | 2 | homeworld_superearth |
| 11 | `bug_hiveworld` | 8 | bug_hiveworld / hiveworld_moor_* / hiveworld_sandy_* |
| 12 | `magma` | 12 | desert_magma_base |
| 13 | `oasis` | 15 | desert_oasis_base / bleak |
| 14 | `deciduous` | 25 | forest_deciduous_base / autumn / crimson |
| 15 | `coniferous` | 10 | forest_coniferous_base |
| 16 | `rift` | 3 | forest_rift_active |

"熟悉的大生态组"= 2/3/12/13（冰原、沙漠/沙丘、熔岩、绿洲）与 8/9/14/15/16（原始林、荒原、落叶林、针叶林、裂隙）+ 6 沼泽；`0 forest / 1 desert / 4 savanna / 5 rocky / 7 snowy_forest` 在本 build **一次都没用到**（通用生态已被细分生态取代）。

---

## 5. 关键发现（改动/复刻时有用的）

1. **`planet_type` 是唯一的"生态选择器"**：它与 `Inherits` setup、`RegionLowland.Name`、`UnkEnum` 三者 36/36 setup 纯对应。改一个字段等于换整套生态。
2. **lowland / highland 是占位重复**：`RegionLowland==RegionHighland`、`PaletteLowland==PaletteHighland`、`ScenarioSettingsLowland==ScenarioSettingsHighland`，438/438 全等。真正的高地/低地区分在 region 记录的"孙级子区域"里，不在这张表。
3. **`Region.Type` 不是语义枚举，是表内序号**：876/876 == region 记录 1-based 序号。用它当语义去猜会全错。
4. **模板行**：行 390–421（32 行）`Inherits=NULL`、`DebugName` 恰好等于 setup 名（`planet_arctic_glacier_base` …）、`name locid` 仍非零。它们不是"真实星球"，据名 join 会被骗。
5. **样本字段不是数量**：`SampleTypes` 每行恒 2 项，437 行 = `[Uranium, Uranium]`，教程行星 = `[Oil, Artifact]`。
6. **修饰符 = 8 个 entity 哈希**，216 行各 1 个，按生态聚集（如 `0x9080b0090bc6f3ab` 只在 sandy、`0xd65b304d05cf9820` 只在 arctic）；在 `generated_entities` 里都是 `kind=other` 且**无百科条目 → 名字仍是 未知**。
7. **`OperationTag`/`ResourceOverrides` 只出现在 8 行**（`bug_hiveworld` 系 + `planet_generation_testing`），是内容/测试专用覆写，不是通用字段。

---

## 6. 这张表里**没有**敌人/阵营选择器（为"Predator strain 能不能靠改本地表实现"服务）

对 41 个成员逐个核对（上表），本表**不存在** race / faction / enemy type / unit list / presence 类字段：

* 全部字段类型只有：路径指针×2、locid(u32)×4、hash64×15、thin hash×4、数组×7（OperationTag、ResourceOverride、GameplayModifier、NatureLocationTag、SolarSystemIdSelection、SampleType、ResourceRegionOverride）、内嵌结构×4（Region×2、Palette×2）、u8×1、u32×2、f32×1。
* 唯一的枚举是 `PlanetType`（生态）、`UnkEnum`（2 值，100% 由 setup 决定）、`SampleType`、`OperationTag`；**没有 `RaceType`**。
* `palette` 里的 `bugs / bots / illuminate` 是**雾的染色**（3 个 Vec3），属于视觉参数，不是敌人选择。
* 对照：`RaceType`（typelib 0x41DCECBD）出现在 **`generated_planet_region_settings` +0x18** 与 **`generated_galactic_presence_settings` +0x1C**；后者（137 行 × 1000 B）还带 `PlanetSelectableType`(+0x114)、`WeatherType`(+0x1B8)、`SubRegionSettingsOverride`(+0x280)，才是"行星在星系/战线上的阵营与存在性"那一层。`EnemyTag` 则出现在 `location_groups` / `satellite_groups`（见 `out/planet/_probe_enemytag.py`，另一路侦察）。
* 结论：**✗ 否** —— 本表没有任何字段能把某个行星切成"普通虫族 / Predator strain"这类敌人变体；`planet_type` 只切生态，8 个 `gameplay_modifiers` 是环境修饰 entity。

---

## 7. 复现命令（全部只读）

```bash
cd D:/mod/work/repo-datamined
python tools/planet_tables.py survey                     # 438 组 / stride 624 / 尾 3504 B（见坑 1）
python tools/planet_tables.py fields planet_data         # 41 成员 typelib 表
python tools/planet_tables.py dump planet_data --limit 2 # 顶层指针/数组/标量（注意坑 3）
python tools/typelib.py show D:/mod/refs/dlbin/plaintext-26088801/dl_library.dl_typelib LevelGenerationPlanetData
```

本文所有计数由 `/tmp` 下的临时解码脚本产出（未落进仓库）；生成物只有
`out/planet/planet-data.json`（438 行 × 41 字段全量 + join 结果）与本文。
关键词自查：

```python
# 1) 876/876 region join：region 表 = generated_region_settings 第二个容器（13 组）
# 2) 216 行带 gameplay_modifiers，8 个不同值
# 3) 12 个 planet_type 值 ↔ filediver enum.PlanetType
```

---

## 8. 坑（给下一个人）

1. **`parse_groups()` 只走一个容器**。`generated_region_settings` 是 `74 组 + u32(0x0D) + 13 组`；不跨过那个 u32，就会把 region 定义当成"15719 B 残余字节"，从而误判"region 无处可 join"。
2. **`dump` 的数组判据是 `msize==16 and type_id!=0`**。`GameplayModifiers(+0x1A8)` 与 `SolarSystemIdSelections(+0x200)` 在 typelib 里 `type_id==0`，会被当成 16 B 十六进制标量打印（空数组显示成 `ffffffffffffffff0000…`）。`NatureLocationTag(+0x1C0)` 有类型，才能正常显示成 `-1:0`。
3. **`survey` 的 `tailB` 不能当"尾巴大小"用**：它按 `size//stride` 猜行数，`solar_system_settings`（1 组 91736 B）会被报成 3822 行 × 24 B ——实际上那是"1 行头 + 变长 blob"。`planet_data` 恰好 1 组 1 行才准确。
4. **`strings_in()` 会把 float 当字符串**（`B\i`、`?333?`、`.Q ` 之类），用它判断"有没有名字"会误报；尾串必须用 `cstr_at()` 按指针解。
5. **`region.type` 与 `planet_type` 都是"魔法数字"**，前者是 region 表序号（34 项，缺 8/31），后者才是生态枚举；两者恰好都连续，很容易看混。
6. **`region_settings` 的 row 0 名字是空串**（`+0x0 → 129` 指向 1 字节 `\0`），若按"名字非空"筛行会一行都筛不到 —— 名字在第 75–87 个 group 的第二容器里。
