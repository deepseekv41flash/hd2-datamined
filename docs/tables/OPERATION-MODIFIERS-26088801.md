# Operation Modifiers（任务级修饰符）：不在 API，硬编码在 `game.dll` —— build 26088801/26251122

> 目标：wiki 有 [Operation Modifiers](https://helldivers.wiki.gg/wiki/Effects#Operation_Modifiers) 条目
> （General / Faction-Specific / Removed），想确认「任务级 modifier 字段」是否由服务器下发、能否像
> GWE type94 / presence 一样用 MITM 注入。
> 结论先说：**服务器 API 不下发任务级 modifier；客户端 `data/game/game.dll` 里有一张硬编码表（13 条）**。
> 证据与 13 条全表见下。

---

## 0. 为什么这次能读（与旧结论「game.dll 解不了」的关系）

旧结论（build 25480438 时代，见 `docs/cases/CASE-STUDY-20261021.md` 与记忆库 `game_dll`）说的是**整份文件加壳**：
段名被抹成 8 个空格，出现 `.vm_sec` / `.winlice` / `.boot` 等段，**所有段的熵都 ≈8.0**，代码/数据都不可读，
要拿 RVA/符号只能在游戏运行时做进程内内存 dump。

现在装了新 build（25988413 → 26088801/26251122，`game.dll` 15.5 MB → **49 MB**），引擎重建后段表恢复正常。
实机对比（`pefile` 读段表 + 每段熵，脚本只读）：

| 版本 | 段名 | 关键段熵 | 可读性 |
|---|---|---|---|
| **旧 build 25480438**（`D:\Helldivers 2_25480438_backup\data\game\game.dll`，15.5 MB） | 全被抹成空格 + `.vm_sec/.winlice/.boot` | 所有段 7.99–8.00 | **整份不可读** |
| **当前 build**（`...\Helldivers 2\data\game\game.dll`，49 MB） | `.text / .rdata / .data / .pdata / _RDATA / .rsrc / .reloc` | **`.text` = 8.0000**（代码仍加密）；**`.data` = 6.4258**；`.rdata` = 7.6659 | **数据段可读、代码段仍不可读** |

本次用到的两个偏移落在数据段：
`0x2CA0168`（13 条 Operation Modifier 表）在 **`.data`**（`+0x7ECB68`）；
`0x1FE95B8`（Title Case 名数组）在 **`.rdata`**（`+0x511B8`）。

所以这次**没有解任何密**：只是①在文件里搜 locid 的 u32 字节 → 得到文件偏移；②用 `pefile` 把偏移映射到
段/VA；③按 0x50 步长把记录读出来；④locid→文案用本地 `.strings` 导出（`refs/strings-en-26088801.json`）。
**只读了数据，没碰代码**。

> ⚠ 连带修正：因为 `.text` 仍是熵 8.0 的加密段，§4 里 "capstone xref 0 命中" **不能**作为"没有引用"的证据
> ——那段字节不是可执行的明文机器码，扫出来的东西没有意义。要追选择逻辑，仍然得走**运行时内存 dump**
> （旧路线）或等代码段解密；数据表本身的可读性不受影响。

---

## 1. 网络侧：抓包证明「没有 modifier 字段」（✓ 抓包）

抓包方式：`variant_mod` MITM 代理（`passthrough=True`，不改写）把响应白名单扩到
`/api/Operation`、`/api/Mission`，请求体白名单 `/api/Operation`；用户 20:34–20:54 实际打了两局。
原始 body：`D:\mod\out\gwe\`（`index.txt` 有 `20261101T1234*` 起的 GET/POST 记录）。

| 端点 | 响应体大小 | 实际字段（全文） | 有 modifier 吗 |
|---|---:|---|---|
| `GET /api/Operation` | 558 B | `nextOperationId` + `operations[]`：`id, seed, warId, planetIndex, placementNodeIndex, campaignId, jointOperationId, isActive, type, difficulty, race, missions[{index,type,state,missionId,participants}], rewards, operationSettingsId` | **✗ 没有** |
| `POST /api/Operation/Create` | 60 B | `{operations:[{id, rewards:[], backupRewards:[]}]}` | **✗ 没有** |
| `POST /api/Operation/Mission/Start` | 52 B | `{missionId: uuid}` | **✗ 没有** |
| `POST /api/Operation/Mission/end` | 560/1244 B | `operationId, missionIndex, missionId, experience, multipliers[{id32,factor,influenceFactor}], badges[], campaignWon, impact, progressionPackageUpdates[], rewards[], …` | **✗ 没有**（`multipliers` 是徽章/经验倍率，不是 modifier） |

⇒ 任务级 modifier 不是服务器字段；`multipliers.id32` 里 `851354768 / 540020798` 等也不是 modifier
（`54…` 等与 GWE type59 的 value 同名空间，属「奖励倍率」一类）。

## 2. 本地：`game.dll` 里的硬编码表（✓ 离线，结构 ⚠ 部分字段未证）

文件：`D:\SteamLibrary\steamapps\common\Helldivers 2\data\game\game.dll`
（47 MB，build 10-29；文件偏移 **0x2CA0168**，**13 条 × 0x50 B**）

每条 0x50 B 的布局（小端）：

| 偏移 | 含义（⚠ 推断） |
|---:|---|
| `+0x00` | **显示名 locid（UPPER 全大写）** → `refs/strings-en-26088801.json` 可解出文案 |
| `+0x04` | **描述 locid**（含 `<i=1>…</i>` 富文本与 `#V_ONE` 参数位） |
| `+0x08` | u32（多数为常量 `0x2F9AB700`；Leviathan 那条不同 `0x01170B37`） |
| `+0x0C` | u32（多数为常量 `0x81B917E0`；同上不同）⇒ 疑似 8 B 类型/类别 hash |
| `+0x10` | u32（13 条里取值 0/19/20/21/23/24/25/26）⇒ 疑似枚举/效果索引 ⚠ |
| `+0x14` | u32（全 0） |
| `+0x18` | u32 hash（每条不同）⇒ 疑似效果/定义 id ⚠ |
| `+0x1C` | u32（0/1/2/500） |
| `+0x20` | u32（0/1） |
| `+0x24` | u32 hash（部分条目相同，如 `0x1425C5FF` 三条） |
| `+0x28` | f32（0 / 1 / 1.25 / 1.5 / 15 …）⇒ 疑似权重或倍率 ⚠ |
| `+0x2C..+0x4F` | 0（CIVILIANS & SEAF 那条在 +0x30 后还有额外 hash 列表） |

**13 条全表**（`name`/`desc` 均为官方英文本地化）：

| # | 名称（UPPER） | 描述 | `+0x10` | `+0x18` | `+0x1C` | `+0x24` | `+0x28` f32 |
|---:|---|---|---:|---|---:|---|---:|
| 0 | **POOR INTEL** | `<i=1>Objective locations</i> are hidden.` | 23 | `DA18D5EF` | 1 | `8A8C0DAA` | 1.5 |
| 1 | **COMPLEX STRATAGEM PLOTTING** | `Stratagem <i=1>Call-in time</i> increased by <i=1>#V_ONE%</i>.` | 19 | `CE7EF33A` | 1 | `4EFD758F` | 1.25 |
| 2 | **ORBITAL FLUCTUATIONS** | `Stratagem <i=1>cooldown</i> increased by <i=1>#V_ONE%</i>.` | 20 | `1101E25C` | 1 | `E3B9B860` | 0 |
| 3 | **ATMOSPHERIC SPORES** | `<i=1>Map obscured</i> by Bug Spores.` | 24 | `8EA68AE6` | 500 | `A8B06BF1` | 15 |
| 4 | **ATMOSPHERIC INTERFERENCE** | `Orbital Stratagems <i=1>Scatter Increased</i>.` | 21 | `6DA4A636` | 1 | `023B19E0` | 0 |
| 5 | **SPORE CLOUD POCKETS** | `Tactical Map <i=1>Disrupted</i>` | 25 | `84AAD4E6` | 1 | `1425C5FF` | 0 |
| 6 | **ROVING SHRIEKERS** | `Flying Shrieker swarms traverse the battlefield.` | 0 | `A0687641` | 500 | `320BB8CC` | 1 |
| 7 | **AA DEFENSES** | `<i=1>Stratagem slots</i> reduced by <i=1>#V_ONE</i>.` | 26 | `F6F1B0C7` | 1 | `1425C5FF` | 0 |
| 8 | **GUNSHIP PATROLS** | `Flying Gunships patrol the battlefield.` | 0 | `A92F094F` | 2 | `1425C5FF` | 0 |
| 9 | **LEVIATHAN BLOCKADE** | `Flying Leviathan warships patrol the battlefield.` | 0 | `1D90EA70` | 0 | `EE372DD1` | 0 |
| 10 | **SEAF UNITS IN AREA** | `Allied SEAF units are operating on the battlefield.` | 0 | `5B2923A7` | 0 | `0DB41104` | 0 |
| 11 | **CIVILIANS IN AREA** | `Caution: loyal civilians are on the battlefield.` | 0 | `0724AB37` | 0 | `63CCFA89` | 0 |
| 12 | **CIVILIANS & SEAF IN AREA** | `SEAF units and loyal civilians are both on the battlefield.` | 0 | `00000001` | 1 | `959BE149` | — |

### 2.1 与 wiki 的差异（✓ 值得注意）

- wiki 的 General/Faction 列表里 **没有** `SPORE CLOUD POCKETS`、`SEAF UNITS IN AREA`、
  `CIVILIANS IN AREA`、`CIVILIANS & SEAF IN AREA` —— 客户端表里**多 4 条**（其中后两条可能是
  同一事件的两个版本；`CIVILIANS & SEAF IN AREA` 正是 wiki 里 "Civilians and SEAF in Area" 的全名）。
- wiki 的 Removed 列表里 **`ELECTRONIC COUNTERMEASURES` 不在主表里**：它的 Title Case 名
  （locid `3942793355`）出现在 `game.dll` 另一处（文件偏移 `0x1FE95B8`，与 Complex/Orbital/
  Atmospheric Interference/Poor Intel/Atmospheric Spores 的 Title Case 名同簇）⇒ 存在一张**二次数组**
  （⚠ 结构未解），疑似旧版/已移除 modifier 的残留。
- `ATMOSPHERIC INTERFERENCE`、`AA DEFENSES`（wiki 标 Removed）**仍在主表**里 ⇒ 引擎仍认得，
  只是服务器不一定再抽到。

## 3. 为什么 MITM 注入不了（(✗) 这条路）

- 响应里没有字段可改（§1）；`Operation` 对象只有 `seed/difficulty/race/...`；
- 客户端渲染「行动变量/Operation Modifiers」时读的是 **本地 game.dll 表 + 难度/阵营/seed 逻辑**，
  不是 Status / Operation 字段；
- 所以和 type94/presence 不同，**没有「往响应里塞 id」的入口**。要改只能走「改 game.dll / 内存」路线
  （属于代码路线，不是数据表/MITM 路线；有 EAC 风险，未做）。

## 4. 下一步（未做，供决策）

1. **找选择逻辑**：对 0x2CA0168 做 xref/反汇编 —— ⚠ **当前不可行**：`.text` 段熵 8.0000（加密），
   capstone 扫出的 "0 命中" 无意义（见 §0 修正）。可行路径仍是运行时内存 dump 后反汇编，或等代码段解密；
2. **实机对照**：记录「同一操作、不同难度」下屏幕上出现的 modifier，与 13 条表/`seed` 对表，
   反推选择算法（不需要改任何文件，只需要看 + 记录）；
3. **参数语义**：`#V_ONE`（50/25/1）与 `+0x10/+0x28` 的对应关系，需要用 xref 找到读字段的代码。

## 5. 复现

```bash
# 1) 抓包（响应白名单扩到 Operation/Mission）
D:\mod\work\variant-net\run_capture.ps1 -Paths "/api/WarSeason/GalacticWarEffects,/Status,/api/Operation,/api/Mission"
# 2) 从 game.dll 提取 13 条 Operation Modifiers（只读；-csv/-json 可落盘）
python tools/opmod_scan.py --csv out/opmod.csv --json out/opmod.json
```

证据等级：网络侧「无字段」= ✓ 抓包（响应全文已落盘）；本地表存在/13 条/名称描述 = ✓ 离线；
字段语义（+0x08/+0x10/+0x18/+0x28）= ⚠ 推断；选择逻辑 = ⚠ 未做。
