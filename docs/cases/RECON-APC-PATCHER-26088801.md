# 第三方 mod 侦察：APC-Patcher v0.4.1（Bastion Mk XVI → 可开 APC）

> 来源：`D:\Downloads\APC-Patcher-v0_4_1-fixed.zip`（98,312,597 B，sha256 `3871783520fe8e2e…`）
> 只读侦察，未安装、未运行其 exe。作者：gfsggq124（社区），本副本为第三方"fixed"版（只改了 exe + Checksums.json）。

## 1 形态：不是游戏内 mod，是**独立补丁器**

| 组成 | 内容 |
|---|---|
| `apc patcher.exe` | 57,344 B，.NET WinForms（随带 `BouncyCastle.Cryptography.dll`），负责备份/部署/还原 |
| `assets/entities-template.gz` | 解压 **47,259,396 B** → 改过的 `generated_entities.dl_bin` 明文，sha `be16f33d…` |
| `assets/physics-template.gz` | 解压 **343,756 B** → 一个 `physics` 资源（可选"自定义物理"） |
| `assets/APC Assets.zip` | 210.4 MB / 24 文件 = 7 个宿主包的 `patch_0` 三件套 |
| `recipe.json` / `Payload-Manifest.json` / `Checksums.json` | 偏移表、载荷清单与哈希 |

**基线可直接核对**：`recipe.json` 的 `original_plaintext_sha256 = dc6d52a1…` **就是本仓库明文缓存里的原版
`generated_entities.dl_bin`**，`original_sealed_sha256 = cac4a228…` 就是我们盘上的原版封包哈希。⇒ 它锁死 build 26088801。

## 2 实体表改了什么：**只动一台车，不加行**

全量比对（47,259,396 B 对 47,259,396 B，长度不变）：**172 段差异 / 590 字节**，全部落在
**一个实体 `0x16474112801385B6` = `Bastion Mk XVI`**（vanilla 里就有名字的休眠载具）及其炮塔子实体 `0xD336BA1CAD16769F`。

| 组件 | 改动 |
|---|---|
| `UnitComponentData +0x00` | `0x16474112801385B6`（自指占位）→ **`0x8C33C20637D2A687`**（APC 的 unit 资源） |
| `MountComponentData` | 原 2 槽 → 重写 3 槽；slot0 = 炮塔 `0xD336BA1CAD16769F` @ 节点 **`0xE9DC426A`（`attach_turret`）**、f2 `0x372F0418` —— **与 GATER 机炮塔挂载完全同签名**（抄的是现成可用挂载） |
| `SeatCollectionComponentData +0x00` | 43 → 31 |
| `WeaponMagazineComponentData +0x88`（炮塔） | 75 → 500 |
| `VehicleComponentData` | ~200 处：浮点调参（0.9→1.0、0.4→0.5…）、数个新 64 位哈希、`+0x80C` 节点哈希 `boss`→`collision` |
| `VehicleMotionComponentData` | 哨兵 `0xFFFFFFFF`→0、若干 1→0、浮点调参 |
| `Attachable` / `Interactable` | 挂接字段与交互提示/locid 改写 |

**内容哈希照旧保持**：`recipe.json` 的 `content_hash = 10252856984938216097` = **`0x8E49771B181FFAA1`**（与我们同一个锚点）。

## 3 物理与资源

* `physics-template.gz` 是**整份 physics 资源**；`recipe.json` 给出调参偏移：`mass 288` / `engine 343440` /
  `transmission 343496` / `brakes 343592,343608` / `springs 322196…322756` / `aero 343632`。
* 7 个宿主包各写一条 `patch_0`：`68ebdce3f7498179`（18.7 MB toc + 89 MB gpu + 110 MB stream，主资产）、
  `9ba626afa44a3aa3`（2,106,400 B）、`495cd5b6043a104d`、`c766ddd8a6875c02`、`4b7bd0cbf5b59fcf`、
  `6a3eecfddce28fe8`、`007e093ca718ca1a`。

## 4 对我们的价值与风险

**价值**：这是「**在表里把一台休眠载具改造成可开载具**」的完整样板 —— 不加行、只换 unit id + 重挂炮塔 +
整包资源补丁 + 可选 physics 资源。手法与我们同源（保哈希、整包驻留、`patch_N`）。

**风险**：它往 **`9ba626afa44a3aa3.patch_0`** 写东西，而本机该位已被占用（23,120 B，10-22）——
与现有 loader/旧 mod **同槽冲突**。若要在本机试，必须先备份 `data/9ba626afa44a3aa3.patch_0*` 三件。
启动器自称冲突会拒绝覆盖，但不要拿唯一副本赌它。

**新情报**：`Bastion Mk XVI`（`0x16474112801385B6`）在 vanilla 实体表里存在、名字完整、
`UnitComponentData` 指向自己（占位）⇒ 是一台**休眠/未启用载具**，可补进未发布清单。

## 5 骨架/座位/挂点到底怎么解决的：**换 unit（壳）**，不是改骨骼

用户的直觉是"坦克换 APC 要改很多骨骼" —— 实测相反：**实体表里一个骨骼节点都没改**。
HD2 里座位、挂点、炮塔位置这些几何全在**车辆的 `unit`（= Stingray 的壳，含节点树）**里，不在实体表。

| 层 | 改动 |
|---|---|
| 实体表 `UnitComponentData +0x00` | 自指占位 → **`0x8C33C20637D2A687`**（模组自带的新壳） |
| 实体表 `MountComponentData` 3 槽 | 节点哈希 `0xE9DC426A` / `0x6A46DA5E` / `0x83775726` |
| 实体表 `SeatCollectionComponentData +0x00` | 43 → 31（**唯一一处座位相关改动**，语义 `⚠ 未证`） |
| 资源 | 新壳 **78,400 B / 224 节点**：含 `attach_turret`、`attach_driver`、`attach_gunner`、`skeleton`、`boss`、`root`、`collision`、`game_mesh` |

**三个挂载节点哈希全部能在新壳的节点表里找到**（已验证）⇒ 挂点就是新壳自带的，实体只是"指向"它们。
同 id 还带 `bones`（1,956 B）与 **`physics`（343,756 B = `physics-template.gz` 那一份）**。
⇒ 坦克→APC 的座位/挂点差异**由新壳一次性承担**，所以实体侧只需要 590 字节。

**资源侧规模**（大 patch 363 条）：`unit ×20`、`animation ×64`、`particles ×41`、`texture ×132`、`material ×66`、`wwise_stream ×10`；
另两个小 patch 各带 1 个 `unit`（炮塔）。

**顺带发现两个机制**：

1. **`package` 资源 = 包依赖声明**。`9ba626afa44a3aa3.patch_0`（boot 包）里有 **10 条 `package`** + 4 条 `strings`
   —— 用它把另外 6 个宿主包的加载关系写进 boot 包。这比我们一直用的 `+0xA8` 声明口更通用，
   对"资源驻留/依赖"这条线值得单独验证。
2. **`physics` 资源可整份替换**（343,756 B）+ 偏移调参（mass/engine/transmission/brakes/springs/aero），
   车辆手感可以完全在资源侧做。

## 6 "2 个挂载槽变 3 个"的真相：**没有扩容，是填了空槽**

`MountComponentData` 每行是**固定的 120 B = 5 槽 × 24 B**（`item u64 | n1 u32 | n2 u32 | n3 u32 | tail u32`），
占用判据是 **`item != 0`**（空槽的 `tail` 本来就已经是 1）。逐槽对照：

| 实体 | slot0 | slot1 | slot2 | slot3 | slot4 |
|---|---|---|---|---|---|
| **Bastion 原版** | 占用 `0x1FA1F596769225C2` | 占用 `0x439F9E65C18567DA` | **空** | 空 | 空 |
| **Bastion→APC** | 占用 `0xD336BA1CAD16769F` | 占用 `0xB9606C5AAB32C3C2` | **占用 `0xD53EE03481AE73FD`** | 空 | 空 |
| **GATER A**（对照） | 占用（机炮塔） | 空←我们挂油罐用的就是它 | 空 | 空 | 空 |

⇒ 「2 → 3」= **重写 slot0/slot1 + 填 slot2**，行大小、块结构一个字节都没变。
**空槽是预分配的，不需要新增任何数据结构。**

**顺带确认 `n1` 的语义**：GATER 机炮塔槽是 `n1 = 0xE9DC426A` = `murmur32("attach_turret")`、
`n3 = 0x372F0418`；而 **APC 的 slot0 用的是同一对 `n1/n3`，只换了 `item`**
⇒ 作者直接抄了一个现成可用的炮塔挂载槽（锚点是**全局节点名哈希**，只要新壳里有同名节点就成立）。

**边界（`⚠ 未证`）**：真要把一个实体扩到第 6 个挂载，必须把 stride 从 120 改成 144，
那会改变该块行数组大小、并挪动其后所有块的偏移 —— 和我们在载荷数组上撞到的「长度不可变」是同一类约束。
