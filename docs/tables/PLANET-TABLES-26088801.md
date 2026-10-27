# 星球侧数据表全景（build 26088801）

> 只读侦察。输入 `D:/mod/refs/dlbin/plaintext-26088801/generated_*.dl_bin`（已解密明文缓存）+ `dl_library.dl_typelib`。
> 未启动游戏、未改任何数据文件。条目三态：`✓ 离线` = 布局与语义都被本 build 数据独立证明；`⚠ 未证` = 布局已证语义未证；`✗ 否证` = 查过不成立。
> 起点是一个第三方案例 `D:\Downloads\variant_mod`（MITM 代理型 mod，见 §1）——它把"星球效果"这条线拽了出来。

---

## 0. 一句话结论

* **星球表本身很厚，但它们管的是"这颗星球长什么样、怎么生成"**（生态/色板/天气/地形/场景/修饰符），**不管"刷什么敌人"**。
* **敌人变种（掠食变种一类）不在任何本地表里**：`planet_data` 41 个成员逐个核对，**无 RaceType、无 faction、无 unit list、无 presence 字段**；presence 表里同阵营的 7 条 enemy_tag 行**逐字节几乎相同**（只差身份键）；`zone_data` 的 `ZoneTags` 是 18 个地形标签，**不是敌人名**。
* **最硬的一条否证**：presence 在关卡生成侧**只接了一个钩子——天气**。`weather_settings` 里有 6 条
  `content/level_generation_settings/galactic_presence_overrides/weather_settings/*`（gloom / hiveworld_clear /
  illuminate_ritual_storm …），**没有敌人侧 override**。官方给 presence 留的扩展点是天气，不是刷怪。
* 变种的开关在**服务器**给出的 `planetActiveEffects` 里，效果 id 再由引擎按 presence 身份键落到固化实现 —— 这就是那个案例必须走 MITM 的原因（§1、§4）。
* 可本地改的部分很实在：生态/色板/雾/天气/场景/修饰符/地形 stamp/**巡逻预设**（§5、§6、§7）。

---

## 1. 案例：`variant_mod` 到底做了什么

**类型判定：网络 MITM 代理，不是数据表 mod。** 它不碰 `data/` 下任何文件，只在本机把
`api.live.prod.thehelldiversgame.com` 解析到自己的 443 监听（hosts + 自签 CA + CRL），然后**只改写一个响应**。

| 项 | 实测内容 |
|---|---|
| 改写目标 | 仅 `GET /api/WarSeason/801/Status`（`war_proxy.py:82` `STATUS_MARK`）；其它请求/响应一字节不动 |
| 改写动作 | 向 `planetActiveEffects[]` **追加** `{index: 星球id, galacticEffectId: N}`（`rewrite_status()`，`war_proxy.py:469`） |
| 效果 id 来源 | 另抓 `GET /api/WarSeason/GalacticWarEffects`（约 300 条）：`effectType=40` → 星图**词条**（tag）；`effectType=71` 且 `values[0]` 命中本地 presence 哈希 → **玩法**（局内变种） |
| 生效条件 | tag + 玩法**成对**注入才出局内变种（`variant_catalog.json` 的注释与 `meta` 结构） |
| 阵营过滤 | 读 `planetStatus.owner` 后逐星球筛，避免把虫族词条写到机器人星球（v1.26 修复） |
| 客机 | 房主装、客机零安装即可见变种；证据是主机日志里**没有客机的任何 REQ**，而客机星图也出现词条 ⇒ 引擎把房主的战况板整张同步给客机 |

> 仓库边界：本节只做**机制结论**。网络层（代理补丁、抓包、effect 菜单、可达性/阵营注入实验）
> 已独立成仓库 **[hd2-network-proxy](https://github.com/deepseekv41flash/hd2-network-proxy)**；
> 本仓库只保留离线数据表这条线的笔记与工具。

**它对我们的价值**：把"变种"拆成了可观测的三段 ——
`galacticEffectId`（服务器）→ `presence` 身份键（本地表里有）→ 引擎固化实现（本地表里没有）。
前两段我们已经能在本地对上（§3.4 的 16/16 对表），第三段决定了它必须走代理。

---

## 2. 星球侧表全景

`python tools/planet_tables.py survey`（本 build，容器按类型分开列；`rows_est` 是 `Σ size//stride`，
**`1/grp+tail` 形态的表真实行数 = 组数**，见 §8 坑 1）：

| 表 | 组 | stride | 真实行 | 形态 | 行类型 | 管什么 |
|---|---:|---:|---:|---|---|---|
| `planet_data` | 438 | 624 | **438** | 1/grp+tail | `LevelGenerationPlanetData` | **一行一颗行星**：生态、四段 locid、色板×2、region×2、场景、修饰符、采样、环境实体、包 |
| `planet_region_settings` | 369 | 128 | **369** | 1/grp+tail | `PlanetRegionSettings` | 行星**分区/城市模板**：RaceType(1 SE 344 / 3 Cyborg 25)、OperationTag、远方战潮效果池、天气、16 B 覆盖块 |
| `region_settings` | 74 + 13 | 3272 / — | 74 + 13 组 | 两段容器 | `GenerationRegionSettings` / `GenerationRegionGroup` | 段 0 = 74 条生成区域设置；**段 1 = region 变体列表（34 列表 / 146 条 settings）**，`planet_data` 的 region 指向这里 |
| `zone_data` | 88 | 912 | **88**（不是 517） | 1/grp+tail | `ZoneSettings` | **生态区**：ZoneTags(18 值)、stamp 群、shader/材质/高度生成器、水面、音乐、**PatrolSetting + PatrolFloat1..11** |
| `planet_types_settings` | 1 | 24 | 88 | 容器 `(16,88)` | `SolarSystemObjectType` | 太阳系天体类型（行星/卫星/小行星…）|
| `planet_override_settings` | 13 | 40 | 44 | 容器 | `PlanetOverrides` | 按星球的**资源覆盖**（name/id/package + replace 三元组）|
| `planet_color_set_settings` | 1 | 64 | 30 | 容器 `(16,30)` | `PlanetColorSet` | 雾色色板（main/secondary/bugs/bots/illuminate 五组 Vec3）|
| `galactic_presence_settings` | 137 | 1000 | **137** | 1/grp+tail | `0xF8F9EC3E` | **星球效果载荷**（presence）：RaceType、修饰符数组、视觉/环境覆盖、事件引用 |
| `scenario_settings` | 39 | 48 | 149 | 2..8 行/组 | `ScenarioSettings` | 任务场景（`planet_data` 的 ScenarioSettings 指向此表）|
| `solar_system_settings` | 1 | 24 | 3822 | 多行/组 | `SolarSystemSettings` | 全局太阳系配置（`planet_data` 只引用其中 1 条）|
| `weather_settings` | 184 | 648 | 190 | 1/grp+tail | `WeatherSettings` | 天气；**含 6 条 presence 天气覆盖**（§6.4）|
| `environment_settings` | 17 | 576 | 17 | 1/grp+tail | `EnvironmentSettings` | 环境（着色/大气）|
| `sky_settings` | 40 | 24 | 480 | 多行/组 | `SkySettings` | 天空盒/时段 |
| `location_groups` | 13 | 56 | **1019 条 `LocationStampInfo`** | 三层嵌套 | `LevelGenerationLocation` | **地点组 → stamp 信息**；`EnemyTag/GuardForceType/StampRaceAffiliation` 全库仅有的敌人字段（§6.3）|
| `satellite_groups` | 36 | 24 | 36 组 | 三层嵌套 | `LevelGenerationSatelliteGroup` | 卫星/前哨点 |
| `planet_territory_graphs` | 11 | 56 | 28105 | 多行/组 | `SavedPlanetTerritoryGraph` | 领土图（`planet_data.PlanetLayoutId` 指这里）|
| `modifier_settings` | 15 | 24 | 52 | 1..8 行/组 | `Modifier` | 修饰符定义行（行内是 `ModifierGroup` 容器）|
| `route_settings` | 3 | 112 | 3 | — | `RouteSettings` | 空投/航线（3 条）|
| `distant_war_effect_settings` | 7 | 48 | 26 | — | `DistantWarEffectPool` | 轨道上看别的星球的"远方战况"特效池 |
| `resource_swap` | — | — | — | 无 LDLD 组 | — | 24 B 小表，另一种形态（⚠ 未解）|

---

## 3. `galactic_presence_settings`：137 条"星球效果载荷"

### 3.1 容器

`u32 137` + 137 × `[LDLD 头 24 B][1000 B 行][尾部 3~220 B]`。行内指针/数组偏移**相对于组 payload 起点**；
空数组编码为 `offset=某值, count=0`（**这一点很坑**：只看 offset 会把它误读成"引用了别的 presence"，见 §3.5）。

### 3.2 行结构（116 个成员，只列可用的）

| 偏移 | 宽 | 含义 | 证据 |
|---|---:|---|---|
| `+0x00` | 8 | 全表常量 `1000`（基对象 id）| 137/137 |
| `+0x08` | 8 | **父模板 id**：`1001`=无模板（42 行），其余 14 组 `1041/1046/1051/1055/1058/1061/1063/1064/1067/1068/1072/1074/1084` | 137/137；按 AddPath 分组 1:1（三张空模板共用一个 id，说明 id 是**去重后的设置对象**）|
| `+0x14` | 4 | **种类**：`0` 地图标记(19) / `1` 事件作战(7) / `3` 战术行动(4) / `4` 敌情或设施(107) | ✓✓ 实机标定，见 §3.2b |
| `+0x18` | 1 | bool，仅 20 行 =1，**全部是 strain/surge 类敌情变体** | ✓ 与 `+0x14=4` 交叉验证 |
| `+0x1C` | 4 | **RaceType**：0 none / 1 superearth / 2 terminid / 3 automaton / 4 illuminate | ✓ 与案例目录的 faction 逐条吻合（§3.4）|
| `+0x20` | 4 | **显示名 locid**（`.strings` 的 32 位 id）：`bugs_gloom`→1147205144=`SPORE BURST STRAIN`；`illuminate_ritual_storm_lvl1`→505181551=`CLASS 1 EXOSTORM` | ✓✓ 两处实机文本对照 |
| `+0x24` | 4 | **描述 locid**：`bugs_gloom`→1134814559=`A mutation causes Terminids on this planet…` | ✓✓ 星图卡描述逐字命中 |
| `+0x28` | 8 | **类别键**（32 个不同值）| 同类别行共享，例：`bots_increased_*` 四条共用 `0x92EA56303ABF23E5` |
| `+0x48` | 4 | f32（137 行非零，0.33..1.0）| ⚠ 权重类 |
| `+0x4C` | 4 | f32 恒 1.0 | ✓ |
| `+0x1F8` | 16 | **GameplayModifiers 数组**（hash64）| ✓ `gloom` = 5 项，与原版星球修饰符同一批哈希（§3.3）|

其余成员是视觉/环境覆盖（色板、天气、资源覆盖、子区域覆盖、材质变量、矢量）——`black_hole` 一类行把它们填满，而 `enemy_tag` 一类行几乎全空。

### 3.2b `+0x14` 种类字段的实机标定（✓✓，2026-10-27）

原本只知道是 0..4 的枚举，语义未证。用「往 Status 里塞一个 effect，看客户端渲染哪块 UI」把它标定出来了：

| `+0x14` | 含义 | 条数 | 注入后的实机表现 | 验证 |
|---|---|---:|---|---|
| `0` | 地图标记 | 19 | 星图图标（rift / void cluster / at-war） | ⚠ 未逐条实测 |
| `1` | **事件作战** | 7 | 部署界面出现**作战卡**（名称+描述+影响） | ✓✓ `1373` on 182/93 → `AVERT VOID` |
| `3` | 战术行动 | 4 | 待测 | ⚠ |
| `4` | 敌情 / 设施 | 107 | 星图卡效果 + 作战界面 `COMBATANT FORCES PRESENT` | ✓✓ `1386` on 93（**跨阵营**）→ `SPORE BURST STRAIN` |

关键点：

* **`+0x14=4` 不会换作战卡**，只作为「这片战场上有什么敌人」列出来。实验里把终结族 `bugs_gloom`
  挂到 illuminate 星球，卡片仍是 `DISRUPT ILLUMINATE`，但敌情行多了一条 —— 说明这两类走的是不同 UI 通道。
* **客户端不校验阵营**：`bugs_gloom`（RaceType=2）挂在 owner=4 的星球上照常渲染。
  `variant_mod` 里那道 `resolve_plan()` 阵营过滤是 mod 作者自己加的保险，不是引擎行为。
* `+0x20`/`+0x24` 是 locid 这件事，也解释了 §3.4 里"103 组互异"——每条 presence 的名字与描述都不同。

> ⚠ 命名陷阱：`bugs_gloom`（`+0x14=4`，`SPORE BURST STRAIN`）与 `gloom`（`+0x14=1`，
> `GLOOM RESEARCH EXPEDITION`）是两行不同数据，且 `gloom` 与 `gloom_hiveworld` 共用同一个显示名。
> 按名字猜语义会连错两次，必须按 `murmur32` 哈希 + `+0x14` 区分。


### 3.3 关键否定：enemy_tag 行不带敌人组成

同阵营 7 条 terminid enemy_tag 行逐字节比较，差异只有 40~60 B：

```
bugs_acid vs bugs_burrower：diff 出现在 +0x20..+0x2F（身份/类别键）、+0x90..+0x97（h28 的自拷贝）、
                            +0xF0/+0x118/+0x1B8/+0x340..（数组头偏移，因尾部长度不同而移位）
```

**没有任何"单位列表 / 数量 / 权重 / 阵营细分"字段**；`+0x1F8`（修饰符数组）对这 7 行全部为空。
⇒ presence 行对敌人变种而言只是**标签**，"标签→刷什么"在引擎侧固化。

### 3.4 与案例目录的机械对表（16/16）

`out/planet/presence-variants.json`（`out/join_variants.py` 生成）把 `variant_catalog.json` 的 16 个变种
逐条落到本地行上，**16/16 全部命中**（目录写在 build 25988413，本表是 26088801，跨 build 稳定）：

| 变种 | effect ids（tag, mechanic）| presence 行 | RaceType |
|---|---|---|---|
| 掠食变种 | 1243, 1245 | `bugs_super_predator` | 2 terminid |
| 孢裂变种 | 1244, 1386 | `bugs_gloom` | 2 |
| 爆裂变种 | 1303, 1310 | `bugs_burrower` | 2 |
| 蟑龙 | 1306, 1309 | `bugs_dragon` | 2 |
| 霸王虫 | 1307, 1308 | `bugs_hive_lord` | 2 |
| 生化人 | 1360, 1361 | `bots_cyborgs` | 3 automaton |
| 灼热部队 | 1248, 1249 | `bots_ivory_legion` | 3 |
| 喷气部队 | 1202, 1203 | `elite_bot_jumpattack` | 3 |
| 入侵舰队 | 1413, 1414 | `illuminate_invading` | 4 illuminate |
| 无票者大军 | 1377, 1378 | `illuminate_harvester` | 4 |
| 入侵者 | 1380, 1379 | `illuminate_engineer` | 4 |
| 窃票者 | 1402, 1403 | `illuminate_bodyhorror` | 4 |
| 重兵部署 | 1401, 1400 | `seaf` | 1 superearth |
| 重甲激增 | 1355 | `bots_increased_warstriders` | 3 |
| 巨型者激增 | 1357 | `bots_increased_hulks` | 3 |
| 蹂躏者激增 | 1359 | `bots_increased_devastators` | 3 |

**另有 27 条敌人味 presence 不在目录里**（原版自用）：`bugs_acid`、`bugs_defiler`、
`bots_increased_tanks`、`bots_orbital_superweapon`、`illuminate_fleet`、6 条 `illuminate_facility_*` 等。

### 3.6 服务器侧的键 = `murmur32(presence 名)`（✓ 实测，2026-10-27 抓包）

从官方 API 抓到的 `GalacticWarEffects`（310 条）里，`effectType=71` 的 `values[0]` 就是
**`murmur32(presence 名)`** —— 即 Stingray 的 32 位名字哈希（`murmur64(seed=0) >> 32`）：

| presence | `murmur32` | GWE 里对应 effect 的 `values[0]` |
|---|---|---|
| `bugs_super_predator` | `0xE9DB526C` | 3923464812 = 0xE9DB526C ✓ |
| `bugs_gloom` | `0x60280611` | 1613235729 ✓ |
| `bots_cyborgs` | `0xA087D5A7` | 2693256615 ✓ |
| `seaf` | `0x492F408A` | 1227833482 ✓ |
| `illuminate_invading` | `0x37640CC3` | 929303747 ✓ |

**所以 §3.2 里 `+0x20/+0x24` 那对不是服务器键**（它们是显示名 / 描述 locid，见 §3.2b），拿它去对 API 值会全对不上。按此口径，本地 137 条 presence 里有 **67 条不同的 presence** 能在 GWE 菜单里找到对应项 —— 75 条 `type71` effect 中，67 条 distinct、3 条重复引用、5 条指向本地不存在的 presence。核对命令：
`python -m srkit hash <presence 名>` → 取 `murmur32=`。

### 3.5 全局检索：presence 在本地只被两处引用，且都不是刷怪

把 105 个身份键 + 32 个类别键打包成 8 字节，扫本 build **全部 53 张明文表**（`tools/probes/planet/presence_scan_all.py`，3.3 s；
关卡侧另有 `out/planet/_probe_xref.py` 用 4 字节步进复扫一遍）：

| 命中 | 位置 | 判定 |
|---|---|---|
| 3 处 | `planet_region_settings` 的 `+0x08..+0x10`（行 99/132/138）= `completed_aspiration` / `completed_yearning` / `completed_hope` 的身份键 | ⚠ **不能算引用**：该字段正常值是 32 位 thin hash（351 行高位为 0），这 3 行高位恰好是 presence 键的高 32 位；最省事的解释是**同名同哈希**。见 §7 实验 E1 |
| 3 处 | `generated_entities.dl_bin` 的 `ShowOnMapComponentData +0x08`，全部指向 **presence 行 97**（`illuminate_rift_sideboard_gate`）的 `+0x28` | ✓ **真引用**，但语义是"星图标记显示哪个 presence"，与刷怪无关 |
| 6 条字符串 | `weather_settings` 的 `content/level_generation_settings/galactic_presence_overrides/weather_settings/*`（gloom / hiveworld_clear / illuminate_ritual_storm…）| ✓ **presence 在关卡生成侧唯一的钩子 = 天气**（§6.4）|

⇒ **"这个星球当前有哪些 presence" 只存在于服务器数据/内存战况板里，本地表没有这个字段；
presence 也没有敌人侧 override。** 这是"变种不能靠改本地表实现"的直接证据。

---

## 4. 判定：变种能不能本地做

| 问题 | 答案 | 证据 |
|---|---|---|
| `planet_data` 能选敌人组成吗 | ✗ 否 | 41 成员无 RaceType/faction/unit list/presence（§5）|
| presence 行能改组成吗 | ✗ 否 | 同阵营行只差键（§3.3）|
| 有本地表记录"星球→presence"吗 | ✗ 否 | 105+32 个键全表扫描，命中只有三处来源：`planet_region_settings` 3 行（同名同哈希）、实体库星图标记 3 处、`weather_settings` 6 条天气覆盖——**都不是刷怪**（§3.5）|
| 能本地伪造"效果已激活"吗 | 需要改内存战况板，或改 API 响应 —— 即那个案例的做法 | 案例 `FINDING`：客机可见是因为引擎同步**房主的板**，不是本地表差异 |

**结论**：想要"变种"这一层，只有两条路：
1. **服务器侧**（MITM 代理 / 官方活动）—— 案例已证明可行；
2. **引擎侧**（Lua/内存改战况板或改 presence→组成的分发）—— 属于代码路线，不是数据表路线。

数据表路线能给我们的是**第 5、6 节的"星球本身"改造**，那部分完全离线可做。

---

## 5. `planet_data`：一行一颗行星

详见 [PLANET-DATA-FIELDS-26088801](PLANET-DATA-FIELDS-26088801.md)（41 成员逐行表，含每条的可复现计数）。核心事实：

* `+0x058 DebugName` = `planet_{index:03d}`（387/438；其余 32 行是模板行，行 390–421 的 `Inherits` 也是 NULL）；`+0x000 Inherits` = 生态 setup 路径，**36 个 setup 与 `PlanetType` 36/36 一一对应**。
* `+0x1B8 PlanetType` 12 个值：`sandy=3(101)`、`moor=9(94)`、`primordial=8(88)`、`arctic=2(48)`、`swamp=6(32)`、`deciduous=14(25)`、`oasis=13(15)`、`magma=12(12)`、`coniferous=15(10)`、`bug_hiveworld=11(8)`、`rift=16(3)`、`superearth=10(2)`。
* `+0x060/+0x088 RegionLowland/Highland`：876/876 命中 `region_settings` 第二容器记录的 **`+0x08` 4 字节 region id**；`Region.Type` == 该记录在表里的 1-based 序号（438 行两侧全部成立）。
* `+0x190 ScenarioSettings` 33/33 命中 `generated_scenario_settings`；`+0x1F8 SolarSystemSettings` 438/438 同值且 == `solar_system_settings` 首 8 字节。
* `+0x1A8 GameplayModifiers`：**216/438 行各 1 项，只有 8 个不同哈希**；8/8 是 `generated_entities` 的 entity key，其中 **6 个也出现在 presence 行 `+0x1F8` 的数组里**（`gloom` 5 项、`illuminate_rift` 7 项）⇒ 修饰符是"实体 + 数组"两处表达同一件事。
* `+0x210 SampleTypes`：437 行 `[9,9]`（Uranium），唯一例外 `planet_tutorial` `[7,6]`。

---

## 6. 关卡生成链（zone / region / location）

逐字段证据见 [LEVELGEN-FIELDS-26088801](LEVELGEN-FIELDS-26088801.md)（451 行）与 `out/planet/levelgen.json`；本节只留结论。

### 6.1 链条能闭合到 zone（`✓ 离线`）

```
planet_data(438 行星)
  └ Region.Lowland/Highland ── Name / Id(thin hash) / Type(enum LevelGenerationRegionType 0..34)
        └ region_settings 段1 的 34 条 region 变体列表        （Name 876/876 · Id 876/876 · Type 876/876）
              └ Variant settings 的 +0x0C LevelGenerationRegionVariantType = v
                    └ region_settings 段0 第 v−1 行（74 行 = 74 个枚举值；显式引用 +0x30 在 146/146 条都是 −1）
                          └ SubRegionSettings[16].Zone (ZoneId)
                                └ zone_data 的块序号（0..87 = enum.ZoneId）
```

覆盖率：**438/438 行星都能落到 zone；876/876 个 region 槽三键全命中；67/88 个 zone 被引用**（21 个未用），
平均 8.4 个 zone/行星。⚠ `行 = 枚举值 − 1` 是推断（显式引用全部为 −1），这是本节唯一的软点。

### 6.2 `zone_data`（88 行 × 912 B，一行 = 一个 ZoneId）

| 字段 | 偏移 | 取值 | 用途 |
|---|---:|---|---|
| `ZoneTags` | +0x00 | 88/88 可解，1~3 个/zone，18 个不同的 `ZoneTag` 枚举值（0..17）| **地形/玩法标签，不是敌人名** |
| `PatrolSetting` | **+0x16C** | 0 → 65 / 2 → 19 / 1 → 3 / 3 → 1 | **4 值巡逻预设枚举**，唯一的本地"刷怪强度"旋钮 |
| `PatrolFloat1..11` | +0x170..+0x198 | 88 行只有 **6 种 float 组合**，与 `PatrolSetting` 强绑定（预设的参数化展开）| 预设 2 = `(2,20,2,20,10,66,2,0,12,12,30)` |
| `MinimapTerrainType` / `ZoneMusicType` / `BanterEventType` | — | — | 表现层 |

`PatrolSetting=2` 的 19 行全部 `MinimapTerrainType=0 (Open)` 且是连续的 zone 组 7..25 —— 像一条"开阔地"
专用预设，对"把某个 zone 换成高强度巡逻"是最干净的实验面。

### 6.3 全库唯一的敌人字段：`LocationStampInfo`（`location_groups` / `satellite_groups`）

三层嵌套 `LevelGenerationLocation(56 B)` → `DLArray<LocationGroup>` → `DLArray<LocationStampInfo>`，
共 **1019 条 stamp 实例**，里面有：

| 字段 | 偏移 | 本 build 分布 | 判定 |
|---|---:|---|---|
| `EnemyTag` | **+0xD0** | **1014/1019 = 0**，非零只有 2(×2)、9(×2)、4(×1) | 枚举有 `BugPredators/BotAssault/…`，但本 build 基本未接线 ⇒ 改它大概率无效 |
| `GuardForceType` | **+0x15F** | 25 个值（0:317、25:120、5:84…） | 守卫力量编成（filediver 无枚举名）⚠ |
| `StampRaceAffiliation` | **+0xE8** | 位掩码 | 阵营门控（不是变种）⚠ |

### 6.4 presence 的唯一关卡生成钩子：天气（`✓ 离线`）

`weather_settings` 里有 6 条路径形如
`content/level_generation_settings/galactic_presence_overrides/weather_settings/<presence>_<state>`，
覆盖 `gloom` / `hiveworld_clear` / `illuminate_ritual_storm` 等事件状态。
**这条目录名本身说明了官方设计意图：presence 会 override 天气，但没有任何 `galactic_presence_overrides/enemy*`。**
敌人变种的分发不在数据层。

---

## 7. 本地可改点 + 下一步实验（均为单变量、可回滚，尚未做）

### 7.1 可改点排序

| # | 表 | 字段 | 现值 | 预期局内效果 | 置信度 |
|---:|---|---|---|---|---|
| 1 | `zone_data` | `PatrolSetting +0x16C` | 0:65 / 2:19 / 1:3 / 3:1 | 切到 2 = 巡逻预设 2 `(2,20,2,20,10,66,2,0,12,12,30)`：数量/间隔/半径类参数整体变化 —— **最可能改变巡逻密度/规模** | ✓ 字段与预设实证，⚠ 局内语义未证 |
| 2 | `zone_data` | `PatrolFloat1..11 +0x170..+0x198` | 88 行仅 6 组 | 单变量微调预设参数（哪个 float 管数量未知，需一次一改） | ⚠ |
| 3 | `location_groups` | `LocationStampInfo.EnemyTag +0xD0` | 1014/1019 = 0 | 给具体 stamp 指定敌人组成（`BugPredators`…）；**几乎全 0 说明可能未接线** | ✓ 分布实证，⚠ 行为未证 |
| 4 | `location_groups` | `GuardForceType +0x15F` | 25 个值 | 守卫编成（枚举名缺） | ⚠ |
| 5 | `planet_region_settings` | `RaceType +0x18` | 1 SE 344 / 3 Cyborg 25 | 城市模板阵营（人类城 vs 生化人城）| ⚠ |
| 6 | `region_settings` | `SubRegionSettingsOverride.RaceAffiliation +0xAB4+0x14` | 0×1028 / 1×76 / 2×76 / 4×4 | 子区域阵营门控（不是变种）| ⚠ |
| 7 | `planet_data` | `PlanetType +0x1B8` / 色板 | 12 枚举 | 换生态/雾色，纯表现 | ✓ 布局 |

**没有一条等价于 `variant_mod`**：上面最多改"数量 / 阵营 / 守卫类型"，不会引入掠食/孢裂这类变种。

### 7.2 三个实验（按性价比排序）

| # | 实验 | 改什么 | 观测 | 判读 | 回滚 |
|---|---|---|---|---|---|
| E1 | **巡逻强度** | `zone_data` 某 zone 的 `PatrolSetting` 0 → 2（连带 11 个 float 按预设 2 覆盖）| 该 zone 的巡逻队规模/间隔 | 有变化 ⇒ 本地"刷怪强度"旋钮成立 | 还原 1 字节 + 44 B |
| E2 | presence 键是引用还是同名 | `planet_region_settings` 行 99 的 8 字节改成 `bugs_super_predator` 的键 `0x108005CC32E23269` | 有没有星球/区域冒出掠食单位 | 出现 ⇒ 离线 presence 引用成立（意外收获）；无变化 ⇒ 同名同哈希，本条闭合 | 还原 8 字节 |
| E3 | 生态可视化 | `planet_data` 某行星 `PlanetType` 换成另一生态 | 进图地表/雾色 | 用于确认"planet_data 是活字段" | 还原 4 字节 |

三条都要求：保哈希编辑（`plain_edit.py` 或实体库写法）、`patch_N` 封包、装盘回读、单变量、先备回滚目录。
E2 的键值取自 `out/planet/presence-variants.json`。

---

## 8. 工具与复现

* `tools/planet_tables.py`（本会话新增）
  * `survey` —— 全表清单（多容器分开列；`shape` 列区分 `1/grp+tail` 与 `N/grp`）
  * `fields <table> [--type N]` —— typelib 成员偏移/宽度/类型
  * `dump <table> [--type N] [--limit N] [--json out.json]` —— 解行：字符串指针、数组头 `(offset,count)`、标量
  * `names <table>` —— 每组尾部字符串
* [PLANET-DATA-FIELDS-26088801](PLANET-DATA-FIELDS-26088801.md) —— planet_data 41 成员字段图（逐字段证据）；全量数据 `out/planet/planet-data.json`
* [LEVELGEN-FIELDS-26088801](LEVELGEN-FIELDS-26088801.md) —— 关卡生成链字段图（451 行）+ 分布；数据 `out/planet/levelgen.json`
* `out/planet/presence-variants.json` —— 16 变种 × effect id × presence 行 × 身份/类别键
* `tools/probes/planet/presence_scan_all.py`、`presence_arrays.py`、`join_variants.py` —— §3 的三段证据（只读，绝对路径输入）

**五个坑**（本会话实际踩到）：

1. **行数不能用 `Σ size//stride`**：`1 行/组 + 组内数组尾` 形态的表（`zone_data`、`planet_data`、presence）
   会被算成多行 —— `zone_data` 因此被报成 517 行，真实 **88 行 = ZoneId 数**。`survey` 的 `shape` 列就是为这个加的。
2. 表可能有**多个容器**（`region_settings` 是 74 组 + `u32 13` + 13 组），只走第一个容器会把第二容器当
   "残余字节"，从而误判"region 无处可 join"。
3. presence 行的数组**空值编码是 `offset=某值, count=0`**：把 offset 当 id 会得出"presence 互相引用"的假结论
   （我最初就把 `1076/1080/1084` 当成引用 id 了，实际是空数组的偏移）。
4. **偏移必须以 typelib 为准**：filediver 的 `GenerationRegionSettings` Go 结构算出来 5200 B，本 build 是 3272 B
   （`SubRegionSettings@+0x238`、`Overrides@+0xAB4`）。Go 结构只提供**字段名与顺序**。
5. `DLArray` 是 16 B（`int64 offset, u64 count`）且**数组实体在组尾**，不能按行宽去读；`decode_row` 对
   `type_id==0` 的 16 B 成员也曾漏判成十六进制标量（工具已修）。
