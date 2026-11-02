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

## 7. WASP Burst 的「随机发射方向」落在哪个字段

**先排除**：武器层的 spread/recoil 不是原因 —— WASP 的 `WeaponData` 的 spread 相关区（`+0x054` = 0.004/0.004、`+0x060` = 1.0/1.0、`+0x074` = 1/1/1、`+0x0A0`、`+0x0CC`）与 **Spear / Commando 逐字段相同**，且武器层参数两档共用。

⇒ 随机性只能来自"每档自己的生成实体"，即 `SeekingMissile` 组件里的 `SeekingMissileDeviationSettings`（68 B，`+0x0B4` 起）。

**全表 29 条 `SeekingMissile` 行的 deviation 第一对角度（`+0x04/+0x08`）分布**：

| 行 | 归属 | 角度对 | 两个 Vector3 |
|---|---|---|---|
| 9 | **WASP Burst** | **−75 / +75** | (20,40,20) / (30,50,30) |
| 8 | WASP Artillery | −8 / +8 | (5,10,5) / (10,15,10) |
| 5 | P-33 制导 | −15 / +15 | (10,20,10) / (10,20,10) |
| 4 | P-92 | 0 / 0 | 0 / 0 |
| 7 | Spear | 0 / 0 | 0 / 0 |
| 6 | P-33 非制导 | 0 / 0 | 0 / 0 |
| 10 | Commando | 0 / 0 | 0 / 0 |
| 其余 22 行 | Solo Silo / 未知 | 0 / 0 | 0 / 0 |

`SeekingMissileDeviationSettings` 结构（typelib，68 B / 13 成员）：
`u8 +0x00 · f32 +0x04 · f32 +0x08 · f32 +0x0C · f32 +0x10 · Vector3 +0x14 · Vector3 +0x20 · u8 +0x2C · f32 +0x30/34/38/3C/40`

**判定**：**±75° 就是"随机发射方向"的参数**（全表唯一的最大值；其他武器 ≤±15°，WASP 另一档 ±8°）。
行为解释：每发导弹在 ±75° 锥内随机取一个初始方向，随后靠制导转向锁定目标 ⇒ 于是会先朝奇怪方向飞、可能撞地形/建筑（与 wiki 原文一致）。

**证据强度**：
- ✓ 数据结构名 `SeekingMissileDeviationSettings`（filediver 类型名表）；
- ✓ 数值分布（Burst ±75 全表唯一）；
- ✓ wiki 行为描述；
- ⚠ 逐字段语义（哪一对是 yaw/pitch、两个 Vector3 是什么）**未定** —— typelib 剥掉了成员名。

**未做的验证实验**（干净、可做）：
1. 把 WASP 行 9 的 deviation 块清零/改成 ±8 ⇒ 实机 Burst 应该变成直线齐射（不再乱飞）；
2. 反向：把 Artillery 行 8 放大到 ±75 ⇒ 单发 Artillery 也应该开始乱射。
两都是 entities 表里同一行的 68 B（`entity_batch_set` 可写，保哈希）。

## 8. 「打转」定位闭环（2026-11-02 两轮单变量实机）

`SeekingMissileDeviationSettings`（WASP 弹头实体 `0x14CC0DB942F6D7F2` 的 `SeekingMissile +0xB4`）就是 WASP Burst 弹道毛病的唯一载体：

| 轮 | 改动 | 实机结果 |
|---|---|---|
| W1 | 只把角度对 `+0xB8/+0xBC` 由 −75/+75 改成 −8/+8 | 「发射方向随机」消失；**弹头仍然打转** |
| W2 | 把 P-33 弹头实体（`0xA1470A4DAB237264`）的整块 68 B 原样复制过来（12 处：`+0xB8…+0xE8`） | **随机消失 + 打转消失** |

W2 是纯参数单变量：`UnitComponent +0x000`（单位资源/模型 `0xFFB0F21DCC7B5E15`）**未改**，Attachable / Detector / ThrusterGroup（352 B）逐字节相同 ⇒
**「打转」不是模型/推进器造成的，而是 deviation 参数块里的角范围/速率字段造成的**（W1 只改了第一对，所以打转还在）。

- 仍未做逐字段拆分（`+0xC0/+0xC4` 与两个 Vector3 范围都可能参与），但"整块复制"已是可用配方。
- 与 Lua 版 `WASP Trajectory Fix` 的对比：那个 mod 换成 P-33 **生成实体**（8 B）+ 重发 P-33 导弹 mesh/贴图（资源驻留）来达到同样效果；
  **纯数据层只需改 68 B 参数、连模型和资源都不用动**，更小、更干净。

### 产物（build 26251122）

| 补丁 | 内容 | 指纹 |
|---|---|---|
| `D:\mod\out\wasp-dev1.dl_bin` | W1：只改 ±8° | sealed 47,259,544 B / `7fdd447c…` |
| `D:\mod\out\wasp-devfull.dl_bin` | **W2（当前装盘）**：整块 = P-33 | sealed 47,259,544 B / `0d075ee2479c43bf`；明文 `428d79c6…` |

W2 基于 Spear parity 盘（Spear 的 `+0x240=223` / `GT+0x48=8` / `+0x58=1` 均保留 ✓）。
回滚到纯 parity：`python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed D:/mod/out/parity-entities.dl_bin`。

## 9. deviation 块逐字段拆分（2026-11-02，四轮单变量实机）

| 轮 | 改动（基线始终是 A 对 = P-33 ±15） | 实机 |
|---|---|---|
| W1 | A 对 `+0xB8/+0xBC`：−75/+75 → −8/+8 | 发射方向随机**消失**；弹头**仍打转** |
| W2 | 整块 68 B = P-33（12 处） | 随机**消失** + 打转**消失** |
| R1 | A + V1/V2 两个 Vec3 = P-33 | 打转**仍在** ⇒ V1/V2 不控制打转 |
| R2 | A + B 对 + 尾部两格 = P-33 | 打转**消失** |
| R3 | A + **只 B 对** = P-33（10/15） | 打转**仍在**，但**半径变小** ⇒ B 不是开关 |
| R4 | A + **只尾部**（`+0xE4`5→2、`+0xE8`0.2→0.1） | **不打转**，但轨迹**仍是弧线** ⇒ 尾部 = 打转开关 |

**定出的语义模型**（用户实机判读 + 跨武器数值互证）：

| 字段 | 语义 | 证据 |
|---|---|---|
| A 对 `+0x04/+0x08` | **发射方向随机范围（度）** | W1：±75→±8 随机消失 |
| B 对 `+0x0C/+0x10` | **弧线半径 / 偏离弧度（度）** | R3 半径变小；R4 大 B 时轨迹是大弧线 |
| `+0x30/+0x34`（结构内偏移） | **打转开关 / 角速度 + 衰减** | R4：只改这两格，打转消失、弧线保留 |
| V1/V2 两个 Vec3 | **未定**（不控制打转；疑为逐轴权重/形状） | R1 全改无感 |
| `+0x2C` u8 | 未知（两武器都 1） | — |

**跨武器一致性验证**（WASP 两档 / P-33 / P-92 正好落在同一模型上）：

| 武器 | B 对 | 尾部 | 模型预测 | 实机观感 |
|---|---|---|---|---|
| WASP Burst | 40/55 | 5 / 0.2 | 小半径 + 强自转 | 打转 ✓ |
| WASP Artillery | 60/75 | 2 / 0.2 | 大弧线 + 弱自转 | 高抛弧线、不打转 ✓ |
| P-33 | 10/15 | 2 / 0.1 | 小弧线 + 不打转 | 准直 ✓ |
| P-92 | 0/0 | 5 / 0.01 | 半径 0 ⇒ 转也看不出 | 无异常 ✓ |

⇒ 「WASP Burst 弹道毛病」= 大 B（弧线）+ 大尾部（自转）叠加；要"直线"就两者都压小（W2 配置），要"弧线但不打转"就只压尾部（R4 配置）。
