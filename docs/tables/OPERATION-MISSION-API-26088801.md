# Operation / Mission API 字段含义（build 26251122，2026-11-01 抓包 + 本地数据对表）

> 数据源：variant_mod MITM 代理（passthrough + `/api/Operation`、`/api/Mission` 白名单）在 20:34–20:54 抓的
> 两局真实请求/响应（`D:\mod\out\gwe\req_*` / `*_api_Operation*`）。
> 交叉源：`Status` 抓包（warId 801）、`refs/strings-en-26088801.json`、`out/planet/index-names-801.json`、
> `game.dll` 明文数据段（本 build）、wiki `Effects` / `Ship_Modules`。
> HD2Runtime 本地仓库里**没有**这些字段的文档（grep `jointOperation/operationSettingsId/territoryIndex/...` = 0 命中）。

## 0. 一句话

`Operation` 对象 = **客户端向服务器“认领/创建”的一次作战配置**；`Mission/Start` 只拿到 `missionId`；
`Mission/end` 的请求是**结算输入**、响应是**结算结果**（经验/徽章/影响力/奖励）。
任务级 modifier 不在这些字段里（另见 `OPERATION-MODIFIERS-26088801.md`）。

## 1. 字段总表（✓ = 有本地交叉证据；⚠ = 推断/未解）

### 1.1 `GET /api/Operation` → `operations[]`（本局实测）

| 字段 | 本局值 | 含义 | 证据 |
|---|---:|---|---|
| `id` / `nextOperationId` | 1236 / 1236 | 作战 id（服务器分配，Create 时客户端先猜 id=1236 再被确认）| ✓ 与 Create 请求 id 一致 |
| `seed` | 260054901 | 作战随机种子（大概率决定 mission 布局/额外随机内容）| ⚠ 用途未证 |
| `warId` | 801 | 当前大战 id | ✓ 与 Status.warId 一致 |
| `planetIndex` | 100 | 星球索引 | ✓ `index-names-801` → **TRANDOR**（terminid 解放战）|
| `placementNodeIndex` | 12 | 作战在“战况图”上的放置节点 | ⚠ 不是 `planetAttacks` 下标（173→100 的边在 index 24）|
| `campaignId` | 51692 | 战役 id | ✓ 与 `Status.campaigns[planetIndex=100].id` 一致 |
| `jointOperationId` | -1 | 联合行动 id；**-1 = 无** | ✓ 之前的防守样本里非 -1（244 号星球 5729）|
| `isActive` | true | 作战是否进行中 | ✓ Close 逻辑推断 |
| `type` | 0 | **战役类型**：0=解放（LIBERATION）| ✓ 与 `Status.campaigns[].type=0` 一致 |
| `difficulty` | 8 | 难度（1–10 枚举，8 = Impossible）| ✓ 与 wiki 难度表 + 选难度 8 吻合 |
| `race` | 2 | 敌人阵营（RaceType：2=terminid）| ✓ 与 presence/planet owner 同枚举 |
| `missions[]` | 3 个 | 作战内任务槽：`{index,type,state,missionId?,participants?}` | ✓ 两次快照对比 |
| `missions[].type` | 1 | 任务类型枚举（⚠ 具体枚举名离线不可读）| ⚠ |
| `missions[].state` | 1 / 3 | **1=未开打、3=已完成**（完成后带 missionId+participants）| ✓ 打前/打后对比 |
| `rewards[]` | [] | 作战奖励（结算后由 Mission/end 返回）| ✓ |
| `operationSettingsId` | 2350081063 | 服务器下发的“作战设置 token” | ⚠ 在 game.dll 0x2CB61D0 有一个同值记录（PEACEKEEPING OPERATION…），但 12.25M 个 u32 中命中 1 个，**不能排除巧合** |

### 1.2 `POST /api/Operation/Mission/Start`

| 字段 | 本局值 | 含义 | 证据 |
|---|---:|---|---|
| `planetIndex` / `warId` | 100 / 801 | 同上 | ✓ |
| `regionIndex` | -1 | 城市分区索引；**-1 = 非城市作战** | ✓ `Status.planetRegions` 只有城市星球（regionIndex≥0）|
| `operationId` | 1236 | 作战 id | ✓ |
| `missionIndex` | 2 | 第几个任务槽（对应 operations.missions[].index）| ✓ |
| `territoryIndex` | 338 | 城市战役“地块”索引 | ⚠ 只在城市战役有意义（本局非城市仍带值）|
| `participants[]` | 1 个 | 玩家平台 id 列表 | ✓ |
| → 响应 `{missionId: uuid}` | 768f72c6-… | 本局任务唯一 id，后续 end 请求/操作状态都引用它 | ✓ |

### 1.3 `POST /api/Operation/Mission/end`（请求 = 结算输入）

| 字段 | 本局值 | 含义 | 证据 |
|---|---:|---|---|
| `warSeasonId` | 801 | 同 warId | ✓ |
| `type` | 1 | **任务类型**（与 missions[].type 同值域）| ✓ |
| `difficultyType` | 8 | 难度（与 operation.difficulty 同值）| ✓ |
| `isOperationOwner` | true | 是否作战房主（结算归属）| ✓ |
| `planetIndex` | 100 | 星球 | ✓ |
| `warTime` | 85596780 | 服务器战争时钟（秒）| ✓ 与 Status.time 同量级 |
| `race` | 2 | 敌人阵营 | ✓ |
| `healthAtStartPlanet` | 1900000 | 开打时星球血量 | ✓ 与 `Status.planetStatus[100].health`=1900000 完全一致 |
| `healthAtStartPlanetEvent` | （解放战无此键） | 防守战/星球事件血量 | ✓ 2026-10-29 防守样本有 |
| `planetEventId` | （解放战无此键） | 星球事件 id（防守战）| ✓ 同上（244 号样本 5729）|
| `campaignId` | 51692 | 战役 id | ✓ |
| `operationId` / `missionIndex` / `missionId` | 1236 / 2 / uuid | 同上 | ✓ |
| `territoryIndex` | 338 | 城市地块 | ⚠ |
| `campaignWonAtStart` | false | 开打时战役是否已胜 | ✓ 语义直观 |
| `missionSuccess` | true | 任务是否成功 | ✓ 与后续 impact>0 一致 |
| `objectives[]` | `{id:2621213607, succeeded:true}` | 任务目标列表；`id` 为 32 位目标 hash | ⚠ id 在 game.dll 0x1FBFE08 处命中（周围是 ~58 个 hash 的**目标定义表**，名称不可解）|
| `badges[]` | 6 条 `{id32,amount}` | 结算徽章/贡献条目；`id32` 是**本地化 id 或目标 hash** | ✓ 4184186012=`Helldiver Replacements`、1624799956=`Successful Extraction`（strings 直接命中）；3071768642 在 game.dll 0x2CA7164 命中（0x2CA7000 起 stride 0xA0 的**地图目标表**：RECOVER SCIENTIFIC SPECIMENS / BUG HORDE / EXTERMINATE TERMINIDS / SEAL BUG HOLES / ACTIVATE TCS+ STATION，id32 位于记录 +0x20）⚠ |
| `participants[]` | `{extracted, loadout[2979303494,2979303494], lootedItems[], platformAccountId, progressedPackages[{id32:277818845,factor:1}]}` | 玩家结算数据：`extracted`=是否撤离成功；`loadout`=带上天的战略配备 id（2 个同值 ⚠ 疑似同一装备的两槽）；`progressedPackages`=推进的进度包（factor 倍率）| ⚠ loadout id 语义未解（在 strings/数据表/ game.dll 均未命中）|
| `heavyLootedItems[]` | [] | 重物拾取（如 SSSD 硬盘等）| ✓ 语义直观 |

### 1.4 `POST /api/Operation/Mission/end` 响应（结算结果）

| 字段 | 本局值 | 含义 | 证据 |
|---|---:|---|---|
| `operationId/missionIndex/missionId` | 1236/2/uuid | 回执 | ✓ |
| `experience` | 267 | 本局获得经验 | ✓ 语义直观 |
| `multipliers[]` | `{id32:851354768,factor:3,influenceFactor:3}`, `{id32:540020798,factor:1,influenceFactor:1}` | 经验/影响力倍率（两条：factor 3 与 1）| ⚠ id32 未解：851354768 在 game.dll 0x205C594 的 hash 表里命中（周围是 `{hash,1}` 记录，疑似“倍率定义表”）；**推测** 3× 是难度倍率、1× 是基础/无加成 |
| `badges[]` | 6 条，含 `influence`、`itemRewards[{mixId,amount}]` | 每条徽章的**影响力贡献**与物品奖励；本局 influence 合计 89（49+20+20）| ✓ 与 wiki 的“影响力”概念一致 |
| `campaignWon` | false | 本局后战役是否被拿下 | ✓ |
| `impact` | 2 | 本局对星球的**战役进度贡献** | ✓ 语义来自 wiki；具体公式 ⚠ |
| `othersImpactPlanet/CommunityTarget/PlanetEvent` | 0/0/0 | 队友/社区目标/星球事件侧的影响（多人时非 0）| ⚠ |
| `progressionPackageUpdates[]` | `{platformAccountId,id32:277818845,level:3,progress:65}` | 玩家等级进度：id32=进度包，level=3，progress=65/100 | ✓ 与 experience 对应 |
| `lootedItemRewards[] / lootedHeavyItemRewards[]` | [] | 拾取掉落物奖励回执 | ✓ |
| `rewards[]` | `[{mixId:897894480,amount:7},{mixId:3608481516,amount:1038}]` | 奖励货币/样本（mixId=奖励混合体 hash）| ⚠ mixId 命名空间未解：两者在 game.dll 0x1FEAD00 附近的 **奖励混合表**里命中，同区 locid 有 `REQUISITION`/`SUPER CREDITS`/`WARBOND MEDAL`；**推测** 3608481516=军票/征用点类、897894480=样本/奖章类 |
| `levelUpRewards[]` | [] | 升级奖励 | ✓ |
| `repeatingPlayer[]` | [] | 重复玩家（连战奖励）| ⚠ |

## 2. 防御战 vs 解放战的字段差异（✓ 2026-10-29 防守样本对照）

| 字段 | 解放战（本局）| 防守战（244 号样本）|
|---|---|---|
| `campaignId` | 有 | 有 |
| `planetEventId` | — | **有**（5729）|
| `healthAtStartPlanetEvent` | — | **有**（1883848）|
| `jointOperationId` | -1 | **非 -1**（5729）|
| `campaignWonAtStart` | 有 | 有 |

## 3. 仍未解的字段（诚实清单）

1. `seed` / `placementNodeIndex` 的用途（不是 planetAttacks 下标，24≠12）；
2. `multipliers[].id32`、`badges[].id32` 里那几个不在 strings 的 hash 的**名字表**（game.dll 里只找到 hash，没找到名字 locid）；
3. `rewards[].mixId` 到具体货币/样本的映射；
4. `objectives[].id` 的目标名（game.dll 0x1FBFE00 附近有 ~58 个 hash 的目标表，但记录里没有 locid）；
5. `loadout` 里的战略配备 id 是谁（2979303494 全库未命中，可能是**装备组合 hash**而非单个战备）；
6. `impact` / `influence` 的精确公式（需要抓多局不同难度/人数对照）。

## 4. 复现

```bash
# 抓包（已完成）：响应白名单 /api/Operation,/api/Mission；请求体 /api/Operation
D:\mod\work\variant-net\run_capture.ps1 -Paths "/api/WarSeason/GalacticWarEffects,/Status,/api/Operation,/api/Mission"
# 字段对表（只读）
python - <<'PY'  # 见本文件 §1 的 id → strings/game.dll 检查逻辑
PY
```

证据等级：`warId/planetIndex/campaignId/race/difficulty/healthAtStartPlanet/missionId/state/missionSuccess/campaignWon/impact` = ✓；
`multipliers/badges(部分)/mixId/objectives/loadout/seed/placementNodeIndex/territoryIndex` = ⚠。
