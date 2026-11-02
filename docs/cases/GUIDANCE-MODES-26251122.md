# 制导武器三问：Commando 的"非制导档" / WASP 两档弹道 / 激光制导 vs 锁定制导（build 26251122）

> 数据全部来自本 build 的 `generated_entities.dl_bin`（明文缓存）+ `dl_library.dl_typelib` + filediver 类型名表 + SDK `WeaponFeedCapabilities.json`。
> 只读分析，未做任何改动。

## 0. 结论速览

| 问题 | 答案 |
|---|---|
| Commando 的非制导模式，和我们改 Spear 的机制一样吗？ | **不一样**。Commando 走 `WeaponFunctionType_LaserGuide`(6) + `LaserDesignatorComponentData` 激光指示器；数据里**没有第二发弹、没有按状态的制导覆盖**。我们的 Spear 方案是 `ProgrammableAmmo`(8) + 备弹 + `GuidanceTarget` 按状态条目。 |
| WASP 两种模式都要锁定、弹道却完全不同，由什么控制？ | 两档是 `ProgrammableAmmo` 的两个状态，**各自发射不同的射弹行 + 生成不同的导弹实体**；弹道差别由「各自 `SeekingMissileDeviationSettings` 参数 + Artillery 档导弹实体多带 `ProjectileClusterComponentData` + 两条射弹行自己的伤害/爆炸」共同决定。锁定则因为两档的 `GuidanceTarget` 状态条目都保持"制导"标记。 |
| Commando（激光制导，弹头跟准星）和 Spear/P-92（锁定后发射）字段差异？ | ①功能槽 = `LaserGuide`(6) vs `ProgrammableAmmo`(8)/None(0)；②`requires_target_lock` = 0 vs 1；③导弹 `SeekingMissileTargetingMode` = 1 `Guidance` vs 2 `TargetLock`；④多两个组件 `LaserDesignator` + `WeaponLinker`；⑤锁定参数（lock_time/lost/+0x18/binding）整组不同。 |

## 1. 关键枚举（filediver 名称表，哈希公式 = `h=5381; h=h*33+b; id=h-5381`）

```
WeaponFunctionType:            None(0) Zeroing(1) ROF(2) Firemode(3) Magazine(4)
                               LightMode(5) LaserGuide(6) MuzzleVelocity(7)
                               ProgrammableAmmo(8) LaserPrism(9)
SeekingMissileTargetingMode:   Behavior(0) Guidance(1) TargetLock(2) External(3) Count(4)
```
（`ROF=2 / Firemode=3 / ProgrammableAmmo=8` 与 SDK 文档吻合，证明枚举值就是声明顺序。）

`SeekingMissileComponent` 行 272 B 的关键字段（typelib 布局 + 名称表）：

| 偏移 | 类型 | 值示例 | 说明 |
|---|---|---|---|
| `+0x000` | `SeekingMissileTargetingMode` | 1 / 2 | **1=Guidance（跟激光指示） 2=TargetLock（锁目标）** |
| `+0x004` | float | 0.0166 | 全武器相同 |
| `+0x008` | u8 | 0/1 | Commando 与部分武器为 1 |
| `+0x00C` | float | −1.0 / 0 / 0.01 | |
| `+0x040..+0x06C` | float×11 | 30/10/10/100 … | 距离/角度类参数 |
| `+0x070` | `EffectSetting`(48 B) | | 特效 |
| `+0x0B0` | `ProjectileType` | 0/303 | 少数导弹内嵌弹种 |
| `+0x0B4` | `SeekingMissileDeviationSettings`(68 B) | ±15°、±75°、±8°… | **转向/偏差参数块 —— 两档弹道差异的主要载体** |
| `+0x0AC / +0x0AD` | u8 | 0/1 | 未解 |

## 2. `GuidanceTarget` 全表（本 build 只有 9 个实体带该组件）

`+0x4C` 起是 **4 × 12 B 的"按功能状态"配置数组**：{u32 flag, u8×6}。下表 els 列 = 前 10 字节（`u32` + 6 个 u8）的十进制串。

| 实体 | requires_lock(+0x1C) | lockT(+0x10) | lost(+0x14) | +0x18 | +0x28 | bind(+0x48) | els[0..3] |
|---|---|---|---|---|---|---|---|
| Solo Silo ×2 | 0 | 2.0 | 1.0 | 1.0 | 0 | 0 | 全 stock |
| 未知 ×1 | 0 | 2.0 | 1.0 | 1.0 | 0 | 0 | 全 stock |
| Quantum Staff | 1 | 0.1 | 3.0 | 1.0 | 0 | 0 | 全 stock |
| **P-92 Warrant** | 1 | 0.1 | 0.1 | 2.0 | 1 | **8** | `0000011100` / `1000100001` / stock / stock |
| **P-33 Missile Pistol** | 1 | 0.75 | 0.15 | 2.0 | 0 | **8** | `0000001111` / `1000100000` / stock / stock |
| **Spear** | 1 | 1.0 | 0.15 | 2.0 | 0 | 0 | 全 stock |
| **W.A.S.P.** | 1 | 0.5 | 0.1 | 2.0 | 0 | **8** | `0000001111` / `1000001111` / stock / stock |
| **Commando** | **0** | 2.0 | 1.0 | 1.0 | 0 | 0 | 全 stock |

（stock = `0,0,0,0, 0,0,0, 1,1,1, 0,0`，即 u32=0、u8[4..6]=0、u8[7..9]=1。）

**推断**（与 5 种既有配置全一致，未单变量验证）：
- `u32[0] = 1` ⇒ 该状态是"第二档/备弹档"（P-92/P-33/WASP 的第二档都是 1）；
- `u8[4] = 1` ⇒ 该档**无制导**（P-92、P-33 的非制导档 = 1；WASP 的 Artillery 档 = 0 所以仍制导；我们给 Spear 补的也是 1）；
- `u8[7..9]` 语义未解（stock 全 1，非制导档各不相同）。

## 3. Commando 的"非制导"是怎么实现的（与 Spear 方案的对比）

**Commando 数据（entity `0x5990123D142B16CB`）**：

| 项 | 值 | 含义 |
|---|---|---|
| `WeaponData +0xB8` | **L=6** | `WeaponFunctionType_LaserGuide`（不是 ProgrammableAmmo） |
| `WeaponData fireModes` | `[2]` | 只有 Single |
| `WeaponData crosshair +0x194` / sight nodes | 0 / 全 0 | 没有按档准星 |
| `ProjectileWeapon +0x000 / +0x028` | 249 / `0x527470C9D5F2B3C7` | 唯一一发弹 + 唯一导弹实体 |
| `ProjectileWeapon +0x240 / +0x248` | **0 / 0** | **没有备弹、没有备用生成实体** |
| `GuidanceTarget +0x1C / +0x48` | **0 / 0** | 不要锁、没有功能绑定、4 个状态条目全 stock |
| 额外组件 | **`LaserDesignatorComponentData`(0x32528174)**、**`WeaponLinkerComponentData`(0xEBD7729C)** | 激光指示器 + 武器关联；Spear/P-92/P-33/WASP 都没有 |
| 导弹 `SeekingMissile +0x000` | **1** | `SeekingMissileTargetingMode_Guidance`（跟激光指示） |

`LaserDesignatorComponentData` 全表只有 4 个实体：**Commando**、"Solo Silo Targeting Remote"（战略配备遥控器）×1、未知 ×2。
`WeaponLinkerComponent` 只有 3 个：C4 Pack、Commando、Solo Silo Targeting Remote —— 同属"激光指示/关联"体系。

**对比我们的 Spear 改法**：

| | Spear（我们改的） | Commando（原生） |
|---|---|---|
| 选档机制 | `ProgrammableAmmo`(8)，左右功能槽 | `LaserGuide`(6)，左功能槽 |
| 第二发弹 | `+0x240` = 备弹行（223） | 无（同一条射弹 249） |
| 备用生成实体 | `+0x248` = 0（不带导弹实体） | 无 |
| 按状态的制导配置 | `GuidanceTarget +0x48=8` + `element[1]` 改 `u32=1,u8[4]=1` | 无（全部 stock） |
| 免锁来源 | 第二档条目的 `u8[4]=1`（按状态覆盖） | 组件级 `requires_target_lock=0` |
| 附加组件 | 无 | `LaserDesignator` + `WeaponLinker` |

⇒ **结论：Commando 的"非制导"不是"第二发弹"，而是"同一条导弹 + 激光指示器开关"**：按住/对准激光时导弹按 `Guidance` 模式追随指示点；没有有效指示时它按普通弹道直飞。它是"一个弹种、两种制导行为"，我们那套是"两个弹种、按状态覆盖参数"。

## 4. WASP 两档（Burst / Artillery）

**SDK 权威**：`WeaponFeedCapabilities.json` → WASP `programmable_ammo` feed，`presentation = {label: "artillery", icon: "airstrike", displayName: "Artillery"}`，`nativeProjectile: true`，`reason: "The programmable function spawns an entity (+584 or +40), not a projectile reference."`
Wiki `modes = ["Burst", "Artillery"]` ⇒ 档 0 = Burst，档 1 = Artillery。

**数据**：

| | 档 0 = Burst | 档 1 = Artillery |
|---|---|---|
| 射弹行 | `44` | `335` |
| 伤害行 / 命中爆炸 | 254 / **374** | 39 / **87** |
| 生成实体 | `0x14CC0DB942F6D7F2` | `0x1597AF7289E1BE93` |
| 导弹 `SeekingMissile` 行 | 9 | 8 |
| `SeekingMissileDeviationSettings` | `±75°`、200/45/40/55、20/40、20/30、50/30 | `±8°`、60/75、5/10、5/10、15/10 |
| 额外组件 | — | **`ProjectileClusterComponentData`(0xB25BDF80)** = {1, ExplosionType 87, AbilityId 2626} |
| 锁定 | 要 | 要 |

弹道差异的**载体**（按可信度排序）：
1. **各自独立的导弹实体**：两档 `+0x248` 分别指向不同实体，各自有一整套 `SeekingMissile` 参数（含 `DeviationSettings` 68 B：转角/速率上限差一个数量级：±75° vs ±8°）；
2. **Artillery 档多一个 `ProjectileClusterComponentData`**（带自己的 ExplosionType + AbilityId）—— 这解释了"看起来像另一种武器"；
3. 两条射弹行的伤害行/命中爆炸完全不同（254/374 vs 39/87）。

**为什么两档都还要锁定**：`GuidanceTarget` 的两个状态条目分别是 `0000001111` / `1000001111` —— 第二档虽然 `u32=1`（备弹档），但 **`u8[4]=0`（不是"无制导"档）**，所以制导+锁定逻辑照旧。对照 P-92/P-33 的非制导档：`1000100001` / `1000100000`，`u8[4]=1`。

## 5. Commando（Guidance/激光）vs Spear/P-92/P-33（TargetLock）字段差异

| 层 | 字段 | Commando | Spear | P-92 | P-33 |
|---|---|---|---|---|---|
| WeaponData | `+0xB8` 左功能 | **6 LaserGuide** | 0 | 8 ProAm | 8 ProAm |
| WeaponData | `+0x194` 准星 | **0** | 16 | 16 | 16 |
| WeaponData | `+0x198` sight nodes | 无 | 无 | `{8,0,16}{8,1,4}` | 同 |
| GuidanceTarget | `+0x1C` requires_lock | **0** | 1 | 1 | 1 |
| GuidanceTarget | `+0x10` lock_time | 2.0 | 1.0 | 0.1 | 0.75 |
| GuidanceTarget | `+0x14` lost | 1.0 | 0.15 | 0.1 | 0.15 |
| GuidanceTarget | `+0x18` | 1.0 | 2.0 | 2.0 | 2.0 |
| GuidanceTarget | `+0x28` | 0 | 0 | 1 | 0 |
| GuidanceTarget | `+0x48` binding | 0 | 0 | **8** | **8** |
| 组件 | LaserDesignator / WeaponLinker | **有 / 有** | 无 | 无 | 无 |
| 导弹 | `SeekingMissile +0x000` | **1 Guidance** | 2 TargetLock | 2 | 2（备用弹实体也是 2） |
| 导弹 | `+0x008` u8 | **1** | 0 | 0 | 0 |
| 导弹 | `+0x00C` | **0** | −1.0 | 0.01 | 0.01 |
| 导弹 | `DeviationSettings +0xB4` | **全 0** | 全 0 | 部分（5.0/0.01…） | ±15° 一组 |
| ProjectileWeapon | `+0x010..+0x01C` | **0/0/0/0** | 0/0/0/0 | 75/150/300/20 | 75/150/300/20 |

**一句话**：Commando 是"**制导方式是激光指示（Guidance）+ 永远可开火**"，Spear/P-92/P-33 是"**锁定制导（TargetLock）+ 组件级或按状态的锁定门禁**"。两者在数据层唯一的公共点是都用 `GuidanceTarget` 组件（锁定类参数），而"制导方式"本身由**导弹实体**的 `SeekingMissileTargetingMode` 决定。

## 6. 对以后做 mod 的含义

- 想让某武器"只跟准星/激光、不需要锁定"：**换/改导弹实体的 `SeekingMissile +0x000 = 1(Guidance)`**，而不是去动 `GuidanceTarget` 的锁定参数；若要玩家可切换，则给它绑 `LaserGuide` 功能 + `LaserDesignator` 组件（Commando 现成的结构）。
- 想让某武器"两个锁定档、弹道不同"：像 WASP 一样给第二档配**独立的生成实体**（各带自己的 `SeekingMissile` 参数与可选 `ProjectileCluster`），`GuidanceTarget` 第二档条目保持 `u8[4]=0`。
- 想"可切换的无制导档"：就是本次 Spear 配方（备弹行 + `u8[4]=1` + `+0x48=8` 绑定）。
