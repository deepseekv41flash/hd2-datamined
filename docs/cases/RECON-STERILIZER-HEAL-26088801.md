# 只读侦察：Sterilizer-Heal v1.0（Lua 期第三方 mod）→ 本 build 的等价字段

> **一句话**：它改的是 **伤害行**（`generated_damage_settings` 里 TX-41 那条 `DamageInfoType` 记录）的
> **4 组字段**，手段是**运行时内存改写**（FFI + `WriteProcessMemory`），不是改盘上文件。
> 同一改动在本 build 可以走 `dl_bin` 数据路线等价实现，不需要 loader。
> 相关：[WEAPON-FIRE-MODES §5.6.3b](../tables/WEAPON-FIRE-MODES-26088801.md)（喷流 → 伤害行 → 状态槽）。

---

## 1 包的构成

| 项 | 值 |
|---|---|
| 分发包 | `D:\Downloads\Sterilizer-Heal-v1.0.zip`（6,712 B） |
| `manifest.json` | Name `Sterilizer Heal`；要求 **Bingus Shared Loader v15+ / API 1** |
| 载体 | `Addon/9ba626afa44a3aa3.patch_0`（20,096 B，**仅 1 个条目**：`lua` 资源 `0x5AD54954A4197766`） |
| 载荷 | 538 行 Lua，`srkit extract --decoded` 直接出可读源码（无混淆） |
| 机制 | `ffi.cdef` 声明 `ReadProcessMemory / WriteProcessMemory / VirtualProtect / VirtualQuery`；内存里扫 `LDLD` + `DamageSettings`(`0xE0A72CF0`) 组头 → 定位记录数组 → 原地改；**每 300 帧（≈5 s）校验一次，被地图重载回滚就重写** |
| 生效条件 | 客户端内存补丁，随游戏进程存在；**不是**文件 mod，也不会进 `data/game/*.dl_bin` |

## 2 它改了哪几个字段（mod 自述 × 本 build 实测核对）

伤害行是 **76 B 的 `rawDamageInfo`**（mod 的字段图，与我们的 typelib/实测一致）：

| 偏移 | 类型 | 字段 | 本 build（TX-41，type **35**） |
|---:|---|---|---|
| `+0` | u32 | `type` | `35` |
| `+4` / `+8` | i32 | `damage` / `durable` | `1 / 1` |
| `+12..27` | 4×u32 | `ap[4]` | `5,5,5,0` |
| `+28` | u32 | `demo` | `5` |
| `+32` | u32 | `force`（= 硬直/Stagger Force） | `10` |
| `+36` | u32 | `impulse`（= 推力/Push Force） | `5` |
| **`+40`** | u32 | **`element`** | **`5`（Gas）** |
| `+44..+75` | 4×{u32 type, f32 value} | **状态槽 0..3** | `(44, 0.5)` `(46, 0.5)` `(0,0)` `(0,0)` |

**修改内容（mod 的 `build_payload()`，逐项）**：

| 目标 | 旧值（旧 build 1.006.301） | 新值 |
|---|---|---|
| `+44` 槽0 `type` | `43` Gas_MK2 | **`28` Stim_Pistol_Heal** |
| `+48` 槽0 `value` | `0.5` | **`1.0`** |
| `+52` 槽1 `type` | `45` Gas_Confusion_MK2 | **`0`**（None） |
| `+56` 槽1 `value` | `0.5` | `0.0` |
| `+40` `element` | `5` Gas | **`0`** None |
| `+4` / `+8` | `1 / 1` | **`0 / 0`**（去掉那 1 点直伤） |

⇒ **没有碰**：`type` 本身、AP、demo/force/impulse、其它伤害行。
mod 注释明确写了「Nothing else is touched (Dog Breath type 29 keeps its gas)」。

## 3 本 build 的对应位置（实测）

| 项 | 值 |
|---|---|
| 表 | `generated_damage_settings.dl_bin`，组 `0xE0A72CF0`（`DamageSettings`），**661 行 × 76 B**，行起点 = 组 payload + 16 |
| TX-41 的行 | `damage_info_type = 35`（第 **34** 行） |
| 该行现值 | `dmg 1/1 · ap (5,5,5,0) · demo 5 · force 10 · impulse 5 · element 5 · slots (44,0.5)(46,0.5)` |
| 与 mod 旧 build 的 28 号行 | **除 `type` 外逐字段相同** ⇒ 同一条逻辑行，只是 build 重新编号（不是新行） |
| 消费者 | damage 35 **只被 spray 行 19（TX-41）** 引用；弹丸引用 0、爆炸引用 0 ⇒ **单消费者**，改它不会波及别的武器 |
| 相邻行 | type **36** 也是 `(44,0.5)(46,0.5)`（另一把毒气/交互物用）⇒ 只改 35 正好对应 mod 说的"Dog Breath 保留毒气" |

## 4 附带收获：状态效果表已解码（原「⚠ 未定位」项结案）

`generated_status_effect_settings.dl_bin`：

| 项 | 值 |
|---|---|
| 容器 | 2 组：`0xC63E0B22` `StatusEffectSettings`（12,792 B）+ `0xDE8193C0` `StatusEffectTemplates`（1,176 B） |
| 组0 布局 | 组头 16 B + **73 行 × 160 B**（typelib `StatusEffectInfo`，之前算成 175 是因为把末尾名字 blob 摊进了行）+ **1,096 B 名字 blob** |
| 名字对齐 | blob 按**存储顺序**给名字，第 i 条 = 第 i 行（**73 行 ↔ 74 条字符串，最后一条是残渣**） |
| 关键成员 | `+0x000 StatusEffectType`(u32) · `+0x010 StatusEffectShaderVariablePreset` · **`+0x02C DamageInfoType`**（该状态自带的每跳伤害行）… |

**id ↔ 名字（挑与本条线相关的）**：

| id | 名字 | 备注 |
|---:|---|---|
| 5 | `Fire` | FLAM-40 槽0（值 2.0）↔ wiki「Status Fire 强度 **2**」 |
| 6 | `Fire_Panic` | FLAM-40 槽2（值 3.0）↔ wiki「Fire_Panic 强度 **3**」 |
| 7 | `Lava` | |
| **68** | **`FlamerSlowed`** | FLAM-40 槽1（值 1.0）↔ wiki「FlamerSlowed 强度 **1**」 |
| 43 / 44 | `Gas` / `Gas` | 两行同名；TX-41 用的是 **44** |
| 45 / 46 | `Gas_Confusion` / `Gas_Confusion` | TX-41 用的是 **46** |
| 26 / 27 | `Stim Fx` / `Stim Stamina` | |
| **28** | **`Stim Heal`** | |
| **29** | **`Stim Pistol Heal`** | mod 在旧 build 用的就是这个语义（旧编号 28） |
| 30 / 31 | `Stim Combat Drugs` / `Stim Cooldown` | |

⚠ **本 build 把两档治疗分成了 28 / 29**（旧 build 只有 28 = `Stim_Pistol_Heal`）⇒
数据路线改的时候先试 **29（`Stim Pistol Heal`，最贴近 mod 原意）**，不行再试 28。

⇒ 顺带把 [WEAPON-FIRE-MODES §5.6.3b](../tables/WEAPON-FIRE-MODES-26088801.md) 里
"状态 id 68/44/46 未定位"的三条填上了，而且 **名字 × 数值 × wiki 三方互证**。

## 5 本 build 的等价改法（数据路线，不用 loader）

目标：把 TX-41 从"毒气喷流"改成"治疗喷流"（保留喷流本身、射程、外观，只换状态）。

| 字段 | 现值 | 改成 |
|---|---:|---:|
| `+4` damage | 1 | **0** |
| `+8` durable | 1 | **0** |
| `+40` element | 5 (Gas) | **0** (None) |
| `+44` 槽0 type | 44 | **29**（`Stim Pistol Heal`；备选 28） |
| `+48` 槽0 value | 0.5 | **1.0** |
| `+52` 槽1 type | 46 | **0** |
| `+56` 槽1 value | 0.5 | **0.0** |

**工具已扩好：`tools/dmg_row_edit.py`**（`dmg_edit.py` 的超集，一次调用可改任意组合，仍用"未引用行的空状态槽"当校正字）：

```bash
# 看一行
python tools/dmg_row_edit.py show --type 35
# 列可当哈希宿主的行（带 --refs 会标出没人引用的）
python tools/dmg_row_edit.py hosts --refs out/dmgrefs.json
# 一次改完并封包（7 道门禁 + 往返校验）
python tools/dmg_row_edit.py set --type 35 --damage 0 --durable 0 --element 0     --slot 0:29:1.0 --slot 1:0:0 --host-type 240 --out out/heal29.plain --seal
```

门禁（全 PASS 才会写盘）：`G1` 长度不变 · `G2` 差异 ⊆ 声明字段 ∪ 校正字 · `G3` 重算哈希 == 原值 ·
`G4` 字段读回 == 目标 · `G5` 宿主行除校正字外未变 · `G6` 目标行未声明字节未变 ·
`G7` 校正字 8 对齐且落在宿主的**空**槽里。

**哈希宿主怎么选**：必须"任何表都不用"的行。本 build 的 typed 引用面 =
弹丸 `+?` / 爆炸 / **spray 组件 `+0xC8`** / **状态表 `+0x2C`（每个状态的每跳伤害行！）**。
⚠ 过去常用的 `537` 其实被状态 25（`Pure Damage`）引用着，不是真空行；
本轮的宿主选了 **type 240**（4 个空槽、四类引用全 0）。

**已生成的产物 + 已装盘**（`heal29`）：

| 产物 | 大小 / sha256 | 说明 |
|---|---|---|
| `out/spray-5/heal29.dl_bin` | 50,384 B / `91f3655c…` | **已装盘 + ✓ 实机**（槽0 = 29 `Stim Pistol Heal`，值 1.0）：**对着自己脚下喷 → 自己回血** |
| `out/spray-5/heal28.dl_bin` | 50,384 B / `e576217d…` | 备选（槽0 = 28 `Stim Heal`），一条命令换装 |
| 盘上回读 | 哈希 `D03587CCBD2FECFC` 不变 | type 35 = `dmg 0 · dur 0 · elem 0 · slot0 (29,1.0)`；**type 36 原样保留毒气** ✓ |

回滚：`python tools/dlbin_deploy.py restore --file generated_damage_settings.dl_bin`

⚠ 注意 **共享行**：`44/46` 这对槽值是 damage 35 与 36 共用的**语义**，但行是分开的
（每行自己存一份槽），所以改 35 不会影响 36 —— 与其它"共享行"场景不同，这里天然隔离。

## 6 三态

| 结论 | 态 |
|---|---|
| 该 mod 改的是**伤害行的状态槽 + element + damage**（不是 spray 组件、不是状态表） | **✓ 离线**（源码逐行 + 本 build 同形行核对） |
| 手段是运行时内存改写 + 定时校验重写 | **✓ 离线**（`WriteProcessMemory` + 300 帧校验） |
| 本 build 对应行 = damage type **35**（第 34 行），字段值与旧 build 28 号行一致 | **✓ 离线** |
| 状态表解码：73 行 × 160 B + 名字 blob，id→名字全表可查 | **✓ 离线**（Fire/Fire_Panic/FlamerSlowed/Gas/Gas_Confusion/Stim* 三方互证） |
| 本 build 的治疗状态 = **29**（`Stim Pistol Heal`；28 `Stim Heal` 未试） | **✓ 实机**（TX-41 对脚下喷 → 自己回血，说明 29 生效且**能作用于自己**） |
| 用数据路线改完 = 同样的治疗效果 | **✓ 实机**（`heal29` 装盘后当场验证；无需 loader、无需内存补丁） |

## 7 风险与注意

- mod 是**客户端内存补丁**：需要 loader、每次启动重建、地图重载后靠定时器补写；我们走盘上数据**没有这些负担**，但也**改不了运行时才生成的拷贝**（本表是常驻表，不涉及）。
- `value = 1.0` 是"状态强度"而非"治疗量"，实际回血量由状态表 `Stim*` 行决定，**不要**把它当血量倍率。
- 只改 TX-41 的 damage 35 —— **不要**顺手改 36（另一把毒气武器/Dog Breath 一脉）。
