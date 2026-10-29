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
| `UnitComponentData +0x00` | `0x16474112801385B6`（自指；vanilla 里确有该 unit）→ **`0x8C33C20637D2A687`**（APC 的 unit 资源） |
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
| 实体表 `UnitComponentData +0x00` | 自指 → **`0x8C33C20637D2A687`**（模组自带的新壳；原 id `0x16474112801385B6` **在 vanilla 里就是这台车的 unit**，70,848 B / 218 节点，见 §11.1 —— 早先写的"占位"已作废） |
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

## 7 三个挂载物分别是什么

| 槽 | `item` | 是什么 | 依据 |
|---|---|---|---|
| slot0 | `0xD336BA1CAD16769F` | **载具炮塔**（无名，无百科条目，16 组件） | 含 `TurretComponentData` + `ProjectileWeapon` + `WeaponData` / `Magazine` / `Reload` / `Wielder` + `Wieldable` + `WeaponCustomization`；模组把它的 `WeaponMagazine +0x88` 由 **75 → 500** |
| slot1 | `0xB9606C5AAB32C3C2` | **“Stalwart”**（21 组件） | `WeaponData/Magazine/Reload/Wieldable/ProjectileWeapon` + `Equipment/Interactable/MeleeAttack/MultiTarget/EntityBind/NetworkPhysics` |
| slot2 | `0xD53EE03481AE73FD` | **第二个“Stalwart”**（同模板相邻行号的另一实例） | 同 21 组件 |

⇒ 改装后的 APC = **1 门炮塔 + 2 挺 Stalwart**（两次侧位；锚点哈希 `0x6A46DA5E`/`0x83775726` 均存在于新壳，名字猜不出 `⚠`）。

**原版 Bastion 的两个挂载物都被换掉**：`0x1FA1F596769225C2`、`0x439F9E65C18567DA`（两者都无百科条目）。

**可复用的结论**：slot1/slot2 挂的是**玩家版支援武器实体**（带 `EquipmentComponentData` / `WieldableComponentData`），
不是专门的"车载武器变体" ⇒ `MountComponentData` 对 item 类型不挑，只要该 unit 能被解析就能挂。
以后给载具加武器位可以直接用现成武器实体，不必等"车载版"。

**三个槽的锚点**（n1 = 父车节点；n3 = 另一侧锚点，语义 `⚠ 未证`）：

| 槽 | n1 | n3 |
|---|---|---|
| slot0 | `attach_turret` (`0xE9DC426A`) | `0x372F0418`（与 GATER 机炮塔同一对，直接抄用） |
| slot1 | `0x6A46DA5E` | `0xD0B74FA2` |
| slot2 | `0x83775726` | `0x65942499` |

## 8 更正与座位问题（2026-10-29 用户指出）

### 8.1 更正：`0x16474112801385B6` **不是休眠载具，它就是 TD-220 Bastion**

前文 §1/§4 写的"休眠/未启用载具"**作废**。本仓库
[MOUNT-SEATS](../tables/MOUNT-SEATS-26088801.md) 早已记录 TD-220 的两个挂载物正是
`0x1FA1F596769225C2`（主炮）与 `0x439F9E65C18567DA`（同轴机枪）——就是 §6 里被替换掉的那两个槽。
⇒ 该实体是**现役 TD-220 Bastion 坦克**，只是平常不以战备形式出现。

### 8.2 模组**没有**新增"座位→武器"绑定

`SeatCollectionComponentData` 整行 424 B 里，改造后**只有 `+0x00` 变了（43 → 31）**，其余逐字节不变
（TD-220 该行本来就几乎全零：整行只有 4 个非零 u32：`+0x00`、`+0x108`、`+0x10C`、`+0x130`）。
⇒ 多出来的两挺武器**不是**通过在座位表里写绑定实现的。

### 8.3 "某个座位能操作什么"到底由什么决定

本仓库 2026-10-25 的分离实验已定案（[MOUNT-SEATS](../tables/MOUNT-SEATS-26088801.md) §4.7.1、§6）：

| 结论 | 证据等级 |
|---|---|
| **座位→武器/挂载的绑定不在 `MountComponentData` / `SeatCollectionComponentData` 里** | `✓ 离线` + 旧运行时一致 |
| 座位能干什么（有没有准星、收不收 R 装填、能否开火）= **座位侧能力**（相机 preset + wielder 通道） | `✓✓` 实机（同一炮塔站只换座位，准星/装填结果相反） |
| 武器行只提供素材（`crosshair_type`、弹药三字段、`WeaponReload` 时长） | `✓ 离线` |

`SeatCollectionComponent` 的字段结构是 `TransitionId` + `Passenger[16]` + flag + `ActiveAimConstraint[22]`，
但 TD-220 这两段基本为空 ⇒ 它的座位来自**壳里的座位节点 + 引擎默认行为**。

⇒ 所以这个模组让乘客位有武器，靠的是三件事的组合，而不是写绑定：

1. **`MountComponentData` 多填槽**（1 门炮塔 + 2 挺 Stalwart，见 §7）；
2. **换壳**（新 unit 自带座位节点与挂点，见 §5）；
3. **`InteractableComponentData` / `VehicleComponentData` 大改**（交互点与相机/操控参数；
   Interactable 里有一批 `1 → 0` 的逐字节开关，`⚠ 未证` 具体哪几位是座位授权）。

要坐实第 3 条，最干净的是**单变量移植**：只把 APC 版的 `InteractableComponentData` 搬到 TD-220 上，
看乘客位有没有出现武器/能否开火。

## 9 单变量移植实验：只搬 `InteractableComponentData`（2026-10-29 已装盘）

**目的**：验证「座位能操作什么」是不是由 `InteractableComponentData` 决定。

**改动（严格单变量）**

| 表 | 改动 | sha |
|---|---|---|
| `generated_entities.dl_bin` | TD-220 `0x16474112801385B6` 的 `InteractableComponentData` 行（1104 B）**整行替换为 APC 版**，其余 0 改动 | `daa74341` |
| `generated_stratagem_settings.dl_bin` | 仅作为**投送脚手架**：id 138 `slot0` = TD-220、`+0xA8` = 其包 `68ebdce3f7498179`、链 34→106→111→138 不变、category 3 | `5f96a6da` |

新工具：`tools/entity_copy_row.py`（整行拷贝 + G1/G2/G3/G4/G6 门禁），本次 G 全 PASS，盘上回读该行与模板逐字节相同。

**观察项与判读**

| 现象 | 判读 |
|---|---|
| 乘客位出现武器/准星、能开火 | `Interactable` 就是座位授权所在，继续缩小到具体字节（`+0x0C` 半径、`+0x80` 标志位等） |
| 行为与坦克原版一致（只有炮手能打） | `Interactable` 不是座位授权 ⇒ 回到 MOUNT-SEATS §4.7.1「座位侧能力（相机 + wielder）」的定案 |
| 上不了车 / 交互点异常 | 交互条目按**壳节点名**寻址，跨壳搬不动 —— 这本身也是结论（`Interactable` 与壳强绑定） |

回滚：`dlbin_deploy.py restore --file generated_entities.dl_bin` 与 `--file generated_stratagem_settings.dl_bin`。

### 9.1 实机结果（2026-10-29）：**交互提示异常** ⇒ 命中的是判读表第 3 行

**现象**：装 `daa74341` 后上车交互提示异常。
**判读**：`InteractableComponentData` 的条目与**壳（节点）强绑定**，把 APC 的整行搬到 TD-220 上，
提示/交互点无法在旧壳里解析 ⇒ **跨壳不可移植**。

**这一发能下的结论**：
* 交互点/上车提示**随壳走**，不是可以脱离壳单独搬运的"授权表"；
* 因此它**不能**回答"别的座位为什么有武器"——测试条件本身不成立（连干净的基线都没有）。

**不能下的结论**：`Interactable` 是否也参与座位武器授权 —— 仍未证。

**已回滚**：`generated_entities.dl_bin` 与 `generated_stratagem_settings.dl_bin` 均 restore 到原版。

**若要真正回答授权问题**，唯一干净的做法是**反向单变量**：把 APC 完整装上（210 MB 资源 + 备份 `9ba626afa44a3aa3.patch_0`），
再把它的 `Interactable` 换回 TD-220 版，看乘客位是否失去武器；成本明显更高。

### 10 完整部署（2026-10-29，手工安装其载荷，未运行其 exe）

| 项 | 值 |
|---|---|
| 备份 | `D:\mod\backups\apc-mod-20261029\9ba626afa44a3aa3.patch_0*`（原 23,120 B 的 loader/旧 mod 槽） |
| 载荷 | 7 组 `patch_0` 三件套（24 文件）已拷入 `data/`；`9ba626…patch_0`=`416e2519`、`68ebdce3…patch_0`=`cfa6c53e` 与 manifest 一致 |
| 实体表 | `b2efae2a`（= `entities-template.bin` 重新封包，APC 版） |
| 战备表 | `5f96a6da`（t17：id138 `slot0`=TD-220、`+0xA8`=`68ebdce3f7498179`，用于召唤） |
| 未做 | 未跑 `apc patcher.exe`；未启用"自定义物理" |

**注意**：模组覆盖了 `9ba626afa44a3aa3.patch_0`（本机原有 23,120 B）。若发现其它旧 mod 失效，
从上面的备份目录把三件拷回即可。

## 11 二轮：`TransitionId` 到底管不管"座位切换"（2026-10-29）

### 11.1 先修正一处：vanilla 里**有**这台车的壳（`✓ 离线`）

§5/§8.1 把 `UnitComponentData +0x00` 的自指写成"占位"，**错**。扫全库（3,522 包，`load_blobs=False`）：

| 资源（id = `0x16474112801385B6`） | 所在 vanilla 包 | 大小 | sha256 前 16 |
|---|---|---|---|
| `unit` | `68ebdce3f7498179` / `17ec2d364664c3e9` | **70,848 B / 218 节点** | `bdd028f7bc54cf94` |
| `bones` | 同上 | 2,737 B | `10a7725ef3bc6be8` |
| `physics` | 同上 | 205,448 B | `6cfd17d78c13adcb` |
| `state_machine` | 同上 | 19,924 B | `58fc657e2a2c5436` |

⇒ 自指是**合法自引用**（unit / bones / state_machine 与实体同 id），不是占位。
模组把整包换成它自己的：

| 资源 | 模组版本 | 与 vanilla 的差别 |
|---|---|---|
| `unit 0x8C33C20637D2A687` | 78,400 B / **224 节点** | 多 6 个节点；多 2 个段（`customization`、`unk_header1`）；除 10 个语义节点外节点哈希**全不同** |
| `state_machine 0x4D7C8CA9C52C7589` | 18,204 B | **vanilla 全库没有这个 id**（模组新建） |
| `state_machine 0x16474112801385B6` | 19,924 B | 与 vanilla **逐字节相同**（只是重发，未改） |

unit 头对照：vanilla `bones_ref = state_machine_ref = 0x16474112801385B6`；
APC `bones_ref = 0x8C33C20637D2A687`、`state_machine_ref = 0x4D7C8CA9C52C7589`。

新壳里已破译的语义节点（`unit_nodes` + 暴力名表）：`interact_gunner`(97)、`driver_hatch`(102)、
`attach_driver`(103)、`attach_gunner`(104)、`attach_turret`(105)、`door`(137)、`interact_passenger`(140)。

### 11.2 `TransitionId` 是**枚举 id**，不是座位清单（`✓ 离线`）

* `refs/dl-type-names.txt` 里 `TransitionId` 只有 **36** 个名（旧版名表）；
  typelib 实测 `djb2("TransitionId") = 0x2BB65418` = 第 **247** 号枚举，**46 个值（0…45）**。
* 成员名含 `TransitionId_frv / lav / troop_transport / cargo_car / civilian_car / rover /
  manned_turret / combat_walker / shuttle / ship_hellpod / generic_interact_switch / …`
  ⇒ 语义 = **载具/工事家族的上车·下车·换位动画过渡集**。
* 本 build 56 个座位行实际用到：`1 3 4 5 7 8 10 11 13 14 20 24 25 26 27 28 29 30 32 33 34 35 36 37 39 40 41 42 43 44`；
  **31 没有任何 vanilla 实体在用**（模组挑的是空号）。

⇒ 「把四个座位全部塞进过渡集」**没法靠改这个字段做到**：它指向**一套**过渡，不是一个可增删的列表。
数据层能做的只有两件事：**换一套**（换 id），或去动壳/状态机那一层。

### 11.3 单变量实验 E1：`31 → 43`（已装盘，⚠ 待实机）

| 项 | 值 |
|---|---|
| 唯一改动 | `SeatCollectionComponentData +0x000`：`31 → 43`（回到 vanilla TD-220 的值） |
| 明文 | `out/apc-recon/t-seat43.plain`（47,259,408 B；G1–G8 全过；哈希锚点仍 `0x8E49771B181FFAA1`） |
| 封包 | `out/apc-recon/t-seat43.dl_bin` = `f9927e95` |
| 装盘 | `data/game/generated_entities.dl_bin` = `f9927e95`；**回读** row10 `TransitionId = 43` ✓ |
| 基线快照 | `out/apc-recon/apc-entities-baseline.dl_bin` = `b2efae2a`（用户已确认可用的 APC 版） |
| 回滚 | `python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed out/apc-recon/apc-entities-baseline.dl_bin` |

判读表：

| 实机现象 | 结论 |
|---|---|
| 恢复"乘客↔炮手"三座依次切换 | `TransitionId` = 座位切换集合开关（✓）；下一步找含 4 座的集合，或试其它 id |
| 仍只有乘客↔乘客 | 切换集合不在实体表（在壳 / 状态机 / 代码侧）⇒ 该字段只负责上下车动画 |
| 上下车动画变怪或卡住 | 43 那套过渡与 APC 壳不匹配 ⇒ 过渡集与壳绑定 |

### 11.4 实机结果（2026-10-29）：`31 → 43` ⇒ **无法上车**（`✓✓ 实机`）

命中判读表里最重的一行：不是"动画变怪"，而是**整个上不了车**。
⇒ `TransitionId` 不是可以随便换的表现参数，而是"**这套壳上哪些上/下车·换位过渡存在**"的身份标识：
换成别的车的过渡集，这台车连"进入"过渡都找不到，交互直接不成立。
（已回滚到基线 `b2efae2a`，可正常上车。）

### 11.5 新证据：这台壳是 **LAV**（`✓ 离线`）

APC unit（78,400 B）`customization` 段里带一段**明文内容路径**：

```
@0x7E30 (80 B)  40 00 00 00 08 00 00 00 00 00 00 00 86 2a fe 21 ff ff ff ff 03 00 00 00 28 00 00 00
                "content/fac_helldivers/vehicles/lav/lav\0"
```

而 `TransitionId` 枚举里正好有 **`TransitionId_lav`**（§11.2）⇒ 模组写的 **31 极可能就是 `TransitionId_lav`**。
**修正 §11.2 末句**：31 不是"随手挑的空号"，而是 **LAV 自己那一套**；本 build 没有 vanilla 实体用 LAV，
所以它看起来像空号。这同时解释了 43 为什么直接上不了车。

另外 `unk_header1` 段（48 B；vanilla 那台坦克壳**没有**这一段）里出现两次 **46**：

```
02 | d2 17 17 07 7d fc 8b ea | 1c | 01 | 20 | 01 | 2e | 2e   (u32，末 3 个为 0)
```

`0x2e = 46` 与 `TransitionId` 枚举值个数（46）相同 —— **待查**（`⚠ 未证`）：
可能是本壳动画控制器的条目数，也可能是过渡集长度。

### 11.6 路线结论（本轮）

| 路线 | 结论 |
|---|---|
| 换 `TransitionId` 让四座都能切 | **✗ 否证**：换集就上不了车（11.4） |
| 在座位表里加座位 / 改切换顺序 | **✗ 无落点**：整行 424 B 只有 4 个非零 u32，没有座位清单（§8.2） |
| 改壳（unit）里的座位 / 过渡数据 | **⚠ 唯一未否证**：候选段 `unk_header1`(48 B)、`bone_info`(34,768 B)、`customization`(80 B)；壳是资源，可用 `resource_patch.py build` 重发（模组已示范这条路） |
| 代码侧（memmod） | 与本轮目标不匹配，代价最大 |

## 12 全库车辆壳普查：**只有 2 个壳没被任何实体用**（2026-10-29，✓ 离线）

扫法（可复跑）：3,522 个包的元数据 → 8,019 个不同 `unit`（48,020 条目）→ 只解 `toc≥15 KB`
+ 名字哈希命中车辆语义节点族（`attach_driver` / `interact_driver` / `interact_enter` /
`interact_passenger` / `right|left|front_hatch` / `attach_gunner` / `attach_turret` / `cargo_attach` /
`driver_hatch`）→ 23 个候选 → 再与实体表 `UnitComponentData +0x00` 的 735 个引用做交集。

**结论：全 build 共 15 个车辆壳，13 个有实体在用，2 个没有。**

| 壳（unit id） | 大小 | 节点 | 语义节点 | 用途 / 引用 |
|---|---|---|---|---|
| `0x79E4B3D2DA5E45E3` | 61,680 B | 198 | attach_driver, interact_enter | `combat_walker`（4 台机甲共用） |
| `0xCC21C7FFD3EBEFB9` | 73,584 B | 193 | attach_driver, interact_driver | `vehicles/frv/frv`（2 个实体） |
| `0x2D85BFE3D8717FE5` | 58,752 B | 194 | 同上 | `vehicles/frv_heavy/frv_flamer` |
| `0x9B2140378640432E` | 62,624 B | 201 | 同上 | `vehicles/frv_supply/frv_supply` |
| `0x423FF97D57AB04F5` | 92,816 B | 258 | attach_driver/​gunner/​turret, driver_hatch | `vehicles/oilrig/oil_rig`（= GATER 系，2 实体） |
| `0xEF3A4136B21592CB` | 66,960 B | 223 | interact_passenger, cargo_attach | `vehicles/shuttle_gunship/…`（5 实体） |
| `0x18F11A4E18192CFE` | 39,040 B | — | interact_passenger, cargo_attach | 2 实体（无 content 路径） |
| `0x75BE82ED8592A6B3` | 41,664 B | 131 | interact_passenger, cargo_attach | **GATER 功能壳**（零网格，1 实体） |
| `0x3F70E3503A3293F9` | 48,272 B | — | interact_passenger, cargo_attach | 1 实体（无路径） |
| `0x00BCF8247A544CDC` | 41,520 B | 97 | attach_driver, attach_turret | 4 实体（无路径） |
| `0xF8131632AA867107` | 34,768 B | 87 | attach_driver, interact_driver | 2 实体，TID 20、2 挂载 |
| `0x16474112801385B6` | 70,848 B | 218 | right/left/front_hatch, interact, attach | **TD-220 Bastion 原壳**（TID 43） |
| `0xB0C9FAF4AF8903F9` | 78,784 B | — | right/left/front_hatch | **TD-110 Storm 原壳**（TID 44） |
| **`0xE37434E0B34DB81F`** | 46,400 B | 165 | attach_driver, interact_driver | ★ **`vehicles/frv/frv_superearth` —— 没有任何实体引用** |
| **`0x16BC189B4D7CB3FE`** | 21,664 B | 76 | attach_driver, door_left/right | ★ **`vehicles/colony_rover/colony_rover` —— 没有任何实体引用** |

另有模组自带的 **LAV 壳 `0x8C33C20637D2A687`**（78,400 B / 224 节点）：**vanilla 全库没有这个 id**，
它是本 build 里唯一同时具备 `interact_gunner` + `interact_passenger` + `attach_driver/​gunner/​turret` 的壳
—— 这正是模组能做出"4 人 3 挂载"的地基。

`⚠ 未证`：两个"未用壳"只是**没有实体表引用**；由 Lua/任务脚本按 id 直接生成的通路未排除。

## 13 反向应用：把 GATER 的壳移植到普通载具（2026-10-29，已装盘 ⚠ 待实机）

> 目标：GATER 走任务/战备投送时**落地前自毁**，数据层已九条否证（见
> [UNRELEASED-INVENTORY](../tables/UNRELEASED-INVENTORY-26088801.md) §7.2）。
> 换个思路：**借 APC 案例的换壳手法**，把 GATER 的壳指给一台普通可召唤载具，
> 让"外观是 GATER、行为是普通车"，从而绕开任务侧的自毁。

### 13.1 与 APC 案例的差别：本例**一个资源都不用补**（`✓ 离线`）

| | APC 案例 | 本例 |
|---|---|---|
| 目标壳 | `0x8C33C20637D2A687`（模组新 id，vanilla 没有） | `0x423FF97D57AB04F5`（vanilla 自带：mesh 92,816 / bones 3,280 / physics 188,280 / state_machine 13,780，6 个包里都有副本） |
| 资源补丁 | 必须（10 个 package + 363 条目） | **不需要** |
| 改动面 | 实体表 + 资源 | **实体表 + 战备表** |

实体 `0x0801B6B3C5D12EBC`（GATER A）自己**没有任何 unit/bones/physics 资源** ⇒ HD2 按**壳 id** 寻址资源，
把宿主的 `UnitComponentData +0x00` 指过去就等于整壳换掉。

### 13.2 宿主选择（`✓ 离线`，全库 15 个车辆壳里挑）

| 宿主 | 缺 GATER 的组件 | 多余组件 | 悬空引用 | 召唤行 | 结论 |
|---|---|---|---|---|---|
| **Maelstrom `0xB0C9FAF4AF8903F9`** | 仅 `ObjectiveDynamicLink`（**要绕开的正是它**） | 5 | 28（已改写） | 149(id 52) 未验 | ★ **选中**：唯一"除自毁链外与 GATER 组件完全对齐"，且自带 Deposit/Buoyancy/VehicleCollisionDamage |
| frv_supply `0x9B2140378640432E` | 同上 | 6（含 Animation/Woundable/Weathering） | 8 | 141(id 26) 未验 | 备选 |
| frv_flamer `0x2D85BFE3D8717FE5` | 缺 **Deposit** + Objective | 7 | 9 | **142(id 138) 已验可用** | 备选（会丢油罐装卸） |
| frv(Gunner) / Bastion / 机甲 | — | — | — | — | 排除（测试车 / 现役 APC / 缺 5 个组件） |

### 13.3 移植清单（`✓ 离线`，一条命令可复跑）

`tools/entity_transplant.py --spec out/apc-recon/gater-host.spec.json`
（新工具：跨实体 14 行整行搬运 + 悬空节点改写 + 保内容哈希；G1/G2/G3/G4/G6/G8 全过）

| 行 | 块 | GATER A 行 → Maelstrom 行 |
|---|---|---|
| Unit | `0x4437574D` | 1535 → 1197 |
| SeatCollection | `0x4AEAFC86` | 53 → 50 |
| Mount | `0x3845B1E0` | 159 → 125 |
| Interactable | `0xFCCA29DB` | 437 → 290 |
| Attachable | `0xBCF41716` | 674 → 585 |
| Vehicle | `0xEAEB2B0D` | 19 → 18 |
| VehicleMotion | `0x83B65443` | 13 → 12 |
| VehicleElectrics | `0x2C7ACD8B` | 12 → 11 |
| Health | `0xB3915DE3` | 489 → 432 |
| EffectReference | `0x604434C9` | 638 → 534 |
| Faction | `0x5653EA91` | 502 → 419 |
| Gore | `0x8D419C7A` | 202 → 172 |
| Drownable | `0x726A4F6B` | 57 → 56 |
| VisibilityMask | `0x8EC31141` | 266 → 226 |

宿主独有、GATER 没有的三个组件里，指向**旧壳节点**的引用被改写成新壳里存在的根节点 `0x4A182741`：
`0x8FAA4635` 20 处、`FoleySound`（`0xB6F66BB5`）8 处（`OverlapDamage` 实测 0 处 —— 它的 8 个值在两套壳里都有）。

### 13.4 已装盘（`⚠ 待实机`）

| 项 | 值 |
|---|---|
| 实体表 | `generated_entities.dl_bin` = **`192a42263a6de393`**（← `out/apc-recon/gater-host.dl_bin`） |
| 战备表 | `generated_stratagem_settings.dl_bin` = **`e515fea8d9f7aac2`**（← `out/apc-recon/gater-host-strat.dl_bin`） |
| 召唤 | 行 138 `payload[0]` = Maelstrom `0xB0C9FAF4AF8903F9`；`+0xA8` = **`0x0DFF5200594E867F`**（GATER 包，90 条目，含壳+油罐+音效） |
| 磁盘回读 | Maelstrom：Unit=`0x423FF97D57AB04F5`、TID=33、Health=12000、Mount[0]=炮塔`0x9872EEB31A5F88FD`@`0xE9DC426A`；APC 行仍在（`0x8C33C20637D2A687`/31）⇒ 可随时换回 |

### 13.5 判读表（待实机）

| 现象 | 判读 |
|---|---|
| 落地**不自毁**、外观 GATER、能上车开动 | 自毁来自**实体/任务侧**（`ObjectiveDynamicLink` 链）⇒ 换壳路线成立 |
| 仍然自毁 | 自毁是按**壳/关卡**触发的 ⇒ 本路线否证（干净结论） |
| 落地是紫问号/不出现 | 壳包没被 `+0xA8` 带起来 ⇒ 换包（`efb0636c8594f558`）或整包驻留 |
| 有车没炮塔 | 炮塔在 `f6fb08cc02d24255`，需另做驻留（旧实验补丁还在盘上） |
| 能上不能开 / 相机乱飞 | 宿主侧残留（`0x8FAA4635` 等）⇒ 下一发清悬空或换 frv_flamer 宿主 |

### 13.6 回滚

```bash
# 回到 APC（TD-220 + LAV 壳）
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed out/apc-recon/apc-entities-baseline.dl_bin
python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin --sealed out/c-route/t17.dl_bin
```

### 13.7 在 26251122 上复验换壳线：一条**更正** + 现行实验状态（2026-10-29 19:4x）

**复验**：`generated_entities.dl_bin` 在新 build 逐字节未变、typelib 也相同 ⇒ §13.3 的 14 行移植 spec、
宿主选择、`TransitionId 33`、`boss` 挂点分析**全部沿用**；只需把基线换成 `refs/dlbin/plaintext-26251122/` 重跑
`entity_transplant.py`（G1/G2/G3/G6/G8 全过，哈希锚点仍 `0x8E49771B181FFAA1`）。

**更正（重要）**：召唤行的 **`+0xA8` 必须声明"壳所在的包"**，否则引擎按实体去找壳资源时包没被加载 ⇒ 空指针。
我们曾只改 **行 138** 的 `+0xA8`，而用户实际叫的是 **id 52（Maelstrom 本体，靠自己存档里的战备位）** ⇒
行 52 的 `+0xA8` 一直是 Maelstrom 自己的 `65EE777B72347CB4` ⇒ 两次实验都在 **`game.dll+0x7045B1`**
崩成同一个 `0xC0000005`（dump 时间 19:29:17 / 19:35:29，偏移完全一致）。
⇒ 那两发**没有检验到任何嫌疑**，此前"状态机/挂载物排除"的临时结论**作废**。

修复后的召唤配置（`strat-final` = `340cee246055ccb5`）：
* 额外战备链恢复：`34 Resupply +0xC8 → 106 → 111 → 138`（供 138 路径使用）
* **行 52 `+0xA8` = `0x0DFF5200594E867F`（GATER 包）**（用户实际路径）
* 行 138 `payload[0]` = 宿主 Maelstrom、`+0xA8` = GATER 包（备用路径）
* 实测：叫 Maelstrom → **车出现、投放动作时爆炸** ⇒ 与旧 build 行为一致，**实验基线恢复**

**现行实验状态**

| 项 | 值 |
|---|---|
| 实体基线（满尺寸、原 SM、炮塔在位） | `6e58c3767668ff09`（`out/gater2625/gater-host.dl_bin`） |
| 嫌疑①「挂载物」版（槽 0 清零） | `e4b86b06e3d4b865`（`gater-host-nomount.dl_bin`）**← 已装，待判读** |
| 嫌疑②「壳状态机」版 | `out/gater2625/sm/patch/0dff5200594e867f.patch_0*`（`+0x20` → 坦克 SM `0x16474112801385B6`）**未装** |
| 战备表 | `340cee246055ccb5`（链 + 52/138 双路径，勿动，保持单变量） |

判读：叫 Maelstrom（id 52）后 —— 仍"投放动作时爆炸" ⇒ 挂载物排除；不再爆炸/能落地 ⇒ 挂载物是触发器。

### 13.8 换壳路线收口：**LAV 壳 → TD-110 Maelstrom** 实机成功（2026-10-29，`✓✓ 实机`）

两个未证嫌疑先被清掉（都不成立）：

| 实验 | 结果 |
|---|---|
| ① 挂载物（`MountComponentData` 槽 0 清零） | 仍投放瞬间爆炸 ⇒ ✗ 排除 |
| ② 壳状态机（unit `+0x20` → 坦克 SM `0x16474112801385B6`，带正确包声明） | 仍投放瞬间爆炸 ⇒ ✗ 排除 |

⇒ GATER 壳的自毁既不在挂载、也不在壳 SM；**GATER 壳这条线封存**（数据层已无落点）。

改按"用已证实可用的壳"做对照：**把 LAV 壳套到 Maelstrom 上**。

| 项 | 值 |
|---|---|
| 供体 | 模组模板里的 **Bastion/APC 实体** `0x16474112801385B6`（entities 两版逐字节相同，可直接当供体） |
| 宿主 | TD-110 Maelstrom `0xB0C9FAF4AF8903F9` |
| 壳 | **LAV `0x8C33C20637D2A687`**（资源由模组 7 组 `patch_0` 提供，旧 build 的补丁在 26251122 上照常生效） |
| 移植 | 同 §13.3 的 14 行；悬空改写这次 `0x8FAA4635` 有 **40 处**（`0xC4B6B405` 0 处、`0xB6F66BB5` 8 处）→ `0x4A182741` |
| 实体表 | `b7cd66e45d5b5b28` |
| 战备表 | `7bed7c4ae91ce268`：行 **52 与 138** → 宿主，`+0xA8` = **`0x68EBDCE3F7498179`（LAV 包）**，额外战备链 `34→106→111→138` 保留 |
| 回读 | `Unit=0x8C33C20637D2A687`、`SeatTID=31`、`Mount=[炮塔 0xD336BA1CAD16769F@attach_turret, Stalwart ×2]`、`Health=8000` |

**实机（用户回报）**：出来是 **APC 外观**，**能上车、能开**，**炮塔与两挺 Stalwart 都能用** ✓✓

**与模组原版的唯一差异（已证原因）**：炮塔弹容量不同。原因 = 模组把弹容写在**炮塔实体**上
（`0xD336BA1CAD16769F` 的 `WeaponMagazineComponentData +0x88`：**75（vanilla）→ 500（模组）**），
而我们只移植了**宿主实体**的 14 行，炮塔实体保持原版 ⇒ 读到 75。读回对照：装盘 75 / 模组模板 500 ✓
⇒ 这是**预期行为**，补一行即可恢复 500。

**这次同时证明的两件事**：
1. **换壳机制在新 build（26251122）上完好**，且**旧 build 的第三方资源补丁仍可用**（7 组 `patch_0` 直接生效）；
2. "换壳"是**模块化**的：宿主行可成套移植，子实体（炮塔/武器）的改动可以按需单独补。

### 13.9 「LAV 壳」标准配方（结项，2026-10-29；读数时刻 20:12）

**当前盘面（保留可用状态，不回滚）**

| 项 | 值 |
|---|---|
| `data/` 补丁 | 模组 **7 组 `patch_0` 三件套（21 文件）**，无其它 `.patch_*` |
| `generated_entities.dl_bin` | **`b7cd66e45d5b5b28`** |
| `generated_stratagem_settings.dl_bin` | **`7bed7c4ae91ce268`**（行 52 / 138 → 宿主，`+0xA8`=LAV 包；链 `34→106→111→138`） |
| 实机 | APC 外观、能上车、能开、炮塔 + 两挺 Stalwart 可用；**炮塔弹容 75（vanilla；模组是 500，未补）** |

**复跑步骤**

1. **资源**：把 `D:\mod\backups\pre-update-26251122-20261029\patches\` 里这 7 个包 id 的 `patch_0` 三件套拷回 `data/`：
   `007e093ca718ca1a`、`495cd5b6043a104d`、`4b7bd0cbf5b59fcf`、`68ebdce3f7498179`、`6a3eecfddce28fe8`、`9ba626afa44a3aa3`、`c766ddd8a6875c02`
2. **实体移植**：`tools/entity_transplant.py --spec out/gater2625/lav-host.spec.json --out out/gater2625/lav-host.plain`
   （供体 = 模组模板 `0x16474112801385B6`，宿主 = `0xB0C9FAF4AF8903F9`，壳 = LAV `0x8C33C20637D2A687`，14 行 + 悬空改写 → `0x4A182741`）
3. **战备**：`stratagem_extra.py --chain 34:106,111,138` → 再 `stratagem_repair.py --payload 52:0=0xB0C9FAF4AF8903F9 --set 52:0xA8=0x68EBDCE3F7498179`（138 行同改）
4. **封/装**：`dlbin_seal.py seal-key` → `dlbin_deploy.py install`（换 build 后首次要 `--accept-current`，它会把新 build 原版另存 `.replaced`）
5. **回读**：`Unit=0x8C33C20637D2A687` / `SeatTID=31` / `Mount=[炮塔 0xD336BA1CAD16769F@0xE9DC426A, Stalwart×2]` / 行 52·138 的 `+0xA8=0x68EBDCE3F7498179`

**四条硬约束（本轮踩出来的）**

1. **召唤行的 `+0xA8` 必须声明"壳所在的包"**——漏了不会报错，会在生成时 AV（`game.dll+0x7045B1`，2026-10-29 两次 dump 实证）；
2. **`SeatCollectionComponentData +0x00`（`TransitionId`）必须与壳一致**：LAV=31、坦克=43/44、GATER=33；不一致会无法上车（§11.4 实证）；
3. **子实体的改动不在宿主移植范围**：模组把弹容写在炮塔实体上（`0xD336BA1CAD16769F.WM +0x88` 75→500），要单独补；
4. **旧 build 的第三方 `patch_0` 在新 build 仍生效**（本轮 26251122 实测）——但**旧封包 `.dl_bin` 不可复用**，必须按新明文重做。

**回滚**

```bash
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin
python tools/dlbin_deploy.py restore --file generated_stratagem_settings.dl_bin
rm "/d/SteamLibrary/steamapps/common/Helldivers 2/data/"*.patch_*
```

**结项状态**：GATER 壳换壳线 **数据层封存**（自毁既不在挂载物、也不在壳 SM，两嫌疑均排除）；
"换壳"作为**机制**已验证可用并沉淀为本配方。
