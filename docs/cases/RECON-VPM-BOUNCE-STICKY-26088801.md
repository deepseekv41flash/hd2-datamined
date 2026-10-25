# 只读侦察：Vanilla Plus Megapack v42 的 `BetterStratagemBounce` / `StickyGrenadeHandles`

> **结论先说**：两个都**不是**改 `StickyComponentData`。
> `BetterStratagemBounce` 改的是**战备表每行 `+0x170` 的一个字节位**；
> `StickyGrenadeHandles` 改的是**物理材质库里 `sticky_grenade_handle` 材质的 userData**（4 B）。
> 两者都是**运行时内存补丁**（Bingus Shared Runtime，FFI + `WriteProcessMemory`），不是数据表 mod。
> 相关：[STICKY-COMPONENT](../tables/STICKY-COMPONENT-26088801.md) · [STATUS-EFFECTS](../tables/STATUS-EFFECTS-26088801.md)

---

## 1 包结构

| 项 | 值 |
|---|---|
| 分发包 | `D:\Downloads\Vanilla Plus Megapack 16294 42 2026-10-18T20-21Z Nw8BMLo12.zip`（4.4 MB，25 个独立 option） |
| 版本 | README：`v42`，支持 **Steam build 25480438 / EXE 1.8.46015.0**，需 Bingus Shared Loader v18+ |
| 每个 option | 一个 `9ba626afa44a3aa3.patch_0`，内含 **2 个 lua 资源**（主脚本 + 共用 6,953 B 运行时 `0x79E4F54AA542EC98`） |
| `StickyGrenadeHandles` 主脚本 | `0x5FCDE649E6A27173`，45 KB，**可读 Lua 源码**（919 行，含作者注释） |
| `BetterStratagemBounce` 主脚本 | `0x19170CA4B0725FF0`，73 KB，正文是 **LuaJIT 字节码**（`loadstring("\27LJ…")`，解码后 18,693 B） |
| 源码 | Megapack 源码树里有它：`VanillaPlusMegapack-main/components/BetterStratagemBounce/src/navigation_patch.lua`（字节码里出现 `archive-v15.4.1`，与 README 的 `v15.4.1` 对得上 ⇒ 同一版本） |

## 2 `BetterStratagemBounce` 改的是**战备表**，不是 sticky

`src/navigation_patch.lua` 的常量：

```lua
buffer_rva = 0x348e8f8,   -- game.dll: 战备设置缓冲区
table_rva  = 0x37cb600,
data_size  = 80280, groups = 11, record_size = 400,
flag_offset = 0x170,      -- ★ 每行里的那个字节
vanilla_flags = { 2, 2, 0, 0, 2, … }   -- 按 kind 索引的期望值
```

做的事（`patch.apply`）：

| 步 | 内容 |
|---|---|
| ① 校验容器 | 每组头必须是 `LDLD` / ver 1 / type **`0x30EB6399`（StratagemSettings）** / 行数组指针 + count 自洽 |
| ② 逐行校验 | `kind = u32(record+0)` 唯一、`table[kind]` 指针 == 该行地址、**`record + 0x170` 的字节 == `vanilla_flags[kind]`** |
| ③ 写入 | **`bit.band(flags, 0xFD)`** —— 即**清掉 bit `0x02`**（`2→0`、`3→1`） |
| ④ 规模 | 它的 build：**149 行里 103 行**被改，然后整块读回校验 |
| ⑤ 回滚 | 出错时只还原"仍是自己写过的样子"的行（不覆盖别人的改动） |

⇒ 完全没碰 `StickyComponentData`。它动的是 **`generated_stratagem_settings` 的行内字节 `+0x170`**。

## 3 本 build（26088801）对照 —— 这个 mod 在我们这版会**拒绝执行**

| 项 | 他们的 build 25480438 | 我们 26088801 |
|---|---|---|
| 战备行数 | 149 | **153**（11 组 + 另有 1 组非战备） |
| `+0x170` 分布 | 期望由 `vanilla_flags` 表描述 | **`{0:43, 1:5, 2:98, 3:7}`** |
| 带 bit `0x02` 的行 | 103 | **105** |
| 按 `kind` 逐行比对 | — | **74 匹配 / 74 不匹配** |

⇒ mod 的第 ② 步会失败并打印 `Stratagem navigation flags differ from supported build`，
**一个字节都不会写** —— 这就是它 build-locked 的真实原因（不是哈希检查，是这张 `vanilla_flags` 表漂了）。

**`+0x170` 是什么**：本 build 取值只有 `0/1/2/3`，typelib 里该位置是**两个相邻 u8**，社区 catalog 没有命名。
按值抽样看**像"投放/行为类别"**：`EAGLE 500KG`/`ORBITAL GATLING`/`EXTRACTION BEACON` = **0**；
`TEAM WEAPONS`/`EMPLACEMENTS`/`BACKPACK` = **2**；`PRESIDENT REWARDS` 系列（医疗背包/火箭哨戒/弹药箱）= **3**。
⇒ **具体含义未证**（mod 只证明"清 bit 0x02 会让信标弹跳变好"，未说明这个枚举叫什么）。

## 4 `StickyGrenadeHandles` 改的是**物理材质库**，也不是 sticky

作者注释已经把机制写清楚了，源码只做了**一次 4 字节写入**：

| 项 | 内容 |
|---|---|
| 现象 | G-123 热熔 / sticky stun grenade 的**手柄先着地时会弹开** |
| 原因 | 手柄是一个独立 capsule，自带材质 **`sticky_grenade_handle`**；引擎**只在接触材质的 tag == 投掷物 sticky 材质**时才粘住 |
| 唯一写入 | `hknpMaterialLibrary` 条目 `sticky_grenade_handle` 的 **`userData`（低 dword，+0x48）** ← `0xC4692706`（材质名 `throwable` 的 thin hash） |
| 只读校验 | `ThrowableComponent +0x54`（sticky 必须 == 1）、`+0x164`（sticky 材质必须 == `throwable`），对象 = `G-123 Thermite (0xC5C05FCB5747C799)`、`sticky stun grenade (0x3FA94F58F596BC0B)` |
| 时序 | 等实体设置加载（实战约 6 s）→ 一次 1 次保护查询 → 写 → 读回校验 → 日志 `applied` / `already applied` |
| 不变量 | 摩擦、回弹等其它材质参数**一律不动**；该材质全游戏只有这两颗雷用 |

⇒ 它**只读** `ThrowableComponent`（当"前提检查"，防止数据被官方更新后瞎改），
**一次都没碰 `StickyComponentData`**，改的是引擎侧 havok 材质库 —— 那张表**不在任何 `.dl_bin` 里**。

## 5 对我们的路线意味着什么

| mod | 能不能用数据路线（dl_bin）等价实现？ |
|---|---|
| **BetterStratagemBounce** | **能**。`generated_stratagem_settings` 每行 `+0x170` 就是我们的字段，直接清 bit `0x02` 即可（`plain_edit.py` / `stratagem_tune.py` 那套保哈希流程），**不需要 loader**。⚠ 两点：① 105 行一起变，影响面大；② 清 bit 之后的实际观感要实机确认 |
| **StickyGrenadeHandles** | **dl_bin 不能，但资源路线可以**（B · 跨载体等价）。它改的是 havok 材质库条目的 `userData` —— 属于 **`physics` 资源族**：我们已逆出 Havok 2019.01 tagfile 载荷布局并改过同族的 mass 字段（`CASE-STUDY-20261021.md` §17–§18），所以"能改"这件事有同族实证；⚠ 但"这一个 userData 落在哪份资源、偏移多少"**尚未针对本条验证** |

## 7 追加侦察（2026-10-25）：`sticky_grenade_handle` 的 userData 在哪份资源里？

目标：给 B 档（跨载体等价）补证据 —— 那个被 mod 写的 `userData` 4 B 到底落在哪份资源。

### 7.1 先钉死 hash ↔ 名字（工具级，可复现）

```bash
python -m srkit hash sticky_grenade_handle throwable
# sticky_grenade_handle  murmur64=0x9A056E1C82863322  murmur32=0x9A056E1C
# throwable              murmur64=0xC4692706CC9E97D7  murmur32=0xC4692706
```

⇒ mod 里的 `Mod.HANDLE = 0x9A056E1C` / `Mod.THROWABLE = 0xC4692706` 就是这两个名字的 **murmur32（thin hash）**，与我们工具算的一致。

### 7.2 引用侧：**已定位**

| 项 | 值 |
|---|---|
| 资源 | `physics` **`0xC5C05FCB5747C799`**「G-123 Thermite」，7,068 B，在包 `fc5b6bff0db90aab` 与 `dfb81f9917285965` 各一份 |
| 载荷形态 | **Havok 2019.01 tagfile**：`TAG0`/`SDKV20190100`/`DATA`/`TST1`/`TPTR`/`TBDY`/`TSTR`/`DTBDY`/`TPAD`/`INDX`/`ITEM`/`PTCH` |
| 内容 | **纯 shape 数据**：`hknpCompoundShape` + `hknpCapsuleShape` + `hknpConvexShape`（手柄就是那个 capsule）+ 质量属性；类型表里**没有任何 `hknpMaterial*`** |
| `sticky_grenade_handle` 的 hash | **`+0x154`**（唯一的 1 处） |
| `throwable` 的 hash | **`+0xC4`**（唯一的 1 处） |
| `+0x150` 起的结构 | `flags=0x00001002 · 0x9A056E1C · 0xB03B6BFF · 0xAEB35C56 · 1.0f · 0 · 0 · 0 · 0 · 1.0f` ⇒ 像"材质/摩擦规格"块：3 个材质 hash + 摩擦/回弹系数 |

⇒ 资源里只有**材质引用（hash）**，没有名字、也没有 `userData`。

### 7.3 定义侧：**未找到**（而且数据目录里根本没有那个名字）

| 检查 | 结果 |
|---|---|
| G-123 的两份 `material`（渲染材质）资源 | 都不含这两个 hash，也不含材质名 |
| 23 GB `bundles.*.nxa` 全文 grep | `sticky_grenade_handle` **0 命中**；`hknpMaterialLibrary` **0**；`hknpMaterial*` **0** |
| 412 MB 顶层散包（`data/` 根下的 hash 文件）grep | 同样 0 |
| 对照组（证明 grep 有效） | `hknpCompoundShape` 在 `bundles.00.nxa` **17 命中**；`SDKV20190100` **66 命中** |

⚠ **但这条不能当成"数据里没有"**：bundle 里只有一部分 havok 载荷是未压缩的（`hknpCompoundShape` 只有 17 次，
而 physics 资源有 39,172 份）⇒ grep 只覆盖**未压缩那部分**。

### 7.4 现在能下的结论（三态）

| 结论 | 态 |
|---|---|
| `sticky_grenade_handle` / `throwable` 的 hash 算法与取值 | **✓ 离线**（`srkit hash`，与 mod 常量逐位一致） |
| 这两个材质在 G-123 的 `physics` 资源里被**引用**（`+0x154` / `+0xC4`） | **✓ 离线** |
| 该资源的 `userData`（4 B）**定义**在哪份资源 | **⚠ 未定位**（不在该 physics 资源、不在其渲染材质、不在未压缩载荷的 grep 范围里） |
| "材质库是引擎启动时构建的" 这一假设 | **⚠ 未证**（若成立，则这条 B 档需要用引擎侧数据/资源替换以外的手段） |

**下一步（有界、只读）**：把 base/boot 相关包里的 `physics` 资源逐个 `srkit extract` 出来 grep
`hknpMaterialLibrary` / `hknpMaterial`（每份 extract 约 1 s，先扫 base 包，命中即停）；
若全库仍无，则结论改为"运行时构建"，B 档要改走别的等价物（例如**换 unit 的材质绑定**或**给手柄换一个
材质 tag** 的数据侧等价物）。

## 6 三态

| 结论 | 态 |
|---|---|
| 两个 option 都不是改 `StickyComponentData` | **✓ 离线**（一个改战备表 `+0x170`，一个改材质库 userData；源码级证据） |
| `BetterStratagemBounce` = 清 `StratagemInfo +0x170` 的 bit `0x02` | **✓ 离线**（`navigation_patch.lua` 源码 + 字节码字符串互证） |
| 该 mod 在 build 26088801 会拒绝执行（`vanilla_flags` 表 74/148 不匹配） | **✓ 离线**（本 build 逐 kind 比对） |
| `+0x170` 的枚举含义（0/1/2/3 各代表什么） | **⚠ 未证**（抽样像投放类别，无社区命名） |
| `StickyGrenadeHandles` = 改 `sticky_grenade_handle` 材质 userData | **✓ 离线**（源码注释 + 唯一写点） |
| 数据路线（dl_bin）能复刻"粘手柄" | **✗ 不能**（材质库不在任何 dl_bin 里） |
| 资源路线能复刻"粘手柄"（havok 材质 userData） | **⚠ 未针对本条验证**；同族（`physics` 载荷 mass 字段）已有实证 ⇒ 置信度 **中** |
