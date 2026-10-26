# 炮塔 / 工事 状态机：已验证配方总表（build 26088801）

> **一句话**：把载具挂载槽里那件炮塔"修好"（出场即展开、不自转、能瞄准），绝大多数情况**只改一个 u32**
> —— 那件壳的 `state_machine` 资源里某一层的 `DefaultState`。但要**先按判据分清它属于哪一类**，不用试。
>
> 本文是**配方手册**（怎么改、改成几、改哪个偏移、哪一版被实机验过）；
> 字段语义与逐件现场记录在 [SENTRY-TURRET-FIELDS-26088801](SENTRY-TURRET-FIELDS-26088801.md)，
> 资源驻留在 [RESOURCE-RESIDENCY-26088801](../engine/RESOURCE-RESIDENCY-26088801.md)。

## 0 三态

| 标记 | 含义 |
|---|---|
| `✓✓` | 实机验证通过（挂到 M-102 FRV 炮手位/人操位真机看过） |
| `✓` | 离线可复算（读 SM/资源/组件行得出的结构事实） |
| `⚠` | 已装或已设计、未实机 |
| `✗` | 实机否证（附现象与回滚方式） |

---

## 1 五条判据（固化，照走不用猜）

### 判据 1：先认模板 —— 看 `layer0` 里有没有"展开态"

用 `state_machine_edit.py --decode` 把 `layer0` 的四个状态读出来，找**部署完成态**：
`部署过渡态（loop=0、带 EmitEndEvent）` 的 `EmitEndEvent` 在本状态的事件表里查到的那条 Link 指向谁，谁就是"部署完成/展开"。

- **有**独立的展开态（状态名 `0x823905BD6B62BA3E`）⇒ **模板 A**，`layer0.DefaultState` 设成那个索引；
- **没有**（默认态是 `0xE954AED4871D630A` 的 idle）⇒ **模板 B**，见判据 2。

> 名字是**全局共享词汇**：同一个 name 哈希在不同壳里绑各自的 clip。「有展开态」不等于「展开态有全身 clip」。

### 判据 2：模板 B 没有展开态 ⇒ 钉到**部署过渡态**，引擎会把末帧保持住

模板 B 的 `layer0` 三态是 `E954AED4`(idle, loop=1, **空 clip** ⇒ 显示 bind 位 = 折叠) /
`79DE1870`(部署过渡, **loop=0**, 全身 clip) / `D23167BF`(收起)。
`s1` **没有任何"再往前走"的过渡** ⇒ 原版一旦部署完成就永久停在 `s1` 末帧。
⇒ **`layer0.DefaultState` 设成部署过渡态的索引（一般是 1）**，`✓✓`：出场即展开，还顺带播一次 0.98 s 展开动画。

> 这条是模板 B 能被挂载的**唯一原因**：`loop=0` 且无出口的状态，引擎保持最后一帧。
> 它让"没有展开态的状态机"也能用 —— 之前只有模板 A 能用。

### 判据 3：关掉"扫视层"（否则整机被摆回收拢位 + 无人时自转）

扫视层的识别方式：**该层某个 state 的名字是 `0x9EA750D5873EB183`**（部署前 idle / 扫视）；
把这一层的 `DefaultState` 改成**同层那个 `Empty` 状态（名字 `0x86342D705E08AD12`）的索引**。

| 件 | 扫视层 | clip | 打到的骨骼 |
|---|---|---|---|
| A/MG-43 | **L5** | `1383C954` 21.33 s | `rotator×83` `gunhousing×65` |
| A/G-16 加特林 | **L6** | `3CEBEDCD` | — |
| A/M-12 迫击炮 | **L5** | `732657A5` 21.67 s | `base_elevation_arm×100` `traverse×76` `elevator_rotator×65` |
| A/MLS-4X 火箭 | **L5** | `1D39879F` 23.33 s | `traverse×84` `elevator_01×76` `elevator_02×26` `covers×1` |
| 模板 A 其余三件（AC-8/火焰/激光）| 无 | — | 本来就没有会压住本体的循环层 |

> 别只按"层号"记 —— 层号各件不同（L5/L6），**按 state 名认**。

### 判据 4（人操工事）：某轴只有在「默认开启的 `Time`/`Blend` 层 + 有键 clip」里才可控

挂到载具后，yaw/pitch 各自去找驱动层：

| 观察 | 结论 |
|---|---|
| 某轴由**默认态开启**的 `Time` 层（或真 `Blend` 树）驱动，且该 clip 在这根轴骨骼上有真关键帧 | 该轴**可控** `✓✓` |
| 某轴只存在于**事件门后的 `Clip` 状态**（事件只在"坐进它自己的座位"时才发） | 该轴在载具上**必然死**（HMG 的 pitch） |
| 某轴的 `Blend` 层里 clip 全是 **0 骨骼空壳** | 参数化瞄准是假的（HMG 的 `EE10B788`：8 条全是 0.067 s / 0 骨骼） |

### 判据 5：改完先自检字节 —— 只应该变 1–2 处

| 件 | SM 大小 | 改动处数 | 偏移 |
|---|---:|---:|---|
| AC-8 | 3,372 | 1 | `@0x74` |
| 火箭 | 4,364 | 2 | `@0x7C`、L5 |
| 火焰 | 2,100 | 1 | `@?`（`--show` 读）|
| 激光 | 2,140 | 1 | `@0x6C` |
| 特斯拉 | 2,012 | 1 | `@0x64` |
| MG-43 | 4,012 | 2 | `@0x74`、`@0xB4C` |
| G-16 | 5,724 | 2 | `@0x7C`、`@0x10B4` |
| M-12 | 4,276 | 2 | `@0x74`、`@0xB8C` |
| HMG-101 | 4,820 | 1 | `@0x74` |
| AT-12 | 6,076 | 1 | `@0x74` |
| FX-12 | 2,028 | 1 | `@0x354` |

变多处或变到别处 ⇒ 多半是拿错了 SM（尤其**一个包里有多份 SM** 时，见 §9 坑 6）。

---

## 2 全局状态名词汇（跨壳复用）

| name 哈希 | 角色 | 出现在 |
|---|---|---|
| `0x79DE1870039A1A7E` | 部署过渡（loop=0，带 `EmitEndEvent`）| **全部** 7 份哨戒 SM + 人操工事 + 特斯拉 |
| `0xD23167BF92D249B8` | 收起 | 全部 |
| `0x330CA356421F7ADA` | **待部署（折叠）** | 模板 A 全家 + 人操工事 + 特斯拉 |
| `0x823905BD6B62BA3E` | **部署完成（展开）** | 模板 A 全家 + 人操工事 + 特斯拉 |
| `0xE954AED4871D630A` | 模板 B 的 idle（loop=1，空 clip）| MG-43 / 加特林 / 迫击炮 |
| `0x69484BEF5AC55426` | 模板 B 的"部署后"（loop=1）| **仅迫击炮** |
| `0x86342D705E08AD12` | `Empty`（空态）| 到处都有，**关层就用它** |
| `0x9EA750D5873EB183` | 扫描/扫视 idle（**要关的那一层**）| MG-43 / 加特林 / 迫击炮 / 火箭 |

事件：`0x3D0B77D2=DeployDone`、`0x27A2636E=RetractDone`、`0x72C4271D=PackageDeploy`、
`0x6F8B215F=PackageRetract`、`0xF5EACFD8=Fire`、`0xA4DD22E8=FireDone`、`0x247452BF=Deployed`（模板 B 用）。

---

## 3 模板 A：有独立展开态

### 3.1 结构

`layer0` 四态（个别壳索引不同）：`s?=79DE1870` 部署过渡（loop=0，`DeployDone` → 展开）、
`s?=330CA356` 折叠（默认）、`s?=823905BD` **展开**（loop=1）、`s?=D23167BF` 收起。
**改法只有一条**：`layer0.DefaultState = 展开态索引`。

⚠ 展开态本身可能是**空 clip**（`823905BD` 绑的 clip 0 骨骼）—— 那它靠 **bind 位**就是展开姿势，照样正确（激光/AT-12/迫击炮都是这种）。

### 3.2 逐件配方

| 件 | 件 id = SM id | SM 大小/层 | 折叠 → 展开 | `layer0` 改动 | 扫视层 | 实机 |
|---|---|---:|---|---|---|---|
| **A/AC-8 自动炮哨戒** | `0x54D86057F5DACFB9`（SM `CBFE1FC7158347F3`）| 3,372 / 6 | s3 → **s2** | **`3→2`** | 无 | `✓✓` |
| **A/MLS-4X 火箭哨戒** | `0x37079568DC86E9C6` | 4,364 / 8 | s1 → **s3** | **`1→3`** + L5 `0→1` | L5 | `✓✓` |
| **A/FLAM-40 火焰哨戒** | `0x820CC3BAFE962858` | 2,100 / 4 | s1 → **s3** | **`1→3`** | 无（L3 本来 Empty）| `✓✓` |
| **A/LAS-98 激光哨戒** | `0x56070F36CFFFA8A8` | 2,140 / 4 | s3 → **s1** | **`3→1`** | 无 | `✓✓` |
| **A/M-12 迫击炮哨戒** | `0x51A0812E3BCE2D74` | 4,276 / 7 | s0 → **s3** `69484BEF` | **`0→3`** + L5 `0→1` | L5 | `✓✓`（含特效）|
| **A/ARC-3 特斯拉塔** | `0x74599E56F72F9D7E` | 2,012 / 2 | s1 → **s3**（loop=1，满骨骼 clip `FFD9A888`）| **`1→3`** | 无 | `✓`（可用，但会电车）|

> **AC-8 的更正**：旧"成果总表"里写作 `layer0=3`，以 §3.8.4 的字节级证据为准：**`0x74: 3→2`**（SM `CBFE1FC7158347F3`）。

**迫击炮的两个额外注意**：
1. 件 `0x51A0812E` 同时是 gas / EMS 两个变体的壳 ⇒ **改一次三家通用**（`⚠` 只验了 M-12）；
2. 迫击炮包里有 **3 个 `state_machine`**（`4B33E6DB` gas / `51A0812E` M-12 / `9A61CD93` EMS）——列补丁条目时**按 id 选**，别取"第一个"。

**特斯拉的特殊性**：无 `TurretComponentData`（塔不转，与原版一致）、无 `ProjectileWeapon`（电弧武器）⇒ 仍能挂；
但**仰角压低时电弧会打到车体自己**（`SensorEye+0x20` 保持原版 `3` = 敌我通吃）。见 §10 未解。

---

## 4 模板 B：没有展开态（须钉部署过渡态）

### 4.1 结构

`s0=E954AED4` idle（**loop=1，clip 0 骨骼空壳** ⇒ 显示 bind 位 = 折叠，原默认）、
`s1=79DE1870` 部署过渡（**loop=0**，`root/rotator/gunhousing/sensorpod` 全身 clip，`EmitEndEvent=0x247452BF Deployed`）、
`s2=D23167BF` 收起。`s1` 无出口 ⇒ 原版停在其末帧 = 展开。

### 4.2 逐件配方

| 件 | 件 id | SM id | SM 大小/层 | `layer0` | 扫视层 | 实机 |
|---|---|---|---:|---|---|---|
| **A/MG-43 机枪哨戒** | `0x37CDE43876BA26BB` | 同左 | 4,012 / 7 | **`0→1`** | **L5 `0→1`** | `✓✓` |
| **A/G-16 加特林哨戒** | `0xEF85D6CF58E31D70` | `61D9DDA22A59E9BC` | 5,724 / 8 | **`0→1`** | **L6 `0→1`** | `✓✓` |

**一轮被否证的弯路（`✗` 实机）**：只关 `layer5`、`layer0` 留原版 `0` ⇒ **出模型但不展开**。
原因见判据 2：`E954AED4` 绑空 clip，bind 位就是折叠。⇒ "模板 B 的 bind 位是展开位"这个类比**是错的**。

---

## 5 人操工事（E/ 类）：第三类挂载件

### 5.1 与 AI 炮塔的关键差异（判据来源）

| 组件 | AI 炮塔 | **人操工事** | 后果 |
|---|:--:|:--:|---|
| `TurretComponentData` | ✅ | **❌** | 车上没有"引擎级炮塔轴"⇒ 某轴可能死 |
| `SeatCollection` / `Interactable` | ❌ | **✅** | 自带可交互座位（按 E 坐进去）|
| `SensorEye` / `Detector` | ✅ | ❌ | 没有 AI 索敌 |
| `Wieldable`/`WeaponWielder`/`WeaponData`/`ProjectileWeapon` | ✅ | ✅ | ⇒ 挂载槽接受它 |
| `RotationSoundPlayer` | ❌ | ✅ | 说明"有可转部件" |

⇒ **能不能挂**只看武器组件（挂载槽不检查 `Turret`）；**能不能转**看判据 4。

### 5.2 逐件配方

| 件 | 件 id = SM id | SM 大小/层 | 折叠 → 展开 | `layer0` | 两轴 | 实机 |
|---|---|---:|---|---|---|---|
| **E/MG-101 HMG 工事** | `0x0E977C49DB7604F9` | 4,820 / 6 | s1 → **s2**（`823905BD`，clip `C1B7AE53` 0 骨骼）| **`1→2`** | yaw ✅ / **pitch ✗ 死** | `✓✓`（yaw+开火可用）|
| **E/AT-12 反坦克工事** | `0x2B11C9E4980EC479` | 6,076 / 7 | s6 → **s3**（`27811FE8` 0.33 s / 0 骨骼）| **`6→3`** | **yaw ✅ / pitch ✅** | `✓✓` 两轴全通 |

**两台差在哪一层（这是判据 4 的原始现场）**：

| | HMG-101 | AT-12 |
|---|---|---|
| yaw 驱动 | L1 `Time` `23C3D282`：`traverse×15` ✅ | L1 `Time` `7F6D09AE`：`traverse×15` ✅ |
| **pitch 驱动** | **没有**：L1 里 pitch 只有 2 个关键帧（常量）；真会动的两条（`E648BB4C` ×17 / `9B7CE3BA` ×16 + 双手 IK）在 **L2 的 `Clip` 态**，事件 `0x9E1081DA`/`0xBCED2F48`（只在坐进它自己座位时发）| **L2 `Time` `4D7C0C93`：`elevation×7`，默认开启** ✅ |
| L2 的 Blend | `EE10B788`：**8 条全是 0.067 s / 0 骨骼的空 clip**（假参数化瞄准）| L5 `Blend`（5 条，默认 `Empty`）|
| 实机 | yaw ✅ / pitch ✗ / 开火 ✅ | yaw ✅ / pitch ✅ / 开火 ✅ |

---

## 6 非武器件（E/FX-12 护盾继电器）

`Wieldable=False`、`WeaponWielder=False`、`ProjectileWeapon=False`、`Turret=False`，**连 `Behavior` 都没有** ——
但挂载槽照样接受它，护盾逻辑照跑：`✓✓`（车上有继电器 + 护盾泡出现 + 跟着车跑）。

| 项 | 值 |
|---|---|
| 件 / SM | `0xED13DDC480EC6910`（2,028 B，2 层）|
| **改动** | **`layer1.DefaultState 0→1`**（v2：走原版链 s0 待机 → s1 播放一次 → `EmitEndEvent 0x44E27DCA` → s2 激活）|
| 为什么不是 `0→2` | v1 直接默认 s2（跳过 s1 过渡）⇒ 实机**看起来仍是未展开**；v2 改走原版链 `⚠` 未验 |
| 其它 | 护盾参数不在 SM 里，在 `ShieldComponentData`（半径 `+0x00`、耐久 `+0x4C`、回充 `+0x58/+0x5C/+0x60`）；时长在 `HellpodPayload+0x04` |

---

## 7 总表：一件一行

| # | 件 | 类 | SM id | 改动 | 关扫视层 | 伴随改动 | 状态 |
|---:|---|---|---|---|---|---|---|
| 1 | A/AC-8 自动炮 | A | `CBFE1FC7158347F3` | `l0 3→2` | — | 壳包 `54dc633a67baa93d`；`Behavior 5→658` | `✓✓` |
| 2 | A/MLS-4X 火箭 | A | `37079568DC86E9C6` | `l0 1→3` | L5 | 整包 `11bbdf8ce39e5fc5`；`Behavior 611→658` | `✓✓` |
| 3 | A/FLAM-40 火焰 | A | `820CC3BAFE962858` | `l0 1→3` | — | 包 `1577e917ad1f287d`；`Behavior 208→658` | `✓✓` |
| 4 | A/LAS-98 激光 | A | `56070F36CFFFA8A8` | `l0 3→1` | — | 包 `36313bf684c1fd79`（单包）；`Behavior 309→658` | `✓✓` |
| 5 | A/M-12 迫击炮 | A（形状）| `51A0812E3BCE2D74` | `l0 0→3` | L5 | 整包 `a5a7e8288c7a478c` + 特效包 `8c5a99a9a40d5b8d`；`Behavior 320→658` | `✓✓` |
| 6 | A/ARC-3 特斯拉 | A（无 Turret）| `74599E56F72F9D7E` | `l0 1→3` | — | 包 `8abffb1f5544121b`；`Behavior 661→658`；掩码保持 `3` | `✓` 可用但电车 |
| 7 | A/MG-43 机枪 | B | `37CDE43876BA26BB` | `l0 0→1` | L5 | 整包 `154bd6143819df7d`（或共享包）；`Behavior 313→658` | `✓✓` |
| 8 | A/G-16 加特林 | B（8 层）| `61D9DDA22A59E9BC` | `l0 0→1` | L6 | 整包 `4ff64273030e87d6`；`Behavior 214→658` | `✓✓` |
| 9 | E/MG-101 HMG | 人操 | `0E977C49DB7604F9` | `l0 1→2` | — | 整包 `68e80476c1c602f5`；`Behavior 314→658` | `✓✓` yaw+开火；pitch ✗ |
| 10 | E/AT-12 AT | 人操 | `2B11C9E4980EC479` | `l0 6→3` | — | 整包 `5a0f047f2695b403`；`Behavior 2→658` | `✓✓` 两轴 |
| 11 | E/FX-12 护盾继电器 | 非武器 | `ED13DDC480EC6910` | `l1 0→1`(v2) | — | 整包 `fe0db34ac2b9ac61`；`Wieldable=False` 也可挂 | `⚠` 模型仍像未展开 |

> **共同伴随改动（所有件都要）**：挂到载具 ⇒ ① `mount_table.py swap` 换槽位；② 整包驻留（挂载路径不加载件自己声明的包）；
> ③ 有 `Behavior` 的件把 `Behavior` 改成 **658**（= 让车位玩家能接管；它**不管敌我**）。

---

## 8 命令速查

```bash
# ① 读：层 / 默认态 / 每态 clip 与骨骼数
python tools/state_machine_edit.py --show sm.bin
python tools/state_machine_edit.py --decode sm.bin                                          # 事件→过渡→部署完成态
python tools/state_machine_edit.py --decode --names <hashlist-normalized.csv> sm.bin        # 带名字（该 csv 来自 srkit 的 hashlists 目录，可选）

# ② 改：一层一个 u32
python tools/state_machine_edit.py --set 0=1 --set 5=1 --out sm_new.bin sm.bin
cmp -l sm.bin sm_new.bin | wc -l          # 判据 5：应该只变 1–2 处

# ③ 查 clip 打点（判据 2/4 的复核）
python tools/animation_probe.py --matrix --bones bones_<id>.json <clip 目录>

# ④ 打成资源补丁（整包驻留，顺手把改后的 SM 一起塞进去）
python tools/whole_package_patch.py build --package <包id> --host f6fb08cc02d24255 --index N \
    --edit state_machine:<SM id>=sm_new.bin --install
python tools/whole_package_patch.py check "<game>/data/f6fb08cc02d24255.patch_N"

# ⑤ 换挂载槽（实体表，保内容哈希 + 封包 + 装盘）
python tools/mount_table.py swap --entity 0x<宿主> --slot 0 --item 0x<件> --out ent.plain
python tools/entity_batch_set.py --edit "0xBA9B803D:0x<件>:0x00:<原Behavior>:658" --out ent2.plain
python tools/dlbin_seal.py seal-key ent2.plain --key refs/dlbin/keys/recipient.pk --out generated_entities.dl_bin

# ⑥ 资源层：查一个 id 在哪些包里 / 列一个包的资源
python -m srkit list "<game>/data" --id 0x<资源id>
python tools/whole_package_patch.py list --package <包id> --verbose
```

---

## 9 坑（全部实机踩过）

| # | 坑 | 现象 | 处置 |
|---:|---|---|---|
| 1 | **挂载路径不加载件声明的包** | 撤掉整包驻留只留 4 KB 同包补丁 ⇒ **紫色问号**（占位模型）| 外来件**必须整包驻留**；`declared=` 只是战备行 `+0xA8`，只有"调那条战备"时才用 |
| 2 | **同包 `patch_N`（配方 D）对挂载件无效** | 同上，那份 4 KB 补丁自始至终空转 | 同上 |
| 3 | **驻留补丁必须自带所有改后字节** | 迫击炮特效包 `patch_4` 里带了一份**原版** SM 且序号更高 ⇒ 迫击炮退回**折叠态** | 重建时 `--edit state_machine:<id>=<改后>.bin` |
| 4 | **补丁序号必须连续** | 删掉 `patch_1` 会让 `patch_2` 被**静默忽略** | 序号 0..N 不留洞（不用就留着）|
| 5 | **模型对 ≠ 特效对** | 迫击炮开火后出现**灰色半透明方块**（引擎画不出特效资源的占位）| 把该件**自己声明的包**整包驻留（`8c5a99a9a40d5b8d`）|
| 6 | **一个包里可能有多份 SM** | 迫击炮包有 3 份（gas/M-12/EMS），按"第一个"取会取错 | 列补丁条目**按 id 选** |
| 7 | **人操工事的参数层 clip 不能乱换** | 把 HMG 的 L1 clip 换成 0 骨骼占位 ⇒ **yaw 反向**，连"坐它自己座位"也反了（回归）| 已回滚；`layer1` 的 `traverse` 关键帧**承载 yaw 方向基准** |
| 8 | **`TurretComponentData+0x48` 不是骨骼哈希** | 按"骨骼哈希"解读找到的是 `551832871`=`traverse`，(标)但无 `traverse` 骨骼的 MG-43 也是这个值 | 它是某个 u32 角色/参数 id ⇒ "抄一条 turret 行"不保证能转 |
| 9 | **"有 Blend 层"≠参数化瞄准** | HMG 的 Blend 是 8 条 0.067 s / 0 骨骼空壳 | 必须查 clip 时长与打点 |
| 10 | **模板 B 不能照抄模板 A** | 只关扫视层 + `layer0` 不动 ⇒ 出模型不展开 | 见判据 2 |
| 11 | **五件套不是硬门槛** | 已证：无 `Turret`（工事/特斯拉）、无 `ProjectileWeapon`（激光/特斯拉）、**全无武器组件**（FX-12）都能挂上 | 挂载槽只看 `Wieldable`/`WeaponWielder` 一类，缺别的不会拒 |

---

## 10 未解 / 边界

| 项 | 现状 | 下一步（按成本）|
|---|---|---|
| **HMG-101 的 pitch** | 死（停最高仰角）。原因：无 `TurretComponentData`，真 pitch 链在事件门后的 L2 | ① 给它补 `TurretComponentData`（`+0x48` 语义未解）；② 把 L2 的抓握事件接进车位 |
| FX-12 的"展开" | v2（`l1 0→1`）已装 `⚠`；v1 直接到 s2 不像展开 | 若 v2 仍折叠 ⇒ 展开不在这个 SM 里（在掉落时生成的 `energy_shield` 子实体/pod）|
| 特斯拉自伤 | 可用但会电车（`SensorEye+0x20=3` 敌我通吃，`+0x20` 改 1 已否证无效）| ① 抬高源点（`unit_offset shift --dz`，已 `✓✓`）；② 缩小 `Targeting+0x00`/`SensorEye+0x00`（25 m）；③ 补 `Turret` 让它能抬高 |
| 模板 B 的 `layer3/layer4` | 由 `Deployed` 事件拉起（`rotator`/`gunhousing` 部署后循环），未单独验 | 若某台"展开但轴不跟"，先查这两层 |
| gas / EMS 迫击炮 | 与 M-12 共用 SM `51A0812E` ⇒ 判据上应同样适用 | 单独验一次（一件一局）|
| `Turret+0x2C/+0x30/+0x44/+0x48` | 看着是哈希/枚举，未命名 | 需要更多件的横比 |

---

## 11 相关

- 字段与逐件现场记录：[SENTRY-TURRET-FIELDS-26088801](SENTRY-TURRET-FIELDS-26088801.md)
- 资源驻留机制与四条配方：[RESOURCE-RESIDENCY-26088801](../engine/RESOURCE-RESIDENCY-26088801.md)
- 挂载/座位表：[MOUNT-SEATS-26088801](MOUNT-SEATS-26088801.md)
- 表字典（组件行宽/偏移）：[TABLE-DICTIONARY-25988413](TABLE-DICTIONARY-25988413.md)
