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
