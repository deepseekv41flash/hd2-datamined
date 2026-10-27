# 关卡生成链表：字段图 + 本地敌人组成开关判定（build 26088801）
> 入库版：本文由并行解码产出，已提升进 `docs/tables/`；批量探针脚本留在 `out/planet/`（可重跑、不入库），
> 一键复算脚本在 `tools/probes/planet/analyze_levelgen.py`。


> 状态：**✓ 离线**（只读静态解析，2026-10-27；输入 `D:/mod/refs/dlbin/plaintext-26088801/`）。
> 数据产物：`out/planet/levelgen.json`。字段名来自 filediver Go 结构；**偏移一律以 typelib 为准**
> （本 build 的 padding 与 Go 结构不同，见 §9 坑 2）。

---

## 0. 判定（先看这 6 行）

1. **✗ 8 张目标表里没有本地敌人组成 / patrol 选择器。** 没有 `EnemyTag`、没有 `EnemyPackage` 引用、
   没有 presence 的两个 u64 引用；`zone_data` 只有 4 值 `PatrolSetting` + 11 个由预设派生的 float。
2. **✓ 整条 levelgen 链能闭合到 zone**：`planet_data`（438 行星）→ region 变体（34 个列表，Name/Id/Type
   三键 876/876 全命中）→ 变体 settings（146 条，`LevelGenerationRegionVariantType` 枚举）→
   `region_settings` 段 0 的 74 行（⚠ 行号 = 枚举值 − 1）→ `SubRegionSettings[16].Zone`（ZoneId）
   → `zone_data` 的块序号（= `enum.ZoneId`，0..87）。覆盖率：**438/438 行星能落到 zone，67/88 个 zone 被引用**。
3. **✓ presence 在本 build 里只被"星图标记实体"引用**：`generated_entities.dl_bin` 的
   `ShowOnMapComponentData +0x8` 命中 3 处（都是 presence 行 97 的 +0x28）；**54 张表扫完，其它 0 命中**。
4. **✓ 唯一带敌人语义的字段在 `location_groups`/`satellite_groups` 的 `LocationStampInfo`**：
   `EnemyTag(+0xD0)`、`GuardForceType(+0x15F)`、`StampRaceAffiliation(+0xE8)`。
   但本 build 里 `EnemyTag` **1014/1019 = 0**（只有 5 个非零：2、9、4）。
5. **✓ presence 唯一被关卡生成侧"消费"的地方是天气**：`weather_settings` 里 6 条
   `content/level_generation_settings/galactic_presence_overrides/weather_settings/*` 路径
   （gloom / hiveworld_clear / illuminate_ritual_storm…），**没有敌人侧 override**。
6. 结论：**变种敌人（掠食/孢裂…）没有本地数据开关**；本地能改的只有"巡逻预设 / 阵营门控 / 敌人标签
   （本 build 几乎全 0）"三类，见 §8。要等价 variant_mod 必须继续走 presence（服务端）路线。

---

## 1. 复现命令

```bash
# 表清单（工具会打印 "! N B after the last group"，那正是本文件要纠的坑）
python tools/planet_tables.py survey

# 行类型成员（offset/size/type）
python tools/planet_tables.py fields zone_data
python tools/planet_tables.py fields region_settings

# 本报告所有数字（一次跑完，产出 out/planet/levelgen.json）
python tools/probes/planet/analyze_levelgen.py

# 探针（各自复跑）
python out/planet/_probe_zone.py        # zone_data 88 行 + presence 137 行基础分布
python out/planet/_probe_sections.py    # 每文件的分段（发现 region_settings 有第二段）
python out/planet/_probe_presence.py    # PatrolSetting × PatrolFloat 组合
python out/planet/_probe_enemytag.py    # location/satellite 的 EnemyTag/GuardForce 分布
python out/planet/_probe_xref.py        # presence u64 × 全部表（充分性检索）
python out/planet/_probe_types.py       # 全部表的类型树语义字段扫描
```

---

## 2. 表几何（先纠 3 个数字：zone_data 是 88 行不是 517）

| 表 | 文件 B | 段 | 组 | 真实行数 | stride | 行类型 | 形态 |
|---|---:|---:|---:|---:|---:|---|---|
| `zone_data` | 518,478 | 1 | 88 | **88**（不是 517） | 912 | `ZoneSettings` | 1 行/组 + 组内数组尾（payload 913..11,968） |
| `region_settings` | 259,627 | **2** | 74 + 13 | 74（段0）+ 13（段1 区域组） | 3,272 / 64 | `GenerationRegionSettings` / `GenerationRegionGroup` | 段1 才是带 region 名字的变体列表 |
| `planet_region_settings` | 61,485 | 1 | 369 | 369 | 128 | `PlanetRegionSettings` | 1 行/组 + 1 B 尾；城市/区域模板 |
| `planet_types_settings` | 16,844 | 1 | 1 | 88 | 24 | `SolarSystemObjectType` | **容器** `(offset=16,count=88)` |
| `scenario_settings` | 8,092 | 1 | 39 | 149 | 48 | `ScenarioSettings` | 2..8 行/组 |
| `solar_system_settings` | 91,764 | 1 | 1 | 3,822 | 24 | `SolarSystemSettings` | 1 组 3,822 行 + 8 B 尾 |
| `modifier_settings` | 1,764 | 1 | 15 | 52 | 24 | `Modifier` | 1..8 行/组 + 8 B 尾 |
| `planet_color_set_settings` | 1,964 | 1 | 1 | 30 | 64 | `PlanetColorSet` | **容器** `(16,30)` |
| 参考：`galactic_presence_settings` | 155,853 | 1 | 137 | 137 | 1,000 | `(未命名)` | 1 行/组 + 尾部字符串 |
| 参考：`location_groups` | 397,106 | 1 | 13 | 13 组 / **1,019 LocationStampInfo** | 56 | `LevelGenerationLocation` | 行 → DLArray<LocationGroup> → DLArray<LocationStampInfo> |
| 参考：`satellite_groups` | 83,413 | 1 | 36 | 36 组 | 24 | `LevelGenerationSatelliteGroup` | 同上（卫星件） |

> `zone_data` 的"517 行"= `Σ size//912`（把组内数组尾当成行）。真实是 **88 行**，正好等于
> `enum.ZoneId` 的 88 个值（UNKNOWN + 87 + NUM_ZONES）——这才是 zone 的行身份。

---

## 3. 字段图

三态：**✓ 离线** = 布局/数据证明；**⚠ 未证** = 推断；**✗ 否证** = 查过不成立。
（"evidence" 都可用 §1 命令复现；未列出的成员用 `fields <table>` 直接看。）

### 3.1 `zone_data.ZoneSettings`（912 B × 88；块序号 = ZoneId）

| offset | size | name | evidence | 三态 |
|---:|---:|---|---|---|
| +0x000 | 16 | `ZoneTags` DLArray<ZoneTag(u8)> | 88/88 行都能解出数组，元素 1~3 个、值域 0..17 | ✓ |
| +0x010 | 16 | `StampGroups` DLArray<StampGroup> | 88/88 可解，指向组内尾（大数组） | ✓ |
| +0x020..0x080 | 16×7 | ShaderProperties/FogVolume 等 DLArray | 多数组，偏移指向组尾 | ✓ |
| +0x090 | 4 | `DefaultMaterial` (int32) | 标量 | ✓ |
| +0x094 | 12 | `MinimapColor` Vec3 | 3 × f32 | ✓ |
| +0x0A0 | 1 | `MinimapTerrainType` | 观察值 0..5 = 枚举 6 值（Open/Difficult/Rocky/Vegetation/Impassable/Bug） | ✓ |
| +0x0A8 | 8 | `ScatterSetting` DLString | 多为 -1/0 | ✓ |
| +0x0C0 | 16 | `CameraEnvironmentEffects` DLArray | 88/88 可解 | ✓ |
| +0x0D0 | 8 | `WindNoiseSettings` | {u32 start,u32 end} | ✓ |
| +0x0D8 | 8 | `WaterMaterial` Hash | 水材质资源哈希 | ✓ |
| +0x0E0..0x0EC | 4×4 | WaterLevelOffset/WaterHeight/OpacityCutoff/MaxWaterDepth | 常见 (-500, 0.5, 1, …) | ✓ |
| +0x100 | 8 | `ReverbZone` DLString | 常见 -1 | ✓ |
| +0x110 | 24 | `QuakeEffectSettings` | 24 B 子结构 | ✓ |
| +0x128 | 1 | `ZoneMusicType` | 88 行只有 0(None)/1(Bug) | ✓ |
| +0x129 | 1 | `BanterEventType` | **88/88 = 0** | ✓ |
| +0x12C | 4 | `PlayerKillHeight` f32 | 常见 -100 | ⚠ |
| +0x130 | 40 | `MinimapScatter` MinimapScatterSet | 子结构 | ✓ |
| +0x15C/0x160/0x164 | 4×3 | UnkThinHash1..3 | 0 | ⚠ |
| +0x168 | 1 | UnkBitfield1 | 常见 32 | ⚠ |
| **+0x16C** | **4** | **`PatrolSetting`** | 88/88，值 0..3 = 枚举 4 值 | **✓** |
| **+0x170..0x198** | **44** | **`PatrolFloat1..11`** | 88 行只有 6 种组合（§4.3） | **✓** |
| +0x19C/0x19D | 1+1 | UnkBool1/UnkBitfield2 | 0/1 | ⚠ |
| +0x1A0 | 4 | `CityPlacementHeuristic` | 观察 0..5 = 枚举 6 值 | ✓ |
| +0x1A4 | 4 | UnknownEnum | 0 | ⚠ |
| +0x1B0/0x1C8/0x1E0 | 24×3 | Vectors1..3（3×Vec2） | 38 行有值，其余 0 | ⚠ |
| +0x1F8..0x204 | 4×4 | UnkFloat1..4 | 常见 3.4e38 | ⚠ |
| +0x208 | 16 | `LocationFlags[4]`（u8×4） | 常见 (1,0,0,0) | ✓ |
| +0x218..0x2A8 | 8×N | Curb/DetailUnit/TrafficlightPrefab 等 Hash | 资源哈希 | ✓ |
| +0x2B8 | 184 | `BoundaryWallSettings` | 子结构 | ✓ |
| +0x370 | 16 | `RoadEmbankmentUnits` DLArray | 数组 | ✓ |
| +0x380 | 16 | `LevelTags[4]`（LevelGenerationTag u32） | 4×u32 | ✓ |
| +0x388 | 1 | UnkBitfield3 | 0 | ⚠ |

### 3.2 `region_settings`（两段）

**段 0：`GenerationRegionSettings` 3,272 B × 74 行**

| offset | size | name | evidence | 三态 |
|---:|---:|---|---|---|
| +0x000 | 8 | `UnkRegionHash` Hash | 3 个不同值（68/74 相同 0x9924738AF17B9252）→ 不是行身份 | ⚠ |
| +0x008 | 4 | `EnvironmentalEffectType` | 枚举 | ✓ |
| +0x00C..0x054 | 4×19 | 环境参数（雾/风/雨等 f32） | 观察大量 0/1/2.75/35/50/256/-500/0.9/0.25 | ⚠ |
| +0x080 | 224 | `LevelGenerationSubRegionSpecialSettings[8]`（28 B/条） | 8 = 224/28 | ✓ |
| +0x160 | 216 | `RouteSettingReference[9]`（24 B/条） | 9 = 216/24 | ✓ |
| **+0x238** | **1,088** | **`SubRegionSettings[16]`（68 B/条）** | 16 = 1088/68；其中 **`+0x004 = Zone (ZoneId)`** → zone_data 块序号 | **✓** |
| +0x67C/0x680 | 4+4 | f32（90 / 1.0 常见） | | ⚠ |
| +0x684 | 524 | MissionType/SubRegionType 混合数组（任务池） | 子结构里有 `MissionType`（16 B）等 | ✓ |
| +0x894 | 512 | LevelGenerationTag 数组 | | ⚠ |
| +0xA94 | 1 | `LevelGenerationMode` | 枚举 | ✓ |
| +0xA95 | 4 | `RegionFlag` | 枚举位 | ✓ |
| **+0xAB4** | **512** | **`SubRegionSettingsOverride[16]`（32 B/条）** | 16 = 512/32；**`+0x14 = StampRaceAffiliation`（1 B 位掩码）**、`+0x18 = OperationType` | **✓** |
| +0xCB4..0xCC4 | 4×4 | 尾部标量 | | ⚠ |

**段 1：`GenerationRegionGroup` 13 组 → 34 个变体列表 → 146 条变体 settings**

| 层 | offset | size | name | evidence | 三态 |
|---|---:|---:|---|---|---|
| Group | +0x00 | 8 | `Name` DLString | 13/13 解成 `region_sandy` 等 | ✓ |
| Group | +0x30 | 16 | `Lists` DLArray<GenerationRegionVariantList(48)> | 13 组共 34 条 | ✓ |
| List | +0x00 | 8 | `Name` DLString | 34/34 解成 `region_sandy_base` 等；**与 planet_data.Region.Name 876/876 命中** | ✓ |
| List | +0x08 | 4 | `Id` ThinHash | **与 planet_data.Region.Id 876/876 命中** | ✓ |
| List | +0x20 | 16 | `Settings` DLArray<GenerationRegionVariantSettings(56)> | 共 146 条 | ✓ |
| Settings | +0x00 | 8 | `Name` DLString | 146/146（46 个不同名，如 `region_shared_city`） | ✓ |
| Settings | +0x08 | 4 | ThinHash（46 个唯一） | 不等于行星 Region.Id（6/876 巧合） | ✓ |
| Settings | **+0x0C** | **4** | **`LevelGenerationRegionVariantType`** | 146 条值 5..74，46 个不同值 = 枚举 0..74 子集 | **✓** |
| Settings | +0x10 | 4 | Weight f32 | 1.0 常见 | ✓ |
| Settings | +0x30 | 8 | `GenerationRegionSettings` 引用 | **146/146 = -1（本 build 未用）** | **✗** |

### 3.3 `planet_region_settings.PlanetRegionSettings`（128 B × 369）

字段名来自 filediver `planet-region-settings-json-dumper`（顺序与 typelib 一致）：

| offset | size | name | evidence | 三态 |
|---:|---:|---|---|---|
| +0x00 | 8 | `Template` DLString | 24 行解出 `.../city_settings/templates/cyberstan_city_template`、`factory_city_template`；其余空 | ✓ |
| +0x08 | 4 | `UnkThinHash0` | 367 唯一 | ✓ |
| +0x0C | 4 | `UnkThinHash1` | 18 唯一 | ⚠ |
| +0x10 | 8 | `RegionPreviewTexturePath` Hash | 4 个不同值 | ⚠ |
| **+0x18** | **4** | **`RegionRaceType`** | **1(SuperEarth)=344、3(Cyborg)=25**，无 Bugs/Illuminate | **✓** |
| +0x20 | 16 | `OperationTags` DLArray | 369/369 = (-1,0) 空 | ✓ |
| +0x30 | 4 | `UnkInt0` | 0=344、4=25（与 Cyborg 行重合） | ⚠ |
| +0x34 | 4 | `UnkInt1` | **369/369 = 99** | ✓ |
| +0x38 | 4 | `RegionOperationType` | 14=360、13=9 | ✓ |
| +0x40/0x58/0x68 | 16×3 | UnkThinHashes0/1、UnkEnumItems | 多为空 | ⚠ |
| +0x50 | 4 | `UnkEnumType` | 0 | ⚠ |
| +0x78 | 4 | `UnkInt2` | 0..8 | ⚠ |

### 3.4 `planet_types_settings` / `solar_system_settings`

| 表 | offset | size | name | evidence | 三态 |
|---|---:|---:|---|---|---|
| planet_types | +0x00 | 8 | 行星类型 Hash | 容器 `(16,88)` → 88 条，每条第 1 个 8 B = 类型哈希 | ✓ |
| planet_types | +0x08 | 16 | `SolarSystemObjectTypeSettings` DLArray | 88/88 可解 | ✓ |
| solar_system | +0x00 | 8 | 行星类型 Hash | 3,822 行 | ✓ |
| solar_system | +0x08 | 16 | `SolarSystemSetting` DLArray | 行内数组；尾部 52 个 `planet_*` 名字符串（`planet_bug_hiveworld_01`…）| ✓ |

### 3.5 `scenario_settings.ScenarioSettings`（48 B × 149）

行 = `{u64 @+0, u64 @+8, u64 @+0x10, u32 @+0x18, DLArray<ScenarioSetting> @+0x20}`。
类型树递归到深度 5 **没有任何 enemy/spawn/faction/team 字段**；无有效字符串（16 条全是二进制噪声）。

| offset | size | name | evidence | 三态 |
|---:|---:|---|---|---|
| +0x00/+0x08/+0x10 | 8×3 | 未命名哈希/ID | 39 组 149 行，每行不同 | ⚠ |
| +0x18 | 4 | 未命名 u32 | 常见 0xFFFFFFFF | ⚠ |
| +0x20 | 16 | `ScenarioSetting` DLArray | 指向组内数组 | ✓ |
| — | — | **敌人语义** | 递归扫描 0 命中 | **✗** |

### 3.6 `modifier_settings` / `planet_color_set_settings` / `planet_override_settings`

* `Modifier`（24 B × 52）：`{u32 @0, u8 @4, DLArray<ModifierGroup> @8}`；只有 1 条噪声字符串 —— 无敌人字段。
* `PlanetColorSet`（64 B × 30，容器）：1 个 ThinHash + 5 × Vec3 颜色（fog main/secondary/bugs/bots/illuminate）——
  只有**颜色**区分阵营（`ZoneFogBugsColor` 等），不是组成。
* `PlanetOverrideSettings`：13 组（44/248/… 行），`PlanetOverrides` DLArray；仅 1 条 `swamp_variant_02` 字符串 —— 无关。

### 3.7 `location_groups` / `satellite_groups` 的 `LocationStampInfo`（456 B）

| offset | size | name | evidence | 三态 |
|---:|---:|---|---|---|
| +0x000 | 104 | `StampInfo`（含 Stamp DLPtr、Path Hash、Weights） | 1,017/1,019 唯一 | ✓ |
| +0x0A8 | 1 | `ModifierLocationTag` | 1019/1019 = 0 | ✓ |
| +0x0B0 | 16 | `NatureLocationTag` DLArray | 1019/1019 = (-1,0) 空 | ✓ |
| +0x0C0 | 16 | `MissionLocationTag` DLArray | 763 个不同数组 | ✓ |
| **+0x0D0** | **4** | **`EnemyTag`** | **1014/1019 = 0；非零只有 2(×2)、9(×2)、4(×1)** | **✓** |
| +0x0D4 | 4 | `SampleType` | 0=984、6/1/7/2/3 各 5 | ✓ |
| **+0x0E8** | **1** | **`StampRaceAffiliation`** | 位掩码：15(全)=341、2(Cyborg)=302、1(Bugs)=200、4(Illuminate)=138、11=26、7=5 | **✓** |
| +0x0E9 | 1 | `PlanetAffiliationTemplateType` | 1=953、10=35、9=14…（10 个值） | ✓ |
| +0x0F0 | 16 | `LevelGenerationRegionType` DLArray | 1019/1019 空 | ✓ |
| +0x134/0x138 | 4+4 | `SubRegionType` ×2 | 0 为主，少量 7/8/9/19/24 | ✓ |
| +0x13C | 1 | `LocationHazardType` | 待解 | ⚠ |
| **+0x15F** | **1** | **`GuardForceType`** | **25 个不同值**（0:317、25:120、5:84、34:76、24:39…）；filediver 无该枚举定义 | **⚠** |
| +0x170 | 16 | `ZoneWeight` DLArray | | ⚠ |
| +0x190/0x198 | 1+16 | `LocationFlag` | | ⚠ |

### 3.8 对照：`galactic_presence_settings`（1,000 B × 137）

| offset | size | 观察 | 三态 |
|---:|---|---|---|
| +0x000 | 8 | **137/137 = 1000**（常量） | ✓ |
| +0x008 | 8 | 1001..1084（14 个唯一）——presence 序号/ID 段 | ✓ |
| +0x01C | 4 | `RaceType`：SuperEarth 67 / Illuminate 22 / None 19 / Cyborg 15 / Bugs 14 | ✓ |
| +0x020 | 8 | 哈希 A：105 个唯一 | ✓ |
| +0x028 | 8 | 哈希 B：32 个唯一 | ✓ |
| +0x280 | 16 | `SubRegionSettingsOverride`（`+0x14 StampRaceAffiliation`） | ✓ |
| tail | — | 模板路径 `content/galactic_presence_settings/templates/enemy_tag` + 标签字符串（`bots_cyborgs`/`bug_facility_strain_rich`…） | ✓ |

> **presence 的 effect id（1243/1245…）不在 presence 行里**：全表搜 u32/u16 == 1243/1245 → 0 处；
> +0x8 的值域只有 1001..1084。effect id → presence 的映射在服务端/WarSeason 侧，不在这些表里。

---

## 4. zone_data 关键分布（回答 Q1/Q2）

### 4.1 `ZoneTags`（Q1）

* 88/88 行都能解出数组；每个 zone 的 tag 数：**1 个 12 行 / 2 个 58 行 / 3 个 18 行**。
* **distinct = 18，值域 0..17**，正好等于 `enum.ZoneTag`（`None` + 16 个 `Value_N_Len_M` + `Count`）。
* 取值分布：`1`×56、`3`×16、`10`×15、`14`×12、`6`×12、`7`×10、`8`×10、`12`×9、`4`×8、`15`×8、
  `9`×6、`0`×5、`16`×5、`13`×4、`2`×3、`5`/`11`/`17` 各 1。
* **✗ 不是敌人类型名**：枚举 16 个值的 Go 名字被剥成 `Value_N_Len_M`（长度 11..34），
  既不是 bug/bot 语义，也没有任何值域外的"敌人标签"。它们是**地形/内容标签**。

### 4.2 `PatrolSetting`（Q2）

| 值 | 行数 | zone 组号 |
|---:|---:|---|
| 0 | 65 | 0-6, 29-35, 37-87 |
| 1 | 3 | 26, 27, 28 |
| 2 | 19 | **7..25（连续块）** |
| 3 | 1 | 36 |

### 4.3 `PatrolFloat1..11`（Q2）

| 字段 | min | max | distinct | 常见值 |
|---|---:|---:|---:|---|
| PatrolFloat1 | 1 | 2 | 2 | 1×69, 2×19 |
| PatrolFloat2 | 0 | 20 | 3 | 0×69, 20×11, 10×8 |
| PatrolFloat3 | 1 | 2 | 2 | 1×69, 2×19 |
| PatrolFloat4 | 0 | 20 | 3 | 0×69, 20×11, 10×8 |
| PatrolFloat5 | 0 | 10 | 2 | 0×69, 10×19 |
| PatrolFloat6 | 40 | 66 | 3 | 40×66, 66×19, 64×3 |
| PatrolFloat7 | 2 | 2 | **1** | 2×88 |
| PatrolFloat8 | 0 | 32 | 2 | 0×85, 32×3 |
| PatrolFloat9 | 0 | 12 | 3 | 2×64, 12×19, 0×5 |
| PatrolFloat10 | 0 | 12 | 3 | 同上 |
| PatrolFloat11 | 30 | 30 | **1** | 30×88 |

**88 行只有 6 种 float 组合，且与 `PatrolSetting` 强绑定**：

```
P=0: (1,0,1,0,0,40,2,0,0/2,0/2,30)        ← 65 行，只有 float9/10 两种小差异
P=1: (1,0,1,0,0,64,2,32,2,2,30)           ← 3 行
P=2: (2,20,2,20,10,66,2,0,12,12,30)       ← 19 行，float2/4 有 20 与 10 两种
P=3: (1,0,1,0,0,40,2,0,2,2,30)            ← 1 行
```

**与 biome/zone 的相关性：**

* `PatrolSetting=2` 的 19 行全部是 `MinimapTerrainType=0 (Open)`，且是**连续的 zone 组 7..25** —— 像一个
  独立的 zone 家族（开放地形/据点群）；P=1 也在 Open（3 行）；P=3 是唯一 terrain=5 (Bug) 的 zone；
  其余 65 行 P=0 分布在全部 6 种 terrain。
* ZoneTags 与 PatrolSetting 无一一对应（同一 tag 可跨多个预设）。
* 结论：**`PatrolSetting` 是 4 值预设枚举，`PatrolFloat1..11` 是预设的参数化展开**（不是每 zone 独立的
  刷怪表）。改 float 等价于微调预设参数；⚠ 每个 float 的语义（数量/半径/延迟…）**未证**。

---

## 5. planet → region → zone 链与覆盖率（回答 Q3）

```
planet_data (438 行星)
  RegionLowland  +0x60 / RegionHighland +0x88   (LevelGenerationRegion, 40 B)
    +0x00 Name  (DLString)      例 'region_moor_baseplanet'
    +0x68 Id    (ThinHash)
    +0x6C Type  (LevelGenerationRegionType, 0..34)
        ↓  Name 876/876、Id 876/876、Type 876/876（三者互相一致）
region_settings 段1  34 × GenerationRegionVariantList   ← 名字/Id 来自这里
        ↓  +0x20 DLArray → 146 × GenerationRegionVariantSettings
           +0x0C LevelGenerationRegionVariantType v  (0..74，实测用 46 个值)
        ↓  ⚠ 行号 = v − 1（74 行 = 枚举 74 个可用值）
region_settings 段0  74 × GenerationRegionSettings
        ↓  +0x238 SubRegionSettings[16].Zone (ZoneId) + InvalidZoneProximity[8]
zone_data  块序号 = ZoneId (0..87)
```

**覆盖率（`out/planet/levelgen.json` → `planet_join`）：**

| 指标 | 数值 |
|---|---|
| 行星数 / region 槽位 | 438 / 876 |
| Region 槽位命中 region 变体列表（Name / Id / Type） | **876 / 876 / 876 = 100%** |
| 能落到 ≥1 个 zone 的行星 | **438 / 438 = 100%** |
| 每行星 zone 引用数合计 | 7,340（平均 8.4 个 zone/行星） |
| 被引用的 zone 数 | **67 / 88**（21 个 zone 没被任何 region 引用） |
| 每个 region 行的 zone 数 | 3..14（众数 9） |
| 最常被引用的 zone | 29、37（各 72 行 region）、6（71）、4/5（70） |
| 行星实际用到的 region type | 32 / 34（未用 `region_sandy_cyborg_factory`、`region_swamp_variant_02`） |

**⚠ 唯一的推断跳**：变体 settings 里指向 `GenerationRegionSettings` 的 8 字节字段（+0x30）在
**146/146 条里都是 -1**（filediver 亦注 "Seems to be unused"）。因此"变体类型 v → 段0 第 v-1 行"
是按 **74 行 = 枚举 74 个值** + 值域 5..74 推出来的，没有显式引用可证。若引擎另有排序规则，
zone 集合会整体错位（但 `zone_data` 本身的字段/分布结论不受影响）。

---

## 6. presence 交叉引用检索（核心判定；回答 Q3/Q4 的关键）

**方法（`out/planet/_probe_xref.py`，54 张 `generated_*.dl_bin` 全扫）：**

1. 收集 137 行 presence 的 **+0x20 / +0x28 两个 u64**（唯一值 105 / 32）；
2. 对每张表的**全部 payload** 以 **4 字节步进读 8 字节窗口**比对（哈希是 8 字节对齐，4 字节步进已覆盖）；
3. 另用 144 个 presence 尾部标签字符串的 **murmur64 哈希**与**原始 ASCII** 再扫一遍；
4. 还扫了 presence 的 +0x8 ID（1001..1084）与 race 值。

**结果：**

| 表 | +0x20 命中 | +0x28 命中 | tag_hash | tag_string |
|---|---:|---:|---:|---:|
| **8 张目标表（zone/region/planet_*/scenario/solar/modifier/color）** | **0** | **0** | **0** | **0** |
| `galactic_presence_settings`（自表，重复值） | 26 | 46 | 0 | 250 |
| `generated_entities.dl_bin` | 0 | **3** | 0 | 0 |
| 其余 43 张表 | 0 | 0 | 0 | 0 |

**实体库那 3 处**：全部是 `ShowOnMapComponentData`（block 111）的 **+0x8** 字段，行 14/19/25，
值 = presence 行 **97** 的 +0x28（race=4 Illuminate，tag=`illuminate_rift_sideboard_gate`）——
即 presence 在本 build 里**只被"星图标记实体"引用**。

**为什么这个检索是充分的：**

* 关卡生成侧若要引用某条 presence，唯一的稳定 id 就是那两个 8 字节哈希（行内 +0x20/+0x28）；
  我们扫的是**全部表的全部字节**，不是抽样；
* 8 字节哈希误命中概率 ≈ 表窗口数 / 2^64（54 张表合计 ~10^7 窗口 → ~1e-12），可忽略；
  实际只命中"同一字段的 3 次重复"，说明命中是真的、而且只此一处；
* 另外从**名字侧**也扫了：134 个 presence 标签字符串（`bugs_burrower`、`bots_increased_devastators`…）
  的 murmur64 与 ASCII 在 54 张表里 0 命中 —— presence 的"敌人标签"没有任何本地表引用。
* 反向看：presence 的 effect id（1243/1245）在 presence 表里也不存在（0 处），说明 id→presence
  的映射不在本地数据里（服务端 WarSeason 侧）。

**唯一在关卡生成侧出现 "presence" 的地方是天气：** `weather_settings` 里 6 条
`content/level_generation_settings/galactic_presence_overrides/weather_settings/*`
（`gloom`、`hiveworld_clear`、`illuminate_ritual_storm`…）。**敌人侧没有对应 override 路径**。

---

## 7. `scenario_settings` / `region_settings` 的 enemy/spawn/faction 字段（Q4）

* `scenario_settings`：类型树（递归 depth 6）**没有** enemy/spawn/faction/team 字段；行只有 3 个哈希/ID
  + 1 个 u32 + `ScenarioSetting` 数组。**✗ 无敌人组成**。
* `region_settings`：**唯一的阵营语义是 `SubRegionSettingsOverride.RaceAffiliation`（+0xAB4+0x14，
  1 字节位掩码 Bugs=1/Cyborg=2/Illuminate=4/SuperEarth=8）**；观察值 0×1028、1×76、2×76、4×4
  （多数为空 = 不限阵营）；`OperationType`（+0x18）14×1172、9×12。**没有敌人组成/刷怪选择器**。
* 补充（不在 8 张表里，但同属 levelgen）：`location_groups`/`satellite_groups` 的
  `EnemyTag/GuardForceType/StampRaceAffiliation` 是**整个数据目录里仅有的敌人选择字段**（§3.7）。

---

## 8. 本地可改点排序（回答要求 ②）

| # | 表 | 字段（offset） | 现值 | 预期局内效果 | 置信度 |
|---:|---|---|---|---|---|
| 1 | `zone_data` | **PatrolSetting (+0x16C)** | 0:65 / 2:19 / 1:3 / 3:1 | 切到 `2` = 巡逻预设 2：float 组 (2,20,2,20,10,66,2,0,12,12,30)，即数量×2、间隔/半径类 0→10/20、40→66 —— 最可能改变**巡逻密度/规模**；这是唯一的本地"刷怪强度"旋钮 | ✓ 字段/预设实证，⚠ 局内语义未证 |
| 2 | `zone_data` | `PatrolFloat1..11 (+0x170..+0x198)` | 见 §4.3 | 直接微调预设参数（哪些 float 管数量/半径/延迟未知）；可单变量试 | ⚠ |
| 3 | `location_groups` / `satellite_groups` | `LocationStampInfo.EnemyTag (+0xD0)` | 1014/1019 = 0 | 给具体 location stamp 指定敌人组成 tag（枚举 BugAcid/BugArmored/BugPredators/…/BotAssault/…）；**本 build 几乎全 0** ⇒ 编辑器可能不读它，或 0=按地图默认 | ✓ 字段/分布实证，⚠ 运行时行为未证 |
| 4 | 同上 | `GuardForceType (+0x15F)` | 25 个值（0:317、25:120、5:84…） | "守卫力量类型"选择器（filediver 无枚举名）—— 可能按难度/阵营选守卫编成 | ⚠ |
| 5 | `region_settings` | `SubRegionSettingsOverride.RaceAffiliation (+0xAB4+0x14)` | 0×1028、1×76、2×76、4×4 | 改阵营归属位掩码 → 该子区域只允许指定阵营的内容（门控，不产生变种） | ⚠ |
| 6 | `planet_region_settings` | `RegionRaceType (+0x18)` | 1(SE)=344 / 3(Cyborg)=25 | 城市模板的阵营（人类城 vs 生化人城）→ 影响城市区敌人种类 | ⚠ |

> **都不等价于 variant_mod**：variant_mod 的效果来自 presence（服务端激活），本地没有任何表引用
> presence 的哈希/标签；上面 6 个点最多改变"数量/阵营/守卫类型"，**不会引入掠食/孢裂这类变种**。

---

## 9. 两个坑（回答要求 ④）

**坑 1：`tools/planet_tables.py` 只解第一段 `[count][groups]`；"行数 = Σ size//stride" 对
1 行/组的表是错的。**

* `zone_data`：88 组，每组 1 行（912 B）+ 组内数组尾；工具按 `Σ size//912` 报 **517 行** —— 假象。
  真实 **88 行**，正好是 `enum.ZoneId` 的 88 个值。
* `region_settings`：文件有**两段**：段 0 = 74 个 `GenerationRegionSettings`，段 1 = 13 个
  `GenerationRegionGroup`（带 region 名字，15,719 B 被工具当成"leftover"）。工具会打印
  `! 15719 B after the last group` —— 那正是段 1。**不读段 1 就拿不到 region 名字/变体列表。**
* 同理 `planet_region_settings` 尾部 2,952 B、`planet_data` 尾部 3,504 B、`presence` 尾部 1,096 B
  都是真实数据的尾部（字符串/键表），不是垃圾。

**坑 2：字段偏移必须以 typelib 为准；filediver 的 Go 结构不是本 build 的布局。**

* filediver `rawGenerationRegionSettings` 的 Go 结构算出 5,200 B，本 build 的 typelib 是
  **3,272 B**；`SubRegionSettings` 在 **+0x238**、`SubRegionSettingsOverride` 在 **+0xAB4**
  （Go 里是 [560]uint8 之后的字段，位置不同）。
* `DLArray` 是 `{int64 offset, uint64 count}`（16 B），数组**存在组尾**（offset ≥ stride），
  不能按"行"读；`DLString` 是 8 B（offset+len），`stingray.Hash` 8 B、`ThinHash` 4 B。
* 枚举（ZoneTag/PatrolSetting/RaceType…）不在 typelib 的类型索引里（只类型，不含枚举名），
  值域要靠 `datalibrary/enum/*.go` 对；`GuardForceType/StampRaceAffiliation` 在 filediver 里
  **没有**枚举文件（404），只能用位掩码/值分布描述。

---

## 10. 三态小结

**✓ 离线（布局/数据证明）**

* `zone_data` 88 行（=ZoneId）、912 B、1 行/组；`ZoneTags` 88/88 可解、18 值 = 枚举；
  `PatrolSetting` 4 值、`PatrolFloat1..11` 88 行仅 6 种组合且按预设分组。
* `region_settings` 两段：74 行生成设置（`SubRegionSettings[16].Zone` 引用 **67/88** 个 zone，每行 3..14 个）；
  13 组 / 34 个变体列表 / 146 条变体 settings（名字 + ThinHash + 变体类型枚举）。
* `planet_data` 438 行星 × 2 region 槽位：Name/Id/Type 对 34 个变体列表 **876/876** 命中；
  **438/438 行星能落到 zone**；`zone_data` 未被引用的 21 个 zone。
* presence 的 +0x20/+0x28 在 54 张表里只有实体库 `ShowOnMapComponentData +0x8` 3 处命中（presence 97）；
  8 张目标表 0 命中；presence 标签字符串/哈希 0 命中。
* `location_groups/satellite_groups` 的 `EnemyTag/StampRaceAffiliation/GuardForceType` 分布（1,019 条 stamp）。

**✗ 否证**

* "8 张目标表里有敌人组成/presence 开关" —— 54 表全字节扫 0 命中；类型树递归无 EnemyTag/EnemyPackage。
* "ZoneTags 是敌人类型名" —— 18 个值 = ZoneTag 枚举（值名被剥成 Value_N_Len_M），无 bug/bot 语义。
* "PatrolFloat1..11 是每 zone 自由参数" —— 88 行只有 6 组，且由 PatrolSetting 决定。
* "变体 settings 用 GenerationRegionSettings 引用关联生成设置行" —— 146/146 = -1（本 build 未用）。
* "scenario_settings 有 enemy/spawn 字段" —— 类型树递归 6 层无匹配。

**⚠ 未定**

* 变体类型 v → 段 0 行号 v-1 是推断（无显式引用；若引擎另有排序则 zone 集合错位）。
* `PatrolFloat1..11` 每个 float 的具体语义（数量/半径/延迟/权重）。
* `GuardForceType` 的枚举定义（filediver 无文件）、`EnemyTag` 非零 5 例的运行时行为。
* 21 个 zone 未被任何 region 引用 —— 是未使用内容还是别的入口（如 override/特殊任务）未查。
* presence → 实体库 ShowOnMapComponent 的 3 个实体（0x3CE56937…、0x84F256FB…、0x84089F05…）在
  名字表里未解析；它们与"敌人变种"如何联动在实体库/运行时侧，超出本轮范围。
