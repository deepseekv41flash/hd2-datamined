# 锁定 / 制导武器（lock-on / seek）—— 武器线遗漏项（build 26088801）

> **状态：✓ 结项。** 数据表侧已验证 **两** 个可改旋钮：**锁定距离**（`SensorEye.distance`）与
> **锁定所需时间**（`GuidanceTarget.lock_on_target_time`）；锥角与可锁目标集合**在引擎侧**（五轮否证）。
> 本篇把 memmod 时期 `c9-seek` 那条线与当前 build 的**明文表**对上，给出可编辑落点、映射与已跑通的做法。
> 情报侧：`D:\mod\c9-recon\web-intel-hd2-lockon.md`（公开资料）· 当年写载物：`D:\mod\c9-seek-write\`（patch_3）。

---

## 0 一句话

「锁定」不是一张表，而是**三张组件表分工**：

| 你想要的 | 在哪 |
|---|---|
| **多远能锁** | `SensorEyeComponentData` → 行内 **`+0x00 distance`**（f32，米） |
| **多宽算锁上** | `GuidanceTargetComponentData` → **`+0x20 target_lock_dot`**（0.95 ⇒ 半角 18.19°） |
| **锁多久 / 丢多久** | 同上表 `+0x10 / +0x14 / +0x18` |
| **导弹怎么追** | `SeekingMissileComponentData` → 速度 / 加速度 / 转向 / PID |

三张表**都在 `generated_entities.dl_bin` 明文里**，走护甲那条「改字节 + 保内容哈希 + 重新封装」路线 ——
**不需要 memmod，重启不掉**。

---

## 1 三张表 + 两张辅助表（本 build 离线实测）

块头偏移是**文件绝对偏移**；`payload = 块头 + 28`。几何全部按 `slots×16 + rows×stride == payload` 校验通过。

| 组件 | type | 块头 | payload | 几何 |
|---|---|---|---:|---|
| **`SensorEyeComponentData`** | `0x14729B6A` | `0x00724D68` | 23,984 | 630 槽 + **316 行 × 44 B** |
| **`GuidanceTargetComponentData`** | `0x84957034` | `0x00785AC0` | 1,528 | 18 槽 + **10 行 × 124 B** |
| **`SeekingMissileComponentData`** | `0xBF3A6789` | `0x0072E460` | 8,816 | 58 槽 + **29 行 × 272 B** |
| `WeaponDataComponentData`（准星） | `0x88E4DBB1` | `0x0193CCE8` | 475,696 | 746 槽 + 374 行 × 1240 |
| `ProjectileWeaponComponentData`（投射物） | `0x45171B68` | `0x02CDE0B8` | 180,760 | 556 槽 + 279 行 × 616 |
| ~~`TargetingComponentData`~~（**不是锁定**，见 §6） | `0x2C0968D2` | `0x01932290` | 28,512 | 594 槽 + 297 行 × 64 |

**键都是实体 GUID**（不是行号）。行基址 = `payload + slots×16`。

文件级锚点（**必须保住**）：`MurmurHash64A(plaintext, seed 0xDEADBEEFABAD1DEA) == 0x8E49771B181FFAA1`，
明文 sha256 `dc6d52a1…`，47,259,396 B。

---

## 2 `SensorEyeComponentData` —— 锁定距离

行 44 B：

```
+0x00 distance(f32,米)  +0x04 peripheral  +0x08 back  +0x0C angle_h  +0x10 angle_v
+0x14 sight_node(u32)   +0x18 flags       +0x1C raycast  +0x20 eye_type
+0x24 ignore_inside_foliage(8.0)  +0x28 inside_foliage(0.5)
```

玩家能锁的 5 把（**5/5 与公开实测锁定距离吻合**）：

| 武器 | 行 | `distance` | `angle_h/v` | 有 `GuidanceTarget` 行 |
|---|---:|---:|---|---|
| P-92 Warrant | 202 | **60** | 20 / 20 | ✓ |
| P-33 Missile Pistol | 203 | **100** | 20 / 20 | ✓ |
| FAF-14 Spear | 305 | **300** | 20 / 20 | ✓ |
| StA-X3 W.A.S.P. | 306 | **300** | 20 / 20 | ✓ |
| MLS-4X Commando | 307 | **300** | 20 / 20 | ✓（激光制导，`requires_target_lock=0`） |

对照：**AR-23 / AR-2 / P-4 都没有 `SensorEye` 行** ⇒ 无锁定。全表 316 行里玩家物品只占 8 行，
其余是 AI 视觉（距离 8–2000、锥 20–360）。另外 3 行玩家物品（**G-50 Seeker 50 m** 等）有传感器但**没有 GT 行**
⇒ 形态上是自动索敌无人机/护卫类，不是锁定武器。

> ⚠ `angle_horizontal = 20` 是**全角还是半角未定**：AI 那批有 170/180，看起来是全角；若全角则 ±10°，
> 比 dot 的 18.19° **更窄** ⇒ 两者谁先卡死，未分离过。

---

## 3 `GuidanceTargetComponentData` —— 锥角与时序

行 124 B（声明顺序 + 自然对齐；用 `target_node` 默认值 `0xBCCF91E5` 定位）：

```
+0x00 always_active(u8)  +0x01 use_target_node(u8)  (+0x02 补齐 2B)
+0x04 target_node(u32, 默认 0xBCCF91E5)   +0x08 priority(f32)
+0x0C owner_priority(100)  +0x10 lock_on_target_time  +0x14 lost_target_time
+0x18 lock_lost_target_time  +0x1C requires_target_lock(u8)
+0x20 target_lock_dot(0.95)  +0x24 target_crosshair_scale(1.75)  +0x28 tracking_loop_start(u32)
```

本 build 全表 9 行（键 = 武器 GUID）：

| 武器 | 行 | `lock_on_target_time` | `lost_target_time` | `lock_lost_target_time` | `requires_target_lock` |
|---|---:|---:|---:|---:|---:|
| P-92 Warrant | 4 | **0.10** | 0.10 | 2.00 | 1 |
| P-33 Missile Pistol | 5 | 0.75 | 0.15 | 2.00 | 1 |
| FAF-14 Spear | 6 | 1.00 | 0.15 | 2.00 | 1 |
| StA-X3 W.A.S.P. | 7 | 0.50 | 0.10 | 2.00 | 1 |
| MLS-4X Commando | 8 | 2.00（默认） | 1.00 | 1.00 | 0 |

**★ 关键结论：`target_lock_dot` 9 行全是 `0.95`、`target_crosshair_scale` 9 行全是 `1.75`**
⇒ **锁定锥角不是逐武器调的**，是统一默认值。
`acos(0.95) = 18.19°` 半角（全锥 36.4°）。
（这也解释了当年 c9 把 `cone` 从社区惯例 12° 改成 18° 为什么"感觉对了" —— 18 正好贴着原版 18.19°。）

---

## 4 `SeekingMissileComponentData` —— 制导参数（映射已建）

键是**投射物实体**，不是武器。映射链：
**武器 GUID → `ProjectileWeaponComponentData` 行 `+0x28`（u64 投射物实体）→ `SeekingMissile` 行**
（4 把锁定武器的 `+0x28` 全部命中该表键 —— 这条链是**实证**，不是猜的。）

| 武器 | SM 行 | Starting / Min / Preferred 速度 | Accel | MaxAngle | Min/Max TurnSpeed | P / I / D |
|---|---:|---|---:|---:|---|---|
| P-92 Warrant | 4 | 90 / 90 / 90 | 200 | 45 | **30 / 30** | 0.01 / 1.0 / 1e-4 |
| FAF-14 Spear | 7 | 10 / 10 / 100 | 200 | 45 | 10 / 13 | 0.01 / 1.0 / 1e-4 |
| StA-X3 W.A.S.P. | 9 | 10 / 10 / 100 | 200 | 45 | 15 / 18 | 0.01 / 1.0 / 1e-4 |
| MLS-4X Commando | 10 | 30 / 75 / 120 | 200 | 45 | 2 / 12 | 0.5 / 1.0 / 1e-4 |

字段偏移（沿用社区 `filediver` schema，本 build 未逐项验）：`MaxLifetime +0x40`、
`Starting/Minimum/PreferredSpeed +0x44/+0x48/+0x4C`、`Acceleration +0x50`、`MaxAngleToTarget +0x54`、
`Min/MaxTurnSpeed +0x58/+0x5C`、`P/I/D +0x60/+0x64/+0x68`、`TargetUpdateInterval +0x6C`。

> ⚠ 教训（当年 §94）：**schema 默认值 ≠ 逐行值**。曾据默认 `min_turn_speed=1` 推断"P-92 转得慢"，
> 实测是 **30/30**（全表最快）—— 差点把它改钝。本页按逐行实测记录。

---

## 5 怎么写（工具已存在，不用新写）

底层原语 **`tools/entity_field_set.py`**：给组件 type + 实体键 + 行内偏移，块定位 / 行定位 / 尾部宿主 / 门禁全自动。

```bash
# 看一行
python tools/entity_field_set.py show --block 0x14729B6A --key 0xCF8934FF6567A42D --width 44

# 改一个字段（f32：P-92 锁定距离 60 → 300）
python tools/entity_field_set.py set --block 0x14729B6A --key 0xCF8934FF6567A42D \
    --field 0x0 --type f32 --value 300 --expect-old 60 --out out/X.plain
```

**门禁 G1–G9**（任一不过就不写文件）：长度 = 原长+pad+8 · 差异 ⊆ 字段∪末块尺寸∪校正字 ·
**重算 Murmur == 原值** · 字段读回 == 目标 · 旧值 == 期望 · 容器重解析自洽 · 校正字 8 对齐 · 追加区除校正字全 0。

封装 / 部署 / 回滚：

```bash
python tools/dlbin_seal.py seal-key out/X.plain --key refs/dlbin/keys/recipient.pk --out out/generated_entities.dl_bin
python tools/dlbin_seal.py open-key <盘上文件> --key refs/dlbin/keys/recipient.sk --out out/readback.plain   # 回读验证
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed out/generated_entities.dl_bin
python tools/dlbin_deploy.py restore --file generated_entities.dl_bin
```

**为什么必须保住哈希**：`seal-key` 每次新随机 ephemeral，封包字节必然不同（正常）；但**明文的内容哈希**
要等于 `0x8E49771B181FFAA1`。工具做法 = 末块 payload 尺寸 += pad+8、文件尾追加 pad+8 零字节、
再把 8 字节校正字解在尾部 —— 锚点不变、容器重解析自洽。
封装模型与陷阱见 [DLBIN-SEALED-BOX](../engine/DLBIN-SEALED-BOX.md)、
文件路线全流程见 [FILE-ROUTE-WORKFLOW](../cases/FILE-ROUTE-WORKFLOW-26088801.md)。

---

## 6 ✗ 更正：`TargetingComponentData` 不是锁定

本篇早前版本把 `TargetingComponentData`（`0x2C0968D2`，594 槽 / **297 行 × 64 B**）当成锁定主数据。**两点更正**：

| 项 | 错的 | 对的 |
|---|---|---|
| 块头偏移 | `0x1932294`（那是 `LDLD` 魔数位置） | **`0x1932290`** |
| 语义 | 锁定 / 炮塔归零 | **AI / 角色索敌瞄准** |

证据：该表 297 个键里 **5 把锁定武器一个都不在**；能解出名字的键全是角色实体（`content/fac_bugs/cha_*`），
行值是 `25.0 / 0.5 / 5.0 / 90.0 / 180.0` 这类**角色视角 / 索敌**参数，与「距离 / 锥角 / 锁定时序」无一对应。
⇒ 改它不会改玩家锁定，别按名字误伤。

`crosshair_type`（**本 build 在 `WeaponDataComponentData +0x194`**，值 **16 = Javelin**；旧 build 行宽 1232 时是 `+0x190`，
本 build 行宽 1240 后段整体后移 4 B —— 实测 P-92/P-33/Spear/WASP = 16、`MLS-4X Commando` = 0、AR-23 = 4）仍然成立，但它只给**准星样式**，
**不给锁定能力** —— 真正的开关是 `SensorEye.distance` + `GuidanceTarget` 行。

---

## 7 单变量实验记录

### run 1 —— 锁定距离（**✓ 实机通过**）

| 项 | 值 |
|---|---|
| 变量 | **P-92 Warrant `SensorEyeComponentData +0x00 distance`：60.0 → 300.0** |
| 只改了 | 3 字节（字段高字节 ×2 + 末块尺寸字段），其余与基线逐字节相同 |
| 离线门禁 | G1–G9 全 PASS；哈希 `0x8E49771B181FFAA1` 不变 |
| 封装 | `out/lockon-1/generated_entities.dl_bin`，47,259,456 B，sha256 `0c5a5f49…` |
| 盘上回读 | live sha256 == 我们的密文；解封逐字节一致；字段读回 **300.0** |
| **实机** | **✓「能锁上超过 60 m 的」** |
| 原版备份 | `D:\mod\backups\dlbin-deploy\game\generated_entities.dl_bin`（`cac4a228…`） |

⇒ **`SensorEye.distance` 就是锁定距离**；且**引擎接受重新封装的实体表**（详见
[ENTITIES-TABLE-LIVE-EDIT](../cases/ENTITIES-TABLE-LIVE-EDIT-26088801.md)）。
实测单位是米、写入值直接生效（60 → 300 后跨过 60 m 仍能锁）。

### run 2 —— 锥角（**已装盘，待实机**）

在 run 1 基础上**只加一个变量**（距离保持 300，便于对照"同一个瞄偏量"）：

| 项 | 值 |
|---|---|
| 变量 | **P-92 `GuidanceTargetComponentData +0x20 target_lock_dot`：0.95 → 0.50** |
| 含义 | 锁定判定半角 `acos(dot)`：**18.19° → 60°**（全锥 36.4° → 120°） |
| 范围 | **只改 P-92 那一行**（GT 行 4）；另 8 行仍 0.95 ⇒ 其它锁定武器不受影响 |
| 离线 | G1–G9 全 PASS；哈希不变；封装 sha256 `6501d324…`（47,259,464 B） |
| 盘上回读 | 解封 == 我们的明文；P-92 `distance=300` / `lock_dot=0.5`；**对照项未动**（P-33 仍 100、Spear 300 且 dot 0.95） |

**实机结果（用户原话）**：「偏得比较多也能锁，但是**锁定进度会卡在一开始，无法锁成功**。」

| 观察 | 推论 |
|---|---|
| 偏得多也出现可锁提示（锁定圈 / 候选框） | **✓ `target_lock_dot` 是运行期判据**，放宽后候选范围真的变宽了 |
| 进度条卡在起始、锁不成功 | **✗ 单靠 dot 不够** —— 存在**第二道门禁**：候选 ≠ 被传感器看见 |

⇒ 两级门禁模型：**`target_lock_dot` 决定「算不算候选」，`SensorEye.angle_h/v` 决定「能不能持续看见并攒进度」**。
这正好解释当年 c9 的「明明瞄着却不锁」：候选框出来了（dot 放行），但传感器看不全（±10°），进度攒不起来。

### run 3 —— 传感器视锥（**已装盘，待实机**）

dot 退回**原版 0.95**（去掉 run 2 那个「候选过多」的混淆因素，基线回到 run 1），只动视锥：

| 项 | 值 |
|---|---|
| 变量 | **P-92 `SensorEyeComponentData +0x0C angle_h` 与 `+0x10 angle_v`：20 → 90**（一个逻辑变量：传感器视锥） |
| 含义 | 若 20 是**全角** ⇒ ±10° → ±45°；若是**半角** ⇒ ±20° → ±90° |
| 离线 | 两次链式 set，G1–G9 全 PASS；哈希不变；封装 sha256 `61f40836…`（47,259,472 B） |
| 盘上回读 | `distance=300 / angle_h=90 / angle_v=90 / lock_dot=0.95`；对照 P-33 仍 `100 / 20` |

**实机结果**：「还是跟上次一样」✗ —— 且与 run 2 **表现一致**（显示范围 > 可锁范围，两个边界都没动）。

| 推论 | 内容 |
|---|---|
| **`SensorEye.angle_h/v` 不是锁定门禁** | 20 → 90（4.5×）无任何变化 |
| **`target_lock_dot` 也不是这两个边界的控制量** | run 3 把它退回 0.95 后表现仍与 run 2 相同 ⇒ run 2 的"显示变宽"要降级为未定 |

⚠ 因此前面「两级门禁 = dot 放候选 / SensorEye 给进度」的模型**作废**。目前能确定的只有：
`dot` 与 `SensorEye.angle` 都**不**控制「可锁范围」。

### run 4 —— 制导最大角（**已装盘，待实机**）

按用户建议「角度改大点、比较明显」，取**唯一还没碰过的角度字段**：

| 项 | 值 |
|---|---|
| 变量 | **P-92 `SeekingMissileComponentData +0x54 MaxAngleToTarget`：45 → 120** |
| 其余 | 全部退回原版（`cone 20/20`、`dot 0.95`、`xhair 1.75`），只保留已证的 `distance 300` |
| 离线 | G1–G9 全 PASS；封装 sha256 `db72fd44…`；盘上回读 `max_angle=120`、其余原版 |

**实机结果**：「还是没变」✗ —— 也不是它（至少不是发射前锁定门禁）。

### ★ run 2 / run 3 的设计缺陷（第三轮之后才看出来）

前三轮全部没变化，把三轮排在一起看，出现一个自洽得多的解释：**锁定锥 = 两个角取小（合取）**。

| 轮次 | `dot` 给的锥 | `SensorEye.angle` 给的锥 | 有效锥 = min | 现象 |
|---|---|---|---|---|
| 原版 | 18.19° | 20° | **18.19°** | 基准 |
| run 2 | 60° | 20° | **20°** | ≈没变 ✓ 可解释 |
| run 3 | 18.19° | 90° | **18.19°** | 完全没变 ✓ 可解释 |
| run 4 | —（改的是 SK，发射后参数） | — | 不变 | ✓ 可解释 |

⇒ **每轮都只放宽了一道闸，另一道始终卡着**，所以"改不动"。若这个模型成立，必须**同时**放宽。

### run 5 —— 两道闸一起开（**已装盘，待实机**）

| 字段 | 原值 → 新值 |
|---|---|
| `GuidanceTargetComponentData +0x20 target_lock_dot` | 0.95 → **0.50**（18.19° → 60°） |
| `SensorEyeComponentData +0x0C/+0x10 angle_h/v` | 20 → **90** |
| `SensorEyeComponentData +0x00 distance` | 60 → **300**（run 1 已证，保持） |

三者算**一个逻辑变量**（同一个"锁定锥"的两个约束）。封装 `067db656…`，盘上回读
`dist=300 / cone=90/90 / dot=0.5`；对照 P-33 仍 `100 / 20 / 0.95`。

**实机结果**：「仍旧一模一样」✗ —— 合取模型也**否证**。

⇒ **锁定锥角不在这三张表里**（`GuidanceTarget` 的 `dot` / `SensorEye` 的 `angle_h/v` / `SeekingMissile` 的
`MaxAngleToTarget` 全部无效）。它大概率写在 `game.dll` 里，或由准星/HUD 几何决定。

### run 6 —— ✗ 取消（不执行）

原计划把 `SensorEye +0x04 peripheral` / `+0x08 back` 从 `-1` 改成 90。**放弃，理由是值语义**：

| 观察 | 推论 |
|---|---|
| 这两格原值都是 **`-1`**；同表别处 `-1` 也表示"不设/用默认"（如 Spear 的 `SeekingMissile +0x0C time_to_enable_guidance = -1`） | `-1` 是**哨兵值**，不是"某个角度" |
| 若哨兵含义是"**不设限**" | 它本来就已经是**无限**，写成 90 反而是**收窄** |
| 若哨兵含义是"**未启用**" | 启用一个从没启用过的周边视野格，**没有任何证据**指明它参与锁定判定 |

两种语义下这一轮都拿不到可解释的结果 ⇒ **不值得占用一局**。

### run 7 —— 锁定速度：**Spear `lock_on_target_time` 1.00 → 0.05**（**已装盘，待实机**）

锥角结项后，改做**同一张表里仍在数据侧**的旋钮：锁定时序。

| 项 | 值 |
|---|---|
| 变量 | **FAF-14 Spear `GuidanceTargetComponentData +0x10 lock_on_target_time`：1.00 → 0.05** |
| 挑它的理由 | 5 把锁定武器里它最慢（P-92 `0.10` · P-33 `0.75` · **Spear `1.00`** · WASP `0.50` · Commando `2.00` 但 `requires_target_lock=0`）⇒ **20× 差最明显** |
| 其余 | 只保留已证的 `P-92 distance 300`；`lost_target_time / lock_lost_target_time / dot / xhair / angle / max_angle` 全原版 |
| 离线 | G1–G9 全 PASS（diff 5 B）；哈希 `0x8E49771B181FFAA1` 不变；封装 sha256 `97b8e371…` |
| 盘上回读 | Spear `lock_t=0.05`、`lost_t=0.15`、`locklost_t=2`、`req_lock=1`；**其余四把时序未动**（0.10 / 0.75 / 0.50 / 2.00） |

**实机结果（用户原话）**：「**Spear 锁定更快，几乎是一瞬间**」✓

⇒ `lock_on_target_time` **就是锁定所需时间**（秒）。1.00 → 0.05 后从「约 1 秒」变成「一瞄即满」。
这一条同时排除了另外两种可能：它不是「保持时间」，也不是「引擎侧写死」。

---

## 7.5 这条线的能力边界（**已收敛，结项**）

| 能力 | 字段 | 判定 |
|---|---|---|
| **锁定距离** | `SensorEyeComponentData +0x00 distance` | **✓ 实机可改**（P-92 60→300，能锁 60 m 以外） |
| **锁定所需时间** | `GuidanceTargetComponentData +0x10 lock_on_target_time` | **✓ 实机可改**（Spear 1.00→0.05，一瞄即满） |
| 锁定锥角 | `GuidanceTarget +0x20 target_lock_dot`（0.95→0.5） | **✗ 否证** |
| 锁定锥角 | `SensorEye +0x0C/+0x10 angle_h/v`（20→90） | **✗ 否证** |
| 锁定锥角 | 上面两者**同时**放宽（合取模型） | **✗ 否证** |
| 锁定锥角 | `SeekingMissile +0x54 MaxAngleToTarget`（45→120） | **✗ 否证**（那是发射后制导限制） |
| 可锁目标集合 | 标签位图 | **✗ 不可读亦不可改**（见 §10） |
| 每把武器的目标过滤（Spear 只锁建筑/精英 vs WASP 锁大多数） | `SeekingMissile +0x00 TargetingMode`（P-92/Spear/WASP 全 = **2**，Commando = **1** 激光） | **✗ 不在数据里**（同一 mode 内过滤不同） |

**结论：数据表能改「距离」与「锁定速度」；改不动「锥角」与「目标集合」**（后者在引擎侧，五次否证后不再投入）。

> 这一条已作为 **C 档样板**写进 [PLAYBOOK §6.1](../cases/PLAYBOOK-LUA-MOD-TO-DLBIN.md)：
> 卡点（L4）+ 最接近替代（距离 ✓ 实机 / 时间 ✓ 实机）+ 残余差距。

### 实验台账（7 轮 · 2 ✓ / 5 ✗）

| run | 变量 | 结果 |
|---:|---|---|
| 1 | `SensorEye.distance` P-92 60 → **300** | **✓ 实机**：能锁 60 m 以外 |
| 2 | `target_lock_dot` 0.95 → 0.5 | ✗ 无变化 |
| 3 | `SensorEye.angle_h/v` 20 → 90 | ✗ 无变化 |
| 4 | `SeekingMissile.MaxAngleToTarget` 45 → 120 | ✗ 无变化 |
| 5 | run 2 + run 3 同时（合取模型） | ✗ 无变化 |
| 6 | `peripheral` / `back` -1 → 90 | ✗ **取消**（`-1` 是哨兵值，改它无意义） |
| 7 | `lock_on_target_time` Spear 1.00 → **0.05** | **✓ 实机**：一瞄即满 |

---

---

## 8 三态

| 结论 | 态 |
|---|---|
| 三张表的块头 / payload 几何 / 行 stride 全部离线校验通过（`slots×16+rows×stride==payload`） | **✓ 离线** |
| 5 把锁定武器的 `SensorEye.distance` = 60/100/300/300/300，非锁定武器**无该行** | **✓ 离线** |
| 武器 → `ProjectileWeapon +0x28` → `SeekingMissile` 行 的映射（4/4 命中） | **✓ 离线** |
| `target_lock_dot` 全表统一 0.95（锥角非逐武器） | **✓ 离线** |
| `TargetingComponentData` 是角色索敌、与玩家锁定无关 | **✓ 离线** |
| 改 `SensorEye.distance` 能改变实机锁定距离 | **✓ 实机**（P-92 60→300，能锁 60 m 以外） |
| 改 `lock_on_target_time` 能改变实机锁定速度 | **✓ 实机**（Spear 1.00→0.05，一瞄即满） |
| 引擎接受改过并重新封装的 `generated_entities.dl_bin` | **✓ 实机**（同上；见 [案例](../cases/ENTITIES-TABLE-LIVE-EDIT-26088801.md)） |
| `target_lock_dot` 是运行期判据（放宽后候选范围变宽） | **✓ 实机**（run 2） |
| ~~锁定需第二道 = 传感器视锥~~ | **✗ 否证**（run 3：20→90 无变化） |
| `MaxAngleToTarget` 是发射前锁定门禁 | **✗ 否证**（run 4：45→120 无变化） |
| 锁定锥 = `dot` 与 `SensorEye.angle` 的**交集**（取小） | **✗ 否证**（run 5 同时放宽仍无变化） |
| **锁定锥在引擎侧**（不在 `GuidanceTarget` / `SensorEye` / `SeekingMissile`） | **✓ 五轮否定后的结论** |
| `angle_h/v = 20` 是全角还是半角 | **— 不追**（run 3/5 证明它不参与锁定判定，单位已无意义） |
| `angle_h/v` 与 `dot` 谁卡「完成锁定」 | **✗ 不适用**（两者都不控制可锁范围） |
| `requires_target_lock` / `tracking_loop_start` 的实机语义 | **⚠ 未证**（不影响已得结论） |
| 能否让**非锁定武器**获得锁定（需同时加 `SensorEye` 行 + `GT` 行 + `crosshair=16`，≥3 变量） | **⚠ 未试** |
| `Tag_CanBeLockedOn` 能否扩大"可被锁"的目标集合 | **✗ 不可行**（标签是 4352 bit 位图，无位↔名映射，见 §10） |

---

## 9 结项：装机状态 / 回滚 / 后续

### 9.1 当前装机（2026-10-24，`generated_entities.dl_bin`）

| 改动 | 原值 → 新值 | 实机 |
|---|---|---|
| P-92 Warrant `SensorEye +0x00 distance` | 60 → **300** | ✓ 能锁 60 m 以外 |
| FAF-14 Spear `GuidanceTarget +0x10 lock_on_target_time` | 1.00 → **0.05** | ✓ 一瞄即满 |
| 其余全部 | 原版（`dot 0.95`、`xhair 1.75`、`cone 20/20`、`max_angle 45`、其它四把的时序） | — |

- 明文 sha256 `642b6e4c…`、封包 sha256 `97b8e371…`、内容哈希锚点 `0x8E49771B181FFAA1`
- 原版备份：`D:\mod\backups\dlbin-deploy\game\generated_entities.dl_bin`（`cac4a228…`）
- 回滚：`python tools/dlbin_deploy.py restore --file generated_entities.dl_bin`

### 9.2 已结项、别再花局验的

| 项 | 判定 |
|---|---|
| 锁定距离 | **✓ 实机可改**（run 1） |
| 锁定所需时间 | **✓ 实机可改**（run 7） |
| 锁定锥角 | **✗ 四路全否证**（`dot` / `SensorEye.angle` / 两者合取 / `MaxAngleToTarget`）⇒ 引擎侧 |
| 可锁目标集合 | **✗ 不可读不可改**（§10：标签是 4352 bit 位图，无位↔名映射） |
| 给非锁定武器加锁定 | **✗ 不可行**：memmod 时代是**我们自己写锁定逻辑**（Lua 轮询目标 + 写瞄准），不是引擎给的；数据表无等价通道（用户 2026-10-24 确认） |

### 9.3 若还要继续（都是独立能力，各自单变量）

| # | 能做什么 | 备注 |
|---|---|---|
| 1 | 其余三把的 `distance` / `lock_on_target_time` 一起调 | 做成「全系远程 + 瞬锁」成品；P-33 100→300、WASP 0.50→0.05 |
| 2 | `SeekingMissile` 转向 / 速度 / 加速度 | **必须挑 Commando（turn 2/12）或 Spear（turn 10/13）**；P-92 已是全表最快（30°/s）改不出差别 |
| 3 | `lost_target_time` / `lock_lost_target_time` | 掉锁后能维持多久；两把枪的 2.0 s 可能可调 |

## 10 锁定「目标列表」在明文表里吗？—— **不在**（✓ 已查清）

结论：**没有名单**。可锁性以**位图**形式存在，但没有标签名、也没有「位 ↔ 名字」的对应表。

### 10.1 证据链

| # | 事实 | 态 |
|---|---|---|
| 1 | `Tag_CanBeLockedOn` 的两个候选 32 位哈希（记忆值 `0x07F0ADE3`、djb2 计算值 `0x07F0C2E8`）在整份 47 MB 明文里**出现 0 次** | **✓ 离线** |
| 2 | 标签表 `TagComponentData`（`0x6E8B3849` @`0x326D0`）：1134 槽 + **567 行 × 544 B**（501 行非空），几何由 typelib 直读 | **✓ 离线** |
| 3 | 行 = **512 B + 32 B = 4352 bit 位图**；行内值为 `32 / 131072 / 134217728` 等**纯 2 的幂** ⇒ 位域，不是 id 列表 | **✓ 离线** |
| 4 | 55 张明文设置表里**没有** tag / 标签定义表（`ls | grep -i tag` 只有 stratagem 两张无关表） | **✓ 离线** |
| 5 | 567 个标签行里能被 `srkit-names` 命名的只有 **95** 个；敌人侧几乎不在表中（`Charger` 3 行、`Scavenger` 2、`Shrieker` 2、`Hulk` / `Devastator` / `Factory` **0**） | **✓ 离线** |

### 10.2 这条对能力边界的意义

- **读不到**：无法从明文里读出"哪些实体可被锁"——位图里只有"第几位"，而位↔名映射缺失。
- **改不了**：给某物加"可锁"必须在 4352 位里找对那一位；映射缺失 ⇒ 只能纯试错，且没有可验证的判据。
- **另一条也堵着**：每把武器的目标过滤（Spear 只锁建筑/精英 vs WASP 锁大多数）也不在
  `SeekingMissile +0x00 TargetingMode` 里 —— 4 把发射器 P-92/Spear/WASP 都是 mode **2**、Commando 是 **1**（激光），
  同一 mode 内过滤不同 ⇒ 过滤在引擎侧。

⇒ **锁定这条线上的数据表能力边界：距离 ✓ 可改（实机已证）；锥角 ✗；目标集合 ✗（不可读亦不可改）。**
