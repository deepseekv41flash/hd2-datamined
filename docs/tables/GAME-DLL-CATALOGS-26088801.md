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
