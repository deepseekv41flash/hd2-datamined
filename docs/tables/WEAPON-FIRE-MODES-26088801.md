# 武器射击模式 / 射速档位（fire modes & ROF）—— 数据表能力模型（build 26088801）

> **状态：核心已实机打通。** 能给**任意武器**加「全自动」「齐射」「全射」，能造/删安全模式，
> 也能改 rpm 三档。尚未打通：槽位上限 3、齐射的"多发"（受枪管数约束，在模型侧）。
> 相关：[CHARGE-WEAPONS](CHARGE-WEAPONS-26088801.md)（蓄力 / 过蓄 / 爆炸）·
> 依据：`refs/hd2runtime-repo/docs/fire-modes.md`、`docs/fire-rate-modes.md`、
> `sdk/WeaponFireModeCapabilities.json`。

---

## 0 一句话

武器有**两套独立的选择器**，都由 `WeaponDataComponentData.function_info` 绑定：
**`Firemode(3)` = 射击模式**（模式值写在 `+0x90…0x9C` 四连槽里）、**`ROF(2)` = 射速档位**
（三档 rpm 写在 `ProjectileWeaponComponentData +4/+8/+12`）。往空槽写枚举值就能给别的武器加模式。

---

## 1 字段位置

### 1.1 射击模式（`WeaponDataComponentData`）

| 偏移 | 字段 | 说明 |
|---|---|---|
| `+0x8C` | `num_burst_rounds` (u32) | 连发轮数（**十进制 140 = 0x8C**） |
| `+0x90` | **`primary_fire_mode`** | 默认模式（槽 1） |
| `+0x94` / `+0x98` / `+0x9C` | secondary / tertiary / quaternary | 依次可选；**0 = 空槽** |
| `+0xB8` / `+0xBC` | `function_info.left` / `.right` | `WeaponFunctionType`；**3 = `Firemode` 选择键、2 = `ROF` 射速选择键** |

⚠ **偏移坑**：上游文档写的是**十进制** `+140 / +144`。按十六进制读 `0x140` 会读到浮点数
（`0.7`、`0.9`），白查一轮 —— `+140 = 0x8C`、`+144 = 0x90`。

### 1.2 射速档位（`ProjectileWeaponComponentData`）

| 偏移 | 字段 | 说明 |
|---|---|---|
| `+4` / `+8` / `+12` | `rounds_per_minute` X / Y / Z（三个 f32） | **Y 是默认档**，也是没有选择器时唯一生效的 |
| — | `WeaponDataComponentData +0xB8/+0xBC` = `2` | `ROF` 选择器；按键按 `Y→Z→X→Y` 循环、跳过 0 槽 |

**射速不随射击模式变**：`rpm` 只有一份，所有模式共用（`fire-modes.md` 原文）。

---

## 2 `FireMode` 枚举表（**已基本填满**）

| 值 | 名字 | 游戏内中文 | 验证 |
|---:|---|---|---|
| 0 | None（空槽） | — | ✓ 空位一律 0 |
| 1 | **Automatic** | 自动 | **✓ 实机**（APW-1 加全自动后可切可连发） |
| 2 | **Single** | 半自动 | ✓ 官方命名 + 57 把只有 `[2]` |
| 3 | **Burst** | 连发 | ✓ 官方命名（AR-23 第三档） |
| **4** | **Volley** | **齐射** | **✓✓ 实机**：AR-23 切过去面板显示「齐射」；SDK 猜的 `Safety_Off` **✗ 错** |
| **5** | **Safe**（安全蓄力，蓄满即发） | 安全 | **✓ 实机**（删掉 Railgun 第二槽后只剩「安全」） |
| **6** | **Unsafe**（可过蓄） | 不安全 | **⚠ 强推断**（Epoch `[6,6]` 能过蓄 + Railgun `[5,6]`） |
| **7** | **Total**（倾泻全部剩余弹药） | **全射** | **✓✓ 实机**：AR-23 一次扣扳机打完整个弹匣、伤害叠加、弹壳全喷 |
| 8 | 未使用 | — | 373 把无一把出现 |

> 反查方法：把「武器在数据里的模式集合」与「wiki 页面的 Firing Modes 一栏」联立。
> `4` 由 SG-88「Semi • Volley」↔ `[2,4]` 与 VG-70「Total • Volley • Auto」↔ `[1,4,7]` **两边独立钉死**，
> 再由游戏内中文名「齐射 / 全射」**实机确认**。

---

## 3 编辑器规则（哪些能做、哪些做不了）

| 规则 | 判定 |
|---|---|
| 加模式 = 往空槽写枚举值 | **✓ 实机** |
| **必须**有 `Firemode(3)` 绑在某个输入上，否则**只能有一个模式**（换掉而非可选） | **✓ 实测结构**（APW-1 原本 `[0,0]` 无选择键） |
| **槽位上限 = 3**（写第 4 槽不显示） | **✓ 实机**（AR-23 第四槽 = 4 后，面板仍三档）<br>SDK 的 `maxModes: 4` **✗ 否证** |
| 非多管武器也接受 `Volley(4)` | **✓ 实机**（AR-23 单管照样能加能切） |
| `Volley` 的发数 = **枪管数**；枪管数**不在数据表**（社区 schema 无 `barrels`，只有 `pellet_count`） | **✓ 实机**：单管 AR-23 加齐射 = 一次一发 |
| `Total(7)` 对任意武器成立，一次打完整个弹匣、**伤害叠加** | **✓✓ 实机**（AR-23 一枪拆 1000 血 E/MG-101 炮台） |
| 射速 rpm 三档可改、可加选择器 | ✓ 离线（MG-43/M-105/MG-206 三档实测值见 §4.2） |

---

## 4 实验台账

### 4.1 射击模式（5 轮，3 ✓ / 1 ✗ / 1 部分）

| run | 变量 | 结果 |
|---:|---|---|
| 3 | Railgun `+0x94`（第二模式 Unsafe）`6 → 0` | **✓ 实机**：面板只剩「安全」⇒ 5 = Safe |
| 4 | APW-1 `+0x94` `0→1`（Automatic）+ `+0xBC` `0→3`（选择键） | **✓ 实机**：半自动/全自动可切、全自动能连发 |
| 5 | AR-23 `+0x9C`（第四槽）`0 → 4` | **✗ 实机**：面板不显示第四档 ⇒ 槽位上限 3 |
| 6 | AR-23 `+0x94`（Single）`2 → 4`（Volley） | **✓ 实机**：面板显示「齐射」能切；单管 ⇒ 一次一发 |
| 7 | AR-23 `+0x94`（Single）`2 → 7`（Total） | **✓ 实机**：一次扣扳机打空弹匣、伤害叠加、弹壳全喷 |

### 4.3 run 8：任意枪加射速切换（**已装盘，待实机**）

| 项 | 值 |
|---|---|
| 目标 | **AR-23 Liberator**（原版 `rpm = 0 / 640 / 0`，只有一个默认档） |
| 变量（一个逻辑能力） | ① `ProjectileWeapon +4/+8/+12` 写成 **100 / 500 / 1000**<br>② `WeaponData +0xB8`（`function_info.left`）`0 → 2`（`ROF` 选择键） |
| 结果 | `rpm = 100 / 500 / 1000`（默认 Y = **500**）；`function_info = (2, 3)` = 左 ROF / 右 Firemode |
| 模式槽 | 保持原版 `[1, 2, 3, 0]`（不掺入射速实验） |
| 为什么绑左输入 | **Railgun 的安全切换就绑在 `+0xB8` 且实机可用** ⇒ 左输入是能按到的真实绑定 |
| 离线 | 4 次链式 set，G1–G9 全 PASS；哈希不变；封包 sha256 `22391afb…` |

**切换顺序**（`fire-rate-modes.md`，game.dll `0x617960`）：按键循环 `Y → Z → X → Y`、跳过 0 槽。
⇒ 实测应按出 **500 → 1000 → 100 → 500**，三档差别极大（每发 0.6 s / 0.06 s / 0.1 s 间隔）。

**判据**：

| 你看到 | 结论 |
|---|---|
| 按功能键能在三档之间循环、射速明显变化 | **✓ 射速路线对任意武器成立** ⇒ 能给任何枪加"慢/标准/极速"三档 |
| 按功能键没反应、射速恒定 500 | 左输入没有对应的按键绑定 ⇒ 改成 `function_info.right = 2` 再试（把 Firemode 挪到左） |
| 射速变化但**不是 500/1000/100** 那个顺序 | 记录实际顺序，修正"菜单顺序 = X/Y/Z"这条假设 |
| 射速改了但**只有一档** | 需要把 `rpm` 三档都非 0（本次已全非 0，若仍失败说明槽位另有条件） |

### 4.2 射速档位（离线）

| 武器 | rpm X / Y / Z | 射击模式槽 | `function_info`（左/右） |
|---|---|---|---|
| **MG-43 Machine Gun** | **630 / 760 / 900** | `[1]` | (0, **2 = ROF**) |
| **M-105 Stalwart** | **700 / 850 / 1150** | `[1]` | (0, **2 = ROF**) |
| MG-206 HMG | 450 / 600 / 750 | `[1]` | (0, **2 = ROF**) |
| **VG-70 Variable** | 300 / 550 / 750 | `[1,4,7]` | (**3**, **2**) ← 两套选择器都有 |
| APW-1（改后） | 0 / 400 / 0 | `[2, 1]` | (0, **3**) |
| AR-23（改后） | 0 / 640 / 0 | `[1, 7, 3]` | (0, **3**) |

---

## 5 能做什么（配方）

| 想要 | 写入 |
|---|---|
| 任意枪加**全自动** | 空槽（或替换现有档）写 `1`；没选择键的先给 `+0xB8`/`+0xBC` 写 `3` |
| 任意枪加**一键倾泻整个弹匣**（伤害叠加） | 写 `7`（**已验证可用**，`Total` 不依赖枪管数） |
| 任意枪加**连发** | 写 `3`（配 `+0x8C` 轮数） |
| 加**齐射** | 写 `4`（但只有多管枪会真打多发；单管 = 一发） |
| 让某把枪**恒定安全模式 / 永久不安全** | 改 `5` / `6` 两个槽 |
| 给任意枪加**射速切换** | `ProjectileWeapon +4/+8/+12` 写三个 rpm + `function_info` 某输入写 `2`（**run 8 待验**） |

---

## 5.5 双弹源 = 主武器 + **下挂武器（两个独立实体）**

有一类武器能切两种弹头，而且**弹匣与备弹都各自独立**（不像 `fnable ammo` 那样共用弹匣）：
**AR/GL-21 One-Two · AR-11 Arbitrator · SMG/FLAM-34 Stoker**。

### 5.5.1 机制：不是"一把枪两个弹池"，是**两个实体**

> 官方研究原文（`research/underbarrel-weapons-F5FEE03DCFDB.json`）：
> *"An underbarrel is a **separate weapon entity** named by the host's default underbarrel item —
> its delta sets **`WeaponCustomization +192 underbarrel_path`** to the entity;
> the host entity carries none of its records."*

⇒ 主武器与下挂**各有一套** `WeaponData` / `ProjectileWeapon|SprayWeapon` /
`WeaponRounds|WeaponMagazine` / `WeaponReload`，所以弹药天然不共用。

### 5.5.2 字段链（三层）

| 层 | 字段 | 本 build 实测 |
|---|---|---|
| ① 切换键 | **`WeaponDataComponentData +0xB8`（`function_info.left`）= `11`**<br>`WeaponFunctionType 11` = 第二弹源/下挂 | **全表 373 把里只有 3 把是 11**，正是这三把（其余：`0`×355、`3`×5、`8`×6、`2/4/6/10` 各 1） |
| ② 链接 | **`WeaponCustomizationComponentData +192` `underbarrel_path`**（由"默认下挂配件"的**实体 delta** 写入） | 基础组件里该格**全为 0** ⇒ 链接在 `generated_entity_deltas.dl_bin`，不在实体表本体 |
| ③ 下挂自身 | 下挂实体自己的 `ProjectileWeapon +0` / `WeaponRounds +72/+80` / `WeaponReload +56` | 见下表 |

### 5.5.3 三把武器 + 它们的下挂（本 build 实测）

| 宿主 | 下挂实体 | 家族 | 弹丸类型 | 容量 | 备弹 | 射速 | reload |
|---|---|---|---:|---:|---:|---:|---:|
| **AR/GL-21 One-Two** | `0x02CD7321CD8445F5`（"Grenade Launcher Grenadier"，与 **GP-31 Grenade Pistol 共用根**） | Projectile（榴弹） | **267** | **1** | **5** | 900 | 0 |
| **AR-11 Arbitrator** | `0xB9C209B4F99B5335`（"shotgun risk"） | Projectile（霰弹） | **201** | **4** | **20** | 80 | 0 |
| **SMG/FLAM-34 Stoker** | `0x992B6F65A5BAB53D`（"Flamerthrower SMG Flamer"，与 **P-72 Crisper 共用根**） | SprayWeapon（喷火） | `+200`=22 | mag **50** | — | — | 2.5 |

- 下挂的 `WeaponData.function_info = (0, 0)` ⇒ 它自己没有选择键，全靠宿主那个 `11` 切进来。
- 下挂的弹丸在**两处**都写着同一个值（`ProjectileWeapon +0` 与 `WeaponRounds +64` 均为 267/201），
  **究竟哪个生效未证**（研究文件把它列为 unproven）。

### 5.5.3b run 9：把 AR/GL-21 的榴弹下挂换成 **GP-20 Ultimatum** 的弹头（**已装盘，待实机**）

| 项 | 值 |
|---|---|
| 变量 | 下挂实体 `0x02CD7321CD8445F5`：`ProjectileWeapon +0` 与 `WeaponRounds +64` 同时 **267 → 105** |
| 为什么改两处 | 两处现在写着同一个弹丸 id，研究文件把「到底哪个生效」列为 unproven ⇒ 一起改 |
| GP-20 的弹丸 | **105**（其 `ProjectileWeapon +0`，行 240） |
| 弹丸 105 的效果 | 命中/到期爆炸 = **type 44** → 伤害 100、半径 **2.5 / 5 / 14 m**、无破片 |
| 对照 | **GP-31 的根是另一个实体** `0x52E4334E6A128CAF`（`+0` 仍 267）⇒ 理论上**不会**跟着变；带 GP-31 可验证 |
| 离线 | G1–G9 全 PASS；哈希不变；封包 sha256 `f1f60cb6…`；回读 `+0`=105、`+64`=105、GP-31 仍 267 |
| **实机** | **✓ 下挂打出来就是 GP-20 的弹头；GP-31 完全不变** |

⇒ 两个结论同时坐实：

1. **下挂的弹丸可以任意换**（改 `ProjectileWeapon +0` 与 `WeaponRounds +64`），宿主武器本体不受影响；
2. **catalog 的"共用根"说法是错的** —— `catalogCorrections` 里那条把下挂根误列进 GP-31，
   实际两者是两个实体、**只是引用同一个弹丸 id 267**；改下挂弹丸 ⇒ **GP-31 不动**（实机）✓。

### 5.5.4 由此得到的操作面

| 想做什么 | 可行性 |
|---|---|
| 改某把武器的**下挂**弹丸 / 容量 / 备弹 / 射速 | **✓ 实机**（run 9：AR/GL-21 下挂换成 GP-20 弹头；容器/备弹仍独立） |
| 把下挂**换成别的武器**（例：给它换成火焰喷射下挂） | ⚠ 需改 `generated_entity_deltas.dl_bin` 里那条默认配件的 `WeaponCustomization +192`，属另一张表，**未试** |
| 给**没有下挂**的枪加下挂（例：AR-23 加榴弹） | ⚠ 同上：必须写 entity delta + 配件 item，且要给宿主 `function_info.left` 写 `11`；**三件事**，未试 |
| 把下挂的弹匣/备弹和主武器**合并** | ✗ 结构上它们本就是两个实体，没有"共享"字段 |

---

## 5.6 输出族：喷火/毒气是**第 4 族 `Spray`**，不是弹丸

### 5.6.1 五族模型

一个武器实体**只能拥有一个输出族组件**（社区原文：*"A weapon entity owns exactly one output-family component
(ProjectileWeapon, BeamWeapon, ArcWeapon, **SprayWeapon** or MeleeWeapon)"*）：

| 族 | 组件 | type | 它的"弹丸"是什么 |
|---|---|---|---|
| 弹丸 | `ProjectileWeaponComponentData` | `0x45171B68` | `+0` ProjectileType → 射弹表一行 |
| 光束 | `BeamWeaponComponentData` | `0xF0721C2C` | `+0` BeamType |
| 电弧 | `ArcWeaponComponentData` | `0xB845669E` | `+0` ArcType |
| **喷流** | **`SprayWeaponComponentData`** | **`0x8E551126`** | **没有弹丸**：`+0xC8`（=十进制 200）`DamageInfoType` |
| 近战 | `MeleeWeaponComponentData` | `0xBBA9003F` | `+12` DamageInfoType |

⇒ **喷火器/毒气枪属于 `Spray`**：它不发射任何 projectile，而是"喷一段带伤害类型的锥形流"，
伤害与命中由 `+200` 那个小枚举决定，视觉由行内若干哈希（粒子/材质）决定。

### 5.6.2 布局与 24 行实测（`SprayWeaponComponentData` @`0x2CD4E50`）

payload **6,112 B** = `ComponentIndexData` **736 B**（46 槽 × 16 B，槽 = `{u64 实体键, u32 行号, u32 0}`）
+ `SprayWeaponComponent` 数组 **5,376 B**（**24 行 × 224 B**，自 `+0x2E0` 起；23 行被引用，第 23 行空）。

> ⚠ 上一版记的「46 槽 + 23 行」差一行：24 来自 typelib 的 `5376 / 224`，不是数出来的。

武器名由 `refs/entity-locid-names.json`（`EncyclopediaEntryComponentData` 名称槽）解出，**23/23 全部有名字**。

| 行 | 武器 / 实体 | kind | `+0x00` warmup | `+0x04` cooldown | `+0xC8` damage | `+0x70` firing 粒子 |
|---:|---|---|---:|---:|---:|---|
| 0 | Bile Titan | enemy | 0 | 0.05 | 0 | `0x55C957DC1C76D67A` |
| 1 | Caustic Spewer | unit | 0 | 0.05 | 0 | `0x55C957DC1C76D67A` |
| 2 | Septic Breath | unit | 0 | 0.05 | 0 | `0x55C957DC1C76D67A` |
| 3 | Caustic Spewer | unit | 0 | 0.01 | 591 | `0x255CA77E5A3919FF` |
| 4 | Hunter | unit | 0 | 0.05 | 0 | `0x55C957DC1C76D67A` |
| 5 | 未知 | unit | 1 | 1 | 0 | `0xBAD1C3CCBB6617B3` |
| 6 | 未知 | unit | 1 | 1 | 0 | `0xBAD1C3CCBB6617B3` |
| 7 | 未知（火焰炮台变体？`+0xC8`=24 与 Sentry 同） | unit | 0.7 | 10 | 24 | `0xE3D15622A42863C4` |
| 8 | Bile Titan | enemy | 0 | 0.05 | 0 | `0xE5F398FCBB669946` |
| 9 | Nursing Spewer | unit | 0 | 0.05 | 0 | `0x77FA0EE04F89E492` |
| 10 | G-142 Pyrotech（投掷物） | throwable | 0 | 0 | 32 | `0x172E1E5393DC59FF` |
| 11 | **A/FLAM-40 Flame Sentry** | unit | 0.7 | 10 | 24 | `0xE3D15622A42863C4` |
| 12 | 未知（毒气交互物） | interactable | 0.7 | 15 | 0 | `0x70690ADA12804044` |
| 13 | 未知（**Stoker 喷火下挂** `0x992B6F65A5BAB53D`） | unit | 0.7 | 10 | 22 | `0xEE2AA1974FBF52AF` |
| 14 | 未知（毒气） | interactable | 0.7 | 15 | 0 | `0x70690ADA12804044` |
| 15 | 未知（Torcher 变体） | interactable | 0.7 | 10 | 21 | `0xC22C03EC68E8DBCE` |
| 16 | 未知（毒气 `+0xC8`=36） | interactable | 0 | 15 | 36 | `0x035E79D1D898362B` |
| 17 | **FLAM-66 Torcher** | primary_weapon | 0.7 | 10 | 21 | `0xC22C03EC68E8DBCE` |
| 18 | **P-72 Crisper** | sidearm | 0.7 | 10 | 22 | `0xA252B7821AAB37D7` |
| 19 | **TX-41 Sterilizer**（毒气） | support_weapon | **0** | **15** | 35 | `0xA3D15A3BBC56DE55` |
| 20 | **FLAM-40 Flamethrower** | support_weapon | 0.7 | 10 | 20 | `0xA252B7821AAB37D7` |
| 21 | **B/FLAM-80 Cremator**（左管） | support_weapon | 0.7 | 10 | 23 | `0xA4F17DABA8ECD8E5` |
| 22 | **B/FLAM-80 Cremator**（右管） | support_weapon | 0.7 | 10 | 23 | `0x7E2D445495989701` |
| 23 | *(未引用)* | — | — | — | — | — |

三条一眼可见的分组：

- **火焰组**（10 以外的全部 `+0x00`=0.7 行）：`warmup=0.7 s`、`cooldown=10 s`；
- **毒气组**（12/14/16/19）：`warmup=0`、`cooldown=15 s`；
- **敌人/占位行**：`+0xC8`(damage)=0（行 3 例外 = 591，Bile Titan 的毒雾）。

**FLAM-40 与 P-72 Crisper 共用同一个 firing 粒子 `0xA252B7821AAB37D7`**；
Cremator 的两行各一个粒子（双管）；Pyrotech 的 `+0xC8`=32 但 `warmup/cooldown` 全 0（它是投掷物，没有导引火）。

装备侧：喷火器的弹药走 **`WeaponMagazineComponentData`（弹匣制）**，不吃 `WeaponRoundsComponentData`；
它们也**没有 `ProjectileWeaponComponentData`** —— 一个武器只有一个输出族，喷火器占的是 Spray。

### 5.6.3 行内结构：16 个字段**全部有名字**（社区 schema × typelib 对位）

`data/components/SprayWeaponComponent.json`（`shalzuth/HelldiversData`，`master` 分支）按**声明顺序**
列出 16 个成员，与 typelib `SprayWeaponComponent`（rec 224）的偏移**逐一严丝合缝**：

| 偏移 | 类型 | 字段 | 语义（社区原文） |
|---|---|---|---|
| `+0x000` | f32 | `warmup_time` | 从冷枪扣扳机到真正喷出之间的时间（= 导引火预热） |
| `+0x004` | f32 | `cooldown_time` | 停火后多久算"冷"（冷了就又要预热） |
| `+0x008` | f32 | `firenode_pose_limit` | 瞄准位姿允许偏离 firenode 的角度（0 = 不限制） |
| `+0x00C` | u32 | `audio_node` | [string] 播 warmup/fire/cooldown 音效的挂点 |
| `+0x010` | f32 | `spray_capsule_radius` | **>0 时改用物理胶囊重叠判定**替代"靠粒子命中"（实验性） |
| `+0x018` | struct | `warmup` | `SprayWeaponStateInfo`（预热态） |
| `+0x050` | struct | `firing` | `SprayWeaponStateInfo`（喷射态） |
| `+0x088` | struct | `cooldown` | `SprayWeaponStateInfo`（冷却态） |
| `+0x0C0` | u32 | `ammo_cost` | 每"团"喷雾扣多少弹药（本 build 全 1） |
| `+0x0C4` | ProjectileType | `projectile_type` | **非 None 就改用弹丸**（喷火/毒气全 0 ⇒ 没有弹丸） |
| `+0x0C8` | DamageInfoType | `damage_info_type` | 碰撞事件用的伤害类型（= 旧称 `+200`） |
| `+0x0CC` | HitEffectDamageType | `effect_type` | 命中特效的伤害类型（全 2） |
| `+0x0D0` | u8 | `particle_collision_trigger_mines` | 粒子碰撞是否引爆地雷（火焰 1 / 毒气 0） |
| `+0x0D4` | u32 | `last_drop_owner_vo_event` | 打完最后一发给持枪者的 VO |
| `+0x0D8` | u32 | `dry_fire_audio_event` | 空仓扣扳机的音效 |
| `+0x0DC` | FireTemplate | `particle_collision_fire_template` | 粒子打在**地形**上留的火焰模板（火焰 3 / 毒气 0 / Pyrotech 2） |

`SprayWeaponStateInfo`（56 B，三段同构）：

| 偏移 | 类型 | 字段 |
|---|---|---|
| `+0x00` | `WeaponCameraShakeInfo`（32 B） | `shake`：3×u64 抖动模板 + f32 **2.0** + f32 **5.0** |
| `+0x20` | u64 | **`muzzle_effect`** —— [particles] 该状态的枪口粒子（**视觉与伤害的实际载体**） |
| `+0x28` | u32 | `callout_event_start` |
| `+0x2C` | u32 | `audio_event_start` |
| `+0x30` | u32 | `audio_event_stop` |
| `+0x34` | WindEffectTemplate | `wind_template` —— 风影响模板（**只有毒气 = 7**） |

⇒ 旧版把 `+0x30/+0x68/+0xA0` 的 `(2.0, 5.0)` 猜成"近/中/远三段喷流"：**错**，那是**相机抖动**的强度/时长，
所有行都相同 `(2, 5)` 正说明"抖动是统一的"；`+0x0C` 也不是哈希而是 `audio_node`。

**三处 wiki 事实与字段名互证（独立第三方，全部对上）**：

| 字段 | 数据 | wiki 原文 | 判 |
|---|---|---|---|
| `warmup_time` | 火焰 **0.7** · 毒气 **0** | FLAM-40「Before firing, the pilot light must be lit by holding the fire button」；TX-41「doesn't have a firing delay due to the **lack of a pilot light**」 | **✓** |
| `cooldown_time` | 火焰 **10** · 毒气 **15** | 「The pilot light will extinguish automatically after a roughly **12-second** period of disuse」 | **✓** 同量级 |
| `wind_template` | 毒气 **7** · 火焰 **0** | 「The Sterilizer's spray is **affected by wind**」；1.006.300「Will be affected by wind less by **60%**」 | **✓✓** |

### 5.6.3b 字段含义：`+200` 是**伤害表的 type 键**（SHODAN + hd2runtime 双证）

**修正上一版的说法**：`+200` 不是一个"未解的小枚举"，而是**伤害表里那一行的 `type` 值** ——
伤害表（`generated_damage_settings.dl_bin`，661 行）**按 `type` 键**，SHODAN 就是这么查的：

```lua
-- shodan-stat-editor/src/stat_editor.lua
local T_SPRAY = 0x8E551126, ... { stride = 224, keyed = true }
-- flame and gas weapons: spray component (+200 damage row), damage per flame / gas hit
local id   = read_field(field_at(T_SPRAY, spray + 200, 'u32', 100000))
local drow = id and tables[T_DAMAGE] and tables[T_DAMAGE].index[id]      -- ← 按 type 反查
...
damage_rows(weapon, 'Damage', '', drow)
status_rows(weapon, 'Damage', '', drow, 'hit')                            -- ← 状态槽也在这一行
```

实测（本 build）：

| 武器 | `+200` | 伤害行 | 伤害 / 耐久 | 3×AP | 状态槽（`+44` 起 4×{type u32, value f32}） |
|---|---:|---:|---:|---|---|
| **FLAM-40** | **20** | 24 | 2 / 2 | 4,4,4 | **(5, 2.0) · (68, 1.0) · (6, 3.0)** |
| FLAM-66 Torcher | 21 | 28 | 2 / 2 | 4,4,4 | (5, 2.0) · (6, 3.0) · (68, 1.0) |
| P-72 Crisper | 22 | 29 | 2 / 2 | 4,4,4 | (5, 2.0) · (68, 0.5) · (6, 2.0) |
| **TX-41（毒气）** | **35** | 34 | 1 / 1 | 5,5,5 | **(44, 0.5) · (46, 0.5)** |
| G-142 Pyrotech | 32 | 31 | 0 / 0 | 7,7,7 | (5, 3.0) |

⇒ **"火 vs 毒"的真正分界是状态 id**：火焰走 **5 / 6 / 68**，毒气走 **44 / 46**。
`+200` 那 2 点伤害只是"每次判定的直伤"，**真正的燃烧/中毒来自伤害行上的状态槽**
（状态效果表 `generated_status_effect_settings.dl_bin`，组 `0xC63E0B22`，73 行）。

⚠ 状态表的行索引还没完全对上（该组 stride 算出来是 175，疑非标准布局）：只确认 **id 5 / 6 存在**，
**68 / 44 / 46 尚未定位**。

**hd2runtime 侧的说法**（`docs/attack-outputs.md`、`docs/enemy-authoring.md`）：
- `spray | SprayWeaponComponent | +200 DamageInfoType` —— 与上面一致；
- 全库 **8 把** spray 武器；一个 spray 武器的 DamageInfo = "the nine DamageInfo members"（伤害行的 9 个成员）；
- 写操作层面它把 spray 归为 **`INCOMPATIBLE_OUTPUT_FAMILY`（fail closed）** ⇒ **hd2runtime 不能写 spray**。
  这也解释了为什么 SHODAN 能改：**它改的是下游的伤害行，不是 spray 组件本身**。

### 5.6.4 毒气比喷火多一层：`Status`

TX-41 的 attack graph（`sdk/SupportWeaponAuthoringCapabilities.json`）：

```
TX-41 STERILIZER S            kind=Spray   role=primary
├─ Gas Var2                   kind=Status  role=primary_status_43
└─ Gas Confusion Var2         kind=Status  role=primary_status_45
```

⇒ **伤害来自 Spray，中毒/迷惑来自 `Status` 攻击**（两套独立数据；状态效果在
`generated_status_effect_settings.dl_bin`）。所以"把喷火器改成毒气枪"不是单改一个 id 能成的，
至少要动 Spray 的 `+200` **并且**给它挂上 Status 攻击。

### 5.6.5 三态

| 结论 | 态 |
|---|---|
| 存在第 4 个远程输出族 `SprayWeaponComponentData` | **✓ 离线**（社区模型 + 本 build 23 行实测，喷火/毒气/敌人喷火全在其中） |
| 喷火器不发射 projectile | **✓ 离线**（没有 ProjectileWeapon 组件；只有 Spray + Magazine） |
| `+200` = 喷流的伤害/命中类型 | **✓ 离线**（与社区 `+200 DamageInfoType` 一致；数值分火焰组 vs 毒气组） |
| `+200` = 伤害表的 `type` 键（不是无名小枚举） | **✓ 离线**（SHODAN 的查法 + 本 build 661 行伤害表按 type 键） |
| 火/毒的分界 = 伤害行 `+44` 状态槽的 id（火 5/6/68 · 毒 44/46） | **✓ 离线**（FLAM-40 / Torcher / Crisper / TX-41 / Pyrotech 五把对照） |
| 状态 id 68 / 44 / 46 在状态表里的行 | **⚠ 未定位**（组 stride 175 疑非标准布局） |
| hd2runtime 不能写 spray（INCOMPATIBLE_OUTPUT_FAMILY） | **✓ 离线**（官方 docs；SHODAN 走伤害行所以能改） |
| 16 个字段名（`warmup_time` … `particle_collision_fire_template`） | **✓ 离线**（社区 schema 声明顺序 × typelib 偏移逐一对应） |
| `+0x00` / `+0x04` = `warmup_time` / `cooldown_time`（不是射程） | **✓ 离线 + wiki 三处互证**（导引火 / 无延迟 / 12 s 熄灭） |
| `+0x30/+0x68/+0xA0` 的 `(2.0, 5.0)` = **相机抖动** | **✓ 离线**（`WeaponCameraShakeInfo`，全表同一值） |
| 喷火器射程 = `SprayWeapon +0x04` | **✗ 否证**（`+0x04` 是 `cooldown_time`；Cremator 25 m 与 FLAM-40 20 m 该值都是 10） |
| 表内存在"射程"标量字段 | **✗ 否证**（Cremator 与 FLAM-40 的**全部 16 个标量完全相同**，只有粒子 id 不同） |
| `firing.muzzle_effect` = 引擎真正读的粒子字段 | **✓ 实机**（run 11：改 id 外观当场变——变成灰色占位方块） |
| 跨包粒子不驻留（缺包 ⇒ 灰色半透明方块） | **✓ 实机**（run 11：FLAM-40 / Crisper 都变方块） |
| 射程 = `firing.muzzle_effect` 指向的粒子资源 | **⚠ 待 run 12**（包已用 Reinforce 驻留，两把枪都指向 TX-41 粒子） |
| 毒气的"中毒"来自 Status 攻击而非 Spray | **✓ 离线**（TX-41 的 attack graph） |

### 5.6.6 喷火器的「射程」：**不在数据表里**，在 `firing.muzzle_effect` 的粒子资源里

**结论**：`SprayWeaponComponent` 的 16 个字段里**没有射程**。射程由 `firing.muzzle_effect`（`+0x70`，
一个 [particles] 资源 id）指向的**粒子资源内部的参数**（粒子速度 / 寿命 / 阻力）决定；
数据表侧只能决定"引用哪个粒子"。

#### 证据 1：wiki 射程 vs 表内数据（五点对照）

| 武器 | wiki 射程 | `firing.muzzle_effect` | 粒子所在包（`refs/srkit-names.json`） |
|---|---|---|---|
| **FLAM-40 Flamethrower** | **20 m**（「measured in first person view」） | `0xA252B7821AAB37D7` | `a37891d879cb3b1d` |
| **P-72 Crisper** | 20 m（「same damage, firing range … as the Torcher」） | `0xA252B7821AAB37D7`（**与 FLAM-40 同一个**） | `a37891d879cb3b1d` |
| **FLAM-66 Torcher** | **20 m**（「Like the basic Flamethrower, it has a range of 20m」） | `0xC22C03EC68E8DBCE` | `49fd919a67a5db66` |
| **B/FLAM-80 Cremator** | **≈25 m**（「roughly 25 meters … 25% more than the FLAM-40's 20-meter range」） | `0xA4F17DABA8ECD8E5` / `0x7E2D445495989701`（双管各一） | `df16f5c644edc2b1` / `784671f2b3a4da79` |
| **TX-41 Sterilizer** | **47 m**（「measured in first person」） | `0xA3D15A3BBC56DE55` | `750605cfc0173701` |

另外：**warmup / cooldown 两个状态的枪口粒子在全部火焰武器上是同一个**
（`0x8B729322F53729F4` / `0x0B844F68DBA4F310`），毒气为 **0**（没有导引火）——
"导引火是一簇通用小火苗、喷流才是各枪自己的"这件事本身也自洽。

#### 证据 2：三重否证 —— 表内没有射程标量

1. **Pyrotech `+0x04` = 0**（用户的第一直觉）：它是个**投掷物**（`kind: throwable`，`warmup/cooldown` 全 0），
   根本不"喷"，拿它当"射程 0"会讲不通 —— 现在已知那是 `cooldown_time`。
2. **Cremator（25 m）与 FLAM-40（20 m）之间，16 个字段里只有三处不同**：
   `damage_info_type`（`0x14`→`0x17`，伤害身份）、六处音效事件 id、**`firing.muzzle_effect`（粒子）**；
   **没有任何数值/行为标量差** —— `warmup/cooldown/capsule_radius/firenode_limit/ammo_cost/mines/fire_template`
   全同，三段状态里的 `wind_template` 与抖动强度也全同。差 25% 射程却找不到任何标量差 ⇒ 射程不在标量里。
3. **Crisper 与 FLAM-40 共用同一个 firing 粒子，两者 wiki 射程也相同（20 m）** ⇒
   "粒子 ↔ 射程"有正相关，"标量 ↔ 射程"没有。

#### 证据 3：结构上只能由粒子承担

- `projectile_type`（`+0xC4`）= **0** ⇒ 没有弹丸可承载射程；
- `spray_capsule_radius`（`+0x10`）= **0** ⇒ 没开"物理胶囊重叠判定"；
- ⇒ 命中判定只剩"**粒子碰撞**"一条路（schema 里 `damage_info_type` 的注释正是
  *"If not set to None（且没有弹丸），this will use **collision events**"*），
  而"粒子"就是 `muzzle_effect`。wiki 也说过 FLAM-40「Its stream of fire deals continuous damage
  throughout its travel」——伤害是**跟着粒子飞**的。

#### run 10 的真实语义（已撤回，不是失败实验）

run 10 改的 `+0x04` 是 **`cooldown_time`：10 → 30 s**，即
「开火后多久算冷」。可观测预测：**停火 20 秒后再扣扳机，喷火器仍然"是热的"，不用重新点导引火**
（原版 `cooldown=10 s` 与 wiki「导引火约 12 秒不用会自动熄灭」吻合）。
这张盘已由 run 11 覆盖（`+0x04` 回原值 10）。

#### run 11 结果（**✗ 实机：灰色占位方块**）

实测（玩家报告）：**FLAM-40 与 P-72 Crisper 都变成灰色半透明方块粒子、完全没有火焰**。

⇒ 两条硬结论：

1. **`+0x70` 确实就是引擎读的那个粒子字段** —— 改 id，外观当场就换（这不是"没生效"，而是"生效了但资源没加载"）；
2. **跨包粒子不驻留** —— 灰色方块 = **资源缺失时的兜底渲染**（与"紫问号"同一类症状）。
   ⇒ "射程跟不跟粒子走"这一轮**没判到**，因为粒子根本没渲染出来。

#### run 12 结果（**✓ 实机：包驻留成功，两把枪都喷出雾状气流**）

配置：两把枪的 `+0x70` 都指向 TX-41 粒子 `0xA3D15A3BBC56DE55`；
Reinforce 两行 `+0xA8` = TX-41 的 toc 包 `0x750605CFC0173701`（封包 `ea2ca48e…` / `8c70575a…`，哈希不变）。

实测（玩家报告）：

1. **FLAM-40 与 P-72 Crisper 都喷出雾状气流**（不再是灰色方块）
   ⇒ **Reinforce 的 `+0xA8` 能驻留"粒子资源"这种消费方**、跨包换粒子成立 —— 新打通的一条路；
2. **Crisper 的射程似乎变长了**（玩家目测：原版只有 ~10 m）。

⚠ 但"射程"这一项**还没量化**，而且冒出一个新矛盾：

| 事实 | 含义 |
|---|---|
| 原版 Crisper 与 FLAM-40 **共用同一个粒子** `0xA252B7821AAB37D7` | 若射程完全由粒子决定，两者的**原版射程应当相同** |
| 玩家目测原版 Crisper 只有 **~10 m**，而 wiki 说 Crisper「same firing range as the Torcher」= **20 m** | 要么目测偏差，要么还有**第二个因子**（发射点位置 / 散布 / 粒子缩放） |
| 换成 TX-41 粒子后 Crisper "看起来更远" | 粒子至少是**主因**，但"只有粒子"尚未排除其它因子 |

#### run 13（已装盘）：同场并列对照 —— FLAM-40 换回原版粒子

为了让"粒子 → 射程"在**同一局、同一画面**里可比，把 FLAM-40 换回它自己的原版粒子
（在 FLAM-40 自己的包里，必然驻留），Crisper 保留 TX-41 粒子：

| 武器 | `+0x70` | 用途 |
|---|---|---|
| **FLAM-40**（行 20） | `0xA252B7821AAB37D7`（原版，20 m） | **基准尺**：原版火焰该有多远 |
| **P-72 Crisper**（行 18） | `0xA3D15A3BBC56DE55`（TX-41，47 m） | 实验组：雾状气流 |
| TX-41（行 19） | 原版 | 不动；同场带不了也没关系，它的 47 m 已是已知基准 |

战备侧不动（Reinforce 两行仍挂 TX-41 包，否则 Crisper 又变方块）。
封包 `77924977…`，哈希 `0x8E49771B181FFAA1` 不变，盘上回读一致。

| 实机现象 | 结论 |
|---|---|
| Crisper 气流**明显长于 FLAM-40 火焰**（接近 2 倍以上） | **射程 = 粒子** ✓✓（同场并列） |
| 两者差不多长 | 粒子只决定外观；Crisper"变长"是错觉 |
| Crisper 仍 ~10 m 而 FLAM-40 ~20 m（**两者原版是同一个粒子**） | 存在**第二因子**（发射点 / 散布 / 粒子缩放）且它比粒子更强势 ⇒ 去查 Crisper 的武器侧与发射节点 |
| Crisper 远处**打不出伤害** | 视觉射程变了但命中没变 ⇒ 伤害判定另有其源 |

#### 能力边界（射程这一项）

| 想做的事 | 手段 | 判 |
|---|---|---|
| 让某把喷火器用上另一把枪的粒子（外观） | 改 `firing.muzzle_effect` 的 u64 + **把供体的包驻留**（Reinforce `+0xA8`） | **✓ 实机**（run 12：两把枪都雾状气流） |
| 用换粒子把射程借长 | 同上 | **⚠ 待 run 13 量化**（run 12 Crisper 目测变长） |
| 把射程调成"任何我想要的米数" | 改**粒子资源**内部的速度/寿命（`.particle`，资源路线，非 `dl_bin`） | **✗ 数据表做不到** |
| 让火焰"命中范围更宽/判定不同" | `spray_capsule_radius`（`+0x10`）> 0 打开物理胶囊重叠判定 | **⚠ 未试**（schema 自标 Experimental） |
| 让火焰更持久 / 更易点燃 | 伤害行 `+44` 状态槽（status 5/6/68）与状态表 | ✓ 见 §5.6.3b |

### 5.6.7 粒子资源本身：**没有表**，只有资源（射程的赌注压在这里）

**结论：`firing.muzzle_effect` 指向的是一个 package 里的 `particles` 资源，没有任何 settings 表描述它的内部参数。**

#### ① 全表搜索：7 个 muzzle 粒子 id 在 55 张明文表里只出现在 spray 行

| 粒子 | id | 命中位置 |
|---|---|---|
| FLAM-40 / Crisper firing | `0xA252B7821AAB37D7` | `generated_entities` ×2（两行各一处） |
| Torcher firing | `0xC22C03EC68E8DBCE` | `generated_entities` ×2 |
| TX-41 firing | `0xA3D15A3BBC56DE55` | `generated_entities` ×1 |
| Cremator 左/右管 | `0xA4F17DABA8ECD8E5` / `0x7E2D445495989701` | `generated_entities` ×1 各 |
| 导引火 warmup / cooldown | `0x8B729322F53729F4` / `0x0B844F68DBA4F310` | `generated_entities` ×11 / ×13（全部火焰武器共用） |

⇒ **除 spray 组件行以外，零命中**。`generated_damage_settings` / `generated_status_effect_settings` /
`generated_explosion_settings` 里都没有它们。

#### ② 表里只有"对粒子的引用"，没有"粒子的参数"

按 8 字节 u64 扫一遍（对齐 4）能反解到 `srkit-names.json` 里 `particles` 类型资源 id 的表：

| 表 | distinct 粒子引用 |
|---|---:|
| `generated_surface_effect_settings` | 404 |
| `generated_explosion_settings` | 151 |
| `generated_destruction_settings` | 151 |
| `generated_hit_effect_settings` | 134 |
| `generated_unit_effect_settings` | 109 |
| `generated_animation_event_trigger_settings` | 53 |
| `generated_distant_war_effect_settings` | 23 |

这些表回答的是"**哪个效果配哪个粒子**"；速度/寿命/阻力这类参数在资源里，表里没有。
而且 **spray 连这种引用表都不走** —— 它的粒子直接写死在 `SprayWeaponStateInfo +0x20`。

社区 schema 也停在引用级：`data/components/` 里与粒子相关的只有
`ParticleEffectSetting`（`effect` + `id` + 孤儿策略）、`DestructionEffectSpawnParticles`
（`particle_effect` + 偏移 + 旋转 + `duration`）、`VehicleEffectParticleInfo`（`name` + 挂点 + 对齐），
**没有一个字段是"粒子飞多快/活多久"**。

#### ③ 资源本体：能取出来，但**没有字段图**

`srkit extract --id <id> --type particles` 可以直接把六把枪的粒子抠出来（本 build）：

| 粒子 | 文件大小 | 头部 `ver` | 头部 extent | 模块数 |
|---|---:|---:|---|---:|
| FLAM-40 firing（20 m） | 28,428 B | 115 | 30 × 30 | 12 |
| FLAM-66 Torcher firing（20 m） | 28,428 B | 115 | 30 × 30 | 12 |
| TX-41 firing（47 m） | 10,848 B | 115 | 30 × 30 | 9 |
| B/FLAM-80 Cremator 左管（25 m） | 32,360 B | 115 | **64 × 64** | 14 |
| B/FLAM-80 Cremator 右管（25 m） | 32,360 B | 115 | **102 × 102** | 14 |
| 导引火（共用） | 8,448 B | 115 | 1 × 1 | 4 |

- **同族同版本**：`u32 115` 版号 + 一个 u32 哈希 `0x5368D4A5` 六把全同 ⇒ 同一种导出格式；
- extent 与"覆盖面积"同向（导引火 1×1 最小、Cremator 翻倍再翻倍，wiki 也说 Cremator "increased range **and coverage**"），
  但 **TX-41 与 FLAM-40 的 extent 同为 30×30 却是 47 m / 20 m** ⇒ **extent 不是射程**；
- FLAM-40 与 Torcher 的粒子**同尺寸、只差 205 字节（0.72%）** ⇒ 同模板只改颜色/参数，是最理想的差分样本；
- 资源内**没有可读字段名**，`srkit codecs` 对 `particles`（`0xA8193123526FAD64`）是 **`no (raw fallback)`**；
  `dl_library.dl_typelib` 里也只有 3 个粒子相关类型名（全是"组件"，不是粒子自身）⇒ **粒子格式不在 DataLibrary 里**。

#### ④ 所以射程这一项的三条路

| 路 | 做法 | 成本 / 判 |
|---|---|---|
| **A** | 改 `firing.muzzle_effect` 指向别的粒子（run 11 已装盘） | 表内一行一 u64；**先证明"粒子决定射程"** |
| **B** | 差分粒子资源找速度/寿命那一格（FLAM-40 vs Torcher 只差 205 B；再叠 Cremator / TX-41 三档） | 需要自己写粒子解码/差分，**无字段图**；可行但工程量大 |
| **C** | `spray_capsule_radius`（`+0x10`）> 0 改命中判定方式 | 表内字段、最便宜，but schema 自标 Experimental |

| 结论 | 态 |
|---|---|
| 没有"粒子参数表"（55 张全扫，粒子 id 只在 spray 行） | **✓ 离线** |
| 无效效果表能反解粒子引用（surface 404 / explosion 151 …） | **✓ 离线** |
| 粒子资源同族同版（`ver 115` + 固定哈希 + extent + 模块数） | **✓ 离线**（六把实测） |
| 资源内字段语义（速度/寿命在哪） | **⚠ 未解**（无字段名、无 schema、codec raw） |
| 跨包粒子不驻留 ⇒ 灰色占位方块 | **✓ 实机**（run 11） |
| Reinforce `+0xA8` 能驻留**粒子资源**这个消费方 | **✓ 实机**（run 12：雾状气流出现） |
| 换粒子能换外观 | **✓ 实机**（run 12） |
| 射程 = 粒子（run 13 量化） | **⚠ 待实机**（run 12 Crisper 目测变长，但同源粒子矛盾未解） |

---

## 6 三态 / 未解

| 结论 | 态 |
|---|---|
| 模式槽 = `FireMode` 枚举、`0` 为空 | **✓ 离线** |
| `Firemode(3)` 是模式选择键、`ROF(2)` 是射速选择键 | **✓ 离线 + 实机**（APW-1 加 3 后能切） |
| 1 = 自动、2 = 半自动、3 = 连发 | **✓** |
| 4 = 齐射、5 = 安全、7 = 全射 | **✓ 实机** |
| 6 = 不安全 | **⚠ 强推断**（未单独验） |
| 槽位上限 = 3 | **✓ 实机**（并否证 SDK 的 `maxModes: 4`） |
| 齐射发数 = 枪管数，枪管数不在数据表 | **✓ 实机 + 离线** |
| `Total` 的"自伤/掀翻"阈值（VG-70 是 >22 发） | **⚠ 未证**（AR-23 打 45 发用户未报自伤，待确认） |
| 给任意枪加**射速切换** | **⚠ 待 run 8**（AR-23：100/500/1000 + 左输入绑 ROF） |
| 要把"齐射多发"给单管枪 | **✗ 数据表做不到** ⇒ 需改 `unit`/`state_machine` 的 muzzle 定位点（资源路线） |
| **双弹源 = 主武器 + 下挂武器两个独立实体**（非弹池共享） | **✓ 离线**（研究文件 + 本 build 三把实测） |
| 切换键 = `function_info.left = 11`（`WeaponFunctionType 11`） | **✓ 离线**：全表只有这 3 把是 11，一一对应 |
| 链接字段 = `WeaponCustomization +192 underbarrel_path`（本 build 基础值为 0，来自 entity delta） | **✓ 离线** |
| 改下挂的弹丸/容量/备弹 | **✓ 实机**（run 9）—— 这是「给主武器加一个**独立弹药池**的第二弹头」的现成入口，**不依赖 programmable ammo** |
| 给无下挂武器加下挂 | **⚠ 未试**（要写 entity delta + item + `func.left=11`） |
