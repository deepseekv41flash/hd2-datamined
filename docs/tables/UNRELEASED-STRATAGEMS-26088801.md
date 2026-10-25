# 未发布战备候选名单（build 26088801 · 额外战备路线）

> **一句话**：本 build 的战备表 **153 行**里，**85 行**是常规已发布、**41 行**是任务/子项、**2 行**自带
> `(NOT USED)` 标记、**9 行**是载具、剩下一小撮是**事件/彩蛋/未开放**。能当「额外战备」带进任务且
> **已经实机验证可用**的是 **M-104 Incinerator FRV（id 138）**；本页把剩下值得试的挑出来排好序。
>
> 机制与配方：[RECON-SHODAN-EXTRA-STRATAGEM](../cases/RECON-SHODAN-EXTRA-STRATAGEM-26088801.md)（`+0xC8`，不占配装位、跟链、成环崩）

## 1 判据（三条，全部可离线复核）

| # | 判据 | 数据位置 |
|---|---|---|
| A | **内部名**直接从行里读：`+0x10`/`+0x14` 是组内字符串指针；名字里带 `(NOT USED)` = 原版自己标记未使用 | 行 `+0x10/+0x14` |
| B | **分类前缀**：`MISSIONS.*` / `MISSIONS CLAN STATION.*` / `[TUTORIAL]` / `TANK.*` / `SEAF Squad` = 任务脚本或子项，默认不进配装 | 内部名 |
| C | **能不能当呼叫用**（结构判据）：`+0x50` 使用次数、`+0x68` 冷却、`+0x3C` 投放方式、`+0x98/+0xA0` 载荷实体数组 | 行字段 |

统计（153 行）：

| 类别 | 行数 |
|---|---:|
| 已发布常规战备（含支援武器/背包/哨戒/轨道/飞鹰/载具已发售款） | **85** |
| 任务脚本 / 子项（判据 B） | **41** |
| 载具（VEHICLES.，其中 M-104 未发布） | **9** |
| 原版标记 `(NOT USED)` | **2** |
| 事件 / 彩蛋 / 未开放（非任务、无 wiki 页、结构像呼叫） | 若干（见 T1） |

## 2 T1 · 最值得试的候选（未发布 / 未使用 / 彩蛋）

| id | 内部名 | 显示名 | 使用次数 | 冷却 | 投放 | 载荷实体 | 备注 |
|---:|---|---|---:|---:|---:|---|---|
| **138** | `VEHICLES. FAST RECON VEHICLE (Ramming Flamethrower)` | 炽灼型快速侦察载具 | ∞ | 480 s | 3 | `2d85bfe3d8717fe5`（`frv_flamer`）+ shuttle | **✓ 实机：能带能叫**（本名单唯一已验证） |
| **36** | `EAGLE. (NOT USED) ADDITIONAL STRAFING RUNS` | （无名，**借 Eagle Strafing Run 的图标**） | 3 | 15 s | 0 | `23a60681dd4383ec` | **✓ 实机：能带能叫、效果 = Eagle Strafing Run；只有 4 次、用完不可用，Eagle Rearm 补不了它** |
| **150** | `EAGLE. (NOT USED) AIR-TO-AIR MISSLES` | Eagle Air-to-Air Missiles | 2 | 15 s | 0 | `dfbb9a0d8fa27d85` | **✓ 实机：有名字有图标、能用**；⚠ **会锁地面目标**（目标筛选未完成）|
| **64** | `ORBITAL. WALKING BARRAGE SMOKE` | Orbital Walking Barrage Smoke | ∞ | 120 s | 5 | `08d58cb1bf65f7a9` | **✓ 实机：有名字有图标、能用**（行走弹幕的烟雾版）|
| **145** | `ORBITAL CONFETTI` | Orbital Confetti | ∞ | 80 s | 1 | `aedc4a073fb4b925` | **✓ 实机：有名字有图标、能用**（纸屑轨道打击彩蛋）|
| **50** | `EAGLE FLY BY` | Eagle Fly By | 5 | 15 s | 0 | `2a275bb78bb20148` | 过场用（飞鹰掠过），多半只是演出；**⚠ 未测** |
| **119** | `SEAF Squad` | （无名） | ∞ | 120 s | 6 | `75f7e96af7dcd303` + `3ec790806d0b0540` | 投放类型 6（与载具/常规不同）；**✓ 实机：能带、能叫，但运输机投下空无一物** ⇒ 半成品行（有呼叫流程、无载荷生成） |

> 说明：`+0x3C` 投放方式：0=飞鹰空投、1=轨道、2=投掷/空投、3=载具空投、4=信标、5=行走弹幕、6=？（SEAF Squad 独有）。

### 2.1 ✓ 已验证可用（2026-10-25 一天内全部实机）

| id | 名字 | 实测现象 |
|---:|---|---|
| 138 | Incinerator FRV | 车辆正常投放、能开 |
| 36 | （无名）额外扫射 | 图标借 Eagle Strafing Run、效果同它；**只有 4 次充能**、Rearm 不补 |
| 150 | Eagle Air-to-Air Missiles | 有名字有图标、能打；⚠ **会锁地面目标**（目标筛选未完成） |
| 64 | Orbital Walking Barrage Smoke | 有名字有图标、能打（烟幕行走弹幕） |
| 145 | Orbital Confetti | 有名字有图标、能打（纸屑彩蛋） |

结论：**未发布战备的图标/名字大多在包里**（只有 36 / 119 这种真没 locid 的回退到占位或同族图标）；
所以「额外战备」是**把未发布内容带进正式任务**的稳定入口。

## 3 T2 · 任务 / 子项行（能带，但基本没意义；个别可能有惊喜）

| 组 | id |
|---|---|
| 任务物件（空投舱/钻机/旗帜/终端…） | 5, 7, 11, 17, 19, 29, 30, 37, 41, 43, 49, 67, 73, 74, 75, 79, 81, 82, 87, 88, 89, 97, 101, 105, 111, 114, 125, 126, 127, 131, 132, 135, 141, 149, 152 |
| 坦克换弹子项（无载荷、6 s 冷却） | 48, 98, 62 |
| 特殊 | 106（CLAN STATION 地毯轰炸）、50（Eagle Fly By）、145（Confetti） |

⚠ 任务行里 `MISSIONS. REINFORCEMENT BEACON`(127)、`MISSIONS CLAN STATION. Nuke`(135)、
`MISSIONS CLAN STATION. Carpet Bombing Run`(106) 这几条**结构上就是"叫东西下来"**，理论上可试；
但任务物件往往依赖任务状态（终端、目标点），带进普通任务可能无反应或报错。

## 4 T3 · 已发布（85 行，仅作对照）

支援武器 / 背包 / 哨戒 / 轨道 / 飞鹰 / 已发售载具（M-102 Gunner FRV、M-103 Supply FRV、EXO 四款、TD-220/TD-110）。
判定方式：内部名是常规分类 + 有 locid 名字 + 军械库能看到。

## 5 怎么测（一次带 3 件）

`tools/stratagem_extra.py --chain` 一次挂整条链（`HOST:A,B,C` = HOST 送 A、A 送 B、B 送 C）：

```bash
# 例：带 Resupply 就同时来 36 / 150 / 64
python tools/stratagem_extra.py --chain 34:36,150,64 --out out/stratagem-extra/t1a.plain --seal
python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin     --sealed out/stratagem-extra/t1a.dl_bin
```

判读：

| 看到 | 结论 |
|---|---|
| 图标出现 + 能按呼叫码 + 掉下来预期的东西 | **可用**，记进 "可带未发布战备" 名单 |
| 图标出现但叫不动 | 行在表里、引擎侧没生成逻辑（半成品行） |
| 图标出现、能叫、**运输机投下空的** | 呼叫流程完整、**载荷没生成**（119 就是这个：结构像、资源/生成逻辑缺）|
| 能叫、效果正常，但**Eagle 只有 4 次且 Rearm 补不上** | Eagle 类额外战备只吃**共享充能池**；Rearm 的补弹目标不含「额外」条目（36 实测）|
| 完全没图标 | 该行被过滤（多半缺 locid 或投放类型没人处理） |
| 任务开始崩溃 | 该行缺运行时前置；一次只链一条再定位 |

⚠ 链路上会**覆盖**中间行原有的 `+0xC8`（Eagle 的 51 会被改掉）——测试完记得回到原版或重挂。

## 5.1 Eagle 类额外战备的一个坑（id 36 实测）

- 额外带来的 Eagle 条目**吃共享的 4 次充能**（不是它自己 `+0x50` 的 3 次）；
- **Eagle Rearm 补不到它** —— 说明 Rearm 的"装填目标"不是"表里所有 Eagle 行"，
  而是与**配装里被选中的条目**（或另一组字段）绑定；额外条目不在补弹名单里。

⇒ 想要"无限用的未发布 Eagle"，光靠 `+0xC8` 不够，得再看 Rearm 的目标集合怎么定。

## 5.2 给开发者的「成品配方」（照抄即可做出一份可用 mod，不需要我们打包）

目标：让玩家带着熟悉的战备进任务时，**额外**拿到未发布战备（不占 4 个自选位）。

**第一步：查 id**

```bash
python tools/stratagem_extra.py --show          # 153 行：id / 名字 / 当前额外战备
python tools/stratagem_extra.py --find FRV      # 按名字找 id（108 / 26 / 138）
```

**第二步：选形态**

| 形态 | 命令 | 效果 |
|---|---|---|
| 单挂 | `--host 34 --extra 138` | 带 Resupply → 多一件 M-104 |
| 链式（一件带一串） | `--chain 34:138,36,150` | 带 Resupply → M-104 → 额外扫射 → A2A 导弹（4 件） |
| 4+4 成品 | 见下方 | 4 个自选位各带 1 条未发布 |

**第三步：4+4 成品示例**（假设自选：Resupply / 轨道精准 / 哨戒机枪 / 飞鹰空袭）

```bash
# 每条宿主只挂 1 条目标（不串链，避免互相覆盖）——四次调用，同一份明文上累加
python tools/stratagem_extra.py --host 34  --extra 138 --out out/p1.plain          # Resupply → M-104
python tools/stratagem_extra.py --plain out/p1.plain --host 121 --extra 64 --out out/p2.plain   # 精准 → 烟幕行走弹幕
python tools/stratagem_extra.py --plain out/p2.plain --host 124 --extra 150 --out out/p3.plain  # 哨戒 → A2A 导弹
python tools/stratagem_extra.py --plain out/p3.plain --host 18  --extra 145 --out out/p4.plain --seal
python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin     --sealed out/p4.dl_bin
```

（`--plain <上一步产物>` 是链式追加的正确写法；每次都会重新解一个校正字、哈希回到原版锚点。）

**第四步：进游戏验收**

| 看什么 | 通过标准 |
|---|---|
| 战备条数量 | 4 + 额外（本页实测 6 正常；8 未测） |
| 图标 / 名字 | 未发布战备多数**自带**图标与名字；没有的回退成同族图标或占位虚框 |
| 叫出来 | 有实体/弹幕/车辆落地并生效（"空的" = 半成品，如 119） |

**第五步：回滚** —— `python tools/dlbin_deploy.py restore --file generated_stratagem_settings.dl_bin`

### 照做前必须知道的五条约束

1. **别造环**：引擎顺着 `+0xC8` 无限跟，成环在任务开始崩（`--chain` 已做重复检测，手改请自己查）。
2. **链会覆盖中间行原有的 `+0xC8`**：Eagle 全家原本 = 51（Rearm），串链会把它们改掉 —— 想做「4+4」请用上面**不串链**的写法。
3. **Eagle 类额外条目只有 4 次共享充能，且 Eagle Rearm 补不到它**（id 36 实测）。
4. **只改本机**：队友的战备表是他们的，看不到你的额外条目。
5. **哈希必须保持**：工具已内置（tail 宿主 + Murmur64A 复原）；手写脚本请沿用 `plain_edit.py` 的 tail 宿主流程，否则引擎校验失败。

## 6 三态

| 结论 | 态 |
|---|---|
| 153 行 = 85 已发布 + 41 任务/子项 + 9 载具 + 2 `NOT USED` + 少量彩蛋 | **✓ 离线**（内部名从行内字符串直接读） |
| M-104（138）可带可叫 | **✓ 实机**（2026-10-25） |
| 36 = 未使用的 Eagle 扫射，能带能叫、效果同 Strafing Run | **✓ 实机**（4 次充能；Rearm 不补） |
| 150 / 64 / 145 都能带、都能叫，且有名字有图标 | **✓ 实机**（三连链一次测完） |
| 150 会锁地面目标（空中目标筛选未完成） | **✓ 实机观察** |
| 119 SEAF Squad | **✓ 实机**：可带可叫，**空投为空**（占位图标；判定为半成品行） |
| 任务行带进普通任务会怎样 | **⚠ 未证**（依赖任务状态，预期大多无反应） |
