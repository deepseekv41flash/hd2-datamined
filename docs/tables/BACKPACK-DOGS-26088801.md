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
