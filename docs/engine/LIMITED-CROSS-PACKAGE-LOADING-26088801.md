# 有限数量的跨包加载：没有 runtime / ffi 之后怎么做（build `26088801`）

> **纯数据实现**：改 `generated_stratagem_settings.dl_bin` 的两个 8 字节字段，让引擎自己去加载你要的资源。
> 不碰进程内存、不需要 Lua / FFI / 注入 / DLL。
>
> **命名**：本仓库把这条能力叫 **「有限数量的跨包加载」**，不是「任意跨包加载」——
> 纯数据最多声明 **两个** 包，且只对「引擎会为它做包请求」的那条链有效（目前只在战备投送链上验证过）。
> [EXPLOSION-VISUAL §5](../explosions/EXPLOSION-VISUAL-26088801.md) 里 `+0xA8` 换爆炸外观的用法，是它的**单包特例**。
>
> **一句话结论**：引擎在战备被叫出时会加载「战备行的 `+0xA8` 包」和「`+0xF8` 所指武器的包」，
> 外加原版物品自己的包 ⇒ **纯数据最多能声明两个包**（这就是「有限数量」的来源），而对投送舱「武器 + 背包」这个用法刚好够。

## 0. 为什么需要这篇

Helldivers 2 的资产按 **toc 包**（package）组织，引擎**按需**加载：只有被引用的包才驻留内存。

换装/换载荷时，如果新资产的包从来没被加载，引擎会画出**紫色问号占位符** —— 它拿到了物品 id，
但找不到网格/材质。这就是所谓「**包不驻留**」。

历史上这件事是**运行期**解决的：

| 时代 | 手段 | 现状 |
|---|---|---|
| memmod（`25988413` 及更早） | HD2Runtime 调引擎自己的 `RefcountedPackageSystem::request(instance, &id8, 1)` 现场请包 | ✗ **已死**：Lua 5.1 没有 `ffi`，且 EAC 在跑 |
| 现在（`26088801`，纯数据） | 改战备行的两个包声明字段，让**引擎自己**在叫出时加载 | ✓ **本文**（已实机，两个包都成立） |

## 1. 引擎的加载模型

观测 + 外部佐证得到的三个来源：

| # | 来源 | 怎么读 | 能不能改 |
|---|---|---|---|
| A | 战备行的 **`+0xA8`** = 一件物品的 **toc 包 id**（u64） | 直接是包 id | **✓ 能改** |
| B | 战备行的 **`+0xF8`** = **授予武器的 `LoadoutEntry` `+0` id**（u32） | 引擎顺着它 → 武器 → 那把武器的包 | **✓ 能改** |
| C | **原版物品自己的包** | 引擎按原版槽位物品自动加载 | ✗ 不可改（但它本来就在） |

**关键推论**：引擎**不会**为你新换进来的物品自动加载包。所以：

- 只换一件、另一件留原版 ⇒ 原版那件靠 C 正常，新那件需要 A；
- 两件都换、两件同包 ⇒ 一个 A 就够；
- 两件都换、两件不同包 ⇒ A 给一件、B 给另一件。

来源 C 是「原版 Apex 舱明明用了两个不同的包却工作正常」的答案 —— 不需要任何额外声明，
因为两件都是原版物品。

## 2. 三个可编辑的量

| 量 | 位置 | 类型 | 语义 |
|---|---|---|---|
| 槽位物品 | `HellpodRackComponentData` 某行某槽 `+0` | u64 | 物品实体键（送什么） |
| **`+0xA8`** | `StratagemSettings` 行内 `+0xA8` | u64 | **一件物品的 toc 包** |
| **`+0xF8`** | 同一行 `+0xF8` | u64（低 32 位有效） | **授予武器的 `LoadoutEntry` `+0` id** |

本 build 的绝对偏移（StA-X3 那行，行基址 `0xEB64`）：

| 字段 | 绝对偏移 | 原值 |
|---|---|---|
| `+0xA8` | `0xEC0C` | `0x5795E99A988D10B7`（W.A.S.P. 包） |
| `+0xF8` | `0xEC5C` | `0x00000000351B2B3E`（LoadoutEntry 行 172 = W.A.S.P.） |

⚠ 行基址按 build 变（本 build：`generated_stratagem_settings` 第 8 块、第 24 行、400 B 行）。
**不要硬编码**：用 `tools/pod_loadout.py` 现算（§5）。

## 3. 解析链：从「物品名字」到「要写的字节」

三段查表，全部从 typelib + 块几何现算：

### 3.1 物品实体键 → toc 包

`LoadoutPackageComponentData` = **`0x7A858691`** @ `0xA7E18`

```
+0     17,600 B  哈希图（1,100 槽 × 16 B）
+17600 17,632 B  行数组（551 行 × 32 B）

行：+0  u32  常量 0x1534F3FD
    +8  u64  ★ toc 包 id
    +16 u64  未解
    +24 u8 ×2（本 build 全 0x01）
```

键 = **物品实体键**，与 rack 槽里那个 u64 同一空间。
交叉验证：GL-21 一行给出 `0x0089BBE3E284FCAA`，正是实机验证成功的那个 `+0xA8` 值。

### 3.2 物品实体键 → `LoadoutEntry` id（`+0xF8` 要的值）

`LoadoutEntryComponentData` = **`0x4F2CF417`** @ `0xB07D8`

```
+0     6,368 B  哈希图（398 槽）
+6368  6,368 B  行数组（199 行 × 32 B）：{+0 id(u32), +4 type, +8 dlc_pack_id, +12 tags[5]}
+12736   796 B  尾数组（199 × u32）
```

**哈希图的键是物品实体键，行的 `+0` 才是 `+0xF8` 要写的 id** —— 两者不是一回事，容易搞混：

| 物品 | 实体键（rack 槽 / 哈希图键） | `+0xF8` 要写的 id |
|---|---|---|
| W.A.S.P. Launcher | `0xCC786F6491FE7E65` | `0x351B2B3E` |
| LAS-44 Nova | `0x73D84EAAE8C75342` | `0xF71F76BA` |
| LIFT-182 Warp Pack | `0xB49756795D9B0E68` | `0xC1E54B3A` |

### 3.3 反查「这条 rack 属于哪个战备行」

数据里**没有**一个「战备行 → rack」的直接 u64 字段（rack 的键只出现在战备表的块尾辅助区）。
可靠做法是**反查**：

1. 读 rack 原版槽 1 的物品（= 该战备授予的武器）；
2. 取它的 `LoadoutEntry` id；
3. 在 `StratagemSettings` 里找 `+0xF8` 等于该 id 的**唯一**一行；不唯一则退回用「`+0xA8` == 该物品的包」。

对 StA-X3：`+0xF8 == 0x351B2B3E` 全局唯一 ⇒ 行基址 `0xEB64`。
共用 rack 的战备（本 build 有 6 组）会命中多行，此时必须显式指定行基址。

### 3.4 包内容核验（可选但建议）

`D:\mod\cache\resource_index.pkl`（`tools/resource_index_build.py` 产出）：
**3,522 个包 / 62,915 个唯一 id / 322,810 条条目**，`{id → [(包序号, 类型)]}`。

按类型统计目标包，先确认里面有 `mesh` + `material`：

```
武器包 0x601D726DE9C3962F (Nova):     mesh=3  material=13  texture=12  ✓
背包包 0x68F670405A504F68 (Warp):     mesh=2  material=14  texture=13  ✓
```

本 build 全库类型分布：`texture 85,382 · material 50,580 · mesh 48,020 · physics 39,016 · animation 37,023 · particles 18,806 · wwise_stream 8,262 · prefab 3,502`。

> ⚠ 同一个 `file_id` 平均有 **5 份副本**，但**副本数不是判据** —— 判据是「你声明的那个包加载了没有」。

## 4. 判定矩阵

| 换法 | 要写什么 | 结果 |
|---|---|---|
| 只换一件，另一件留原版 | `+0xA8` = 新物品的包 | 两件都亮（原版那件靠来源 C） |
| 换两件、**同包** | `+0xA8` = 那个包（`+0xF8` 不动） | 两件都亮 |
| 换两件、**不同包** | `+0xA8` = **背包**的包；`+0xF8` = **武器**的 `LoadoutEntry` id | 两件都亮 |
| 换两件、不同包，只给 `+0xA8` | — | 一件正常、一件**紫问号**（= 不驻留） |

**实测实例（AC-8，2026-10-23）**：把 AC-8 舱的背包换成 B-1 Supply Pack ——
`+0xA8` 由 AC-8 背包包 `0x49875503E219E80D` 改成 B-1 包 `0x519980A75EBD50AD`，`+0xF8` **一个字没动**，
结果舱里 AC-8 与 B-1 **两件都出模型**。这正是「**保留原包、同时加载新包**」：
武器的原始包由 `+0xF8` 继续提供，`+0xA8` 腾出来给新物品。

为什么双包时是「背包进 `+0xA8`、武器进 `+0xF8`」：`+0xF8` 的语义是**授予武器**，只能放武器；
剩下的位置给背包。原版 Apex 舱就是这个形状（`+0xA8`=Apex 背包包，`+0xF8`=Apex 武器）。


> **✗ 2026-10-25 更正（机甲链路上的实测）**：上面的「纯增量」结论**对机甲不成立**。
> 把爱国者战备行的 `+0xA8` 从它自己的包（`22749a294788af66`）换成解放者包后，
> **依赖爱国者包的左臂立刻变成紫问号** ⇒ 这一格是「**替换**」而不是「追加」：
> 写谁就只加载谁。想同时要两个包，必须占**两个口**（载具 live 行 + 常驻行）。
> 详见 [EXO-ARM-VARIANTS §9](../tables/EXO-ARM-VARIANTS-26088801.md)。

## 4.5 实战例（2026-10-24）：把 GP-20 Ultimatum 的包挂到 **Reinforce**

思路：Reinforce 是**每局必叫**的战备 ⇒ 把目标包声明在它身上，等于「**免费**」让引擎加载一次，
之后依赖该包的改动就有现成驻留（不必再换舱）。

| 项 | 值 |
|---|---|
| 目标行 | `MISSIONS. REINFORCEMENT BEACON`（组 5 行 20，`type=0x7F`） |
| 只改 | 该行 **`+0xA8`：`0x0000000000000000` → `0xB779A2F9D0928E03`**（GP-20 的 toc 包，取自 `LoadoutPackageComponentData` 行 500） |
| 其余 | `+0xF8` 与身份字段一字未动 |
| 离线 | 新工具 `tools/stratagem_package.py`，G1–G7 全 PASS；哈希 `0x04BBE33EF809862A` 不变；封包 sha256 `102dc3bf…` |
| 盘上回读 | 解封 == 我们的明文；**全表只有这一行**的 `+0xA8` 等于该包 id |

⚠ **这一条本身不可直接观测**：`+0xA8` 的作用是「叫出该战备时把包请求进来」，不改变 Reinforce 的外观。
要看到效果必须**再有一个依赖该包的消费方**（例如把 GP-20 塞进投送舱槽位，看模型是否正常而不是紫问号）。
⇒ 把它当「预置驻留」，不是「可见效果」。

**补充（同日第二次装机，与 §R3 形态对齐）**：R3 当年填的是 Reinforce 的**两行**
（`MISSIONS. REINFORCEMENT BEACON` + `TUTORIAL REINFORCEMENT BEACON`），本轮先只填了 missions 一行，
现补齐两行 —— 盘上回读 `+0xA8 == 0xB779A2F9D0928E03` 的行数为 **2**（`0x6FDC` / `0x1247C`），
封包 sha256 `43ffccbd…`。**两行都填**才是 R3 已证「关卡加载即驻留」的那个形状。

⚠ 工具坑：`stratagem_tune.py` 只认 `+80/+84/+104`，写不了 `+0xA8`；新加的 `stratagem_package.py` 专管
`+0xA8` / `+0xF8`（u64）。它的 G6 白名单必须按**写入宽度**展开（u64 = 8 字节），否则 `+0xAC`
会被误报成"漂移"（本轮实际踩过一次）。

## 4.6 实战例（2026-10-24）：给**粒子资源**做驻留（新消费方）

前面的例子都在"物品"（武器 / 背包）这一层。这次出现了一个**新的消费方**：
`SprayWeaponComponentData` 行里的 `firing.muzzle_effect`（`[particles]` 资源 id）。
把喷火器的该字段改成另一把枪的粒子后，游戏里喷出来的是
**灰色半透明方块 + 完全没有火焰** —— 这正是"资源不在内存"的兜底渲染
（详见 `docs/tables/WEAPON-FIRE-MODES-26088801.md` §5.6.6 run 11）。

驻留做法与 §4.5 同一套：把**粒子所在包**声明到每局必叫的 Reinforce 上。

| 项 | 值 |
|---|---|
| 目标粒子 | TX-41 的 firing 粒子 `0xA3D15A3BBC56DE55`，所在包 `0x750605CFC0173701`（24 个资源：该粒子 + 6 贴图 + 2 材质 + 模型/动画/音频） |
| 写入 | `MISSIONS. REINFORCEMENT BEACON`（`0x6FDC`）与 `TUTORIAL REINFORCEMENT BEACON`（`0x1247C`）的 **`+0xA8` = `0x750605CFC0173701`** |
| 离线 | `tools/stratagem_package.py`，G1–G7 全 PASS；哈希 `0x04BBE33EF809862A` 不变；封包 sha256 `8c70575a…` |
| 盘上回读 | 两行 `+0xA8` == 该包 id；全表差异只有这 2×8 B + 2 个校正字 |
| **实机** | **✓ 成立**：FLAM-40 与 P-72 Crisper 的 `+0x70` 都指向该粒子后，两把枪从"灰色占位方块"变成**正常喷出雾状气流** ⇒ `+0xA8` 挂包对**粒子资源**同样有效（消费方不限于物品） |

**包 id 空间校验**：`srkit-names.json` 的 `package` 字段就是本表要的 u64 toc 包 id ——
拿已证的 GP-20 例子对：包 `b779a2f9d0928e03` 里确实有 `GP-20 Ultimatum` 资源，与写进 `+0xA8` 的
`0xB779A2F9D0928E03` 完全一致。

**一个 `+0xA8` 只能装一个包** —— 本 build 里 `+0xA8 == 0` 的空槽普查：

| 行 | 偏移 | 备注 |
|---|---|---|
| `MISSIONS. REINFORCEMENT BEACON` | `0x006FDC` | 每局必叫（R3 已证"关卡加载即驻留"） |
| `TUTORIAL REINFORCEMENT BEACON` | `0x01247C` | 与上面填同一个包才是已证形状 |
| `MISSIONS. SOS Beacon` | `0x0072FC` | 空槽；但要玩家装备并**叫出来**才可能请求 |
| `[TUTORIAL] EXTRACTION` | `0x01260C` | 教学关专用 |

⇒ 现在**一次只能可靠驻留一个包**。要多装一个，得指望玩家装备/叫出 SOS Beacon 那一行。

⚠ 工具坑（本轮踩到）：`--host` 必须给更精确的子串 —— 默认 `NOT USED` 会命中
`ADDITIONAL STRAFING RUNS` 与 `AIR-TO-AIR MISSLES` 两行而报"宿主不唯一"；
另外链式写入换目录时，`dl_library.dl_typelib` 要跟着拷到 `--plain` 同目录（工具按兄弟路径找它）。

## 5. 一条命令

```bash
python tools/pod_loadout.py show  --rack 29
python tools/pod_loadout.py plan  --rack 29 --weapon "LAS-44 Nova" --backpack "LIFT-182 Warp Pack"
python tools/pod_loadout.py build --rack 29 --weapon "LAS-44 Nova" --backpack "LIFT-182 Warp Pack" \
    --out-dir D:/mod/work/podload --seal
```

`build` 做的事：解析名字 → 算包与 `LoadoutEntry` id → 反查战备行 → 判单包/双包 → 调 `pod_rack_swap.py` 改 rack
→ 调 `plain_edit.py` 改战备 → （可选）`dlbin_seal.py` 封装。**它不部署**，部署仍由 `dlbin_deploy.py` 负责。

物品可以写**代号 + 名字**（`"GL-28 Belt-Fed Grenade Launcher"`）或直接给 `0x` 实体键；重名时会列出候选让你精确指定。

## 6. 验证与自检

| 手段 | 说明 |
|---|---|
| **紫问号 = 免费资源探针** | 三个状态可分：**完全没有** = 代码路径没走到；**紫问号** = 走到了但资源缺；**正常** = 资源在 |
| **差分实验** | 同一 rack、同一对物品，只换 `+0xA8` ⇒ 谁出模型就跟着换。这比「改完能看见」强得多，因为它排除「本来就驻留」 |
| **门禁** | rack 侧 9 道（G1/G2/G3/G4/G6/G7/G8/G9）、战备侧 6 道（G1–G6）；都要求重算 Murmur == 原值 |
| **回归对比** | `pod_loadout.py build` 的产物与手工上机验证过的那一版**逐字节相同**（`entities.plain` 与 `stratagem.plain` 都是）|
| **污染排除** | 用 `worldLoot = false` 的物品做实验。`true` 的物品会被地图随机刷新的同类预加载 ⇒ 读数被污染（本项目踩过：B-1 的 `worldLoot = true`，第一次测试因地图刷了它而「正常」） |

## 6.5 声明口普查：全库只有 5 个字段装包 id

用 `resource_index.pkl` 的 **3,522 个包 id** 当目标空间，把 `generated_entities`（275 块）+ 55 张设置表
全部扫一遍（4 字节对齐的 u64 ∈ 包集合），得到的**完整清单**：

| 文件 | 组件 / 表 | type | 偏移 | 使用行数 | 性质 |
|---|---|---|---:|---:|---|
| entities | `LoadoutPackageComponentData` | `0x7A858691` | `+0x8` | **436** | **每个物品恰好一个** = 它自己的包 |
| entities | `EnemyPackageComponentData` | `0x1E232357` | `+0x8` | **157** | 敌人生成包 |
| stratagem_settings | `StratagemSettings` | `0x30EB6399` | **`+0xA8`** | **33** | 每发战备一个（本文用的就是它） |
| planet_override_settings | — | `0x003BA515` | `+0x10` | 8 | 行星包，与物品无关 |
| entities | `EnemyPackageComponentData` | `0x1E232357` | `+0x10` | **1** | 孤例，疑似副包槽 |

**三条硬事实**：

1. **没有任何组件带「包列表」** —— 不存在「一个物品挂 N 个包」的结构，所以不能靠"多填几个槽"扩容；
2. **每个物品只有一个包位**（`LoadoutPackageComponentData +0x8`），而那正是它自己的包 ——
   改它等于把这个物品的资产搬走，**破坏它本身**，不是"额外加一个包"；
3. 唯一能**额外**加载包的地方是战备行：`+0xA8`（直接一个包）+ `+0xF8`（经武器间接一个包）。
   ⇒ **每一行最多 2 个包**，与一次投送几件物品无关。

> ⚠ **本节是「按值搜」，空槽天生看不见** —— 值是 0，永远不在包集合里。所以「只能靠多填几个槽」
> 这个判断当时下早了。§6.6 换结构穷举，结论改写：**每行上限 2 个，但 153 行里 133 行没填满**。

### 那上限还能怎么提

| 方向 | 可行性 |
|---|---|
| 一发战备多塞几件物品 | ✗ 同一行仍然只有 2 个包位（`spawn_payload_size` 最多 4 件） |
| **把别的战备的「空槽」也填上** | **⚠ 待验证**（§6.6）：空槽存量 155 个，且包是引擎级全局驻留 ⇒ 理论上可凑出 >2 个包 |
| 用多个战备分别声明 | ⚠ 同上，取决于「加载时机」假说（§6.6.5） |
| 换掉某个物品自己的包（`+0x8`） | ✗ 就把那个物品本身弄坏了 |
| **合并包**：把需要的资源打进一个新包，让一个包同时含多件物品的资产 | ✓ 兜底解法，属于包层（toc）而不是数据层 |

合并包与本仓库已有的包写入能力相接：`srkit` 侧已实现 HD2 LEGACY package format（`toc.bin`/gpu/stream）的写入器，
引擎能从 `.patch_N` 索引新 ID 的资源。**它是不依赖 §6.6 实验结果的那条确定路线。**

## 6.6 空槽普查：133/153 行没填满，空槽存量 155 个

§6.5 是**按值搜**：把「值 ∈ 包集合」当条件。这个方法的盲区正是本节的主角 ——
**空槽的值是 0，永远不会落在包集合里**。所以「装包口只有两个、每行都用满」的推论只对了一半。

### 6.6.1 换方法：按结构穷举，再按「空/满」分类

1. 用 typelib 取 `StratagemSettings` 行类型 **`0x7BD60854`** 的**全部 68 个成员**（行 400 B），
   拿到每个成员的偏移 / 大小（typelib 无字符串，字段名要从外部名单来，但**偏移是可信的**）；
2. 对每个 8 字节对齐成员，扫 153 行，统计「非零行数 / 互异值 / 落在 307 个 `LoadoutPackage` 包集合里的个数」；
3. 结果是干净的：**只有 `+0xA8` 出现过包 id**（114 行，**114/114 全在包集合里**）。
   其余 u64 成员 —— `+0x10/+0x18/+0x20`（payload 内字符串指针）、`+0x40/+0x98/+0x118/+0x130/+0x140/+0x150/+0x160/+0x178`
   （16 B 时间/延迟组）、`+0xB0`（哈希对）、`+0xF0`（4 行，哈希对）—— **0 命中**；
4. 另外三个旁证：`+0x88` 是 u64 成员但 **153/153 行全 0**（结构上存在、原版从不使用，能不能当第三口**未验证**）；
   `+0xF8` 是 **u32**（不是 u64），也就是它天生只能指「一个有 `LoadoutEntry` 条目的物品」（199 选 1），
   不能像 `+0xA8` 那样填任意包 id；`+0x00` 是战备 id，本 build 恰好是 **1..153 的一个排列**。

⇒ **装包口结构上确实只有两个**，但「每行都用满」是错的。

### 6.6.2 存量：153 行按「空槽」分四类

| 类别 | 行数 | 是什么战备 | 空出来的口能再塞什么 |
|---|---:|---|---|
| 两槽已满 | **20** | 武器 + 背包的双件战备（AC-8 / RR-77 / Spear / W.A.S.P. …） | — |
| **仅 `+0xA8` 空** | **17** | 支援武器（包已由 `+0xF8` 指到那把武器） | **任意包 id**（u64 自由填） |
| **仅 `+0xF8` 空** | **94** | 背包 / 哨戒 / 鹰 / 轨道 / 载具 / 补给 / 任务道具 | **一个有 `LoadoutEntry` 条目的物品**（间接装它的包） |
| **两槽全空** | **22** | 不投送任何物品的战备（增援 / 撤离 / 任务目标 …） | **两样都行** |

**空槽实例总数 = 17 + 94 + 22×2 = 155 个。** 对比原版只用了 114 + 37 = 151 个 ⇒ 存量与原用量同级。

### 6.6.3 22 个「两槽全空」的行（真正的零成本位）

这些行**一件物品都不投送**，所以两个声明口跟它的本职工作没有关系 —— 填什么都不会顶掉它自己的载荷。

| idx | 行基址 | id | 名字 |
|---:|---|---:|---|
| 23 | `0x2d70` | 51 | EAGLE. REARM |
| 38 | `0x522c` | 79 | MISSIONS. Cyborg Carry Data |
| 39 | `0x53bc` | 82 | MISSIONS. Carry Data |
| 41 | `0x56dc` | 152 | MISSIONS. EXTRACTION |
| 47 | `0x603c` | 125 | MISSIONS. SPIRE STERILIZER |
| 53 | `0x699c` | 111 | MISSIONS. Scrambler |
| 54 | `0x6b2c` | 7 | MISSIONS. EXTRACTION BEACON |
| 55 | `0x6cbc` | 114 | MISSIONS. IMMEDIATE EXTRACTION BEACON |
| 56 | `0x6e4c` | 101 | MISSIONS. EMERGENCY EXTRACTION BEACON |
| **57** | **`0x6fdc`** | 127 | **MISSIONS. REINFORCEMENT BEACON** |
| 58 | `0x716c` | 5 | MISSIONS. ORBITAL ILLUMINATION FLARE |
| 59 | `0x72fc` | 149 | MISSIONS. SOS Beacon |
| 60 | `0x748c` | 131 | MISSIONS. Upload Discovery |
| 61 | `0x761c` | 135 | MISSIONS CLAN STATION. Nuke |
| 62 | `0x77ac` | 106 | MISSIONS CLAN STATION. Carpet Bombing Run |
| 70 | `0x842c` | 37 | MISSIONS. OIL RIG EXTRACT |
| 71 | `0x85bc` | 126 | MISSIONS. CALL IN DESTROYER |
| **138** | **`0x1247c`** | 96 | **TUTORIAL REINFORCEMENT BEACON** |
| 139 | `0x1260c` | 41 | [TUTORIAL] EXTRACTION |
| 150 | `0x1386c` | 48 | TANK. TANK RELOAD HE |
| 151 | `0x139fc` | 98 | TANK. TANK RELOAD AT |
| 152 | `0x13b8c` | 62 | TANK. TANK RELOAD CANISTER |

> **为什么 `Reinforce` 是这一档里最好的**：它不占 4 个战备位（HD2 的增援是常驻动作），
> 而且从关卡加载起就在栏里。**它的两个声明口在任何一局里都是白给的。**
>
> ⚠ 但「两槽全空」并不等于「免费」—— R4/R6 证明**不在栏里的行不会被读**。
> 这一档里已经实测的只有 `Reinforcement Beacon`（✓ R3）和 `EAGLE. REARM`（✓ R5-B，需带鹰）；
> `EXTRACTION BEACON` / `EMERGENCY EXTRACTION BEACON` 实测**不在栏里**（✗ R6）。

### 6.6.4 17 个「仅 `+0xA8` 空」的行（任意包）

| idx | 行基址 | id | 战备 | `+0xF8`（已指到的武器） |
|---:|---|---:|---|---|
| 92 | `0xc04c` | 85 | PRESIDENT REWARDS. MACHINEGUN | `0xF8FECED4` |
| 94 | `0xc774` | 83 | TEAM WEAPONS. GRENADE LAUNCHER | `0xC74C740D`→Grenade Launcher |
| 97 | `0xcc24` | 58 | TEAM WEAPONS. RAILGUN | `0xB77A3F9D`→Railgun |
| 98 | `0xcdb4` | 116 | TEAM WEAPONS. HARPOON GUN | `0x14118731`→Speargun |
| 100 | `0xd0d4` | 65 | TEAM WEAPONS. LASER CANNON | `0xA83CF95D`→Laser Cannon |
| 101 | `0xd264` | 153 | TEAM WEAPONS. LASER PULSE CANNON | `0x9C77755B`→Quasar Cannon |
| 102 | `0xd3f4` | 144 | TEAM WEAPONS. SNIPER | `0x83970A39`→Anti-Materiel Rifle |
| 103 | `0xd584` | 151 | TEAM WEAPONS. EXPENDABLE ANTI-TANK | `0xCB778090`→EAT |
| 104 | `0xd714` | 15 | TEAM WEAPONS. EXPENDABLE ANTI-TANK (Booster) | `0xCB778090`→EAT |
| 105 | `0xd8a4` | 40 | TEAM WEAPONS. EXPENDABLE NAPALM LAUNCHER | `0x6C19DD47`→Expendable Napalm |
| 107 | `0xdbc4` | 6 | TEAM WEAPONS. COMMANDO | `0x8518B86B`→Commando |
| 108 | `0xdd54` | 115 | TEAM WEAPONS. FLAMETHROWER | `0x5563504D`→Flamethrower/Cremator |
| 109 | `0xdee4` | 33 | TEAM WEAPONS. HEAVY MACHINEGUN | `0x1FC9CA61`→HMG ×3 |
| 110 | `0xe074` | 95 | TEAM WEAPONS. MACHINEGUN | `0x1B4F8FA2`→Machine Gun |
| 111 | `0xe204` | 13 | TEAM WEAPONS. LIGHT MACHINE GUN | `0x00DAE676`→Stalwart ×4 |
| 119 | `0xee84` | 63 | TEAM WEAPONS. CHEM GUN | `0xF77D6B07`→Sterilizer |
| 128 | `0xfc94` | 66 | TEAM WEAPONS. LASER RIFLE ION | `0xF71F76BA`→Nova |

这一类最实用：**你本来就要带一把支援武器、本来就要叫它**，而它的包已经由 `+0xF8` 负责了，
`+0xA8` 就是纯增量。想加载哪个包就填哪个。

### 6.6.5 94 个「仅 `+0xF8` 空」的行

84 个不同战备、94 行（`Jump Pack` / `Portable Hellbomb` / `Resupply` / `Medical Supplies` / `CARGO CONTAINER` /
`Super Earth Flag` 各出现两次）。覆盖面是：13 个背包、9 个哨戒、11 个鹰、13 个轨道、9 个工事/地雷、
13 个载具（FRV / 机甲）、以及补给与任务道具。
这一档只能填「有 `LoadoutEntry` 条目的物品」（199 选 1）—— 比 `+0xA8` 窄，但存量最大。

### 6.6.6 上限重算

| 口径 | 原来的结论 | 现在 |
|---|---|---|
| 单行能声明几个包 | 2 | 2（不变，结构决定的） |
| **一局能声明几个包** | 2 | **16**（4 个战备位 × 2 + 增援信标 4 + SOS Beacon 2 + 带鹰时 `EAGLE. REARM` 2；不带鹰 14）—— ✓ 实机：R3 三包并存、R7「带上去就算在栏」、R9「SOS 单人默认在栏」 |
| **不占战备位能声明几个** | 0 | **8**：`REINFORCEMENT BEACON` 4（✓ R3）+ `SOS Beacon` 2（✓ R9）+ `EAGLE. REARM` 2（✓ R5-B，带鹰时）；`EXTRACTION` 系列已否证（R6） |
| 一发投送舱里放几件不同包的物品 | 2 | **≥2 已实机**；`spawn_payload_size` 上限 4，只要凑得出 4 个驻留包就能放 4 件 |

### 6.6.7 还没回答的那个问题：什么时候加载

§6.5 §7 里「`+0xA8` 写任意包 = 通用预加载开关？」一直标着**未测**。现在有三档假说，差别极大：

| 假说 | 触发条件 | 若成立的后果 |
|---|---|---|
| **A 装备即加载** | 战备进了 4 个装备位就预加载 | 带 4 个战备 = 白拿 4 个包；`Reinforce` 不占位 ⇒ 可能连占位都不用 |
| **B 叫出即加载** | 叫出那发战备时才请求 | 需要主动叫一次；支援武器/补给类最方便 |
| **C 关卡加载时无条件** | 153 行全部预加载 | 填上就常驻，**完全免费**；但这等于原版会把整个战备资产库驻留，先验概率低 |

**判定实验（两/三个任务，同一份 build，单变量）**

固定 rig 用已经在实机站住的那一套（§POD-RACK 轮 C/D/F）：
rack 29 槽 1 = **LAS-44 Nova**（包 `0x601D726DE9C3962F`）、槽 2 = **LIFT-182 Warp Pack**（包 `0x68F670405A504F68`），
战备行 `0xEB64` 的 `+0xA8` 只填 **Nova 的包** ⇒ 基线读数：**Nova 正常 / Warp 紫问号**（已实机）。

在这个 rig 上加**一个**动作：把 **Warp 的包**填进一个跟我们无关的空槽。

| 任务 | 额外动作 | 判读 |
|---|---|---|
| **R0** | 只叫投送舱，`Resupply`/`SOS` 都**不叫** | Warp 正常 ⇒ **C 或 A**（不叫也加载，免费档最高）；紫问号 ⇒ 排除 C，进 R1 |
| **R1** | 先叫一次 `Resupply`（`+0xF8` 空槽 = Warp 的 `LoadoutEntry` `0xC1E54B3A`），再叫投送舱 | Warp 正常 ⇒ **B 成立**（`+0xF8` 空槽可用） |
| **R2** | 先叫一次 `SOS Beacon`（`+0xA8` 空槽 = Warp 的包），再叫投送舱 | Warp 正常 ⇒ **B 成立且 `+0xA8` 可填任意包** |
| **R3**（可选） | 把 Warp 的包填进 `Reinforce` 行 57/138 的 `+0xA8`，然后叫一次增援 | 验证「零成本位」这一档 |

R1/R2 任一正常，就说明**「空槽 = 包加载器」**成立，6.6.6 的 8 个包上限可以直接用。
R0 正常则连叫都不用叫，直接进免费档。

#### 实验登记（同一 build、单变量、逐轮）

| 轮 | 变量 | 读数 | 判定 |
|---|---|---|---|
| **R1** | `Resupply` 两行 `+0xF8` = Warp 的 LOE `0xC1E54B3A`；先叫 Resupply，再叫投送舱 | Warp **紫问号**；Resupply 补给箱**完全正常** | ✗ **否证**：`+0xF8` 在「不授予武器的战备」上**不触发包加载**。补给箱也没坏 ⇒ 它连「载荷资产包」都不是，就是**根本没被读** |
| **R3** | `Reinforce` 两行 `+0xA8` = Warp 的包 `0x68F670405A504F68`；**不叫增援** | Warp **正常渲染**，而且**连死都没死** —— 没有任何游戏内动作 | ✓✓ **阳性，最高档**：**填上就驻留**。这类包在**关卡加载时**就被请求，与「叫不叫、带不带」无关 |
| **R4** | `M-1000 Maxigun` 行 `+0xA8` = Warp 的包（**覆盖**原值 `0xB2C6…`）；**不带、不叫** | Warp **紫问号** | ✗ **否证**：`+0xA8` **不是整表遍历**。关卡加载只读「**进栏**」的战备的行 ⇒ 能用的不是 155 个空槽，而是「进栏行 × 2」 |
| **R5-A** | `Eagle Rearm` 行 `+0xA8` = Warp 的包；**不带任何 Eagle** | Warp **紫问号** | 不是「无条件常驻」 |
| **R5-B** | 同一 build，**带一发 Eagle** | Warp **正常**；且 4-4-4-4 **Eagle Rearm 回收照常可用** | ✓ **条件常驻成立**：进栏即预加载，且它不占战备位。附带结论：**`+0xA8` 是纯增量声明**，换掉不会破坏本战备载荷 |
| **R6** | `EXTRACTION BEACON`（54）+ `EMERGENCY EXTRACTION BEACON`（56）的 `+0xA8` = Warp 的包；不带、不叫 | Warp **紫问号** | ✗ 撤离信标**不在栏里** ⇒ 「两槽全空」≠ 免费 |
| **R9** | `MISSIONS. SOS Beacon`（59）的 `+0xA8` = Warp 的包；**不选它、只在单人局里带着不占位的默认栏** | Warp **正常** | ✓ **单人默认栏里就有 SOS Beacon** ⇒ 又白拿 **2 口** |
| **R10** | 一个舱送三件**不同包**的物品：rack 29 = Nova / Warp / GL-28（`+556`=3），包分别铺在 `+0xA8` / `+0xF8` / 增援信标 57 | **三件全部正常渲染** | ✓✓ **上限被打破**：旧上限 2 件不同包 → 实机 3 件 |
| **R12** | rack 29 四件：Nova / Warp / GL-28 / **GL-28 背包**（`+556`=4），三个包仍由战备行 + 增援信标 + SOS Beacon 提供 | **四件全出**，GL-28 拾取背包后**能装填开火** | ✓✓ 投送舱容量到顶（`spawn_payload_size` 上限 4），且只用了 1 个舱行口 + 2 个免费口 |

R1 + R3 合起来把模型确定下来了：

| 字段 | 何时被读 | 证据 |
|---|---|---|
| `+0xA8` | **关卡加载时**（无条件） | R3：没叫、没带、没死，包照样驻留 |
| `+0xF8` | 只在**该战备授予武器**时 | R1：Resupply 不授予武器 ⇒ 写了也没人读 |

> 这是本项目在纯数据路线上找到的**第一个「免费供体」**：`Reinforce` 不占战备位、不必被叫出，
> 两个声明口填什么都在关卡加载时就驻留。但**「两槽全空」不等于「免费」** —— 见下面 R4/R6 的否证。

**范围有多大？—— R4 已答：不是整表，是「常驻行」。**

R4 把 Warp 的包填进 **M-1000 Maxigun** 那一行（`0xf654`），**不带、不叫**，读数 **紫问号**。
⇒ 关卡加载**不会**遍历 153 行，只处理「常驻」的那一批。所以能用的不是 155 个空槽，
而是「**常驻行 × 2**」，上界 = 22 个零成本行 × 2 = **44 个**。

**下一个问题：什么叫「常驻」？—— R5 已答：进栏即常驻。**

R5 用 `Eagle Rearm`（行 `0x2d70`，两槽全空）做了两次任务 —— 它是「带了鹰才进栏」的典型：

| 任务 | 带装 | 读数 | 判定 |
|---|---|---|---|
| **R5-A** | 不带任何 Eagle 战备 | Warp **紫问号** | 不是无条件常驻 |
| **R5-B** | 带一发 Eagle | Warp **正常**；**Eagle Rearm 本身照常可用** | ✓ **条件常驻成立**：进栏就预加载，而它不占 4 个战备位 |

两轮合起来，规则可以写成一句话：

> **关卡加载时，引擎会给「这一局出现在你战备栏里的每一发」请求它的 `+0xA8` 包** ——
> 不管它占不占 4 个战备位。

于是供体分成三档：

| 档 | 例子 | 成本 | 实测 |
|---|---|---|---|
| **永远在栏**（真免费） | `MISSIONS. REINFORCEMENT BEACON`（57）、`TUTORIAL REINFORCEMENT BEACON`（138）、`MISSIONS. SOS Beacon`（59，单人默认栏自带） | **0** —— 不带也在 | ✓ R3 / R9 已证 |
| **带了才进栏**（半免费） | `EAGLE. REARM`（23） | 你得带一发 Eagle —— 但你本来就要带 | ✓ R5-B 已证 |
| **占 4 个战备位之一** | 17 个支援武器行（`+0xA8` 空）等 | 一个战备位 | ⚠ **正在测（R7）** |
| ✗ **不在栏里** | `EXTRACTION BEACON`（54）、`EMERGENCY EXTRACTION BEACON`（56）、`TEAM WEAPONS. MINIGUN`（124，未带） | — | ✗ R6 / R4 否证 |

> ## ⚠ 更正（2026-10-25 晚）：**行 138 不是常驻口**，12 个「块」是**分类**不是池
>
> R3 当时**一次把包写进了 57 和 138 两行**，读数「Warp 正常」，于是记成「两行都常驻」。
> 现在按容器结构重新看：`generated_stratagem_settings` 的 **12 个块 = 12 个分类**
> （`BACKPACK` / `CONSUMABLES` / `EAGLE` / `EMPLACEMENTS` / 特例 / `MISSIONS` / `ORBITAL` /
> `PRESIDENT REWARDS` / `TEAM WEAPONS` / `SENTRYS` / **`TUTORIAL`** / `VEHICLES`），
> 而 **行 138 = `TUTORIAL REINFORCEMENT BEACON`（块 10，`0x1247C`）**，只在**教学关**里用；
> 普通任务的增援信标是 **行 57 = `MISSIONS. REINFORCEMENT BEACON`（块 5，`0x6FDC`）**。
> ⇒ R3 的阳性读数来自 **57**，138 是同一轮里写的死行（被误当成第二个免费口）。
>
> **佐证（同一批数据）**：§11 的敌人炮塔曳光修复把 `FDF011DAECF24312` 写在**行 59（SOS Beacon）**
> ⇒ 曳光出来了；而火箭炮塔那几轮把同一个包写在**行 138** ⇒ 拖尾/命中爆炸一直不出现。
> 同一包、同一件弹丸、唯一变量就是「写在哪一行」。
>
> **修正后的免费/半免费口**：
>
> | 行 | 真身 | 什么时候被读 |
> |---|---|---|
> | **57** `0x6FDC` | `MISSIONS. REINFORCEMENT BEACON`（块 5） | ✓ 普通任务常驻（R3 实际验证的就是这行）|
> | **59** `0x72FC` | `MISSIONS. SOS Beacon`（块 5） | ✓ 单人默认栏（R9 ✓ 实机）|
> | **23** `0x2D70` | `EAGLE. REARM`（块 2） | ✓ 带一发 Eagle 时（R5-B ✓）|
> | ~~138~~ `0x1247C` | `TUTORIAL REINFORCEMENT BEACON`（**块 10**） | ✗ 教学关才读 ⇒ **普通任务里等于没写** |
>
> 查块归属：`python tools/strat_slot_census.py --row N`（工具已按块枚举，但**旧档把「块」当成了「池」**）。

R5-B 的第二个读数同样重要：**`+0xA8` 是纯增量声明**。Eagle Rearm 的 `+0xA8` 被换成 Warp 的包后，
按 4-4-4-4 回收**照常工作** —— 说明它**不是**「这发战备载荷的资产包」，换掉不会让战备本身坏掉。
§6.6.8 里那条最大的风险（填错会破坏本战备载荷）就此划掉。

> **名字纠正（重要，R6 踩到的）**：R6 原本按外部名单的显示名选行，那两份名单把 `MISSIONS. EXTRACTION`（41）
> 和 `MISSIONS. EXTRACTION BEACON`（54）**贴反了**。现在改成读行内 `+0x10` / `+0x18`
> 指向的字符串（**payload 相对**偏移），拿到的内部名才是权威：
> `MISSIONS. EXTRACTION`（41）、`EXTRACTION BEACON`（54）、`IMMEDIATE EXTRACTION BEACON`（55）、
> `EMERGENCY EXTRACTION BEACON`（56）。`strat_slot_census.py` / `strat_slot_fill.py` 已改为优先用内部名。
> 真正的 `MISSIONS. EXTRACTION`（41）**还没测**。

**R7：带进战备位的算不算「在栏」？—— ✓ 算。**

`TEAM WEAPONS. CHEM GUN`（行 `0xee84`，= Sterilizer）的 `+0xA8` = Warp 的包，
带 Sterilizer 但**整局不叫它**：叫出投送舱后 **Warp 直接正常**；随后把 Sterilizer 叫出来，
它自己也完全正常（再次确认 `+0xA8` 是纯增量）。

> **供体资格：不能选会在地图上刷新的武器。** 地图上的随机武器架会预加载它自己的包 ——
> 本轮踩过/避开的：`MG-43 Machine Gun`、`Railgun`。供体行要挑债券武器
> （`CHEM GUN` / `HARPOON GUN` / `LASER RIFLE ION` 这一档），它们的包不可能被地图自带的内容拉进来。

到这里规则收敛成一句：

> **关卡加载时，引擎给「这一局出现在你战备栏里的每一发」请求它的 `+0xA8` 包。**
> 「在栏」= 4 个带上去的 + 引擎自己塞进来的（增援信标、带鹰时的 `EAGLE. REARM`）。
> 不需要被叫出，也不需要「永远在栏」。

#### 一局能声明几个包（最终账）

| 来源 | 口数 | 证据 |
|---|---:|---|
| 4 个战备位 × 2 口（`+0xA8` 自由包 / `+0xF8` 物品条目） | **8** | ✓ R7（第 1 口）+ R3/R5（`+0xF8` 见 R1 限制） |
| `MISSIONS. REINFORCEMENT BEACON`（57）+ `TUTORIAL REINFORCEMENT BEACON`（138） | **4** | ✓ R3 |
| `MISSIONS. SOS Beacon`（59）—— **单人默认栏自带** | **2** | ✓ R9 |
| `EAGLE. REARM`（23，带鹰时） | **2** | ✓ R5-B |
| **合计** | **16**（不带鹰 14） | — |

对比原来的 **2** —— 提高 6~7 倍，且全程纯数据、不需要任何运行期手段。

**R10：把它用起来 —— 一个舱送三件不同包的物品（✓✓ 已实机）。**

旧上限 2 的直接后果是「三件不同包的物品不可能同时渲染」。实测 rig：
rack 29 三个槽（Nova / Warp Pack / GL-28 Belt-Fed，`+556` 设 3），三个包分别铺在
战备行 `+0xA8`（Nova）、增援信标 57/138 `+0xA8`（Warp）、`SOS Beacon` 59 `+0xA8`（GL-28）——
**后两个是纯免费口**，投送舱自己只出了一口。

读数：**三件全部正常渲染**。上限从「2 件不同包」抬到 **≥3**，而且不需要牺牲舱行自己的声明。

> 副产品：GL-28 没有背包就开不了火（弹药走第四种模型 `WeaponLinkedAmmoComponentData`，
> 见 [WEAPON-AMMO-RESERVE §4b](../tables/WEAPON-AMMO-RESERVE-26088801.md)）。
> 正在用合并器把「GL-28 弹药行」和这套 rig 拼成一份上机 —— 也是合并器的首次实机
> （[MOD-MERGER §3.1](../cases/MOD-MERGER-26088801.md)）。

两个字段的行为必须分开记：`+0xA8` 是**声明式**的（关卡加载时请求），`+0xF8` 是**解析式**的
（只有走到「本战备授予武器」那条链才被读）。从 §6.5 起把两者当成"一对声明口"是个简化，R1/R3 把它拆开了。

> R1 最初留过「包加载了但很快释放（引用计数掉回 0）」这个替代解释 —— **R3 直接排除了它**：
> R3 里根本没叫增援，包从关卡加载起就一直在，紫色 ? 不会再出现。

### 6.6.8 风险与注意

| 风险 | 说明 | 缓解 |
|---|---|---|
| ~~`+0xA8` 可能是「本战备载荷的资产包」，填错会让那个战备自己坏掉~~ | ✓ **已排除**（R5-B）：`Eagle Rearm` 的 `+0xA8` 换成 Warp 的包后，4-4-4-4 回收**照常工作** ⇒ 它是**纯增量声明** | — |
| `+0xF8` 语义是「授予武器」 | 填进非武器条目可能改变该战备的授予物 / UI（R1 里 Resupply 一切正常，但那是"没被读"） | 只在授予武器的战备上用 |
| 12 个块 = 12 个战备池 | 同一战备出现在多个块（`REINFORCEMENT BEACON` 57/138、`RESUPPLY` 13/86…） | **同名行全部一起改**，否则可能改到不被使用的那个池 |
| 任务脚本驱动的行（`Upload Data` / `ACTIVATE DRILL` / `CALL IN SUPER DESTROYER` / `Carpet Bomb`） | 改动可能影响任务流程 | 不优先用；只在确认机制后用 |
| `+0x88` 全零的 u64 | 看着像第三个口，但**没有任何证据**它能被用 | 只在空槽路线彻底走不通时才试（一次只动一格） |
| 「装了才进栏」的行（`Eagle Rearm` 等） | 不带对应装备时**不加载**（R5-A 紫问号） | 要它就得真带上那件装备 —— 但那件装备本来就要带才划算 |

> 查表命令：`python tools/strat_slot_census.py`（全表）、`--free`（只看有空槽）、`--both`（只看两槽全空）、
> `--row N`（单行详情，含绝对偏移）、`--json out.json`。

## 7. 能力边界（为什么叫「有限数量」）

**能做的**

- 把任意**合法拾取物**（`Interactable` + 对应组件）放进投送舱的槽位；
- 让**最多两个**不同包的物品同时渲染；
- 用 `+0xF8` 顺带改变「这发战备授予的武器」。

**做不到 / 未验证**

| 限制 | 说明 |
|---|---|
| **单行超过两个包** | 没有第三个声明口（唯一候选 `+0x88` 全 153 行零值，**无任何证据**） |
| **一局超过两个包** | ✓✓ **已实机**（R3 三个包同时驻留；R7 带进战备位即预加载；R9 SOS 单人默认在栏）⇒ 一局最多 **16** 个包，不再是 2 |
| 加载「包里没有的资源」 | 声明只是请求加载；资源必须真的在包里（用 §3.4 先查） |
| 声明式包依赖 | ✗ 已否证三次：包头 56 B 不是依赖表、56 张明文表对资产包 0 引用、bundle 不是加载单位 |
| `+0xA8` 写任意包 | ✓✓ **已实机**（R3：`Reinforce +0xA8` = Warp 的包 ⇒ 关卡加载即驻留，不需要叫、不需要带） |
| `+0x88` 当第三口 | **未测** —— 全 153 行零值，无任何证据支持，只在空槽路线走不通时才值得试 |
| `+0xF8` 的 UI 副作用 | 改它是否影响战备名/图标未系统记录（两轮都没观察到异常） |
| 3 件以上生成 | `spawn_payload_size` 可写（1–4），但槽 5–8 在武器舱是只读 |

## 8. 与 Runtime 的对照

| | HD2Runtime（运行期） | 本文（纯数据） |
|---|---|---|
| 加载包的时机 | 写槽位**之前**显式 `request` | 引擎叫出战备时按声明加载 |
| 能声明的包数 | 任意（逐个请求） | **每行最多 2 个**；一局靠空槽可凑更多（§6.6，待验证） |
| 失败表现 | 写被拒（`ASSET_UNAVAILABLE`），保留原版物品 | 静默 —— 出现紫问号 |
| 持久性 | 重启还原（内存态） | **落盘，重启不还原** |
| 前提 | `ffi` + 运行期执行权 | 只要文件写权限 |
| 状态 | ✗ 本 build 不可用 | ✓ 已实机 |

SDK 的 `packages`/`residentPackages` 概念与本文一致：它把「rack 包 + 战备包 + **原版物品的包**」列为常驻集合；
本文补上的正是「**换进来的物品**怎么进这个集合」。

## 9. 溯源与许可

外部依据（只引用字段名/偏移/结论）：

- **[HD2Runtime by SkyeShade](https://github.com/SkyeShade/HD2Runtime)** —— `+0xA8` 为战备根包、
  `+0xF8` 武器的包、`RefcountedPackageSystem::request` 的用法与参数要求。
- **HD2Runtime SDK 0.30.3** —— `docs/pod-payloads.md`（`residentPackages` 三分量、
  「资源只在它自己的包加载时才有」）、`PodPayloadCapabilities.json`（`worldLoot`、`packageResidency: LIVE_PROVEN`）。

本项目一手证据：`+0xA8`/`+0xF8` 的语义定位、item→包 与 item→`LoadoutEntry` 解析器、
两个包槽的实机差分、以及 `pod_loadout.py` 对实机验证件的逐字节复现。
数据结构细节见 [POD-RACK](../tables/POD-RACK-26088801.md)。
