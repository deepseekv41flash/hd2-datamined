# 投送舱容量总表：每条 rack 到底能吐几个槽 —— build `26251122`

> **一句话**：每行**物理上 8 个槽**（8 × `RackAttach` 64 B）；**能吐几件不由槽位数决定**，
> 由行内 `+556`（`spawn_payload_size`）决定，而且它数的是**前 N 个非空槽**。
> 本 build 原版只有 **1 / 2 / 4 / 6** 四档（50 / 18 / 4 / 1 条）。
> 想吐 N 件 = 把 `+556` 写成 N 并把前 N 个槽填上东西。
>
> 相关：[POD-RACK](POD-RACK-26088801.md)（换载荷配方 + 双包声明）· [ENTITY-TABLE](ENTITY-TABLE-25988413.md)（实体库几何）·
> [WEAPON-AMMO-RESERVE](WEAPON-AMMO-RESERVE-26088801.md)（同一个 `+556` 的另一种用法）

---

## 0. 验证状态（三态口径见 [INDEX §7](../../INDEX.md#7-三态标记与自检)）

| 结论 | 状态 | 证据 |
|---|---|---|
| `HellpodRackComponentData` `0xA98BB156`：73 行 × 568 B，每行 `RackAttach[8]`（64 B/槽） | **✓ 离线** | typelib 成员 + 块几何现算（`tools/pod_rack_slots.py`） |
| **`+556` = `spawn_payload_size`，只有「前 N 个非空槽」生成** | **✓ 离线 + ✓ 实机 + ✓ 外部** | 本表全量（§2）· POD-RACK §2 的 rack 4 顶槽实机 · HD2Runtime SDK `docs/pod-payloads.md` |
| 原版取值只有 4 档：`1`×50 / `2`×18 / `4`×4 / `6`×1 | **✓ 离线** | §2 全表逐行读 `+556` |
| **实际件数 = `min(spawn, 非空槽数)`**（空槽不生成，后面的 authored 槽会顶上来） | **✓ 离线 + ✓ 实机** | §1.2；rack 4 清空背包槽后出两把 AC-8；rack 26/65 `spawn=2` 却只 authored 1 槽 |
| `+552` = `random_payload_size`，≠0 时从 authored 里**随机抽**；原版只有 rack 39 / 71 | **✓ 离线 + ✓ 外部** | SDK「Jammed Pod」`random=1` 且 6 个不同载荷（= rack 71） |
| 槽内 `+0x34` 是 **`RackSide` 枚举**（0 未 authore / 1 右 / 2 左），**不是数量** | **✓ 离线 + ✓ 外部** | 与 SDK 56 条 rack 的 `rackSide` 逐槽对齐（4 槽舱 = 1/2/1/2，6 槽舱末两槽 = 0） |
| 4 槽舱 = **rack 67 补给 / 68 弹药 / 69 针剂**；6 槽舱 = **rack 70（唯一）** | **✓ 离线 + ✓ 外部** | 67/69 与 SDK「Resupply pod」「Health Pack Rack pod」在 spawn=4 + 4 件 + side 序列上逐项同构 |
| 73 行在 26251122 与 26088801 之间 **spawn/random/载荷逐字节相同**（0/73 漂移） | **✓ 离线** | `--compare` 结果（§7） |
| `+556` 写到 **3 / 4** 可行（三件 / 四件全出） | **✓✓ 实机** | R10（rack 29 `+556`=3，三件）· R12/G 轮（rack 29 `+556`=4，Nova + Warp + GL-28 + GL-28 背包）；均在 [LIMITED-CROSS-PACKAGE](../engine/LIMITED-CROSS-PACKAGE-LOADING-26088801.md) 台账 |
| **4 槽舱吐 4 件 = 实机；而且载荷可以是 NPC（不是物品）** | **✓✓ 实机（2026-10-29）** | rack 67（`spawn=4`）4 个槽写 4 种 SEAF 实体 → 实机**掉出 4 个**；同一次源数据配 rack 47（`spawn=1`）只掉 1 个（§6） |
| `+556` 写到 **5–8**（超出原版 4 档） | **⚠ 未证** | SDK 声明可写区间 `[1,4]`（需 `allow_unverified_effect`）；原版只有 rack 70 的 6 档 |

---

## 1. 三个数字：8 / authored / spawn

### 1.1 结构

```
HellpodRackComponentData 0xA98BB156  @0x5E8E78, payload 43,768
  +0      2,304 B = ComponentIndexData 哈希图（144 槽 / 72 键 ⇒ 73 行，末行无键）
  +2304  41,464 B = 行数组（73 × 568 B）

行（568 B）
  +0    512  RackAttach[8]    ← 物理槽，固定 8 个
  +552    4  random_payload_size   ≠0 ⇒ 随机抽
  +556    4  spawn_payload_size    ★ 生成几个
槽（RackAttach，64 B）
  +0      8  Item（载荷实体键，0 = 空）
  +52     4  RackSide（0 未 authore / 1 右 / 2 左）
```

### 1.2 为什么是「前 N 个**非空**槽」

`+556` 不是"只在前 N 个下标里生成"，而是**跳过空槽、按顺序取前 N 个有货的槽**：

| 证据 | 现象 |
|---|---|
| rack 4（AC-8 舱，`spawn=2`，authored = ①AC ②AC 背包 ③AC ④AC 背包） | 把槽 ② 的背包清空后，舱里出现**两把 AC-8** —— 槽 ③ 被顶上来（POD-RACK §2，✓ 实机） |
| rack 47（MG-43，`spawn=1`，authored = ①MG ②MG） | 写 4 个不同 SEAF 到槽 ①②③④，实机**只出 1 个**（2026-10-29）——第 1 个非空槽之后的不生成 |
| rack 26（EAT-411，`spawn=2`，authored 只有 1 槽） | 实际只能吐 1 件：**空槽不会补**，答案就是 `min(spawn, authored)` |

⇒ 两个独立的数一起决定"吐几件"：

```
实吐件数 = min(spawn_payload_size, 非空槽数)      （random=0 时）
```

### 1.3 原版四档分布

| `+556` | 条数 | 谁 |
|---:|---:|---|
| 1 | **50** | 单件武器/背包舱（MG-43、Stalwart、Railgun、Guard Dog…） |
| 2 | **18** | 成对舱（武器+背包，或两把同款 expendable） |
| 4 | **4** | rack 67 补给 / 68 弹药 / 69 针剂 / 13 悬空载荷 |
| 6 | **1** | rack 70（针剂 ×6，唯一 6 槽舱） |

`authored`（非空槽数）分布：0×3 · 1×14 · 2×43 · 4×11 · 6×2。
**42 条 rack 的 `authored > spawn`** —— 这些"多余的 authored 槽"就是原版留的空位，抬高 `+556` 即可启用。

---

## 2. 全表（73 行）

生成命令（只读，逐次现算偏移）：

```bash
python tools/pod_rack_slots.py --table \
    --sdk "D:\mod\c11-recon\sdk-0.30.3\PodPayloadCapabilities.json"
```

列含义：
`spawn` = 行内 `+556`（生成几个）；`random` = 行内 `+552`；`authored` = 非空槽数；
**`实吐` = `min(spawn, authored)`**（random≠0 的行是"从 authored 里抽 spawn 个"）；
`槽` 列 = `槽号:载荷名(类型,side)`，`side` 即槽内 `+0x34`。

| rack | 舱 / 消费战备 | spawn | random | authored | 实吐 | 槽（side:载荷） |
|---:|---|---:|---:|---:|---:|---|
| 0 | （空 rack，未配置） | 1 | 0 | 0 | 0 | （空） |
| 1 | TEAM WEAPONS. AIR BURST ROCKET LAUNCHER | 2 | 0 | 4 | 2 | 0:Airburst Rocket Launcher(support_weapon,side2) · 1:Airburst Rocket Backpack(backpack,side1) · 2:Airburst Rocket Launcher(support_weapon,side2) · 3:Airburst Rocket Backpack(backpack,side1) |
| 2 | B-1 Supply Pack pod | 1 | 0 | 2 | 1 | 0:Supply Pack(backpack,side2) · 1:Supply Pack(backpack,side1) |
| 3 | ARC-3 Arc Thrower pod | 1 | 0 | 2 | 1 | 0:Arc Thrower(support_weapon,side2) · 1:Arc Thrower(support_weapon,side1) |
| 4 | TEAM WEAPONS. AUTOMATIC CANNON | 2 | 0 | 4 | 2 | 0:Autocannon(support_weapon,side2) · 1:Autocannon Backpack(backpack,side1) · 2:Autocannon(support_weapon,side2) · 3:Autocannon Backpack(backpack,side1) |
| 5 | SH-20 Ballistic Shield Backpack pod | 1 | 0 | 2 | 1 | 0:Ballistic Shield Backpack(backpack,side2) · 1:Ballistic Shield Backpack(backpack,side1) |
| 6 | BACKPACK. BALLISTIC SHIELD BACKPACK | 2 | 0 | 2 | 2 | 0:Ballistic Shield Backpack(backpack,side2) · 1:Ballistic Shield Backpack(backpack,side1) |
| 7 | SH-20 Ballistic Shield Backpack pod | 1 | 0 | 2 | 1 | 0:Ballistic Shield Backpack(backpack,side2) · 1:Ballistic Shield Backpack(backpack,side1) |
| 8 | GL-28 Belt-Fed Grenade Launcher pod | 2 | 0 | 2 | 2 | 0:Belt-Fed Grenade Launcher(support_weapon,side2) · 1:Belt-Fed Grenade Launcher Backpack(backpack,side1) |
| 9 | TEAM WEAPONS. C4 | 2 | 0 | 2 | 2 | 0:C4 Pack(support_weapon,side2) · 1:C4 Pack(backpack,side1) |
| 10 | SSSD Hard Drive 舱 | 1 | 0 | 1 | 1 | 0:SSSD Hard Drive(interactable,side2) |
| 11 | TEAM WEAPONS. CHEM GUN | 1 | 0 | 2 | 1 | 0:Sterilizer(support_weapon,side2) · 1:Sterilizer(support_weapon,side1) |
| 12 | 未命名工事/载具舱 | 1 | 0 | 1 | 1 | 0:未知(interactable,side2) |
| 13 | 悬空载荷 ×4 舱 | 4 | 0 | 4 | 4 | 0:0x200DC4955BD13C54(?,side2) · 1:0x2DA2D250E59E37AD(?,side1) · 2:0xB4424B37E87A68BE(?,side2) · 3:0x4DE030AA465BB790(?,side1) |
| 14 | MISSIONS. DARK FLUID BACKPACK | 1 | 0 | 1 | 1 | 0:Chemical Backpack(backpack,side2) |
| 15 | SH-51 Directional Shield pod | 1 | 0 | 1 | 1 | 0:Directional Shield(backpack,side2) |
| 16 | LIFT-182 Warp Pack pod | 1 | 0 | 2 | 1 | 0:Warp Pack(backpack,side2) · 1:Warp Pack(backpack,side1) |
| 17 | AX/AR-23 Guard Dog pod | 1 | 0 | 2 | 1 | 0:Guard Dog(backpack,side2) · 1:Guard Dog(backpack,side1) |
| 18 | AX/FLAM-75 Hot Dog pod | 1 | 0 | 2 | 1 | 0:Hot Dog(backpack,side2) · 1:Hot Dog(backpack,side1) |
| 19 | AX/TX-13 Dog Breath pod | 1 | 0 | 2 | 1 | 0:Dog Breath(backpack,side2) · 1:Dog Breath(backpack,side1) |
| 20 | AX/LAS-5 Rover pod | 1 | 0 | 2 | 1 | 0:Rover(backpack,side2) · 1:Rover(backpack,side1) |
| 21 | AX/AR-23 Guard Dog pod | 1 | 0 | 2 | 1 | 0:Guard Dog(backpack,side2) · 1:Guard Dog(backpack,side1) |
| 22 | AX/ARC-3 K-9 pod | 1 | 0 | 2 | 1 | 0:K-9(backpack,side2) · 1:K-9(backpack,side1) |
| 23 | SH-32 Shield Generator Pack pod | 1 | 0 | 2 | 1 | 0:Shield Generator Pack(backpack,side2) · 1:Shield Generator Pack(backpack,side1) |
| 24 | 40-K Meltagun pod | 1 | 0 | 1 | 1 | 0:Meltagun(support_weapon,side2) |
| 25 | MGX-42 Bullet Storm pod | 2 | 0 | 2 | 2 | 0:Bullet Storm(support_weapon,side2) · 1:Bullet Storm(support_weapon,side1) |
| 26 | EAT-411 Leveller pod | 2 | 0 | 1 | 1 | 0:Leveller(support_weapon,side2) |
| 27 | EAT-700 Expendable Napalm pod | 2 | 0 | 2 | 2 | 0:Expendable Napalm(support_weapon,side2) · 1:Expendable Napalm(support_weapon,side1) |
| 28 | TEAM WEAPONS. SPEAR | 2 | 0 | 4 | 2 | 0:Spear(support_weapon,side2) · 1:Spear Backpack(backpack,side1) · 2:Spear(support_weapon,side2) · 3:Spear Backpack(backpack,side1) |
| 29 | TEAM WEAPONS. WASP | 2 | 0 | 4 | 2 | 0:W.A.S.P. Launcher(support_weapon,side2) · 1:W.A.S.P. Launcher Backpack(backpack,side1) · 2:W.A.S.P. Launcher(support_weapon,side2) · 3:W.A.S.P. Launcher Backpack(backpack,side1) |
| 30 | FLAM-40 Flamethrower pod | 1 | 0 | 2 | 1 | 0:Flamethrower(support_weapon,side2) · 1:Flamethrower(support_weapon,side1) |
| 31 | GL-21 Grenade Launcher pod | 1 | 0 | 2 | 1 | 0:Grenade Launcher(support_weapon,side2) · 1:Grenade Launcher(support_weapon,side1) |
| 32 | GL-52 De-Escalator pod | 1 | 0 | 1 | 1 | 0:De-Escalator(support_weapon,side2) |
| 33 | S-11 Speargun pod | 1 | 0 | 2 | 1 | 0:Speargun(support_weapon,side2) · 1:Speargun(support_weapon,side1) |
| 34 | B/FLAM-80 Cremator pod | 2 | 0 | 2 | 2 | 0:Cremator(support_weapon,side2) · 1:Cremator Backpack(backpack,side1) |
| 35 | MG-206 Heavy Machine Gun pod | 1 | 0 | 2 | 1 | 0:Heavy Machine Gun(support_weapon,side2) · 1:Heavy Machine Gun(support_weapon,side1) |
| 36 | B-100 Portable Hellbomb pod | 1 | 0 | 2 | 1 | 0:Portable Hellbomb(backpack,side2) · 1:Portable Hellbomb(backpack,side1) |
| 37 | LIFT-860 Hover Pack pod | 1 | 0 | 2 | 1 | 0:HOVER PACK(backpack,side2) · 1:HOVER PACK(backpack,side1) |
| 38 | （空 rack，未配置） | 1 | 0 | 0 | 0 | （空） |
| 39 | Guard Dog 舱（随机变体） | 1 | 1 | 1 | 1 | 0:Guard Dog(backpack,side2) |
| 40 | LIFT-850 Jump Pack pod | 1 | 0 | 2 | 1 | 0:Jump Pack(backpack,side2) · 1:Jump Pack(backpack,side1) |
| 41 | LAS-98 Laser Cannon pod | 1 | 0 | 2 | 1 | 0:Laser Cannon(support_weapon,side2) · 1:Laser Cannon(support_weapon,side1) |
| 42 | MLS-4X Commando pod | 1 | 0 | 2 | 1 | 0:Commando(support_weapon,side2) · 1:Commando(support_weapon,side1) |
| 43 | LAS-99 Quasar Cannon pod | 1 | 0 | 2 | 1 | 0:Quasar Cannon(support_weapon,side2) · 1:Quasar Cannon(support_weapon,side1) |
| 44 | TEAM WEAPONS. LASER RIFLE ION | 1 | 0 | 2 | 1 | 0:Nova(support_weapon,side2) · 1:Nova(support_weapon,side1) |
| 45 | EAT-17 Expendable Anti-Tank pod | 2 | 0 | 2 | 2 | 0:Expendable Anti-Tank(support_weapon,side2) · 1:Expendable Anti-Tank(support_weapon,side1) |
| 46 | M-105 Stalwart pod | 1 | 0 | 2 | 1 | 0:Stalwart(support_weapon,side2) · 1:Stalwart(support_weapon,side1) |
| 47 | MG-43 Machine Gun pod | 1 | 0 | 2 | 1 | 0:Machine Gun(support_weapon,side2) · 1:Machine Gun(support_weapon,side1) |
| 48 | 悬空载荷 ×2 舱 | 1 | 0 | 2 | 1 | 0:0xD961F2F803F61692(?,side2) · 1:0xD961F2F803F61692(?,side1) |
| 49 | Medic Backpack (reward variant) pod | 1 | 0 | 2 | 1 | 0:MEDIC BACKPACK(backpack,side2) · 1:MEDIC BACKPACK(backpack,side1) |
| 50 | CQC-9 Defoliation Tool pod | 1 | 0 | 1 | 1 | 0:Defoliation Tool(support_weapon,side2) |
| 51 | CQC-1 One True Flag pod | 1 | 0 | 1 | 1 | 0:One True Flag(support_weapon,side2) |
| 52 | CQC-20 Breaching Hammer pod | 1 | 0 | 1 | 1 | 0:Breaching Hammer(support_weapon,side2) |
| 53 | M-1000 Maxigun pod | 2 | 0 | 2 | 2 | 0:Maxigun(support_weapon,side2) · 1:Maxigun Backpack(backpack,side1) |
| 54 | MS-11 Solo Silo pod | 2 | 0 | 2 | 2 | 0:Solo Silo(unit,side2) · 1:Solo Silo Targeting Remote(support_weapon,side1) |
| 55 | PLAS-45 Epoch pod | 1 | 0 | 2 | 1 | 0:Epoch(support_weapon,side2) · 1:Epoch(support_weapon,side1) |
| 56 | RS-422 Railgun pod | 1 | 0 | 2 | 1 | 0:Railgun(support_weapon,side2) · 1:Railgun(support_weapon,side1) |
| 57 | GR-8 Recoilless Rifle pod | 2 | 0 | 4 | 2 | 0:Recoilless Rifle(support_weapon,side2) · 1:Recoilless Rifle Backpack(backpack,side1) · 2:Recoilless Rifle(support_weapon,side2) · 3:Recoilless Rifle Backpack(backpack,side1) |
| 58 | MISSIONS. REMOTE EXPLOSIVES | 2 | 0 | 4 | 2 | 0:未知(interactable,side2) · 1:未知(other_item,side1) · 2:未知(interactable,side2) · 3:未知(other_item,side1) |
| 59 | MISSIONS. SHOULDER MOUNTED CAMERA | 1 | 0 | 2 | 1 | 0:TACTICAL VIDEO CAMERA(support_weapon,side2) · 1:TACTICAL VIDEO CAMERA(support_weapon,side1) |
| 60 | APW-1 Anti-Materiel Rifle pod | 1 | 0 | 2 | 1 | 0:Anti-Materiel Rifle(support_weapon,side2) · 1:Anti-Materiel Rifle(support_weapon,side1) |
| 61 | TEAM WEAPONS. SNIPER RIFLE DUO (APEX) | 2 | 0 | 4 | 2 | 0:Apex(support_weapon,side2) · 1:Apex Backpack(backpack,side1) · 2:Apex(support_weapon,side2) · 3:Apex Backpack(backpack,side1) |
| 62 | 悬空载荷 ×2 舱 | 1 | 0 | 2 | 1 | 0:0xB95BD5148316F8DD(?,side2) · 1:0xB95BD5148316F8DD(?,side1) |
| 63 | Resupply 物件舱（任务） | 1 | 0 | 2 | 1 | 0:Resupply(backpack,side2) · 1:Resupply(backpack,side1) |
| 64 | 任务物件舱（ObjectiveCarry） | 1 | 0 | 1 | 1 | 0:未知(interactable,side2) |
| 65 | 悬空载荷 ×1 舱 | 2 | 0 | 1 | 1 | 0:0xF8A8B17708C06606(?,side2) |
| 66 | SSSD Hard Drive 舱 | 1 | 0 | 1 | 1 | 0:SSSD Hard Drive(interactable,side2) |
| 67 | Resupply pod（补给舱） | 4 | 0 | 4 | 4 | 0:SUPPLIES(interactable,side1) · 1:SUPPLIES(interactable,side2) · 2:SUPPLIES(interactable,side1) · 3:SUPPLIES(interactable,side2) |
| 68 | AMMO 舱（弹药 ×4） | 4 | 0 | 4 | 4 | 0:AMMO(interactable,side2) · 1:AMMO(interactable,side1) · 2:AMMO(interactable,side2) · 3:AMMO(interactable,side1) |
| 69 | Health Pack Rack pod（针剂 ×4） | 4 | 0 | 4 | 4 | 0:STIMS(interactable,side1) · 1:STIMS(interactable,side2) · 2:STIMS(interactable,side1) · 3:STIMS(interactable,side2) |
| 70 | Health Pack ×6 舱 | 6 | 0 | 6 | 6 | 0:STIMS(interactable,side2) · 1:STIMS(interactable,side1) · 2:STIMS(interactable,side2) · 3:STIMS(interactable,side1) · 4:STIMS(interactable,side0) · 5:STIMS(interactable,side0) |
| 71 | Jammed Pod pod（随机 1 件） | 1 | 1 | 6 | 1 | 0:Machine Gun(support_weapon,side2) · 1:Flamethrower(support_weapon,side1) · 2:Anti-Materiel Rifle(support_weapon,side2) · 3:Guard Dog(backpack,side1) · 4:Jump Pack(backpack,side0) · 5:Supply Pack(backpack,side0) |
| 72 | （末行，无 key 无载荷） | 1 | 0 | 0 | 0 | （空） |

> 名字来源按优先级：人工判定表 [`refs/pod-rack-aliases.json`](../../refs/pod-rack-aliases.json) →
> SDK 56 条 rack 里**唯一**同构 → 战备行内部名（`+0x10` 相对偏移的字符串）→ 载荷实体名。
> 自动命名会撞车的行（例如 rack 47 的 "Machine Gun" 同被 MG-43 / MG-206 命中）**宁可留空也不猜**，
> 由人工表钉住并标状态。

---

## 3. 按「能吐几件」分组

### 3.1 六件舱（1 条）

| rack | 舱 | 载荷 | 备注 |
|---:|---|---|---|
| 70 | Health Pack ×6 舱 | 6 × `STIMS`(`interactable`) | 唯一 6 槽舱；槽 4/5 的 `side=0` —— 说明 6 槽不是"标准写法"，SDK 目录里也没有它 |

### 3.2 四件舱（4 条）

| rack | 舱 | 载荷 | 状态 |
|---:|---|---|---|
| **67** | **Resupply pod（补给舱）** | 4 × `SUPPLIES`(`interactable`) | ✓ 外部：与 SDK「Resupply pod」同构（4 × Supply Box / spawn 4 / side 1-2-1-2）；消费战备 = `Resupply` + `Resupply (reward variant)` · **✓✓ 实机（2026-10-29）：4 槽换成 4 种 SEAF → 掉出 4 个** |
| **68** | **AMMO 舱（弹药 ×4）** | 4 × `AMMO`(`interactable`) | ✓ 离线；不在 SDK 56 条里（不在战备池，任务/脚本用） |
| **69** | **Health Pack Rack pod（针剂 ×4）** | 4 × `STIMS`(`interactable`) | ✓ 外部：与 SDK「Health Pack Rack pod」同构 |
| 13 | 悬空载荷 ×4 舱 | 4 个**实体库里不存在**的键 | 空转：`spawn=4` 也一件都生成不出来 |

### 3.3 两件舱（16 条 · 武器+背包成对）

`1` Airburst · `4` AC-8 · `6` 弹道盾背包 · `8` GL-28 · `9` C4 · `25` Bullet Storm · `27` EAT-700 ·
`28` Spear · `29` W.A.S.P. · `34` Cremator · `45` EAT-17 · `53` Maxigun · `54` Solo Silo ·
`57` Recoilless · `58` Remote Explosives · `61` Apex

其中 `1 / 4 / 28 / 29 / 57 / 61` 是 `authored=4`（成对的槽 ③④ 是镜像备份，`spawn=2` 所以不生成）。

### 3.4 一件舱（49 条）

单件武器/背包舱（MG-43 `47`、Stalwart `46`、Railgun `56`、Guard Dog `17/21`…），以及：
`2/5/7/11/16/…` 这些 `authored=2` 的行 —— **两槽同款**是左右手镜像备份，`spawn=1` 所以只掉 1 件。

特例三条：

| rack | 情况 |
|---:|---|
| 26 EAT-411 | `spawn=2` 但只 authored 1 槽 ⇒ 实吐 1 |
| 65 悬空载荷 | `spawn=2` 但只 authored 1 槽（且该键不是实体）⇒ 实吐 ≤1 |
| 71 Jammed Pod | `spawn=1` + **random=1** + 6 个不同载荷 ⇒ 每次从 6 件里**随机掉 1 件**（✓ 外部：SDK 同构） |
| 39 Guard Dog | `spawn=1` + random=1，但可抽集合只有 1 件 ⇒ 等效单件 |

### 3.5 空舱（3 条）

`0` / `38` / `72` —— 8 槽全 0（`72` 连哈希图键都没有，是 72 键 / 73 行的末行）。

---

## 4. 要「吐 N 件」怎么选舱（配方）

| 目标 | 免改 `+556` 的做法 | 需要改 `+556` |
|---|---|---|
| 1 件 | 任意单件舱（49 条） | — |
| 2 件 | §3.3 的 16 条两件舱 | 任意舱 `+556=2` + 填两槽（原版就有 2 档，改档无实机） |
| 3 件 | 原版无 3 档 | 任意 `authored≥3` 的舱改成 3 —— **✓✓ 实机（R10，2026-10-23：rack 29 三件全出）** |
| 4 件 | **rack 67 / 68 / 69** | 任意 `authored≥4` 的舱改成 4 —— **✓✓ 实机（R12/G 轮 物品、2026-10-29 NPC）** |
| 6 件 | **rack 70** | 任意舱 `+556=6` + 填 6 槽（⚠ 未证：原版 6 档存在但没被我们改写过） |

### 4.1 未发布舱：把「医疗补给」叫出来（额外战备链）

rack 69 的消费方是 **id 80 / 93 `HEALTH PACK RACK`（显示名 Medical Supplies）**，属未发布战备：
商店不卖、配装里没有 ⇒ 必须走 `StratagemInfo +0xC8 additional_stratagem`（带上宿主战备时**附赠**
另一条，不占配装位；**成环会崩**，见 `tools/stratagem_extra.py`）。

```bash
# 在现有车辆链(34→106→111→138)的链首插入 80，两件事同局可测
python tools/stratagem_extra.py --plain D:\mod\out\gater2625\lav-strat.plain \
    --chain 34:80,106,111,138 --out strat.plain
# 结果：34(Resupply) → 80(Medical Supplies) → 106(Carpet Bomb) → 111(Scrambler) → 138(Incinerator FRV)
```

| 事实 | 值 |
|---|---|
| 宿主 | **id 34 `CONSUMABLES. RESUPPLY`**（配装里带补给即可，不额外占位） |
| 目标 | **id 80**（93 是同舱的 President Rewards 变体，`+0xA8` 相同 `0xC6D14774E5C77651`） |
| 链长 | 4 跳（原 3 跳 + 链首插 1）——已验证原 3 跳可跑，本次多 1 跳待实机 |
| 门的逻辑 | 只改 3 个 `+0xC8`（34/80 两处 + 尺寸字段），其余字节不动，Murmur 复原 |

写 `+556` 的配方（rack 行内 `+0x22C`，**行基址 = 行数组起点 + rack 号 × 568**）。
用 `rack_edit.py`（任意槽 + `--spawn` 一次写完，G1–G7）：

```bash
# ① 只改 spawn（把 MG-43 舱抬到 4 件；`--expect-slot spawn=1` 就是 G7 校验旧值）
python tools/rack_edit.py --rack 47 --spawn 4 --expect-slot spawn=1 --out entities.plain

# ② 改槽 + 改 spawn（一次成型：补给舱 4 槽塞 4 个 SEAF）
python tools/rack_edit.py --rack 67 \
    --slot 0=0x75F7E96AF7DCD303 --slot 1=0xBFB5C88D557595D8 \
    --slot 2=0x78DABC7344E50234 --slot 3=0xA00331F24DEEF2EE \
    --spawn 4 --expect-slot spawn=4 --out entities.plain

# ③ 封装 + 部署
python tools/dlbin_seal.py seal-key entities.plain --key <recipient.pk> --out generated_entities.dl_bin
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed generated_entities.dl_bin
```

> ⚠ **不要用 `plain_edit.py` 改这个字段**：它只认设置表的 24 B 块头；实体库是 28 B 头块链，
> 会被直接拒绝。实体库的内容哈希校正必须走 `rack_edit.py` / `pod_rack_swap.py` 的 tail 宿主。
>
> 本轮实测：只改 spawn 时文件里只有 **2 个字节**变化（spawn 本身 + 末块 payload 尺寸字段），
> 哈希锚点仍是 `0x8E49771B181FFAA1`；把 `--expect-slot` 写成 `spawn=9` 会被 G7 咬住并且**不写输出**。

⚠ 三条硬约束：

1. **别靠"清空槽"减件数** —— 空槽会被后面的 authored 槽顶上来（§1.2）。
2. **别动 `+552`** —— 它是"随机抽"，不是数量；原版 71 条为 0、2 条为 1。
3. **`spawn` 与 authored 要成对改**：`spawn` 大于非空槽数时不会补出空槽物件，只会少吐。

---

## 5. 边界与未解

- **上限就是 8**：每行只有 8 个 `RackAttach`；`spawn > 8` 无意义（未测，结构上无第 9 槽）。
- **5–8 档未实机**：SDK 把可写区间声明为 `[1,4]` 并要求 `allow_unverified_effect`；本仓库只证到 4。
- **6 槽舱的写法是特例**：rack 70 槽 4/5 的 `side=0`，与 4 槽舱"1/2/1/2"不同；照抄它抬 `spawn=6` 是否稳，未测。
- **悬空载荷**：rack 13 / 48 / 62 / 65 的槽指向**实体库里不存在的键**，改这些槽之前先换成真载荷（否则 `spawn` 抬高也不吐）。
- **一舱多战备（shared rack）**：SDK 记 6 条；改这些舱要逐个确认消费方（`--no-strat` 可跳过反查，反查只在命中唯一时才给名字）。
- **槽内 `+56`、行内 `+560` 之后**等未知字段仍未解；本表只覆盖 `Item` / `RackSide` / `+552` / `+556`。

---

## 6. 修正与教训（本线自己踩的坑）

| 之前的说法 | 实际 | 影响 |
|---|---|---|
| "槽内 `+0x34` 是**数量**（补给舱 = 数量 1/2/1/2）" | `+0x34` = **`RackSide`**（0/1/2），不是数量 | 曾据此以为"补给舱吐 6 个箱子"。实际补给舱 = `spawn=4` × 每槽 1 件 = **4 个** |
| "MG-43 舱塞 4 个 SEAF 只出 1 个，原因不明" | **rack 47 `spawn=1`**（本次普查的直接读数） | 4 个槽 authored 也没用：第 1 个非空槽之后不生成。要让舱吐 4 个 NPC，得换 rack 67/68/69（`spawn=4`）或把 `+556` 抬到 4 |
| "多槽舱会不会只吐 1 个 NPC / 舱载荷有没有 NPC 单发限制" | **没有**：rack 67（`spawn=4`）4 槽写 4 种 SEAF → **✓✓ 实机掉 4 个**（2026-10-29） | 约束只在 `+556`；同一份数据放 rack 47（`spawn=1`）只掉 1 个 —— 两个读数互为对照 |

> 盘上字节证据（工作区 `D:\mod\out\gater2625\`）：`pod-seaf4.plain`（4 个 SEAF 塞 rack 47）读回仍是 `spawn=1`；
> `pod-seaf4-resupply.plain`（4 个 SEAF 塞 rack 67）读回 `spawn=4`。同一份实体库里只差这一行。
> 实机读数：前者 1 个、后者 **4 个** ⇒「能吐几件」这一格就是唯一变量。

---

## 7. 复现

```bash
python tools/pod_rack_slots.py                       # 分布 + 2 件以上舱速览
python tools/pod_rack_slots.py --table               # 73 行 markdown（本 doc §2）
python tools/pod_rack_slots.py --rack 47             # 单条详情（含槽 side 与实体键）
python tools/pod_rack_slots.py --json refs/pod-rack-slots-26251122.json
python tools/pod_rack_slots.py --compare "D:\mod\refs\dlbin\plaintext-26088801"
```

`--compare` 实测输出：`⇒ 73 行里 0 行有差异`（build `26088801` → `26251122`，
spawn / random / 8 个槽的实体键全部逐字节相同）⇒ **本表跨 build 稳定，不必每次更新重做**；
`+0x22C` 与 `+0x228` 的偏移在换 build 时仍应由 `pod_rack_swap.py` 现算复核。

**探 `+556` 5–8 档的已装盘件（2026-10-29 20:5x）**：`D:\mod\out\pod-seaf8-rack69\`

| 文件 | sha256 前 16 | 内容 |
|---|---|---|
| `generated_entities.dl_bin` | `f4902f6e32a2aac4` | **rack 69（医疗补给舱）8 槽 = 8 种 SEAF + `spawn=8`**；rack 67 回原版（补给恢复 4 个补给箱） |
| `generated_stratagem_settings.dl_bin` | `cf65b3b368693109` | 链 **34→80→106→111→138**（链首插入医疗补给，车辆线 138 保留） |

两份都做过 sealed round-trip（`open-key` 解回逐字节相等）与盘上回读（rack 69 `spawn=8` / 8 个 SEAF 实体键、
链四跳齐全）。回滚：`dlbin_deploy.py restore --file <文件名>`。
（早前备的 rack 67 八槽件仍在 `D:\mod\out\pod-seaf8\`，未装。）

机器可读产物：[`refs/pod-rack-slots-26251122.json`](../../refs/pod-rack-slots-26251122.json)
（73 行 × `spawn/random/authored/effective/pod/slots`）。

---

## 8. 溯源与许可

外部依据（只引用字段名/偏移/结论，不复制代码）：

- **[HD2Runtime](https://github.com/SkyeShade/HD2Runtime)** SDK 0.30.3 —— `docs/pod-payloads.md`（"前 `spawn_payload_size` 个槽生成"）、
  `PodPayloadCapabilities.json`（56 条 rack 的 `spawnCount` / `randomPayloadSize` / 每槽 `rackSide` / `active`，
  以及 `Jammed Pod` 的 `random=1` 语义）。本地参照 `D:\mod\c11-recon\sdk-0.30.3\`。
- 本仓库一手证据：`tools/pod_rack_slots.py`（typelib 现算 + 哈希图反查）、
  POD-RACK §1–§2 的槽位/顶槽实机记录、`refs/pod-rack-aliases.json` 的人工判定与状态。
