# AvatarComponentData ↔ 护甲 / 护甲被动线：连接图（build 26251122）

> 2026-11-04。回答「Avatar 表里那些量是不是护甲被动改的东西」。结论：**是同一批运行时量的两层**，
> 而且**定制（customization）通道确实会直接覆盖 Avatar 字段**——全 build 只有 3 个 entity delta 写 Avatar。
> 相关：本页工具 [`tools/avatar_deltas.py`](../tools/avatar_deltas.py)；
> 字段图 [AVATAR-HELLDIVER-FIELDS-26251122](AVATAR-HELLDIVER-FIELDS-26251122.md)；
> 护甲线 [ARMOR-PASSIVE-STATS](../tables/ARMOR-PASSIVE-STATS-26088801.md)、
> [ARMOR-KIT-WEIGHTS](../tables/ARMOR-KIT-WEIGHTS-26088801.md)；
> 本地 SDK 资料 `c11-recon/sdk-0.30.3/{docs/armor-stats.md,docs/armor-passives.md,ArmorPassiveCatalog.json,ArmorStatsCapabilities.json}`。

## 0. 一句话

| 层 | 在哪 | 谁 |
|---|---|---|
| **基准层** | `AvatarComponentData` 852 B（本 build 已全解） | 12 档速度、体力消耗/恢复、滑步、陡坡、投掷、潜行、尘土、用力等级、自疗、布娃娃、瞄准、嘲讽 |
| **乘数层** | 护甲重量档（game.dll 三张 class 表）+ 护甲被动 stat 键（`passive_bonuses` 的 pm/sm 行） | F（体力因子）缩放体力类；S（速度因子）写进 locomotion 速度槽；passive 键按 key 改具体 stat |
| **展示层** | 军械库 | RATING=50+50A · SPEED=500×S · STAMINA=100×(2−F) |

⇒ 改 Avatar 字段 = 改**所有甲/所有玩家**的基准；改护甲被动/重量 = 改**某套甲**的乘数。
两者不互相覆盖，**预计叠乘**（Avatar 基准 × S × passive 乘数）。

## 1. 证据（本地 SDK 文档 + 我们自己的表扫描）

### 1.1 护甲重量因子 F / S 的消费点（SDK `docs/armor-stats.md`，与 hd2runtime 0.30.3 同源）

- **F（stamina factor，轻/中/重 = 0.75 / 1.0 / 1.5）**：
  > “F goes to the avatar … **scales stamina drain and regen alike, and the jump, dive, climb and slide costs**.”
  ⇒ 直接对应 Avatar 的 `SprintStaminaDecayDuration`、`JogStaminaDecayDuration`、
  `StaminaRecoverTime{Stand,Crouch,Prone}`、`StaminaCost{Jump,Dodge,Climb,Slide}`（vault 消耗为 0，未点名）。
- **S（speed factor，1.1 / 1.0 / 0.9）**：
  > “**S to its locomotion speed slot 3** … S is written into the locomotion record and smoothed there,
  > but **no reader of that product was found statically**.”
  ⇒ S 写进 avatar 的 locomotion 记录（就是 `AvatarComponentData` 这类记录）的**速度槽 3**，但“怎么消费”未证。
  注意：`MoveInfo.Speeds` 的顺序是 `[ReversingMultiplier(0), Aim(1), Walk(2), Jog(3), Sprint(4), …]`
  ⇒ “槽 3” 很可能是 **Jog**（与 §1.2 的 Oxygenator 指向 jog 互相呼应，但**待实测**）。
- **生命周期**：护甲值每次命中生效；**speed / stamina 在下一次 armor apply（重生或换甲）**才写入 avatar。

### 1.2 护甲被动键 ↔ Avatar 概念（SDK `ArmorPassiveCatalog.json`，32 个被动逐行有 key_name/reader）

| 被动 | key | 类型/值 | reader | 对应 Avatar 概念 |
|---|---|---|---|---|
| 38 OXYGENATOR | `movement_speed` (`CD79A687`) | Multiply ×1.1 | **data-driven：jog** | `MoveInfo.Speeds.Jog` |
| 38 OXYGENATOR | `unknown_f6d67313` | Multiply ×1.1 | **data-driven：sprint** | `MoveInfo.Speeds.Sprint` |
| 38 OXYGENATOR | `slide_boost` (`6938BD56`) | Set 0 | direct | 滑步族（具体字段未钉死） |
| 8 SERVO-ASSISTED | `throw_range` (`26C969A1`) | Multiply ×1.3 | direct | `Short/LongThrowInfo.PowerMultiplier`（1.4） |
| 12 PEAK PHYSIQUE | `weapon_ergonomics` (`C8CCB6FA`) | Add 30 | direct | `MinAimDuration/MaxAimDuration/MinFireReadyDuration/MaxFireReadyDuration` |
| 41 TRUE GRIT | `weapon_ergonomics` (`C8CCB6FA`) | Add 20 | direct | 同上 |
| 31 FEET FIRST / 32 REDUCED SIGNATURE | `movement_noise` (`AF8B7112`) | Multiply ×0.5 | direct | `MoveInfo.SprintNoiseRadius`（10） |
| 2 SCOUT / 32 REDUCED SIGNATURE | `enemy_detection_range` (`14ECCE15`) | Multiply ×0.7 / 0.6 | direct | `DetectionInfo.SightModifier*`（1 / 0.75 / 0.5） |
| 3 FORTIFIED / 6 ENGINEERING KIT | `crouch_prone_recoil` (`C36935A9`) | Multiply ×0.7 | direct | `ExertionLevels[].Sway*` / 武器后坐（未钉死） |
| 14 UNFLINCHING | `flinch_prevention` (`73734D67`) | Set 0 | direct | 同上（晃动/受击抖动） |
| 34 SUPPLEMENTAL ADRENALINE | `stamina_when_damaged` (`A189ADB6`) | Add 2 | direct | 体力系统（Avatar 体力基准） |

**不属于 Avatar 的护甲被动项**（别混进这条线）：抗性（`fire/arc/gas/explosive/impact/knock_prone/limb` 等）、
容量（`grenade_capacity` `stim_capacity`）、武器 stat（`primary/support/sidearm reload`、`ammo_capacity`、
`sidearm_draw`、`sidearm_recoil`，走 `sm` stat 槽 11–17）、`lethal_damage_survival`、`chest_bleed_prevention`、
`radar_scan_interval` ⇒ 属于 Health / Inventory / Weapon / Status 系统。

### 1.3 定制（customization）通道会**直接覆盖 Avatar 字段**：全 build 只有 3 个 entity delta

用新工具 `tools/avatar_deltas.py` 扫 `generated_entity_deltas.dl_bin`（572 个 delta key）：
写 `AvatarComponentData`（本 build 组件索引 **235**）的 delta 只有 3 个：

| delta key | 覆盖的 Avatar 字段 | 值 | hd2runtime 记录 |
|---|---|---|---|
| `0x73012E9238B6E3B9` | `Speeds.Walk` / `Speeds.Jog` | 1.5 / 4.08 | 船上 avatar 的私有副本 ✓ |
| `0x7CBC47149F781994` | `SprintStaminaDecayDuration` / `StaminaRecoverTime{Stand,Crouch,Prone}` | 4 / 18 / 16 / 14 | “sprint decay 4、recover 18/16/14”**（归属未解）** |
| `0x42654E8989043F96` | `LongThrowInfo.PowerMultiplier` | 1.85 | “long-throw power 1.85”**（归属未解）** |

- 语义：游戏**在 spawn 时用 entity delta 给 avatar 做私有副本**（hd2runtime），所以这三个 delta 就是
  “某个 customization/场景会把 Avatar 字段改成这些值”的证据——**护甲/定制线与 Avatar 表的直接接线点**。
- 归属：三个 key 在**全部 55 张 dl_bin**里都没有其它引用（u64 与 32 位高低半都扫过，0 命中），资源索引
  `all_entries.json` 也 0 命中 ⇒ 只能从资源/代码侧找（与 hd2runtime 的“未解”一致）。待续。
- 顺带：这些值也能被我们改（`generated_entity_deltas.dl_bin` 是可编辑表），但先要弄清是谁触发它们。

## 2. 组合与编辑面（做 mod 前必读）

| 想改的量 | 文件侧入口 | 我们能改吗 | 生效时机 |
|---|---|---|---|
| Avatar 基准（速度/体力/滑步/投掷/潜行/尘土/用力等级…） | `generated_entities.dl_bin`（本页字段图） | ✓（dl_bin 路线，已是验证过的路线） | 启动时读表；任务内即时 |
| 护甲 S/F/A 三张 class 表 | **game.dll 可执行数据段**（RVA 已由上一线钉死） | ✗（dl_bin 路线碰不到；只有内存/可执行数据路线） | armor apply |
| 某套甲的重量档（决定 S/F/A 均值） | `generated_customization_armor_sets.dl_bin` 部件 `+16` | ✓（上一线已实机） | 下一次 armor apply |
| 护甲被动 pm/sm 行（stat 键、武器 stat 槽） | `generated_customization_passive_bonuses.dl_bin` | ✓（上一线已实机） | apply 时/运行期（按 reader） |
| 护甲被动图标/包 | `generated_add_resource_dependencies` 等 | ✓ | 加载期 |

**叠乘关系（待实测确认）**：预计 `实际速度 = Avatar.Speeds.X × S × Σpassive 乘数`，
`实际体力 = Avatar 体力字段 ÷ F × …`；改 Avatar 后轻/重甲差异仍在（S 继续乘）。

## 3. 建议的单变量实验（都很便宜，一次启动可测）

1. **OXYGENATOR jog/sprint 键**：把 `passive_bonuses` 里 perk 38 的 `movement_speed` 从 1.1 改 2.0（pm 行），
   实测 jog 速度；再直接改 Avatar `+0x010 Jog` 对照 ⇒ 证明两条路线是否同量、是否叠乘。
2. **护甲重量 vs Avatar 基准**：把一套甲的 9 个部件档位从 light 改 heavy（上一线工具），测 jog 速度变化；
   与直接改 Avatar Jog 对比 ⇒ 反推 S 到底乘在哪些速度槽（“slot 3”是不是 Jog）。
3. **SERVO-ASSISTED throw_range**：×1.3 → ×3，测投掷距离；再改 Avatar `+0x130 LongThrowInfo.PowerMultiplier` 对照
   （delta 里的 1.85 也提示投掷距离就是该字段的函数）。
4. **PEAK PHYSIQUE weapon_ergonomics**：+30 → +100，测举枪/瞄准时间；对照 Avatar `+0x334…+0x340`。
5. **体力 F**：轻甲 vs 重甲测冲刺耗尽时间/恢复时间；对照 Avatar `+0x034/+0x03C…`（预期：F=1.5 时 23 s → 约 15 s）。

## 4. 结论

- **可以联系起来**：护甲线的 S/F 因子与被动键，改的是**Avatar 基准字段的乘数/消费端**；
  F 与体力字段一一对应（文档明确），OXYGENATOR 直接指向 jog/sprint，投掷/工效/噪音/侦测也各有对应概念。
- **三层模型**是正确姿势：基准（Avatar 表）· 乘数（护甲/被动 stat）· 展示（军械库）。
  之前两条线并不冲突，只是各自站在不同层。
- **最强的新证据**：全 build 只有 3 个 entity delta 直接写 Avatar 字段（含 hd2runtime 没解开归属的两个），
  说明“定制 → Avatar”是真实存在的通道；下一步把它们的归属解出来，就能做“按 spawn/按装备生效”的 Avatar 修改。
- **可执行面**：Avatar 字段（dl_bin ✓）、护甲 kit 档位（✓）、被动行（✓）；game.dll 三张 class 表（✗，非本路线）。

## 5. 复跑

```bash
# 3 个写 AvatarComponentData 的 entity delta + 字段名
python tools/avatar_deltas.py
# 护甲被动键/类型的原始数据（之前护甲线的两个参考文件）
python - <<'PY'
import json
d=json.load(open(r'D:\mod\c11-recon\sdk-0.30.3\ArmorPassiveCatalog.json',encoding='utf-8'))
print([(p['id'],p['name'],[m['keyName'] for m in p['modifiers']]) for p in d['passives']])
PY
```
