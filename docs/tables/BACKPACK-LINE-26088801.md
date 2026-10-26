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
| **A. 额外战备**（已装）| 战备表链 `Resupply(34) → Dark Fluid Vessel(30) → Solo Silo(92)`，行 30 的 `+0xA8` 本来就是 `0xD87885C7EAACE597` ⇒ 呼叫时应自带包声明 | `⚠` 待实机（判读：有图标/能叫/载荷是否生成）|
| **B. 投送舱换载荷**（已装）| rack **47**（MG-43 支援武器的舱，`spawn=1`）槽 0/1 = **`0x073270650F859DD0`**；`+0xA8` 保持 MG-43 的包（舱体本身要渲染），另加**整包驻留** `patch_17` = 包 `d87885c7eaace597`（toc 579,808 `5c75c825604ecbbb` / gpu 5,991,744 `8ec10d4faa58ad71` / stream 23,549,712 `0ad289dd8cd2c33a`）⇒ 叫 MG-43 的舱里就是暗液体容器 | `⚠` 待实机 |

## 6 相关

- 投送舱换载荷：[POD-RACK-26088801](POD-RACK-26088801.md)
- 战备额外条目：[UNRELEASED-STRATAGEMS-26088801](UNRELEASED-STRATAGEMS-26088801.md)
- 实体表字段图：[ENTITY-TABLE-25988413](ENTITY-TABLE-25988413.md)
