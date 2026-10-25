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

## 7 状态爆：把状态送进一片区域（孤儿爆炸行路线）

`ExplosionInfo`（152 B）**没有** `StatusEffectType` 字段 —— typelib 全扫，它只有
`StatusEffectTemplateType`（模板，不是状态 id）。爆炸能挂状态的唯一入口是：

```
爆炸行 +0x04 DamageInfoType  →  伤害行 +0x2C 起的 4 个状态槽
```

⇒ 「给一颗无状态的弹头加状态爆」= **找一条没人用的爆炸行，把它的伤害行指向一条
「零伤害 + 状态槽」的伤害行**，再把弹丸的 `+0x90`（命中）/ `+0x9C`（失效）指向它。
整行克隆供体爆炸的做法见 [EXPLOSION-VISUAL §4](../explosions/EXPLOSION-VISUAL-26088801.md)。

### 7.1 孤儿爆炸行普查（`26088801` 现算）

判据与 memmod 时代 `c9-recon/a30-ammo/build_row_catalogue.py` 一致：
**没有任何射弹行的 `+0x90`（命中爆炸）或 `+0x9C`（失效爆炸）指向它**。

| 口径 | `25988413`（memmod 文档） | `26088801`（现算） |
|---|---:|---:|
| 爆炸行 | 422 | 424 |
| 被射弹引用 | 159 | 159 |
| **无主** | **263** | **265** |
| 其中伤害行独占 | 94 | 98 |
| 有名字（目录里 97 个命名全是有人用的） | — | **0 / 265** |

独立产物 `refs/explosion-names-chain.json` 交叉验证：159 行有 consumers，
265 个孤儿行 consumers 全空 —— 两个口径一致。

```bash
python tools/expl_orphans.py                    # 摘要 + 全空/近空白候选
python tools/expl_orphans.py --list             # 265 行全表
python tools/expl_orphans.py --type 254 --json out/expl-orphans-26088801.json
```

小半径候选（伤害行独占、无破片）：
`73`（1.0 m）· `216`（1.0 m）· `272`（1.1 m）· `86`/`283`/`305`（2.0 m）· `254`（1.4/1.5/2.0 m）。

> ⚠ 记录一条自己的错结论：本轮之前曾写「424 条爆炸**全**被引用、零孤儿」——
> 是把爆炸行自己的 `+0`（type）当成了引用。以本表为准，方法已被两个独立产物复核。

### 7.2 配方（纯离线，四步）

```bash
# ① 选一条孤儿爆炸（伤害行独占），把它的伤害行改成我们的"零伤害 + 状态槽"行
python tools/expl_set.py --plain <base_expl.plain> --type 254 --set 0x4:446 \
    --host-type 3 --host-offset 0x4 --out expl.plain       # 宿主 = 另一条孤儿行的空 8 字节字

# ② 弹丸：命中 + 失效都指过去
python tools/plain_edit.py --plain <base_proj.plain> --out proj.plain \
    --set <弹丸行+0x90>=u32:254 --set <弹丸行+0x9C>=u32:254

# ③ 封包（内容哈希已在 ①② 保住，hash 值与原版一致）
python tools/dlbin_seal.py seal-key expl.plain --key refs/dlbin/keys/recipient.pk --out generated_explosion_settings.dl_bin

# ④ 装盘（先确认游戏已退出）
python tools/dlbin_deploy.py install --file generated_explosion_settings.dl_bin --sealed out/.../generated_explosion_settings.dl_bin
```

⚠ **视觉**：孤儿行是没被用过的预设，它的粒子资产**可能不在任何已加载的包里**
⇒ 实机看到的可能是灰色方块占位符（判读方法见
[EXPLOSION-VISUAL §6](../explosions/EXPLOSION-VISUAL-26088801.md)）。
要好看就按同一篇 §4 把「已知会渲染」的供体爆炸整行克隆进来，再改 `+0x04`。

### 7.3 案例：P-11 Stim Pistol 治疗爆（已装盘，**✓ 实机**）

原生 P-11 弹丸 `+0x3C`（`DamageInfoType`）= **0**、`+0x90`/`+0x9C` = 0 ⇒
子弹本身不挂伤害行（治疗走的是别的路径）。要让它「打脚下也自愈」必须补一层 AoE：

| 环节 | 值 |
|---|---|
| 治疗伤害行 | **446**（无主行整条重写）：`damage 0 / durable 0 / AP 0,0,0,0 / demo 0 / force 0 / impulse 0 / element 0` + `slot0 = (29 Stim Pistol Heal, 1.0)` |
| 爆炸载体 | **孤儿爆炸 254**（伤害行原本独占 492；半径 1.4 / 1.5 / 2.0 m；破片 0）→ `+0x04 = 446` |
| 弹丸挂点 | 弹丸 **323**（P-11）：`+0x3C = 446` · `+0x90 = 254` · `+0x9C = 254` |

产物：`out/stim-heal/explode.plain` → `generated_explosion_settings.dl_bin`（68,204 B）；
`out/stim-heal/projectile2.plain` → `generated_projectile_settings2.dl_bin`（96,664 B）。
两个明文哈希与原生一致（`0x2ABCD21D…` / `0x946A4FE5FAAAE076`），已装盘并回读核对。
⚠ 同在盘上的 `explosion 326`（Railgun 过蓄自毁 → 伤害行 32）是上一轮的改动，未动。

回滚：`python tools/dlbin_deploy.py restore --file generated_explosion_settings.dl_bin`
（弹丸同理）。

| 判定 | 态 |
|---|---|
| 爆炸只能经伤害行施加状态（`ExplosionInfo` 无 `StatusEffectType`） | **✓ 离线**（typelib） |
| 孤儿爆炸行可整条征用（265 条，交叉验证 0 冲突） | **✓ 离线**（两个独立产物） |
| **治疗爆打自己脚下 → 自己回血、不受伤** | **✓ 实机**（2026-10-25） |
| **半径真的生效**：>2 m 打地面**不回血**（1.4/1.5/2.0 m 那组半径） | **✓ 实机**（2026-10-25，反向对照） |
| 状态爆是「任意武器 + 任意状态」的通用形态（弹丸 `+0x90/+0x9C` → 孤儿爆炸 → 伤害行状态槽） | **✓ 实机** |

### 7.4 这个案例同时是 A 档和 C 档（别混成一句）

拆成两个需求，判定不同：

| 需求 | 判定 |
|---|---|
| ① 让**任意武器施加任意状态**（数据层能力） | **A · dl_bin 等价，✓ 实机**：4 条 dl_bin 改动 + 两次封包，不牺牲任何在用爆炸、不插行手术 |
| ② P-11 **「开火即自愈」**（Lua 时期的原始形态） | **C · 不可实现**：老 mod 是运行时 `player_fired` 事件 + `Player:heal`（**一条数据都没改**），数据侧没有事件钩子 ⇒ 卡在 L4；替代 = 本页的治疗爆（打脚下 2 m 内回血 **✓ 实机**，>2 m 不回血 **✓ 实机**） |

⚠ **更正上一版**：本页曾写「这案例把 C 档翻成了 A 档」—— 那只是对 ① 成立；② 依然是 C。

| 当初的担心 | 实际 |
|---|---|
| 爆炸行没有 `StatusEffectType` 字段 | **成立，但不构成障碍** —— 状态从伤害行走，爆炸只负责"把这条伤害行送到一片区域" |
| 没有可征用的空爆炸行 | **不成立** —— 全 build **265 条孤儿爆炸**（其中 98 条伤害行独占），双产物交叉验证 |

→ C 档完整写法：[RECON-P11-SELF-HEAL](../cases/RECON-P11-SELF-HEAL-26088801.md) ·
[PLAYBOOK §6.1](../cases/PLAYBOOK-LUA-MOD-TO-DLBIN.md)（代码型）与
[PLAYBOOK §6.2](../cases/PLAYBOOK-LUA-MOD-TO-DLBIN.md)（数据边界型）
