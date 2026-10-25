# 阵营（Faction）与 AI 行为（Behaviour）：memmod 期的两条改法，现在都在明文表里（build `26088801`）

> **一句话**：memmod 时期那两个"运行时写"——`--faction 1`（改阵营位掩码）与 `AIBEH`（把炮塔的 behaviour id 抢过来）——
> 对应的就是实体库里的两张明文组件表：**`FactionComponentData`（`0x5653EA91`）`+0` 的 u32 位掩码**
> 和 **`BehaviorComponentData`（`0xBA9B803D`）`+0` 的 u32 behaviour id**。
> 两张表都在 `generated_entities.dl_bin` 里，可离线读、可保哈希写（本轮已用门禁证明）。
>
> **状态**：表结构 / 枚举 / 旧日志对照 **✓ 离线**；离线写入 **✓ 门禁通过（G1–G8）**；**实机未验 ⚠**。

---

## 1 旧档怎么做的（memmod 期，工作区档 `D:\mod\docs\`）

| 线 | 旧文档 | 做法 | 表象 |
|---|---|---|---|
| **阵营** | `VEHICLE-MOUNT-ITEMS.md` §6.0（2026-10-19 实机全通） | 运行时把件的 `FactionComponentData` 记录 `+0` 位掩码改成 **1**（超级地球）；旧档枚举：1=超级地球 / 4=光明族 / 8=自动化军团 / 0=继承 | 敌人件挂超级地球载具时：**没有实体**（或"运输机当场把槽位打空"）——症状与"建不出 unit"一样 |
| **AI 行为** | `VEHICLE-AI-TURRET-TAKEOVER.md` §3.2 | `AIBEH` pass：把炮塔的 **behaviour id** 换成"第一个有编号的兄弟槽"的值（日志 `645 → 658`），一次写、粘住 | AI 不再抢炮塔，玩家能持续操作 |

两条都是**进程内存**写（memmod 时代）；本轮把它们落到数据表上。

---

## 2 现在它们在哪（**✓ 离线**，`generated_entities.dl_bin`）

| 组件 | type id | 键 / 行 | stride | 行内关键字段 |
|---|---|---:|---:|---|
| **`FactionComponentData`** | `0x5653EA91` | 533 / 534 | 152 | **`+0` u32 = 阵营位掩码**；`+4` u32（样本里常见 32）；`+12` 起是一段交替 `429981570 / 2494648122` 的成对值（疑"关系矩阵"，未解） |
| **`BehaviorComponentData`** | `0xBA9B803D` | 993 / 994 | 12 | **`+0` u32 = behaviour id**；`+4` f32 = **20.0（993 行全同，常量）**；`+8` u32 = flags（0/8/2/16/128 等） |
| `AiEnemyComponentData` | `0x9D0EEFB5` | 160 / 160 | 736 | 存在即"AI 大脑"（mount 工具的否决项就是它）；行内 102 个非零字段（AI 参数） |
| `SensorEyeComponentData` | `0x14729B6A` | 315 / 316 | 44 | 索敌（锁定距离等，见 [LOCKON-TARGETING §2](LOCKON-TARGETING-26088801.md)） |
| `TargetingComponentData` | `0x2C0968D2` | 297 / 297 | 64 | 角色索敌瞄准参数（**不是**玩家锁定） |
| `DetectorComponentData` | `0xFF67A367` | 321 / 321 | 24 | 探测 |

> 与 [MOUNT-SEATS §4](MOUNT-SEATS-26088801.md) 的五件套/否决项目一致：**Faction 行有值 ∈ {2,4,8} ⇒ 敌人件**；
> **AiEnemy 行存在 ⇒ 自带 AI 大脑**。

---

## 3 阵营枚举：实测补上 **2 = 终结者（虫子）**

按"位掩码值 → 实体名"抽样反查（名字来自 `EncyclopediaEntry`）：

| 值 | 数量 | 样例句 | 判定 |
|---:|---:|---|---|
| **0** | 141 | （多无名字） | 无阵营 / 继承 |
| **1** | 166 | `Solo Silo` 等 | **超级地球**（✓ 与旧档一致） |
| **2** | 71 | `Impaler`、`Bug Hole`、`SPORE SPEWER`、`Infested Tower`、`Alpha Commander` | **终结者（虫子）** ← **旧档没记，本轮补** |
| **4** | 52 | `Overseer`、`Elevated Overseer`、`Voteless` | **光明族**（✓） |
| **8** | 103 | `Devastator`、`Factory Strider`、`Fabricator`、`Trooper` | **自动化军团**（✓） |

> **英文对照**（写文档/检索第三方资料时用这套）：`1 = Super Earth` · `2 = Terminid`（虫子）· `4 = Illuminate`（光明族）· `8 = Automaton`（自动化军团）· `0 = inherit`。
> 本轮光明族光束炮头就是 **faction 4 → 1**（Illuminate → Super Earth）。

**有行 vs 没行**（很重要，改之前先看这个）：

| 件 | Faction 行 | `+0` |
|---|---|---|
| 运输机炮塔 `0x8365609B35EF6672` | **有** | **1**（超级地球） |
| 地堡 HMG `0xCD28A27A79BE53D5` | **有** | **8**（自动化军团） |
| 40 mm 炮塔站 `0x9872EEB31A5F88FD` | 无 | —（继承） |
| MG-206 `0x085C1EDB038EC24E` | 无 | — |
| TD-110 主炮 `0xD58AE6A04EDB10DE` | 无 | — |
| 爱国者导弹巢 / EXO-49 右臂机炮 | 无 | — |

⇒ **"敌人件"才有 Faction 行且值为 2/4/8**；玩家件多数没有这一行。
旧档的跨阵营配方（敌人件必须 `--faction 1`）现在就是：**把 `FactionComponentData +0` 写成 1**（没有行的件先不用管）。

---

## 4 AI 行为：旧 `AIBEH` 写的就是 `BehaviorComponentData +0`

把旧日志里的 id 拿到本 build 的表里逐个对上（**✓ 离线**）：

| behaviour id | 实体 | 备注 |
|---:|---|---|
| **645** | `0x8365609B35EF6672` 运输机炮塔 | 旧日志"slot 0 behaviour 645 → 658"的**被改方** |
| **658** | `0x3A061009AA31E9CB` **TD-110 槽 2 的原始件（烟幕发射器）** | 旧日志的"**源槽**"——就是它！玩家开火件的 behaviour |
| **670** | `0x9872EEB31A5F88FD` 40 mm 炮塔站 / `0xC25DC40EDE0E2D16` 孤儿炮塔站 | 站点自己的 behaviour |
| 655 | TD-110 主炮 / TD-220 主炮 | |
| 691 | MG-206（3 个实体变体）| |
| 171 / 172 | 爱国者导弹巢 / EXO-49 右臂机炮 | |

⇒ **"把 AI 领走"= 把某个件的 `BehaviorComponentData +0` 改成玩家武器件的 id**（如 658），
不需要 runtime、不需要每帧 PIN 兜底。表里 658 只出现 **1 次**（就是那个烟幕件），说明它是唯一的"玩家炮塔行为"样本之一。

`+4` 全表恒 **20.0**（f32）⇒ 不是逐件可调的量，改它很可能无意义（未验）。
`+8` 的 flags（0/8/2/16/128）语义未知，**别乱动**。

---

## 5 可写性（**✓ 离线门禁通过**，未装盘）

`tools/entity_field_set.py` 直接就能写这两格（tail 宿主保内容哈希）：

```bash
# 阵营：地堡 HMG（自动化军团 8）→ 超级地球 1
python tools/entity_field_set.py set \
    --block 0x5653EA91 --key 0xCD28A27A79BE53D5 --field 0 --type u32 --value 1 --expect-old 8 \
    --out out/x.plain
# 行为：运输机炮塔 645 → 658（旧 AIBEH 的同一个改动）
python tools/entity_field_set.py set \
    --block 0xBA9B803D --key 0x8365609B35EF6672 --field 0 --type u32 --value 658 --expect-old 645 \
    --out out/y.plain
```

本轮两条都真跑了一遍（输出到 `D:\mod\out\faction-beh-test\`）：**G1–G8 全 PASS**，
Murmur64A 内容哈希保持 `0x8E49771B181FFAA1`。

### 5.1 工具同步（本轮已改）

`tools/mount_table.py`：

- `FACTION_NAMES` 里 `2: "?"` → **`2: "terminid"`**（并加注释写明四个值的实测依据）；
- 否决项 `veto_enemy_faction` 从 `(4, 8)` 扩到 **`ENEMY_FACTIONS = (2, 4, 8)`** —— 以前**虫子件不会被拦**。

---

## 6 三态

| 主张 | 态 |
|---|---|
| 阵营在明文表 `FactionComponentData` `0x5653EA91`，`+0` = 位掩码 | **✓ 离线**（533 键，按名抽样反查） |
| 枚举 1=SE / 2=终结者 / 4=光明族 / 8=自动化军团 / 0=继承 | **✓ 离线**（2 为本轮新增） |
| 玩家件多数**没有** Faction 行；敌人件有且值为 2/4/8 | **✓ 离线** |
| AI 行为在明文表 `BehaviorComponentData` `0xBA9B803D`，`+0` = behaviour id | **✓ 离线**（旧日志 645/658 双向对上） |
| 旧 `AIBEH` = 改这一格 | **✓ 离线推定**（645 被改方、658 源槽全对上；旧档为运行时写） |
| 两格都能离线保哈希写 | **✓ 离线**（G1–G8 全过） |
| 实机效果（改阵营后敌人件能挂、改 behaviour 后 AI 不再抢炮塔） | **⚠ 未证**（本 build 未做） |

---

## 7 溯源

- 旧档：`D:\mod\docs\VEHICLE-MOUNT-ITEMS.md` §6.0（跨阵营配方）· `D:\mod\docs\VEHICLE-AI-TURRET-TAKEOVER.md` §3.2（AIBEH）
- 本 build 表几何：`tools/entity_field_set.py` / `tools/typelib.py` 现算；数据 `refs/dlbin/plaintext-26088801/generated_entities.dl_bin`
- 名字：`refs/entity-locid-names.json`（`EncyclopediaEntryComponentData`）
- 相关：[MOUNT-SEATS §4](MOUNT-SEATS-26088801.md)（五件套 / 两条否决项）· [LOCKON-TARGETING §2](LOCKON-TARGETING-26088801.md)（SensorEye 字段）

---

## 8 复现旧实验：运输机炮塔 → TD-110 槽 0，只改 `Behavior +0`（**⚠ 待验**）

### 8.1 盘上内容

| 文件 | 大小 | sha256 | 改动 |
|---|---:|---|---|
| `D:\mod\out\shuttle-beh\generated_entities.shuttle-beh658.dl_bin` | 47,259,608 | `14c8f6462fdb9acb` | ①TD-110 行 125 **槽 0**：`0x9872EEB31A5F88FD`（40 mm 站）→ **`0x8365609B35EF6672`（运输机炮塔）**；②`BehaviorComponentData +0`：**645 → 658**（旧 `AIBEH` 的同一个改动） |

**不动 Faction**：运输机炮塔本来就 `Faction +0 = 1`（超级地球），不需要改（与旧档结论一致）。
换件走 `mount_table.py swap`（G1–G10 全过，`changed=[(125,0,…)]`）；行为走 `entity_field_set.py`（G1–G8 全过，diff=2）；
封箱后 `open-key` 回读字节级一致；Murmur64A 保持 `0x8E49771B181FFAA1`。

工具在换件时给出两条提醒（都是旧档已知的）：**AI 索敌三件套齐**（它会自己开火）、**机械射界 ±180 → ±105**。

### 8.2 ⚠ 数据路线与旧 memmod 路线的两个差别（判读前必须知道）

| # | 差别 | 影响 |
|---|---|---|
| 1 | 旧 `AIBEH` 改的是**实例**（运行时那份组件数据）；数据路线改的是**件本身的行** | **全局生效**：所有运输机炮塔（包括敌人运输机上的那门）都会跑 behaviour 658 |
| 2 | 旧实验有 runtime warm 兜底；本轮**没有为它声明包**（保持单变量） | 炮塔资源在 4 个包里：`af782724c0f7658b` / `131fe264b7380717`（超级地球运输机，各 212 资源 / 22.7 MB）、`a0a27e07d3cbb445`（空降舱，28 资源）、`09985dc611a3a8b6`（关卡包，228 MB）。任务里运输机一出现通常就驻留了 |

### 8.3 判读

| 观察 | 判定 |
|---|---|
| 炮塔模型出现、能瞄能打、**不自己转 / 不被 AI 抢** | **✓ 纯数据版 `AIBEH` 成立**（不需要 runtime、不需要每帧 PIN） |
| 仍自己转 / 打几秒被抢 | behaviour 658 不够（可能还要兄弟槽的其它条件，或实例行不是从件行复制） |
| **紫问号** | 包没驻留 ⇒ **千万别开火**（[EXO-ARM-VARIANTS §10.2](../tables/EXO-ARM-VARIANTS-26088801.md)：紫问号臂件开火会崩）⇒ 下轮再加 `+0xA8` 声明 |

回滚：`python tools/dlbin_deploy.py restore --file generated_entities.dl_bin`
（会连 EXO-45 双臂、TD-110 槽 2/FRV 的 40 mm 站一起回原版；只想回上一版则重装
`D:\mod\out\exo45-arms-v2\generated_entities.exo45-mk2-ac200.dl_bin`。）

---

## 9 上一轮结果 + 驾驶位复测（2026-10-25）

### 9.1 §8 的结果：**纯数据版 `AIBEH` ✓ 成立**

运输机炮塔装到 TD-110 **槽 0（主炮位）**、只把 `Behavior +0` 改成 658：

> 实机：**模型出现、能瞄能打、一直都不会被抢**（用户原话）

⇒ memmod 时代的 `AIBEH`（运行时改实例 + 每帧 `PIN` 兜底）**在数据路线上一个 u32 就够了**，
不需要 runtime、不需要持续写。这条与 §3/§4 的表结构完全对得上（645 = 运输机炮塔原 behaviour，
658 = TD-110 烟幕件的 behaviour）。

### 9.2 本轮：把同一门炮放回**驾驶位的槽**（旧 memmod 从未测过的组合）

memmod 时期的历史：**先用驾驶位**（槽 2，原烟幕位）→ 被 AI 抢 → 换到主炮位 → `AIBEH` 成功后
**再没放回驾驶位**。本轮把这个缺口补上：

| 项 | 值 |
|---|---|
| TD-110 **槽 0** | 恢复原版主炮 `0xD58AE6A04EDB10DE`（不再占用主炮位） |
| TD-110 **槽 2（原烟幕位）** | **`0x8365609B35EF6672`（运输机炮塔）** |
| `Behavior +0`（运输机炮塔） | 已是 **658**（§8 的件级改动**仍然生效**，本轮不用再动） |
| 文件 | `D:\mod\out\shuttle-slot2\generated_entities.shuttle-slot2.dl_bin`（47,259,624 B，sha256 **`92124d3528403d7e`**） |
| 门禁 | 两次换件 G1–G10 全过（`changed=[(125,0,…)]`、`changed=[(125,2,…)]`），Murmur64A 保持，封箱回读一致 |

### 9.3 判读表（三条互斥）

| 观察 | 判定 |
|---|---|
| 驾驶位**能瞄能打、不被抢** | ✓ 关键结论：**座位控制通道与 AIBEH 互不冲突** —— 之前"驾驶位不行"是 AI 抢，不是座位没通道 |
| 能开火但**不能瞄/不能转** | 该座位没有瞄准/相机通道（与 [MOUNT-SEATS §4.7](MOUNT-SEATS-26088801.md) 的"准星/装填属座位侧"同源） |
| **紫问号** | 包未驻留 ⇒ **不要开火**（[EXO-ARM-VARIANTS §10.2](../tables/EXO-ARM-VARIANTS-26088801.md)） |

附带观察点（都不影响主判据）：

- 模型会挂在**烟幕发射器的小挂点**上，可能悬空/偏移；
- 机械射界按件（±105），但玩家实际能转多少 = 相机层与机械层取小；
- 想再验"AI 是否真被领走"，可以做一局**对照**：把 `Behavior +0` 改回 645（同一个件级改动），
  驾驶位应重新出现"打几秒被抢" ⇒ 这是 §8 结论的**反向验证**。

回滚：`python tools/dlbin_deploy.py restore --file generated_entities.dl_bin`
（回上一版：`install --sealed D:\mod\out\shuttle-beh\generated_entities.shuttle-beh658.dl_bin`）

---

## 10 放进**敌人**炮塔（2026-10-25，**⚠ 待验**）：Faction 8→1 + Behaviour 90→658 + 包声明

### 10.1 选件与改动

| 项 | 值 |
|---|---|
| 件 | **`0x9926876B2375A1BB`**「Bunker Turret · 自动化军团小口径自动炮」（28 组件：`ProjectileWeapon` ✓ `Turret` ✓ `Wieldable`+`WeaponWielder` ✓ **`AiEnemy`** ✓ 索敌三件套 ✓） |
| 旧读数 | `Faction +0 = 8`（自动化军团）· `Behavior +0 = 90` |
| 本轮改成 | **`Faction +0 = 1`**（超级地球）· **`Behavior +0 = 658`**（旧 `AIBEH` 那套玩家武器行为） |
| 挂载 | TD-110 **槽 2（原烟幕位 / 驾驶位）**：上一轮的运输机炮塔 → 本件；槽 0 保持原版主炮 |

文件（**✓ 已装**）：`D:\mod\out\enemy-turret\generated_entities.enemy-turret.dl_bin`（47,259,648 B，sha256 **`ae1e006f5fd896f4`**）。
换件 G1–G10、两格字段写 G1–G8 全过，Murmur64A 保持 `0x8E49771B181FFAA1`，封箱回读一致。

### 10.2 资源加载（用户特别提醒的那一条）

该件的资源在 **4 个包**里各有完整一套（bones / physics / state_machine / mesh 1.74 MB）：

`4f3d304001614b38` · `0c37e83a8d16b67a` · `a8c58d2665dc2d99` · `b000071734784fb3`
（旧档把前两个称作「自动化军团指挥地堡的**关卡内容包**」——不是 loadout 包，**不会因为带了某个战备就驻留**。）

按 [§9](../cases/EXO45-ARM-SWAP-26088801.md) 与 [EXO-ARM-VARIANTS §9](EXO-ARM-VARIANTS-26088801.md) 的结论（**`+0xA8` 是替换语义、一台载具只给 1 个口**），
本轮用**两个免费常驻行**声明同一个包：

| 行 | `+0xA8` | 依据 |
|---|---|---|
| `Reinforce` **行 57**（基址 `0x6FDC`，字段 `0x7084`） | `0x4F3D304001614B38` | 变体 A 实机证明该行在关卡加载时被读、且它自己不投送资产（原值 0） |
| `Reinforce` **行 138**（`0x12524`） | 同上 | 同上（同一战备的重复行，保险起见两行都写） |

文件：`D:\mod\out\enemy-turret\generated_stratagem_settings.enemy-pkg.sealed.dl_bin`（82,448 B，sha256 **`cbc2ae630dbcbd65`**）。
它是在上一版（EXO 双臂用的两包：行 143 = 解放者包、`SOS` 行 59 = 爱国者包）**之上**再加两个声明 ⇒ 现在同时有 **4 个包口**在用：

| 口 | 包 | 服务于 |
|---|---|---|
| EXO-45 行 143 | `e72d3e9b05c3db0b`（解放者） | 爱国者右臂 200 发机炮 |
| `SOS Beacon` 行 59 | `22749a294788af66`（爱国者） | 爱国者左臂导弹巢 |
| `Reinforce` 行 57 / 138 | `4f3d304001614b38`（自动化军团地堡内容包） | 本轮敌人炮塔 |

### 10.3 判读表

| 观察 | 判定 |
|---|---|
| 模型出现、能瞄能打、**不被抢** | **✓ 敌人件在数据路线上也通了**（`Faction 1` + `Behaviour 658` + 包声明三件套齐） |
| 模型出现但**自己开火 / 被抢** | `AiEnemy` 大脑仍在跑（只改 behaviour 不够）⇒ 下一步处理 `AiEnemy`（该表 736 B 里 102 个非零字段，未解） |
| **紫问号** | 声明的那个包副本不是引擎实际要的那份 ⇒ 换 `0c37e83a8d16b67a` 再试 |
| **没有实体**（不是问号） | 与旧档"地堡机枪没实体"同症状 ⇒ 查组件集/阵营是否被引擎拒绝 |

### 10.4 ⚠ 全局副作用（这局要留意）

`Faction` 与 `Behavior` 都是**件级**改动，不是实例级：

- **世界上所有这型炮塔**（自动化军团地堡小口径自动炮）都会变成「超级地球阵营 + 玩家武器行为」⇒
  这一局如果刷到自动化军团地堡，**那门炮大概率不再打你**（阵营 1 = 友军）；
- 反过来也说明：**不要用这种改法做"只改一台"的实验**，要做单台只能走运行时。

回滚：

```bash
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin
python tools/dlbin_deploy.py restore --file generated_stratagem_settings.dl_bin
# 只回上一版（驾驶位 = 运输机炮塔）
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed "D:\mod\out\shuttle-slot2\generated_entities.shuttle-slot2.dl_bin"
python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin --sealed "D:\mod\out\exo45-arms-v2\generated_stratagem_settings.two-pkgs.sealed.dl_bin"
```

---

## 11 曳光/拖尾不显示：旧档早有答案 —— **缺第 3 个包**（2026-10-25）

### 11.1 症状与旧档的判据

§10 的敌人炮塔实机：**模型出现、能瞄能打、不被抢，但没有曳光弹拖尾**。
旧档 `D:\mod\docs\VEHICLE-MOUNT-ITEMS.md` §6.0 把跨阵营换件拆成**三层**，第 3 层正好对应这个症状：

| 层 | 缺这层时的症状 | 数据位置 | 旧档手段 |
|---|---|---|---|
| 1 件本体的包 | 紫色 `?` | 普查 `bundle-index.tsv` | 请求包 |
| 2 阵营 | 槽位**没有实体** | `FactionComponentData +0` | `--faction 1` |
| **3 弹丸效果** | **有伤害/命中/火花，看不到飞行段（曳光/拖尾）** | 弹丸行里的效果 id → 所在包 | 把**效果包**一起请求 |

并且旧档给过同一件（`9926876B2375A1BB`）**实测可用组合的必需包**：

> `4F3D304001614B38` · `0C37E83A8D16B67A` · **`FDF011DAECF24312`（弹丸拖尾粒子唯一所在包）**

⇒ 我们 §10 只声明了第一个，缺后两个；**尤其是 `FDF011DAECF24312`**（喷口/拖尾粒子）。

两个旧档细节也一并记下（查包时必踩）：

- 弹丸表里的效果 id 在**原始字节序**里与普查 hex **逐字节相同**，按 u64 小端读会全部查不到；
- 装特效包后旧档**连续开火崩过一次**（ntdll `0xC0000026`），原样字节复测又不崩 ⇒ 判为**偶发资源压力**；
  `--projfx`（换同包内更轻的粒子）只能算缓解。

### 11.2 本轮怎么补：三个包各占一个常驻口

`+0xA8` 是替换语义、一车一行只给 1 个口（[§9](../cases/EXO45-ARM-SWAP-26088801.md)），
所以只能用**账号常驻行**（默认栏里的 `Reinforce`、`SOS Beacon`）来声明。为了腾出干净的口，
本轮把 EXO-45 的双臂**恢复原版**（那两个外来包的需求随之消失）：

| 口（都是默认栏，关卡加载即读） | `+0xA8` | 作用 |
|---|---|---|
| `Reinforce` 行 57（`0x7084`） | `0x4F3D304001614B38` | 炮塔本体（76 资源：turret_small_autocannon + 关卡零碎） |
| `Reinforce` 行 138（`0x12524`） | `0x0C37E83A8D16B67A` | 指挥地堡顶部 + 炮塔（37 资源；旧档"必需包"之二） |
| **`SOS Beacon` 行 59（`0x73A4`）** | **`0xFDF011DAECF24312`** | **拖尾/粒子（1414 资源 / 68 MB / 200 particles，旧档称"唯一所在包"）** |

### 11.3 盘上内容（**✓ 已装，⚠ 待验**）

| 文件 | 大小 | sha256 | 内容 |
|---|---:|---|---|
| `D:\mod\out\enemy-turret-vfx\generated_entities.enemy-vfx.dl_bin` | 47,259,664 | **`5fcbb92bdfe25717`** | TD-110 槽 2 = 敌人炮塔；`Faction 8→1`；`Behaviour 90→658`；**EXO-45 双臂恢复原版** |
| `D:\mod\out\enemy-turret-vfx\generated_stratagem_settings.vfx3.sealed.dl_bin` | 82,440 | **`2b561a4bf1751f71`** | 上表三个包声明（其余全原版） |

门禁：换件 G1–G10 ×2、`plain_edit` G1–G6（diff 25 B / 3 处读回一致）；封箱后 `open-key` 回读逐字节一致；
Murmur64A 分别保持 `0x8E49771B181FFAA1`（实体）与 `0x04BBE33EF809862A`（战备）。

### 11.4 判读

| 观察 | 判定 |
|---|---|
| 曳光/拖尾出现 | **✓ 第 3 层补齐**，与旧档同一件、同一配方对齐 ⇒ 数据路线也能拿全 VFX |
| 仍无拖尾 | 换 `0c37e8…`/`fdf011…` 之外的候选包？先确认这件武器的弹丸行指向哪个效果 id（见旧档第 3 层读法） |
| 开火偶发崩溃 | 与旧档同款"资源压力"现象；`--projfx` 类缓解思路保留，别当修复 |

回滚：

```bash
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin
python tools/dlbin_deploy.py restore --file generated_stratagem_settings.dl_bin
# 回上一版（无曳光、但有 EXO 双臂）：
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed "D:\mod\out\enemy-turret\generated_entities.enemy-turret.dl_bin"
python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin --sealed "D:\mod\out\enemy-turret\generated_stratagem_settings.enemy-pkg.sealed.dl_bin"
```

---

## 12 复核：光明族光束炮头「借 40mm 站壳」这条老路线，现在还行得通吗（2026-10-25，**✓ 离线可行 / 实机未验**）

### 12.1 老路线是什么（旧档 + 记忆）

旧实验（`25480438`/`25988413` 时代，见工作区 `VEHICLE-MOUNT-ITEMS.md` §6.0b 与
`D:\mod\docs\` 下的记忆条目「光明族光束炮塔挂载实验」）：

1. 光明族炮头本身**有网格但位置错**（美术原点照臂关节设计，挂到车顶就缩在车底）；
2. 于是把它的**壳**（`UnitComponentData +0`）换成 **40mm 炮塔站的壳** ⇒ 模型变成 40mm 站、**光束从车顶炮管位置打出**；
3. 代价：**炮管不跟瞄准转**（`TurretComponentData` 的偏航/俯仰/枢轴是按原壳骨骼写的）；
4. 当时另试了原生车顶炮塔形态的件（`5D142C3A73EBC634` tank_turret_rocketlauncher）——位置对、**能转**，
   但那是"换件"不是"换壳"，光明族这件本身绕不过骨骼问题。
5. 另有两条副作用记档：**behaviour 改 658 会让这件 `STATUS_INVALID_DISPARITY` 崩**；
   特效包装上后偶发资源压力崩溃。

### 12.2 本 build 里这些件还在不在（**✓ 离线**）

`BeamWeaponComponentData`（`0xF0721C2C`）共 **23 行**，光明族三件都在，且字段齐：

| 件 | unit（壳） | Faction | Behaviour | 组件 |
|---|---|---|---|---|
| **`0xF196069E7E14C497`**（旧档里的 **F196**） | `0x4E342031A9D5C4F9` | **4**（光明族） | **284** | 20 个，含 `BeamWeapon` ✓ `Turret` ✓ `Wieldable`+`WeaponWielder` ✓ |
| `0x4E342031A9D5C4F9`（炮身/壳本体） | 自身 | 4 | 283 | 同上 |
| `0x7ACB4BD753B71DE0` | `0x4E342031A9D5C4F9` | 4 | 285 | 同上 |

壳与特效的包也都还在（目录里能查到）：

| 资源 | 包 | 备注 |
|---|---|---|
| `0x4E342031A9D5C4F9`（光明族壳） | `dd43ebba60a66968`（mesh 317 KB，很轻） | 借壳后**不再需要** |
| **`0x9872EEB31A5F88FD`（40mm 站壳）** | **`f6fb08cc02d24255`（基础共享包）** | 40mm 站实验一直能用 ⇒ 基本常驻 |
| **`0x63520CD25548948A`（光束粒子，旧档更正后的正解）** | `046d4441a6dae0a9` / `d448a6c8eb991f1a` | **要声明其中一个**，否则"无光束特效"复现 |

### 12.3 结论：**技术上可行，但两处硬伤照旧**

| 方面 | 现在能不能做 | 说明 |
|---|---|---|
| 借壳（模型 = 40mm 站、炮口位置对） | **✓ 能，且是纯数据**：`UnitComponentData +0` 一个 u64 改掉（`entity_field_set.py --block 0x4437574D --key 0xF196069E7E14C497 --field 0 --type u64 --value 0x9872EEB31A5F88FD`） | 比当年的 `--shell` 更干净 |
| 阵营 4 → 1 | ✓ 同 §10（`FactionComponentData +0`） | — |
| 光束特效 | ✓ 能，**但必须声明粒子包**（旧档"无特效"的根因） | 需要一个 `+0xA8` 常驻口 |
| **炮管跟瞄准转** | **✗ 不能**（老限制原样存在） | 转动绑壳骨骼；借壳必丢。除非改资产重挂骨骼，或改选原生车顶炮塔件 |
| 玩家可操控 | **⚠ 未知，但没有"658 必崩"的证据** | 旧档**没有**「这件改 658 会崩」的记录（见 §12.5 更正）；要试可直接照 §10 改 658，风险未知 |

### 12.4 如果要实际装一版，口位怎么排

现盘上三个常驻口已给敌人炮塔（`4F3D304001614B38` / `0C37E83A8D16B67A` / `FDF011DAECF24312`）。
光束实验**至少还要一个口**给 `046d4441a6dae0a9`。可选：

1. **二选一**：先把敌人炮塔那条线收起来，SOS 行改给光束粒子包（最省）；
2. **共存**：再找一个"进栏且 `+0xA8` 恒为 0"的行（例如带一发 Eagle 时的 `Eagle Rearm` 行 23）——
   这属于"进栏才读"，要玩家配合带对应战备；
3. 40mm 壳包（基础共享包）**不用声明**。

⇒ 一句话：**路线还在，但只能复现"位置对 + 有光束"，转动依旧拿不到**；
这条线的价值现在主要是"拿一个外观/演出"，不是"拿一门能转的光束炮"。

### 12.5 ✗ 更正（2026-10-25）：上一版说「658 在这件上会崩」是**误归因**

上一轮我写「这件上 behaviour 658 会 `STATUS_INVALID_DISPARITY` 崩」，来源是记忆库里的一条**实验摘要**
（「AIBEH 将行为 ID 从 80 替换为 658 导致 `STATUS_INVALID_DISPARITY` 崩溃，关闭 AIBEH 后不再崩」）。
回查一手报告（`D:\mod\g2-vehicle-loadout
econ\REPORT-xref-hmg-station-2026-10-18.md`）后，结论相反：

| 事实 | 出处 | 说明 |
|---|---|---|
| 全报告唯一一次 `0xC0000026 (STATUS_INVALID_DISPARITY)` 出现在**火箭炮塔 `5D142C3A73EBC634`** 上 | §86.3（L3915） | 触发条件是「**外加三个特效包 + 连续开火**」；该件在本 build 的 `Behaviour +0` 是 **79**（不是 80），**与光明族三件（283/284/285）无关** |
| 同一份字节**复测不崩**（只掉帧） | §86.6（L3944–3956） | 官方更正：崩溃是**偶发**，与**资源占用/特效负载**相关，**不是**某颗粒子或某个 behaviour 的确定性缺陷 |
| `--no-aibeh` 开关的由来是**装填实验**，不是躲崩 | §67.3（L3016） | 当时假设「装填由 behaviour tick 推进」，§68 用 `--no-aibeh` 把它**证伪**了 |
| 光束线里「保留原生 283（不换 658）」那步是为测**转动** | §85.3 | 没有记录任何崩溃 |

⇒ 正确表述：**「658 在光明族炮头上会崩」没有证据**；那条是记忆摘要里的错误归因（把「装特效包后偶发崩」记成了「改 behaviour 导致崩」）。
做光明族实验时可以直接按 §10 的办法改 658；已知的真实风险只有一条：
**外来件 + 大量特效 ⇒ 掉帧 ⇒ 偶发崩溃**（旧档 §86.6 的结论）。

---

## 13 实装：光明族光束炮头 + 40mm 壳 → 驾驶位烟幕槽（2026-10-25，**⚠ 待验**）

### 13.1 四处改动（全部纯数据）

| # | 层 | 改动 | 门禁 |
|---|---|---|---|
| ① | 挂载 | TD-110 行 125 **槽 2**：地堡炮塔 `0x9926876B2375A1BB` → **`0xF196069E7E14C497`**（光明族光束炮头） | G1–G10 ✓ `changed=[(125,2,…)]` |
| ② | 借壳 | `UnitComponentData +0`（`0x4437574D`）：`0x4E342031A9D5C4F9` → **`0x9872EEB31A5F88FD`**（40mm 站壳） | G1–G8 ✓ |
| ③ | 阵营 | `FactionComponentData +0`：**4 → 1** | G1–G8 ✓ |
| ④ | 行为 | `BehaviorComponentData +0`：**284 → 658**（按 §12.5 的更正：没有"658 必崩"的证据） | G1–G8 ✓ |

### 13.2 包声明（三个常驻口，敌人炮塔那条线已让出）

| 口 | `+0xA8` | 内容 |
|---|---|---|
| `Reinforce` 行 57 | `0x046D4441A6DAE0A9` | **光束粒子 + 材质/贴图**（1706 资源 / 72.8 MB / 248 particles）——旧档口径里"光束本体粒子"那一包 |
| `Reinforce` 行 138 | `0xF6FB08CC02D24255` | **40mm 站壳所在的共享包**（保险起见点名；前几轮 40mm 站实验里它本来就常驻） |
| `SOS Beacon` 行 59 | `0xDD43EBBA60A66968` | 光明族炮头自己的壳包（66 资源 / 12 MB；借壳后仍点名以免它的动画/挂点资源缺） |

不用声明的：`fdf011daecf24312`（曳光粒子，那是地堡炮塔的弹丸拖尾，本件用不到）。

### 13.3 盘上内容

| 文件 | 大小 | sha256 |
|---|---:|---|
| `D:\mod\out\beam-turret\generated_entities.beam.dl_bin` | 47,259,696 | **`c49fab20a65029e6`** |
| `D:\mod\out\beam-turret\generated_stratagem_settings.beam.sealed.dl_bin` | 82,440 | **`f1809694e1c19e0d`** |

✓ 已装；两文件封箱回读一致，Murmur64A 各自保持原值。

### 13.4 判读

| 观察 | 判定 |
|---|---|
| 模型 = **40mm 站**，光束**从炮管/车顶打出**，能开火有伤害 | **✓ 实机通过（2026-10-25）** —— 用户原话：「模型变成 40mm 站，光束从车顶炮管位置打出、有伤害」 |
| **炮管不跟瞄准转** | **预期如此**（§12.3 的硬伤，三次否证） |
| 有光束观感 | ✓ 粒子包声明生效 |
| 没有光束 | 粒子包不是引擎要的那份 ⇒ 换 `d448a6c8eb991f1a` |
| 紫问号 / 没实体 | 壳包或件包没驻留 ⇒ 先别开火（[EXO-ARM-VARIANTS §10.2](../tables/EXO-ARM-VARIANTS-26088801.md)） |

回滚：`restore` 两个文件；回上一版（地堡炮塔 + 曳光）：
`install --sealed D:\mod\out\enemy-turret-vfx\generated_entities.enemy-vfx.dl_bin` +
`install --sealed D:\mod\out\enemy-turret-vfx\generated_stratagem_settings.vfx3.sealed.dl_bin`。

---

## 14 收尾（2026-10-25）：这一整条线现在的能力边界

### 14.1 实机已证（**✓**）

| 能力 | 手段（全纯数据，不用 runtime） | 实机 |
|---|---|---|
| 把任意外来件装到任意载具挂载槽 | `MountComponentData` → `MountInfo.item`（`mount_table.py swap`，G1–G10） | ✓ 多次（40 mm 站 / 运输机炮塔 / 地堡炮塔 / 机甲臂 / 光明族炮头） |
| 让外来件的包驻留 | 战备行 `+0xA8`（**替换**语义）：载具自己的 **live 行**给 1 个口，其余借**账号常驻行**（`Reinforce` 57/138、`SOS Beacon` 59） | ✓ |
| 敌人件给玩家用 | `FactionComponentData +0`：`2/4/8 → 1`（Terminid/Illuminate/Automaton → Super Earth） | ✓（地堡炮塔、光明族炮头） |
| 把 AI 从炮塔上"领走" | `BehaviorComponentData +0` → **658**（玩家武器行为；当年 `AIBEH` 运行时那一步） | ✓（运输机炮塔、地堡炮塔、光明族炮头） |
| 补弹丸拖尾/光束特效 | 声明**特效包**（曳光 `fdf011daecf24312`、光束粒子 `046d4441a6dae0a9`） | ✓（两者都在本会话验过） |
| 借壳换外观/炮口位置 | `UnitComponentData +0` 指向目标壳（如 40 mm 站 `9872EEB31A5F88FD`） | ✓（光明族炮头） |
| 座位侧行为（准星/装填/相机夹制） | **数据层做不到**：属座位/相机/引擎代码侧 | ✓ 已分离（[MOUNT-SEATS §4.7](MOUNT-SEATS-26088801.md)） |

### 14.2 做不到 / 需要换思路（**✗**）

| 限制 | 原因 | 出路 |
|---|---|---|
| **借壳后炮管不跟瞄准转** | 转动/枢轴绑**壳的骨骼**（三次否证） | 改资产重挂骨骼；或换"原生车顶炮塔形态"的件（`5D142C3A73EBC634` 那类可两全） |
| 一台载具要 2 个以上外来包时只能借行 | `+0xA8` 是替换、live 行只有 1 个口 | 借常驻行（已验证 3 口够用）；或让外来件与原生件同包 |
| 只改一台（实例级） | 我们改的是**件级**行 | 走运行时（本 build 无稳定通道） |
| 缺包时"先开火试试" | 紫问号状态开火**会崩** | 先确认没有紫问号再开火（[EXO-ARM-VARIANTS §10.2](../tables/EXO-ARM-VARIANTS-26088801.md)） |

### 14.3 当前盘上状态（可直接玩）

| 文件 | sha256 | 内容 |
|---|---|---|
| `generated_entities.dl_bin` | `c49fab20a65029e6` | TD-110 槽 2（驾驶位）= 光明族光束炮头 + 40 mm 壳；阵营 1；行为 658。TD-110 槽 0/1 = 原版主炮/炮塔环；EXO-45 双臂 = 原版 |
| `generated_stratagem_settings.dl_bin` | `f1809694e1c19e0d` | `Reinforce` 57 → 光束粒子包 · 138 → 40 mm 壳共享包 · `SOS` 59 → 光明族壳包 |

回滚：`python tools/dlbin_deploy.py restore --file <两个文件>`
（`generated_entities.dl_bin` / `generated_stratagem_settings.dl_bin`）。

### 14.4 与 memmod 时代的对照（这条线的意义）

| 当年（memmod） | 现在（纯数据） |
|---|---|
| HD2Runtime `require_assets` 现场请包 | 战备行 `+0xA8` 声明 |
| `--faction 1` 运行时写阵营记录 | `FactionComponentData +0` 改一格 |
| `AIBEH` 写 behaviour + `PIN` 每帧兜底 | `BehaviorComponentData +0` 改一格，**一劳永逸** |
| `--shell` 运行时借壳 | `UnitComponentData +0` 改一格 |
| 特效靠 9 个包一起 warm | 只声明**真正用到的那几个**包（曳光 1 个、光束 1 个） |

⇒ **整条"外来件当玩家武器站"的路线已经全部从运行时搬到数据文件上**，且稳定性更好（无每帧写、无页保护、无 `HELD` 轮询）。
唯一搬不过去的是**座位侧能力**（准星/装填/相机夹制）与**骨骼绑定的转动**——这两条是引擎代码与资产层的事。

---

## 15 试装：Barrager Tank 车顶火箭炮塔（**唯一能同时拿位置+转动的外来件**，⚠ 待验）

### 15.1 这件是什么

`0x5D142C3A73EBC634` = 自动化军团 **Barrager Tank**（`0x63DF3D07B7424588` 行 94 槽 0）的**车顶火箭炮塔**
（资源名 `tank_turret_rocketlauncher`，百科名 `Ballistic Missile`）。28 组件：`Turret` ✓ `Wieldable`+`WeaponWielder` ✓
`ProjectileWeapon` ✓ `Backblast` ✓ `AiEnemy` ✓ 索敌三件套 ✓；`Faction +0 = 8`、`Behavior +0 = 79`；
壳 = 自身（包 `1a3dc966179bd5a4`，mesh 1.35 MB）；射界 yaw **±180** / pitch **−30…+90**；
弹丸 `+0 = 334`、rpm 1000、弹匣 1000。

**为什么选它**：旧档 §86.1 实测——不换壳、只做「包 + 阵营」，**位置正确 + 炮管跟着瞄准转**。
判据是「壳体是不是车顶炮塔形态」，它正是。

### 15.2 改动（3 处）

| # | 层 | 改动 | 门禁 |
|---|---|---|---|
| ① | 挂载 | TD-110 行 125 **槽 2**：光明族炮头 → **`0x5D142C3A73EBC634`** | G1–G10 ✓ |
| ② | 阵营 | `Faction +0`：**8 (Automaton) → 1 (Super Earth)** | G1–G8 ✓ |
| ③ | 行为 | `Behavior +0`：**79 → 658**（归玩家；不换的话 AI 会自己打） | G1–G8 ✓ |

### 15.3 特效包（旧档 §86.2 给的清单，本轮按 3 个口裁剪）

| 口 | `+0xA8` | 内容 | 覆盖 |
|---|---|---|---|
| `Reinforce` 行 57 | `0x1A3DC966179BD5A4` | 炮塔本体（4 资源 / 1.35 MB） | 模型 |
| `Reinforce` 行 138 | `0xFDF011DAECF24312` | **拖尾粒子 6094745A691467E1** + 200 particles + 156 textures / 68 MB | 曳光拖尾 **＋枪口/命中粒子**（那两个 id 在 9 个包里都有副本，含此包 ✓） |
| `SOS Beacon` 行 59 | `0x6A3EECFDDCE28FE8` | 导弹共享贴图 `6A6598587D4BC8F5`（680 textures / 33 MB） | 弹体贴图 |

**省掉的**：`318c6255be1254cd`（旧档 9 包里最小的那个，14.9 MB）——它的粒子在本轮已由 `fdf011…` 覆盖，
只可能缺它自己的材质/贴图 ⇒ 若枪口闪光观感不对，下一步把它顶上来（要腾口）。

⚠ 旧档同一件上的崩溃警告依然有效：**外来件 + 大量特效 + 连续开火 ⇒ 掉帧 ⇒ 偶发崩**；
真要稳，可把 `ProjectileSettings` 里该弹丸的拖尾换成同包自动炮粒子（旧档 `--projfx` 的做法）。

### 15.4 盘上内容（**✓ 已装**）

| 文件 | 大小 | sha256 |
|---|---:|---|
| `D:\mod\out\rocket-turret\generated_entities.rocket.dl_bin` | 47,259,720 | **`4f766dc7b2ec9496`** |
| `D:\mod\out\rocket-turret\generated_stratagem_settings.rocket.sealed.dl_bin` | 82,440 | **`add3788215d47d2d`** |

### 15.5 判读

| 观察 | 判定 |
|---|---|
| 模型 = 车顶火箭炮塔、**炮管跟着瞄准转** | ✓✓ **外来件两全**（这是本会话第一次在 TD-110 上拿到"会转的玩家炮塔"） |
| 有曳光/拖尾、导弹可见 | ✓ 特效包对齐 |
| 开火能打、伤害正常 | ✓ |
| 炮管不转 | 与旧档预测相反 ⇒ 说明 658 这个行为可能影响转动，退一步把 `Behavior` 回 79 再测 |
| 紫问号 | 某个包没驻留 ⇒ 先别开火 |

回滚：`restore` 两个文件；回上一版（光明族光束）：
`install --sealed D:\mod\out\beam-turret\generated_entities.beam.dl_bin` +
`install --sealed D:\mod\out\beam-turret\generated_stratagem_settings.beam.sealed.dl_bin`。

---

## 16 火箭炮塔"只有发射特效"（2026-10-25）：按 id 全都在已声明包里，缺的是**材质/贴图包**

### 16.1 症状

实机：**发射（枪口）特效有**，但 **弹体本身没有特效**、**命中爆炸特效也没有**。

### 16.2 离线对账：弹丸与爆炸引用的资源 id **全部**落在已声明的三个包里

弹丸 `334` 行（`generated_projectile_settings.dl_bin`，行基址 44 + i×272）：

| 字段 | 值 | 所在包 | 已声明 |
|---|---|---|---|
| `+0x10` 贴图 | `0x6A6598587D4BC8F5` | `6a3eecfddce28fe8` | ✓ |
| `+0x48` 拖尾粒子 | `0x6094745A691467E1` | `fdf011daecf24312` | ✓ |
| `+0x80` 弹体资源 | `0x9A030A53A7BD6C0A` | `1a3dc966179bd5a4`（本机包） | ✓ |
| `+0x90` 命中爆炸 | **410** | — | — |
| `+0x9C` 到期爆炸 | 0 | — | — |

爆炸 `410` 行（`generated_explosion_settings.dl_bin`，行基址 44 + i×152）：`+0x38` 粒子 = **`0xDCFF2CC15A3E5DE7` → `fdf011daecf24312`** ✓ 已声明；伤害行 472。

⇒ **按"id → 包"查，一个都不缺。** 所以缺的不是"某个 id 的包没加载"，而是旧档 §86.2/§86.4 里
**完整特效集是 4 个包**（`1a3dc966179bd5a4` + `fdf011daecf24312` + `6a3eecfddce28fe8` + **`318c6255be1254cd`**），
本轮为了塞进 3 个口，把最后一个省了 —— 它是**枪口/命中套的材质与贴图包**
（102 资源 / 14.9 MB：21 particles、24 textures、29 materials）。

粒子的**本体**在很多包里都有副本（例如枪口粒子 `7FE6533156BFA9AB` 有 **9 份**），
但**粒子引用的材质/贴图**只在自己那个包里 ⇒ 只声明"含粒子的包"不等于特效完整。

### 16.3 本轮补法：第 4 个口挂在 `Eagle Rearm`

| 口 | `+0xA8` | 备注 |
|---|---|---|
| `Eagle Rearm` **行 23**（字段 `0x2E18`） | **`0x318C6255BE1254CD`** | 原值 0 ⇒ 是空口；但**该行只在"带了 Eagle"时被读**（同文 R5-B 的条件常驻）⇒ 请确保战备里带一发 Eagle |

盘上：`generated_stratagem_settings.dl_bin` = **`d6c8416c62956f3b`**（entities 不变 `4f766dc7b2ec9496`）；
`plain_edit` G1–G6 全过，封箱回读一致。

### 16.4 判读与后续

| 观察 | 结论 / 下一步 |
|---|---|
| 命中爆炸特效出现（弹体也回来） | ✓ 就是省掉的那个材质包 ⇒ 收线 |
| 命中回来了、**弹体仍空** | 查 `6a3eecfddce28fe8`（33 MB 纹理包）是否真加载成功；不够就再补 `0692f83587540ae5` 或 `d2f2dd4a65a22617`（同样含枪口/命中粒子） |
| 两者都还空、且没有紫问号 | 说明特效是**路径解析**（包内路径）而不是 id 查表 ⇒ 只能把旧 9 包全上，或把该弹丸拖尾换成同包已验证粒子（旧档 `--projfx`） |
