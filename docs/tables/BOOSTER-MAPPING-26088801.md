# Booster 的调谐标量 `+0x08` 与明文表的映射关系（build `26251122`）

> **一句话**：`game.dll` Booster 表 `+0x08` 是**标量（scalar）**，不是指针/索引 —— 代码在
> `IsBoosterActive()` 判定之后直接读它参与各自公式；**表与明文表之间没有指针链**，
> "映射"发生在代码里，落点分四种形态。耐力这条：`1.3` 作用在
> `AvatarComponentData` 的**体力时长/消耗**字段上（**排空速率 ÷ 1.3**）。

## 0. 三态

| 结论 | 态 | 证据 |
|---|---|---|
| `+0x08` 是标量、不是明文表的索引/指针 | **✓ 三方一致** | ①值域与形态（0.0–10.0，含 0.05/0.15/0.35 等分数值）②第三方原生追踪：表 0x38 行、`+8` = tuning scalar、`+4` = granted `StratagemType`，"**25 处读、0 处写**"③ARP 的 `+0x08 = 0.0`（它的效果是生成实体，没有标量可乘）|
| `+0x04` = 关联战备（granted `StratagemType`）| **✓ 三方一致** | 我们：Surplus EAT `+0x04 = 15` = EAT 复制体战备 id；第三方：该行的授予类型名 `StratagemType_LATOneshot_Booster` |
| 耐力的基线值在 `AvatarComponentData`（明文实体表）| **✓ 双源** | 本仓库字段图（852 B / 207 字段，typelib 28/28 对齐）+ filediver 的 Go 结构注释 |
| `1.3` 在这条上 = 排空速率 ÷ 1.3 | **✓ 双源** | 第三方 `booster.stamina_scale = 1.3`，消费方式写明 "drain ÷ v"；同一文档在 `stamina_sprint_duration` 注释里写 "(÷ 1.3 with modifier 2)" |
| wiki 的 +22.5% 上限 / +40% 回复 与 1.3 的对应关系 | **⚠ 未证** | 同一 Booster 的三条效果，代码里可能是三条公式/常量；单看 1.3 推不出 1.225/1.4 |
| 标量就是"倍率"这件事本身 | **✓ 我们自己核过一对** | `FLEXIBLE REINFORCEMENT BUDGET +0x08 = 0.75` ↔ wiki「reduces the 2:00 cooldown to **1:30**」= 120 s × 0.75 = 90 s，**逐值吻合**（不依赖第三方） |

## 1. `+0x08` 不是指针：三条独立判据

| 判据 | 内容 |
|---|---|
| **值域形态** | 全 21 行取值 `0.0 / 0.05 / 0.15 / 0.35 / 0.5 / 0.7 / 0.75 / 0.9 / 1.0 / 1.3 / 1.5 / 10.0` —— 若是指针或行号，不可能出现 0.05、0.35 这类值 |
| **外部原生追踪** | 第三方 hd2runtime 的 booster research：`game.dll` 静态表"one 0x38-byte row per enum value，行的 tuning scalar 在 `+8`，granted `StratagemType` 在 `+4`"，代码示例 `if IsBoosterActive(Vitality) damage = int(damage * table[Vitality].scalar)`，并断言 **"25 instructions read the table and none write it"**、跨 3 个快照字节一致 |
| **自洽反例** | ARP 的 `+0x08 = 0.0`：它的效果是"代码生成一台炮塔实体"，没有任何可乘的标量 —— 与"标量"解释完全自洽 |

⇒ 结论：**这张表是"标量 + 关联战备 + 本地化 id"的纯元数据表**，不含任何指向 `generated_*.dl_bin` 的引用。
（唯一像"引用"的是 `+0x04`，它指向**同族战备**，不是明文表行。）

## 2. 四种映射形态（标量最终落在哪）

| 形态 | 例子 | 明文落点 | 代码怎么用 |
|---|---|---|---|
| **A. 标量 × 明文字段** | Vitality 0.9、Stamina 1.3、Muscle 0.35、UAV 1.5、Flexible 0.75、Localization 0.9、Extraction 0.7、Motivational 0.5、Extinguishers 0.5 | **`AvatarComponentData`**（玩家实体 852 B）等实体组件 | 读基值再乘/除标量 |
| **B. 标量作阈值/计数** | Sample Scanner 0.15（掉率阈值）、Sample Extricator 10（上限）、Dead Sprint 0.05（血量地板）、Reinforcement +1 | 无（纯逻辑） | `random < v` / `count < int(v)` / 血量 ≥ v |
| **C. 无标量，代码按字面 type 选明文行** | Firebomb → 爆炸 `83`；Stun Pods → `335`；Concealed Insertion → 烟雾；Experimental Infusion → 状态 `29`（替代 `25`）| **爆炸表 / 伤害表 / 状态表** | 硬编码字面量，落在明文表里的**某一行** |
| **D. 数据引用（非标量路径）** | ARP（`StratagemInfo` 的战备 booster 列表）、Surplus EAT（`+0x04` 授予战备）| **战备表 / 实体表** | 数据侧直接给 |

→ 所以"Booster 强度会不会指向明文表里的某一项"的答案是：**不指向**；但它**落到**明文表的**字段**（形态 A）
或**整行**（形态 C）上 —— 这就是"映射关系"的真身。

## 3. 耐力专题：`1.3` 到底作用在哪些字段上

### 3.1 基线（明文，`AvatarComponentData` 第 0 条记录，852 B）

| 偏移 | 字段 | 原版 | 说明 |
|---|---|---:|---|
| `+0x034` | `SprintStaminaDecayDuration` | **23 s** | 满体力冲刺耗尽所需秒数 |
| `+0x038` | `JogStaminaDecayDuration` | 300 s | 慢跑耗尽（地形慢跑实际读 `+0x34`）|
| `+0x03C` / `+0x040` / `+0x044` | `StaminaRecoverTime` 站/蹲/趴 | 7 / 6 / 5 s | 回满所需秒数 |
| `+0x048` | `StaminaRecoverDelay` | 1.5 s | 消耗后多久开始回 |
| `+0x04C` / `+0x050` / `+0x054` / `+0x058` / `+0x05C` | 跳/飞扑/翻越/攀爬/滑步 消耗 | 0.2 / 0.1 / 0 / 0 / 0.05 | 体力是 0..1 的分数 |

> 体力不是独立的组件类型（实体表里**没有** `StaminaComponentData`）——全部在 `AvatarComponentData` 的 `MoveInfo` 段里。

### 3.2 映射式

```
每帧：stamina -= cost_multiplier × dt / SprintStaminaDecayDuration        （有 Booster 时 ÷ 1.3）
每帧：stamina += regen_multiplier × dt / StaminaRecoverTime               （有 Booster 时另有回复加成）
```

- `+0x08 = 1.3` ⇒ **冲刺可跑时长 23 s × 1.3 ≈ 29.9 s**（排空速率 ÷ 1.3 = 时长 × 1.3）；
- wiki 另外写的 **最大体力 +22.5%、回复 +40%** 是同一 Booster 的另两条效果（wiki 示例：护甲 100 的回复 100 → 140）；
- ⇒ `1.3` **不能**被读成"+30% 全能"：它只是代码里那一条公式的除数。

### 3.3 数据侧等效做法（不装 Booster）

想要同样的效果又不碰 `game.dll`，直接改玩家实体的 `AvatarComponentData`（保哈希写，工具链已验证）：

| 目标 | 改哪 | 原版 → 等效 |
|---|---|---|
| 冲刺时长 +30% | `+0x034` | 23 → **29.9** |
| 站立回满 +40% 速率 | `+0x03C` | 7 → **5.0** |
| 最大体力 +22.5% | ⚠ 该字段不在本记录（是运行期 `max stamina`，未在本表里定位）| 待查 |

```bash
python tools/entity_fields_batch.py set --block <AvatarComponentData 块> --key <玩家实体键> \
    --field 0x034=f32:29.9 --field 0x03C=f32:5.0 --out out/avatar-stamina.plain
```
（`--block`/`--key` 取值照 [AVATAR-HELLDIVER-FIELDS](../cases/AVATAR-HELLDIVER-FIELDS-26251122.md) §5 的配方）

## 4. 与第三方（hd2runtime）的对照口径 —— 它那张快照是**旧版本**

hd2runtime 的 booster research 来自快照 `F5FEE03DCFDB`，**不是本 build**。可用/不可用要分开：

| 可借用（代码语义，跨版本稳定） | 不可借用（号段，逐 build 会漂） |
|---|---|
| 表结构：0x38 行、`+8` 标量、`+4` granted `StratagemType`、25 读 0 写 | **爆炸 type 号**（它写 Concealed Insertion = `400`）|
| 标量的消费方式（`int(damage * v)`、`drain ÷ v`、`random < v`…）| **状态 id / DamageInfo id**（它写 Dead Sprint = status 59 / `DamageInfo 541`）|
| "ARP 与 Surplus EAT 是 data-driven、不走 `IsBoosterActive` 门" | 具体战备 id |

**证据：它写的 `400` 在本 build 站不住。** 本 build（且 build 25988413 逐行一致）里
`type 400` = `ExplosionType_Tower_Collapse`（row 351：伤害行 495、半径 20/40/70、震屏 5000），
与"烟雾、无伤害、半径 5/5"完全不符；符合描述的是 `type 401`（row 194：伤害行 0、半径 5/5/0、
震屏 0、有粒子，紧邻 83/335 两行）。

⇒ **本仓库口径**：Concealed Insertion = 爆炸 **`401`**；`400` 视为旧 build 号段，不采纳。
（附带说明：ARP/Surplus EAT 两条与它的结论一致，因为这俩不依赖号段。）

**同理 Dead Sprint 的 status 59** 也只是旧号：本 build 里 status `59` 每跳伤害行为 0，
而 `DamageInfo 541`（15 伤害 / AP0 / 元素 2=Arc / 硬直 100）挂在 status **`36`** 上 ——
本 build 的 Dead Sprint 到底用哪个状态 id，**仍未解**（别照抄 59）。

**唯一"现役可用"的交叉点**：Firebomb（`83`）与 Stun Pods（`335`）两边**逐字段完全一致**
（200/200、AP10、Fire 20、2/4/4 / 50/50、AP10、Stun Massive 100、2/4/4）—— 这两条已闭环。

## 5. 复现

```bash
# 1) Booster 表 21 行（+0x04 / +0x08 / locids）
python - <<'PY'
import struct, pathlib
b = pathlib.Path(r"D:/SteamLibrary/steamapps/common/Helldivers 2/data/game/game.dll").read_bytes()
for i in range(21):
    o = 0x2CB4840 + i*0x38
    item, g4 = struct.unpack_from('<2I', b, o)
    f8 = struct.unpack_from('<f', b, o+8)[0]
    gC = struct.unpack_from('<I', b, o+12)[0]
    print(i, item, g4, f8, gC)
PY

# 2) 玩家体力基线
python out/_scratch/deep_arp.py 0x73681FFD58FA1A90   # 模板：任意实体的组件行 dump
#    或按 AVATAR-HELLDIVER-FIELDS §5 用 entity_fields_batch show --block ... --field 0x034

# 3) 三条投送舱爆炸行
#    见 docs/explosions/POD-IMPACT-EXPLOSIONS-26088801.md §2
```

**来源**：
- 第三方原生追踪与字段命名：`D:/mod/c11-recon/sdk-0.30.3/docs/booster-authoring.md`（hd2runtime SDK，
  snapshot `F5FEE03DCFDB`；其原文同时给出 13 条标量的字段名、消费公式与 wiki 对照）、
  `.../docs/helldiver-fields.md`（体力语义）。
- 明文基线值：`refs/dlbin/plaintext-26251122/generated_entities.dl_bin` +
  `docs/cases/AVATAR-HELLDIVER-FIELDS-26251122.md`。
- wiki：Stamina Enhancement（+22.5% 上限 / +40% 回复、护甲-回复表）。
