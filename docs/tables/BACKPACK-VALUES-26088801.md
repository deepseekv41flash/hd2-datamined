# 背包自身属性：字段表与改法（build 26088801）

> 目标：**改一件背包自己的数值**——跳跃冷却、跳跃高度、补给的次数、护盾半径/耐久、位移距离……不涉及"给别的背包加能力"（那条线已否证，见 [BACKPACK-LINE §8](BACKPACK-LINE-26088801.md)）。
> 所有字段名都是 `✓` 证据：**类型名**来自本 build 的 typelib（`tools/typelib.py`，引擎剥掉了成员名但**保留了类型名**），
> **语义名**来自 HD2Runtime 的 `schemas/entity_fields.json`（pinned build 与本 build 同源 `F5FEE03DCFDB`），两者**逐条偏移对上**。
> 三态：`✓` 离线读过字节；`✓✓` 实机验过；`✗` 否证；`⚠` 未证。

## 1 字段表（`✓` 全表现算）

### 1.1 跳包族（`JumppackComponentData` 块 `0x54270608`，stride 280）

| 偏移 | 类型 | 语义名 | Jump Pack | HOVER PACK | Dark Fluid |
|---|---|---|---|---|---|
| `+0x000` | f32 | **`jump.vertical_launch_velocity`**（起跳垂直速度，m/s）| **40.0** | 40.0 | 35.0 |
| `+0x004` | f32 | （未命名；疑似水平/滞空参数）| 20.0 | 20.0 | 20.0 |
| `+0x008` | `CApiVector3` | 未命名向量 | 0,0,0 | — | — |
| `+0x048…+0x060` | `AbilityId` ×6 | 能力 id（跳包行 = **2055–2060** 连号）| 2055–2060 | — | — |
| `+0x09C` | f32 | **`hover.duration`**（悬停时长，s）| **−1.0**（无悬停）| **6.0** | −1.0 |

配套冷却：**`RechargeComponentData`**（块 `0x1F42878E`，stride 4）

| 偏移 | 类型 | 语义名 | Jump Pack | HOVER | Dark Fluid |
|---|---|---|---|---|---|
| `+0x000` | f32 | **`recharge.time`**（使用间隔，s）| **15.0** | 11.5 | 8.0 |

⇒ **"跳跃冷却" = `Recharge+0x00`；"跳跃高度" = `Jumppack+0x00`（速度 ∝ √高度，40→60 ≈ 2.25 倍高度）**。

### 1.2 补给 / 弹药背包（`DepositComponentData` 块 `0xC435BA85`，stride 152）

| 偏移 | 类型 | 语义名 | Supply Pack | 说明 |
|---|---|---|---|---|
| `+0x000` | u32 | **`deposit.capacity`**（总充能数）| **4** | 用户口语的"补给次数" |
| `+0x004` | i32 | **`deposit.start_amount`**（出场自带）| **4** | 必须与上一条同步改，否则出场只有旧数量 |
| `+0x008` | u32 | **`deposit.refill_amount`**（每次补给给几发）| **1** | 补给站/空投补给它时恢复的数量 |
| `+0x020` / `+0x024` | `AbilityId` | 存取动作的能力 id | 2636 / 0 | — |
| `+0x080` | `DepositRefill` | 补满行为枚举 | 3 | — |

> ⚠ HD2Runtime 把补给包这三格标为 **read-only**（"没有公布值证明它们的充能含义"）⇒ 本文件第一轮就是去证它。

### 1.3 护盾背包（`ShieldComponentData` 块 `0x5154DB66`，stride 344）

| 偏移 | 类型 | 语义名 | Shield Generator Pack |
|---|---|---|---|
| `+0x000` | f32 | **`shield.radius`**（m）| 1.3 |
| `+0x04C` | f32 | **`shield.durability`**（护盾血量）| 150.0 |
| `+0x058` | f32 | **`shield.recharge_delay`**（受伤后回充延迟，s）| 60.0 |
| `+0x05C` | f32 | **`shield.broken_recharge_delay`**（破盾后重启延迟，s）| 12.0 |
| `+0x060` | f32 | **`shield.recharge_rate`**（回充速度，hp/s）| 150.0 |
| `+0x06C` | `StatusEffectType` | 破盾施加的状态 | — |
| `+0x144` | `ShieldShapeType` | 形状枚举（球=0，定向不是球）| — |

（SH-20 弹道盾的甲在 **`HealthComponentData` 的伤害区**里，`zone.armor`；SH-51 定向盾本体在 `entity.health`/`entity.armor`：见 HD2Runtime `docs/backpack-authoring.md`。）

### 1.4 位移/Warp 背包（`DisplacementComponentData` 块 `0xA7813546`，stride 632）

| 偏移 | 类型 | 语义名 | Warp Pack |
|---|---|---|---|
| `+0x078` | f32 | `warp.distance`（m）| 10.0 |
| `+0x080` / `+0x084` | f32 | `warp.upward_bias` / `downward_bias` | 1.4 / 4.0 |
| `+0x08C` / `+0x090` | f32 | `warp.safe_heat_threshold` / `unsafe_…` | 15.0 / 45.0 |
| `+0x094` | f32 | `warp.heat_per_use` | 33.0 |
| `+0x098` | f32 | `warp.heat_cooldown_per_second` | 6.0 |
| `+0x0A4/0x0BC/0x0D4/0x0EC/0x104` | f32 | `warp.{head,left_arm,right_arm,left_leg,right_leg}_injury_damage` | 10/35/35/45/45 |

## 2 改法：一条命令一个字段

```bash
python tools/entity_field_set.py set --block 0x1F42878E --key 0x59C5CA839449B379 \
    --field 0x00 --type f32 --value 5 --expect-old 15 \
    --plain <base>.plain --out <next>.plain
# 门禁必须全过：G1 长度 / G2 差异范围 / G3 重算 murmur64 == 原值 / G4 读回 / G7 旧值 == 期望 / G8 校正字 / G6 容器自洽
```

- 多字段链式：把上一次的 `--out` 当下一次的 `--plain`（哈希每步都保住，安全）。
- `--type` 支持 `u32 / i32 / f32 / u64`（u64 用于 `Unit+0x00` 这类资产 id）。
- 组件块 id 一览：`Jumppack 0x54270608`、`Recharge 0x1F42878E`、`Deposit 0xC435BA85`、`Shield 0x5154DB66`、`Displacement 0xA7813546`。
- **坑**：同一 id 的多条 `.patch_N` 之间按索引覆盖（pitfall #9）：把改动打进**新索引**的补丁时，必须把同一 id 的其它改动字节一起带上。

## 3 第一轮实验（2026-10-26 21:1x 已装，`⚠` 待实机）

基线 = `out/jumpsupply/before.plain`（= 原版 + rack 47 暗液体）。五处改动，三个可独立观察的件：

| # | 件 | 字段 | 原值 → 新值 | 观察点 |
|---:|---|---|---|---|
| 1 | **Jump Pack** | `Recharge+0x00` `recharge.time` | 15 → **5 s** | 两次跳跃的最短间隔（手感 + 若有 HUD 条则看充能速度）|
| 2 | **Jump Pack** | `Jumppack+0x00` `vertical_launch_velocity` | 40 → **60** | 跳得更高（√比例约 2.25 倍高度）|
| 3 | **Supply Pack** | `Deposit+0x00/0x04` `capacity`/`start_amount` | 4/4 → **8/8** | 补给包总次数是否为 8（HUD 数字/用尽时机）|
| 4 | **Shield Generator Pack** | `Shield+0x00` `shield.radius` | 1.3 → **2.0 m** | 护盾泡明显变大 |

（其余全部原版：`refill_amount` 仍 1，护盾耐久/回充、Warp 全套未动。）

**判读**

| 现象 | 结论 |
|---|---|
| 1 冷却明显变短、2 跳更高、3 次数变多、4 护盾变大 | 四个字段语义全部 `✓✓` 确认 ⇒ 本节字段表可直接当"背包数值编辑器"用 |
| 只有部分生效 | 逐条看：跳高不生效 ⇒ 高度还吃 `+0x04`/其它标量；补给次数不生效 ⇒ 走的是 `refill_amount` 或弹药池；护盾半径不生效 ⇒ 半径可能是 `+0x144` 形状参数派生 |
| 全不生效 | 说明这些组件在**装备生成时被复制**进实例，改动只影响**新召唤**（背包要重新呼叫，不能热改）|

**装盘记录**

| 项 | 值 |
|---|---|
| 注入件 | `data/game/generated_entities.dl_bin` = `out/bkval/p1e.dl_bin`（md5 `4f60109d34b6c315e3e1fc6b964507f6`，47,259,496 B）|
| 明文 | `out/bkval/p1e.plain`（sha256 `c994ca76…65ccf9a`，round-trip 一致）|
| 读回 | Jump `recharge=5.0` / `launch=60.0`；Supply `capacity=8` `start=8` `refill=1`；Shield `radius=2.0` |
| 回滚 | `cp out/jumpsupply/entities.before-jumpsupply "<game>/data/game/generated_entities.dl_bin"`（md5 `dc744d3e2fa00fd429d0e6bb5aabb690`）|

## 4 相关

- 字段来源与资料盘点：[BACKPACK-LINE §7.4](BACKPACK-LINE-26088801.md)
- 组件几何（块 id / stride / 行数）：[ENTITY-TABLE-25988413](ENTITY-TABLE-25988413.md)
- 保哈希改字段的通用原语：[FILE-ROUTE-WORKFLOW](../cases/FILE-ROUTE-WORKFLOW-26088801.md)
