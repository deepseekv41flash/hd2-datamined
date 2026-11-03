# `avatar_helldiver` 表语义全解（build 26251122）—— `AvatarComponentData` 字段图

> 2026-11-03 深夜。目标：把玩家 Helldiver 的 `AvatarComponentData` 记录**每个字段都命名、给出原版值与含义**。
> 结论：**852 B 记录全部 207 个字段已命名**，字段布局与我们的 typelib **28/28 成员偏移精确对齐**。
> 机器可读全表：[`refs/avatar-component-fields-26251122.json`](../refs/avatar-component-fields-26251122.json)
> 工具：[`tools/avatar_field_map.py`](../tools/avatar_field_map.py)（字段图+值）、
> [`tools/component_index_map.py`](../tools/component_index_map.py)（离线组件索引）、
> [`tools/entity_fields_batch.py`](../tools/entity_fields_batch.py)（一次写多个字段并保哈希）。

## 0. 资料来源（本地优先，网上补充）

| 来源 | 用途 | 位置 |
|---|---|---|
| **filediver 的 Go 反向工程源码** `datalibrary/avatar_component.go` | **字段名 + 注释语义**（主力） | 本地 vendored：`refs/web/filediver_datalibrary_avatar_component.go`；上游 <https://github.com/xypwn/filediver>（`datalibrary/` 稀疏克隆，commit `master` 2026-11-03） |
| **本项目的 dl 类型库** `dl_library.dl_typelib` | 结构尺寸/成员偏移，**用来验证字段图** | `refs/dlbin/plaintext-26251122/dl_library.dl_typelib` |
| **本项目的实体表明文** `generated_entities.dl_bin` | 取原版值 | `refs/dlbin/plaintext-26251122/generated_entities.dl_bin` |
| **本项目的实体 delta 表** `generated_entity_deltas.dl_bin` | 交叉验证字段偏移（船上 avatar 私有副本） | `tools/ref_scan.py delta-show 0x73012E9238B6E3B9` |
| **hd2runtime 的 Helldiver 研究文档** | 交叉验证 +4…+92 与 +340 区间，以及运行时语义（10 m/s 上限、船上私有副本） | 本地：`c11-recon/sdk-0.30.3/docs/helldiver-fields.md`；网上：<https://github.com/skyeshade/hd2runtime/blob/219d7086/sdk/docs/helldiver-fields.md> |
| 组件索引空间（delta 里的组件编号） | 把 delta 的 `comp 235` 认成 `AvatarComponentData` | `tools/component_index_map.py`（离线解出） |

## 1. 记录在哪

- 实体：`0x4D1C334D294DFA97`，`dev_name = content/fac_helldivers/cha_avatar/avatar_helldiver`，
  `kind=interactable`、无百科名 ⇒ 玩家 Helldiver 的**类型记录**（hd2runtime 的 `hd2.helldiver()`）。
- 组件块：`AvatarComponentData`，块 tid **`0x40EF204C`**，块头 `0x191B0A8`；payload 1736 B = 哈希图 32 B（2 槽）
  + **2 行 × 852 B**；唯一有效行 = row 0（键即上面的实体键）。
- 行结构：`AvatarComponent`（tid `0xB501F712`），**852 B**。
- 当前 build 组件索引：**235**（`component_index_map.py` 用「block0 组件清单 ↔ 各块哈希图归属」离线解出；
  rank 194→idx 234、rank 196→idx 236 夹出占位 195 的这一块 = 235）。

## 2. 结构总览（852 B）

| 行内区间 | 成员（filediver 名） | 大小 | 含义 |
|---|---|---|---|
| `+0x000` | `InputInfo` (`AvatarInputSettings`) | 4 | 按住切姿态键多久进趴姿 |
| `+0x004` | `MovementInfo` (`MoveInfo`) | 148 | **移动速度 12 档 + 体力体系** |
| `+0x098` | `SteepSlopeMovement` (`SteepSlopeMovementInfo`) | 56 | **陡坡自动滑行 14 参数** |
| `+0x0D0` | `SlideMovementInfo` (`ActionSlideMovementInfo`) | 24 | **主动滑步 6 参数**（平地/上坡/下坡 × 时长/速度） |
| `+0x0E8` | `ClimbInformation` (`ClimbInfo`) | 60 | 攀爬/自动上台阶 |
| `+0x124` | `ShortThrowInfo` (`ThrowInfo`) | 8 | 短抛（角度偏移、力度倍率） |
| `+0x12C` | `LongThrowInfo` (`ThrowInfo`) | 8 | 长抛 |
| `+0x134` | `DetectInfo` (`DetectionInfo`) | 12 | 潜行：站/蹲/趴 的敌人视野系数 |
| `+0x140` | `WeatheringSettings` (`AvatarWeatheringSettings`) | 20 | **尘土/风化：速度阈值 + 各姿势累积速率** |
| `+0x154` | `ExertionLevels[8]` (`ExertionLevelInfo`) | 416 (8×52) | **用力等级 8 级**：阈值 + 晃动倍率 + 动画/VO 哈希 |
| `+0x2F4` | `ExertionVoiceOverParams` (`ExertionVoParams`) | 28 | 死亡/出生/用力起止/流血止 的 VO + 受伤阈值 |
| `+0x310` | 尾部 17 个 float | 68 | 自疗、布娃娃伤害、瞄准/举枪时长、嘲讽 |

> ⚠ **跨 build 差异**：filediver 快照的 `AvatarComponent` 还多一个 `MovementHaptics`
> （`AvatarMovementHapticsSettings`，10 个 `stingray.ThinHash` = 40 B，左右手各姿势的震动反馈音效哈希）。
> 本 build **没有**这个成员：892 − 40 = **852** ✓（本表按本 build 排）。所以**不要照搬 filediver 的绝对偏移**。

## 3. 字段表（原版值）

### 3.1 输入 / 移动速度（`MoveInfo.Speeds`）

| 偏移 | 字段 | 原版 | 说明（filediver 注释 / hd2runtime） |
|---|---|---:|---|
| `+0x000` | `InputInfo.HoldStanceButtonTimeForProne` | 0.2 s | 按住切姿态键多久进入趴姿 |
| `+0x004` | `Speeds.ReversingMultiplier` | 0.75 | 反向（倒退）时速度倍率；hd2runtime 称"慢速档的方向系数" ✓ 同一字段 |
| `+0x008` | `Speeds.Aim` | 2.0 | 瞄准移动速度（慢速档 × 方向系数） |
| `+0x00C` | `Speeds.Walk` | 2.0 | 走路 |
| `+0x010` | `Speeds.Jog` | 3.2 | 慢跑 |
| `+0x014` | `Speeds.Sprint` | 5.5 | 冲刺（有体力时；游戏把目标速度 cap 在 10 m/s） |
| `+0x018` | `Speeds.SprintExerted` | 4.25 | 体力耗尽时的冲刺 |
| `+0x01C` | `Speeds.CrouchAim` | 1.2 | 蹲瞄准 |
| `+0x020` | `Speeds.CrouchWalk` | 1.5 | 蹲走 |
| `+0x024` | `Speeds.CrouchJog` | 2.25 | 蹲慢跑 |
| `+0x028` | `Speeds.CrouchSprint` | 4.0 | 蹲冲刺 |
| `+0x02C` | `Speeds.Prone` | 1.5 | 趴姿爬行 |
| `+0x030` | `Speeds.Swim` | 1.5 | 游泳 |

### 3.2 体力 / 转向 / 噪音（`MoveInfo` 其余 25 个 float）

| 偏移 | 字段 | 原版 | 说明 |
|---|---|---:|---|
| `+0x034` | `SprintStaminaDecayDuration` | 23 s | 满体力冲刺耗尽所需时间（÷1.3 有 modifier 2） |
| `+0x038` | `JogStaminaDecayDuration` | 300 s | 慢跑耗尽时间（hd2runtime 备注：地形慢跑实际用 +52 冲刺值） |
| `+0x03C` | `StaminaRecoverTimeStand` | 7 s | 站立回满时间 |
| `+0x040` | `StaminaRecoverTimeCrouch` | 6 s | 蹲姿回满 |
| `+0x044` | `StaminaRecoverTimeProne` | 5 s | 趴姿回满 |
| `+0x048` | `StaminaRecoverDelay` | 1.5 s | 消耗/动作后多久开始回体力 |
| `+0x04C` | `StaminaCostJump` | 0.2 | 每次跳跃消耗（体力比例） |
| `+0x050` | `StaminaCostDodge` | 0.1 | 每次飞扑消耗 |
| `+0x054` | `StaminaCostVault` | 0 | 每次翻越消耗（hd2runtime 未找到读取点） |
| `+0x058` | `StaminaCostClimb` | 0 | 每次攀爬消耗 |
| `+0x05C` | `StaminaCostSlide` | 0.05 | **每次滑步消耗**（Slidedivers ×0.35 → 0.0175） |
| `+0x060` | `VisibilityJump` | 1 | 动作"可见度"倍率（Go 注释为复制粘贴错误，语义待验证） |
| `+0x064` | `VisibilityDodge` | 1 | 同上（飞扑） |
| `+0x068` | `VisibilityVault` | 1 | 同上（翻越） |
| `+0x06C` | `VisibilityClimb` | 1 | 同上（攀爬） |
| `+0x070` | `VisibilitySlide` | 1 | 同上（滑步） |
| `+0x074` | `HipfireTime` | 0.5 s | 腰射后保持腰射姿态的时间 |
| `+0x078` | `ThrowHipfireTime` | 0.8 s | 投掷后保持腰射姿态时间 |
| `+0x07C` | `CrouchTurnSpeedMultiplier` | 1 | 蹲姿转向倍率 |
| `+0x080` | `ProneTurnSpeedMultiplier` | 0.65 | 趴姿转向倍率 |
| `+0x084` | `JogTurnSpeedMultiplier` | 1 | 慢跑转向倍率 |
| `+0x088` | `SprintTurnSpeedMultiplier` | 1.2 | 冲刺转向倍率 |
| `+0x08C` | `DownedTurnSpeedMultiplier` | 0.25 | 倒地转向倍率 |
| `+0x090` | `SwimTurnSpeedMultiplier` | 0.6 | 游泳转向倍率 |
| `+0x094` | `SprintNoiseRadius` | 10 | 冲刺噪音半径（敌人警觉范围） |

### 3.3 陡坡自动滑行（`SteepSlopeMovementInfo`，14 个 float）

| 偏移 | 字段 | 原版 | 说明 |
|---|---|---:|---|
| `+0x098` | `SlideEnterAngle` | 45° | **进入滑行状态的坡度角**（坡度超过它开始滑） |
| `+0x09C` | `SlideEnterMinimumDuration` | 0.3 s | 在"过陡"坡度上需保持多久才进入滑行（"quicker entry"） |
| `+0x0A0` | `SlideSpeed` | 3 | 滑行速度 |
| `+0x0A4` | `SlideGravityMultiplier` | 1 | 把你往坡下拉的重力倍率（"stronger downhill pull"） |
| `+0x0A8` | `SlideMinimumDuration` | 0.3 s | 进入滑行后最短保持时间 |
| `+0x0AC` | `SlideExitAngle` | 40° | **退出滑行、恢复可移动的坡度角** |
| `+0x0B0` | `SlideBeyondMoverMaxAngleExitDuration` | 0.2 s | 超过"可行走最大坡度"后多久退出滑行 |
| `+0x0B4` | `SlowedMovementStartAngleUphill` | 10° | 上坡开始减速的角度 |
| `+0x0B8` | `SlowedMovementMaxAngleUphill` | 55° | 上坡减速到最大的角度 |
| `+0x0BC` | `SlowedMovementSpeedMultiplierUphill` | 0.01 | 上坡最大减速倍率（0.01 ⇒ 几乎走不动） |
| `+0x0C0` | `SlowedMovementStartAngleDownhill` | 30° | 下坡开始减速角度 |
| `+0x0C4` | `SlowedMovementMaxAngleDownhill` | 55° | 下坡最大减速角度 |
| `+0x0C8` | `SlowedMovementSpeedMultiplierDownhill` | 0.02 | 下坡最大减速倍率 |
| `+0x0CC` | `SlopeAngleInterpolationFractionPerSecond` | 0.9999 | 坡度法线/角度插值速度（所有坡度修正共用） |

### 3.4 主动滑步（`ActionSlideMovementInfo`，6 个 float）

| 偏移 | 字段 | 原版 | 说明 |
|---|---|---:|---|
| `+0x0D0` | `SlideFlatDuration` | 0.5 s | 平地滑步持续（退出时长） |
| `+0x0D4` | `SlideFlatSpeed` | 3 | 平地滑步速度 |
| `+0x0D8` | `SlideUphillDuration` | 0.1 s | 上坡（最大上坡角）滑步持续 |
| `+0x0DC` | `SlideUphillSpeed` | 2.9 | 上坡滑步速度 |
| `+0x0E0` | `SlideDownhillDuration` | 1 s | 下坡（最大下坡角）滑步持续 |
| `+0x0E4` | `SlideDownhillSpeed` | 3.6 | 下坡滑步速度 |

### 3.5 攀爬（`ClimbInfo`）

| 偏移 | 字段 | 原版 | 说明 |
|---|---|---:|---|
| `+0x0E8` | `StartOffset` (Vec3) | (0, 0.4, 2.1) | 吸附到攀爬点时的根偏移 |
| `+0x0F4` | `ClimbOffset` (Vec3) | (0, 0, 0) | 到达悬挂时的根偏移 |
| `+0x100` | `MinHeightFalling` | 1.2 | 最小下落高度 |
| `+0x104` | `MaxHeight` (Vec2) | (1.95, 1.4) | 可翻越障碍最大高度（地面 / 空中） |
| `+0x10C` | `MaxForwardDistance` (Vec2) | (0.6, 0.5) | 最大前向距离（地面 / 空中） |
| `+0x114` | `ForwardStartCheckDistancePerMeterPerSecond` | 0.05 | 每 m/s 移动速度追加的检查距离 |
| `+0x118` | `MaxAutoStepUpHeight` | 0.8 | 自动上台阶最大高度 |
| `+0x11C` | `AutoStepUpCooldown` | 0.5 | 自动上台阶冷却 |
| `+0x120` | `ClimbRefInterpolationSpeed` | 8 | 攀爬参考插值速度 |

### 3.6 投掷 / 潜行 / 尘土

| 偏移 | 字段 | 原版 | 说明 |
|---|---|---:|---|
| `+0x124` | `ShortThrowInfo.ThrowAngleOffset` | 5 | 短抛相对镜头前方的角度偏移 |
| `+0x128` | `ShortThrowInfo.PowerMultiplier` | 0.7 | 短抛力度倍率 |
| `+0x12C` | `LongThrowInfo.ThrowAngleOffset` | 5 | 长抛角度偏移 |
| `+0x130` | `LongThrowInfo.PowerMultiplier` | 1.4 | 长抛力度倍率 |
| `+0x134` | `DetectionInfo.SightModifierStanding` | 1 | 站姿敌人视野系数 |
| `+0x138` | `DetectionInfo.SightModifierCrouching` | 0.75 | 蹲姿视野系数 |
| `+0x13C` | `DetectionInfo.SightModifierProne` | 0.5 | 趴姿视野系数 |
| `+0x140` | `WeatheringSettings.MoveSpeedRequirement` | 0.5 | 移动速度超过它才开始沾尘土 |
| `+0x144` | `WeatheringSettings.DirtSpeedStanding` | 1 | 站立移动沾尘土速率 |
| `+0x148` | `WeatheringSettings.DirtSpeedCrouching` | 3 | 蹲移速率 |
| `+0x14C` | `WeatheringSettings.DirtSpeedProne` | 10 | 趴爬速率 |
| `+0x150` | `WeatheringSettings.DirtSpeedSliding` | 20 | **滑步沾尘土速率**（Slidedivers ×0.75 → 15） |

### 3.7 用力等级（`ExertionLevels[8]`，每级 52 B）

每级结构：`Index(u32) | ExertionThreshold | SwayMultiplierScoped | SwayMultiplierThirdperson | SwayFrequencyMultiplierScoped | SwayFrequencyMultiplierThirdperson | SwayRecoilMultiplierScoped | SwayRecoilMultiplierThirdperson | SwayInterpSpeed`（8×float）+ 4 个 `ThinHash`（进入/退出动画事件、用力呼吸 VO 起/收）。

| 级 | 偏移 | Index | Threshold | Scoped/第三人称 晃动倍率 | 频率倍率 | 后坐倍率 | SwayInterp |
|---|---|---:|---:|---|---|---|---:|
| 0 | `+0x154` | 0 | 0 | 1 / 1 | 1 / 1 | 1 / 1 | 1.2 |
| 1 | `+0x188` | 1 | 0.001 | 1 / 1 | 1 / 1 | 1 / 1 | 1.2 |
| 2 | `+0x1BC` | 2 | 0 | 1.1 / 1.1 | 1.1 / 1 | 1 / 1 | 1.2 |
| 3 | `+0x1F0` | 3 | 0.5 | 1.2 / 1.2 | 1.2 / 1 | 1 / 1 | 1.2 |
| 4 | `+0x224` | 4 | 1.0 | 1.3 / 1.3 | 1.3 / 1 | 1 / 1 | 1.2 |
| 5 | `+0x258` | 5 | 2.0 | 1.4 / 1.4 | 1.4 / 1 | 1 / 1 | 1.2 |
| 6 | `+0x28C` | 6 | 3.0 | 1.5 / 1.5 | 1.5 / 1 | 1 / 1 | 1.2 |
| 7 | `+0x2C0` | 7 | 3.0 | 1.6 / 1.6 | 1.6 / 1 | 1 / 1 | 1.2 |

（`+0x2B0` 等之后的 4 个 ThinHash 是有值的资源哈希，具体对应哪条动画事件/呼吸音效未解。）

### 3.8 VO / 自疗 / 布娃娃 / 瞄准 / 嘲讽

| 偏移 | 字段 | 原版 | 说明 |
|---|---|---:|---|
| `+0x2F4..+0x304` | `ExertionVoiceOverParams` 5 个 ThinHash | 有值 | 死亡/出生/用力起止/流血止 的 VO 事件 |
| `+0x308` | `InjuryHpThreshold` | 0.5 | 受伤呻吟 HP 阈值 |
| `+0x30C` | `CriticalBleedHpThreshold` | 0.2 | 濒死流血 HP 阈值 |
| `+0x310` | `HealSelfDuration` | 8 s | 自疗（按住治疗）所需时间 |
| `+0x314` | `HealSelfDecayWaitTime` | 0.5 s | 停止自疗后开始衰减的等待 |
| `+0x318` | `HealSelfDecayRate` | 0.5 | 自疗进度衰减速率 |
| `+0x31C` | `HealSelfCancelDamageAmount` | 5 | 取消自疗受到的伤害 |
| `+0x320` | `RagdollDamageVelocityLower` | 12 | 布娃娃伤害速度下限 |
| `+0x324` | `RagdollDamageVelocityUpper` | 105 | 布娃娃伤害速度上限 |
| `+0x328` | `RagdollDamageMin` | 10 | 布娃娃最低伤害 |
| `+0x32C` | `RagdollDamageMax` | 300 | 布娃娃最高伤害 |
| `+0x330` | `RagdollDamageSnowModifier` | 0.75 | 雪地布娃娃伤害倍率 |
| `+0x334` | `MinAimDuration` | 0.09 s | 满人机工效时举枪瞄准时间 |
| `+0x338` | `MaxAimDuration` | 0.5 s | 最低工效瞄准时间 |
| `+0x33C` | `MinFireReadyDuration` | 0.04 s | 满工效举枪到可开火时间 |
| `+0x340` | `MaxFireReadyDuration` | 0.12 s | 最低工效可开火时间 |
| `+0x344` | `TauntTimeBeforeDrain` | 10 s | 嘲讽概率开始衰减前的时间 |
| `+0x348` | `TauntDrainPerSecond` | 0.01 | 每秒衰减概率 |
| `+0x34C` | `TauntOnTriggerProbabilityMul` | 0.5 | 成功嘲讽后概率倍率 |
| `+0x350` | `TauntCooldownTimer` | 10 s | 嘲讽冷却 |

## 4. 交叉验证（为什么可信）

1. **typelib 精确对齐**：`avatar_field_map.py` 用 Go 布局模拟出 28 个成员，逐一对上 `0xB501F712` 的
   28 个 typelib 成员偏移（PASS），总大小 **852 = 2 行 × 852 B** 的 stride 精确一致。
2. **跨 build 差异可解释**：filediver 快照 892 B = 本 build 852 B + `MovementHaptics` 40 B。
3. **hd2runtime 文档逐字段对上**：`+4…+48` 12 个速度、`+52…+92` 体力、`+340` 起 ExertionLevelInfo 全部同义
   （hd2runtime 把 +4 叫 `speed_direction_factor`，filediver 叫 `ReversingMultiplier`，值 0.75 相同）。
4. **实体 delta 交叉**：`tools/ref_scan.py delta-show 0x73012E9238B6E3B9`
   （船上 avatar 私有副本）打了 `comp 235` 的 `+12=1.5`、`+16=4.08`；
   `component_index_map.py` 离线解出本 build `AvatarComponentData` 组件索引 = **235**，
   而 +12/+16 正是 `Speeds.Walk` / `Speeds.Jog` ⇒ 与 hd2runtime「船上 walk 1.5 / jog 4.08」的记录一致 ✓。
5. **第三方 mod 反证**：Slidedivers - Tribes 改的 15 个字段全部落在这张表里，且与作者 README 的
   4×/1.7×/1.75×/1.15×/5.2×/2.2×、35%、75%、「quicker entry / faster auto sliding / stronger downhill pull」
   一一对应（见 [RECON-SLIDEDIVERS-TRIBES-26251122](RECON-SLIDEDIVERS-TRIBES-26251122.md) §4）。

## 5. Slidedivers - Tribes 的 15 个字段（命名后）

| 字段 | 原版 → Tribes | 作者描述 |
|---|---|---|
| `MovementInfo.StaminaCostSlide` | 0.05 → 0.0175 (×0.35) | 滑步耗体力 35% |
| `SteepSlopeMovement.SlideEnterAngle` | 45 → 36 (×0.8) | 更快进入（角度更松） |
| `SteepSlopeMovement.SlideEnterMinimumDuration` | 0.3 → 0.15 (×0.5) | quicker entry |
| `SteepSlopeMovement.SlideSpeed` | 3 → 5.4 (×1.8) | faster automatic sliding |
| `SteepSlopeMovement.SlideGravityMultiplier` | 1 → 1.5 (×1.5) | stronger downhill pull |
| `SteepSlopeMovement.SlideMinimumDuration` | 0.3 → 0.525 (×1.75) | 滑行保持更久 |
| `SteepSlopeMovement.SlideExitAngle` | 40 → 28 (×0.7) | 更晚退出滑行 |
| `SteepSlopeMovement.SlideBeyondMoverMaxAngleExitDuration` | 0.2 → 0.25 (×1.25) | 超坡度后更晚退出 |
| `SlideMovementInfo.SlideFlatDuration` | 0.5 → 2.0 (×4) | 平地时长 4× |
| `SlideMovementInfo.SlideFlatSpeed` | 3 → 5.1 (×1.7) | 平地速度 1.7× |
| `SlideMovementInfo.SlideUphillDuration` | 0.1 → 0.175 (×1.75) | 上坡时长 1.75× |
| `SlideMovementInfo.SlideUphillSpeed` | 2.9 → 3.335 (×1.15) | 上坡速度 1.15× |
| `SlideMovementInfo.SlideDownhillDuration` | 1 → 5.2 (×5.2) | 下坡时长 5.2× |
| `SlideMovementInfo.SlideDownhillSpeed` | 3.6 → 7.92 (×2.2) | 下坡速度 2.2× |
| `WeatheringSettings.DirtSpeedSliding` | 20 → 15 (×0.75) | 滑步尘土 75% |

## 6. 编辑指南

```bash
# 直接改这一行的任意字段（一次多个，tail 校正字保 Murmur 锚点）
python tools/entity_fields_batch.py set \
  --block 0x40EF204C --key 0x4D1C334D294DFA97 \
  --field 0x010=f32:5.5 \      # Speeds.Jog
  --field 0x05C=f32:0.0175 \   # StaminaCostSlide
  --out out/avatar/my-tweak.plain
# 然后按常规封包 + 装盘：
python tools/dlbin_seal.py seal-key out/avatar/my-tweak.plain --key refs/dlbin/keys/recipient.pk --out out/avatar/my-tweak.dl_bin
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed out/avatar/my-tweak.dl_bin
```

注意：

- **type-wide**：这是 `avatar_helldiver` 的**类型记录**，本机模拟的每个 Helldiver 都读它；联机只影响自己（hd2runtime 结论）。
- 船上 avatar 有**私有副本**（delta `0x73012E9238B6E3B9`，walk 1.5 / jog 4.08）⇒ 船上测不出移动改动，**要进任务测**。
- 记录有 852 B，改任何 4 字节字段都可以；**不要**照搬 filediver 的绝对偏移（本 build 少 `MovementHaptics`）。
- 别的可选玩法：`Speeds.*` 改跑速、`StaminaCost*` 改消耗、`RagdollDamage*` 改布娃娃伤害、
  `DetectionInfo.*` 改潜行、`WeatheringSettings.*` 改沾土、`ExertionLevels[*].Sway*` 改瞄准晃动。

## 7. 未解 / 待验证

1. `VisibilityJump/Dodge/Vault/Climb/Slide`（+0x60…+0x70，默认全 1）：Go 注释是复制粘贴的"体力消耗"，
   实际语义疑为动作的**可见度/噪音**系数；可用单变量实测（改成 0 / 10 看是否影响潜行）。
2. `ExertionLevels[*]` 的 4 个 ThinHash（动画事件/呼吸 VO）具体指向哪条资源未查（有哈希可查）。
3. 嘲讽 4 个字段的触发逻辑（游戏内嘲讽是方位敏感动作）。
4. hd2runtime 提到的「哪些 customization 带 sprint decay 4 和 recover 18/16/14、long-throw power 1.85」
   —— 这些在 `generated_entity_deltas` 里，尚未定位到具体配件。
