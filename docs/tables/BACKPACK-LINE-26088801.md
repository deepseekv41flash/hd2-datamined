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

### 7.3 第一轮否证 + 第二轮：`Equipment+0xDC` = "使用键行为类"（`✗` 已被 §7.4 推翻）

> **2026-10-26 20:5x 更正（`✓` 已读到字段名）**：本节的"`+0xDC` = 使用行为开关"**假设作废**。
> 从 typelib 的成员类型表读出 `EquipmentComponent+0xDC` 的类型是 **`BackpackWwiseIndex`**（Wwise = 音频中间件），
> 同区还有 `+0xD8 EquipmentWwiseIndex` ⇒ **那是音频索引，不是行为门**。第二轮 A/C 实验因此无效（见 §7.4）。
> 本节保留原始推理，只作为"怎么错的"记录：单看数值相关性会得出错误结论，必须叠类型名。


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


### 7.4 背包字段从哪来（本地/网上资料盘点，`✓`）+ 第三轮实验：`EquipmentType`

#### 7.4.1 资料盘点（谁给了什么）

| 来源 | 本地位置 / 链接 | 给到什么 | 用法 |
|---|---|---|---|
| **本仓库 typelib 解析器** | `tools/typelib.py`（LTLD v4：type/enum/member 描述 + 字符串表） | **成员类型表**：每个字段偏移上"是什么类型"（`EquipmentType` / `AbilityId` / `CApiVector3` …） | 本次关键证据来源；成员**名字**被剥离（`ns=0`，字符串表 0 字节），只有类型还在 |
| **HD2Runtime `schemas/entity_fields.json`** | `refs/hd2runtime-repo/schemas/entity_fields.json` | 语义字段名 + 记录内偏移 + 单位 + 是否可写（`jump.vertical_launch_velocity +0x00`、`hover.duration +0x09C`、`recharge.time +0x00`、`deposit.capacity/start/refill +0x00/+0x04/+0x08`） | 与本地字节逐条对照后**全部吻合** ⇒ 可直接当"人话字段名"用 |
| HD2Runtime 背包能力目录 | `refs/hd2runtime-repo/sdk/BackpackAuthoringCapabilities.json` + `docs/backpack-authoring.md` | 16 件背包 × 85 字段实例（可写 71 / 只读 14）、证据分级（gameplay_proven / schema_proven / native_correlated）、**"补给包与地狱火的充能语义未证实"** | 判"哪些字段有人实机验证过"；**没人做过"把跳跃能力搬到别的背包"** |
| 名字表（filediver `dl_type_names.txt` 派生） | `dl-type-names.json`（6,696 条） | **枚举名与枚举值名**：`EquipmentType_*` 30 条、`ExplosionType_*` 205 条、`AbilityId_*` 等 | 注意：**只有名字，没有枚举值序号**，不能直接 index→name |
| 社区枚举 dump | `refs/helldiversdata/enums_*.json` | 枚举值**列表**（顺序 ≠ 枚举序号，已用 `ExplosionType` 逐位比对证伪：251 vs 205 条、逐位只对 1 条） | 只能当"这个名字存在"的证据，不能当序号表 |
| Shodan stat editor 几何 dump | `C:\Users\Admin\HD2SDK-CommunityEdition\docs\shodan-acquisition-path.md:146` | 每个组件块的 `offset/indices/records/stride`（例如 `JumppackComponentData stride=280 indices=6 records=4`） | 与本地现算几何一致（本 build 背包 35 件 vs 它的 34 件 = 差一个新增件） |
| HD2 Modding Wiki（网上） | [Audio Modding](https://boxofbiscuits97.github.io/HD2-Modding-Wiki/dev/audio/overview.html#wwise) | 确认 HD2 用 **Wwise**（`Wwise 2023.1.7.8574`）+ 音频 mod 走 `.wem` | 佐证 `*WwiseIndex` = 音频索引 |
| 其它 | — | `deadworks.net/db/*` 是 **Deadlock** 的库，与 HD2 无关（死路，记录以免重踩） | — |

**结论**：本地资料足够画出"**字段 → 类型**"的完整图，但**没有**任何来源给出 `EquipmentComponent` 的成员名（引擎成员名被剥），
也没有人做过"背包能力移植"。所以"哪个字段是使用键行为门"只能靠**类型名 + 值→成员集对照 + 实机单变量**三步。

#### 7.4.2 `EquipmentComponent`（232 B）字段图（`✓` typelib 类型名）

| 偏移 | 类型 | 备注 |
|---|---|---|
| `+0x000` | u32 | 全表恒 0 |
| `+0x004` / `+0x010` / `+0x020` / `+0x02C` | `CApiVector3` | 坐标/朝向类 |
| `+0x080` | **`EquipmentType`** | **装备类枚举**（背包 12 个类，见 §7.4.3）|
| `+0x084` | u8 | 351 行里只有 2 行非零 |
| `+0x088` | **`EquipmentDropMode`** | 掉落模式枚举：全表 `{0:158, 1:182, 2:11}`（背包里的跳/补给都是 1）|
| `+0x0B8` | **`AbilityId`** | **35 件背包全是 `2066`**（197/351 行非零）⇒ 共享值，不是判别位 |
| `+0x0BC` | **`AbilityId`** | 背包全 0 |
| `+0x0C0` | `WeaponGripType` | 握法枚举（武器侧）|
| `+0x0D8` | **`EquipmentWwiseIndex`** | 音频索引 |
| `+0x0DC` | **`BackpackWwiseIndex`** | 音频索引 ← **§7.3 的误判点**（8 只表示"音效组 8"）|

#### 7.4.3 `EquipmentType` 值 → 类（`✓` 全表 351 行现算；名字为语义对齐的推断）

| 值 | 件数 | 成员（背包侧）| 枚举名（推断）|
|---:|---:|---|---|
| 10 | 2 | Chemical Backpack、`0x8726D02AEAF98E86` | （老旧名表无此值）|
| 17 | 10 | 10 件补给/弹药类背包 | `BackpackSupport` |
| 18 | 3 | Maxigun、`0xBB4B15B588F974FD`、Cremator | `BackpackSupport` 变体 |
| **19** | **2** | **Jump Pack `0x59C5CA839449B379` + HOVER PACK `0x5EC80F4F1CDB66CF`** | **`BackpackJumppack`** |
| 20 | 1 | MEDIC BACKPACK | `BackpackMedic` |
| 21 | 7 | 狗类/补给类 7 件 | `BackpackDrone` |
| 22 | 1 | Shield Generator Pack | `BackpackEnergyShield` |
| 23 | 1 | **Supply Pack `0x4EF9A47109239A58`** | **`BackpackSupply`** |
| 24 | 1 | Warp Pack | `BackpackDisplacement` |
| 25 | 4 | `0x967E…`（MeleeShield）、`0x5F9A…`、`BACKPACK-a`、`0xA4E7…` | `BackpackShield` |
| 26 | 1 | Dark Fluid Vessel | （老旧名表无此值）|
| 27 | 1 | 便携地狱火 | （老旧名表无此值）|
| 28 | 40 | Larva Container 等任务物件 | `Objective` |

**关键读数**：值 **19 收的正好是游戏里仅有的两件跳包**（Jump Pack / HOVER PACK），且 `EquipmentType` 是
`EquipmentComponent` 里唯一区分"跳包 vs 补给包"的**具名枚举**（其余差异是 hash/资源引用）。
⇒ 它是"使用键行为派发"的最佳候选（引擎很可能按这个类选装备行为类）。

#### 7.4.4 背包族组件字段图（`✓` 类型名 + 与 HD2Runtime 语义名对照）

| 组件 | stride | 关键字段 |
|---|---:|---|
| `JumppackComponentData` | 280 | `+0x000 f32` = **`jump.vertical_launch_velocity`**（Jump/HOVER = **40.0**，Dark Fluid = 35.0）；`+0x09C f32` = **`hover.duration`**（Jump Pack = **-1.0** = 无悬停；HOVER PACK = 6.0）；`+0x048…+0x060` 六个 **`AbilityId`**（Jump 行 = 2055/2056/2057/2058/2059/2060 连号）；`+0x044` = `SurfaceImpactType` |
| `RechargeComponentData` | 4 | `+0x000 f32` = **`recharge.time`**（Jump 15 / HOVER 11.5 / Dark Fluid 8）|
| `DepositComponentData` | 152 | `+0x000` `deposit.capacity`、`+0x004` `start_amount`、`+0x008` `refill_amount`、`+0x020/+0x024 AbilityId`、`+0x080 DepositRefill` |
| `BackpackComponentData` | 1 | 纯标记（35 件全 `01`）|
| `EquipmentComponentData` | 232 | 见 §7.4.2 |
| `AbilityComponentData` | 32 | 行 = **`SpawnAbility[4]`**（35 件背包逐字节相同 `0C 00 …`）|

#### 7.4.5 第三轮实验（2026-10-26 20:5x 已装，两件互不干扰的单变量）

| 实验 | 目标件 | 改动 | 预测 |
|---|---|---|---|
| **A 正向** | Supply Pack `0x4EF9A47109239A58` | `EquipmentComponent+0x80` **23 → 19**（`Jumppack`/`Recharge` 行保留）| 按跳跃键生效 |
| **C 反向** | Jump Pack `0x59C5CA839449B379` | `EquipmentComponent+0x80` **19 → 23** | 跳跃键失灵 |

判读矩阵：

| A（Supply）| C（Jump Pack）| 结论 |
|---|---|---|
| 能跳 | 失灵 | **`EquipmentType` = 使用行为派发门** `✓✓`；配方收口 = `Jumppack` 行 + `Recharge` 行 + `EquipmentType=19` |
| 能跳 | 仍能跳 | 充分非必要（`EquipmentType` 只是"类标签"，另有路径）|
| 不能跳 | 失灵 | 必要但不充分 ⇒ 下一候选只剩资源层（unit 状态机/动画是否含跳跃分支）或 `EffectReferenceComponentData`（3912 B，693 行全满、要扩块）|
| 不能跳 | 仍能跳 | `EquipmentType` 与本机制无关 ⇒ 背包能力**不能靠纯数据移植**，收口为否证 |

**风险**：`EquipmentType` 可能同时驱动军械库/配装 UI 的分类或图标 ⇒ Supply Pack 可能显示成跳包样式；不影响回滚。

**装盘记录**

| 项 | 值 |
|---|---|
| 注入件 | `out/jumpsupply/s4b.dl_bin`（md5 `84d593f54ef7257e5929a131925ad2d1`，47,259,488 B）|
| 明文 | `out/jumpsupply/s4b.plain`（sha256 `29630cf8…bf252a`，round-trip 一致）|
| 读回 | Jump Pack `EquipmentType=23`、Supply `EquipmentType=19`；两件都仍有 `Jumppack`(launch 40.0/hover −1.0) + `Recharge` 15.0 |
| 被丢弃的中间件 | `s3b.*`（`+0xDC` 音频实验，§7.3 已作废）|
| 回滚 | `cp out/jumpsupply/entities.before-jumpsupply <game>/data/game/generated_entities.dl_bin` |

### 7.5 第三轮结果：`EquipmentType` 不是"跳"的开关，但**按 5 会崩** ⇒ 行为分支确实被进去了（`✗`+`✓`）

| 实验 | 结果（2026-10-26 21:0x 实机） | 读数 |
|---|---|---|
| **A** Supply `EquipmentType 23→19`（跳包类）| 跳跃键**仍不能跳** | 单改类**不产生跳跃** |
| **C** Jump Pack `EquipmentType 19→23`（补给类）| **仍能正常跳** | `EquipmentType` **不是跳跃的必要条件** ⇒ 它不参与"跳跃键"这条路 |
| **新现象** | Supply Pack **按 5（原版使用键）→ 游戏崩溃** | **关键**：说明我们的改动**确实被行为层读到了**——"使用键"这条路把 Supply Pack 当跳包处理，然后踩空崩掉 |

**推理（`✓` 事实 + 推断）**

1. 第一轮（只有 `Jumppack`+`Recharge` 行、类是原版 23）**不崩**；
   第三轮（多改了类 19）**按 5 崩** ⇒ **`+0x80` 类值参与了"使用键"的派发**（否则不会换代码路径），只是不参与跳跃键。
2. 崩 = 跳包能力分支被进入，但 Supply Pack **缺这条分支要的东西**（空指针）。
   缺件候选（按可能性）：
   - **`EffectReferenceComponentData`**（3912 B，只有跳/悬浮/盾/位移/搬运类才有）——跳包分支可能直接索引"推进器特效"；
   - **`DepositComponentData`** 与跳包能力同时存在 ⇒ 使用键可能先被"取补给"吃掉、或在合成配置上踩空；
   - **unit 资产/状态机**（Supply 的 asset 没有推进器骨骼与跳跃动画状态）——资源层。
3. 因此第四轮的设计目标：**把跳包组件集补齐**，看"补件"能否救活。

### 7.6 第四轮：给 Supply Pack 补齐跳包组件集（2026-10-26 21:0x 已装，`⚠`）

| 项 | 值 |
|---|---|
| 目标件 | Supply Pack `0x4EF9A47109239A58` |
| 已有（第一轮）| `Jumppack`（行 3，复制自 Jump Pack）+ `Recharge` = 15 s（行 3）|
| **新增①** | **`EffectReferenceComponentData`**（块 `0x604434C9`，stride 3912）：**共享** Jump Pack 的行 **478**（只加键、不改行内容）|
| **新增②** | `EquipmentComponent+0x80` `EquipmentType` = **19**（跳包类）|
| 对照件 | Jump Pack **完全原版**（`EquipmentType=19`、行 1/1/478）|
| 注入件 | `out/jumpsupply/s5b.dl_bin`（md5 `c8ac576fb4669600619e5936cb5ecdf3`，47,259,488 B；明文 sha256 `382d29c5…2b7635` round-trip 一致）|

**工具要点（新增能力，值得记）**：`entity_hashmap_insert.py --row <行号>` **可以指向已被别的键占用的行**（只插键、不改行内容）
⇒ **块满（`EffectReference` 693 行 / 693 键，无孤儿行）时不必扩块**，直接共享别件的行即可。本轮 `--row 478` 门禁 G1–G6 全过
（槽 500 = 起点，0 步探测）。

**判读**

| Supply 现象 | 结论 |
|---|---|
| **能跳** | 背包跳跃 = **组件集齐就够**（`Jumppack`+`Recharge`+`EffectReference`+类 19）⇒ `✓✓` 配方收口，可推广到其它背包 |
| **仍崩（按 5）** | 缺的不是组件而是**资源**（unit 资产缺推进器/跳跃状态机）⇒ 与 MS-11 车载发射井同构，**纯数据到不了**，只能换壳 |
| **不崩但也不跳** | 组件够、`EquipmentType` 不是派发门 ⇒ 派发键在别处（下一候选只剩身份字段：`Unit+0x00` 资产 / `Attachable+0x00` / `Spottable+0x38`）|
| 补给功能坏了但别的正常 | 预期副作用（使用键被跳包分支占用）|

**若仍崩，第五轮的两个候选（按顺序）**：① 去掉 Supply 的 `DepositComponentData` 键（`entity_hashmap_insert.py --delete`）；
② **换壳**：`UnitComponentData+0x00` 改成 Jump Pack 的资产 `0x59C5CA839449B379`（会变成跳包外观，但能判定"能力是否在资产里"）。

**回滚**：`cp out/jumpsupply/entities.before-jumpsupply <game>/data/game/generated_entities.dl_bin`（回到未插跳跃的干净态）。
