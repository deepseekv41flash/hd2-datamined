# `zone_data` / `region_settings` 字段解明（build `26088801`，线上 schema 交叉）

> **一句话**：`zone_data` = **88 个 Zone（块序号 = `enum.ZoneId`）× 912 B**，一个 Zone 就是地形生成的一组
> 「材质 / 雾 / 高度 / 小地图 / 水体 / 巡逻 / 边界墙」参数；`region_settings` = **74 行 × 3,272 B 的
> `GenerationRegionSettings` + 13 组 `GenerationRegionGroup`（34 个变体列表 / 146 条变体 settings）**。
> 本次用线上 `shalzuth/HelldiversData` 的 `ZoneSettings.json` 补了 **18 个字段名**，并明确了线上 schema
> 是**旧版子集**（缺 `PatrolSetting`、`BoundaryWallSettings`、`LevelTags` 等本 build 字段）。

## 0. 三态

| 结论 | 态 | 证据 |
|---|---|---|
| `zone_data` = 88 行 × 912 B，块序号 = `ZoneId`，被 67/88 个 zone 引用 | **✓ 离线**（本仓库既有结论）| `LEVELGEN-FIELDS` §2/§3.1；`planet_data→…→zone` 438/438 全覆盖 |
| 18 个字段名（下表标 ✓）| **✓ 双源**：偏移/取值（本仓库）+ 名字与类型（线上 schema）| 线上 `data/components/ZoneSettings.json` 的字段名/类型逐一与我们的偏移+默认值对上（`water_height` 默认 −501 ↔ 实测 −500 一档、`player_kill_height` −100、`max_water_depth` 1、`scatter_setting` 是字符串…）|
| 5 个 `*_generators` 数组的名字 | **⚠ 顺序推断** | schema 里 5 个 `ShaderProperties` 数组的顺序，与本记录 `+0x020…+0x060` 五个 16 B DLArray 的偏移顺序一致；未逐字段验证 |
| `region_settings` 段 0/段 1 结构 | **✓ 离线** | `LEVELGEN-FIELDS` §3.2（`SubRegionSettings[16]` 的 `+0x004 = Zone` 是 join 键，876/876）|
| 线上 `RegionSettings.json`（4×`CApiVector2`）就是本表主结构 | **✗ 否** | 它只有 `start/control/end/normal` 四个 Vec2，更像**曲线/路径**子结构；本表段 0 是 44 成员的 3,272 B 记录，二者不是同一个东西（该 4-Vec2 在本表哪一段未定位）|

## 1. `zone_data` 字段表（912 B；块序号 = ZoneId）

名字列：**✓** = 与线上 schema 对上（值/类型双证）；**⚠** = 本仓库自证但 schema 无（本 build 新增）；**?** = 未解。

| offset | size | 字段 | 语义 / 实例值 | 证据 |
|---:|---:|---|---|---|
| `+0x000` | 16 | `ZoneTags` DLArray\<ZoneTag u8\> | 1–3 个 u8，值域 0..17 | ⚠ |
| `+0x010` | 16 | **`stamp_groups`** DLArray | 指向组尾的大数组（地形印章/拼块组）| ✓ |
| `+0x020` | 16 | **`color_variation_generators`** DLArray\<ShaderProperties\> | 颜色变化生成器链 | ⚠ 顺序推断 |
| `+0x030` | 16 | **`fog_volumes_generators`** DLArray\<FogVolumeShaderProperties\> | 雾体积生成器 | ⚠ 顺序推断 |
| `+0x040` | 16 | **`minimap_vizualisation_generators`** DLArray\<ShaderProperties\> | 小地图可视化生成器 | ⚠ 顺序推断 |
| `+0x050` | 16 | **`material_generators`** DLArray\<ShaderProperties\> | 地表材质生成器 | ⚠ 顺序推断 |
| `+0x060` | 16 | **`height_generators`** DLArray\<ShaderProperties\> | 高度场生成器 | ⚠ 顺序推断 |
| `+0x070` | 16 | 未定（schema 里疑为 `height_modification_curve`）| — | ? |
| `+0x080` | 16 | 未定 | — | ? |
| `+0x090` | 4 | **`default_material`** int32 | 该 zone 的默认材质 id | ✓ |
| `+0x094` | 12 | **`minimap_color`** Vec3 | 小地图配色 | ✓ |
| `+0x0A0` | 1 | **`minimap_terrain_type`** | 0 Open / 1 Difficult / 2 Rocky / 3 Vegetation / 4 Impassable / 5 Bug | ✓ |
| `+0x0A8` | 8 | **`scatter_setting`** DLString | 散布资源名（多为 −1/0）| ✓ |
| `+0x0C0` | 16 | **`camera_environment_effects`** DLArray\<CameraEffect\> | 相机环境效果 | ✓ |
| `+0x0D0` | 8 | **`wind_noise_ids`** `{u32 start, u32 end}` | 风声区间 | ✓ |
| `+0x0D8` | 8 | **`water_material`** ulong hash | 水材质资源 | ✓ |
| `+0x0E0` | 4 | **`water_level_offset`** f32（默认 0）| — | ✓ |
| `+0x0E4` | 4 | **`water_height`** f32（schema 默认 −501；实测常见 −500）| 水面高度 | ✓ |
| `+0x0E8` | 4 | **`water_zone_opacity_cutoff`** f32（默认 0.5）| 水体透明阈值 | ✓ |
| `+0x0EC` | 4 | **`max_water_depth`** f32（默认 1）| 最大水深 | ✓ |
| `+0x100` | 8 | **`reverb_zone`** DLString | 混响区（常见 −1）| ✓ |
| `+0x110` | 24 | **`quake_effect`** `QuakeEffectSettings` | 地震效果 | ✓ |
| `+0x128` | 1 | **`music_type`** | 0 None / 1 Bug | ✓ |
| `+0x129` | 1 | **`banter_event_type`** | 本 build 88/88 = 0 | ✓ |
| `+0x12C` | 4 | **`player_kill_height`** f32（默认 −100）| 掉落致死高度 | ✓ |
| `+0x130` | 40 | **`minimap_scatter`** `MinimapScatterSet` | 小地图散布 | ✓ |
| `+0x16C` | 4 | **`PatrolSetting`** | 0..3 四值（巡逻/刷怪节奏）| ⚠ 本 build 新增 |
| `+0x170..0x198` | 44 | **`PatrolFloat1..11`** f32 | 88 行只有 6 种组合 | ⚠ 本 build 新增 |
| `+0x1A0` | 4 | **`CityPlacementHeuristic`** | 0..5 六值（城市放置启发式）| ⚠ |
| `+0x208` | 16 | `LocationFlags[4]` u8×4 | 常见 (1,0,0,0) | ⚠ |
| `+0x218…` | 8×N | Curb / DetailUnit / TrafficLight 等 hash | 资源哈希 | ✓ |
| `+0x2B8` | 184 | **`BoundaryWallSettings`** | 边界墙参数 | ⚠ 本 build 新增 |
| `+0x370` | 16 | `RoadEmbankmentUnits` DLArray | 路堤单元 | ⚠ |
| `+0x380` | 16 | **`LevelTags[4]`** u32 | 关卡标签 | ⚠ |
| 其余 | | `UnkThinHash1..3`、`UnkBitfield1..3`、`UnkFloat1..4`、`Vectors1..3` | 未解 | ? |

**线上 schema 里有、本表尚未定位的 4 个字段**（说明 schema 与记录不是逐字段对齐）：
`material_lookup_unit`(ulong)、`weather_visibility`(f32, 默认 4)、`ambience_sound_id`(uint)、
`location_height_offset`(f32, 默认 0)、`height_modification_curve`(float 数组)。

## 2. 语义解读（这些字段合起来干什么）

- **`*_generators`（5 条）+ `stamp_groups`**：地形不是"手摆的"，而是**生成器链 + 印章拼块**。
  材质/颜色/雾/高度各有一条生成器数组，`stamp_groups` 提供可拼接的地形块集合。
- **水体/地震/风/混响/音乐/击杀高度**：都是**战斗与氛围参数**，改它们只影响局内体感，不改变地形拓扑。
- **`PatrolSetting` + 11 个 `PatrolFloat`**：本 build 独有的**刷怪/巡逻节奏**开关（88 行仅 6 种组合 ⇒ 是档位，不是自由数值）。
- **`BoundaryWallSettings` / `LevelTags` / `CityPlacementHeuristic`**：边界墙、关卡标签、城市放置——决定"这张图边缘长什么样、能不能出城市"。

## 3. `region_settings`（两段；详见 `LEVELGEN-FIELDS` §3.2）

| 段 | 规模 | 关键字段 | join |
|---|---|---|---|
| 段 0 `GenerationRegionSettings` | **74 行 × 3,272 B** | `+0x008` `EnvironmentalEffectType`；`+0x080` `SubRegionSpecialSettings[8]`；`+0x160` `RouteSettingReference[9]`；**`+0x238` `SubRegionSettings[16]`（68 B/条，`+0x004 = Zone`）**；`+0xA94` `LevelGenerationMode`；`+0xAB4` `SubRegionSettingsOverride[16]`（`+0x14 = StampRaceAffiliation`、`+0x18 = OperationType`）| `SubRegionSettings.Zone` → `zone_data` 块序号 |
| 段 1 `GenerationRegionGroup` | **13 组** | 组名（`region_sandy` 等）；`+0x30` `Lists` → 34 个变体列表（`Name`/`Id`，与 `planet_data.Region.Name/Id` 876/876 命中）；`+0x20` `Settings` → 146 条变体 settings（`+0x0C` = `LevelGenerationRegionVariantType`，`+0x30` = 段 0 引用，本 build 全是 −1）| 名字/Id 与行星行双向命中 |

**线上 `RegionSettings.json` 的定位**：它只定义 `start / control / end / normal` 四个 `CApiVector2`
—— **二次贝塞尔（起点/控制点/终点 + 法线）**，语义像"道路/墙/带状路径"，**不是** 3,272 B 的区域主记录。
本表哪一段用了这个 4-Vec2 结构，**未定位**（候选：`RouteSettingReference[9]` 的某个下游）。

## 4. 可以怎么改（本地、保哈希）

| 想改 | 动哪 | 风险 |
|---|---|---|
| 某 zone 的地表材质/配色/雾 | `+0x090` / `+0x094` / `+0x020`–`+0x060` 的生成器数组 | 低（数组本身在组尾，改指针要先确认目标资源驻留）|
| 水体（有没有水/多深）| `+0x0E0..+0x0EC` 四个 f32 + `+0x0D8` 材质 | 低 |
| 刷怪/巡逻节奏 | `+0x16C` `PatrolSetting`（0..3，档位）+ `PatrolFloat` | 低（只 6 种组合，改档比改 float 稳）|
| 城市/边界墙 | `+0x1A0` / `+0x2B8` | 中（可能影响导航/碰撞）|
| 换整颗星用哪套 region/zone | **不在本表** → `warinfo.settingsHash` | 需网络层（已验配方）|
| 改 region 名字 / `Id` | 段 1 的 `Name`/`Id` | **高**：join 按 `Id`/名字哈希，改了就断 |

## 5. 未解

1. `+0x070` / `+0x080` 两个 16 B DLArray 的身份；`+0x1A8..` 与 `Unk*` 系列；
2. 线上 `RegionSettings`（4-Vec2 曲线）在本表的位置；
3. `weather_visibility` / `ambience_sound_id` / `location_height_offset` / `height_modification_curve` 的偏移；
4. `PatrolSetting` 0..3 与 `PatrolFloat` 6 种组合的**语义对应**（需要进局对比刷怪密度）。

## 6. 来源

- 偏移/取值/join：本仓库 `docs/tables/LEVELGEN-FIELDS-26088801.md` §2/§3.1/§3.2（typelib + 实测）；
- 字段名/类型/默认值：线上 `shalzuth/HelldiversData` → `data/components/ZoneSettings.json`、
  `data/components/RegionSettings.json`（旧版 schema，字段是本 build 的子集）；
- 本表实例：`refs/dlbin/plaintext-26251122/generated_zone_data.dl_bin`、
  `generated_region_settings.dl_bin`。
