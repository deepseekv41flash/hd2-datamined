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
| 换件后**实机**可用性 | **⚠ 未证（本 build）** | 机制在旧 build 由 memmod 实机验证；本 build 只做了离线等价 |

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
