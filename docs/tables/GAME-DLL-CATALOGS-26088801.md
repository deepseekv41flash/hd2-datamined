# `game.dll` 两张硬编码目录：Operation 类型/impact 族 + 舰船升级模块（build 26251122，✓ 只读）

> 承接 [GAME-DLL-PLAINTEXT-26088801](GAME-DLL-PLAINTEXT-26088801.md) 的“高价值线索”。本文把两个数据簇解到可用粒度；
> 提取器：`tools/gamedll_catalog_extract.py`（`--json out/gamedll-catalogs.json`）。

## 1. Operation 类型 / impact 定义族（`.rdata` 0x2077570，12 条 × 0xA8 B）

`+0x10` 的 impact 文案非空即视为一条；`0x2077570` 起连续 **12 条**（更早/更后是别的结构，含 `stride 0x150/0x210` 的变体簇）。

| # | `+0x00/04/08` | impact（`+0x10`，`+0x14`/`+0x18` 同文重复） | 百分比标签 `+0x1C` | 类型标签 `+0x20` |
|---:|---|---|---|---|
| 0 | 1/1/0x01010101 | Completing this operation contributes to the planet's **Liberation**. | `#PERCENTAGE% LIBERATED` | OPERATION |
| 1 | 1/1/0x01010101 | 同上 | LIBERATED | OPERATION |
| 2 | 1/3/0x01010101 | 同上 | LIBERATED | OPERATION |
| 3 | 0/1/0 | 同上 | LIBERATED | OPERATION |
| 4 | 0/3/0 | 同上 | LIBERATED | OPERATION |
| 5 | 1/1/1 | 同上 | LIBERATED | OPERATION |
| 6 | 1/1/1 | Completing this operation contributes to the planet's **Defense**. | LIBERATED | OPERATION |
| 7 | 1/3/1 | 同上（Defense） | LIBERATED | OPERATION |
| 8 | … | Completing this Operation helps **reclaim this city**. Successfully reclaiming… | `#PERCENTAGE% LIBERATED` | CITY OPERATION |
| 9 | … | Completing this Operation helps **hold this city**. Successfully holding… | `#PERCENTAGE% HELD` | CITY OPERATION |
| 10 | … | Completing this Operation helps **liberate this Megafactory**. Each liberation… | LIBERATED | MEGAFACTORY OPERATION |
| 11 | … | （空 impact 占位）| LIBERATED | MEGAFACTORY OPERATION |

字段布局（记录 0 全字段实测）：

| 偏移 | 内容 | 备注 |
|---:|---|---|
| `+0x00/+0x04/+0x08` | 3 个 u32 小枚举 | 取值 `1 / 1 / 0x01010101`、`1/3/1`、`0/1/0`… ⚠ 未证（疑似 阵营/攻守/难度档）|
| `+0x0C` | locid `OPERATION IMPACT` | 卡片标题模板 |
| `+0x10/+0x14/+0x18` | 同一条 impact 文案 locid ×3 | 三种语境（Liberation/Defense/City 各一套表）|
| `+0x1C` | `#PERCENTAGE% LIBERATED` / `#PERCENTAGE% HELD` | 进度标签 |
| `+0x20` | `OPERATION` / `CITY OPERATION` / `MEGAFACTORY OPERATION` | 类型标签 |
| `+0x24` | 0 | — |
| `+0x30..+0xA4` | 4×6 个 8 字节 hash（全表同位置重复出现）| ⚠ 未解，疑似图标/音效/条件 hash |

**结论**：这族只是**操作卡片的文案模板表**——没有 `operationSettingsId`、没有 modifier 数量/池字段。
服务器下发的 `operationSettingsId`（抓包 8 个里只有 1 个在本地命中，见主文档）**不是这张表的索引**；
“任务级 modifier 怎么选”在这张表里依然看不到（只能靠加密代码/运行时）。

## 2. 舰船升级模块（`.rdata` 0x208A454，44 条 × 0x30 B）

记录布局：`+0x00` 名称 locid、`+0x04` 描述 locid、`+0x08` 效果模板 locid（含 `#VALUE`/`#VALUE%`）、
`+0x1C` hash、`+0x20` u32、`+0x24` f32（#VALUE 的候选数值，如 0.9=10%、2.0、0.7=30%…）。

44 条全表（`效果模板` 优先于描述）：

| # | 模块 | 效果（模板/描述） |
|---:|---|---|
| 0 | AUTOMATED HELLPOD LOADING | Reduces cooldown for Hellpod stratagems by 10%. |
| 1 | PRE-FILLED HELLPODS | …by an additional 10%. |
| 2 | EXPANDED ARMORY | Allows 1 additional use per mission for all Hellpod stratagems. |
| 3 | ENHANCED COOLING SYSTEM | Reduces cooldown for Strike stratagems by 10%. |
| 4 | EXPANDED CREW | …by an additional 10%. |
| 5 | IMPROVED GUIDANCE SENSORS | Reduces call-in time for Strike stratagems by 30%. |
| 6 | AUTOMATED FORTIFICATION ASSEMBLY | Reduces cooldown for all Fortification stratagems by 10%. |
| 7 | SPRING-LOADED HINGES | Reduces set-up time for all Fortification stratagems by 30%. |
| 8 | DOUBLE THICKNESS PANELS | Increases durability of Fortification emplacements by 50%. |
| 9 | LIQUID HYDROGEN COOLANT | Reduce cooldown for Barrage Stratagems by 10%. |
| 10 | ADDITIONAL GUN CHAMBERS | Increase number of salvos fired per barrage stratagem by 1. |
| 11 | SLIMLINE BOMB CASINGS | Barrage stratagems fire twice as many bombs in each salvo. |
| 12 | XXL WEAPONS BAY | Eagle multi-bomb stratagems drop `#VALUE` additional bomb(s). |
| 13 | PIT CREW HAZARD PAY | Reduces Eagle Rearm time by `#VALUE%`. |
| 14 | EXPANDED WEAPONS BAY | Increases Eagle stratagem uses per Rearm by `#VALUE`. |
| 15 | FULLY-AUTOMATED ASSEMBLY | Reduces cooldown for Sentry stratagems by 10%. |
| 16 | HIGH-QUALITY LUBRICANT | Sentries rotate towards new targets more quickly. |
| 17 | EXPANDED SENTRY MAGAZINES | Increases ammunition for Sentry emplacements by 50%. |
| 18 | TARGETING SOFTWARE UPGRADE | `#VALUE-second` reduction in call-in time for all Orbital stratagems. |
| 19 | NUCLEAR RADAR | Increases minimap enemy ping radius by `#VALUE%`. |
| 20 | POWER STEERING | Improves steering for Helldivers during Hellpod deployment. |
| 21 | EXPLODING SHRAPNEL | Reduces damage falloff from center of explosions caused by orbital Stratagems. |
| 22 | HIGH-DENSITY EXPLOSIVES | Increases the damage radius on explosions caused by orbital Stratagems by `#VALUE%`. |
| 23 | MORE GUNS | Barrage orbitals fire `#VALUE` additional salvo(s) per barrage. |
| 24 | ZERO-G BREECH LOADING | Orbital stratagem cooldown time reduced by `#VALUE%`. |
| 25 | LIQUID-VENTILATED COCKPIT | Eagle stratagem cooldown time reduced by `#VALUE%`. |
| 26 | DONATION ACCESS LICENSE | Support Weapons deploy with the maximum number of carriable magazines. |
| 27 | STREAMLINED REQUEST PROCESS | Decreases Support Weapon stratagem cooldown by `#VALUE%`. |
| 28 | PAYROLL MANAGEMENT SYSTEM | Reduces reload time for all support weapons by `#VALUE%`. |
| 29 | HAND CARTS | Decreases cooldown for all Backpack stratagems by `#VALUE%`. |
| 30 | SYNTHETIC SUPPLEMENTATION | Reduces cooldown for Sentry/Emplacement/Resupply stratagems by `#VALUE%`. |
| 31 | ADVANCED CONSTRUCTION | Increases health of Sentry stratagems by `#VALUE%`. |
| 32 | RAPID LAUNCH SYSTEM | All Emplacement stratagems launch immediately once called in. |
| 33 | DYNAMIC TRACKING | All Sentry stratagems launch immediately once called in. |
| 34 | SHOCK ABSORPTION GEL | Increases ammo for all Sentry stratagems by `#VALUE%`. |
| 35 | ENHANCED COMBUSTION | Fire damage from Stratagems increased by `#VALUE%`. |
| 36 | ATMOSPHERIC MONITORING | Orbital HE barrage spread reduced by `#VALUE%`. |
| 37 | SUPERIOR PACKING METHODOLOGY | Resupply Stratagem boxes refill Support Weapons with the maximum number… |
| 38 | CIRCUIT EXPANSION | Lightning arcs, fired from weapons and turrets, jump to one additional enemy. |
| 39 | BLAST ABSORPTION | Sentries take `#VALUE%` less damage from explosions. |
| 40 | MORALE AUGMENTATION | Reduces cooldown time for all Stratagems by `#VALUE%`. |
| 41 | STREAMLINED LAUNCH PROCESS | All Support Weapon stratagems launch immediately once called in. |
| 42 | CROSS-PLATFORM COMPATIBILITY | Mortar Sentries prioritize fire at marked targets. |
| 43 | ADVANCED CREW TRAINING | Eagle Rearm cooldown further reduced by `#VALUE%` if called… |

**本地对表结果**：`generated_stratagem_upgrade_settings.dl_bin` 在**三个 build 里都是 133 B 空文件**
（26251122 / 26088801 / plaintext-all 全部 size=133），且 44 条模块的 locid 在全部 55 张明文本表中 **0 命中**
⇒ 舰船模块**不在 dl_bin 数据表里**，名/描述/参数都是引擎侧硬编码（本表）。因此：
- 能做的“对表”= 把上面 44 条拿去**游戏内 Super Destroyer 菜单逐条核对**（或社区清单），
  差集才是“未发布/预留模块”；
- `#VALUE` 的实际数值候选在记录 `+0x24` f32（如 0.9=10%、0.7=30%、2.0），精确语义 ⚠ 未证（需要运行时/反汇编）。

## 3. 与任务级 modifier 的关系（诚实结论）

- Operation impact 族里**没有** modifier 字段——它只是操作卡文案；
- 舰船模块表里也**没有** Operation Modifier 相关字段；
- “难度/seed → 任务级 modifier”的选择逻辑仍在加密 `.text` 里，本轮**没有再前进**；
  可行路径仍是运行时内存 dump，或等代码段解密。

## 4. 复现

```bash
python tools/gamedll_catalog_extract.py --json out/gamedll-catalogs.json
# → {"opmods":13, "opsets":12, "ship_modules":44}
```

证据等级：偏移/条目/文案 = ✓ 离线可复算；`+0x00/04/08`、hash 字段、`+0x24` 语义 = ⚠ 推断；
“44 条 vs 游戏内菜单”的差集 = ⚠ 未做（需要菜单侧清单）。

## 2.1 对表结果：**30 条已发布 / 14 条未发布**（✓ wiki 基准）

基准：[Helldivers Wiki · Ship Modules](https://helldivers.wiki.gg/wiki/Ship_Modules)（页面最后编辑 2026-09-08，
共 **30 条**已发布模块，6 个区各 5 条）。把 44 条硬编码名与 wiki 30 条逐条对表：

- **30/30 已发布模块全部命中**（说明提取无遗漏、命名一致）；
- 剩下 **14 条只存在于 game.dll、wiki/游戏内菜单没有** ⇒ **未发布/预留模块**：

| # | 未发布模块 | 效果模板（`#VALUE` 为待定参数） | 疑似所属区 |
|---:|---|---|---|
| 0 | AUTOMATED HELLPOD LOADING | Reduces cooldown for Hellpod stratagems by 10%. | 爱国行政中心（哨戒/投放类）|
| 1 | PRE-FILLED HELLPODS | …by an additional 10%. | 同上 |
| 2 | EXPANDED ARMORY | Allows 1 additional use per mission for all Hellpod stratagems. | 同上 |
| 3 | ENHANCED COOLING SYSTEM | Reduces cooldown for Strike stratagems by 10%. | 轨道炮 |
| 4 | EXPANDED CREW | …by an additional 10%. | 轨道炮 |
| 5 | IMPROVED GUIDANCE SENSORS | Reduces call-in time for Strike stratagems by 30%. | 轨道炮 |
| 6 | AUTOMATED FORTIFICATION ASSEMBLY | Reduces cooldown for all Fortification stratagems by 10%. | 工程湾（工事）|
| 7 | SPRING-LOADED HINGES | Reduces set-up time for all Fortification stratagems by 30%. | 同上 |
| 8 | DOUBLE THICKNESS PANELS | Increases durability of all Fortification emplacements by 50%. | 同上 |
| 9 | LIQUID HYDROGEN COOLANT | Reduce cooldown for Barrage Stratagems by 10%. | 轨道炮（弹幕）|
| 10 | ADDITIONAL GUN CHAMBERS | Increase number of salvos fired per barrage stratagem by 1. | 轨道炮（弹幕，与已发布 MORE GUNS 同效果）|
| 11 | SLIMLINE BOMB CASINGS | Barrage stratagems fire twice as many bombs in each salvo. | 同上 |
| 15 | FULLY-AUTOMATED ASSEMBLY | Reduces cooldown for Sentry stratagems by 10%. | 机器人车间 |
| 17 | EXPANDED SENTRY MAGAZINES | Increases ammunition for Sentry emplacements by 50%. | 同上 |

> 规律：14 条恰好是 **6 个区里“第 0/1/2 级”的旧设计稿**（已发布的 30 条 = 2024-04 第 4 级 + 2024-07 第 5 级 + 首发 3 级里挑的 30 条），
> 名称/描述/参数都完整、字符串也已本地化 ⇒ 属于**引擎里有实现、菜单未放出**的预留模块（和之前 Operation Modifiers 同类现象）。
> 这些模块**不在 dl_bin 数据表**里，所以数据路线无法直接启用；要实现只能走引擎/内存路线（EAC 风险，未做）。

## 2.2 结论修正

`generated_stratagem_upgrade_settings.dl_bin` 恒为 133 B 空表并不能说明“模块表被删”——模块定义从来不在 dl_bin，
而是 `game.dll` 这张 44 条表 + 引擎实现；wiki 30 条与 44 条的对表就是完整证据链（30/30 + 14 未发布）。


---

## 5. Booster（配装增益）定义表 —— 2026-11-06 新发现（`0x2CB4840`）

> **✓ 收口入口**：整条 Booster 线的全表、机制四形态、能力边界与未解清单见
> [BOOSTER-COMPLETE-26088801](BOOSTER-COMPLETE-26088801.md)；本节只留表本体与三个特例的原始记录。

**背景**：代理侧注入 `cat 5`（`progressionCategory=5`，30 条）即可解锁 Booster（实机 ✓，见 proxy 仓库
`UNLOCK-MAP` §10，R2）。但**55 张 `generated_*` 明文表里没有 Booster 表** —— 定义在 `game.dll`。

### 5.1 表位置与结构

| 项 | 值 |
|---|---|
| 文件 | `data/game/game.dll`（46.8 MB）|
| 基址 | **`0x2CB4840`** |
| 步长 | **`0x38`（56 B）** |
| 条数 | **21**（idx 0 = `NO BOOSTER`，其后 20 个真实 Booster）|

记录字段（偏移相对记录首字节）：

| 偏移 | 类型 | 含义 | 例（VITALITY ENHANCEMENT）|
|---|---|---|---|
| `+0x00` | u32 | **itemId**（= 目录里 `cat 5` 的 `mixId`）| `1110686504` |
| `+0x04` | u32 | 0（保留；`SURPLUS EAT ALLOCATION` 这条是 15，语义 ⚠）| 0 |
| `+0x08` | f32 | **强度/倍率**（语义 ⚠ 未证，但与效果强弱档位吻合）| `0.9` |
| `+0x0C` | u32 | 恒 1（flag/count，⚠）| 1 |
| `+0x10` | u32 | **名称 locid（全大写）** | `'VITALITY ENHANCEMENT'` |
| `+0x14` | u32 | **名称 locid（标题式）** | `'Vitality Enhancement'` |
| `+0x18` | u32 | **描述 locid** | "Provides minor damage reduction…" |
| `+0x1C` 起 | u32×n | 另有 4–6 个 locid（短/长描述、参数化模板等）| — |

### 5.2 全表（20 条真实 Booster + 强度值）

| idx | itemId | 强度 f32 | 名字 |
|---:|---:|---:|---|
| 0 | 2747100039 | 1.000 | NO BOOSTER（占位）|
| 1 | 1110686504 | 0.900 | VITALITY ENHANCEMENT |
| 2 | 684729784 | 1.300 | STAMINA ENHANCEMENT |
| 3 | 2776452811 | 0.350 | MUSCLE ENHANCEMENT |
| 4 | 4136928865 | 1.500 | UAV RECON BOOSTER |
| 5 | 4066886572 | 1.000 | INCREASED REINFORCEMENT BUDGET |
| 6 | 4273318008 | 0.750 | FLEXIBLE REINFORCEMENT BUDGET |
| 7 | 1908198785 | 1.500 | HELLPOD SPACE OPTIMIZATION |
| 8 | 876985512 | 0.900 | LOCALIZATION CONFUSION |
| 9 | 3504405746 | 0.700 | EXPERT EXTRACTION PILOT |
| 10 | 2709264466 | 0.500 | MOTIVATIONAL SHOCKS |
| 11 | 3912131454 | 1.000 | EXPERIMENTAL INFUSION |
| 12 | 3102833400 | 1.000 | FIREBOMB HELLPODS |
| 13 | 336215081 | 0.150 | SAMPLE SCANNER |
| 14 | 2239116615 | 0.050 | DEAD SPRINT |
| 15 | 3793458484 | 0.000 | ARMED RESUPPLY PODS |
| 16 | 796779894 | 10.000 | SAMPLE EXTRICATOR |
| 17 | 1151328602 | 1.000 | STUN PODS |
| 18 | 1602836857 | 1.000 | CONCEALED INSERTION |
| 19 | 3545987157 | 0.500 | INTEGRATED EXTINGUISHERS |
| 20 | 1213901450 | 1.000 | SURPLUS EAT ALLOCATION |

### 5.3 覆盖度：目录 30 条里有 10 条**本地无 Booster 定义**

代理抓到的目录里 `cat 5` 共 **30** 条，本表只覆盖 **20** 条。剩下 10 条在整个 `game.dll` 里
**0 命中**（不止这张表，全文都搜不到）：

```
196883860  767342143  1046516979  1175500164  1195476753  1607993656  2031253145  2262930209  3126789594  3229102862
```

⇒ 这 10 条是**"服务端目录里有、本地没有 Booster 定义"**的条目 —— 与"未上架/占位"的形态一致。
（代理注入能解锁它们，但客户端拿不到本地定义，所以效果/名字可能异常；待单独观察。）

### 5.4 能力边界

- **改 Booster 的实际强度**：文件侧入口是 **game.dll 这张表**（`+0x08` f32 最像倍率，⚠ 未证）或 entities 侧的效果实现；
  **不是** dl_bin 明文表（那 55 张里没有 Booster 表）。
- **解锁 Booster**：走代理注入 `cat 5`（一行 inventory）即可，不需要动任何文件。

### 5.5 特例：`SURPLUS EAT ALLOCATION` 发的是**专用战备复制体**（2026-11-06 定）

`game.dll` Booster 表里这条记录**唯一**有一个非零的 `+0x04`：`15`（其余 20 条全是 0）——
这就是"有限次数"的来源。而战备表里 EAT-17 **有两条独立行**（名字与 locid 完全相同）：

| 内部名 | 显示名 | name_id | 战备表行 |
|---|---|---|---|
| `TEAM WEAPONS. EXPENDABLE ANTI-TANK` | Expendable Anti-Tank | `1885509695` | 行 103（原始）|
| `TEAM WEAPONS. EXPENDABLE ANTI-TANK (Booster)` | Expendable Anti-Tank | `1885509695`（**同一个**）| 行 104（**Booster 专用复制体**）|

两行逐字段对齐（`generated_stratagem_settings` 明文，行基址 `0xD57C` / `0xD70C`，步长 `0x190`=400 B），
共 **15 个 dword 不同**，关键差异：

| 偏移 | 原版（行 103）| Booster 版（行 104）| 解读 |
|---|---|---|---|
| `+0x008` | **151** | **15** | **两条独立的 stratagem id** |
| **`+0x058`** | **`0xFFFFFFFF`** | **`2`** | **使用次数：原版=无符号（无限）→ 复制体=2（有限）** ⚠ 字段名待与 `STRATAGEM-FIELDS` 交叉确认 |
| `+0x020…+0x02C` | `15975 / 0 / 16003 / 0` | 全 `0xFFFFFFFF` | 复制体少了 4 个 locid（描述类字段为空）|
| `+0x088` | 3 | 1 | 数量类差异 ⚠ |
| `+0x09C` | 0 | 1 | 标志位差异 ⚠ |
| `+0x070` | `1116471296`（f32 8.0）| 0 | 数值差异 ⚠ |
| 其余 9 处 | — | — | 多为 locid / 索引顺延 |

**结论**：Surplus EAT Allocation **不是**调用原版 EAT-17（id `151`），而是发放一条**专用复制体**（id `15`），
两者显示名与 name_id 完全相同，所以界面上看起来一模一样；复制体自带"有限次数"（`+0x058=2`），
因此不会污染原版 EAT-17 的无限使用。⇒ 想改这个 Booster 的"给多少发"，动的是战备复制体行的
`+0x058`（`max_uses`，2）；Booster 表 `+0x04` 只是**指向**那条复制体（见 §5.5.1）。

#### 5.5.1 `+0x04` 不是"数量"，更像"关联战备 id"（2026-11-06 晚修正）

原先把 `+0x04 = 15` 读成"发放 15 次"，但 15 恰好等于 **EAT 复制体自己的 stratagem id**，而其余 20 条
Booster 全是 0（它们没有任何关联战备）。两者择一，后者解释力更强：

| 证据 | 读数 |
|---|---|
| EAT 复制体 stratagem id | `15` |
| `SURPLUS EAT ALLOCATION` 的 `+0x04` | `15` |
| 其余 20 条 Booster 的 `+0x04` | 全 `0`（且它们在战备表里都没有"(Booster)"变体）|

⇒ 记作 **"关联战备 id，0 = 无"**（⚠ n=1 的强假设，还没有第二个非零样本）。真正决定"几发"的是
被指向的那条战备行的 `+0x058`。

---

## 5.6 特例：`ARMED RESUPPLY PODS` 用的是**代码生成的独立炮塔实体**（2026-11-06 定）

和 §5.5 完全不同的机制 —— 这条 Booster **没有**任何战备复制体，它靠代码把一台炮塔挂到补给舱上。

### 5.6.1 先说否掉的三条路

| 假设 | 否证 |
|---|---|
| 有一条"Resupply (Booster)"战备复制体 | 战备表 153 行里 `RESUPPLY` 只有 2 行（id `34` 玩家版 / id `112` 任务版），全表唯一带 `(Booster)` 后缀的行是 EAT 那条 |
| Booster 表里存了实体/战备引用 | ARP 记录（idx 15）：`+0x04=0`、`+0x08=0.0`、`+0x0C=1`，其余 10 个 dword 全是 locid；**整条记录没有任何实体哈希字段** |
| 炮塔是补给舱 `MountComponentData` 里的挂载件 | 补给舱实体 `0x5052EC6A928CCF1A`（`content/fac_helldivers/hellpod/ammo_rack/ammo_rack`）只有 **13 个组件**，**不含** `Mount` / `Turret` / `ProjectileWeapon` / `Wieldable`；`MountComponentData` 165 行里也没有它 |

补给舱的 13 个组件：`Animation` `Attachable` `Destructible` `Faction` `Health` `HellpodPayload`
`HellpodRack` `LoadoutPackage` `Spottable` `StatusEffectReceiver` `Tag` `Unit` `UnitCustomization`。

### 5.6.2 炮塔本体：`0x73681FFD58FA1A90`

做法：把全库 242 个"同时有 `WeaponMagazine` + `ProjectileWeapon`"的实体逐条读 `+0x88`（弹匣容量）
与 `+0x08`（射速）——**容量 140 的实体全库只有一个**，就是它。

| 字段 | 读数 | wiki（Armed Resupply Pods / AR-23P P）|
|---|---|---|
| `WeaponMagazine +0x88` 容量 | **140** | Capacity **140** ✓ |
| `ProjectileWeapon +0x08` 射速 | **640** | Fire Rate **640 rpm** ✓ |
| `ProjectileWeapon +0x00` 弹丸类型 | `8` | 与 M-103 炮塔同型，wiki 标 `AR-23P P` ✓（二者同弹丸）|
| `ProjectileWeapon +0x10` 距离 | `75` | — |
| `Behavior +0x00`（**AIBEH**）| **`214`** | —（FRV 那台是 `213`）|
| `SensorEye +0x00` / `Targeting +0x00` | `25` / `25` | wiki 写 30 m ⚠ |
| `Turret +0x08` / `+0x0C` | `50` / `80`（俯仰/水平转速）| — |
| `Turret +0x14…+0x20` 角度限位 | `-60 / 90 / -180 / 180` | — |
| `HellpodPayload +0x04` 寿命 | **`0`**（不自行撤走）| "until ran out of bullets or the pod itself being demolished" ✓ |
| `HellpodPayload +0x08` 载荷模板 | `1272` | — |
| 组件数 | **24**，且**没有** `WeaponReload` | "打完就停"，不能装填 ✓ |

### 5.6.3 同族对照：M-103 Supply FRV 的炮塔 = 真·挂载件

`MountComponentData` row 121（宿主 `0x9B2140378640432E` = M-103 车身）slot 0 的件是
`0x4DF41F84668D07FB`，与上面那台只差三点：

| 字段 | ARP 炮塔 `0x7368…` | FRV 炮塔 `0x4DF4…` | wiki M-103 |
|---|---|---|---|
| 容量 `+0x88` | **140** | **120** | Capacity **120** ✓ |
| 射速 | 640 | 640 | 640 ✓ |
| 弹丸 | 8 | 8 | AR-23P P ✓ |
| AIBEH `Behavior+0x00` | `214` | `213` | — |
| 转速 `Turret +0x08/+0x0C` | 50 / 80 | **90 / 130** | ↔130 ↕90 ✓✓ |
| `WeaponReload` 组件 | **无** | **有** | "可用补给架装填" ✓ |
| 寿命 `HellpodPayload+0x04` | 0 | 0 | — |
| 装载包 `LoadoutPackage+0x08` | `0xFB48DE3E9D5F187C` | `0xFB48DE3E9D5F187C` | — |

转速 90/130 与 wiki 逐值吻合，说明 `Turret +0x08/+0x0C` 的读法没问题，也说明这两条是"同一族的
两份实体"，不是同一个东西（容量与装填能力是刻意分开的）。

### 5.6.4 为什么判定"代码生成"而不是"数据挂载"

- `0x73681FFD58FA1A90` 在 `generated_entities.dl_bin` 里**零外部引用**（只有自己的
  `UnitComponentData +0` 自引用）；55 张 `generated_*` 表、153 条战备载荷数组、165 行 `Mount` 表
  **全都不引用它**；
- 补给舱那 3 个同壳变体（`0x5052EC6A928CCF1A` / `0xD7F32C2DF7934784` / `0xAF04113302F5621D`）
  组件集完全相同，也没有任何"带武装"的补给舱变体存在（全库没有 `HellpodRack + 武器` 的实体）；
- `game.dll` 里也不含任何实体哈希（49 MB 全文 u64 命中 0）⇒ 生成关系只可能在代码里，靠哈希表
  在加载期解析。

⇒ 最合理解释：**ARP 生效时，代码在补给舱落地点额外拉起 `0x73681FFD58FA1A90` 这台炮塔**，
它自带 AIBEH/索敌/转动/无限时长，所以看起来像"挂"在舱顶。

### 5.6.5 这条线的可改点（⚠ 未实机）

| 想改什么 | 改哪 |
|---|---|
| ARP 炮塔弹量 140 | `0x73681FFD58FA1A90` 的 `WeaponMagazine +0x88` |
| 射速 640 | 同行 `ProjectileWeapon +0x08` |
| 索敌距离（25 m）| `SensorEye +0x00` / `Targeting +0x00` |
| 转速 / 俯仰限位 | `Turret +0x08/+0x0C/+0x14…+0x20` |
| 会不会自己消失 | `HellpodPayload +0x04`（现 0 = 不消失）|
| AI 行为 | `Behavior +0x00`（214；FRV 是 213）|

因为 FRV 的炮是**另一个实体**（`0x4DF4…`），改 `0x7368…` 理论上只影响 ARP，不会连带改 M-103。
工具：`tools/entity_fields_batch.py set`（保内容哈希）。

### 5.6.6 还没证 / 下一步

- ⚠ 没有数据侧硬引用，**"0x7368… = ARP 炮塔"是字段吻合 + wiki 三值对上**的识别，不是引用链证明；
  唯一的一分钱验证：把 `+0x88` 从 140 改成 999，进一局带 ARP 打光看弹量。
- 同族之外还有 19 条 Booster，机制未必都像 EAT（复制体）或 ARP（代码生成炮塔）；`+0x04=0`
  说明它们都没有关联战备，具体形态要逐条挖。

### 5.7 另一类形态：投送舱落地爆炸（Firebomb / Stun Pods / Concealed Insertion）

这三条吃的是**爆炸表**，不是战备行也不是实体：`83`（Firebomb，伤害行 438）、`335`（Stun Pods，
伤害行 439）、`401`（Concealed Insertion，伤害行 0）—— 三条都是弹丸表 0 引用的"代码触发"行。
逐字段证据、改法边界见 [POD-IMPACT-EXPLOSIONS](../explosions/POD-IMPACT-EXPLOSIONS-26088801.md)。
