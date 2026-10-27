# `MountComponentData` / `SeatCollectionComponentData` 全解 —— build `26088801`

> **一句话**：两张表都是「哈希图 + 定长行」的老形状，只是**索引装载率 0.50、索引从 +0 开始**（旧文档说的
> "Mount 前面 64 B 前缀"是误读，那是哈希图前 4 个空槽）。`MountComponent` = **5 个 `MountInfo` 槽**，
> 换件**只写 item 的 8 字节**；`SeatCollectionComponent` = `TransitionId` + `Passenger[16]` + 若干 flag
> + `ActiveAimConstraint[22]`，**座位→武器的绑定不在这两张表里**。
> 相关：`D:\mod\docs\VEHICLE-MOUNT-ITEMS.md`（memmod 时代判据与实测矩阵，build 25480438；工作区文档，未入库）·
> [ENTITY-LOCID](ENTITY-LOCID-26088801.md)（实体↔名字）· [POD-RACK](POD-RACK-26088801.md)（实体库 tail 宿主已实机）

---

## 0. 验证状态（三态口径见 [INDEX §7](../../INDEX.md#7-三态标记与自检)）

| 结论 | 状态 | 证据 |
|---|---|---|
| `MountComponentData` `0x3845B1E0` = 5,248 B 哈希图（328 槽）+ 165 × 120 B | **✓ 离线** | typelib 成员 + 整数自洽，`mount_table.py explain` |
| `SeatCollectionComponentData` `0x4AEAFc86` = 1,792 B（112 槽）+ 56 × 424 B | **✓ 离线** | 同上 |
| 索引装载率 0.50、索引从 **+0** 开始（没有 64 B 前缀） | **✓ 离线** | 328 槽 / 164 键、112 槽 / 56 键；Seat 的**第 1 槽**就有一条真键（→ 行 38），按旧读法会丢 |
| `MountComponent` = 5 × `MountInfo`（24 B），槽里 `+12` = `MountSide` 枚举 | **✓ 离线 + 外部名表** | typelib 子类型 id 与 `dl-type-names.json`(filediver) 的 djb2 逐一对上 |
| `MountSide` 数值 = **0 Common / 1 Right / 2 Left** | **✓ 离线（资源名直证）** | EXO-49 槽 0 的件资源名 `_walker_autocannon_left`、side=2；槽 1 `..._right`、side=1 |
| 挂载件 122 件，分桶 16/4/1/11/37/53 | **✓ 离线 + 旧账吻合** | memmod 旧口径 121 件 = 16/4/1/**10**/37/53（只差 build 漂移的 +1，见 §4.3） |
| 五件套全齐 12 件，其中 11 件挂 AI 索敌三件套；唯一"无否决项"= 40 mm 炮塔站 | **✓ 离线 + 旧实测印证** | §4.4；memmod "五件套不充分"实测 |
| `SeatCollectionComponent` 各字段名 | **✓ 离线 + 外部名表** | `TransitionId` / `Passenger` / `ActiveAimConstraint` 均为名表反查所得 |
| `TransitionId` 按载具家族共享（机甲全 10、三种 FRV 33/26/27/28、两坦克 43/44） | **✓ 离线** | §5.2 全表 |
| 座位→武器/挂载的绑定**不在**这两张表里 | **✓ 离线（否定）** + 旧运行时一致 | §6 |
| 换件补丁能装、能读、哈希不变 | **✓ 离线** | G1–G10 全过 + sealed round-trip 逐字节相等 |
| 射界 = **机械层（数据表）+ 相机层（原生）取小** | **✓ 旧实机 + ✓ 离线复核** | 旧：CAM/CAMW/TURW 三轮实测（相机 preset 26 = ±40，写开后露出炮塔 ±105/±180）；本轮：55 张明文表扫不到 `(−40,+40)` 字面值，载具不含 `TargetAimConstraint` 组件 |
| 换件后**实机**可用性 | **✓ 实机（本 build，2026-10-25）** | TD-110 槽 2（原烟幕）换 40 mm 炮塔站：模型出现、可瞄、可开火、玩家可操作；驾驶员位无相机夹制 ⇒ 水平射界 = 件自己的 ±180 |
| 改**机械射界**能否被玩家感知 | **✓ 实机（本 build，2026-10-25）** | TD-220 主炮/同轴 `Turret` yaw ±20 → ±180：游戏内停点明显变大，但仍停住 ⇒ 机械层生效、相机层继续夹（两层取小成立） |

---

## 1. 两表的几何（由 typelib 现算，不写死）

`generated_entities.dl_bin` 是 **`LDLD` 块序列**：每块 `24 B 头(type,ver,payload,…) + payload`，
块与块之间通常有 **4 B 对齐空当**（275 块里 273 处为 4、1 处为 0）；文件里**只有一份**这两种表。
所有偏移相对**块 body**（= 块头 `+28`）。

| 表 | 容器类型 | 块头 | body | 哈希图 | 行数组 | 装载 |
|---|---|---|---|---|---|---|
| `MountComponentData` | `0x3845B1E0` | `0x1CC9C58` | `0x1CC9C74` | **5,248 B = 328 × 16** | **165 × 120 B**（`MountComponent`） | 164 / 328 = 0.50 |
| `SeatCollectionComponentData` | `0x4AEAFc86` | `0x1CDAC88` | `0x1CDACA4` | **1,792 B = 112 × 16** | **56 × 424 B**（`SeatCollectionComponent`） | 56 / 112 = 0.50 |

- 哈希图条目 = `{u64 键(实体键), u32 行号, u32 0}`；空槽全零。`pad` **实测全为 0**（328+112 槽无例外）。
- Mount 的 **165 行里第 164 行没人引用**（其余 164 行与 164 个键一一对应）；Seat 的 56 行**全部**被引用。
- 同样的"2× 槽 / 0.50 装载"也出现在 `Turret`(148 槽/74 键)、`Wieldable`(1030/515)、
  `WeaponWielder`(442/221)、`ProjectileWeapon`(556/278)——这是这套实体库的普遍形状。

```
$ python tools/mount_table.py explain
MountComponentData 0x3845B1E0 @0x1CC9C58 payload=25,048
  哈希图 5,248 B = 328 槽 × 16 B（占用 164）
  行数组 165 × 120 B   行类型 MountComponent
  行内成员（1）: +0x000 120 B MountInfo
SeatCollectionComponentData 0x4AEAFC86 @0x1CDAC88 payload=25,536
  哈希图 1,792 B = 112 槽 × 16 B（占用 56）
  行数组 56 × 424 B   行类型 SeatCollectionComponent
  行内成员（20）: +0x000 TransitionId / +0x008 Passenger[16] / +0x108 u8[8] / +0x110 22 B
                 / +0x128 u32 / +0x12C u32 / +0x130 u8[4] / +0x134 ActiveAimConstraint[22] / +0x18C u8[22]
```

> **更正**：本工作区早前把它读成「Mount = 64 B 前缀 + 324 × 16 索引 + 165 × 120」。
> 64 B 只是哈希图前 4 个**空槽**；行数/槽数取 typelib 成员就没这个问题。
> `Memmod` 时代写的「324×16 @+0、163×120 @+5184」也是同一处误读（163 行是旧 build 的真实行数）。

---

## 2. `MountInfo`（24 B）：一个挂载槽

| 偏移 | 类型 | 字段 | 实测 |
|---:|---|---|---|
| `+0x00` | u64 | **`item`** | 挂载件的实体键；**换件只写这 8 字节** |
| `+0x08` | u32 | `anchor_a` | 挂点 id：**同一挂点跨载具同值**（TD-220 与 TD-110 的主炮位都是 `3809236753`，同轴位都是 `3085546557`） |
| `+0x0C` | `MountSide` | `side` | `0=Common / 1=Right / 2=Left`（§0 的直证）；成对武器必是一 1 一 2（狂战士双锯、浩克双炮、炮艇双火箭巢） |
| `+0x10` | u32 | `anchor_c` | 第二个挂点/预设 id，同样跨载具复用（主炮位 `3413768791`、同轴位 `3037160110`） |
| `+0x14` | u8 | flag | 825 个槽里 **814 个 = 1**；11 个 0 里 10 个是敌 AI 重武器（Vox Engine 4、Factory Strider 5、Supply FRV 1），1 个是 Factory Strider 的空槽 |
| `+0x15` | u8 | flag | 只有 **6 个 = 1**：两坦克主炮、TD-110 三件垂发、M-103 副武器 |
| `+0x16` | 2 B | pad | 全 0 |

**换件配方**：写 `item` 8 字节，`side`/两个 `anchor`/两个 flag **一律不动**——
memmod 时代的 WATCH 实测"写完 node/pad 未变"，与本 build 的槽结构一致（只是字段名现在有了）。

---

## 3. 谁有挂载

| 项 | 数 |
|---|---:|
| 哈希图键 / 行 / 槽容量 | 164 / 165 / 328 |
| 有内容的记录 | **134**（133 条有 item + 1 条只有 anchor） |
| 非空 item 槽 | **235** |
| 槽位填充（槽 0→4） | **133 / 67 / 21 / 12 / 2**（越靠后越少，典型的"按需追加"） |
| 非空槽的 side 分布 | Common **152** / Right **48** / Left **35** |
| owner 分类 | enemy **65** / unit **43** / vehicle **18** / interactable **5** / other **2** |

- 挂载表不只服务载具：**敌人（65 条）比载具（18 条）还多**——浩克的双联炮、炮艇的火箭巢、
  工厂行者的炮塔全走这套表；`unit` 那 43 条是地堡/指挥堡/残骸之类的固定武器位。
- `shuttle_tanker`（行 124）是**只有 anchor、item=0** 的那条：挂点已经 authored，但没装东西。
- 第 165 行（row 164）没有任何键指向它，是**孤儿行**（4 个槽全 0）。

### 3.1 载具挂载记录（19 条，全部槽位）

| 行 | 载具 | 实体键 | 槽 | side | item | 件名 |
|---:|---|---|---:|---|---|---|
| 15 | Scout Strider | `0xF8131632AA867107` | 0 | Common | `0x2A346BF4552997E2` | wep_scoutwalker_hmg |
| 15 | Scout Strider | `0xF8131632AA867107` | 1 | Common | `0xEE00BFE8FF769F70` | twalker_armor_halfcover |
| 17 | EXO-45 Patriot | `0x79E4B3D2DA5E45E3` | 0 | Left | `0x824B7E0C4C879EB5` | _walker_missle_launcher |
| 17 | EXO-45 Patriot | `0x79E4B3D2DA5E45E3` | 1 | Right | `0x08F6089289C83D22` | combat_walker_turret |
| 19 | M-102 Gunner FRV | `0xCC21C7FFD3EBEFB9` | 0 | Common | `0x085C1EDB038EC24E` | MG-206 重机枪（M-102 枪手位） |
| 20 | GROUND ALL-TERRAIN EXTRACTION RIG | `0x423FF97D57AB04F5` | 0 | Common | `0x9872EEB31A5F88FD` | 40 mm 炮塔站 |
| 21 | shuttle_gunship | `0x3F8734AEC15B82AD` | 0 | Common | `0x8365609B35EF6672` | 运输机炮塔 |
| 22 | shuttle_transport | `0x75BE82ED8592A6B3` | 0 | Common | `0x8365609B35EF6672` | 运输机炮塔 |
| 23 | TD-220 Bastion MK XVI | `0x16474112801385B6` | 0 | Left | `0x1FA1F596769225C2` | TD-220 主炮 |
| 23 | TD-220 Bastion MK XVI | `0x16474112801385B6` | 1 | Right | `0x439F9E65C18567DA` | TD-220 同轴机枪 |
| 95 | Reinforced Scout Strider | `0x9076EEED17FCEE35` | 0 | Common | `0x2A346BF4552997E2` | wep_scoutwalker_hmg |
| 95 | Reinforced Scout Strider | `0x9076EEED17FCEE35` | 1 | Common | `0xD3CD6F0CA83BB51E` | 0xD3CD6F0CA83BB51E |
| 95 | Reinforced Scout Strider | `0x9076EEED17FCEE35` | 2 | Common | `0xA8173FBA5DEC35C3` | 0xA8173FBA5DEC35C3 |
| 95 | Reinforced Scout Strider | `0x9076EEED17FCEE35` | 3 | Common | `0x397FB7E4883AF100` | 0x397FB7E4883AF100 |
| 106 | EXO-55 Breakthrough | `0x35DBF54F016F3624` | 0 | Left | `0x65489809A8181B96` | 0x65489809A8181B96 |
| 106 | EXO-55 Breakthrough | `0x35DBF54F016F3624` | 1 | Right | `0xDF51FE8D62F294BE` | 0xDF51FE8D62F294BE |
| 107 | EXO-51 Lumberer | `0x7B2326F6FD9C8069` | 0 | Left | `0x0736BEE2D6328726` | 0x0736BEE2D6328726 |
| 107 | EXO-51 Lumberer | `0x7B2326F6FD9C8069` | 1 | Right | `0x17C5D12D8D5DEE2C` | 0x17C5D12D8D5DEE2C |
| 108 | EXO-49 Emancipator | `0xC2D449ECF7FACAB1` | 0 | Left | `0xE5F64DCC3BFE9DD1` | _walker_autocannon_left |
| 108 | EXO-49 Emancipator | `0xC2D449ECF7FACAB1` | 1 | Right | `0xFF9878576A4C543B` | walker_autocannon_right |
| 119 | M-102 Gunner FRV (duplicate) | `0xE9CD1D0D118886AF` | 0 | Common | `0x085C1EDB038EC24E` | MG-206 重机枪（M-102 枪手位） |
| 120 | M-104 Incinerator FRV | `0x2D85BFE3D8717FE5` | 0 | Right | `0x444880F62CA7EAE8` | B/FLAM-80 Cremator（M-104 喷火位） |
| 120 | M-104 Incinerator FRV | `0x2D85BFE3D8717FE5` | 1 | Common | `0xF99FBDAFEAF3D006` | 0xF99FBDAFEAF3D006 |
| 121 | M-103 Supply FRV | `0x9B2140378640432E` | 0 | Common | `0x4DF41F84668D07FB` | M-103 AI 炮塔 |
| 121 | M-103 Supply FRV | `0x9B2140378640432E` | 1 | Common | `0x9E83637BB077E782` | 0x9E83637BB077E782 |
| 122 | shuttle_gunship | `0x7B0F8449CA9D2DA0` | 0 | Common | `0x8365609B35EF6672` | 运输机炮塔 |
| 123 | shuttle_gunship | `0xEF3A4136B21592CB` | 0 | Common | `0x8365609B35EF6672` | 运输机炮塔 |
| 124 | shuttle_tanker | `0x3F70E3503A3293F9` | 0 | Common | `0x0000000000000000` | (空) |
| 125 | TD-110 Maelstrom | `0xB0C9FAF4AF8903F9` | 0 | Left | `0xD58AE6A04EDB10DE` | TD-110 主炮 |
| 125 | TD-110 Maelstrom | `0xB0C9FAF4AF8903F9` | 1 | Right | `0xC36B5B37C058DBDD` | 0xC36B5B37C058DBDD |
| 125 | TD-110 Maelstrom | `0xB0C9FAF4AF8903F9` | 2 | Left | `0x3A061009AA31E9CB` | 0x3A061009AA31E9CB |
| 125 | TD-110 Maelstrom | `0xB0C9FAF4AF8903F9` | 3 | Left | `0x8AFF7F0793A5BCED` | 0x8AFF7F0793A5BCED |
| 125 | TD-110 Maelstrom | `0xB0C9FAF4AF8903F9` | 4 | Right | `0x8AFF7F0793A5BCED` | 0x8AFF7F0793A5BCED |
| 159 | GROUND ALL-TERRAIN EXTRACTION RIG (duplicate) | `0x0801B6B3C5D12EBC` | 0 | Common | `0x9872EEB31A5F88FD` | 40 mm 炮塔站 |

> 机甲臂件（EXO-45 的两件、EXO-55/EXO-51 各两件）**没有可读资源名**，工具里就是 16 进制键；左/右由 `side` 列给出（§0 已用 `_walker_autocannon_left/right` 直证）。
> row **21 / 122 / 123 是三个实体键共用同一个 `shuttle_gunship` unit 资源**（资源目录里三条都指向
> `content/fac_helldivers/vehicles/shuttle_gunship/shuttle_gunship`），各有一份挂载记录、都装同一个炮塔；
> row 22 `shuttle_transport` 的 unit 落在**共享基包** `f6fb08cc02d24255`（与 hellpod / weapon_rack 同包）。

> **命名**：实体名（百科）与游戏内编号不同——`Bastion Mk XVI` = **TD-220 Bastion MK XVI**，
> `Maelstrom` = **TD-110 Maelstrom**（wiki 双向对上）。
> 件名优先用资源目录后缀名；没有名字的件用 16 进制键（它们本来就没有可读资源名）。

---

## 4. 挂载件盘点（122 个不同 item）

### 4.1 分桶：与 memmod 旧账逐桶吻合

| 桶 | 判据（纯离线） | 本 build | memmod 旧账（121 件） |
|---|---|---:|---:|
| AI 驱动 | `SensorEye`+`Targeting`+`Detector` 三件齐 | **16** | 16 |
| 空壳 | 该键**没有任何组件记录**（悬空 id） | **4** | 4（旧账叫"未知"） |
| 只有炮塔 | `Turret` 有行 ∧ `ProjectileWeapon` 无行 | **1** | 1 |
| 候选 | `ProjectileWeapon` ∧ `Turret` 都有行 | **11** | 10 |
| 只会开火 | `ProjectileWeapon` 有行 ∧ `Turret` 无行 | **37** | 37 |
| 惰性 | 其余 | **53** | 53 |
| 合计 | | **122** | 121 |

**六桶里有五桶逐字相等**，唯一差 1 的"候选"桶正好等于新 build 多出来的那件——
这既是布局读对了的旁证，也说明**装备表和旧 build 几乎没动**。

### 4.2 五件套 + 两条否决项（离线判定）

| # | 判据 | 看哪张表 | 不满足的后果 |
|---|---|---|---|
| 1 | 几何 | 资源目录里该键的 `mesh` 的 `gpu_size` | 0 网格 = 无模型；`gpu_size=0` 但有 mesh = 流式几何（要包驻留） |
| 2 | 包驻留 | 该键的资源出现在哪些 toc 包 | 没驻留 → 紫 `?` |
| 3 | 炮塔 | `TurretComponentData` 有行（限位偏移见 §4.6） | 固定指向，不能瞄 |
| 4 | 玩家可操作 | `Wieldable` **和** `WeaponWielder` 都有行（必要不充分） | 不能瞄不能打 |
| 5 | 开火 | `ProjectileWeaponComponentData` 有行 | 只能瞄不能打 |
| 否决 | 阵营 | `FactionComponentData` 行 `+0` 位掩码 ∈ {4,8} | 敌兵登车，运输机当场把槽打空（memmod 实测） |
| 否决 | AI 大脑 | 上面三件套齐 | 它自己索敌开火，玩家抢不到 |

几何三分类（与 memmod 文档 §3 同一口径）：**内联 101 / 流式 17 / 无网格 4**。
122 件里 `Turret` 27、`ProjectileWeapon` 61、`Wieldable` 91、`WeaponWielder` **15**。

### 4.3 交叉验证：四条旧实测逐条对上

| 旧结论（25480438，实机） | 本 build 离线读数 | 判定 |
|---|---|---|
| 40 mm 站 / 孤儿站可用，因为同在**共享基包** `f6fb08cc02d24255` | `0x9872EEB31A5F88FD` 的资源只出现在 `f6fb08cc02d24255` | ✓ |
| 运输机炮塔 mesh ≈ 251 KB | `0x8365609B35EF6672` mesh `gpu_size = 251,050` | ✓ |
| TD-220 同轴机枪**没有几何**（骨骼引用型） | `0x439F9E65C18567DA` mesh 3 条但 `gpu_size` 全 0 | ✓ |
| TD-110 主炮 1.84 MB | `0xD58AE6A04EDB10DE` mesh `gpu_size = 1,836,154` | ✓ |

### 4.4 五件套全齐的 12 件——11 件自带 AI 大脑

| 件 | 名称 | 阵营否决 | AI 大脑 | 几何 | 包 |
|---|---|---|---|---|---|
| `0x9872EEB31A5F88FD` | **40 mm 炮塔站** | — | — | 流式 | **共享基包** |
| `0x8365609B35EF6672` | 运输机炮塔 | — | ✓ | 内联 | 4 包 |
| `0x4DF41F84668D07FB` | M-103 AI 炮塔 | — | ✓ | 内联 | 2 包 |
| `0x356DE4A7808EF3E3` / `0xF2881F5807348116` / `0x611BA777783B08A2` | Vox Engine ×3 | ✓ | ✓ | 内联 | 2 包 |
| `0x3AAFBA89B53B0F63` / `0x390E6B3D2F26BD70` / `0x843D18D4B5512B63` | 工厂行者件 ×3 | ✓ | ✓ | 内联 | 2 包 |
| `0x5D142C3A73EBC634` | 车顶火箭炮塔 | ✓ | ✓ | 内联 | 1 包 |
| `0xCD28A27A79BE53D5` | 地堡 HMG | ✓ | ✓ | 内联 | 2 包 |
| `0x9926876B2375A1BB` | 自动化军团自动炮 | ✓ | ✓ | 内联 | 4 包 |

⇒ **"五件套齐"并不等于"玩家能用"**：11/12 都自带 AI 索敌，10/12 还是敌阵营。
唯一同时满足五件套 + 两条否决项的，就是 **40 mm 炮塔站**——正好是 memmod 实测"可用池"里那两件之一
（另一件孤儿站 `0xC25DC40EDE0E2D16` 没有被任何载具 vanilla 引用，所以不在 122 件里）。

### 4.5 「候选」11 件里 10 件缺 `WeaponWielder`

| 件 | 名称 | WeaponWielder | 说明 |
|---|---|---|---|
| `0x9872EEB31A5F88FD` | 40 mm 炮塔站 | **有** | 唯一"玩家位"件 |
| `0x1FA1F596769225C2` | TD-220 主炮 | 无 | 车长炮：由座位/相机侧授权 |
| `0xD58AE6A04EDB10DE` | TD-110 主炮 | 无 | 同上 |
| `0x439F9E65C18567DA` | TD-220 同轴机枪 | 无 | 同上（且无几何） |
| `0x8FB47DD28B398CF7` / `0x49674794A165EDA8` / `0x9AB036439F74C115` / `0x8372619B2702D743` / `0x2D62A25F36C08F33` | 敌人重武器 ×5 | 无 | 敌人自持 |
| `0x051C3196A0192D33` / `0x767977BD472A62DA` | Caustic Spewer ×2 | 无 | 敌人自持 |

⇒ **换件时如果目标是这 10 件之一，预期是"有模型/能打但不能由玩家操作"**；要"能操作"就得选
带 `WeaponWielder` 的件（本 build 的挂载池里只有 40 mm 炮塔站）。
这也解释了旧账里"运输机炮塔两表都有、依然不能操作"——它的 `WeaponWielder` 记录与 40 mm 站不同，
且带 AI 大脑。

### 4.6 射界：`TurretComponentData` 四项限位（本 build 的偏移是新的）

判据 3（"能瞄"）用的是**件自己的** `TurretComponentData` 行（`0x1EBA7593`，148 槽 / 74 键 /
75 行 × 76 B）。本 build 的四项限位在：**`+0x14` pitch_min / `+0x18` pitch_max /
`+0x1C` yaw_min / `+0x20` yaw_max**（f32）。

> ⚠ **与旧文档的偏移不同**：memmod 时代记的是 `+0/+4/+8/+12`；本 build 的那四个位置是小浮点
> （`+0`≈9.3e-14、`+4`≈3.9e-19），限位整体后移到了 `+0x14…+0x20`。数值本身仍与旧实测逐条吻合。

| 件 | pitch（min…max） | yaw（min…max） | 旧文档记的 | 判定 |
|---|---|---|---|---|
| `0x9872EEB31A5F88FD` 40 mm 炮塔站 | −13 … 60 | **−180 … +180** | "40 mm 站 ±180" | ✓ |
| `0xC25DC40EDE0E2D16` 孤儿站 | −20 … 80 | **−180 … +180** | "孤儿站 ±180" | ✓ |
| `0x439F9E65C18567DA` TD-220 同轴机枪 | −3 … 25 | **−20 … +20** | "TD-220 同轴机枪 ±20" | ✓ |
| `0x1FA1F596769225C2` TD-220 主炮 | −3 … 25 | −20 … +20 | — | — |
| `0x8365609B35EF6672` 运输机炮塔 | 0 … 90 | **−105 … +105** | "炮塔自己的 ±105" | ✓ |

判据自证：75 行**全部**满足 `pitch_min ≤ pitch_max`、`yaw_min ≤ yaw_max`、落在 ±180/±360 内；
yaw 对最常见的正是 `(-180, 180)`（52 行，全向炮塔）。

⇒ 机动判据见 §4.7（**这一层只是机械限位，玩家实际能转多少还要过相机那关**）。

### 4.7 两层射界：机械限位（数据表）＋ 相机夹制（原生，不在数据表）

玩家手里"能转多少"是**两层取小**，旧线两轮实测已把这两层分开：

| 层 | 在哪 | 数值（旧 build 实测） | 证据 |
|---|---|---|---|
| ① **炮手相机 preset**（先夹） | **原生** `game.dll+0x32F9990`，0x90 B 记录按 preset id 编号；限位在 `+0x4C..+0x58` | **preset 26 = 坦克炮手：yaw ±40、pitch −15…+25**；邻居 25/27 都是 ±180；**前 40 个 preset 里 35 个是整圈** ⇒ ±40 是特意设的，不是系统天花板 | CAM 只读打印；CAMW 把 `+0x54/+0x58` 从 −40/+40 写到 ±180（8 B），**用户实测能转到 ±105 才停** = 相机确为第一层 |
| ② **炮塔机械限位**（后夹） | `TurretComponentData` 行（§4.6） | 运输机炮塔 ±105；40 mm 站/孤儿站 ±180；TD-220 同轴 ±20 | TURW 把炮塔 yaw 写到 ±180，**用户实测能转 ±180** |

旧记录出处（工作区文档，未入库）：`D:\mod\docs\VEHICLE-AI-TURRET-TAKEOVER.md` §8（CAM/CAMW/TURW 三 pass
与用户实测）、`D:\mod\docs\VEHICLE-MOUNT-ITEMS.md` §7（0.7.0 `CAM` pass 的落盘位置）。

**本 build 的离线复核（本轮新增）**：

- 把本工作区 **54 份 `generated_*.dl_bin` 明文**逐字节扫 `f32(−40.0, +40.0)` 组合 —— **0 命中**；
  扫 `f32(−15, +25, −40, +40)` 四连 —— 也是 0。⇒ 相机限位**不以字面值存在数据表里**（与"原生表"一致）。
- 实体组件表里唯一名字带 aim 的组件 `TargetAimConstraintComponentData`（`0xC3431570`，
  104 B × 229 行）**与载具/座位不相交**：19 个有挂载记录的载具键 ∩ 它的 229 个键 = **0**，
  56 个座位所有者 ∩ 它的键 = **0**。它的行是 `{u32, 3 × AimConstraintInfo(28 B), u32×3, u8}`，
  像是"AI/瞄准约束"而不是载具相机夹制。
- 名表里已有 `CameraTemplateType` 枚举（`LandVehicle` / `FRVTurret` / `MannedTurret` /
  `RegularTurret` / `Cars` / `Emplacement`…），说明相机是**模板化**的；但模板参数本身仍未在数据文件里找到。
- **Lua 面能碰到相机，但碰不到 preset**：本 build 存在第三方**纯 Lua boot 覆盖**的第一人称 mod
  （替换 `boot` 资源 `0xF476DF93691895FA`，无需 loader）。它每帧只写**单台相机的 `local_position`**
  （`Camera.set_local_position` + `World.update_unit`，`render` 里写、`update` 开头还原），
  **从不碰旋转**；Lua API 表里也没有"相机 preset / 角度上限"这一类接口。
  ⇒ Lua 能当**只读测量探针**（读 `Camera.local_rotation`/`world_pose`），但改不了这一层；
  真要改只能用 `set_local_rotation` 每帧加偏移（等价性未证）或运行时定位原生表。
- **为什么在二进制里也搜不到**：本 build 的 `data/game/game.dll`（49,075,800 B）`.text` 段熵 **8.00**
  （加密/压缩），`bin/runtime.dll`（64 MB）段名直接是 `packer0…packer42`（加壳）⇒
  **磁盘字节 ≠ 运行时字节**（旧线也记过同一现象）。所以"在 game.dll 里按 ±40/±180 搜表"必然落空；
  相机表只能像旧 build 的 `CAM` 那样**运行时读**（旧址 `game.dll+0x32F9990`，新 build 的 RVA 未定位）。

⇒ **两条结论**：

1. **数据文件路线只能改第 ② 层（机械限位）**。第 ① 层（相机）在本 build 仍是原生表；
   旧 build 已证明它能写（CAMW，8 B，页本来就可写），但那属于内存路线，不是 dl_bin。
2. **补丁 A 的实机判据要按"取小"来写**：TD-220 槽 1 原装同轴机枪 yaw = ±20；
   换成 40 mm 站后机械层 = ±180。**若该座位用的相机 preset 是 26（±40），实际能转应从 ±20 变成 ±40**，
   而不是 ±180。所以判读点是"**能否越过 20°、停在哪**"：停在 ~±40 = 换件生效（相机仍夹）；
   若真能到 ±180，说明该座位用的不是 ±40 那档相机。

#### 4.7.1 准星与装填：**座位侧能力，不是武器字段**（2026-10-25，✓ 实机分离）

同一个 40 mm 炮塔站（`0x9872EEB31A5F88FD`，台账数据一字不改）只换座位，结果完全相反：

| 座位 | 准星 | 按 R 装填 | 其它 |
|---|---|---|---|
| TD-110 **驾驶员位**（槽 2，原烟幕） | ✗ 无 | ✗ 被拒（备弹 5、时长 4.0 s 都在也没用） | 开火/瞄准正常 |
| TD-110 **主炮位**（槽 0，炮手；原主炮） | **✓ 有** | **✓ 有**（容量压到 10 后打空能换弹） | 该位另有武器干扰 |
| **M-102 Gunner FRV 枪手位**（单武器） | **✓ 有** | **✓ 有** | 模型正常、转动正常（v5，2026-10-25） |

⇒ **"画不画准星 / 收不收 R" 由座位（相机 + wielder 通道）决定**，武器行只提供素材：
`crosshair_type`（`WeaponData +0x194`，样式）、`+0x88/+0x8C/+0x94`（弹匣 / 起始备匣 / 上限）、
`WeaponReload +0x38`（装填时长）。

武器侧唯一"只有站点才有"的字段 `WeaponData +0x190`（40 mm 站与孤儿站 = 1，其余 371 行 = 0）
**✗ 已被否证**与准星有关：改成 0 后驾驶员位仍无准星。
完整普查、枚举成员表与补丁台账见
[LOCKON-TARGETING §11](LOCKON-TARGETING-26088801.md) 与
[WEAPON-AMMO-RESERVE §8](WEAPON-AMMO-RESERVE-26088801.md)。

⇒ **结项**：准星与装填都是**座位侧**能力；武器行只给素材（样式 `crosshair_type`、弹药三字段、
`WeaponReload` 的时长）。数据层做不到"给某座位加准星/装填"，能改的只有样式与弹药参数。
单武器座位的干净验证用 M-102 Gunner FRV 枪手位（v5：两条挂载记录行 19 与 119 的槽 0 一起换）。

> ⚠ **Turret 行偏移跨 build 漂移过，不能照抄**：旧 build 的 TURW 是写 `+8/+12` 生效的
> （✓ 实机，25480438），而本 build 的 `+8/+12` 是另一对值（运输机炮塔 120/120），±105 在 `+0x1C/+0x20`。
> 旧文档当年还专门否证过"第三方写的 `+0x1C/+0x20` 不是这张表的布局"——那在旧 build 是对的，
> **在本 build 反而对上了**。这类字段位置每 build 必须重测。

---

## 5. `SeatCollectionComponent`（424 B）

| 偏移 | 类型 | 字段 | 实测 |
|---:|---|---|---|
| `+0x000` | `TransitionId` | 上车/下车过渡 | 1…44；**按载具家族共享**（§5.2） |
| `+0x008` | `Passenger[16]`（16 × 16 B） | `{u32, u32, u64}` | 只有 Scout Strider 的 `p0` 非零，u64 = `Trooper` 实体（它的 AI 驾驶员） |
| `+0x108` | u8[8] | flag | 逐行取值不同（见 §5.3），`[0]` 恒 0、`[1][2][3]` 多为 1 |
| `+0x110` | 22 B | flag 数组 | typelib 报 `+0x111`，但首字节随行变化 ⇒ 实际从 `+0x110` 起 |
| `+0x128` | u32 | 未知 | 只有两行非零（`0x02C4C01F`，两个"Expandable Cover"实体） |
| `+0x12C` | u32 | 未知 | 同上（`0xEB44D687`） |
| `+0x130` | u8[4] | flag | 常见 `1000` / `1001` / `1010` |
| `+0x134` | `ActiveAimConstraint[22]`（22 × u32） | 瞄准约束 | 只有 4 行非零：**三种 FRV + 重复行**，且 4 个值完全相同 |
| `+0x18C` | u8[22] | flag 数组 | 常见全 0 或全 1，与非零 aim 行互斥 |

### 5.1 两种"给玩家一把枪"的数据形态

| 形态 | 例子 | 武器在哪 | 座位在哪 |
|---|---|---|---|
| **载具**（挂载表） | TD-110/TD-220/EXO/FRV | `MountComponentData` 的槽 | `SeatCollectionComponentData` |
| **炮台/工事**（自带武器） | HMG Emplacement / 反坦克炮台 / 榴弹炮台 / 机械族炮台 | **实体自己的** `Turret`+`ProjectileWeapon`+`Wieldable`+`WeaponWielder` | 同一个实体的 `SeatCollection` |

⇒ 工事**没有**挂载记录（56 个座位所有者里 40 个没有挂载行），因为"那把枪"就是实体本身；
载具才需要挂载表来声明"车体上插了哪些件"。

### 5.2 `TransitionId` 家族

| TransitionId | 使用者 |
|---:|---|
| 10 | EXO-45 / EXO-49 / EXO-51 / EXO-55（四台机甲同一个上下机过渡） |
| 33 / 26 / 27 / 28 | FRV 底盘 / M-102 Gunner / M-103 Supply / M-104 Incinerator |
| 43 / 44 | TD-220 Bastion / TD-110 Maelstrom |
| 20 | Scout Strider；5 = Cargo Truck；40 = shuttle_gunship |
| 32 | HMG Emplacement ×6（含 4 个未命名 variant） |
| 25 | Grenadier Battlement / Expandable Cover |
| 13 / 14 | cyborg_emplacement_hmg / _mg |
| 24 | cyborg_dropoff_01 ×4 |
| 30 / 35 / 39 / 34 … | 各类可交互（ICBM 锁、电站、补给站…） |

这说明 `TransitionId` 是**上下具/上下炮台的动画过渡**，同一套过渡被同家族共用——
它不是"座位布局 id"，同一家族里座位数可以不同（FRV 三型一个车体，过渡各不相同）。

### 5.3 56 行全表

| 行 | 实体 | kind | TransitionId | 8 bool | ActiveAimConstraint | Passenger |
|---:|---|---|---:|---|---|---|
| 0 | `0xAE1F84C3A7EB3B74` | interactable | 41 | 01110000 | — | — |
| 1 | `0x574D028263CB630A` | interactable | 4 | 01111000 | — | — |
| 2 | `0xB9AAAE21AD68B51C` | interactable | 4 | 01111000 | — | — |
| 3 | cyborg_emplacement_hmg | interactable | 13 | 00111000 | — | — |
| 4 | cyborg_emplacement_mg | interactable | 14 | 00111000 | — | — |
| 5 | **Scout Strider** | vehicle | 20 | 01011000 | — | **p0 = Trooper** |
| 6 | `0x4821CF7AAFEA1419` | interactable | 39 | 01101000 | — | — |
| 7 | EXO-45 Patriot | vehicle | 10 | 01111001 | — | — |
| 8 | **M-102 Gunner FRV** | vehicle | 26 | 01111101 | **有** | — |
| 9 | GROUND ALL-TERRAIN EXTRACTION RIG | vehicle | 33 | 01111001 | — | — |
| 10 | **TD-220 Bastion MK XVI** | vehicle | 43 | 01111001 | — | — |
| 11 | `0x2DE164C0302AB49B` | interactable | 42 | 01111010 | — | — |
| 12 | Cargo Truck | vehicle | 5 | 01111001 | — | — |
| 13 | `0x925158186B8FD952` | interactable | 37 | 01110000 | — | — |
| 14 | icbm_lock | interactable | 30 | 01110000 | — | — |
| 15 | `0xFF660C3FD24531A0` | interactable | 34 | 01110010 | — | — |
| 16 | `0x91209E5AF7A9660B` | interactable | 34 | 01110010 | — | — |
| 17 | `0xE05784031312C43F` | interactable | 35 | 01110000 | — | — |
| 18 | `0x8A50B60B22186B9B` | interactable | 35 | 01110000 | — | — |
| 19 | `0x6DC9F65AF69783BD` | interactable | 35 | 01110000 | — | — |
| 20 | `0xE9929CB8800E1C8F` | interactable | 35 | 01110000 | — | — |
| 21 | power_station | interactable | 36 | 01111000 | — | — |
| 22 | `0x5D96918BA0FF1CD5` | interactable | 29 | 01110000 | — | — |
| 23 | `0x0E88F182E83A4275` | interactable | 24 | 01101000 | — | — |
| 24 | `0x4C182656063F121A` | interactable | 24 | 01101000 | — | — |
| 25 | `0x424036E9F7DE9A1E` | interactable | 11 | 01110000 | — | — |
| 26 | `0x317B2C0E4D10E293` | interactable | 24 | 01101000 | — | — |
| 27 | `0xB50DBC63A02C0D3B` | interactable | 24 | 01101000 | — | — |
| 28 | `0x1D72EBD1A6916E67` | interactable | 3 | 01110000 | — | — |
| 29 | `0xA5E5C49757629354` | interactable | 7 | 01110000 | — | — |
| 30 | `0xBBBBE501BEDE8603` | interactable | 4 | 01111000 | — | — |
| 31 | `0xFCA5EDCC43A6E847` | interactable | 4 | 01111000 | — | — |
| 32 | `0x81A827B78F077BEC` | interactable | 4 | 01111000 | — | — |
| 33 | Anti-Tank Emplacement | interactable | 1 | 00001000 | — | — |
| 34 | Expandable Cover | interactable | 25 | 00101000 | — | — |
| 35 | Grenadier Battlement | interactable | 25 | 00101000 | — | — |
| 36 | `0x6D5E37A8AD1FAC2B` | interactable | 39 | 01101000 | — | — |
| 37 | HMG Emplacement | interactable | 32 | 00011000 | — | — |
| 38 | HMG Emplacement | interactable | 32 | 00011000 | — | — |
| 39 | `0xE0E257B37526DBE3` | interactable | 32 | 00111000 | — | — |
| 40 | `0x1980D92B619FF5FE` | interactable | 32 | 00111000 | — | — |
| 41 | `0x24510E7B16B5F7A5` | interactable | 32 | 00111000 | — | — |
| 42 | `0xEB91B90EEC279745` | interactable | 32 | 00111000 | — | — |
| 43 | EXO-55 Breakthrough | vehicle | 10 | 01111001 | — | — |
| 44 | EXO-51 Lumberer | vehicle | 10 | 01111001 | — | — |
| 45 | EXO-49 Emancipator | vehicle | 10 | 01111001 | — | — |
| 46 | M-102 Gunner FRV (duplicate) | vehicle | 26 | 01111101 | **有** | — |
| 47 | **M-104 Incinerator FRV** | vehicle | 28 | 01111101 | **有** | — |
| 48 | **M-103 Supply FRV** | vehicle | 27 | 01111101 | **有** | — |
| 49 | shuttle_gunship | vehicle | 40 | 01100010 | — | — |
| 50 | **TD-110 Maelstrom** | vehicle | 44 | 01111001 | — | — |
| 51 | `0xB09E60B74B484FA9` | interactable | 8 | 01110000 | — | — |
| 52 | `0xB6FE4BD12C248286` | interactable | 34 | 01110010 | — | — |
| 53 | GROUND ALL-TERRAIN EXTRACTION RIG (duplicate) | vehicle | 33 | 01111001 | — | — |
| 54 | `0xD4A349DAAE850283` | interactable | 30 | 01110000 | — | — |
| 55 | `0x95D717E4AA9ED443` | interactable | 8 | 01110000 | — | — |

（第 38 行的键 `0xA970CBA66FBEAA11` 就是哈希图**第 1 槽**那条——索引从 +0 开始的直接证据：
按旧"64 B 前缀"读法会把它漏掉，全表就只剩 55 条。）

---

## 6. 座位 ↔ 武器：**不在这两张表里**

三条离线证据：

1. `SeatCollectionComponent` 里没有任何指向挂载行/挂载槽的字段：只有过渡 id、16 个 `Passenger`、
   两组 flag、22 条 `ActiveAimConstraint`、两个未知 u32。**22 条 aim constraint ≠ 5 个挂载槽**。
2. `MountInfo` 里也没有座位字段：`item` + 两个挂点 id + `MountSide` + 2 个 flag。
3. 工事（HMG/反坦克/榴弹炮台）**有座位、没挂载**，说明"坐上去用哪把枪"是实体/座位侧的事，
   不是挂载表的事。

与旧运行时结论一致：memmod 时代发现"同一件 item 在驾驶位完全无控制、在炮手位能短暂瞄+打，
几秒后控制被收回"，并把它归到"座位侧绑定 / 实体自带状态机"。本 build 的证据表明**那层绑定确实不在
数据表里**——`TransitionId` 只是上下具动画，真正把"座位→相机→wielder"连起来的是代码侧
（旧线索：`game.dll+0x32F9990` 的相机预设表，preset 26 = 坦克炮手）。

---

## 7. 换件配方（纯数据文件、保内容哈希）

### 7.1 工具

```bash
python tools/mount_table.py list                       # 134 条记录 / 载具 19 条
python tools/mount_table.py show --entity "TD-220"     # 槽位解码 + 五件套判据 + 射界
python tools/mount_table.py seats                      # SeatCollection 56 行
python tools/mount_table.py find 40mm                  # 按名字找件
python tools/mount_table.py explain                    # 打印几何推导
python tools/mount_table.py swap --entity 0x16474112801385B6 --slot 1 \
    --item 0x9872EEB31A5F88FD --out out/x.plain        # 换件（保哈希）
python tools/mount_table.py verify out/x.plain         # 复核：哈希/容器/几何/只变了哪个槽
# swap 还会把"新旧射界"打出来（补丁 A：原 ±20 → 新 ±180），这是进游戏最硬的判据
```

`swap` 的物理动作只有一步：**把 `MountInfo.item` 的 8 字节写成目标件**。
哈希宿主用与 `entity_field_set.py` / `pod_rack_swap.py` 同一套**末块 payload 追加**法
（实体库上已由 POD-RACK 实机验证过）：

```
末块 payload += pad+8 ; 文件尾追加 pad+8 个零 ; Murmur64A 校正字落在 len+pad（8 对齐）
```

### 7.2 门禁 G1–G10（全部通过才落盘）

| 门 | 内容 |
|---|---|
| G1 | 长度 = 原长 + pad + 8 |
| G2 | 差异 ⊆ 目标 8 B ∪ 末块 payload 尺寸字段 ∪ 校正字 |
| G3 | 重算 `Murmur64A` == 输入哈希（vanilla = `0x8E49771B181FFAA1`） |
| G4 | item 读回 == 目标 |
| G5 | 同记录其它 4 个槽逐字节未变 |
| G6 | 容器重解析自洽（275 块链首尾相接） |
| G7 | 旧值 == `--expect-old`（给了才查） |
| G8 | 校正字 8 对齐且不与目标重叠 |
| G9 | 追加区除校正字外全 0 |
| G10 | 重新解析全表：只有目标槽变了（全表 236 个非空槽逐槽比对） |

### 7.3 两个工件（都已跑完门禁）

| 工件 | 动作 | 明文 sha256（前 16） | sealed |
|---|---|---|---|
| `out/mount-swap/generated_entities.td220-slot1-40mm.dl_bin` | TD-220 槽 1：`TD-220 同轴机枪` → **40 mm 炮塔站**（换件） | `a47404cc8f293f82` | 47,259,456 B，sha256 `364a521bf166f0f5…` |
| `out/mount-swap/generated_entities.td220-slot2-add-40mm.dl_bin` | TD-220 槽 2（空）→ **40 mm 炮塔站**（加槽） | `f8a1474c935c2965` | 47,259,456 B，sha256 `203d552c9e7a1673…` |

```
$ python tools/mount_table.py verify out/mount-swap/td220-slot1-40mm.plain
  PASS  哈希 == vanilla  0x8E49771B181FFAA1
  PASS  容器链自洽  275 块
  PASS  Mount 几何  328 槽 / 165 行 × 120
  PASS  Seat 几何  112 槽 / 56 行 × 424
  变化的槽: [(23, 1, '0x439F9E65C18567DA', '0x9872EEB31A5F88FD')]
  PASS  变化的槽 ≤ 1
```

封装与回读（sealed → unseal == 明文，逐字节）：

```bash
python tools/dlbin_seal.py seal-key out/mount-swap/td220-slot1-40mm.plain \
    --key refs/dlbin/keys/recipient.pk --out out/mount-swap/generated_entities.td220-slot1-40mm.dl_bin
python tools/dlbin_seal.py open-key out/mount-swap/generated_entities.td220-slot1-40mm.dl_bin \
    --key refs/dlbin/keys/recipient.sk --out out/mount-swap/_roundtrip.plain   # → 与明文 equal: True
```

### 7.4 部署 / 回滚（**本会话未执行**；要先关游戏）

```bash
python tools/dlbin_deploy.py backup  --file generated_entities.dl_bin
python tools/dlbin_deploy.py install --file generated_entities.dl_bin \
    --sealed "D:/mod/out/mount-swap/generated_entities.td220-slot1-40mm.dl_bin"
# 回滚
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin
```

### 7.5 进游戏怎么判（三个观察点）

1. **模型**：召 TD-220 看槽 1 位置（同轴机枪位）是不是变成 40 mm 站的炮塔外形
   —— 40 mm 站在共享基包，任务里天然驻留，不该出紫 `?`。
2. **操作**：坐进车长位，看这门 40 mm 能不能瞄、能不能打；**最硬的判据是射界**——
   机械层从 **±20°** 变成 **±180°**（§4.6），但玩家实际能转多少还要过**相机 preset** 那关（§4.7）：
   - 若该座位相机是 preset 26（±40）⇒ 预期从 **±20 变成 ±40 就停**（越过 20° 即证明换件生效）；
   - 若能转到 **±180** ⇒ 该座位不是 ±40 那档相机，机械层完全放开。
   两种情况都能证明"射界取件自己的 `Turret` 行"（同时否证"射界取宿主车的"）。
3. **槽 2 工件**：如果模型出现但**操作不了**，说明"空槽加件"只补了模型、没有座位授权——
   这正好把 §6 的结论钉死（座位→武器的绑定在代码侧）。

---

### 7.6 换**跨包**件：包驻留配方（**✓ 实机，2026-10-25**）

换进来的件如果**不在本车/本机甲自己的 toc 包里**，引擎只拿到 item id、找不到网格 ⇒ 画**紫色问号**。
数据路线（不用 runtime、不用携带源载具）的解法是改**战备行的 `+0xA8`**（声明"要加载哪个包"）：

| 规则 | 依据 | 态 |
|---|---|---|
| 一辆载具自己的战备行，只要玩家**带了这件战备**，它的 **live 行** `+0xA8` 会在关卡加载时被读 | `EXO45-ARM-SWAP` B 组：`row 143` 生效、`row 88` 无效 | ✓ 实机 |
| **一条战备只给 1 个口**：同一战备的重复行 **不算**第二个口 | 同上（`+0x106` 分类位/`+0x150` 哨兵显示 row 88 是遗留记录） | ✓ 实机 |
| 账号常驻行可白拿：`Reinforce` 行 57/138、`SOS Beacon` 行 59 | [LIMITED-CROSS-PACKAGE-LOADING §6.6.7](../engine/LIMITED-CROSS-PACKAGE-LOADING-26088801.md) R3/R9 | ✓ 实机 |
| **`+0xA8` 是「替换」**：写谁就只加载谁，本机甲自己的内容包会被挤掉 | 2026-10-25：爱国者行改填解放者包后，依赖爱国者包的左臂紫问号（[EXO-ARM-VARIANTS §9](EXO-ARM-VARIANTS-26088801.md)） | **✗ 否证（原"增量"结论作废）** |
| `+0xF8` 对"不授予武器"的战备无效（机甲用不了） | 同文 R1 | ✗ 否证 |

⇒ **N 件不同包的换装 = N 个口**：1 个来自载具自己的 live 行，其余从常驻行借。

> ⚠ **操作警示（2026-10-25 实机）**：换进来的件如果**包没驻留**会显示**紫色问号**；
> 在这种状态下**按开火键会崩游戏**（单次观察，见 [EXO-ARM-VARIANTS §10.2](../tables/EXO-ARM-VARIANTS-26088801.md)）。
> 召唤后**先确认没有紫问号再开火**；紫问号 = 去补 `+0xA8` 的包声明，别靠开火试探。
> 另注：**本体**（机甲/载具自己）能渲染**不代表**它的内容包已驻留——机甲本体网格在四台机甲包里各有一份副本（§9.3 同源证据）。
完整案例（EXO-45 换盾/加农炮，三种变体的判读）见
[EXO45-ARM-SWAP](../cases/EXO45-ARM-SWAP-26088801.md)。

## 8. 能力判定

| 能力 | 判定 | 依据 |
|---|---|---|
| **给载具换一件武器**（槽里已有件 → 换另一件） | **A · dl_bin 等价** | 与 memmod 时代写的是同一处 8 字节；本 build 表结构不变、哈希可保、实体库 tail 宿主已实机 |
| **给空槽加一件武器** | **A（数据层）/ ⚠ 运行时要看座位** | 模型该出现；能不能操作取决于代码侧授权（§6） |
| 换件后"能瞄/能打" | 有条件的 A | 件必须自带 `Turret` + `ProjectileWeapon`（§4.2 判据 3/5） |
| 改**机械射界**（件的 `Turret` 行 yaw/pitch） | **A · dl_bin 等价** | 本 build 偏移 `+0x14/+0x18/+0x1C/+0x20`（§4.6）；写点与旧 build 同一张表 |
| 改**相机射界**（玩家实际能转多少的上限） | **不在数据层** | 相机 preset 表是原生 `game.dll+0x32F9990`（0x90 B/记录，preset 26 = ±40）；本 build 55 张明文表扫不到该值；旧 build 只能内存写（CAMW） |
| 换件后"玩家能操作" | 有条件的 A | 件必须带 `Wieldable` + `WeaponWielder`（本 build 挂载池里只有 40 mm 站满足） |
| 换件后"模型正常" | 有条件的 A | 件包必须驻留（共享基包 / 本车包 / 带车同行）；敌阵营件还要改 `Faction`（本工具不做） |
| 改变"哪个座位控制哪个槽" | **不在数据层** | §6 三条证据；memmod 也只能靠运行时 `Behaviour`/wielder 干预 |

> ⚠ **槽类型决定判据**：上表"必须 `Turret` / 必须 `Wielder`"只适用于**炮塔槽**（AI 炮塔、机械限位）；
> **M-102 枪手位**这种"玩家操作、座位给瞄准"的槽，原生件就没有 `Turret` / `WeaponWielder` 也能用，
> 见 §11。

---

## 9. 未解项

1. `+0x14` / `+0x15` 两个 flag 的确切语义（0x14 有 11 个 0、全在敌 AI 重武器；0x15 只有 6 个 1，
   全是"主炮/垂发/副武器"级）。离线只有相关性，没有因果。
2. `anchor_a` / `anchor_c` 是什么的 id：同挂点跨载具复用（两坦克主炮位完全相同）⇒ 像是**骨骼挂点/预设 id**，
   但在资源目录里查不到对应名字，也没有第三张表可对。
3. `SeatCollectionComponent` 的 `+0x110`（22 B）、`+0x134`（22 × u32）、`+0x18C`（22 B）三组 22 长度
   的语义；现在只知道"FRV 四行在 aim 数组里非零且四值相同"。
4. `Passenger[16]` 的 `{u32,u32,u64}` 前两个 u32 是什么：全表只有一条非零（Scout Strider），样本太少。
5. 4 件"空壳"键（无组件记录）是不是被删表的残留——它们在挂载记录里还被引用着。
6. **相机 preset 与座位的绑定关系**：`CameraTemplateType` 枚举（`LandVehicle` / `FRVTurret` /
   `MannedTurret` / `RegularTurret` …）已出现在名表里，但"哪个座位用哪个模板/哪组 ±40"在本 build 的
   数据文件里找不到；旧 build 也只能靠原生表读（`CAM`）与写（`CAMW`）。
7. Turret 行限位偏移**跨 build 漂移过**（旧 `+8/+12` → 本 build `+0x1C/+0x20`）：
   漂移是"字段重排"还是"同一实体换了一套结构"未定，但**旧偏移不能照抄**已由两轮实测各自证明。

---

## 10. 复现命令

```bash
# 几何
python tools/mount_table.py explain
# 载具 19 条 / 全部记录
python tools/mount_table.py list --kind vehicle
python tools/mount_table.py list --json > /tmp/mount.json
# 座位
python tools/mount_table.py seats --json > /tmp/seats.json
# 一件的判据
python tools/mount_table.py find "TD-110"
python tools/mount_table.py show --row 23
# 换件 + 复核
python tools/mount_table.py swap --entity 0x16474112801385B6 --slot 1 \
    --item 0x9872EEB31A5F88FD --out out/mount-swap/x.plain
python tools/mount_table.py verify out/mount-swap/x.plain
```

数据来源（全部只读）：`D:\mod\refs\dlbin\plaintext-26088801\generated_entities.dl_bin`（明文，
哈希 `0x8E49771B181FFAA1`）、同目录 `dl_library.dl_typelib`、`refs/entity-locid-names.json`、
`refs/entity-components.json`、`refs/srkit-names.json`、`D:\mod\dl-type-names.json`。

## 11. M-102 枪手位 = 武器挂点？（2026-10-27 已装，`⚠` 待实机）

问题："M-102 Gunner FRV 的炮塔是不是也能像 Guard Dog 一样挂武器？之前测的都是往载具上挂各种炮塔，
原版它挂的是 MG-206 Heavy Machine Gun。"

### 11.1 离线结论：**能换，而且原版挂的本来就是"武器 item"，不是炮塔**

`python tools/mount_table.py show --entity 0xCC21C7FFD3EBEFB9` 的读数：

| 项 | 值 |
|---|---|
| 载具 | **M-102 Gunner FRV `0xCC21C7FFD3EBEFB9`**（另有一条重复行 `0xE9CD1D0D118886AF`），挂载记录 row 19 / 119 |
| 槽 0（唯一非空，`side=Common`）| item = **`0x085C1EDB038EC24E` = MG-206 重机枪（M-102 枪手位）** |
| 原生件组件 | **23 个**：`ProjectileWeapon` + `WeaponMagazine` + `WeaponReload` + `Wieldable` + `Behavior` + `LoadoutEntry`/`Encyclopedia` …；**无 `Turret`、无 `WeaponWielder`** |
| 几何 / 包 | inline mesh（3 条，2.45 MB）；包 `81da0125…` / **`902c54afb4ed396f`** / `0bdf199f…`，其中 `902c54afb4ed396f` 是本车 loadout 声明的包 |
| 座位 | M-102 的 `SeatCollection`（TransitionId 26）**带 `ActiveAimConstraint`**（§5.3）|

三条推论：

1. **FRV 枪手位挂的就是普通武器 item**（MG-206 的一个变体），不是炮塔 ⇒ "能不能挂武器"在结构上不是问题：
   槽里放什么由 `MountInfo.item` 决定（与 Guard Dog 同一个 u64、同一张表）。
2. §8 的"能瞄/能打 = 件必须自带 `Turret` + `ProjectileWeapon`"**只适用于炮塔槽**；M-102 原生件
   `Turret=False` 照样能用，因为**瞄准限制在座位**（`ActiveAimConstraint` + 相机 preset，§5.3/§4.7）。
3. §8 的"玩家能操作 = 件必须 `Wieldable` + `WeaponWielder`"对 M-102 也不成立（原生件 `WeaponWielder=False`）——
   玩家自己就是 wielder，座位→武器绑定在代码侧（§6）。

⇒ **预测**：M-102 枪手位可以挂任意普通武器 item；限制只会来自 ① 包驻留 ② 武器自身数据
（休眠型要补两处，见 [BACKPACK-DOGS §28](BACKPACK-DOGS-26088801.md)）③ 代码侧座位逻辑。

### 11.2 本轮实验（单变量）：FRV 变体 → 通用 MG-206 支援武器 item

| 项 | 值 |
|---|---|
| 改动 | 两个 M-102 实体的 `Mount` 槽 0 item：`0x085C1EDB038EC24E`（FRV 变体，23 组件）→ **`0x2152D5147B0AC418`（通用 MG-206 支援武器 item，22 组件，无 `Behavior`）** |
| 为什么选它 | 它与原生件**声明**的是同一个包 `902c54afb4ed396f`（本车 loadout 已声明）——**当时以为零驻留风险**；⚠ 后被实测否证（`✗`，见 §11.4）：声明 ≠ 载具会加载 |
| entities | `out/mount-frv/z2.dl_bin`（md5 `759974667b2c3ce07db7e944f59e4ea2`，47,259,600 B；明文 sha256 `4d39bd25…`）|
| 门禁 | 两次 `mount_table.py swap` 全 PASS（G1–G10）；对基线 `verify`：**恰好两个槽变**（row 19 / row 119 槽 0），哈希仍 `0x8E49771B181FFAA1`；装盘后 unseal 回读与暂存明文逐字节相等 |

### 11.3 判读

| 现象 | 结论 |
|---|---|
| 模型正常 + 坐枪手位能瞄能打（MG-206 手感）| **FRV 枪手位 = 通用武器挂点**，FRV 变体不是必需 ⇒ "像狗一样挂武器"成立；下一步可直接换 MG-43 / P-19（补驻留 / §28 两处修复）|
| 模型在但**打不了** | 差异落在变体的 `Behavior`/`HitEffect` 或代码侧座位绑定；下一步换 **MG-43**（普通武器、无 `Behavior`）区分"变体必需"还是"武器类别门槛" |
| 紫问号 | **已观测**：不是挂载点问题，是驻留问题——见 §11.4（已用整包驻留修复）|
| 崩 | 记录调用栈，回滚 |

**回滚**：`cp out/dogs/z1.dl_bin "<game>/data/game/generated_entities.dl_bin"`（GuardDog=P-2、其余三狗 P-19 的上一个通过版）。

### 11.4 第一轮结果：**紫问号** ⇒ "声明包 ≠ 载具会加载的包"（2026-10-27，`✗` 否证 + 已修）

实测：召 M-102 后枪手位是**紫问号**。离线定位（资源包来自 `resdep` 索引 + 两个件的 `resdep chain` 叶子）：

| 判据 | 原生件 `0x085C…`（FRV 变体）| 通用件 `0x2152…`（本轮换上）|
|---|---|---|
| unit/bones 资源出现在哪些包 | `81da0125a3af89ee` / `902c54afb4ed396f` / **`0bdf199f7ac14f43`** | **只有 `902c54afb4ed396f`** |
| 自身 `LoadoutPackage +0x08` 声明 | `902c54afb4ed396f` | `902c54afb4ed396f` |
| M-102 本体资源包 | `81da0125a3af89ee` / `149f685717737cae` / **`0bdf199f7ac14f43`** | 同左 |

⇒ 载具挂载路径**不会**去加载挂载件自己声明的包（与 Guard Dog 的"包必须驻留"同一规则，
[BACKPACK-DOGS §28.6](BACKPACK-DOGS-26088801.md)）：
- 原生件能用，是因为它的 unit 资源在**车自己的包 `0bdf`/`81da` 里有一份副本**（引擎按包加载，不按 item 声明）；
- 通用件的 unit 资源只在 `902c`，车不加载它 ⇒ 紫问号。

**修复**：把 `902c54afb4ed396f` 整包驻留到常驻宿主包：

| 项 | 值 |
|---|---|
| 补丁 | `f6fb08cc02d24255.patch_30`（+ `.gpu_resources` / `.stream`）|
| 源包 | `902c54afb4ed396f`：**73 条**，toc 3,386,266 B / gpu 9,191,280 B / stream 4,281,924 B |
| 门禁 | G1–G7 全过（补丁 73 条 == 源包 73；伴生文件尺寸/哈希自洽）|
| 产物 | `out/res-frv/`（toc sha256 `78231fbacc673f70…`）——**已装盘**（`data/` 下三件）|

**复测清单**（游戏需重开，让它重新读补丁）：① 召 M-102 看枪手位是否还有紫问号；② 有紫问号**先别开火**（会崩，§7.6）；
③ 无问号后坐枪手位试瞄/开火/装填。

**回滚**：删 `data/f6fb08cc02d24255.patch_30{,.gpu_resources,.stream}` 三件即回到"无驻留"状态；entities 回滚见 §11.3。

> 方法论：挂载件的 `LoadoutPackage` 声明只说明"谁用它、谁就得先把它加载好"，**不能指望挂载路径兑现**。
> 换任何跨包件（无人机 / 载具 / 机甲同理）都要先准备驻留，再谈"能不能开火"。

### 11.5 第一轮结果：**模型加载 + 正常使用**（2026-10-27，`✓✓`）

补上 patch_30 后复测：**枪手位模型正常出现，枪能正常使用**（可瞄/可打）。

⇒ **M-102 枪手位 = 通用武器挂点**成立；FRV 专用变体（`Behavior`/`HitEffect`）**不是必需**；
剩下的门槛就是驻留（§11.4）——和 Guard Dog 完全同一套规则。

| 结论 | 态 |
|---|---|
| M-102 枪手位可换普通武器 item（数据层）| `✓✓` 实机（MG-206 通用件）|
| 原版挂的是"武器 item"不是炮塔 | `✓` 离线组件构成 |
| 跨包件需要驻留（`LoadoutPackage` 声明不兑现）| `✓✓` 实机（patch_30 前紫问号 / 后正常）|

### 11.6 第二轮：换 **MG-43**（2026-10-27 16:5x 已装 → **`✓✓` 实机正常**）

单变量：两个 M-102 实体的槽 0：通用 MG-206 `0x2152D5147B0AC418` → **MG-43 Machine Gun `0x11C27D3BABB38956`**
（LoadoutEntry `item_type=2` 支援武器；`ProjectileWeapon+Magazine+Reload+Wieldable`，无 `Turret`/`WeaponWielder`）。

| 项 | 值 |
|---|---|
| 件 | **MG-43 Machine Gun `0x11C27D3BABB38956`**，几何 inline（mesh 5 条，1.69 MB）|
| 驻留 | **新增 patch_31**：源包 `c024a2e8ae639757`（MG-43 的 `LoadoutPackage+0x08` 声明包；64 条，toc 2.68 MB / gpu 8.84 MB / stream 6.05 MB，G1–G7 全过）|
| 已有驻留 | patch_30（MG-206 的 `902c`）保留，回滚/对照用 |
| entities | `out/mount-frv/z3.dl_bin`（md5 `e95594318ff8e8323e6b85297386a65e`，47,259,616 B；明文 sha256 `a19a8050…`）|
| 门禁 | 两次 swap G1–G10 全 PASS；对 z2 基线恰好两个槽变；哈希仍 `0x8E49771B181FFAA1`；seal 回读逐字节相等 |

**判读**

| 现象 | 结论 |
|---|---|
| 模型正常 + 能瞄能打 | 载具枪手位挂**任意同构武器**成立（MG-43 与 MG-206 同类）；可继续试手枪（P-19 包已驻留 patch_26）|
| 模型正常但不打/不能装填 | 车座对"支援武器"有特殊输入假设（载具件可能无限弹/固定装填）⇒ 记录表现再定位 |
| 紫问号 | patch_31 未生效或包不对 ⇒ 核对补丁序号/重开游戏；**先别开火**（§7.6）|

**回滚**：entities 回 `out/mount-frv/z2.dl_bin`（MG-206 版，已实机通过）；或删 `patch_31` 三件回"MG-43 无驻留"状态。

**结果（`✓✓`）**：模型/瞄准/开火均正常 ⇒ 载具枪手位挂**任意同构支援武器**成立；驻留用同样配方（patch_32 起都是"声明包 → 整包驻留"）。

### 11.7 第三轮：带背包的武器 —— **AC-8 Autocannon**（2026-10-27 17:0x 已装，`⚠` 待实机）

单变量：两个 M-102 实体槽 0：MG-43 `0x11C27D3BABB38956` → **AC-8 Autocannon `0xA8CFFB316F0B5C5F`**。

| 项 | 值 |
|---|---|
| 件 | **AC-8 `0xA8CFFB316F0B5C5F`**（`item_type=2` 支援武器），23 组件：`ProjectileWeapon` + **`WeaponRounds`** + `WeaponReload` + **`WeaponAssistedReload`** + `Wieldable`；几何 inline（mesh 1 条，2.08 MB）|
| 背包 | 背包是**独立 item**：`0xE60AE045E0090F4C` / `0x26BDDF070C31B275`（"Autocannon Backpack"）。本轮**不挂背包**（枪手位只有枪）|
| 驻留 | **新增 patch_32**：源包 `6ad7cc21015a5f85`（AC-8 的 `LoadoutPackage+0x08` 声明包；51 条，toc 3.86 MB / gpu 4.39 MB / stream 4.87 MB，G1–G7 全过）|
| entities | `out/mount-frv/z4.dl_bin`（md5 `5ef97d0e099ed2dd84ff9c9caa185816`，47,259,632 B；明文 sha256 `aed648ed…`）|
| 门禁 | 两次 swap G1–G10 全 PASS；对 z3 基线恰好两个槽变；哈希仍 `0x8E49771B181FFAA1`；seal 回读逐字节相等 |

**数据侧先记一笔**：AC-8 的 `WeaponRounds`（行 23）`+64` 弹丸 = **117**，`+72` 弹匣 = **10.0**，`+80/+84` 备弹 = **0/0**；
`WeaponReload` 行 226 有值；另有 `WeaponAssistedReload`（队友协作装填）。背包不在枪的实体上。

**判读**

| 现象 | 结论 |
|---|---|
| 模型正常、能打（打空后能装填）| 带背包的武器在**枪手位**同样可用；装填走弹药池/后备弹药，不依赖背包装备位 |
| 能打但**打空后装不上/弹量停在初始值** | AC-8 的备弹/装填依赖背包 item（本轮没挂）⇒ 下一轮把 **Autocannon Backpack** 挂到空槽（槽 1–4）或补背包路径 |
| 紫问号 | patch_32 未生效/包不对；**先别开火**（§7.6）|
| 崩 | 记调用栈、回滚 |

**回滚**：entities 回 `out/mount-frv/z3.dl_bin`（MG-43 版，已实机正常）；或删 `patch_32` 三件。

### 11.7.1 结果：**能打；装填 = 玩家背对应背包即可**（2026-10-27 17:0x，`✓✓`）

实测（AC-8 挂 M-102 枪手位）：
- **模型/瞄准/开火正常**；
- 打空后**空手装不上**（符合数据侧：`WeaponRounds` 备弹 0/0，备弹在背包 item 上）；
- **但玩家背上 `Autocannon Backpack` 后能正常装填** —— **车座会认玩家身上的背包**。

⇒ 两条新规则：

| # | 规则 | 态 |
|---|---|---|
| 1 | "枪 + 背包"分离的武器（AC-8 类）挂到枪手位后，**枪能独立工作，弹药供给仍走玩家的背包装备位**（`WeaponRounds`/`WeaponAssistedReload` 的弹药来源是背包 item，车座没有自己的背包装备位）| `✓✓` 实机 |
| 2 | 载具枪手位不是孤立武器系统：**与玩家装备共用弹药链**（背对应背包即可装填）| `✓✓` 实机 |
| — | 不背背包也能装填 | `✗` 否证（空手打空后卡住）|

> 想做到"不靠玩家背包"：后续可查三条路——① 把 `Autocannon Backpack` 挂进 M-102 空槽；② 直接给枪的
> `WeaponRounds` 写备弹（`+80/+84`，此路用户此前已实测可行）；③ 找载具自身的弹药池字段。任一成立就能让车自己带弹。

### 11.8 第四轮：手枪 —— **P-19 Redeemer**（2026-10-27 17:1x 已装 → **`✓✓` 实机正常**）

用户点名"最特殊的那两个之一"（休眠型武器）：枪手位换 **P-19 Redeemer `0x3575AABC5F1F9326`**。

| 项 | 值 |
|---|---|
| 件 | **P-19 Redeemer `0x3575AABC5F1F9326`**（`item_type=3` 副武器），几何 inline（mesh 1 条，1.10 MB）|
| 驻留 | **不需要新增**：P-19 包 `99f20df1c4cf885a` 早已整包驻留（`patch_26`，含弹匣 physics `0xC891ACF9E8DBDA97`）|
| 休眠修复 | 也不需要新改：本轮 base（z4 明文）里 P-19 的 `ProjectileWeapon+0 = 296`、`WeaponCustomization+0x80 = 0xC891ACF9E8DBDA97` 都是之前狗线留下的（实机复核过）|
| entities | `out/mount-frv/z5.dl_bin`（md5 `8e948727d07ab89d5f1f4cdf465175fb`，47,259,648 B；明文 sha256 `1b2ab540…`）|
| 门禁 | 两次 swap G1–G10 全 PASS；对 z4 基线恰好两个槽变；哈希仍 `0x8E49771B181FFAA1`；seal 回读逐字节相等 |

**判读**

| 现象 | 结论 |
|---|---|
| 模型/瞄准/开火正常，打 296 手感同玩家 P-19 | **枪手位与武器类别无关**（手枪也行）；休眠型武器在载具上同样"实体修复 + 包驻留"两件套 |
| 模型出现但比例/位置怪 | 挂点是为 MG 设计的，属视觉问题、不影响结论 |
| 能打但弹道/命中异常 | 记录（可能座位相机/准星适配问题）|
| 紫问号 | 检查 patch_26 是否在；**先别开火**（§7.6）|

**预测**：P-19 有 `WeaponMagazine`（31 发）+ `WeaponReload`，**不需要背包**，装填应直接可用（对比 AC-8 需要玩家背包）。
若装填正常 ⇒ 进一步证明"车座弹药链 = 枪自己的弹匣/弹药池，背包只在枪依赖背包时介入"。

**回滚**：entities 回 `out/mount-frv/z4.dl_bin`（AC-8 版，已实机正常）。

### 11.8.1 结果：正常（`✓✓`）

用户回报：**模型/瞄准/开火/装填全部正常**。手枪在枪手位可用；P-19 自带 31 发弹匣，**不需要背包**（与 AC-8 形成对照）。

⇒ "载具枪手位 = 通用武器挂点"已覆盖：支援武器（MG-206 通用件 / MG-43 / AC-8）+ 手枪（P-19）；
休眠型武器只要 **包驻留 + 实体复刻 delta** 两件套就位即可。

### 11.9 规则汇总（载具 / 工事挂载线收尾，2026-10-27）

| # | 规则 | 依据 | 态 |
|---|---|---|---|
| R1 | 挂载句柄 = `MountComponentData` → `MountInfo.item`（u64）；**载具 / 机甲 / 工事 / 无人机同一张表、同一个字段**；换件只写这 8 字节，`side` / `anchor` / `flag` 一律不动 | §2 · §11 · §12 | `✓✓` |
| R2 | 挂载路径**不加载挂载件声明的包**（`LoadoutPackage+0x08` 不兑现）；跨包件必须**整包驻留**（`whole_package_patch`），否则紫问号；原生件能显示是因为资源在**宿主自己的包**里有一份副本 | §11.4 实机 | `✓✓` |
| R3 | 判据按**槽类型**分：炮塔槽要 `Turret`+`WeaponWielder`（AI/机械限位）；**玩家枪手位不需要**（瞄准来自座位/相机，玩家就是 wielder）| §8 修订 · §11.1 | `✓` |
| R4 | 弹道与射速完全由**枪自己的组件**决定（`ProjectileWeapon` 逐字节相同 ⇒ 同弹道）；挂载点不参与 | §11 · §12 | `✓` |
| R5 | **弹药链**：枪自带弹匣/弹药池 ⇒ 自给自足（P-19 31 发可装填）；枪+背包分离（AC-8）⇒ **车座认玩家背的对应背包**，空手打空后装不上 | §11.7.1 · §11.8.1 实机 | `✓✓` |
| R6 | 武器类别不设限（支援武器 / 手枪都行），门槛只有：**包驻留** + 休眠型武器的**实体复刻 delta**（`Proj+0` / `cust+0x80`）| §11.5–§11.8 | `✓✓` |
| R7 | 工程流程：`mount_table.py swap`（G1–G10）→ `dlbin_seal.py seal-key` → 装盘 → unseal 回读逐字节相等；单变量、留回滚 | §7 | `✓✓` |

## 12. E/GL-21 Grenadier Battlement：墙 + 挂载的 GL-21 变体（2026-10-27，`✓` 离线解剖）

用户问："它是一个墙，上面有一把 60 发弹容量的 GL-21。看看它和原版 GL-21 除弹容、备弹之外的区别，以及 E/GL-21 Grenadier Battlement 的 mount 字段。"

### 12.1 两个实体（一个墙 + 一把枪，枪是独立 item）

| 角色 | 实体键 | 组件数 | 说明 |
|---|---|---:|---|
| **墙（E/GL-21 Grenadier Battlement）** | `0x0C8257D1C0255593` | 20 | 含 `Mount` + `SeatCollection` + `ExpandableCover` + `Health`/`Destructible` + `HellpodPayload` + `Faction` …（工事本体）|
| **墙上的 GL-21 变体（独立 item）** | `0x1D5943301A29C940` | 18 | `ProjectileWeapon` + `WeaponMagazine` + `WeaponReload` + `WeaponData` + `WeaponCustomization` + `Wieldable` …；**没有** `LoadoutEntry` / `LoadoutPackage` / `MeleeAttack` / `Spottable` |
| **原版 GL-21（支援武器）** | `0x02EECD0B1FA49630` | 22 | 以上 18 个 + `LoadoutEntry` + `LoadoutPackage` + `MeleeAttack` + `Spottable` |

> 两个实体在百科里都叫 `Grenadier Battlement` / `E/GL-21`（枪变体沿用了同一个显示名），但它们的
> `EncyclopediaEntry` 行内容不同（各自 locid）。

### 12.2 mount 字段（完整）

| 项 | 值 |
|---|---|
| 记录 | `MountComponentData` 行 **105**（行基址 `0x1CCE22C`，5 槽 × 24 B）|
| 槽 0 | `item = 0x1D5943301A29C940`（GL-21 变体）· `side = 0 Common` · `anchor_a = 3976219499 (0xED004B6B)` · `anchor_c = 600573527 (0x23CC0657)` · `flag20 = 1` · `flag21 = 0` |
| 槽 1–4 | 空（全 0）|
| 座位 | `SeatCollectionComponentData` 行 **35**：`TransitionId = 25`（Grenadier Battlement / Expandable Cover 家族），无 Passenger，**`ActiveAimConstraint[22]` 全 0** |
| 声明包 | 墙自己的 `LoadoutPackage +0x08 = 0x9D4EB484C405E7A2`（= GL-21 资产包；枪变体的弹匣 physics `0x5207AEE5F447A3E4` 也在这个包里）⇒ **墙+枪不需要额外驻留** |

> 对照：原版 GL-21 的 `LoadoutPackage +0x08 = 0x0089BBE3E284FCAA`（另一个 GL-21 资产包副本）。
> 两个包都含同一把 GL-21 的 unit 资源。

### 12.3 与原版 GL-21 的区别（除弹容 / 备弹外）

共享组件逐字节比对（当前明文）：

| 组件 | 结果 |
|---|---|
| `ProjectileWeaponComponentData`（616 B）| **逐字节相同** ⇒ 同弹丸、同射速、同弹道标记 |
| `UnitComponentData`（136 B）| **相同** ⇒ 同一个 GL-21 壳资源 |
| `Ability` / `Attachable` / `Animation` / `Interactable` / `Equipment` / `EntityBind` / `PhysicsImpactEffect` / `NetworkPhysics` / `CollisionEvent` / `EquipmentShowcase` / `Wieldable` | 逐字节相同 |
| `WeaponMagazineComponentData` | `+0x88` 容量 **60 vs 10** · `+0x8C` 初始弹匣 **0 vs 2** · `+0x90` 补给 **0 vs 3** · `+0x94` 备弹 **0 vs 3**（其余相同）|
| `WeaponCustomizationComponentData` | `+0x80`（弹匣/弹药模型资源）：**`0x5207AEE5F447A3E4`（physics） vs `0xB98F2B3D1BDE24B0`（bones `nade_launcher_ammo_frag`）** |
| `WeaponReloadComponentData` | `+0x0C` / `+0x18` 两组（共 4 个 u32）不同 ⇒ 装填动画/事件哈希不同（`⚠` 语义未定）|
| `WeaponDataComponentData` | `+0x00/+0x04` = **后坐 x/y：25/25 vs 170/175**（与 wiki GL-21 的 `recoilxy` 170/175 对上 ⇒ 字段语义确认）；`+0x1C/+0x20` = **20/30 vs 60/90**（`⚠` 疑似散布/后坐倍率，未定）；`+0x3A8` = `0xAE6CC371` vs `708.0f`（`⚠` 未定）|
| `EncyclopediaEntryComponentData` | 名字 / 代码 / 描述 locid 不同（条目不同：`E/GL-21` vs `GL-21`）|
| 组件集 | 墙版少 `LoadoutEntry` / `LoadoutPackage` / `MeleeAttack` / `Spottable`（不是可拾取物品、无近战、不可扫描）|

⇒ **墙版 GL-21 = 同一条弹道 + 低后坐（25/25 vs 170/175）+ 60 发 + 无备弹 + 独立弹匣模型/装填动画**；
除弹容/备弹外，差异集中在"操作手感（后坐）"、"弹药/装填资源"、以及"物品类组件被裁掉"。

### 12.4 可换性（与 §11 同规则）

- 墙的挂载点就是 `MountInfo.item` 一个 u64 ⇒ 可以换别的枪（和 M-102 / 狗同一条配方）；
- 但**墙只声明了 `0x9D4EB484C405E7A2` 一个包** ⇒ 换成不在这个包里的件要整包驻留（R2）；
- 墙的枪变体**自己没有 `LoadoutPackage`** ⇒ 它只在这个墙里能"零驻留"用，搬到别处同样要驻留。

### 12.5 复现命令

```bash
python tools/mount_table.py show --entity 0x0C8257D1C0255593     # 墙的挂载记录 + 五件套
python tools/resdep.py chain --entity 0x1D5943301A29C940 --dry-run   # 枪变体的组件/资源叶子
```

### 12.6 它到底是挂件还是独立武器？玩家能直接手持吗？

**① 是独立武器实体，以"挂载"方式装上去的。** 全档引用扫描（`u64 == 0x1D5943301A29C940`，20 处）：

| 引用位置 | 说明 |
|---|---|
| `EntitySettingsHashmap` 索引 1 处 | 它自己是**独立实体**（有自己的实体条目） |
| 17 张组件表各一行（哈希图槽） | 自己的 `ProjectileWeapon`/`WeaponMagazine`/`WeaponReload`/`WeaponData`/`WeaponCustomization`/`Unit`/`Wieldable`/`Encyclopedia`… 全套 |
| **`MountComponentData` row 105 +0x0** | **唯一的外部引用 = 墙的挂载槽**（键 `0x0C8257D1C0255593`） |

⇒ 它不是墙模型的一部分、也不是一个"mount 组件"；墙只是通过 `MountInfo.item` 指向它（和 M-102 指向 MG-206 完全一样）。

**② 不能"直接"手持。** 依据：

| 判据 | 墙版 GL-21 | 原版 GL-21 |
|---|---|---|
| 在 `LoadoutEntryComponentData`（玩家装备表）里 | **无行**（不可选中、不进装备菜单）| 有行（`item_type=2` 支援武器）|
| 在 `LoadoutPackageComponentData`（声明包）里 | **无行** | 有行（`0x0089BBE3E284FCAA`）|
| `MeleeAttack` / `Spottable` | 无（无近战、不可扫描）| 有 |
| `Wieldable` / `Equipment` / `Interactable` | 有（与原版逐字节相同）| 有 |

⇒ 它是"世界里的枪"（由工事/座位持有），**没有经过玩家装备系统**，所以正常游戏里不能捡起/装备/手持。

**③ 但"玩家操作"是可以的**：只要把它放进**玩家可操作的槽位**（M-102 枪手位、或它自己墙的座位），
玩家就能像用 P-19 一样使用它——因为武器组件是完整的（`ProjectileWeapon` 与原版逐字节相同）。
若要让它变成"可装备手持武器"，需要给它补 `LoadoutEntry` + `LoadoutPackage`；而**给实体新增组件这条路已被
否证**（[ENTITY-LOCID 附记的 GL-28 实验](../tables/ENTITY-LOCID-26088801.md)：插行不被采纳、删联动键后崩溃），
所以纯数据上**不建议**；唯一已验证的"玩家使用"路径就是挂载/座位。

> 组合结论：墙版 GL-21 = **独立武器 + 工事挂载 + 非装备表物品**。它是一个"功能性武器"，但不是"可携带物品"。
