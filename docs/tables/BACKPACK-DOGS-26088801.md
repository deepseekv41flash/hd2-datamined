# AX 系列背包（Guard Dog 家族）：武器是"挂"上去的（build 26088801）

> 问题：`AX/AR-23 Guard Dog` 这类背包，武器是怎么装上去的？
> 答案（`✓` 离线逐字节）：**三层实体，武器是第三层，挂载句柄就是 `MountComponentData+0x00` 这一个 u64**——和载具挂点同一个组件、同一个字段。
> 另有第二条线索：**战备行 `+0xF0` 也写着同一把武器**（全表 153 行只有 4 行非零）。第一轮实验就是判这两个句柄谁说话。

## 1 三层链路（`✓`）

```
① 战备行  组0 行6  'BACKPACK. GUARD DOG (Drone)'
     +0x00 = 76 (类型枚举)     +0xF0 = 0xA32621E3BDE13379  ← 武器实体
        │
        │  ✗ 实体表里没有任何组件引用"无人机"的 id（xref 负结果，见 §5）
        ▼
② 背包 item  AX/AR-23 Guard Dog Backpack  0x255EBC5767D7CEEC（15 个组件，**没有武器**）
        │
        │  （生成引用不在这张表里 ⇒ 疑似资产/引擎侧，同"跳跃能力"那条结论）
        ▼
③ 无人机     AX/AR-23 Guard Dog Drone     0xA0FF2F9A0CA6992A（18 个组件）
     MountComponentData +0x00 ───────────► 武器实体 AX/AR-23 Guard Dog Weapon 0xA32621E3BDE13379
                （u64 = 被挂的 item 实体 id，与载具挂点同字段）
```

**耳机·无人机（③）的组件集**（18 个，和"背包"完全不是一类东西）：
`Unit` `Mount` `WeaponWielder` `Ability` `Attachable` `Tag` `Faction` `Health` `EffectReference`
`Behavior` `Boids` `Navigation` `Rotation` `Motion` `SensorEye` `Detector` `Targeting` `MultiTarget`
⇒ 它是个**完整的飞行单位**（会跟随、会锁定、会开火），不是"背包的一个特效"。

**武器（④）的组件集**（18 个，标准武器实体）：
`Unit` `WeaponData` `ProjectileWeapon` / `BeamWeapon`+`WeaponHeat` / `SprayWeapon` / `ArcWeapon`
`WeaponMagazine` `WeaponReload` `WeaponCustomization` `MeleeAttack` `Animation` `Equipment`
`EquipmentShowcase` `Interactable` `Wieldable` `Attachable` `Ability` `CollisionEvent` `NetworkPhysics` `PhysicsImpactEffect`

**关键读数**：`WeaponWielderComponentData`（36 B）**只有 float 参数**（`1.0 / 3.11 / 1.0 / 0.5 / 1.0 / 1.0 / 0.3`），
**不含任何武器引用** ⇒ 换枪**只改 `Mount+0x00` 一个 u64**，不用同步第二个字段。

## 2 十架无人机全表（`✓` 全表扫：Mount 有行且带 `Behavior`+`WeaponWielder` 的实体会）

| 无人机实体 | 模型资产 | 挂载武器 | 武器子系统 |
|---|---|---|---|
| `0xA0FF2F9A0CA6992A` | `AX/AR-23 Guard Dog Drone`（自身）| `0xA32621E3BDE13379` **AX/AR-23 Guard Dog Weapon** | Projectile（实弹）|
| `0x019544309FAC4508` | 同上 | `0x263817187B7CE092` | Projectile |
| `0xF800D5F62789246C` | 同上 | `0x3D4970D1C4E640EE` | Projectile |
| `0x1DB272DDA55199E0` | 同上 | `0x7F6E4F4455D4A6C2` | **AbilityWeapon**（`Ability`+`AbilityWeapon`，非枪）|
| `0x5BEEC97F4C7F4AE9` | 通用无人机（`0xCB8D6DBE2AD74BE4`）| `0x2C66C201B2543D2C` | **Beam**+Heat（激光）|
| `0x7956C174E9FAEFE0` | 通用 | `0x27EE1ED8F6FB6356`（名字表：`LAS-5 Scythe`）| **Beam**+Heat |
| `0x4B071633584E4594` | 通用 | `0xA0532C3616528CBF`（K-9）| **Arc**（电弧）|
| `0x979E9BC6D48D1FC6` | 通用 | `0x65CD4325BA23F3C6` | **Spray**（喷火/喷气）|
| `0xB9BAF571FC8F9959` | 通用 | `0xB729A2BA153BCAED` | **Spray** |
| `0xF9D5219640D65EF9` | 通用 | `0x968211C0033DCE64`（名字表：`AR-23 Liberator`）| Projectile |

⇒ 4 架 AR-23 模型 + 6 架通用模型；**武器子系统类型正好分出四个族**（实弹 / 激光 / 电弧 / 喷射）。

## 3 战备行 `+0xF0`：全表只有 4 行非零（`✓`）

| 组 | 行 | 行名 | `+0xF0` |
|---|---:|---|---|
| 0（13 个背包战备）| 6 | `BACKPACK. GUARD DOG (Drone)` | `0xA32621E3BDE13379` GD 武器 |
| 0 | 7 | `BACKPACK. Laser Rifle (Drone)` | `0x2C66C201B2543D2C` Rover 激光武器 |
| 0 | 12 | `BACKPACK. GUARD DOG (Drone) Stun` | `0xA0532C3616528CBF` K-9 电弧武器 |
| 8（团队武器）| 27 | `TEAM WEAPONS. MELEE FLAG` | `0xB0F1B354BA1D38D8` CQC-1 One True Flag |

战备表几何（本 build）：**stride 400**，`rows_at = payload + 16`，组 0 = 13 个背包战备（行 6/7/12 里的 3 个狗）。
其余 149 行该字段全 0 ⇒ 它不是"通用装备字段"，更像"无人机携带武器"的旁挂字段。

## 4 字段速查

| 组件（块 id，stride）| 偏移 | 类型 | 含义 |
|---|---|---|---|
| `MountComponentData` `0x3845B1E0`，120 | `+0x00` | u64 | **被挂 item 的实体 id**（载具挂点同字段，HD2Runtime `mount.weapon`）|
| | `+0x08` / `+0x0C` | u32 | 本 build 狗无人机为 `0x53BEC437` / `0x23CC0657`（模板/挂点标识，未证）|
| `WeaponWielderComponentData`，36 | — | f32 ×9 | 只有瞄准/后坐参数，**无武器引用** |
| 战备行（表 `generated_stratagem_settings`，stride 400）| `+0xF0` | u64 | 狗战备的武器 id（见 §3）|
| 战备行 | `+0x00` | u32 | 类型枚举（狗：76 / 118 / 2 …）|
| 战备行 | `+0x50` | f32 | 呼叫时间（GD 行 = 5.0）|
| 战备行 | `+0x68` | f32 | 冷却基数（GD 行 = 480.0）|

## 5 没解出来的那一环：背包 → 无人机（`✗` 负结果）

在整张实体表里对 7 个狗背包 id 与 10 个无人机 id 做 u64 引用扫描：

- **没有任何组件引用无人机的 id**（只出现在 `UnitComponentData+0x00`，那是"谁用这个资产"）；
- 也没有组件引用"背包 → 无人机"的配对关系；
- 跨表扫描：`generated_animation_event_trigger_settings` 引用了 GD 背包 id 1 次（动画事件触发器），
  `generated_stratagem_settings` 引用了**武器** id（§3），**没有表引用无人机 id**。

⇒ 生成关系大概率在**资产/引擎侧**（与 §8 的"跳跃能力在数据表之外"同一类结论），本轮不追。

## 6 第一轮实验（2026-10-26 21:5x 已装，`⚠`）

两个互不干扰的句柄，各改一件，一局两个读数：

| 实验 | 目标 | 改动 | 预测 |
|---|---|---|---|
| **A** | Guard Dog（3 架 AR-23 模型无人机 `0xA0FF…` / `0x0195…` / `0xF800…`）| `Mount+0x00` → **Rover 的激光武器** `0x2C66C201B2543D2C` | 狗吐**蓝色激光** ⇒ `Mount` 是权威句柄 |
| **B** | Rover（战备行 组0 行7 `BACKPACK. Laser Rifle (Drone)`）| `+0xF0` → **Guard Dog 武器** `0xA32621E3BDE13379` | Rover 打**实弹** ⇒ 战备行 `+0xF0` 是权威句柄（或至少被读）|

**判读**

| A（狗）| B（Rover）| 结论 |
|---|---|---|
| 激光 | 实弹 | 两个句柄都在用时被读；`Mount` 与战备行需**同步改**才能稳 |
| 激光 | 激光 | **`Mount` 权威**，战备行 `+0xF0` 只是声明/图标 ⇒ 换枪配方 = 改一个 u64 |
| 实弹 | 实弹 | **战备行 `+0xF0` 权威** ⇒ 官方武器走战备行，无人机 `Mount` 只在"无声明"时兜底 |
| 都不变 | 都不变 | 武器来自别处（asset/引擎）⇒ 与 §5 一致，收口 |

**装盘记录**

| 项 | 值 |
|---|---|
| entities | `out/dogs/d1c.dl_bin`（md5 `598e0515f91742a3296c04e002b9fcd7`，47,259,520 B）|
| 战备表 | `out/dogs/s1.dl_bin`（md5 `f84292cbbeb971bac809223a6c698d2d`，82,440 B）|
| 明文 | `d1c.plain` / `s1.plain`，round-trip 一致（sha256 `972ae8de…` / `833a65bf…`）|
| 基线 | entities = `out/bkval/p1e.plain`（含已验证的背包数值改动）；战备表 = 原版，备份 `out/dogs/stratagem.before.dl_bin`（md5 `168f2711…`）|
| 回滚 | `cp out/dogs/stratagem.before.dl_bin <game>/data/game/generated_stratagem_settings.dl_bin` + `cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin` |

## 7 相关

- 背包数值（冷却/跳高/补给次数/护盾半径）：[BACKPACK-VALUES-26088801](BACKPACK-VALUES-26088801.md)
- 背包家族与"能力不能移植"的收口：[BACKPACK-LINE-26088801](BACKPACK-LINE-26088801.md)
- 载具挂点（同一 `MountComponentData` 字段、另一套用法）：[MOUNT-SEATS-26088801](MOUNT-SEATS-26088801.md)

### 6.1 第一轮结果：`Mount` 权威，战备行 `+0xF0` 不改武器（2026-10-26 22:0x，`✓✓` + `✗`）

| 实验 | 实机结果 | 结论 |
|---|---|---|
| **A** Guard Dog 的 3 架 AR-23 无人机 `Mount+0x00` → Rover 激光武器 | **狗吐激光** | **`Mount+0x00` 就是挂载句柄** `✓✓` |
| **B** Rover 战备行 `+0xF0` → GD 实弹武器 | **Rover 仍打激光** | 战备行 `+0xF0` **不决定武器**（负结果）|

⇒ **换狗枪配方 = 改无人机 `MountComponentData+0x00` 一个 u64**。战备表已回滚原版（`md5 168f2711…`）。

## 7 还能挂什么：候选池（`✓` 全表扫 + 名字表分类）

### 7.1 引擎自己验证过"能挂"的池子：**80 件**（164 条 `Mount` 行里出现的不同 item）

| 类别 | 件数 | 说明 / 举例 |
|---|---:|---|
| **带武器组件** | **56** | 实弹 38 · 炮塔(`Turret`) 14 · 喷射 6 · 光束 3 · 电弧 2 · `AbilityWeapon` 2（有重叠）|
| 无武器组件 | **24** | 挂上去只会"挂在下面"不会开火：`conscript_jumppack` `0xE2E62FDD…`、`conscript_backpack_lmg` `0x426B3DF0…`、`soldier_chainsaw` `0x4FB6077F…`、`conscript_melee_claw` `0x2D1636F2…` |

**最稳的几个原生挂件**（被多处宿主用过）：

| item | 名字 / 形状 | 原生被挂次数 |
|---|---|---:|
| `0x070BC8D3E18BB8F9` | `/soldier_standard_rifle`（实弹）| **8** |
| `0x8365609B35EF6672` | `shuttle_gunship_turret_hmg`（炮塔+实弹）| 4 |
| `0x2ED3696E12A14D4C` | `soldier_machinegun`（实弹）| 2 |
| `0x2A346BF4552997E2` | `wep_scoutwalker_hmg`（实弹）| 2 |
| `0x8FB47DD28B398CF7` | `cyborg_tank_turret_cannon`（炮塔+实弹）| 2 |
| `0xF196069E7E14C497` | 炮塔+光束 | 2 |
| `0x5D142C3A73EBC634` | `tank_turret_rocketlauncher`（炮塔+实弹）| 1 |
| `0x49674794A165EDA8` | `tank_turret_autocannons`（炮塔+实弹）| 1 |
| `0xCD28A27A79BE53D5` | `turret_command_bunker_hmg`（炮塔+实弹）| 1 |
| `0x9926876B2375A1BB` | `turret_small_autocannon`（炮塔+实弹，载具线测过）| 1 |

### 7.2 池子之外、形状兼容可以试的三类

| 类 | 数量 | 例子（实体 id） | 预期 |
|---|---:|---|---|
| **玩家支援武器** `kind=support_weapon` | 46 | MG-43 `0x11C27D3BABB38956` · AC-8 `0xA8CFFB316F0B5C5F` · MG-206 `0x085C1EDB038EC24E`（**已在原生挂载池里出现 2 次**）· GL-21 `0x02EECD0B1FA49630` · RS-422 `0x2E9D0BDC48B09E60` · FLAM-40 `0x39AB99895147A3BF` · ARC-3 `0x96DE9CD50F7306E6` · LAS-98 `0xD54B9505C0F72873` | 形状与狗武器**完全同构**（`WeaponData`+`ProjectileWeapon`/`Magazine`/`Reload`）⇒ 最可能直接开火 |
| **炮塔/载具武器**（`Turret`+武器） | 14 | 见 §7.1 下半 | 炮塔件带 `TurretComponentData`（阵地行为），挂在无人机上可能"能射但转向由无人机接管" |
| **NPC 武器** | 多 | `soldier_standard_rifle`（8 次）、`soldier_machinegun`、`cyborg_tank_turret_cannon` | 包常在基础共享包 ⇒ 渲染最稳 |

**唯一硬风险 = 包是否加载**（载具线老账）：共享包里的 unit 零预热；他车/他包的 item 要"在场"才渲染，否则紫问号。
⇒ 挂**玩家武器**时，玩家最好同时带那把武器。

### 7.3 第二轮实验（2026-10-26 22:1x 已装，`⚠`）

一次召唤同时回答两件事：**这个 donor 能不能挂/能不能打**，以及**这只狗用的是哪个无人机实体**（留一个原生武器当对照）。

| 无人机 | 挂上去的东西 | 类别 |
|---|---|---|
| `0xA0FF2F9A0CA6992A` | **MG-43** `0x11C27D3BABB38956` | 玩家支援武器 |
| `0x019544309FAC4508` | **`shuttle_gunship_turret_hmg`** `0x8365609B35EF6672` | 炮塔+实弹（原生挂 4 次）|
| `0xF800D5F62789246C` | 原版 `0x3D4970D1C4E640EE`（**对照**，未动）| 原生实弹 |
| Rover `0x5BEEC97F4C7F4AE9` | **Arc Thrower ARC-3** `0x96DE9CD50F7306E6` | 玩家电弧武器 |
| Rover `0x7956C174E9FAEFE0` | 原版激光（**对照**，未动）| 原生光束 |

**判读**：召唤 Guard Dog 看它打成什么——MG-43 弹链 / 机炮炮塔弹 / 原版实弹，三者任一都能同时定位"哪架无人机"和"这类比能不能打"；
Rover 若吐电弧 ⇒ 电弧类可挂。若出现紫问号/武器不可见 ⇒ 包没加载（挂载成功但资源缺），也能从外观判断是哪一架。

**装盘**：entities = `out/dogs/e1c.dl_bin`（md5 `5eb21f5bc27761055996c1e0a65c04db`，round-trip 一致）；
战备表已回滚原版。回滚实体：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`。

### 6.2 第二轮结果：玩家支援武器直接可挂，且**装填正常**（2026-10-26 22:1x，`✓✓` / `⚠`）

| 无人机 | 挂的东西 | 实机结果 | 读数 |
|---|---|---|---|
| Guard Dog `0xA0FF2F9A0CA6992A` | **MG-43** `0x11C27D3BABB38956` | **开火 + 装填都正常** | 玩家支援武器**可直接挂**；顺带**定死映射**：Guard Dog 用的就是这架 |
| Rover `0x5BEEC97F4C7F4AE9` | ARC-3 电弧 `0x96DE9CD50F7306E6` | **紫色问号**（挂上了、资源没加载）| ⚠ 两因未分：包没加载 / 电弧类不兼容 |

**用户实机补充（重要约束）**：**Rover 没有装填机制**（它原生就是激光，无限弹药）；挂**非无限弹药**的武器要用 **Guard Dog**——
因为只有它能装填。⇒ 以后"有限弹药 donor"一律挂在 Guard Dog 上。

### 6.3 背包 ↔ 无人机映射（`✓` 实测钉死 2 件 + 资产名交叉）

| 狗 | 无人机实体 | `BehaviorId` | 原生武器族 |
|---|---|---|---|
| **Guard Dog**（AX/AR-23）| **`0xA0FF2F9A0CA6992A`** | **192** | 实弹 |
| **Rover**（AX/LAS-5）| **`0x5BEEC97F4C7F4AE9`** | **191** | 光束 |
| 其余 8 架 | `0x01954430…`/`0xF800D5F6…` = 192 · `0x1DB272DD…` = **315** · `0x7956C174…` = 192 · `0x4B071633…`(K-9) = 191 · `0x979E9BC6…`(HotDog) = **189** · `0xB9BAF571…`(DogBreath) = **190** · `0xF9D52196…` = 192 | | |

⇒ **`BehaviorId` 是按狗分的行为类**：实弹狗 192 / 光束·电弧狗 191 / 喷火狗 189 / 喷气狗 190 / `AbilityWeapon` 变异 315。

### 6.4 狗的弹药池（背包侧 `Deposit`，`✓`）

| 狗背包 | `capacity` / `start` / `refill` | `DepositRefill(+0x80)` |
|---|---|---|
| Guard Dog `0x255EBC5767D7CEEC` | **8 / 8 / 8** | 1 |
| Guard Dog `0xDFC8…` / `0xE88A…` | 4 / 4 / 2 | 3 |
| Rover | 4 / 4 / 2 | 3 |
| HotDog / DogBreath / K-9 | 6 / 6 / 6 | 1 |

## 8 第三轮实验：重武器 + 能不能把 Rover 改造成"会装填的狗"（2026-10-26 22:2x 已装，`⚠`）

| 无人机 | 改动 | 测什么 |
|---|---|---|
| **Guard Dog** `0xA0FF2F9A0CA6992A` | `Mount+0x00` MG-43 → **AC-8 Autocannon** `0xA8CFFB316F0B5C5F` | 重武器能否挂、能否装填 |
| **Rover** `0x5BEEC97F4C7F4AE9` | `Mount+0x00` 电弧 → **MG-43** `0x11C27D3BABB38956`，且 `BehaviorComponentData+0x00` **191 → 192**（换成 Guard Dog 的行为类）| Rover 能不能被"改成会装填的狗" |

**判读**

| Guard Dog | Rover | 结论 |
|---|---|---|
| 机炮能打能装填 | 能打且**能装填** | **`BehaviorId` 就是装填门** ⇒ 任何狗都能改造成有限弹药载体 `✓✓` |
| 机炮能打能装填 | 能打但**不装填** | 装填不在 Behavior ⇒ 下一候选：背包 `DepositRefill +0x80`（1 vs 3）、或无人机侧别的件 |
| 机炮能打不能装填 | — | 装填能力与武器耦合（AC-8 的弹匣/后坐流程），只对部分武器有效 |
| 机炮紫问号 | Rover 紫问号 | 不是武器侧问题而是**无人机侧资源**（Rover 机体缺件），Guard Dog 才是唯一稳的载体 |

**装盘**：entities = `out/dogs/f1c.dl_bin`（md5 `70af3e1da11cf1c43ffa4ad162d2190b`，round-trip 一致）。
回滚：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`（回到"只改背包数值"的干净态）。

### 8.1 第三轮结果：紫问号是**武器资源没加载**，不是机体问题（2026-10-26 22:2x，`✓` 归纳 + `⚠` 待分因）

| 无人机 | 挂的东西 | 结果 | 读数 |
|---|---|---|---|
| Guard Dog `0xA0FF…` | **AC-8 自动加农炮** `0xA8CFFB316F0B5C5F` | **紫问号** | 该 item 的 unit 资源不在场 |
| Rover `0x5BEEC97F…` | **MG-43**（同一把枪）| **正常显示**（能出 MG-43）| ⇒ 上一轮 Rover 的紫问号是**武器侧（ARC-3）**，不是 Rover 机体 |

**黄金规则（三轮归纳，`✓`）**：紫问号 = **那个 item 的 unit 资源不在场**。
同一把 MG-43 在 Guard Dog 和 Rover 上都正常；换成 AC-8 / ARC-3 就紫 ⇒ 差别是**玩家身上有没有带那把枪**（带谁谁加载）。

⇒ 两条实践规则：
1. 挂**玩家武器**时，玩家要同时携带那把武器（否则紫问号）；
2. 想无条件稳，选**原生挂载池**的 donor（游戏自己就在挂，包一定在）——见 §7.1。

### 8.2 四个载体与换弹能力（用户实机，`✓`）

| 狗 | 换弹机制 | 定位 |
|---|---|---|
| **Guard Dog** | **有** | 有限弹药 donor 的首选载体 |
| **Hot Dog**（AX/FLAM-75）| **有** | 可作载体 |
| **Dog Breath**（AX/TX-13）| **有** | 可作载体 |
| Rover（AX/LAS-5）| **无** | 原生无限弹药；适合承载激光/电弧类 donor |

⇒ **一次会话可以同时改 4 个背包**（四只狗各有独立无人机实体）——四路并行实验。

## 9 第四轮：四个载体 × 四个"原生池"donor（2026-10-26 22:4x 已装，`⚠`）

全部选**原生挂载池**里的 item（引擎自己就在挂，包必然在场），一次测四类形状：

| 狗 | 无人机 | 挂上去的 donor | 类别 | 原生被挂 |
|---|---|---|---|---|
| **Guard Dog** | `0xA0FF2F9A0CA6992A` | `soldier_standard_rifle` `0x070BC8D3E18BB8F9` | NPC 实弹 | **8 次** |
| **Hot Dog?** | `0x979E9BC6D48D1FC6` | `shuttle_gunship_turret_hmg` `0x8365609B35EF6672` | 炮塔+实弹 | 4 次 |
| **Dog Breath?** | `0xB9BAF571FC8F9959` | `soldier_machinegun` `0x2ED3696E12A14D4C` | NPC 机枪 | 2 次 |
| **Rover** | `0x5BEEC97F4C7F4AE9` | `tank_turret_autocannons` `0x49674794A165EDA8` | 炮塔+实弹 | 1 次 |

> Hot Dog / Dog Breath 两架无人机的归属还没实测钉死（它们都是"通用模型 + 喷射武器"）；本轮给它们挂了**不同**的 donor，
> 所以哪只狗吐出哪把枪，就同时说明了"谁是谁"。Rover 的 `BehaviorId` 已还原成原版 191（上一轮 191→192 的改造**未定论**，避免污染本轮）。

**判读**

| 现象 | 结论 |
|---|---|
| 四只狗都能出模型、能开火 | **原生挂载池 = 零风险 donor 源** ⇒ 换枪自由（只要 donor 在这个池子里）|
| 某只狗紫问号 | 该 donor 的包不在场（或该狗机体缺件）；用"哪只狗 × 哪个 donor"交叉定位 |
| 炮塔类只出模型不开火 | 炮塔件需要 `Turret` 宿主（无人机不是）⇒ **优先挂"武器件"而不是"炮塔件"** |
| 狗飞起来行为怪（不跟人/乱打）| `BehaviorId` 与武器族不匹配 ⇒ 要把行为也换成同族（见 §6.3）|

**装盘**：entities = `out/dogs/g2.dl_bin`（md5 `5de91c96fe0b515f59f3ac4201876550`，47,259,584 B，round-trip 一致）。
回滚：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`（回到"只改背包数值"的干净态）。
