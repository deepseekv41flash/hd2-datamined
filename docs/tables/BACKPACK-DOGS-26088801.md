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

## 10 紫问号的解法：把 donor 的包做**整包驻留**（2026-10-26 22:5x 已装，`✓` 机制 / `⚠` 待实机）

**问**：能不能把挂那把枪的包驻留下来，避免紫问号？
**答**：能，这正是 `.patch_N` 的整包驻留路线（载具线 P1–P4 已实测过多轮）。

### 10.1 为什么紫问号是"包不在场"

- 紫问号 = **该 item 的网格/材质/贴图没加载**，不是 `Mount` 写错（写错是"什么都没有"或崩）。
- 用户判断：上一轮 MG-43 能显示，很可能是**那局地图上刚好刷出了 MG-43**（世界里的拾取物会把它的包拉进内存），
  而不是"玩家带着"——也就是**靠运气**。要脱离运气，就得让包常驻。

### 10.2 实现（一条命令一个包）

```bash
python tools/whole_package_patch.py build     --package <item 的 LoadoutPackageComponentData+0x08>     --host f6fb08cc02d24255 --install
```
`.patch_N` 把资源按 `file_id` 塞进**已经常驻的宿主包**，全局可查——不受 `+0xA8` 那几个"有限跨包口"的限制。

| donor | 包（`LoadoutPackage+0x08`）| 包内资源 | toc / gpu / stream | 产出 |
|---|---|---|---|---|
| **AC-8 自动加农炮** `0xA8CFFB316F0B5C5F` | `0x6AD7CC21015A5F85` | 51 条（texture13/anim10/particles7/material6/mesh4/physics2/bones1/state_machine1…）| 3.86 / 4.39 / 4.87 MB | **patch_18** |
| **ARC-3 电弧** `0x96DE9CD50F7306E6` | `0x2A9FB8F5D0576EAE` | 44 条（texture13/particles8/material8/anim7/bones2/mesh2/state_machine1…）| 4.50 / 4.06 / 3.65 MB | **patch_19** |

**注意**：这两个包里**没有 `unit`** 资源，只有网格/材质/贴图/动画/状态机 ⇒ 说明紫问号缺的是**渲染资源**；
item 的 `unit` 多半在别处（大概率在常驻的 base 共享包里）——这一点是**推断，未单独验证**（`⚠`）。

### 10.3 第四轮（已装，`⚠`）

| 狗 | 无人机 | 挂的 donor | 驻留 |
|---|---|---|---|
| **Guard Dog** | `0xA0FF2F9A0CA6992A` | **AC-8** `0xA8CFFB316F0B5C5F` | **patch_18**（已装）|
| **Rover** | `0x5BEEC97F4C7F4AE9` | **ARC-3** `0x96DE9CD50F7306E6` | **patch_19**（已装）|

**测法（关键）**：这一局**不要**携带 AC-8 / ARC-3，也尽量别让地图上刷出它们，直接召唤 Guard Dog / Rover。

**判读**

| 现象 | 结论 |
|---|---|
| 两把都正常出模型、能开火 | **驻留 = 紫问号的正解** `✓✓` ⇒ 任意 donor 都能"无条件挂"，不再看运气 |
| 仍然紫问号 | 缺的不在 `LoadoutPackage+0x08` 这个包里 ⇒ 要找到真正含 `unit` 的包（下一候选：`srkit list --id <item 资产 id> --type unit` 全库定位）|
| 出模型但不开火 | 资源解决了、行为/弹道不匹配（回到 `BehaviorId` / 武器族问题）|

**装盘**：`f6fb08cc02d24255.patch_18`（51 条）+ `.gpu_resources` + `.stream`；`patch_19`（44 条）同理；
entities = `out/dogs/h1b.dl_bin`（md5 `404668faaf9255736d7d1ca838a51bc4`）。
**回滚**：删掉 `data/f6fb08cc02d24255.patch_18*` 与 `patch_19*` 六个文件；entities 回 `out/bkval/p1e.dl_bin`。

## 11 驻留 = 紫问号的正解（2026-10-26 22:4x 实机，`✓✓`）+ 开火模式是行为决定的（`⚠` 待验）

| 狗 | 挂的 donor | 实机结果 | 读数 |
|---|---|---|---|
| **Guard Dog** `0xA0FF…` | **AC-8 自动加农炮**（+patch_18 驻留）| **正常，能换弹** | **整包驻留 = 紫问号正解** `✓✓`；且 AC-8 走 Guard Dog 的装填循环 |
| **Hot Dog** `0x979E9BC6…` | **`shuttle_gunship_turret_hmg`**（原生池）| **正常** | **炮塔件挂在无人机上也可以用**（撤回之前"炮塔件需要 `Turret` 宿主"的猜测）|
| **Rover** `0x5BEEC97F…` | **ARC-3 电弧**（+patch_19 驻留）| **模型正常、有蓄力特效，但不开火** | 资源问题已解决（不再紫问号）；剩下是**开火模式**问题 |

**用户推断（`⚠` 合理但未证）**：Rover 的 `BehaviorId=191` 是"持续光束"行为（原生就是激光），
**AIBEH 一直按住扳机不松**，而 ARC-3 是**蓄力—松手释放**型 ⇒ 永远不放电弧。
⇒ 推论：**"能不能打"不只看武器组件，还看这条狗的行为是否与该武器的开火模式匹配**（光束/按住型 vs 点射/松手型）。

### 11.1 背包 ↔ 无人机映射（现在已实测钉死 3 只，`✓✓`）

| 狗 | 无人机实体 | `BehaviorId` | 原生武器 |
|---|---|---|---|
| **Guard Dog**（AX/AR-23）| `0xA0FF2F9A0CA6992A` | 192 | 实弹 |
| **Rover**（AX/LAS-5）| `0x5BEEC97F4C7F4AE9` | 191 | 光束 |
| **Hot Dog**（AX/FLAM-75）| `0x979E9BC6D48D1FC6` | 189 | 喷射 |
| Dog Breath（AX/TX-13）| `0xB9BAF571FC8F9959`（按排除法推定，`⚠`）| 190 | 喷射 |

## 12 第五轮：验证"开火模式由行为决定"（2026-10-26 22:4x 已装，`⚠`）

2×2 设计：**同一把 ARC-3** 分别挂在"实弹行为"和"光束行为"的狗上；再把 Rover 的行为改成实弹行为。

| 狗 | 挂的 donor | 改动 | 想验的事 |
|---|---|---|---|
| **Guard Dog** `0xA0FF…`（行为 192）| **ARC-3** `0x96DE9CD5…` | 只换枪 | 实弹行为 + 蓄力武器 ⇒ **能放电弧吗** |
| **Rover** `0x5BEEC97F…`（行为 191）| **ARC-3**（不变）| **`BehaviorId` 191 → 192** | 把行为换成实弹型 ⇒ **是否就能松扳机发射** |
| **Hot Dog** `0x979E9BC6…`（行为 189）| **`tank_turret_rocketlauncher`** `0x5D142C3A73EBC634` | 换 donor | 火箭巢能不能挂/打（原生池，包必在）|
| **Dog Breath** `0xB9BAF571…`（行为 190）| **`cyborg_tank_turret_cannon`** `0x8FB47DD28B398CF7` | 换 donor | 加农炮能不能挂/打（原生池）|

**判读**

| Guard Dog（弧）| Rover（弧+行为192）| 结论 |
|---|---|---|
| 能放 | 能放 | **ARC-3 只是缺正确行为** ⇒ 想挂蓄力类武器必须换 `BehaviorId` `✓✓` |
| 能放 | 不能 | 行为不是唯一条件（Rover 机体另有缺件）⇒ 载体白名单 = 实弹狗的机体 |
| 不能 | 不能 | 弧武器在无人机上根本不工作（`ArcWeapon` 需要玩家手部/蓄力输入）⇒ 无人机只适合"按住型/自动型"武器 |

顺带：Hot Dog 火箭巢 / Dog Breath 加农炮两个原生池 donor 的结果能补全"炮塔件挂在无人机上"的可用清单。

**装盘**：entities = `out/dogs/i1d.dl_bin`（md5 `f8ba190b2e0bee2eedcda417835f60b5`）；
驻留 patch_18（AC-8）/patch_19（ARC-3）保持安装，本轮 ARC-3 仍需要它。
回滚：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`（+ 删 patch_18/19 若要彻底复原）。

### 11.2 更正：**原生池 ≠ 资源保证**（Dog Breath + `soldier_machinegun` = 紫问号，`✓` 反例）

第四轮里 **Dog Breath** 挂的 `soldier_machinegun` `0x2ED3696E12A14D4C`（**原生挂载池成员，游戏自己挂过 2 次**）**仍然紫问号**。

⇒ **"原生池"只证明"形状/行为上能被挂、能开火"，不保证"包在场"。** §7.1 里那句"原生挂载池 = 零风险 donor 源"作废。

那为什么 `shuttle_gunship_turret_hmg` 那例正常？——它的宿主是**每局都在场的运输机/撤离穿梭机**，包随场景常驻，
所以"看起来免驻留"。同理 `soldier_standard_rifle` 那类 NPC 武器，要看当场景里有没有那个 NPC 拿它。

**真规则只有一条**：想不看运气 ⇒ **把 donor 的包驻留**（`patch_18` / `patch_19` 就是这么做的）。
原生池的价值退化为：**形状白名单**（这些 item 有炮塔/武器组件、在被挂时能开火）。

## 12 第五轮（修订版）：三个载体 × 同一把蓄力武器 + 一个天然常驻对照（2026-10-26 22:4x 已装，`⚠`）

因为 §11.2 的教训，本轮把三只狗统一挂 **ARC-3**（`patch_19` 已驻留，必然出模型），
只让**行为**变化——这样"能不能放电弧"的差异只能来自 `BehaviorId`：

| 狗 | 无人机 | 挂的 | `BehaviorId` | 资源 |
|---|---|---|---|---|
| **Guard Dog** | `0xA0FF2F9A0CA6992A` | **ARC-3** `0x96DE9CD50F7306E6` | **192**（实弹狗行为）| patch_19 |
| **Rover** | `0x5BEEC97F4C7F4AE9` | **ARC-3** | **192**（原版 191，**本轮改成 192**）| patch_19 |
| **Dog Breath** | `0xB9BAF571FC8F9959` | **ARC-3** | **190**（喷气狗行为）| patch_19 |
| **Hot Dog** | `0x979E9BC6D48D1FC6` | `shuttle_gunship_turret_hmg`（对照，已验证正常）| 189 | 天然常驻 |

**判读**

| Guard Dog(192) | Rover(191→192) | Dog Breath(190) | 结论 |
|---|---|---|---|
| 能放 | 能放 | 能放 | 蓄力武器只要**行为不是"按住型"**就行；或干脆与行为无关（那就是别的原因）|
| 能放 | 能放 | 不能 | 190 也是一种"按住型"；⇒ 用 Guard Dog 的行为当通用解 |
| 能放 | 不能 | 不能 | 行为不是唯一条件：**Rover/DB 机体**另有缺件 ⇒ 载体白名单 = 实弹狗机体 |
| 都不能 | | | `ArcWeapon` 在无人机上根本不工作（需要手部蓄力输入）⇒ 无人机只适合按住/自动型武器 |

**装盘**：entities = `out/dogs/i1e.dl_bin`（md5 `0086cc062d3155d0e76640b5abbab2dd`）；驻留 patch_18/19 保持安装。
回滚：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`。

### 12.1 第五轮结果：**蓄力武器在实弹行为下"偶尔能放、丢视线必放"**（2026-10-26 22:5x，`✓` 现象 / `⚠` 机制）

Guard Dog（`BehaviorId=192`）+ ARC-3：**偶尔能放电弧；目标丢失视线时必定放电弧。**

读数：`ArcWeapon` 的"蓄力—释放"由**扳机状态**驱动；AIBEH 在有视线时一直按住（蓄力不释放），
一旦丢失视线它就松手 ⇒ 电弧打出。⇒ 用户先前推断的"按住不放"方向是对的，只是不是"永远不放"，
而是"**只在松手时机（丢视线）才放**"。这解释了为什么原生带 ArcWeapon 的狗没有这个问题——它的行为本来就是"点一下放一次"。

⇒ 推论：**想稳定用蓄力类武器，应该让"本来就会用 ArcWeapon 的狗"来承载**（即下一轮换 K-9 的理由）。

## 13 第六轮：K-9 当蓄力载体 + 首次试**主武器/副武器**（2026-10-26 22:5x 已装，`⚠`）

用户指令：① 换用本来就带 `ArcWeapon` 的 **AX/ARC-3 K-9** 承载 ARC-3；
② Guard Dog 换**主武器** PLAS-1 Scorcher、Hot Dog 换**副武器** P-19 Redeemer（此前只测过支援武器）。

| 狗 | 无人机 | 挂的 donor | 类别 | 资源 |
|---|---|---|---|---|
| **K-9**（AX/ARC-3）| `0x4B071633584E4594` | **ARC-3** `0x96DE9CD50F7306E6`（原挂自身弧武器 `0xA0532C36…`）| 玩家支援·蓄力 | patch_19 |
| **Guard Dog** | `0xA0FF2F9A0CA6992A` | **PLAS-1 Scorcher** `0xEEA5E3CEF1E12C14` | **主武器**（等离子）| **patch_20** |
| **Hot Dog** | `0x979E9BC6D48D1FC6` | **P-19 Redeemer** `0x3575AABC5F1F9326` | **副武器**（连发手枪）| **patch_21** |
| Rover | `0x5BEEC97F4C7F4AE9` | ARC-3（保留，行为已改 192）| — | patch_19 |
| Dog Breath | `0xB9BAF571FC8F9959` | ARC-3（保留，行为 190）| — | patch_19 |

**新增驻留（均已装盘）**

| donor | 包 | 包内资源 | toc / gpu / stream | 补丁 |
|---|---|---|---:|---|
| **PLAS-1 Scorcher** `0xEEA5E3CE…` | `0xC51F160470B34AE3` | 76 条（texture28/material17/particles9/mesh7/physics4/anim4/bones2…）| 6.54 / 10.96 / 4.30 MB | **patch_20** |
| **P-19 Redeemer** `0x3575AABC…` | `0x99F20DF1C4CF885A` | 46 条（texture17/anim8/material7/mesh5/bones2/physics2…）| 2.09 / 4.98 / 3.93 MB | **patch_21** |

**判读**

| K-9（弧）| Guard Dog（PLAS-1）| Hot Dog（P-19）| 结论 |
|---|---|---|---|
| 稳定放电（不再缺视线才放）| — | — | **载体行为决定蓄力武器可用性** `✓✓`：以后蓄力/点射类一律挂 K-9 或实弹狗 |
| 仍只在丢视线时放 | — | — | 说明问题不在行为，而在 `ArcWeapon` 需要**玩家手部输入**（无人机无此输入）|
| — | 能打 | 能打 | **主武器 / 副武器也能挂**（此前只验证过支援武器）⇒ 挂载池覆盖全部武器槽 |
| — | 能打但不装填 | — | 主/副武器需要 `WeaponMagazine` + 狗装填循环；看 Guard Dog（有装填）表现 |
| — | 紫问号 | 紫问号 | 包没驻留成功（不该发生，本轮已驻留）⇒ 查 patch_20/21 是否被游戏接受 |

**装盘**：entities = `out/dogs/j1c.dl_bin`（md5 `be3c3d05cd272a120938429ce7c731b5`）；patch_18/19/20/21 全部保持安装。
**回滚**：entities 回 `out/bkval/p1e.dl_bin`；要减体积可只删 patch_18…21 里不用的那几对文件。

### 13.1 第六轮结果：主武器通吃、蓄力武器到此为止（2026-10-26 23:0x，`✓✓` / `✗`）

| 狗 | 挂的 | 实机结果 | 读数 |
|---|---|---|---|
| **Guard Dog** | **PLAS-1 Scorcher（主武器）** | **能打，正常装填** | **主武器也能挂、装填循环同样生效** `✓✓` |
| **K-9**（天生带 ArcWeapon）| **ARC-3** | **仍只在丢视线时放** | **换成本来会放电弧的狗也没用** ⇒ 不是"载体行为"单一原因 |
| **Hot Dog**（行为 189 喷火）| **P-19 Redeemer（副武器）** | 行为异常、**一直不开火** | 副武器在喷火行为下不工作 |

**ARC-3 的结论（`✗` 否证到根）**：连原生带 `ArcWeapon` 的 K-9 都只能在丢视线时放电
⇒ `ArcWeapon` 的"蓄力—松手"要的是**玩家手部的扳机释放事件**，无人机 AI 没有这个事件流。
⇒ **蓄力类武器不能挂给无人机**（数据层无解；除非改 AIBEH 的输入源，超出数据表范围）。

## 14 第七轮：只改 Guard Dog —— 副武器 P-19 单变量（2026-10-26 23:1x 已装，`⚠`）

用户要求本轮只动 **Guard Dog** 一只（矩阵设计取消），其余狗全部恢复到**原版武器**：

| 狗 | `BehaviorId` | Mount+0x00 | 状态 |
|---|---|---|---|
| **Guard Dog** | 192 | **P-19 Redeemer `0x3575AABC5F1F9326`** | **本轮唯一改动**（原挂自身 AR-23 实弹，资源由 **patch_21** 驻留）|
| Hot Dog | 189 | `0x65CD4325BA23F3C6` | 原版 |
| Dog Breath | 190 | `0xB729A2BA153BCAED` | 原版 |
| K-9 | 191 | `0xA0532C3616528CBF` | 原版 |
| Rover | 191 | `0x2C66C201B2543D2C` | 原版 |

**判读（单变量）**

| Guard Dog 现象 | 结论 |
|---|---|
| **能打 + 能装填** | **副武器可挂**，且走 Guard Dog 的装填循环 ⇒ 武器槽覆盖：支援武器 ✓✓ / 主武器 ✓✓ / 副武器 ✓✓ |
| 能打但**不装填** | 副武器的弹药循环与狗装填不匹配（`WeaponMagazine` 差异）⇒ 只能当"一次性弹药"用 |
| **紫问号** | 驻留没被接受（patch_21）⇒ 查补丁是否被游戏加载 |
| 行为怪/不开火 | 副武器需要"点射"输入而 AIBEH 给的是"按住"（与 ARC-3 同类问题）⇒ 副武器白名单限 Guard Dog 行为 |

**装盘**：entities = `out/dogs/l1.dl_bin`（md5 `de3567c727f871e8e152dc0eb00352bc`，47,259,504 B）；patch_18–21 保持安装。
**回滚**：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`（= 只保留背包数值改动）。

### 14.1 结果：副武器挂在 Guard Dog 上**仍然不开火**（2026-10-26 23:2x，`✗`）

| 狗 | 挂的 | 结果 |
|---|---|---|
| Guard Dog（行为 192，有装填）| **P-19 Redeemer（副武器）** | **模型正常、不开火** |

用户判断（`⚠` 合理）：**开发者大概率没给"副武器挂载"做适配**；而且 P-19 本身是**全自动**武器，
按"按住扳机"的 AIBEH 逻辑本该能连发 ⇒ 更像**武器槽白名单**问题（支援武器 ✓ / 主武器 ✓ / 副武器 ✗），
而不是"点射 vs 按住"的输入类型问题（ARC-3 才是后者）。

## 15 第八轮：锁定武器 —— StA-X3 W.A.S.P. Launcher（2026-10-26 23:2x 已装，`⚠`）

用户想看看"**装上锁定武器会是什么行为**"。

| 项 | 值 |
|---|---|
| 目标件 | **W.A.S.P. Launcher `StA-X3`** 实体 `0xCC786F6491FE7E65`（背包 `0xB8FEB0CC191C1EF3` 不动）|
| 挂到 | **Guard Dog** 无人机 `0xA0FF2F9A0CA6992A`（行为 192，唯一改动；其余狗原版）|
| 驻留 | 包 `0x5795E99A988D10B7`（54 条：texture17 / material9 / bones6 / mesh6 / anim5 / particles4 / physics3 / state_machine2）→ **patch_22** |

**为什么值得测**：W.A.S.P. 的组件表里有 **`GuidanceTarget`（锁定/制导）**、`SensorEye`、`EntityBind`、`WeaponAssistedReload`；
而无人机本身就有 `Targeting` / `MultiTarget` / `SensorEye` / `Detector`。
⇒ 要么**无人机自己的索敌顶替了玩家的锁定输入**（能锁定开火），要么**制导武器要玩家锁定事件**（同 ARC-3 的"缺输入"）。

**判读**

| 现象 | 结论 |
|---|---|
| 正常锁定 + 发射 | 锁定武器可用（无人机的 `Targeting` 顶上玩家输入）⇒ 制导类进白名单 |
| 有锁定动作但不发射 | 制导要玩家扳机事件（同 ARC-3 的缺输入），无人机只做"瞄准"不做"确认发射"|
| 不锁定、直射/乱射 | `GuidanceTarget` 失效但弹道仍在 ⇒ 当普通火箭用 |
| **紫问号** | 驻留没生效（patch_22）⇒ 查补丁加载 |
| 崩溃 | `GuidanceTarget` 与无人机 `Targeting`/`MultiTarget` 冲突 ⇒ 记录为"不能挂" |

**装盘**：entities = `out/dogs/m1.dl_bin`（md5 `7ab6d4d1515a83db1e2877c8cc115af2`）；patch_18–22 保持安装。
**回滚**：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`。

### 15.1 结果：锁定武器**完全可用**（2026-10-26 23:2x，`✓✓`）

| 狗 | 挂的 | 结果 |
|---|---|---|
| Guard Dog | **StA-X3 W.A.S.P.** | **正常锁定 + 发射**；**只对原武器能锁定的敌人发射** |

读数：
- 无人机的 `Targeting`/`MultiTarget`/`SensorEye`/`Detector` **顶替了玩家的锁定输入** ⇒ 制导类武器可以直接挂 `✓✓`。
- **可锁定目标集仍然继承武器自己的 `GuidanceTarget` 配置**（我们之前锁在线就已知"目标集合不在明文"）⇒ 换枪不改变"能锁谁"。
  这既是限制也是好消息：**挂 W.A.S.P. 不会让它锁到本不该锁的东西**。

## 16 第九轮：蓄力但**自动发射**的 LAS-99 Quasar Cannon（2026-10-26 23:3x 已装，`⚠`）

用户的判断很关键：Quasar 同样是蓄力武器，但**蓄满自动发射、不需要松手** ⇒ 如果它能打，
就把 ARC-3 的失败干净地归因到"**需要松手**"而不是"蓄力"。

| 项 | 值 |
|---|---|
| 目标件 | **LAS-99 Quasar Cannon** `0x35A61296619CC47E`（23 个组件：`WeaponHeat`+`ProjectileWeapon`+`WeaponData`+`EffectReference`+`StatusEffectReceiver`…）|
| 挂到 | **Guard Dog** `0xA0FF2F9A0CA6992A`（行为 192，唯一改动；其余狗原版）|
| 驻留 | 包 `0xCF1ACDE501CCFA1B`（71 条：texture19 / material19 / particles13 / mesh5 / anim4 / physics3 / bones2 / state_machine2）→ **patch_23** |

**三态对照（同一把"蓄力"族，区别只在释放方式）**

| 武器 | 蓄力后 | 实机 |
|---|---|---|
| ARC-3 电弧 | **要松手**才放 | ✗ 只在丢视线（AI 松手）时放 |
| Quasar LAS-99 | **蓄满自动放** | 本轮测 |
| W.A.S.P. | 锁定即放 | ✓✓ 正常 |

**判读**

| Quasar 现象 | 结论 |
|---|---|
| 蓄力后**自动发射**、能装填/冷却 | **"松手"就是 ARC-3 失败的唯一原因** `✓✓`；蓄力类武器只要"自动释放"就能上无人机 |
| 蓄力但永不发射 | 蓄力释放都依赖玩家输入 ⇒ 无人机与所有蓄力武器无缘 |
| 蓄力特效都没有 | `WeaponHeat` 的蓄力流程需要手部 wielder 状态机 ⇒ 资源层耦合 |
| 紫问号 | patch_23 未生效 |

**装盘**：entities = `out/dogs/n1.dl_bin`（md5 `6aa784a3263022bccc9a6d2ff7681f5c`）；patch_18–23 保持安装。
**回滚**：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`。

### 16.1 结果：Quasar **正常开火** ⇒ ARC-3 的病因定死（2026-10-26 23:3x，`✓✓`）

LAS-99 Quasar Cannon（蓄力、**蓄满自动发射**）挂在 Guard Dog 上**正常开火**。

⇒ **ARC-3 失败的唯一原因就是"需要松手"**：AI 只提供"按住扳机"，不提供"释放事件"；
只要武器是**自动释放**（Quasar）、**锁定即放**（W.A.S.P.）或**按住连发**（实弹），无人机都能用。

## 17 收尾：AX 狗背包"换枪"线结项（2026-10-26 23:4x）

### 17.1 一句话配方

> **改无人机实体的 `MountComponentData+0x00`（u64）= 想挂的 item 实体 id。就这一个字段。**

```bash
python tools/entity_field_set.py set --block 0x3845B1E0 --key <无人机实体>     --field 0x00 --type u64 --value <donor 实体 id> --expect-old <原值>     --plain <base>.plain --out <next>.plain
```

### 17.2 三条硬规则（全部实测）

| 规则 | 内容 | 违反的后果 |
|---|---|---|
| **R1 资源** | donor 的**包必须在场**。不在场就紫问号 | 紫问号。解法：`whole_package_patch.py build --package <LoadoutPackage+0x08> --host f6fb08cc02d24255 --install`（整包驻留）|
| **R2 载体** | 载体决定**能不能装填**：Guard Dog(192) 通用；Hot Dog(189)/Dog Breath(190) 也有装填；Rover(191)/K-9(191) **无**装填（原生无限弹药）| 有限弹药武器打完不换弹 |
| **R3 开火输入** | AI 只给"**按住扳机**"，不给"**松手**" | 需要松手才释放的武器（ARC-3）只在丢视线时误放 |

### 17.3 白名单 / 黑名单账本（全部实机）

| 类别 | donor | 结果 |
|---|---|---|
| 支援·实弹 | **MG-43** `0x11C27D3BABB38956` | **✓✓** 开火 + 装填（第一把验证）|
| 支援·实弹（重）| **AC-8** `0xA8CFFB316F0B5C5F` | **✓✓** 开火 + 装填（驻留后）|
| 支援·锁定 | **W.A.S.P.** `0xCC786F6491FE7E65` | **✓✓** 正常锁定 + 发射；**可锁目标集继承武器自身 `GuidanceTarget`** |
| 支援·蓄力自动放 | **Quasar LAS-99** `0x35A61296619CC47E` | **✓✓** 正常开火 |
| 主武器 | **PLAS-1 Scorcher** `0xEEA5E3CEF1E12C14` | **✓✓** 开火 + 装填 |
| 炮塔件 | `shuttle_gunship_turret_hmg` `0x8365609B35EF6672` | **✓✓** 正常（挂在 Hot Dog 上）|
| 支援·蓄力需松手 | **ARC-3** `0x96DE9CD50F7306E6` | **✗** 只在丢视线时放 |
| 副武器 | **P-19 Redeemer** `0x3575AABC5F1F9326` | **✗** 不开火（槽位不适配；连全自动都不行）|
| 原生池 NPC 武器 | `soldier_machinegun` `0x2ED3696E12A14D4C` | ⚠ 紫问号（**包不在场**，与形状无关）|

### 17.4 载体映射（实测钉死）

| 狗 | 无人机实体 | `BehaviorId` | 换弹 |
|---|---|---|---|
| Guard Dog | `0xA0FF2F9A0CA6992A` | 192 | **有** |
| Rover | `0x5BEEC97F4C7F4AE9` | 191 | 无 |
| Hot Dog | `0x979E9BC6D48D1FC6` | 189 | **有** |
| Dog Breath | `0xB9BAF571FC8F9959`（排除法推定，`⚠`）| 190 | **有** |
| K-9 | `0x4B071633584E4594` | 191 | 无 |

### 17.5 没解出来的（留档，别再踩）

1. **背包 → 无人机**的生成引用**不在实体表**（对 7 个背包 id / 10 个无人机 id 做 u64 xref 全是负结果）⇒ 在资产/引擎侧，和"跳跃能力不能移植"同构。
2. **可锁目标集**写在武器自己的 `GuidanceTarget` 配置里，非明文可改（与 LOCKON 线结论一致）⇒ 换枪不改变"能锁谁"。
3. **副武器为什么不适配**未定位（怀疑是武器槽白名单，非输入类型问题——P-19 是全自动仍不打）。

### 17.6 复原状态（已执行）

| 项 | 状态 |
|---|---|
| `data/game/generated_entities.dl_bin` | **`out/bkval/p1e.dl_bin`**（md5 `4f60109d34b6c315e3e1fc6b964507f6`）= 原版 + rack 47 暗液体 + 已验证的背包数值改动；**无任何狗换枪** |
| `data/game/generated_stratagem_settings.dl_bin` | **原版**（md5 `168f2711620f07533f55a9480506d69f`）|
| 实验驻留包 | `patch_18`–`patch_23`（6 个包，约 100 MB）**已从 `data/` 移除**；产物留档在 `out/res-{ac8,arc3,plas1,p19,wasp,quasar}/`，要复现直接拷回 `data/` |
| 补丁序号 | `patch_0`–`patch_17` 保持连续（17 = 暗液体包）|

**复现任意一轮**：`out/dogs/` 里对应的 `*.plain` → `dlbin_seal.py seal-key` → 拷进 `data/game/`（需要不紫问号就同时把对应 `out/res-*/` 的三件套拷回 `data/`）。
