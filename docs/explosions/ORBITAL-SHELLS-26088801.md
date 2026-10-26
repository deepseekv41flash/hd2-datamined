# 轨道弹幕的"弹丸 → 爆炸"链，与"HE/EMS 交替"到底能不能做（build 26088801）

> 起因：社区工具里出现两条未发布候选 `轨道120mm HE/EMS火力网 [effect 1426]`、`轨道燃烧加特林 [effect 1427]`。
> 本文只记**可复算的事实**与**否证**，结论在三态里标出。

## 0 三态

| 标记 | 含义 |
|---|---|
| ✓ | 离线可复算（本 build 明文 + 社区元数据交叉） |
| ✗ | 已否证（写明证据）|
| ⚠ | 未验 |

## 1 社区元数据里那两件是什么（`✓` 阅读）

来源：`refs/helldiversdata/generated_projectile_settings.json`（246 行，社区 dump）+ `refs/hd2runtime-repo/research/`。

轨道弹丸家族的弹道参数（`calibre / mass / speed`）：

| 射弹 | cal | mass | speed | 命中爆炸 |
|---|---:|---:|---:|---|
| `Orbital_Cannon_120mm_HE` | 84 | 5000 | 400 | `OrbitalStrike` |
| `Orbital_Cannon_120mm_HE_Cheap` | 84 | 5000 | 400 | `OrbitalStrike_Cheap` |
| **`Orbital_Stunround`（EMS）** | **84** | **5000** | **400** | `OrbitalStun` |
| `Orbital_Stunround_Upgraded_MK2 / MK3` | 84 | 5000 | 400 | `OrbitalStun_MK2 / MK3` |
| `Orbital_Cannon_110mm` | 110 | 5000 | 400 | `OrbitalShot` |
| `Orbital_Cannon_380mm_HE` | 406 | 30000 | 400 | `OrbitalBarrage` |
| `Orbital_Cannon_Napalm` | 84 | 5000 | 400 | `Orbital_Napalm` |
| `Orbital_Gas`（+MK2/MK3） | 84 | 5000 | 400 | `OrbitalGas` |
| `Orbital_Smoke` | 84 | 5000 | 400 | `AirStrikeSmoke` |

⇒ **120mm HE 与 EMS 眩晕弹的弹道一模一样**（84 / 5000 / 400），只有命中爆炸不同。
"HE/EMS 火力网" = 同一门弹幕混打这两种**已存在**的弹丸，不需要新弹头数据。

## 2 本 build 里对应的行与爆炸 id（`✓`）

`ProjectileInfo` 272 B、355 行、行基址 **44**（`96604 - 44 = 355×272`）。
用社区 dump 的 **name hash**（行内 `+4/+8/+12`）对齐，命中：

| 射弹 | 行号 | `+0`=ProjectileType | `+0x90` 命中爆炸 | `+0x9C` 到期爆炸 |
|---|---:|---:|---:|---:|
| `Orbital_Cannon_120mm_HE` | **135** | **197** | **213** | 213 |
| `Orbital_Stunround`（EMS） | **148** | **76** | **188** | 0 |
| `Orbital_Cannon_380mm_HE` | 79 | — | 210 | 0 |
| `Orbital_Gas` | 151 | — | 82 | 0 |
| `Orbital_Smoke` | 10 | — | 0 | 0 |

**爆炸 213 在整张射弹表里只被 1 行引用（行 135）**；188 也只被 1 行（行 148）
⇒ 把行 135 的爆炸换成 188，只影响"120mm HE 这一发弹"，不会波及其它战备（`✓` 全表 355 行扫过）。

## 3 "逐发交替（HE/EMS 混编）"在数据层做不到（`✗` 否证）

HD2Runtime 的字段名里有 `orbital_120mm_he_barrage_attack_delivery_1/2/3_projectile`，本以为能在数据里找到三条投送。

| 查法 | 结果 |
|---|---|
| `ProjectileWeaponComponentData` 行结构（容器 `0x45171B68` → 行类型 `0x2290C42E`，**616 B / 556 行**，typelib 逐成员）| 弹丸槽**只有两个**：`+0x000`（主弹）与 `+0x240`（备弹/alt，正是当年"可编程弹药"用的那格），**没有第三、第四条** |
| 556 行武器的 `+0x000` / `+0x240` 里有没有 197（120mm HE）或 76（EMS）| **0 行** —— 战备轰炸的炮弹根本不是通过实体武器组件的数值字段发射的 |
| `AttackPatternComponentData`（`0x4CCBAD23`）| **全表只有 1 行**，且不含 197/76 |
| 其它"投送"类组件（`ObjectiveVehicleDelivery` / `ObjectiveDeliverableVehicle` / `ObjectiveCarryDelivery` / `ObjectiveShellRack` / `ObjectiveShell`）| 都是任务目标物件，与轨道弹幕无关 |

⇒ 那三条 `attack_delivery_*_projectile` **不在 dl_bin 表里**，是**资源层（unit / 投送资源的节点或事件）**里的名字 ——
这与旧结论一致：**战备 → 弹丸的关联不是数值外键，是运行时按资源名解析**（见 [STRATAGEM-REFERENCE-CHAIN](../tables/STRATAGEM-REFERENCE-CHAIN-25988413.md)）。
所以"同一条弹幕里逐发交替两种弹种"**纯数据做不到**。

## 4 纯数据能做的（`✓` 可执行）

| 方案 | 改动 | 效果 |
|---|---|---|
| **A. 120mm EMS 弹幕** | 射弹行 **135** 的 `+0x90`（命中爆炸）**213 → 188**；`+0x9C` 可选 | 120mm 弹幕全部变成 EMS 眩晕弹；因 213 独占，其它战备**零影响** |
| **B. 燃烧加特林（近似）** | 找 `ORBITAL. GATLING BARRAGE` 用的射弹行，把命中爆炸换成燃烧类（如 `EagleBomb_Napalm` 的爆炸行）| 与 A 同型：单弹种替换 |
| ~~C. 同一条弹幕 HE/EMS 交替~~ | —— | **✗ 数据层无入口**（见 §3）|

> B 需要先定位加特林弹幕的射弹行（同一套 name-hash 对齐法，`Orbital` 家族里没有 gatling 项 ⇒ 它用的是另一族射弹，待查）。

## 5 相关

- 弹丸行字段与换爆炸配方：[EXPLOSION-PROJECTILE-25988413](EXPLOSION-PROJECTILE-25988413.md)
- 爆炸表与粒子：[EXPLOSION-VISUAL-26088801](EXPLOSION-VISUAL-26088801.md)
- 战备→弹丸不是数值外键：[STRATAGEM-REFERENCE-CHAIN-25988413](../tables/STRATAGEM-REFERENCE-CHAIN-25988413.md)
