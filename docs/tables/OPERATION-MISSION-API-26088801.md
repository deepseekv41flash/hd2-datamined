# Operation / Mission API 字段含义（build 26251122，2026-10-29 + 11-01 抓包 + game.dll 对表）

> 数据源：`variant_mod` MITM 代理（本机 hosts 劫持 `api.live.prod.thehelldiversgame.com`，只改写 `/api/WarSeason/801/Status`，
> 其余端点只读落盘）。本版本基于 **6 局任务**的完整请求/响应 + 前后 Status 快照：
> `D:\mod\out\gwe\`（`req_*_api_Operation_*.json` / `*_api_Operation_*.json` / `*_api_WarSeason_801_Status.json`）。
> 交叉源：`refs/strings-en-26088801.json`（locid→文案）、本 build 明文 `game.dll` `.data`（目标表见
> **`MISSION-OBJECTIVES-26251122.md`**）、`out/planet/index-names-801.json`、`Status` 抓包。
> HD2Runtime 本地仓库里没有这些字段的文档（grep `jointOperation/operationSettingsId/territoryIndex/...` = 0 命中）。

## 0. 一句话

`Operation` = **客户端向服务器“认领/创建”的一次作战配置**（客户端先提案、服务器确认 id）；
`Mission/Start` 只拿 `missionId`；
`Mission/end` 的**请求**是"客户端报告+结算输入"（其中 `warTime`/`healthAtStart*` 是**客户端缓存的 Status 快照**，不是服务器实时值），
**响应**是服务端结算结果（经验/倍率/徽章影响力/奖励/战役进度）。
任务级 modifier 不在这些字段里（见 `OPERATION-MODIFIERS-26088801.md`）。

## 1. 六局样本总表（全部本号段抓包）

| 局 | `operation.type` | 任务 `type` | 难度 | 星球 | 目标数 | badges | XP | 影响力合计 | 货币(3608481516) | `impact` | `campaignWon` | `othersImpactPlanetEvent` |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---|---:|
| 11-01 解放 100（成功）| 0 | 1 | 8 | TRANDOR(100) | 1 | 6 | 267 | 89 | 1,038 | 2 | false | 0 |
| 11-01 解放 100（失败）| 0 | 1 | 8 | 100 | 1 | 1 | 0 | 0 | 0 | 0 | false | 0 |
| 10-29 真防守 244 | 4 | 3 | 5 | UVARYLIA 5(244) | 1 | 5 | 210 | 120 | 962 | 1 | false | 4,789 |
| 11-01 **伪造**防守 156 | 4 | 3 | 8 | CHARBAL-VII(156) | 1 | 6 | 258 | 86 | 1,002 | 2 | **true（伪值 ✗）** | **1,880,999（伪值 ✗）** |
| 11-01 城市分区 207 | 8 | 1 | 8 | MINTORIA(207) | 8 | 9 | 936 | 312 | 4,434 | 2 | false | 0 |
| 11-01 真防守 207 | 4 | 3 | 8 | MINTORIA(207) | 8 | 10 | 903 | 301 | 4,602 | 2 | false | **1,844** |

> 11-01 两局都在难度 8（Impossible），可直接横向对比；伪造防守那局的 `campaignWon/othersImpact*` 是"服务器不认识该事件"的残值，
> 原因见 §5.4。

## 2. `POST /api/Operation/Create`（客户端提案）

请求体（`{"operations":[{…}]}`，一次一个作战）：

| 字段 | 示例 | 含义 | 证据 |
|---|---:|---|---|
| `id` | 1237 | 客户端**先猜**的作战 id，服务器确认后同值返回 | ✓ Create 请求 id == 响应 `operations[].id` |
| `warId` | 801 | 大战 id | ✓ 与 Status 一致 |
| `planetIndex` | 156 | 星球索引 | ✓ `index-names-801`（156=CHARBAL-VII、207=MINTORIA）|
| `campaignId` | 51752 | 战役 id | ✓ 与 `Status.campaigns[].id` 一致（城市/防守同 campaign 也可）|
| `jointOperationId` | 5730 / **-1** | 联合作战/事件 id；**-1 = 无**（普通/城市作战）| ✓ 防守=事件 id；解放/城市=-1 |
| `type` | 0/4/8 | **作战类型**（见 §2.1）| ✓ 与任务形状互锁 |
| `difficulty` | 8 | 难度 1–10（8=Impossible）| ✓ 与 wiki 难度表 |
| `race` | 3 | 敌人阵营（2=终结族 / 3=自动机 / 4=光明族）| ✓ 与 Status owner/race 同枚举 |
| `missions[]` | `[{type,state,index}×N]` | 任务槽：`type`=任务类型（1 常规 / 3 防守）、`state`=1 未打 | ✓ 见 §2.2 |
| `seed` | 1544323042 | 随机种子（**每次 Create 都不同**）| ✓ 同星球多次建作战不同值 |
| `placementNodeIndex` | 9 | 部署节点（**每次 Create 随机**）| ⚠ 不是 `planetAttacks` 下标；同星球多次不同值（100 号：20/32/32/18/8/12；207 防守：20/12/26/1；207 城市：1/1）|
| `operationSettingsId` | 538077316 | 作战设置行 id（客户端选任务池用）| ✓ 见 §2.3 |

响应（60 B）：`{"operations":[{"id":1237,"rewards":[],"backupRewards":[]}]}` —— 只回执 id，没有 modifier/奖励字段。

### 2.1 `operation.type` 枚举（本号段实测）

| 值 | 含义 | 配套特征 | 实例 |
|---:|---|---|---|
| **0** | 普通解放战役 | `jointOperationId=-1`、3×任务 `type=1` | 100 TRANDOR、93、139、158… |
| **4** | **事件防守 / 联合作战** | `jointOperationId=<planetEvent.id>`、3×任务 `type=3` | 244(5729)、156(9101 伪造)、207(5730) |
| **8** | **城市分区作战** | `jointOperationId=-1`、3×任务 `type=1`、`Mission/Start.regionIndex≥0` | 207 MINTORIA region 1 |
| 9 / 13 | ⚠ 未解（旧抓包里出现在 0 号/260 号星球的特殊实验战役，`operationSettingsId` 也另属一档）| — | 2026-10-29 城市战役实验 |

### 2.2 `missions[].type`（= 任务类型，与 `Mission/end.type` 同值域）

| 值 | 含义 | 证据 |
|---:|---|---|
| 1 | 常规任务（解放 / 城市分区）| ✓ 本号段所有 type 0/8 作战 |
| 3 | **防守任务** | ✓ type 4 作战全部 3×type3；`Mission/end.type=3` 且带 `planetEventId` |

### 2.3 `operationSettingsId` 观察（⚠ 具体键未证，但规律清楚）

| 星球/类型 | 值 | 备注 |
|---|---:|---|
| 防守（156/244/207 三个星球、难度 5/8）| **538077316** | ✓ 防守类固定，与难度无关 |
| 解放 100（难度 1/6/8）| 2350081063 | ✓ 与难度无关 |
| 解放 139 | 2350081063；也有 2796992372 | ⚠ 跨天/跨 session 不同 |
| 解放 93 | 2796992372 / 3194790369 | ⚠ 同上 |
| 解放 158 / 182 | 2807074392 / 3194790369 | — |
| 城市 207 | **3204348594** | 城市分区专属 |
| 特殊（0 号/260 号，type 9/13）| 3766033139、2452579076、3866136882 | ⚠ 未解 |

## 3. `POST /api/Operation/Mission/Start`

| 字段 | 示例（防守 / 城市 / 解放）| 含义 | 证据 |
|---|---|---|---|
| `planetIndex` | 207 / 207 / 100 | 星球 | ✓ |
| `warId` | 801 | — | ✓ |
| `regionIndex` | **-1 / 1 / -1** | **城市分区索引**：`-1` = 非城市作战；`≥0` = 该城市分区 | ✓ 城市任务=1，其余=-1 |
| `operationId` | 1243 | 作战 id | ✓ |
| `missionIndex` | 2 | 第几个任务槽（对应 `missions[].index`）| ✓ |
| `territoryIndex` | 214 / 148 / 338 | 关卡地块索引（levelgen 地块；非城市也有值）| ⚠ 具体映射未解 |
| `participants[]` | 1 个平台 id | 参战玩家 | ✓ |
| → 响应 | `{"missionId":"0a859dd6-…"}` | 本局任务唯一 id，后续 end/操作状态引用 | ✓ |

## 4. `POST /api/Operation/Mission/end`（请求 = 客户端报告 + 结算输入）

### 4.1 字段表

| 字段 | 示例 | 含义 | 证据 |
|---|---:|---|---|
| `warSeasonId` / `planetIndex` / `race` / `campaignId` | 801 / 207 / 3 / 51752 | 同上 | ✓ |
| `type` | 3 / 1 | **任务类型**（1 常规、3 防守）；与 `operation.type` 不是同一枚举 | ✓ 见 §1 |
| `difficultyType` | 8 | 难度（= operation.difficulty）| ✓ |
| `isOperationOwner` | true | 是否作战发起者 | ✓ |
| **`warTime`** | **85605180** | **客户端最近一次缓存 `Status.time`（不是服务器实时时钟！）** | ✓ **6/6 局与抓包 Status 的 `time` 逐字节相同**（§4.2）|
| **`healthAtStartPlanet`** | 1300000 | **该 Status 快照里 `planetStatus[planet].health`** | ✓ 同上 |
| **`healthAtStartPlanetEvent`** | 2248348 | **该 Status 快照里 `planetEvents[planetEventId].health`**（仅防守任务）| ✓ 同上 |
| `planetEventId` | 5730 | 事件 id（仅防守任务）| ✓ 与 Status.planetEvents 一致 |
| `regionIndex` | 1 | 城市分区（**仅城市作战带此键**）| ✓ 仅 type 8 作战 |
| `operationId` / `missionIndex` / `missionId` | 1243 / 2 / uuid | 同 Start | ✓ |
| `campaignWonAtStart` | false | 开局时战役是否已被拿下（客户端缓存）| ✓ |
| `missionSuccess` | true | 任务胜负（只看撤离/结束判定，**不看目标完成数**）| ✓ 城市局 3 个侧目标失败仍 true |
| `objectives[]` | `[{id,succeeded}]` | **目标实例列表**；`id` = game.dll 目标表行键（见 `MISSION-OBJECTIVES-26251122.md`）；同一 id 可重复（3 个指挥地堡 = 3 条）；数量 1–8 随关卡生成 | ✓ 6 局 17 个 id 全部在目标表命中 |
| `badges[]` | `[{id32,amount}]` | **计数器**：本局发生的"徽章事件"及次数（击杀数/阵亡数/前哨数/目标完成…）| ✓ 与响应逐条对应（见 §5.2）|
| `participants[].extracted` | true | 是否撤离成功 | ✓ |
| `participants[].loadout` | `[2979303494,2979303494]` | 玩家**装备组合 hash**（两槽同值；在 `generated_entities.dl_bin` 里是行键）| ⚠ 具体编码未解 |
| `participants[].lootedItems[]` / `heavyLootedItems[]` | [] | 拾取物 / 重物 | ✓ |
| `participants[].progressedPackages[]` | `[{id32:277818845,factor:1}]` | 要推进的进度包 | ✓ |

### 4.2 `warTime` / `healthAtStart*` = 客户端 Status 快照（✓ 6/6 精确命中）

| 局 | `warTime` | 对应 Status 文件（`D:\mod\out\gwe\`）| 该 Status 的 event health |
|---|---:|---|---:|
| 10-29 真防守 244 | 85343300 | `8945e8dc_api_WarSeason_801_Status.json`（14:20Z）| 1,883,848（= 请求里的 `healthAtStartPlanetEvent`）|
| 11-01 解放 100（失败）| 85596140 | `2afb0fec_api_WarSeason_801_Status.json` | —（无事件）|
| 11-01 解放 100（成功）| 85596780 | `9620e606_api_WarSeason_801_Status.json` | — |
| 11-01 伪造防守 156 | 85600950 | `23195938_api_WarSeason_801_Status.json`（21:54:34）| 1,881,000（= 我们注入的 health）|
| 11-01 城市 207 | 85603350 | `7a647a36_api_WarSeason_801_Status.json`（22:34:36）| — |
| 11-01 真防守 207 | 85605180 | `7f6ae829_api_WarSeason_801_Status.json`（23:05:02）| 2,248,348 |

⇒ 结论：`warTime`/`healthAtStart*` 是"玩家开局时看到的世界"，**不是权威值**；做归因时必须拿对应 Status 一起比对。

## 5. `POST /api/Operation/Mission/end` 响应（结算结果）

### 5.1 字段表

| 字段 | 示例 | 含义 | 证据 |
|---|---:|---|---|
| `experience` | 903 | 本局经验 | ✓ |
| `multipliers[]` | `[{id32:851354768,factor:3,influenceFactor:3},{id32:540020798,factor:1,influenceFactor:1}]` | **难度倍率**：第一条按难度取 id、factor 与 influenceFactor 相同；第二条恒定 ×1（基础项）| ✓ 见 §5.3 |
| `badges[]` | 10 条，含 `amount/influence/itemRewards[{mixId,amount}]` | 每条徽章的**影响力贡献**与物品奖励；`influence` 合计 = 该局影响力 | ✓ 与 hd2 结算界面一致 |
| `campaignWon` | false | 本局结束后**战役是否被拿下**（防守 = 事件血量归零、解放 = 星球拿下）| ✓ 真防守 false；伪造局 true 为残值（§5.4）|
| `impact` | 2 | 本局战役进度贡献（**落点见 §5.5**）| ✓ 难度 5→1、难度 8→2（两档观测）|
| `othersImpactPlanet` | 0 | 本局期间**其他玩家**对星球本体的贡献 | ⚠ 两例均为 0 |
| `othersImpactCommunityTarget` | 1844 | 同上，对"社区目标"的贡献 | ✓ 与下一项同值（社区目标=事件）|
| `othersImpactPlanetEvent` | 1844 | **本局期间其他玩家把事件血量打掉的量** | ✓ 两例真防守验证（§5.6）|
| `progressionPackageUpdates[]` | `{platformAccountId,id32:277818845,level:6,progress:362}` | 等级/进度包更新 | ✓ 与经验对应 |
| `lootedItemRewards[]` / `lootedHeavyItemRewards[]` | [] | 拾取奖励回执 | ✓ |
| `rewards[]` | `[{mixId:897894480,amount:7},{mixId:3608481516,amount:4602}]` | 奖励货币/资源（mixId = 服务端奖励混合体）| ⚠ 命名空间未解（§5.7）|
| `levelUpRewards[]` / `repeatingPlayer[]` | [] | 升级奖励 / 连战重复玩家 | ⚠ |

### 5.2 `badges[]`：请求侧计数器 → 响应侧影响力/物品

| `id32` | 解锁情况 | 语义 | 影响力 | itemRewards |
|---:|---|---|---:|---|
| 4184186012 | ✓ locid | **Helldiver Replacements**（阵亡/增援次数）| 0 | — |
| 1624799956 | ✓ locid | **Successful Extraction** | 0 | — |
| 1595769879 | ✓ locid | **Destroyed Light Automaton Outpost** | 5 | 3608481516 ×50 |
| 2701252726 | ✓ locid | **Destroyed Medium Automaton Outpost** | 10 | 3608481516 ×100 |
| 4283980414 | ✓ locid | **Destroyed Heavy Automaton Outpost** | 20 | 3608481516 ×150 |
| 1449100876 | ⚠ hash | 未命名计数（amount 21–57，**影响力 = amount×1**）| ×1 | 3608481516 ×(4×amount) |
| 1265652808 | ⚠ hash | 每局成功必带（amount=1）| 0 | 897894480 ×7 |
| 3973473708 | ⚠ hash | 每局成功必带（amount=1）| 20 | 3608481516 ×50 |
| 3071768642 | ⚠ hash | 与"清剿/歼灭类目标"绑定的计数 id（目标表 `+0x54`，见目标表文档）；本号段 4 局 amount 恒为 8 ⚠ | 20 | 3608481516 ×100 |
| 889185878 | ⚠ hash | 真防守与城市战出现（amount=1）| 100 | 3608481516 ×500 |
| 1748229498 | ⚠ hash | 真防守与城市战出现（amount=2）| 100 | 3608481516 ×400 |
| 1495751876 | ⚠ hash | 仅 10/29 真防守出现（amount=1）| 0 | 897894480 ×4 |

> 请求里的 `amount` 是计数器次数；响应里除 `1449100876` 按次数线性计影响力外，其余是固定影响力（amount 只作展示）。
> 影响力量级参考：解放成功 89、真防守 120/301、城市 312；`influence` 与 `multipliers[0].influenceFactor` 的相乘关系 ⚠ 未验证。

### 5.3 `multipliers`：id32 按**难度**索引（✓ 本轮解出）

- `game.dll` `.data` **`0x205C578`** 起有一组 **10 个 u32**（index = 难度-1）：

| 难度 | 1 | 2 | 3 | 4 | **5** | 6 | 7 | **8** | 9 | 10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| id32 | 1029670384 | 2459419623 | 2389643433 | 4122185694 | **33707031** | 1237009911 | 1155577500 | **851354768** | 1714937842 | 1551907567 |
| factor（实测）| — | — | — | — | **1.75** | — | — | **3.0** | — | — |

- 验证：10/29 真防守难度 5 → `33707031 / 1.75`；11-01 解放/伪造防守/城市/真防守四局难度 8 → 全部 `851354768 / 3.0` ✓；
- 第二条 `540020798 / 1.0` 在 6 局里恒定（基础项）；
- 结论：**`multipliers` 只随难度变，与任务类型/星球/防守与否无关** ✓；难度 1–4/6/7/9/10 的 factor 未采到样本 ⚠（但 id32 表已给出）。

### 5.4 `campaignWon` 与"伪造战役"的残值（重要坑）

| 情形 | 响应值 |
|---|---|
| 真实防守（事件血量未归零）| `campaignWon=false`，`othersImpactPlanetEvent` = 其他玩家期间打掉的血量（真值）|
| 解放成功（星球未拿下）| `campaignWon=false` |
| **伪造防守**（服务器不认识 `campaignId 51990 / planetEventId 9101`）| `campaignWon` = **true**、`othersImpact*` = 1,880,999（= 注入事件血量 −1）⇒ **全部为残值，不能使用** |

⇒ 做防守实验时：**只要是自己伪造的 campaign/event，结算里 `campaignWon`/`othersImpact*` 一律视为无效**；
经验/影响力/徽章/奖励仍按真实结算发放。

### 5.5 `impact` 的落点：三条任务线各打各的血条（✓ 本轮实测）

| 任务线 | 落点 | 实测 |
|---|---|---|
| 解放（type 0 / 任务 type 1）| `planetStatus[planet].health` | 行星血量随全服进度变化（其它星球可观测下降）；本局 100 号因回血保持在满值，单局 −2 无法单独归因 ⚠ |
| 防守（type 4 / 任务 type 3）| `planetEvents[eventId].health` | 事件血量全服下降（23:05→23:46 掉 2,247）；本局 `impact=2` |
| 城市分区（type 8 / 任务 type 1 + `regionIndex`）| **`planetRegions[planet][regionIndex].health`** | **200,000 → 199,998 = −2 = `impact`**（该窗口内该分区只有我们这一局）✓ |

### 5.6 `othersImpactPlanetEvent` 语义（✓ 两例真防守验证）

| 局 | 操作窗口 | 返回值 | 期间事件实际掉血 | 折算 |
|---|---|---:|---|---|
| 10-29 真防守 244 | 14:22:15 → 14:43:13（21.0 min）| 4,789 | 同期速率 ≈200/min ⇒ ≈4,205 | ✓ 同量级 |
| 11-01 真防守 207 | 23:08:28 → 23:40:19（31.9 min）| **1,844** | 23:05→23:46（41.8 min）共掉 **2,247**；按窗口折算 ≈1,711–1,844（期间在线 2,693→3,062，速率上升）| ✓ 同量级 |

对照：解放任务与城市任务该字段恒为 0（任务不挂在事件上）。

### 5.7 `rewards[].mixId`（⚠ 命名空间未解）

| mixId | 出现的量级 | 推测 |
|---:|---|---|
| 897894480 | 4–7 | 小额资源（样本/奖章类）|
| 3608481516 | 962–4,602 | 大额资源（军票/征用点类）|

`rewards` 总额 ≈ 徽章 itemRewards 之和 + 额外部分（额外部分随任务类型/目标数变化）⚠。
（两个 mixId 在 game.dll `0x1FEAD00` 附近的奖励混合表区有命中，同区 locid 有 `REQUISITION`/`SUPER CREDITS`/`WARBOND MEDAL`。）

## 6. 三种任务线的字段差异（速查）

| 字段 | 解放（type 0）| 事件防守（type 4）| 城市分区（type 8）|
|---|---|---|---|
| `jointOperationId` | -1 | 事件 id | -1 |
| `missions[].type` | 1 | **3** | 1 |
| `Mission/Start.regionIndex` | -1 | -1 | **≥0** |
| `Mission/end.regionIndex` | 无 | 无 | **有** |
| `Mission/end.planetEventId` | 无 | **有** | 无 |
| `Mission/end.healthAtStartPlanetEvent` | 无 | **有** | 无 |
| 目标任务数 | 1（本号段）| 1–8 | 8 |
| 奖励量级（difficulty 8）| XP 267 / 货币 1,038 | XP 258–903 / 货币 1,002–4,602 | XP 936 / 货币 4,434 |
| `impact` 落点 | 行星 | 事件 | 分区 |

## 7. 伪造防守 vs 真防守（同 build、同难度 8）

| 字段 | 伪造 156 | 真防守 207 |
|---|---|---|
| Create 形状 | `opSettings 538077316 / jointOp 9101 / type 4 / 3×type3` | `opSettings 538077316 / jointOp 5730 / type 4 / 3×type3`（**完全同构**）|
| 服务器接受 | ✓ `{"operations":[{"id":1237}]}` | ✓ id 1243 |
| 任务目标 | **1 个：ERADICATE AUTOMATON FORCES**（普通清剿）| **8 个：EVACUATE PRIORITY CITIZENS + ESTABLISH COMMUNICATION UPLINK×2 + 侧目标** |
| XP / 影响力 / 货币 | 258 / 86 / 1,002 | 903 / 301 / 4,602 |
| `campaignWon` | true ✗ | false ✓ |
| `othersImpactPlanetEvent` | 1,880,999 ✗ | 1,844 ✓ |

⇒ 伪造防守**链路完全可用**（建作战→开局→打完→结算），但 ① 生成的是普通任务池任务、不是真防守任务；
② `campaignWon/othersImpact*` 不可用。**研究防守语义必须用真实事件样本。**

## 8. 仍未解（诚实清单）

1. `seed` / `placementNodeIndex` 的确切用途（两者都"每次随机"，不是 planetAttacks 下标）；
2. `operationSettingsId` 的键（随星球/任务池变、不随难度变；93 号跨天不同值 ⚠）；
3. `territoryIndex` 的映射（levelgen 地块 id，具体表未找到）；
4. `badges` 里 hash 型 id（`1449100876/1265652808/3071768642/3973473708/889185878/1748229498/1495751876`）的名字表
   （不在 26088801 的 strings 里；部分与 game.dll 目标表 `+0x54` 关联，见目标表文档）；
5. `rewards[].mixId` 到具体货币的映射；
6. `loadout` 两槽同值 hash 的编码；
7. `impact` 公式（难度 5→1、8→2；其它难度未知）；
8. `SetMaxRewards`（客户端在任务中发的 `{maxRewards,missionId}`）：本号段见过 14 / 8 / 4，规则 ⚠ 未解。

## 9. 证据文件（`D:\mod\out\gwe\`）

| 轮次 | Create | Start | end 请求 → 响应 | 前后 Status |
|---|---|---|---|---|
| 10-29 真防守 244 | `req_e856f9fa` | `req_7dd3bdcc` | `req_85e7f190` → `f766f01d` | `8945e8dc` |
| 11-01 解放 100 | `req_fd9a1ef7` / `req_644e1d2b` | `req_05e926f4` / `req_8cb7c8ab` | `req_69249892` → `15998437`；`req_c1fe2cca` → `e899f6af` | `9620e606` / `2afb0fec` |
| 11-01 伪造防守 156 | `req_419c21eb` | `req_585875be` | `req_be90471d` → `d0bdbe5b` | `23195938` / `4ff62a20` |
| 11-01 城市 207 | `req_607da437`(1242)、`req_2afeaeac`(1238) | `req_a72b7f59` | `req_fca34003` → `12b9a872` | `7a647a36` / `8d70d101` |
| 11-01 真防守 207 | `req_cdc8d894` | `req_f3f61671` | `req_4776dd8b` → `dd2350f7` | `7f6ae829` / `32fad0ba` |
| 11-01 真防守 207 的 3 次未打作战 | `req_f93da49f`(1239)、`req_08e6f70e`(1240)、`req_771b5373`(1241) | `req_60899f7b`(1240)、`req_52c2aa4d`(1241) | 只有 Abandon（`req_0029a1d9`/`req_eb3ef706`）| — |

## 10. 复现

```bash
# 抓包代理（只读落盘；防守实验时用 tools/start_defense_proxy.ps1 切 rewrite）
#   HD2_GWE_DUMP=D:\mod\out\gwe
#   HD2_GWE_PATHS=/api/WarSeason/801/Status,/api/Operation
#   HD2_GWE_REQ_PATHS=/api/Operation
# 目标表解码见 MISSION-OBJECTIVES-26251122.md §7；multipliers 数组见 §5.3 的 0x205C578。
```

证据等级：`warId/planetIndex/campaignId/race/difficulty/healthAtStart*/warTime/planetEventId/regionIndex/
operationId/missionId/missionSuccess/campaignWon/impact/othersImpact*/multipliers/objectives/badges(部分)/rewards(量级)` = ✓；
`seed/placementNodeIndex/territoryIndex/loadout/mixId/badges(hash 名)/SetMaxRewards` = ⚠。
