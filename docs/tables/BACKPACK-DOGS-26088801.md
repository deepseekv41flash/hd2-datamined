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

## 18 第十轮：副武器 + 制导 —— P-92 Warrant 交叉验证（2026-10-27 13:1x 已装，`⚠`）

社区反馈：**给 Guard Dog 挂副武器 P-92 Warrant 可以正常使用**，理由是"它是锁定类武器"。
我方此前实测 **P-19 Redeemer（副武器）✗ 不开火**。两条信息合起来，数据层给了一个很干净的解释：

| 武器 | 槽位 | `GuidanceTarget` | 实机 |
|---|---|---|---|
| **P-19 Redeemer** `0x3575AABC5F1F9326` | 副武器 | **无** | **✗ 不开火**（已实测）|
| **P-92 Warrant** `0xCF8934FF6567A42D` | 副武器 | **有** | 社区称可用（本轮验证）|
| StA-X3 W.A.S.P. `0xCC786F6491FE7E65` | 支援 | **有** | **✓✓ 正常锁定+发射**（已实测）|

⇒ 假设（`⚠`）：**制导类武器把"瞄准/确认"交给无人机的 `Targeting`/`MultiTarget`，自己不需要玩家输入**，
所以能绕过"副武器在无人机上不开火"的问题；而普通副武器（P-19，全自动）仍卡住。
两件事可能是**叠加**的（槽位不适配 + 制导补偿），本轮就是把这两个变量交叉验证。

| 项 | 值 |
|---|---|
| 目标件 | **P-92 Warrant** `0xCF8934FF6567A42D`（23 个组件，含 `GuidanceTarget`+`SensorEye`）|
| 挂到 | **Guard Dog** `0xA0FF2F9A0CA6992A`（唯一改动；其余狗原版）|
| 驻留 | 包 `0x5D5C93EF05A46880`（39 条：texture12 / animation10 / material5 / mesh4 / physics2 / particles2 / bones1 / wwise_bank1 / state_machine1）→ **patch_18** |

**判读**

| 现象 | 结论 |
|---|---|
| **能打** | 副武器**不是硬门槛**，制导确实能救 ⇒ 白名单增加"制导副武器"，社区说法成立 |
| 有锁定动作但不发射 | 与 ARC-3 同类：制导也要"确认发射"事件，无人机给不了 |
| 完全不开火/无锁定 | 副武器槽是硬门槛 ⇒ 社区的案例另有条件（可能他们改的不是同一架无人机，或同时改了别的件）|
| 紫问号 | patch_18 未生效 |

**装盘**：entities = `out/dogs/p92.dl_bin`（md5 `f8d67bea4a649a8e7df2bc4b81cc5977`）；patch_18 = P-92 包。
**回滚**：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin` + 删 `patch_18` 三件套。

### 18.1 结果：P-92 Warrant **真能打** ⇒ 副武器槽不是硬门槛（2026-10-27 13:1x，`✓✓`）

| 武器 | 槽位 | `GuidanceTarget` | 实机 |
|---|---|---|---|
| P-19 Redeemer | 副武器 | 无 | ✗ 不开火 |
| **P-92 Warrant** | 副武器 | **有** | **✓✓ 能打**（社区说法成立）|
| StA-X3 W.A.S.P. | 支援 | 有 | ✓✓ 锁定+发射 |

⇒ 制导假说目前 **3/3 吻合**；同时否掉了"副武器一律不适配"的粗判据（P-19 是**个例**，不是槽位通例）。

## 19 第十一轮：四只狗 × 四把**无制导**副武器（2026-10-27 13:2x 已装，`⚠`）

这是判决"制导到底是不是判据"的实验：四把副武器**全都没有 `GuidanceTarget`**，
若"制导"是真判据 ⇒ 四只狗应当**全部不开火**；只要有一把能打，就说明 P-19/P-92 的差异另有原因。

| 狗 | 无人机 | 挂的副武器 | `GuidanceTarget` | 驻留补丁 |
|---|---|---|---|---|
| **Rover** | `0x5BEEC97F4C7F4AE9` | **LAS-7 Dagger** `0x7B06196E90154C88`（激光手枪）| **无** | patch_19（包 `82DCD83D81A385F3`，68 条）|
| **Guard Dog** | `0xA0FF2F9A0CA6992A` | **P/40-K Bolt Pistol** `0xDBB6C961C59FADC1` | **无** | patch_20（包 `9514615D563612F1`，34 条）|
| **Hot Dog** | `0x979E9BC6D48D1FC6` | **P-72 Crisper** `0x3F92BA65EF65CCA9`（喷火手枪）| **无** | patch_21（包 `41CE78FE8F96BEBE`，25 条）|
| **Dog Breath** | `0xB9BAF571FC8F9959` | **PLAS-15 Loyalist** `0xAA69A60D74A3EC54`（等离子手枪）| **无** | patch_22（包 `9EFFC1C882578BAF`，52 条）|
| K-9 | `0x4B071633584E4594` | 原版电弧（对照，未动）| — | — |

**判读**

| Rover(Dagger) | GD(Bolt) | HD(Crisper) | DB(Loyalist) | 结论 |
|---|---|---|---|---|
| ✗ | ✗ | ✗ | ✗ | **制导就是判据** `✓✓`：无制导副武器一律不发射（P-19 不是特例，是通例）|
| 任意一把能打 | | | | 制导不是判据 ⇒ 差异在别处（下一候选：`WeaponMagazine`/`ProjectileWeapon` 的 wielder 槽、或该枪的 `EquipmentType` 类别）|
| 有锁定/瞄准动作但不发射 | | | | 同 ARC-3：缺"确认发射"事件 |
| 紫问号 | | | | 对应 patch_N 未生效 |

**装盘**：entities = `out/dogs/q4.dl_bin`（md5 `4543d8b918cf917ee96d6323e1c70709`）；
驻留 patch_18（上一轮 P-92）+ patch_19–22（本轮四把），盘上补丁现在到 `patch_22`。
**回滚**：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`；删 patch_18–22 可回收本轮体积。

### 19.1 结果：**四把无制导副武器全都能打** ⇒ 制导假说否证、槽位假说否证（2026-10-27 13:3x，`✗✗`）

| 狗 | 挂的 | `GuidanceTarget` | 实机 |
|---|---|---|---|
| Rover | LAS-7 Dagger | 无 | **✓** |
| Guard Dog | P/40-K Bolt Pistol | 无 | **✓** |
| Hot Dog | P-72 Crisper | 无 | **✓** |
| Dog Breath | PLAS-15 Loyalist | 无 | **✓** |

两条假设同时被推翻：
- **✗ 制导不是判据**（四把无制导副武器全开火）；
- **✗ 副武器槽不适配也不成立**（副武器在四只狗上都能用）。

⇒ **P-19 Redeemer 是孤例**（唯一测过"渲染正常、死活不开火"的武器）。问题从"副武器能不能挂"收缩成
**"P-19 为什么不工作"**，候选：`WeaponMagazine`（全自动、大弹匣）、`ProjectileWeapon` 的 wielder 槽、
`EquipmentType` 类别、`WeaponData+0x184`（fnid）。本轮把 P-19 重新挂到 **K-9** 上复测，先排除"上轮是配置/驻留问题"。

## 20 第十二轮：四把新副武器 + P-19 复测（2026-10-27 13:3x 已装，`⚠`）

| 狗 | 无人机 | 挂的副武器 | 驻留 | 备注 |
|---|---|---|---|---|
| **Rover** | `0x5BEEC97F4C7F4AE9` | **LAS-58 Talon** `0x416D053372C4E433` | **复用 patch_19**（与 Dagger 同包 `82dcd83d81a385f3`）| 同厂同包，省一个补丁 |
| **Guard Dog** | `0xA0FF2F9A0CA6992A` | **P-113 Verdict** `0x1A437158E1B8D2A1` | patch_23（包 `b47514ae19a494f0`，36 条）| |
| **Hot Dog** | `0x979E9BC6D48D1FC6` | **P-69 Veto** `0xC780BCD79547DA0F` | patch_24（包 `58038f21c4334481`，41 条）| |
| **Dog Breath** | `0xB9BAF571FC8F9959` | **P-44 Mist** `0x027DEC442CC26A90` | patch_25（包 `7160179c08dd7d81`，44 条）| |
| **K-9** | `0x4B071633584E4594` | **P-19 Redeemer** `0x3575AABC5F1F9326` | patch_26（包 `99f20df1c4cf885a`，46 条）| **孤例复测**（原挂电弧）|

**判读**

| 四把新副武器 | K-9 上的 P-19 | 结论 |
|---|---|---|
| 全都能打 | **还是不开火** | P-19 确实是**个体问题** ⇒ 下一轮做"P-19 换本体检定"（把它的 `ProjectileWeapon`/`WeaponMagazine` 行与能打的副武器逐字段对比）|
| 全都能打 | **这次能打** | 上轮是环境问题（驻留/加载时序）⇒ 结论要改写，副武器全线无坑 |
| 有不能打的 | — | 副武器内部还有分类差异（按不能打那把的组件去找共同点）|

**装盘**：entities = `out/dogs/r5.dl_bin`（md5 `a5765df1639fad5822922f43dd06ccd0`）；
盘上驻留补丁 `patch_18`–`patch_26`（9 个实验包，连续）。回滚同上（`cp out/bkval/p1e.dl_bin …`）。

### 20.1 结果：四把新副武器**也全都能打**（2026-10-27 13:4x，`✓✓`）

LAS-58 Talon / P-113 Verdict / P-69 Veto / P-44 Mist —— **四把全部正常开火**（K-9 上的 P-19 本轮没测）。

⇒ 到这一轮为止，**副武器在无人机上已是常态可用**（累计 9 把副武器 ✓：P-92、Dagger、Bolt、Crisper、Loyalist、Talon、Verdict、Veto、Mist），
唯一的例外仍然只有 **P-19 Redeemer**。所以结论进一步收紧成一句话：
**"副武器能不能挂"这个问题已经不存在了；剩下的唯一问题是 P-19 个体为什么不工作。**

## 21 第十三轮：三把新副武器（含散弹手枪）+ P-19 复测（2026-10-27 13:4x 已装，`⚠`）

| 狗 | 无人机 | 挂的副武器 | 驻留 | 备注 |
|---|---|---|---|---|
| **Rover** | `0x5BEEC97F4C7F4AE9` | **P-2 Peacemaker** `0x05E4E5C2DB6E44A2` | patch_27（包 `bf2250de0b17285c`，41 条）| |
| **Guard Dog** | `0xA0FF2F9A0CA6992A` | **P-4 Senator** `0x8D3D52A3B2F19402` | patch_28（包 `94b554570b12c088`，42 条）| |
| **Hot Dog** | `0x979E9BC6D48D1FC6` | **SG-22 Bushwhacker** `0x2B28E17FFED05F7C` | patch_29（包 `2350348a9acf49c4`，39 条）| **散弹手枪**（首次测非"单发/连发枪"族的副武器）|
| **Dog Breath** | `0xB9BAF571FC8F9959` | **P-19 Redeemer** `0x3575AABC5F1F9326` | **复用 patch_26**（包 `99f20df1c4cf885a`）| **孤例复测（换载体）** |
| K-9 | `0x4B071633584E4594` | 原版电弧（对照，未动）| — | — |

**判读**

| Bushwhacker（散弹）| P-19（在 Dog Breath 上）| 结论 |
|---|---|---|
| 能打 | **还是不开火** | 副武器全族可用 + **P-19 是稳定复现的个体问题** ⇒ 进入"本体检定"：拿 P-19 的 `ProjectileWeapon`/`WeaponMagazine`/`WeaponData` 行与能打的那 9 把逐字段 diff |
| 能打 | **这次能打** | 上一轮 P-19 失败可能是**载体相关**（Guard Dog 上不行 / 别的狗上可以）⇒ 记"P-19 需要特定载体" |
| 不能打 | — | 散弹族在无人机上不工作（`SprayWeapon`/多弹丸 path 差异）⇒ 补一条族级否证 |

**装盘**：entities = `out/dogs/s4.dl_bin`（md5 `602f2cad3214ee4c53631640e61a7c18`）；盘上驻留补丁 `patch_18`–`patch_29`（12 个实验包，连续）。
**回滚**：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`；实验补丁可整段删除回收体积（`patch_18`–`patch_29`）。

### 21.1 结果：两通两不通，**载体行为（AIBEH）成了主线**（2026-10-27 14:0x，`✓✓`+`✗`）

| 狗 | `BehaviorId` | 挂的 | 实机 |
|---|---|---|---|
| **Hot Dog** | **189** | SG-22 Bushwhacker（散弹手枪）| **✓** |
| **Guard Dog** | **192** | P-4 Senator | **✓** |
| **Rover** | **191** | P-2 Peacemaker | **✗ 不开火** |
| **Dog Breath** | **190** | P-19 Redeemer | **✗ 不开火** |

**用户归因（`⚠` 合理，与已有记录一致）**：
1. **Rover（191 = 光束狗）带实弹武器可能不发射** —— 与 ARC-3 那轮"只在丢视线时放"、以及本轮 P-2 沉默一致；
2. **Dog Breath（190）有"给敌人挂中毒效果然后不打"的特性**（制作组更新日志提过）⇒ **不适合当测试载体，停用**；
3. **稳定载体收敛为 Guard Dog(192) + Hot Dog(189)**（这两只到现在为止对每一个 donor 都能打）。

**载体 × 实弹 donor 账本（累计）**

| `BehaviorId` | 狗 | 实弹/锁定/蓄力类 donor 表现 |
|---|---|---|
| **192** | **Guard Dog** | **✓** MG-43 · AC-8 · PLAS-1 · W.A.S.P. · Quasar · P-92 · Dagger · Bolt · Verdict · Senator |
| **189** | **Hot Dog** | **✓** gunship HMG 炮塔 · Crisper · Bushwhacker |
| **191** | Rover / K-9 | **✗** 实弹：Rover+P-2 不打、ARC-3 只在丢视线放；K-9+ARC-3 同 |
| **190** | Dog Breath | 中毒特性（不打），停用 |

⇒ 这一轮把之前"某把枪在某个载体上失败"的混乱解释清了大半：**载体行为比武器型号更重要**。
唯一还没归位的仍是被怀疑的 **P-19 Redeemer**。

## 22 第十四轮：四只载体**全带 P-19**（2026-10-27 14:1x 已装，`⚠`）

设计：同一把 P-19 同时挂到 **Rover(191) / Guard Dog(192) / Hot Dog(189) / K-9(191)** —— 这是"P-19 到底有没有问题"的判决轮，
因为 192 与 189 已被证明是万能载体。

| 狗 | `BehaviorId` | 挂的 | 驻留 |
|---|---|---|---|
| Rover `0x5BEEC97F4C7F4AE9` | 191 | **P-19 Redeemer** `0x3575AABC5F1F9326` | patch_26（复用）|
| Guard Dog `0xA0FF2F9A0CA6992A` | 192 | **P-19** | patch_26 |
| Hot Dog `0x979E9BC6D48D1FC6` | 189 | **P-19** | patch_26 |
| K-9 `0x4B071633584E4594` | 191 | **P-19** | patch_26 |

**判读**

| Guard Dog(192) | Hot Dog(189) | Rover/K-9(191) | 结论 |
|---|---|---|---|
| ✗ | ✗ | ✗ | **P-19 本体问题**定死（两个万能载体也不打）⇒ 下一轮做"P-19 vs 能打副武器"逐字段 diff |
| ✓ | ✓ | ✗ | **P-19 没问题**；之前 GD 上的失败是**那一次的环境/时序**问题 ⇒ 结论改写为"191 载体才是门槛" |
| ✓ | ✓ | ✓ | 之前的失败全部是环境问题 ⇒ 副武器/载体矩阵已完成，收线 |

**装盘**：entities = `out/dogs/t4.dl_bin`（md5 `64f10eacfeada51e700dad318ea22f59`）；
驻留仍为 `patch_18`–`patch_29`（P-19 用 patch_26）。回滚：`cp out/bkval/p1e.dl_bin <game>/data/game/generated_entities.dl_bin`。

### 22.1 结果：四只载体全都不行 ⇒ P-19 本体问题定死 + 关键新线索（2026-10-27 14:1x，`✗`）

Rover / Guard Dog / Hot Dog / K-9 四只载体挂 P-19 **全部不开火**（含两个万能载体 192/189）
⇒ **P-19 是纯个体问题**，与载体无关。同时用户给了一条更硬的观察：

> **P-19 的弹匣模型在所有无人机上都不渲染**，怀疑"没弹匣 ⇒ 不能开火"。

**数据层对照（`✓` 全表现算，本 build）**

| 武器 | `ProjectileWeapon+0x000`（弹丸 type）| `WeaponCustomization+0x80`（弹匣/定制引用）| 实机 |
|---|---|---|---|
| **P-19 Redeemer** | **0** | **0** | **✗** |
| P-4 Senator | **0** | `0xB96CC3B704A76464` | ✓ |
| P-92 Warrant | 331 | `0xFC1F0A3B3FC97238` | ✓ |
| P/40-K Bolt | 205 | `0x619795F79CEDA1B3` | ✓ |
| P-113 Verdict | 16 | `0x005C2262F672CAF4` | ✓ |
| P-69 Veto | 241 | **0** | ✓ |
| LAS-58 Talon | 146 | `0xE53E4B0C20563D21` | ✓ |
| P-44 Mist | 167 | `0x1D908F18A11708E6` | ✓ |

**读出来的机理（`⚠` 强假设）**：武器的弹丸有两个来源 ——
① `ProjectileWeapon+0x000` 直给；② 走**弹匣/定制引用**（`WeaponCustomization+0x80`）解析。
P-19 是**唯一两个都空**的武器（`+0x000 = 0` 且 `+0x80 = 0`）⇒ 无人机 AI 拿不到弹丸类型 ⇒ 不发射，
弹匣模型也因为没有引用而不渲染。Senator 虽然 `+0x000 = 0`，但 `+0x80` 有效，所以能打；Veto 反之。

## 23 第十五轮：给 P-19 补一个弹丸 type（2026-10-27 14:1x 已装，`⚠`）

**单变量**：只把 `P-19` 的 `ProjectileWeaponComponentData+0x000` 从 **0 → 205**（205 = P/40-K Bolt 的弹丸 type，已被证明能在无人机上打）。

| 项 | 值 |
|---|---|
| 改动 | `ProjectileWeaponComponentData`（块 `0x45171B68`）键 `0x3575AABC5F1F9326` `+0x000` u32：**0 → 205** |
| 载体 | 四只狗都不变（Rover/GuardDog/HotDog/K-9 全挂 P-19，行为 191/192/189/191）|
| entities | `out/dogs/u1.dl_bin`（md5 `3ca381cc7be9f11bcecd1cf2f15a7ad0`）|

**判读**

| 现象 | 结论 |
|---|---|
| **能开火** | 假设成立 `✓✓`：P-19 缺的就是"弹丸来源"，补一个就能用；顺带说明**"弹匣模型不渲染"是同一根因的症状** |
| 能打但**弹匣仍不渲染** | 弹丸来源与弹匣模型是两件事（模型另有引用，可能是 `+0x80`）|
| 仍不开火 | 弹丸不是唯一条件 ⇒ 下一候选：给 `WeaponCustomization+0x80` 写一个有效引用（照抄 Senator 的）|
| 崩/异常 | 弹丸 type 与 P-19 的 `WeaponData`/弹匣不匹配（205 是 Bolt 的弹丸）⇒ 换成 P-19 自己的弹丸 type（需另找）|

**回滚**：`cp out/dogs/t4.dl_bin <game>/data/game/generated_entities.dl_bin`（回到"P-19 原值 + 四载体"状态）。

### 23.1 P-19 是否"多份数据"？答：**不是** —— 缺的是**弹匣资源引用**（2026-10-27 14:2x，`✓` 离线）

**① "假 P-19 / 多份副本"假设 → 否证。**
- 全表里 **共用 P-19 同一张壳**（`Unit+0x00 = 0x3575AABC5F1F9326`）的实体 **只有 1 个**（就是它自己）；
- 全档扫描：只有 `generated_collision_event_settings` 引用它 1 次，**没有任何第二份"只能看不能打"的 P-19**；
- 名字表里那两个"P-19 Redeemer"是**资源名**（`bones` / `physics`），不是第二份武器数据。

**② 弹丸从哪来：`ProjectileWeapon+0x000` 与 `WeaponCustomization+0x80` 两条路，P-19 两条都空。**
`WeaponCustomization+0x80` 不是普通哈希——它在资源索引里解出来是**弹匣/挂件的物理资源**：

| 武器 | `cust+0x80` | 资源类型 | 实机 |
|---|---|---|---|
| **P-19 Redeemer** | **0** | — | **✗（弹匣模型也不渲染）** |
| P/40-K Bolt | `0x619795F79CEDA1B3` | `physics` | ✓ |
| P-4 Senator | `0xB96CC3B704A76464` | `physics`（`…/equipment/sidearm_weapon/…`）| ✓ |
| LAS-58 Talon | `0xE53E4B0C20563D21` | `physics` | ✓ |
| P-44 Mist | `0x1D908F18A11708E6` | `bones` | ✓ |

**③ 关键发现：P-19 自己的包里就有一个"P-19 Redeemer"物理资源没被引用**
`0xC891ACF9E8DBDA97`（type=`physics`，name=`P-19 Redeemer`，包 `99f20df1c4cf885a`）——
这正好是 `cust+0x80` 该放的东西。⇒ **P-19 的行漏了这条弹匣引用**，所以弹匣模型不渲染、也(可能)装不上弹。

## 24 第十六轮：给 P-19 补回弹匣资源引用（2026-10-27 14:2x 已装，`⚠`）

**单变量**：`WeaponCustomizationComponentData+0x80`（u64）**0 → `0xC891ACF9E8DBDA97`**（P-19 包内自带的 `P-19 Redeemer` physics）。
其余不变（四只狗仍全挂 P-19）。entities = `out/dogs/v1.dl_bin`（md5 `e90c4e67ac3a5b4ae6e98dde08a38d44`）。

> 备用变体：上一轮把 `ProjectileWeapon+0x000` 写成 205 的版本（`out/dogs/u1.dl_bin`，md5 `3ca381cc…`）**未测**，若本轮仍失败可换它。

**判读**

| 现象 | 结论 |
|---|---|
| **弹匣模型出现 + 能开火** | 根因定死 `✓✓`：P-19 缺的是**弹匣资源引用**；"弹匣不渲染"与"不开火"同源 |
| 弹匣出现了但仍不开火 | 弹匣引用解决了渲染，但弹丸仍要来自 `Proj+0x000` ⇒ 叠加 205 才是完整配方 |
| 一切照旧 | `cust+0x80` 不是弹匣/装填的入口 ⇒ 转"弹匣实体"路线（照 Guard Dog Magazine 那种独立 item）|

**回滚**：`cp out/dogs/t4.dl_bin <game>/data/game/generated_entities.dl_bin`。

### 24.1 结果：弹匣**出现了**，但仍不开火（2026-10-27 15:1x，`⚠` 部分成立）

补 `WeaponCustomization+0x80 = 0xC891ACF9E8DBDA97` 之后：**P-19 的弹匣模型在无人机上出现了**，
但**仍然不开火**。⇒ `cust+0x80` 是**弹匣渲染**的入口（这一半假设成立 `✓`），不是装填/弹丸的入口。

按 §24 的判读矩阵，进入下一格：**弹丸仍要来自 `Proj+0x000`** ⇒ 两条一起补。

## 25 第十七轮：弹匣引用 + 弹丸 type 双补（2026-10-27 15:1x 已装，`⚠`）

在上轮基础上**再加一条**（本次唯一新增变量）：`ProjectileWeaponComponentData+0x000`：**0 → 205**（Bolt 的弹丸）。

| 项 | 值 |
|---|---|
| 已有（上轮）| `WeaponCustomization+0x80 = 0xC891ACF9E8DBDA97`（弹匣 physics）|
| 新增（本轮）| `ProjectileWeapon+0x000 = 205` |
| 载体 | 四只狗仍全挂 P-19（Rover/GuardDog/HotDog/K-9）|
| entities | `out/dogs/w1.dl_bin`（md5 `5FEEE79A688D93DD0A1700743D4C081E`）|

**判读**

| 现象 | 结论 |
|---|---|
| **能开火** | 配方齐了 `✓✓`：**弹匣资源（渲染）+ 弹丸 type（开火）两条独立门**；P-19 在无人机上缺的正是这两样 |
| 仍不开火（且弹丸/枪口特效出现）| 弹丸路径通了但 AI 不扣扳机 ⇒ 回到 AIBEH（P-19 的 `Equipment`/`WeaponData` 里还有 AI 不认的东西）|
| 崩/异常 | 205 与 P-19 的 `WeaponData`/弹匣不匹配 ⇒ 换成 P-19 自己的弹丸（下一步：从包内资源或同名弹丸反查）|

**回滚**：`cp out/dogs/t4.dl_bin <game>/data/game/generated_entities.dl_bin`（P-19 原值 + 四载体）。

### 25.1 结果：**能开火** ⇒ P-19 根因定死（2026-10-27 15:3x，`✓✓`）

`cust+0x80`（弹匣 physics）+ `Proj+0x000 = 205` 两条一起补 ⇒ **P-19 在无人机上能开火了**。
⇒ 根因链完整：**缺弹匣资源引用 → 弹匣不渲染**；**缺 `ProjectileWeapon+0x000` 弹丸 → 不开火**。两扇门各自独立。

### 25.2 追问："P-19 自己的弹丸"到底是什么？→ 数据里**没有**（`✗` 查不到）

用户要求换成 P-19 自己的弹丸，逐条排查全档：

| 查的地方 | 结果 |
|---|---|
| `ProjectileWeapon+0x000` / `+0x240` | 原版 P-19 两处都是 **0** |
| `WeaponMagazine` / `WeaponCustomization` / `WeaponReload` 行 | 与弹丸 id 无任何对应（用 5 把已知武器的弹丸 id 反查偏移，0 命中）|
| `generated_weapon_customization_settings` / `add_resource_dependencies` | **0 次**引用 P-19 武器包或弹匣包 |
| P-19 的"弹匣包" `b15cd2256a2e677b`（hashlist `Mag` 映射：`P-19 Redeemer`）| 只有 6 条资源：**texture×3 / physics×1 / mesh×1 / material×1**，没有数据实体 |
| 实体表 | P-19 只有一份（共用同壳的实体仅它自己）|

⇒ 当时结论：**P-19 的弹丸是引擎内置默认（或运行时按武器 hash 查表），不在任何数据表里**（**`✗` 已否证，见 §28**）。
玩家侧能打，是因为玩家开火路径会走这个内置默认；无人机路径不会。

> **2026-10-27 更正（→ §28）**：它**在**数据里——不在实体记录，而在 `generated_entity_deltas.dl_bin` 的**弹种配件 delta** 里。
> P-19 的默认弹种是 `PISTOL-SMG 9x20mm. FULL METAL JACKET`（配件槽 6），它的 delta 把 `ProjectileWeapon+0` 写成 **`296`**。
> 实体记录里的 `0` 是**休眠值**：玩家建造武器时被 delta 覆盖，无人机挂载路径不跑这条链 ⇒ 才需要手工补。

**"两处都为 0"的全表普查（`✓`）**：278 个有 `ProjectileWeapon` 的实体里 **13 个**两处都是 0；其中 **11 个有 `WeaponRounds` 弹药池**（弹丸由池子给，如 Senator、Bushwhacker ✓），
**只有 2 个"既无直给弹丸、又无弹药池"**：**P-19 Redeemer** 与 **P-2 Peacemaker**（都只有 `WeaponMagazine`）。⇒ 这一对就是"必须手补弹丸"的名单。

## 26 第十八轮：改用 P-19 同族弹丸 `Pistol_9x20mm_fmj`（2026-10-27 15:3x 已装，`⚠`）

既然"自己的"弹丸不在数据里，改用**同口径候选**逐个实测，先上 9x20mm 标准弹：

| 项 | 值 |
|---|---|
| 改动 | `ProjectileWeapon+0x000`：**205（Bolt 的 12x25 热能）→ 208**（按社区枚举表 `ProjectileType_Pistol_9x20mm_fmj`）|
| 保留 | `cust+0x80 = 0xC891ACF9E8DBDA97`（弹匣渲染，已证）|
| entities | `out/dogs/x1.dl_bin`（md5 `38495098AB38A8B58B7547823C3FA152`）|

> `⚠` 枚举表的 **index ≠ type id 有反例**（Talon 的 146 在表里是 `Missile_SAM`，明显不对），所以 208 只是**首选猜测**；
> 验证办法：同一局里玩家自己带 P-19 当副武器，对比**曳光/音效/伤害**是否一致。

**判读**

| 现象 | 结论 |
|---|---|
| 手感/伤害与玩家 P-19 一致 | 208 就是 P-19 的原弹 ⇒ 配方收口 |
| 能打但**手感不同**（火/激光/伤害）| 换下一个候选：`9x20mm` 家族 `3`(pla) / `52`(hv) / `175`(rip) / `111`(tox) / `125`(exp) |
| 完全无曳光/无伤害 | 208 不是弹丸（枚举表偏移）⇒ 用二分法在 1..355 里扫（每次 1 个，看"有枪口火光"即命中）|

**回滚**：`cp out/dogs/w1.dl_bin <game>/data/game/generated_entities.dl_bin`（回到 205 版，已验证可开火）。

### 26.1 用游戏面板数据反查出 P-19 的**原生弹丸 = `296`**（2026-10-27 15:5x，`✓✓` 离线定案）

用户提供了 P-19 的弹丸面板（Size 9 mm / Mass 7 g / Initial Velocity 375 m/s / Drag 120% / Gravity 100% /
Penetration Slowdown 25% / 70 Standard · 12 Durable）。用这组数字在 **355 行 × 272 B** 的弹丸表里做指纹匹配：

| 面板字段 | 弹丸行偏移 | 命中方式 |
|---|---|---|
| Size 9 mm | `+0x18` f32 | = 9.0 |
| Initial Velocity 375 m/s | `+0x20` f32 | = 375.0 |
| Mass 7 g | `+0x24` f32 | = 7.0 |
| Drag 120% | `+0x28` f32 | = 1.2 |
| Gravity 100% | `+0x2C` f32 | = 1.0 |
| Penetration Slowdown 25% | `+0x40` f32 | = 0.25 |

**全表只有 5 个弹丸六项全中**：`296 / 167 / 218 / 288 / 241`；其中 288（drag 0.6）、241（size 12 / drag 0 / gravity 0.3）先被排除。

**再用伤害行收敛**：弹丸行 **`+60` = 伤害行 id**（DAMAGE-SETTINGS 已证）。本 build 的伤害表几何是
**base 100 / stride 76**（注意：`DAMAGE-SETTINGS` 里写的 base 44 在**本 build 偏移了**，用 44 会读出 `f32 25.0` 的垃圾，必须按"`+0` 是 1..661 全排列"重新定位）：

| 弹丸 | 伤害行 | 标准/耐久 | 判定 |
|---|---:|---|---|
| **`296`** | **80** | **70 / 12** | **= 面板数值 ⇒ 这就是 P-19 的原生弹丸** `✓✓` |
| 167 | 81 | 110 / 18 | 同族高伤变体 |
| 218 | 82 | 90 / 18 | 同族另一变体 |

⇒ **P-19 的原生弹丸 = type `296`**（9 mm / 375 m/s / 7 g / drag 1.2 / dmg 70·12）。
之前"数据里查不到"是因为它**既不在武器行、也不在弹匣行**——当时误判成"引擎内置默认"；**§28 找到了真正的引用**：
P-19 默认弹种配件的 entity delta 就是写 `ProjectileWeapon+0 = 296` 的那一步。

## 27 第十九轮：P-19 装回**原生弹丸 296**（2026-10-27 15:5x 已装 → **`✓✓` 实机通过**）

| 项 | 值 |
|---|---|
| 改动 | `ProjectileWeapon+0x000`：208（9x20mm fmj 猜测）→ **296（原生，面板数值吻合）** |
| 保留 | `cust+0x80 = 0xC891ACF9E8DBDA97`（弹匣渲染，已证）|
| 载体 | 四只狗全挂 P-19（Rover 191 / GuardDog 192 / HotDog 189 / K-9 191）|
| entities | `out/dogs/y1.dl_bin`（md5 `8D111EE35FBEAF601AA0A957CC3807F2`）|

**判读**：能开火且**手感/伤害与玩家手里那把 P-19 完全一致** ⇒ 配方收口（"无人机挂 P-19"= 弹匣资源 + 原生弹丸 296）。

### 27.1 结果：**能开火，且与玩家手里的 P-19 完全一致**（2026-10-27 16:1x，`✓✓`）

四只狗（Rover 191 / Guard Dog 192 / Hot Dog 189 / K-9 191）全挂 P-19 + `cust+0x80 = 0xC891ACF9E8DBDA97` + `Proj+0 = 296`：
**开火正常，手感/伤害与玩家自己那把 P-19 无差别**。

⇒ "无人机挂 P-19" 配方**收口**；也说明第 16 轮补的弹匣资源确实是**那一个**（`Pistol 9x20mm. Extended` 配件的 AddPath），不是随便一个 physics。
数据侧为什么这两个值就是对的 ⇒ **§28**（296 不是猜的：它就是官方默认弹种 delta 写进去的值）。

**回滚**：`cp out/dogs/x1.dl_bin <game>/data/game/generated_entities.dl_bin`（208 版）。

## 28 第二十轮：找到弹丸 `296` 的引用 —— 原版 P-19 的运行逻辑闭环（2026-10-27 16:0x，`✓✓` 离线 + 实机）

用户追问："看看有没有任何对这个弹头的引用，或许能解释原版 P-19 的运行逻辑" —— **有，而且它一句话解释了三件事**：
P-19 为什么原版能打、无人机为什么不打、我们手工补的那两个值为什么与玩家版完全一致（§27.1 已实机确认）。

### 28.1 一句话

实体记录里 `ProjectileWeapon+0 = 0` **不是缺陷，是休眠值**；P-19 的弹丸由它**默认弹种配件**（配件槽 6）的 **entity delta** 在"武器建造"时写进 `+0`。
玩家拾取/装备武器 = 走一次建造 ⇒ delta 生效 ⇒ 打 `296`；无人机挂载 = 直接读实体记录、不跑玩家武器那条 delta 链 ⇒ 读到 `0` ⇒ 不开火。

### 28.2 引用藏在哪：`generated_entity_deltas.dl_bin`

全档唯一块 `0x683E604F` = **`ComponentEntityDeltaStorage`**（352,345 B）。payload 结构（本 build 实测，`python tools/ref_scan.py delta-info` 可复现）：

| 区 | payload 内偏移 | 条数 | 每条 | 结构 |
|---|---:|---:|---:|---|
| header | `+0` | 5 组 | 80 B | 每组 `(u64 offset, u64 count)` |
| hashmap | `+0x50` | 1024 槽（572 非空）| 16 B | `{u64 AddPath, u32 settingsIndex, u32 pad}` |
| settings | `+0x4050` | 1144 | 8 B | `{u32 componentCount, u32 firstComponent}` |
| component | `+0x6410` | 1038 | 12 B | `{u32 组件索引, u32 firstDelta, u32 deltaCount}` |
| delta | `+0x94B8` | 6119 | 12 B | `{u32 成员偏移, u32 宽度, u32 data 偏移}` |
| data | `+0x1B38C` | 240,817 B | — | 被打进去的字节本身 |

**组件索引 → 组件名（本 build 实测，换 build 必须重测）**：

| 索引 | 组件 | 索引 | 组件 |
|---:|---|---:|---|
| `5` | `WeaponMagazineComponentData` | `239` | `WeaponDataComponentData` |
| `114` | `WeaponReloadComponentData` | `274` | `WeaponCustomizationComponentData` |
| `119` | `WeaponRoundsComponentData` | `324` | `ProjectileWeaponComponentData` |

### 28.3 完整链：P-19 Redeemer

| # | 环节 | 本 build 的值 |
|---:|---|---|
| 1 | 实体 `WeaponCustomizationComponentData`（row 139）默认槽 | slot 5 `0xB269A0B3` · slot 6 **`0x4B7F0B70`** · slot 1 `0x2F7B4497` · slot 2 `0x469F34D9` |
| 2 | slot 6 的配件行（`weapon_customization_settings`）| **`PISTOL-SMG 9x20mm. FULL METAL JACKET`**（`+8 = 0x4B7F0B70`，`+32 AddPath = 0xC756800DA816EFE1`）|
| 3 | 该 AddPath 的 delta | comp **324**（`ProjectileWeaponComponentData`）成员 `+0` 宽 4 → data `28010000` = **`296`**（data 偏移 `0xCB4C`，文件绝对 `0x027EF4`）|
| 4 | slot 5 的配件行 | `Pistol 9x20mm. Extended`（`+32 AddPath = 0xC891ACF9E8DBDA97`）|
| 5 | 该 AddPath 的 delta | comp **5**：`+136=31 / +140=4 / +144=6 / +148=6`（弹匣容量/初始/补给/备弹）＋ comp **274** **`+0x80` 宽 8 = `0xC891ACF9E8DBDA97`**（弹匣 physics）|
| 6 | 玩家建造武器 | 两处 delta 依次打进组件记录 ⇒ `Proj+0 = 296`、`cust+0x80 = 0xC891ACF9E8DBDA97` |
| 7 | 无人机挂载 | 不走建造链 ⇒ 实体记录保持 `Proj+0 = 0`、`cust+0x80 = 0`（= §22.1 那两扇门）|

**所以第 16/19 轮手工写的那两个值，正好就是官方 delta 写的那两个值** —— 不是"借用别的武器"，是**手工复刻建造链**。
§27.1 实机结果（四只狗开火、手感伤害与玩家 P-19 完全一致）正是这条链的**行为侧**验证。

### 28.4 全档"296"账本（为什么之前搜不到）

`u32 == 296` 全档共 **180 处**，逐处归因后**只有 1 处是弹丸引用**：

| 位置 | 处数 | 性质 |
|---|---:|---|
| `generated_planet_territory_graphs` | 111 | 图数据里的普通整数 |
| `generated_entities` | 38 | 37 处是哈希图的"行号 = 296"（`{key, row}` 的 row 字段）＋ 1 处 `BehaviorComponentData` 的 `BehaviorId = 296`（行为 id，不是弹丸）|
| `generated_entity_deltas` | 9 | 8 处结构性字段（`settingsIndex=296`、delta 行的成员偏移 = 296 等）；**1 处是 data 里的 `296` = P-19 弹种 delta 的弹丸值** |
| 其余 8 张表 | 22 | 各表内的普通数值/索引（如 `damage_settings` 的 1 处不在行数组里）|

⇒ 之前"查不到"的根因不是表里没有，而是**它不在实体记录里**：实体记录只有休眠的 `0`，真值在**配件 delta 的 data 段**。data 段是"被打进去的字节"，不是行数组的一列 ⇒ 按字段扫实体/按行扫表都扫不到。

### 28.5 第二把武器验证：P-2 Peacemaker 的弹丸是 `342`（`✓✓` 面板 + wiki 双证）

同一套链解 P-2：默认 slot 6 = **`PISTOL-SMG 9x20mm. HOLLOW POINT`**（`0xABEA8C15`，AddPath `0x70564BCA8BDD43D1`）→ delta → `ProjectileWeapon+0 = **342**`。

| 弹丸 | size | velocity | mass | drag | gravity | penSlow | 伤害行 | 标准 / 耐久 |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `296`（P-19 的 FMJ）| 9 mm | **375 m/s** | 7 g | 1.2 | 1.0 | 0.25 | 80 | **70 / 12** |
| `342`（P-2 的 HOLLOW POINT）| 9 mm | **320 m/s** | 7 g | 1.2 | 1.0 | 0.25 | 83 | **100 / 20** |

**两条独立验证都落在 342 行上**：

| 验证源 | 结果 |
|---|---|
| **实机面板**（用户 2026-10-27 截图）| 9 mm / 7 g / **320 m/s** / Drag 120% / Gravity 100% / Pen 25% / **100 Ballistic · 20 Ballistic** ⇒ 与 342 行**逐项相同** |
| **本地 wiki 镜像**（`refs/wiki/wiki.sqlite`）| P-2 的 weapon 模块 `attacks[0].name = P-2_P`；该 projectile 模块 = 9 mm / **320 m/s** / 7 g / pen 0.25，damage 模块 = **100 / 20** ⇒ 与 342 行 **6/6 全中** |

⇒ "实体记录=休眠值、默认弹种 delta=真值"的模型在**第二把武器**上复现。
顺带把两边的枚举名对上了：P-19 的 `296` = `Pistol_9x20mm_fmj`，P-2 的 `342` = `P-2_P`（wiki 旧命名）。

### 28.6 对配方/方法论的影响

| 问题 | 以前（§25.2 口径）| 现在（§28 口径）|
|---|---|---|
| P-19 的原生弹丸在哪 | "数据里没有，靠面板指纹反推 296" | **默认弹种 delta 直接写 296**（面板指纹与 delta 双向吻合）|
| 无人机为什么必须手补 | "无人机不认引擎默认" | **无人机挂载不跑玩家武器的建造/配件 delta 链**（行为侧已证；引擎内部路径 `⚠` 未证）|
| 换弹种怎么写 | 只能猜 id | 直接读该弹种的 delta：`Proj+0 = <该弹种 delta 的值>`（例：`PISTOL-SMG 9x20mm. THERMITE` → `288`）|
| 哪些武器是"休眠型" | 只有 P-19/P-2 两把碰巧发现 | 规则：**实体 `Proj+0 = 0` 且默认配件带 slot 6 弹种** ⇒ delta 型；本 build 有 **67** 个弹种配件的 delta 写 comp 324 `+0`（与社区 HD2Runtime 0.28.1 文档的 67 一致），slot 7 的 15 个备选弹种写 comp 119 `+68` |

### 28.7 复现命令

```bash
python tools/ref_scan.py delta-info                    # 存储几何 + 组件索引直方图
python tools/ref_scan.py delta-show 0xC756800DA816EFE1 # P-19 弹种 delta -> +0 = 296
python tools/ref_scan.py delta-show 0xC891ACF9E8DBDA97 # P-19 弹匣 delta -> cust+0x80
python tools/ref_scan.py delta-ammo --component 324 --member 0 --slot AmmoType   # 67 个弹种 -> 各自弹丸
python tools/ref_scan.py exact 296                     # 全档 296 账本
```

工具手册：[REFSCAN](../tools/REFSCAN.md)。配件表结构：[WEAPON-CUSTOMIZATION-DECODED](WEAPON-CUSTOMIZATION-DECODED.md) §7。

### 28.8 附带成果：用**本地 wiki 镜像**给弹丸 id 贴枚举名（61 武器 / 59 个 id）

`refs/wiki/wiki.sqlite`（763 页 / 235 个 weapon 模块 / **701 条 projectile 模块** / 1340 条 damage 模块）里有枚举名和字段。
做法：实体百科 `(code, name)` → wiki 页标题 **`"<code> <name>"`** → weapon 模块 `attacks[0].name` 得枚举名；
我们这边 id = 默认弹种 delta（INDIRECT）或实体自带 `Proj+0`（ACTIVE_DIRECT）。工具：`python tools/xcheck_projectile_names.py`。

| 判据 | 结果 |
|---|---|
| 精确 join 到的武器 | **61** |
| size / velocity / mass / penSlow 一致 | **61 / 61**（弹道参数全中）|
| dmg / dmg2 一致 | 49 / 60、50 / 60 |
| 全字段一致 | **49** |
| 不一致的 12 个 | **只有伤害**——wiki 是旧快照：P-19 60/5 vs 现 70/12、AR-23 80/15 vs 90/22、MP-98 65/7 vs 90/18、P-4 200/70 vs 225/75 … |

⇒ 说明"delta 解出的 id"与官方命名/弹道参数自洽；wiki 数值不能当现值（版本旧），但**名字/结构**可用。
id→名清单写到 `out/wiki-proj-names.json`（59 个 id）。样例：

| id | wiki 枚举名 | id | wiki 枚举名 |
|---:|---|---:|---|
| `296` | `Pistol_9x20mm_fmj` | `342` | `P-2_P` |
| `281` | `Rifle_5.5x50mm_fmj`（AR-23 / M-105）| `150` | `Rifle_8x60mm_fmj`（MG-43）|
| `205` | `P/40-K_P` | `167` | `P-44_P` |
| `241` | `P-69_P` | `314` | `Pistol_13x40mm_fmj`（P-4）|

`⚠` 命名混时代：同一个 id 可能有两个名字（本档 1 例：`281` 也出现在 StA-52 的 `AR-23_P`）——当线索，别当唯一名。

## 29 第二十一轮：P-2 Peacemaker 挂 **Guard Dog** —— 休眠型第二把（2026-10-27 16:1x 已装 → **`✓✓` 实机通过**）

设计（单变量）：只把 **Guard Dog** 的挂载物从 P-19 换成 P-2；P-2 实体按 §28 的"手工复刻 delta"配方补两个值；其余三只狗保持 P-19 作对照。

| 项 | 值 |
|---|---|
| 载体 | **Guard Dog 192**（`0xA0FF2F9A0CA6992A`）→ `Mount+0` = **P-2 Peacemaker `0x05E4E5C2DB6E44A2`** |
| P-2 改动 1 | `ProjectileWeapon+0`：**0 → 342**（= 默认弹种 `PISTOL-SMG 9x20mm. HOLLOW POINT` 的 delta 值，见 §28.5）|
| P-2 改动 2 | `WeaponCustomization+0x80`（u64）：**0 → `0x4F839E923046E631`**（= 默认弹匣 `Pistol 12x20mm. Standard` 的 AddPath，即弹匣 physics/mesh 资源）|
| 不动 | Rover / Hot Dog / K-9 仍挂 P-19；P-19 实体的 `296` + 弹匣修复保持原样 |
| 驻留 | **不需要新增**：patch_27（包 `bf2250de0b17285c`）里已有 `physics 0x4F839E923046E631` + `mesh 0x4F839E923046E631 = P-2 Peacemaker Mag`（`srkit list` 实测）|
| entities | `out/dogs/z1.dl_bin`（md5 `09A3ED8998E4016A7FA3C64A67FDA962`，47,259,584 B；明文 sha256 `fce5a7e4…`）|
| 门禁 | 三次 `entity_field_set` 全 PASS（G1/G2/G3/G4/G7/G8/G6）· 明文哈希仍 `0x8E49771B181FFAA1` · 装盘后 unseal 回读与暂存明文**逐字节相等** |

**判读**

| 现象 | 结论 |
|---|---|
| 能开火、弹匣模型在、手感/伤害与玩家 P-2 一致（**100·20**，320 m/s）| 休眠型配方在第二把武器复现 `✓✓`，"实体=休眠值 + 配件 delta=真值"可通用化（§28.6）|
| 能开火但**弹匣不渲染** | P-2 弹匣资源不在这个包里（需另找 Mag 包驻留）——与 `srkit list` 的结论冲突，优先复核补丁序号 |
| 能开火但**弹容量不对**（30 而不是玩家的 15）| **预期**：无人机读实体 base 值（`WeaponMagazine +136 = 30 / +140 = 6`），默认弹匣 delta 才写成 15 / 5；若确认是 30，按同一"复刻 delta"逻辑补 `+136=15 / +140=5 / +144=8 / +148=8` 即可 |
| 完全不开火 | Guard Dog 路径对 P-2 还有别的门槛（半自动/AIBEH…）⇒ 回到逐项排查 |

**预测（先记下）**：按 §28 的模型，本轮**弹匣容量大概率是 30 而不是 15** —— `WeaponMagazine` 的 base 值（30/6）是休眠值，默认弹匣 delta 才写 15/5，无人机不跑 delta。

### 29.1 结果：**正常开火 + 弹匣模型渲染**（2026-10-27 16:2x，`✓✓`）

用户回报：Guard Dog 挂 P-2 **正常开火，弹匣模型也渲染出来了**。

⇒ 休眠型配方在**第二把武器**上复现，且两条"手工复刻 delta"都对：
- `ProjectileWeapon+0 = 342`（默认弹种 `PISTOL-SMG 9x20mm. HOLLOW POINT` 的弹丸）；
- `WeaponCustomization+0x80 = 0x4F839E923046E631`（默认弹匣 `Pistol 12x20mm. Standard` 的 AddPath，physics+mesh 都在 patch_27 里）。

**"实体记录 = 休眠值、默认配件 delta = 真值"从个案升级成通用规则**（判据见 §28.6）。P-19（全自动）与 P-2（半自动）都成立 ⇒ 与射速/开火模式无关。

可选核对（不影响收口）：
1. **弹容量**：预期是 base 值 **30** 而不是玩家的 15（见上面预测）；若确实是 30，按同法补 `+136=15 / +140=5 / +144=8 / +148=8`。
2. **手感/伤害**：P-2 面板 100·20 / 320 m/s；§28.5 已由"面板 + wiki"双证弹丸 = 342，理论上与玩家手持一致，可顺手对比一次。

**回滚**：`cp out/dogs/y1.dl_bin "<game>/data/game/generated_entities.dl_bin"`（四狗全挂 P-19、已实机通过的版本）。

## 30 载体装填机制修正：Guard Dog = **直接填弹匣**（2026-10-27，行为 `✓✓` / 机理 `⚠`）

两轮实机把 §17 的 R2（"载体决定装填"）的**实现方式**钉住了：
**Guard Dog 的装填不消耗、也不检查备弹，是直接往弹匣里填**；填几次按枪自己的单次装填量分段。

### 30.1 证据

| # | 证据 | 枪的数据 | 实机 |
|---:|---|---|---|
| ① | 墙版 GL-21 挂 GD（[MOUNT-SEATS §12.7](MOUNT-SEATS-26088801.md)）| `WeaponMagazine +136 = 60`；`+140/+144/+148`（初始/补给/备弹）**全 0** | 60 发打空**能装填** —— 备弹 0 也填得满 |
| ② | AC-8 挂 GD（更早一轮）| `WeaponRounds +72 = 10.0`（容量）；`+92 = 5`（与 wiki `clipsize = 5` 对上）| 能装填，但**两次**才装满（wiki：`cap 10 / clipsize 5` ⇒ 2 段）|

⇒ 两条规则：

| # | 规则 | 态 |
|---|---|---|
| 1 | **Guard Dog 的装填 = 直接填弹匣/填弹组，不检查也不扣备弹池**（玩家手持路径不同：玩家从备弹池扣）| `✓✓` 行为（两例）|
| 2 | **"装满"分几次，取决于枪自己的单次装填量**：单弹匣型（`WeaponMagazine`）一次满；分弹组型（`WeaponRounds`，容量 / clip 比）按段数多次（AC-8 = 2 次）| `✓✓` 行为 + 数据对齐 |
| 3 | "备弹 0/0 的枪在狗上打空即废"是**错的** —— 只要枪有 `WeaponReload`、载体能装填，就能一直打 | `✗` 旧预测纠正 |

### 30.2 数据侧对照

| 枪 | 弹药组件 | 容量 | 单次装填量（候选字段）| 狗实测 |
|---|---|---|---|---|
| 墙版 GL-21 | `WeaponMagazine` | `+136 = 60` | 60（单弹匣）| **1 次满** |
| AC-8 | `WeaponRounds` | `+72 = 10.0` | `+92 = 5`（wiki `clipsize = 5`）| **2 次满** |
| P-19（狗线）| `WeaponMagazine` | `+136 = 31` | 31 | 能装填（次数未记）|

`⚠` `+92` 的精确语义（clipsize / 单次装填量 / pellets）还没用实验区分；目前只有"AC-8 的 5 = wiki clipsize 5"一条旁证。

### 30.3 边界与配方影响

- 结论来自 **Guard Dog**；Hot Dog / Dog Breath 假设相同但未复测；Rover / K-9 **无装填**（R2）不受影响。
- 引擎侧实现未证（没有运行时探针）；这是"行为 + 数据对齐"的结论。
- **配方影响**：给狗挂任意带 `WeaponReload` 的枪，**不需要补备弹**也能持续输出；
  "备弹字段"在狗线上被弱化（只有玩家手持路径在意它）。

### 30.4 单变量轮次：AC-8 `+92` 5 → 10（2026-10-27 17:5x 已装，`⚠` 待实机）

目的：验证 §30.2 里"`+92` = 单次装填量"这个候选语义。

| 项 | 值 |
|---|---|
| 基线 | Guard Dog 挂 AC-8（此前 AC-8 在狗上装填要 **2 次**才装满，当时 `+92 = 5`）|
| **唯一变量** | AC-8 `WeaponRounds`（行 23）`+92`：**5 → 10** |
| 为回到可观察基线而恢复的一处 | Guard Dog 挂载：墙版 GL-21 → **AC-8 `0xA8CFFB316F0B5C5F`**；其余不动（M-102=P-19、其余三狗=P-19/P-2）|
| entities | `out/dogs/z7.dl_bin`（md5 `2fe1eb91a0962a675e7feabfff743982`，47,259,672 B；明文 sha256 `f73d2fbd…`）|
| 门禁 | 两次 `entity_field_set` G1–G8 全 PASS（读回 `+92 = 10`，`+72` 容量仍 10.0）；对 z6 基线**恰好 1 个槽变**（狗行 98）；哈希仍 `0x8E49771B181FFAA1`；seal 回读逐字节相等 |

**判读**

| 现象 | 结论 |
|---|---|
| 变成**一次**装满 | **`+92` = 单次装填量** 坐实（`✓✓`），§30.2 升级为字段语义 |
| 仍然两次装满 | `+92` 不是单次装填量（`✗`）⇒ 转查 `+96`（f32=6.0）/ 其他字段或运行时 |
| 出现第三种变化（一次装更多/更少、总量变）| 按"分段量 × 段数"模型修正并记录 |
| 开火/装填异常（不装、卡住）| 先回滚；再用二分（`+92 = 7/8`）确认是否越界敏感 |

**回滚**：entities 回 `out/dogs/z6.dl_bin`（GuardDog=墙版 GL-21 的上个通过版）。

### 30.4.1 结果：**一次装满** ⇒ `+92` = 单次装填量（`✓✓`）

用户实测：
- **Guard Dog 挂 AC-8**：`+92` 改 10 后**一次装满**（此前 5 时两次）；
- **玩家手持 AC-8 也一次装满** ⇒ 这个字段**对玩家路径同样生效**，不是狗专属逻辑；
  与 wiki `clipsize = 5`（原版）+ 实测 `+92 = 5` 一致，改成 10 = 一次装两组。

⇒ §30.2 表格里 `+92` 从"候选字段（`⚠`）"升级为**字段语义**：
**`WeaponRounds +92 = 单次装填量（clipsize）`**。
也就是说"两次装满"是**枪自己的分段量**造成的，不是狗的限制；狗与玩家都是"按枪的分段量填到满"。
（顺带：改 `+92` 同时改变了玩家手感——这是同一个字段在两个路径上共用的直接证据。）



