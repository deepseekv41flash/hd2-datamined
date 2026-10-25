# 状态效果表 `generated_status_effect_settings` 全解（build 26088801）

> **一句话**：73 行 × **160 B** + 末尾 **1,096 B 名字 blob**，**第 i 条名字 = 第 i 行**；
> 从此每个 status id 都有名字和"每跳伤害行"。**Thermite = id 13**（tick 伤害行 533），
> 但全库**没有任何字段引用它**（见 §5）。
> 相关：[WEAPON-FIRE-MODES §5.6.3b](WEAPON-FIRE-MODES-26088801.md)（喷流 → 伤害行 → 状态槽）·
> [RECON-STERILIZER-HEAL](../cases/RECON-STERILIZER-HEAL-26088801.md)（第三方 mod 改状态槽）

---

## 1 容器与布局

| 项 | 值 |
|---|---|
| 文件 | `generated_status_effect_settings.dl_bin`（14,020 B） |
| 组 0 | `0xC63E0B22` `StatusEffectSettings`，payload 12,792 B |
| 组 1 | `0xDE8193C0` `StatusEffectTemplates`，1,176 B = 29 行 × 40 B（`StatusEffectTemplate`） |
| 组 0 布局 | 组头 16 B（`u64 0x10` + `u64 count`）+ **73 行 × 160 B** + **1,096 B 名字 blob** |
| 名字对齐 | blob 里第 i 条可打印串 = 第 i 行的名字；多出的最后 1 条是残渣 |
| ⚠ 坑 | 之前把 blob 摊进行里，算出 stride **175**（12792 = 16+73×175+1）—— 那 1 B 是假象；typelib 给的才是 **160** |

## 2 `StatusEffectInfo`（160 B）字段图（typelib）

| 偏移 | 类型 | 说明 |
|---|---|---|
| `+0x000` | `StatusEffectType` | **状态 id**（主键） |
| `+0x008` | u64 | |
| `+0x010` | `StatusEffectShaderVariablePreset` | 视觉预设 |
| `+0x018` | u64 | |
| `+0x020` / `+0x024` / `+0x028` | f32 ×3 | 三个数值参数（时长/强度/间隔之类，未逐项证实） |
| **`+0x02C`** | **`DamageInfoType`** | **该状态每跳用的伤害行**（0 = 不造成伤害） |
| `+0x030` | u8 | |
| `+0x040…+0x067` | f32 ×10 | 其余参数 |
| `+0x068` | u8 ×4 | 四个开关位 |
| `+0x070` | 16 B（rec 8） | 两个 id 的数组 |
| `+0x090` | 16 B（rec 24） | 一个子结构 |

## 3 id ↔ 名字 ↔ 每跳伤害行（73 行全表）

`id=名字(tick 伤害行)`；**0 表示该状态不直接造成伤害**。

| id | 名字（tick） | id | 名字（tick） | id | 名字（tick） |
|---:|---|---:|---|---:|---|
| 1 | Blind(0) | 26 | Stim Fx(0) | 51 | Intense Heat(0) |
| 2 | Bleed(552) | 27 | Stim Stamina(0) | 52 | Extreme Cold(0) |
| 3 | Deaf(0) | **28** | **Stim Heal(0)** | 53 | Tremor(0) |
| 4 | Confusion(0) | **29** | **Stim Pistol Heal(0)** | 54 | Sandstorm(0) |
| **5** | **Fire(531)** | 30 | Stim Combat Drugs(0) | 55 | Blizzard(0) |
| 6 | Fire_Panic(0) | 31 | fff?Stim Cooldown(0) | 56 | Acid Storm(0) |
| 7 | Lava(532) | 32 | BurningLight(656) | 57 | Weather Insulated(0) |
| 8 | Slowed(0) | 33 | BurningHeavy(538) | 58 | TornadoStun(0) |
| 9 | WebDrips(0) | 34 | RadiationLight(539) | 59 | Dark Fluid(0) |
| 10 | Rooted(0) | 35 | RadiationHeavy(540) | 60 | Death March(553) |
| 11 | Acid Splash(534) | 36 | Electric(541) | 61–63 | Hotshot Laser Rifle(554/555/556) |
| 12 | Acid Stream(535) | 37 | Hidden(0) | 64 | Illuminate Scrambler(0) |
| **13** | **Thermite(533)** | 38–42 | Stun Small/Medium/Large/Massive/Illuminate(0) | 65 | Constitution(557) |
| 14 | Cyborg Fire(536) | 43 | Gas(544) | 66 | Constitution Booster Armor Resistance(0) |
| 15 | Choked(0) | **44** | **Gas(544)** | 67 | L>Post Mortem Explosion(0) |
| 16 | Sand(0) | 45 | Gas_Confusion(0) | **68** | **FlamerSlowed(0)** |
| 17 | Mud(0) | **46** | **Gas_Confusion(0)** | 69 | Gloom(544) |
| 18 | Snow(0) | 47 | Inverted_Aim_Assist(0) | 70 | Dark Fluid(0) |
| 19 | Submerged(0) | 48 | Flashlighted(0) | 71 | Poison(558) |
| 20 | Thornbush(542) | 49 | Smoke_Covered(0) | 72 | Poison_Heavy(558) |
| 21 | Cactus(543) | 50 | Backpack Chemicals(0) | 73 | PoisonVulnerability(0) |
| 22 | Barbwire(542) | 23 | BushSmall(0) | 24 | BushLarge(0) |
| 25 | Pure Damage(537) | | | | |

> 存储顺序里 **第 5/6 行是 id 7 和 6 交换的**（id 6 `Fire_Panic` 存在第 6 行）——按"第 i 行取第 i 条名字"
> 时这一处已经核对过（`Fire`=5 / `Fire_Panic`=6 / `FlamerSlowed`=68 与 wiki 的强度 2/3/1 三方一致）。

## 4 全库只有 10 处字段能"施加状态"

按 typelib 反查"类型为 `StatusEffectType` 的字段"（6698 个类型名全扫）：

| 宿主类型 | 偏移 | 在哪 |
|---|---|---|
| `DamageStatusEffectInfo` | `+0x000` | 伤害行 `DamageInfo+0x2C` 的 **4 个状态槽**（`{u32 type, f32 value}`） |
| `DestructionStatusEffectVolume` | `+0x000` | `DestructionEffect+0`（场景破坏体的状态体积） |
| `EnvironmentalEffectTagComponent` | `+0x004` | 实体组件（环境标签） |
| `HeatInjuryInfo` / `HeatLevelSetting` | `+0x014` | 高温伤害 |
| `ShieldComponent` | `+0x06C` | 护盾 |
| `StatusEffectContinuousEffect` | `+0x000` | `StatusEffectTemplate+4`（8 个状态）→ 体积/定时球形模板 |
| `StatusEffectInfo` | `+0x000` | 状态表自己 |
| `StratagemScramblerComponent` | `+0x018` | 干扰器 |
| `VehicleComponent` | `+0xE20` | 载具（32 B = 8 个状态） |

⇒ **给武器加状态，唯一实用的入口是"伤害行的 4 个状态槽"**（喷流 / 弹丸命中 / 爆炸都走伤害行）。

## 5 专题：`Thermite`（id 13）—— 定义了，但没人引用

| 事实 | 值 |
|---|---|
| id | **13**（状态表第 12 行，`+0x000`） |
| 名字 | `Thermite` |
| 每跳伤害行 | **533**：`damage 150 / durable 150 · ap[4] = 7,7,7,0 · demo 10 · force 0 · impulse 0 · element 0 · 无状态槽` |
| 谁引用它 | **没有。** 全 55 张表按 `StatusEffectType` 类型字段扫（递归深度 ≤3）→ 仅命中它自己的定义行；实体组件（Shield/Vehicle/环境标签）同样 0 命中 |

**那 P-34 / G-123 的"Thermite"从哪来？** 走一遍真实链路（都不是状态）：

| 武器 | 链路 | 末端伤害行 | 带状态？ |
|---|---|---|---|
| **P-34 Breacher** | `ProjectileWeapon +0` = 弹丸 **274**（speed 150） → 命中爆炸 **167** | **75**：60 / AP 4,4,3,0 / demo 15 | **否** |
| **G-123 Thermite** | 爆炸 **201**（`ExplosionType_Thermite`，半径 1.5 / 2.5 / 4.0） | **352**：2000 / AP 7,0,0,0 / demo 30 / force 20 / impulse 40 | **否** |

⇒ 本 build 里"热熔"是靠**高 AP 直伤 + 粘附（`StickyComponentData`）+ 爆炸**
实现的；`Thermite` 这条状态**大概率是引擎侧按武器硬编码施加**，或者干脆是没接线的旧行。

**想用它（数据路线）**：把 13 写进任意伤害行的状态槽即可（与 Sterilizer-Heal 同一招）：

```bash
# 例：让 FLAM-40 的伤害行(20)第 4 槽施加 Thermite，强度写 1.0
python tools/dmg_row_edit.py set --type 20 --slot 3:13:1.0 \
    --host-type 240 --out out/thermite.plain --seal
```

⚠ 两个未知：`value` 的语义（状态强度）与 tick 频率由状态行 `+0x020/+0x024/+0x028` 决定，
本状态这三个值是 `0 / 1.0 / 1.0`；另外 533 那行 AP7 / 150 伤害相当高，强度别乱开。

## 6 三态

| 结论 | 态 |
|---|---|
| 状态表 = 73×160 B + 名字 blob，id↔名字全表可查 | **✓ 离线**（`Fire/Fire_Panic/FlamerSlowed` 与 wiki 三方互证） |
| `+0x2C` = 该状态的每跳伤害行 | **✓ 离线**（531/533/552… 全部落在伤害表内且被状态引用清单吻合） |
| 全库只有 10 处能施加状态；武器侧唯一入口 = 伤害行 4 个槽 | **✓ 离线**（typelib 类型反查） |
| **Thermite = id 13**，tick 伤害行 533 | **✓ 离线** |
| 没有任何数据字段引用 id 13（引擎硬编码/旧行） | **✓ 离线**（全表 + 实体组件双向扫描 0 命中） |
| 主动写 `slot=(29, 1.0)`（`Stim Pistol Heal`）会让伤害行变成治疗 | **✓ 实机**（Sterilizer-Heal：TX-41 喷脚下自己回血） |
| 主动写 `slot=(13, v)` 能打出热熔效果 | **⚠ 待实机** |
