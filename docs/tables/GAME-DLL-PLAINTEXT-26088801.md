# `game.dll` 明文数据段里有什么（build 26251122，✓ 只读侦察）

> 背景：新 build 的 `game.dll` 段表恢复正常，`.text` 仍加密（熵 8.0000），但 `.rdata`（熵 7.6659）与
> `.data`（熵 6.4258）里的**静态数据是明文**。本文盘点这两段里「有价值 / 无价值」的内容，
> 方法 = **locid 字扫描 + 邻近聚类**（本地化字符串的 32 位 id 在数据段里成片出现），
> 工具：`tools/gamedll_data_survey.py`（数据簇）、`tools/opmod_scan.py`（Operation Modifiers）。
> 单条 Operation Modifiers 的结论见 [OPERATION-MODIFIERS-26088801](OPERATION-MODIFIERS-26088801.md)。

## 1. 扫描结果总览

`.rdata` + `.data` 里共 **13,067** 个「locid 字」，聚成 **60 个 ≥3 命中的数据簇**（73 个总簇）。
按内容归类如下（按对玩法/未发布内容的价值排序）：

| 价值 | 数据簇（文件偏移，段） | 规模 | 是什么 | 状态 |
|---|---|---|---|---|
| **高** | `0x2CB61D0` 起（`.data`） | 单条 ~0x100 B | **OperationSettings 定义**（抓包里的 `operationSettingsId` 之一 = `0x8C136427` = 2350081063），含 3 个 locid（PEACEKEEPING OPERATION + 2 段描述）与 ~20 组 `{u32 hash, f32 1.0}` 权重 | ⚠ 结构未证（下一项） |
| **高** | `0x208A440`（`.rdata`） | 143 locid 命中 | **舰船升级模块的名称/描述**：`ORDERS / PLATOON ORDERS / MAJOR ORDERS / AUTOMATED HELLPOD LOADING / PRE-FILLED HELLPODS / EXPANDED ARMORY / ENHANCED COOLING SYSTEM / EXPANDED CREW / IMPROVED GUIDANCE SENSORS …` | ⚠ 未跟本地 `generated_stratagem_upgrade_settings` 对表（可能是未发布模块的来源） |
| **中** | `0x2CA36B8`（`.data`） | 570 locid | 设置菜单文案（GAMEPLAY/DISPLAY/GRAPHICS/AUDIO/HUD/ACCESSIBILITY/…、按键提示） | 低游戏价值 |
| **中** | `0x2C9F630`（`.data`） | 219 locid | 设置项描述（Motion Sensor Sensitivity/Acceleration/…、Deadzone 等） | 低游戏价值 |
| **中** | `0x20AA41C / 0x208E410 / 0x20A5480 / 0x20BC430 / 0x20774D0 / 0x209C42C / 0x2085474 / 0x2097740 / 0x20AF414 / 0x20C5650 / 0x20B7950 / 0x2080820 / 0x207C47C / 0x2093434 / 0x20A1414 …`（`.rdata`，约 15 簇） | 每簇 230–465 locid | **Operation/战役类型定义族**：`OPERATION IMPACT`、`Completing this Operation contributes to …`、`#PERCENTAGE% HELD / LIBERATED`、`CITY OPERATION`、`MEGAFACTORY OPERATION`、`PEACEKEEPING OPERATION` | ⚠ 待解（结构与 `operationSettingsId`、难度、modifier 数量的关系） |
| 低 | `0x2060060 / 0x206E780`（`.rdata`） | 各 ~2,097 locid | **舰船命名用词表**（Adjudicator/Steward/Agent/Soul/Arbiter/Wings/Harbinger/Halo/Dawn/… + of Benevolence/of Courage/…） | 纯命名表 |
| 低 | `0x1FF1400`（`.rdata`） | 193 locid | 语音字幕（`{0.00->0.98}Package inbound…` 等） | 纯字幕 |
| 低 | 其余小簇 | 3–150 locid | 零散 UI 文案/提示 | — |

## 2. 两个高价值线索

### 2.1 OperationSettings 记录（`operationSettingsId` 在本地有定义）

抓包的 8 个 `operationSettingsId` 里 **只有 1 个能在本地命中**：

```
2350081063 = 0x8C136427  →  game.dll 文件偏移 0x2CB61D0（.data）
```

该记录前 ~0x30 B（小端）：

| 偏移 | 值 | 猜测 |
|---:|---|---|
| `+0x00` | `0x8C136427` | **operationSettingsId**（与 API 字段一致）|
| `+0x04` | `1` | ⚠ |
| `+0x08` | `2` | ⚠ 可能是 modifier 数量/单局数 |
| `+0x0C` | `1` | ⚠ |
| `+0x10` | `10` | ⚠（难度上限？）|
| `+0x14..+0x1C` | 0 | — |
| `+0x20` | `1.0f` | ⚠ |
| `+0x24` | locid `0x0CDF8AC5` = **PEACEKEEPING OPERATION** | 名称 |
| `+0x28` | locid `0x0D314823` = “Our enemies have forced co…” | 描述 |
| `+0x2C` | locid `0x0C5E0839` = “Tactically eliminate all o…” | 描述（第二条？）|
| `+0x30` 起 | ~20 组 `{u32 hash, f32 1.0}` | 权重/任务类型表（⚠ 未证）|

其余 7 个 id（`0x20126884 / 0x922F6304 / 0xA6B6B774 / 0xA7508E58 / 0xBE6CA1E1 / 0xE0791AF3 / 0xE6709132`）
**本地 0 命中** ⇒ 它们大概率是服务端侧定义（或客户端只在 Create 请求里原样回传、不做本地解析）。
> 备注：`0xA6B6B774` / `0xBE6CA1E1` 正是 2026-10-27 防守伪造实验里观察到的 `operationSettingsId` 变化值，
> 说明它确实是服务器下发的操作配置 token。

### 2.2 舰船升级模块的硬编码名/描述

`0x208A440` 簇里是一组「分组名 + 模块名 + 描述」：

```
ORDERS / PLATOON ORDERS / MAJOR ORDERS
AUTOMATED HELLPOD LOADING   – Reduces cooldown for Hellpod stratagems …
PRE-FILLED HELLPODS         – Reduces cooldown for Hellpod stratagems …
EXPANDED ARMORY             – Allows 1 additional use per mission …
ENHANCED COOLING SYSTEM     – Reduces cooldown for Strike stratagems …
EXPANDED CREW               – Reduces cooldown for Strike stratagems …
IMPROVED GUIDANCE SENSORS   – …
```

这些名称与本地 `generated_stratagem_upgrade_settings` 里的舰船模块同族；**值得做一次对表**：
**哪些模块名只出现在 game.dll、不在本 build 的模块表里**（= 未发布/预留模块，如之前社区清单里那些
"barrage spread reduced / +1 salvo" 条目）。

## 3. 结论

1. 明文数据段**没有**超出已解范围的“第二套玩法表”：玩法数值仍全在 `generated_*.dl_bin`（已有明文缓存）；
2. 额外能挖的只有三类硬编码静态定义：**OperationSettings / Operation 类型定义族**、**舰船升级模块名**、
   **Operation Modifiers**（已解出 13 条）；其余是 UI 文案、舰船命名词表、语音字幕；
3. 代码段（`.text`）仍加密 ⇒ 这些表**如何被选择/使用**依然拿不到（需运行时内存 dump）。

## 4. 下一步（建议）

1. **解码 OperationSettings 簇**：先定记录边界/步长（约 15 个 `.rdata` 簇 + `.data` 的 0x2CB61D0 记录），
   把 `operationSettingsId` ↔ 名称 ↔ 描述 ↔ `{hash,1.0}` 权重表连起来；若其中有“modifier 数量/池”字段，
   任务级 modifier 的选择逻辑就能从**数据侧**反推（不需要碰加密代码）；
2. **舰船模块对表**：game.dll 模块名 ↔ `generated_stratagem_upgrade_settings`，列未发布模块清单；
3. 收工：`stop.ps1` 停代理回纯转发。

## 5. 复现

```bash
python tools/gamedll_data_survey.py --json out/gamedll-clusters.json   # 数据簇摘要（locid 字扫描）
python tools/opmod_scan.py --csv out/opmod.csv --json out/opmod.json   # 13 条 Operation Modifiers
```

证据等级：数据簇/偏移/样例文案 = ✓ 离线（可复算）；簇身份猜测 = ⚠ 推断；
OperationSettings 字段语义 = ⚠ 未证；代码引用关系 = ✗ 不可读（`.text` 加密）。
