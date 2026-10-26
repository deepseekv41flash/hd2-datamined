# 背包线开线档：Dark Fluid Vessel 的物品 id 与背包相关表（build 26088801）

> 起因：想做未发布战备 **Dark Fluid Vessel**。本文只记**已查到的事实**（物品 id / 资产 / 包 / 相关表几何 / 35 件背包普查），
> 以及可走的两条投放路线。三态：`✓` 离线可复算 · `⚠` 未验 · `✗` 否证。

## 1 Dark Fluid Vessel = 哪个物品（`✓`）

| 项 | 值 | 怎么得到的 |
|---|---|---|
| 战备行 | **id 30**，内部名 `MISSIONS. DARK FLUID BACKPACK` | 战备表 ASCII + `stratagem_extra --show` |
| 行基址 | `0x07DEC`（`+0x00`=30，`+0x10`=0x4784 指向内部名字符串 @0x9810） | 按 id 扫行 + 字符串偏移校准 |
| 行 `+0xA8`（声明包）| **`0xD87885C7EAACE597`** | 该行直接读 |
| **物品实体** | **`0x073270650F859DD0`** | 从包里的资产名反查：包内有 `physics/mesh 0x0E4E0A4947D5BFBE` 名 **`…ion_dark_fluid_backpack`**，再在全表 `UnitComponentData+0x00` 里搜它 |
| unit 资产 | `0x0E4E0A4947D5BFBE`（mesh 6,608 B / GPU 320,324 B）| 同上 |
| 自身 `LoadoutPackage+0x08` | `0xD87885C7EAACE597`（与战备行一致）| 组件行读 |
| `LoadoutEntry`（背包目录 id）| **0**（未注册进目录）| 组件行 `+0x00` = 0；`+0x04` = **6**（猜测=物品种类枚举，背包类）|
| 名字表显示 | **"Chemical Backpack"**（与 `0x43EC60F66E7E046B` 同名，共用条目）| `entity-locid-names` |

⇒ 它是**背包类**（`BackpackComponentData` 有行），但**没有 LoadoutEntry id** ⇒ 正常配装界面选不到；要靠"额外战备"或"投送舱换载荷"塞进去。

## 2 它的组件行内容（`✓` 逐块读）

| 组件块 | 块 id | stride | 本件行要点 |
|---|---|---:|---|
| `BackpackComponentData` | `0x49B8E93D` | **1** | `01` —— **纯标记位**（"这是个背包"），不是参数表 |
| `JumppackComponentData` | `0x54270608` | **280** | 有整行配置（含 2503–2506 等 id、多组 `1.0/0.15/20.0` 浮点）⇒ 它同时挂了"跳包"逻辑 |
| `EquipmentComponentData` | `0x5357A825` | **232** | `+0x00` = `0x4FDD3337` |
| `AttachableComponentData` | `0xBCF41716` | 64 | `+0x00` = `0xA3D491D1` |
| `WieldableComponentData` | `0x3BF780F6` | 32 | `01` / 结尾 `01` |
| `RechargeComponentData` | `0x1F42878E` | **4** | `0x41000000` = **f32 8.0** |
| `ObjectiveCarryComponentData` | `0xE1C4B569` | 128 | 有整行（任务"搬运"逻辑，暗液体是任务物件）|
| `MaterialSwapComponentData` | `0x3A4683F7` | **1888** | 有整行（材质替换表）|

## 3 背包相关"表"清单（开线用的地图，`✓` 块 id/stride 现算）

| 组件块 | id | stride | 行数 | 说明 |
|---|---|---:|---:|---|
| **`BackpackComponentData`** | `0x49B8E93D` | **1** | **35** | **背包种类总表**（见 §4）|
| `JumppackComponentData` | `0x54270608` | 280 | — | 跳包/推进参数 |
| `EquipmentComponentData` | `0x5357A825` | 232 | 352 | 装备通用（含 `Equipment` 类型）|
| `AttachableComponentData` | `0xBCF41716` | 64 | — | 可挂载（含 `+0x20` 距离=180 默认）|
| `WieldableComponentData` | `0x3BF780F6` | 32 | — | 可持握 |
| `RechargeComponentData` | `0x1F42878E` | 4 | — | 单个 f32（本件 8.0）|
| `ObjectiveCarryComponentData` | `0xE1C4B569` | 128 | — | 任务搬运 |
| `LoadoutEntryComponentData` | — | 32 | 199 | 目录条目；本件 id=0 ⇒ 未注册 |
| `LoadoutPackageComponentData` | — | 32 | — | `+0x08` = 资源包 |
| `HellpodRackComponentData` | `0xA98BB156` | 568 | 73 | 投送舱槽位（换载荷用）|
| `MountComponentData` | — | 120 | 165 | 载具挂载（若要做"车载背包"）|

## 4 背包全家：`BackpackComponentData` 一共 35 件（`✓`）

已发布（游戏内可拿到的）：
`Airburst Rocket Backpack` · `Apex Backpack` · `Autocannon Backpack` ×2 · `Ballistic Shield Backpack` ×2 ·
`Belt-Fed Grenade Launcher Backpack` · `Guard Dog` ×3 · `Dog Breath` · `Hot Dog` · `K-9` · `Rover` ·
`Directional Shield` · `Shield Generator Pack` · `Supply Pack` · `Recoilless Rifle Backpack` ×2 · `Spear Backpack` ×2 ·
`Jump Pack` · `Warp Pack` · `W.A.S.P. Launcher Backpack`

**疑似未发布 / 事件件**（名字就是这些）：
`BACKPACK` ×2（`0xF5C67AED5CB5ACA0` / `0x8726D02AEAF98E86`）· `MEDIC BACKPACK`(`0x0A55E504092B981D`) ·
`HOVER PACK`(`0x5EC80F4F1CDB66CF`) · `Chemical Backpack`(`0x43EC60F66E7E046B`) ·
**`Chemical Backpack` = Dark Fluid Vessel(`0x073270650F859DD0`)** · `Cremator Backpack`(`0x43EB1C3C1A1860E0`) ·
`Maxigun Backpack`(`0x056DE1C5E21E723E`) · `Portable Hellbomb`(`0x9ACE8638421ABC8E`) · `C4 Pack`(`0x2A18F81C44A26771`) ·
`Larva Container`(`0x9EA89CEEA6F8E766`)

> 这 35 行是**背包线的种子清单**：每件只要 `Unit+0x00`（资产）+ `LoadoutPackage+0x08`（包）就能定位模型与资源。

## 5 两条投放路线

| 路线 | 做法 | 状态 |
|---|---|---|
| **A. 额外战备** | 战备表链 `Resupply(34) → Dark Fluid Vessel(30) → Solo Silo(92)`，行 30 的 `+0xA8` 本来就是 `0xD87885C7EAACE597` ⇒ 呼叫时应自带包声明 | `⚠` 未单独验（**同场会污染 B 的资源归因**，见 §5.1）|
| **B. 投送舱换载荷**（已装，`✓✓` 实机）| rack **47**（MG-43 支援武器的舱，`spawn=1`）槽 0/1 = **`0x073270650F859DD0`**；`+0xA8` 保持 MG-43 的包（舱体本身要渲染），另加**整包驻留** `patch_17` = 包 `d87885c7eaace597`（toc 579,808 `5c75c825604ecbbb` / gpu 5,991,744 `8ec10d4faa58ad71` / stream 23,549,712 `0ad289dd8cd2c33a`）| **`✓✓`：舱里出容器模型，能捡起、能背上** |

### 5.1 归因更正 → 已隔离（2026-10-26 20:3x，`✓✓`）

**第一轮（20:1x）**：B 首测时 **A 也被保留在同一局里**，而 A 的战备行 `+0xA8` 指向的**正是同一个包** `d87885c7eaace597`
⇒ 当时无法把"资源被解析"归给 `patch_17`（声明口 / 驻留 / 别的东西已加载，三者都能解释）。
⇒ 当时只敢写：`✓✓` **投送舱能送背包件、能捡起背上**；**不写**"资源靠驻留"。

**隔离轮（20:3x）**：把战备表**恢复原版**（撤掉 `34→30→92` 链，A 不在场），**保留** `patch_17` 与 rack 47，
再叫一次 MG-43 —— **仍然出容器模型、仍能背上**。

⇒ **结论（单变量，`✓✓`）**：**驻留单独够用**。投送舱送外来背包件的配方与武器件/炮塔件一致：

| 步骤 | 做法 |
|---|---|
| 1 | `pod_rack_swap.py edit --rack <宿主舱> --slot0/--slot1 = <物品实体>`（两个参数都要显式给，见 §5.2）|
| 2 | 目标物品**自己的包**做整包驻留（=`LoadoutPackage+0x08`，本件 `d87885c7eaace597`）|
| 3 | 宿主战备行的 `+0xA8` **保持原值**（舱体/轨道投送本体靠它渲染），**不需要**改成新物品的包 |

**战备声明的角色**：至少对这个包而言，`+0xA8` 声明**不是**投送舱路线解析资源的必要条件（A 撤掉后照样亮）。

### 5.2 复现时的一个坑（本轮踩到）

`pod_rack_swap.py` 的 `--slot0` / `--slot1` **带默认值**（`GL-21` / `B-1 Supply Pack`）；
只给 `--slot0` 会让槽 1 被静默写成 B-1 Supply Pack，而门禁 G4 仍报"2 处读回一致"。**两个参数都要显式给出**，或事后 `show` 回读。

## 6 相关

- 投送舱换载荷：[POD-RACK-26088801](POD-RACK-26088801.md)
- 战备额外条目：[UNRELEASED-STRATAGEMS-26088801](UNRELEASED-STRATAGEMS-26088801.md)
- 实体表字段图：[ENTITY-TABLE-25988413](ENTITY-TABLE-25988413.md)

## 7 背包的"特性"由哪些字段控制（`✓` 35 件全扫）

**`BackpackComponentData` 只是一字节标记**（`01`），不携带任何参数 ⇒ 一件背包的"特性"取决于**它有哪些专用组件**。
35 件里"非通用组件"的出现次数：

| 组件 | 件数 | 控制什么 |
|---|---:|---|
| `AbilityComponentData` | **35** | 槽位存在，但 35 件的行都是 `{0xC,0}×4`（**无 id**）⇒ 背包的主动效果**不走 ability 槽** |
| **`DepositComponentData`** | **23** | 最普遍的"功能件"标记（可存放/取出类，补给/弹药/狗类都有）|
| `BehaviorComponentData` | 4 | 有 AI/行为（狗类、暗液体、便携地狱火）|
| `VisibilityMaskComponentData` / `TwoPointChainComponentData` | 3 / 3 | — |
| **`JumppackComponentData`** | **3** | **跳/悬浮能力本身**（Jump Pack、HOVER PACK、暗液体）|
| **`RechargeComponentData`** | **3** | 与上一条**同现**：单个 f32 = 使用间隔（**15 / 11.5 / 8 s**）|
| `ObjectiveCarryComponentData` | 3 | 任务搬运（暗液体、Larva 等）|
| `ShieldComponentData` | 1 | 护盾背包的护盾参数（另有 `ShieldControllerComponentData` / `HitReact` 各 1）|
| `InteractableMinigame` / `InteractableObjectiveTerminal` | 1 / 1 | 便携地狱火的交互玩法 |
| `MaterialSwapComponentData` | 2 | 材质替换（外观变化）|
| `WeaponDataComponentData` / `MeleeShield` / `Displacement` / `CarryEffect` … | 各 1–2 | 单件特色 |

**三个代表件的"特色组件"（对照就一眼看出差别）**

| 件 | 特色组件 |
|---|---|
| **Jump Pack** | `Ability` + **`Jumppack`** + **`Recharge`** |
| **HOVER PACK** | 同上（只差 `Recharge` = 11.5 s）|
| **Chemical Backpack（暗液体）** | `Ability` + `Jumppack` + `Recharge`(8 s) + `Behavior` + `GroundCheck` + `MaterialSwap` + `ObjectiveCarry` + `ObjectiveDynamicLink` |
| Shield Generator Pack | `Ability` + `Shield` + `HitReact` |

⇒ **"跳/悬浮"这一族的全部特性 = `JumppackComponentData`（参数）+ `RechargeComponentData`（间隔）**。
三件的 `Jumppack` 行**前 4 个 float 完全相同**（`20 0 0 1`）⇒ 差别不在跳包参数里，而在冷却与其它组件。

### 7.1 给别的背包加"Jumppack 配置"：能，做法是**插一行**

```
python tools/entity_hashmap_insert.py --block <JumppackComponentData 0x54270608> \
    --key 0x<目标背包> --copy-row-from 0x59C5CA839449B379   # 源 = Jump Pack
    # 想连冷却一起给：再插 Recharge 行（0x1F42878E，4 B）或直接改已有的那格 f32
```

- `entity_hashmap_insert.py` 会做**哈希图插入 + 行整行复制**，门禁含"全部旧键仍可查"（探测链不被破坏）；
- 也可只 `--row` 指向已有孤儿行，代价是那一行内容被共享；
- 反向操作（去掉跳跃）用 `--delete`。

**可检验的预测**：给 Supply Pack 插 `Jumppack` 行 + 设 `Recharge` 后，它应当**能被跳跃键使用**（图标/技能条可能不变，因为那由配装/图标资源决定）。
**风险**：该背包的 unit 没有推进器挂点/特效 ⇒ 跳跃动作可能没有视觉特效；`Behavior`/动画也可能不匹配。

### 7.2 首个实验：给 Supply Pack 插跳跃（2026-10-26 20:4x，`✗` 否证 → 见 §7.3）

| 项 | 值 |
|---|---|
| 目标件 | **Supply Pack `0x4EF9A47109239A58`**（已发布背包，配装里直接带即可） |
| 改动 1 | **插 `JumppackComponentData` 行**（块 `0x54270608`，280 B）——整行复制自 Jump Pack `0x59C5CA839449B379`；工具用**孤儿行 3**，门禁全过（含 G4b 行内容==源行、G5 全部旧键仍可查） |
| 改动 2 | **插 `RechargeComponentData` 行**（块 `0x1F42878E`，4 B）——同样复制自 Jump Pack ⇒ **15 s** |
| 验证 | 读回：Jumppack 行存在且与 Jump Pack 逐字节相同；Recharge = 15 ✓ |
| entities | `4495379a8eb193c4`（回滚件 `out/jumpsupply/entities.before-jumpsupply`）|

**判读**

| 观察 | 结论 |
|---|---|
| 按跳跃键**能起跳** | `Jumppack` 行就是唯一门槛 ⇒ **背包特性可以任意拼装**（护盾+跳跃、补给+跳跃…）|
| 能起跳但**没有推进器特效/动作怪** | 参数够了，缺视觉资源（unit 无推进器挂点/动画）⇒ 属资源层，数据层到此为止 |
| 跳跃键**毫无反应** | 还缺其它件：下一步候选是 `EquipmentComponentData` 的类型字段、或 `AbilityComponentData` 的 id（35 件背包这一格全是 0，但**背包的"使用键"绑定可能就吃它**）|
| 背包**不能装备/游戏异常** | 立刻回滚（`cp` 回滚件即可）|

**实机结果（2026-10-26 20:4x）**：跳跃键**完全没反应** ⇒ 走第三行分支，进入 §7.3。

### 7.3 第一轮否证 + 第二轮：`Equipment+0xDC` = "使用键行为类"（`✗` 结果 / `✓` 离线 / `⚠` 已装待测）

**否证结论**：`JumppackComponentData` 行 + `RechargeComponentData` 行**不足以**让一件背包会用跳跃键。
同时可以排掉 `AbilityComponentData`：35 件背包那一行是**逐字节相同**的 `0C 00 … 0C 00 00`（32 B，无任何 id），
它不可能是判别位。

**离线排查（`✓` 全表扫）**：把 Jump Pack / HOVER PACK / Dark Fluid Vessel / 便携地狱火 这四件
"**按使用键主动激活**"的背包当一组，在**全部 17 个背包组件 × 每 4 字节**里找"四件同值、外件没有"的字段，
**唯一命中**：

| 命中 | 值 | 独占性 |
|---|---|---|
| **`EquipmentComponentData +0xDC`** | **8** | 35 件背包里只有这 4 件是 8；其余 31 件没有 8 |

`+0xDC` 在整个 `EquipmentComponentData`（351 行）里的分布也支持"背包专用枚举"：
**非零行恰好 30 个且全是背包**（321 行为 0）。

**按 `+0xDC` 给 35 件分组（`✓`，与"特色组件"完全自洽）**

| `+0xDC` | 件数 | 代表件 | 该组组件特征 |
|---:|---:|---|---|
| 0 | 6 | 两个未发布 `BACKPACK`、C4 Pack、3 个补给件 | 无"主动使用"组件 |
| 1 | 1 | **Supply Pack** `0x4EF9A47109239A58` | `Deposit` |
| 2 | 5 | Maxigun、`0x0949…`、`0x26BD…` 等 | `Deposit`（部分带 `Tag`/`Animation`/`TwoPointChain`）|
| 3 / 4 / 5 | 3 | `0x5F9A…`、两件盾（弹道盾/定向盾）、Warp Pack | `Shield`/`ShieldController`/`MeleeShield`/`Displacement` |
| 6 | 7 | 补给类（含两件 Recoilless/Spear 类）| `Deposit` |
| 7 | 1 | Shield Generator Pack | `Shield`+`HitReact` |
| **8** | **4** | **Jump Pack / HOVER PACK / Dark Fluid Vessel / 便携地狱火** | `Jumppack`（地狱火为 `Behavior`+`InteractableMinigame`）|
| 9 | 1 | MEDIC BACKPACK | `Deposit` |
| 10 | 3 | 补给类 | `Deposit` |
| 13 / 14 | 2 | Chemical Backpack / Larva Container | `ObjectiveCarry`+`CarryEffect` |
| 15 | 1 | Cremator Backpack | `Deposit`+`TwoPointChain`+`Animation` |

⇒ 判读：`+0xDC` = **"背包的使用键行为类"**（8 = 需要玩家按键激活的主动能力；**具体效果**仍由
`Jumppack` / `Behavior` / `InteractableMinigame` 这些件提供）。这与"地狱火（不是跳包）也是 8"吻合 ——
它共享的是"按键激活"这一层，不是"跳跃"。

**第二轮实验（2026-10-26 20:5x 已装，两个互相独立的单变量，一局两个读数）**

| 实验 | 目标件 | 改动 | 预测 |
|---|---|---|---|
| **A 正向** | Supply Pack `0x4EF9A47109239A58` | `EquipmentComponentData+0xDC` **1 → 8**（`Jumppack`/`Recharge` 行保留）| 跳跃键生效 |
| **C 反向** | Jump Pack `0x59C5CA839449B379` | `EquipmentComponentData+0xDC` **8 → 1** | 跳跃键失灵 |

判读矩阵：

| A（Supply）| C（Jump Pack）| 结论 |
|---|---|---|
| 能跳 | 失灵 | **`+0xDC` 就是使用行为开关** `✓✓`；配方 = `Jumppack` 行 + `Recharge` 行 + `+0xDC=8` |
| 能跳 | 仍能跳 | `+0xDC` 充分非必要 ⇒ 还有第二条路径，继续查 |
| 不能跳 | 失灵 | `+0xDC` 必要但不充分 ⇒ 下一候选 **`EffectReferenceComponentData`**（3912 B，跳/盾/位移/搬运类才有；**该块 693 行全满，插行要先扩块**）|
| 不能跳 | 仍能跳 | `+0xDC` 与本机制无关 ⇒ 下一轮改用 `+0x80`（19↔23）与 `Attachable+0x00` |

**装盘记录**

| 项 | 值 |
|---|---|
| 注入件 | `out/jumpsupply/s3b.dl_bin`（md5 `45bcd28dab62f89c2e4d084625850b5c`，47,259,488 B）|
| 明文 | `out/jumpsupply/s3b.plain`（sha256 `6b327ce5…fea337`，round-trip 一致）|
| 门禁 | `entity_field_set.py` 两次全过（G1/G2/G3/G4/G7/G8/G6）；读回：Supply `+0xDC=8`、Jump `+0xDC=1`，Supply 的 `Jumppack`/`Recharge` 行仍在 |
| 回滚 | `cp out/jumpsupply/entities.before-jumpsupply <game>/data/game/generated_entities.dl_bin`（回到"未插跳跃"状态）|

