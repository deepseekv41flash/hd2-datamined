# 蓄力武器（charge-up）—— 组件表定位与字段图（build 26088801）

> **状态：✓ 主线打通。** 蓄力时间 ✓ 实机（ARC-3 一按即放）· 过蓄伤害 = `DamageMin→DamageOver` 插值 ·
> 过蓄自毁爆炸行已定位（Railgun type 326 → 伤害类型 362）且 **✓ 实机**（过蓄不伤己）·
> 射击模式另有专篇 [WEAPON-FIRE-MODES](WEAPON-FIRE-MODES-26088801.md)。
> 相关：[LOCKON-TARGETING](LOCKON-TARGETING-26088801.md)（锁定线）· 社区结构来源：`xypwn/filediver`
> `datalibrary/weapon_charge_component.go`

---

## 0 一句话

蓄力在 **`WeaponChargeComponentData`**（`0xEAC335A1` @ 明文 **`0x0075E5D0`**）里，
每把武器一行 **216 B**，里面是 **三档蓄力状态（Min / Full / Over）× {蓄力时间, 弹丸类型}** + 一整组
**蓄力倍率**（速度/伤害/穿甲/电弧距离/分裂/链数）+ 音效与材质句柄。
**「能不能不蓄满就开火」直接对应 `Min` 档的 `ProjType` 是否为 0**（见 §2）。

---

## 1 表的几何

| 项 | 值 |
|---|---|
| 组件类型 | `WeaponChargeComponentData` = `0xEAC335A1`（旧 build schema 与本 build 同值） |
| 块头 | `0x0075E5D0`（`payload = 块头 + 28`） |
| payload | 3,456 B = **20 槽 × 16 + 11 行 × 216** |
| 行 stride | **216 B**（与社区 `WeaponChargeComponent` 的结构尺寸**逐字节吻合**） |
| 键 | 武器 GUID（不是行号）；行基址 = `payload + 20×16` = `0x0075EC6C`… 见 §4 |

> 同族还存在 `WeaponHeatComponentData`（`0x4C981CD9` @`0x1A8E660`，60 槽 / 31 行 × 592）
> 与 `WeaponWindUpComponentData`（`0x84CE7EEE` @`0xC5BB8`，18 槽 / 10 行 × 36）——
> 前者是激光类"过热"，后者是前摇/摇把，**都不是**蓄力；查蓄力只看 Charge 表。

---

## 2 行内字段图（216 B，已用数据逐项校准）

```
+0x00 ChargeStateSetting[0]  Min 档   ┐
+0x18 ChargeStateSetting[1]  Full 档  ├ 每档 24 B：
+0x30 ChargeStateSetting[2]  Over 档  ┘  +0x00 ChargeTime(f32,秒) +0x04 ProjType(u32)
                                         +0x08 ProjectileParticle(u64) +0x10 ThinHash(u32) +0x14 pad

+0x48 ProjectileMultipliers = 12 × f32（48 B）
        SpeedMin / SpeedOver · DamageMin / DamageOver · PenetrationMin / PenetrationOver
        DistanceMin / DistanceOver · ExtraArcSplitsMin / Over · ExtraArcChainsMin / Over

+0x78 ChargeStartSoundID      +0x7C ChargeStopSoundID
+0x80 ReadyToFireSoundID      +0x84 DangerOverchargeSoundID
+0x88 ChargeMesh  +0x8C ChargeMaterial  +0x90 ChargeVariable   (+0x94 pad)
+0x98 ChargeUpMuzzleFlash(u64)  +0xA0 ChargeUpMuzzleFlashLoop(u64)
+0xA8 ChargeAnimID  +0xAC ChargeEndAnimID  +0xB0 ChargeRateAnimID  +0xB4 SpinSpeedAnimID
+0xB8 AutoFireInSafety(u8)   ← 关掉 = 按住扳机能一直保持蓄力
+0xB9 ExplodesOnOvercharged(u8)
+0xBC ExplosionAudioEvent(u32)  +0xC0 UnknownFloat(f32)
+0xC4 DryFireAudioEvent(u32)    +0xC8 ExplodeType(u32)
+0xCC StateValue.State(u32)     +0xD0 StateValue.Value(f32)   (+0xD4 pad) → 合计 216 ✓
```

**校验方式**：`0xB8` 处四把枪读出 `u32=256` ⇒ 字节 `0xB8=0`、`0xB9=1`
（`AutoFireInSafety=0`、`ExplodesOnOvercharged=1`），与社区 bool 顺序一致；结构总长 216 = 我们的 stride。

---

## 3 ★ 关键相关性：「要不要蓄满」= `Min.ProjType` 是否为 0

`ChargeStateSettings` **每一档都有自己的 `ProjType`**。实测（`+0x04` / `+0x1C` / `+0x34`）：

| 武器 | Min 档 type | Full 档 type | 玩家行为（用户描述） |
|---|---:|---:|---|
| **PLAS-101 Purifier** | **131** | 301 | **不蓄满也能开火** ✓ |
| PLAS-15 Loyalist | **72** | 346 | 能（同类三档弹丸） |
| PLAS-45 Epoch | **168** | 196 | 能（同类三档弹丸） |
| **PLAS-39 Accelerator** | **0** | 0 | **必须蓄满** ✓ |
| **ARC-3 Arc Thrower** | **0** | 0 | **必须蓄满** ✓ |
| RS-422 Railgun | 0 | 0 | 必须蓄满（实际一致） |

⇒ **有 Min 档弹丸 = 可以"打弱的一发"；三档全 0 = 只能等 Full**。
（三档全 0 并不意味着"没弹丸"，而是本组件不按蓄力换弹丸，弹丸来自 `ProjectileWeapon`/`ArcWeapon` 等其它组件。）

⚠ 这是**离线强相关**（6/6 与现象一致），运行期因果**未证**——见 §6 的判据设计。

---

## 4 六把蓄力武器的实际数值（本 build）

| 武器 | 行 | Min 时间 | Full 时间 | Over 时间 | Speed Min/Over | Dmg Min/Over | Pen Min/Over | Dist Min/Over |
|---|---:|---:|---:|---:|---|---|---|---|
| PLAS-39 Accelerator | 2 | 0.45 | **0.50** | 0.90 | 0.7 / 1.0 | 1.0 / **2.5** | 1 / 1 | 0.7 / 1.4 |
| PLAS-101 Purifier | 4 | **0.01** | 1.00 | 1.00 | — | — | — | — |
| PLAS-15 Loyalist | 5 | **0.01** | 0.75 | 3.00 | 1 / 1 | 0.5 / 1 | 0.55 / 1 | 0.7 / 1.4 |
| **ARC-3 Arc Thrower** | 6 | **1.00** | **1.10** | 1.20 | 0.7 / **1.4** | 1 / 1 | 1 / 1 | 1 / 1（电弧倍率另有 `Splits/Chains`，ARC-3 全 0） |
| PLAS-45 Epoch | 8 | 1.00 | 2.50 | 2.60 | 1 / 1 | 1 / 2 | 1 / 1 | 0.7 / 1.4 |
| RS-422 Railgun | 9 | 0.45 | 0.50 | 3.00 | 0.7 / 1.0 | 1.0 / 2.5 | 1 / 1 | 0.7 / 1.4 |

> Accelerator 与 Railgun 的倍率组**完全相同**（0.7/1.0 · 1.0/2.5 · 1/1 · 0.7/1.4），像是同一套"单发重击"模板。

---

## 5 怎么改

与锁定线同一套（实体表通用原语），只需换 `--block` / `--key` / `--field`：

```bash
python tools/entity_field_set.py show --block 0xEAC335A1 --key 0x96DE9CD50F7306E6 --width 216   # ARC-3
python tools/entity_field_set.py set  --plain <in> --block 0xEAC335A1 --key <武器 GUID> \
    --field 0x18 --type f32 --value 0.05 --expect-old 1.1 --out <out>
# 封装 / 装机 / 回读 同 LOCKON-TARGETING §5
```

可改的旋钮（按有用程度）：

| 目标 | 字段 |
|---|---|
| 蓄满更快 / 几乎不用蓄 | `+0x18` Full.ChargeTime（配合 `+0x00` Min、`+0x30` Over） |
| 允许"不蓄满就开火" | `+0x04` Min.ProjType（要填一个合法的弹丸类型 id） |
| 蓄力对伤害的加成 | `+0x54` DamageMin / `+0x58` DamageOver |
| 过充会炸自己 | `+0xB9` ExplodesOnOvercharged |
| 按住扳机保持蓄力 | `+0xB8` AutoFireInSafety |

---

## 6 run 1：ARC-3 蓄满时间 → 0.05（**✓ 实机**）

| 项 | 值 |
|---|---|
| 变量 | **ARC-3 `WeaponChargeComponentData`：Min `1.00→0.02` · Full `1.10→0.05` · Over `1.20→0.06`**（一个逻辑变量：三档蓄力时间） |
| 其余 | 只叠加已证的 `P-92 锁定距离 300` + `Spear lock_t 0.05`；Accelerator 等**未动** |
| 离线 | G1–G9 全 PASS ×3 次链式；哈希 `0x8E49771B181FFAA1` 不变 |
| 装盘 | 相对上一版**只差 11 字节**（三个 f32 + 末块尺寸）；封包 sha256 `a5b7c49d…` |
| 盘上回读 | ARC-3 `Min=0.02 / Full=0.05 / Over=0.06`；Accelerator 仍 `0.45/0.50/0.90` |

**实机结果（用户原话）**：「**按下几乎立刻能放电**」✓ —— `ChargeTime` **就是蓄力时长（秒）**。

⇒ 三档时间可任意压短；同样的做法可套到 Accelerator（`0.50`）、Railgun（`0.50`）、Epoch（`2.50`）。

---

## 6.5 过蓄（overcharge）：伤害怎么变、爆炸是哪一行

### 6.5.1 伤害随蓄力变化的机制 = `ProjectileMultipliers`

社区结构里每项属性**只有两个端点**：`…Min`（最小蓄力时）与 `…Over`（完全过蓄时），
中间由引擎按蓄力程度插值。实测：

| 武器 | DamageMin | **DamageOver** | PenMin / PenOver | SpeedMin / SpeedOver | DistMin / DistOver |
|---|---:|---:|---|---|---|
| **RS-422 Railgun** | 1.0 | **2.5** | 1 / 1 | 0.7 / 1.0 | 0.7 / 1.4 |
| **PLAS-45 Epoch** | 1.0 | **2.0** | 1 / 1 | 1 / 1 | 0.7 / 1.4 |
| PLAS-39 Accelerator | 1.0 | **2.5** | 1 / 1 | 0.7 / 1.0 | 0.7 / 1.4 |
| PLAS-15 Loyalist | 0.5 | 1.0 | 0.55 / 1 | 1 / 1 | 0.7 / 1.4 |

⇒ **这正是「蓄满到过蓄之间伤害会变」的来源**：从 `DamageMin` 一路涨到 `DamageOver`。
Railgun 是 **1.0× → 2.5×**（涨 150%），Epoch 是 **1.0× → 2.0×**。

另有一条**独立**的变化通道：Epoch 的三档 `ProjType` 不同（Min `168` → Full/Over `196`），
即"换弹丸"；Railgun 三档全 0（不换弹丸，只吃倍率）。

### 6.5.2 过蓄爆炸对应的爆炸行（`generated_explosion_settings.dl_bin`）

蓄力行 `+0xC8` = `ExplodeType`，指向爆炸表里的行。**逐武器实测 + wiki 对照**：

| 武器 | `AutoFireInSafety` `+0xB8` | `ExplodesOnOvercharged` `+0xB9` | `ExplodeType` `+0xC8` | 爆炸行 | 半径（内 / 外 / 冲击波） | 伤害类型 | 伤害 / 耐久 |
|---|---:|---:|---:|---:|---|---:|---:|
| **RS-422 Railgun** | 0 | **1** | **326** | 209 | **0.4 / 2 / 3 m** | 362 | **300 / 300** |
| **PLAS-45 Epoch** | 0 | 0 | **321** | 107 | 3 / 4 / 5 m | 68 | **800 / 800** |
| PLAS-39 Accelerator | 0 | 1 | 326 | 209 | 0.4 / 2 / 3 m | 362 | 300 / 300 |
| Purifier / ARC-3 / Loyalist | 0 | 1 | 269 | 208 | 0.4 / 2 / 3 m | 362 | 300 / 300 |

> 半径列按 **内 / 外 / 冲击波**（`+0x10/+0x14/+0x18`）排列：**判定边界看中间值（外圈）**，
> 末值是视觉冲击波。参见 `docs/explosions/EXPLOSION-VISUAL-26088801.md` §1。

**★ 关键：爆炸行 `+0x4` 是「伤害类型 id」，不是「伤害行号」。**
`type 362` → damage 表 **行 350**，逐字段与 wiki 的 *Railgun Overcharge E* 完全吻合：

| damage 行 350（type 362） | 值 | wiki「Overcharge E」 |
|---|---:|---|
| `+4` 伤害 / `+8` 耐久 | **300 / 300** | 300 / 299-0 ✓ |
| `+12` 内圈 AP | **3** | 3 Medium ✓ |
| `+28` 爆破力 | **20** | 20 ✓ |
| `+32` 硬直 | **5** | 5 ✓ |
| `+36` 推力 | **40** | 40 ✓ |

⇒ **爆炸 type 326（行 209）就是「RS-422 Railgun Overcharge E」**（半径 0.4/2/3 m 也一致）。
Epoch 的 type 321 则是 **800 伤害、3-4-5 m** 的大爆炸 —— 但它的 `ExplodesOnOvercharged=0`，所以
"过蓄会不会炸"可能还有别的判据（**未证**）。

⚠ **踩过的坑（记下来）**：最初把 `+0x4` 当成"伤害行号"去查 `damage row 362`，读出 2000 伤害，
与 wiki 的 300 冲突 —— 是 wiki 图把它逼出来的。**伤害表是「type → 行」的间接引用，不是行号。**

### 6.5.3 run 2：Railgun 过蓄不再自伤（**已装盘，待实机**）

| 项 | 值 |
|---|---|
| 文件 | **`generated_explosion_settings.dl_bin`**（不是实体表，独立备份/回滚） |
| 变量 | **爆炸 type 326 行内 `+0x4`（伤害类型 id）：`362` → `32`** |
| 为什么选 `32` | damage 表 `type 32` = 行 31，**伤害 0 / 耐久 0**，且**当前没有任何爆炸行引用它** ⇒ 零副作用 |
| 只影响 | type 326 这一条；**type 269 仍指 362、type 321 仍指 68**（盘上回读确认） |
| 离线 | G1–G6 全 PASS；哈希 `0x2ABCD21D2536373D` 不变；封包 sha256 `b2e6bf0f…`（68,204 B） |
| 保留 | 爆炸的**视觉与音效不变**（半径/音效句柄都没动），只是不再造成伤害 |

**实机判据**：带 **RS-422 Railgun** 进图，蓄满后**继续按住到过蓄**——

- ✓ 若**照旧爆闪/爆响但自己不掉血** ⇒ 确认 type 326 + 伤害类型 362 就是过蓄自毁
- ⚠ 若**完全不爆了**（连特效都没）⇒ `+0x4` 同时兼作"是否爆炸"的开关，应改回 362 并改伤害行 350 的 `+4/+8`
- ✗ 若**照旧被炸死** ⇒ 过蓄自毁走的是另一条路（不在 `ExplodeType` 里）

---

## 6.6 射击模式 / 安全模式 / 加模式 —— **已拆到独立一篇**

射击模式那部分（模式槽、选择键、`FireMode` 枚举反查表、Railgun 安全模式、给 APW-1 加全自动、
Volley / Total 实验、射速三档）已经长到可以独立成篇，移到
[**WEAPON-FIRE-MODES**](WEAPON-FIRE-MODES-26088801.md)。

一句话摘要：**模式 = `WeaponDataComponentData +0x90…0x9C` 里的 `FireMode` 值**
（`1` 自动 / `2` 半自动 / `3` 连发 / `4` 齐射 / `5` 安全 / `6` 不安全 / `7` 全射，**槽位上限 3**），
**能否切换**看 `function_info` 是否绑了 `Firemode(3)`（`+0xB8` 左 / `+0xBC` 右）。
本页只保留**蓄力相关**（`ChargeStateSetting` / 过蓄倍率 / 过蓄自毁爆炸）。

---

## 7 三态

| 结论 | 态 |
|---|---|
| `WeaponChargeComponentData` 块位置 / 几何（20 槽 + 11 行 × 216） | **✓ 离线** |
| 216 B 行结构 = 三档 ChargeStateSetting + 12 倍率 + 句柄 + 布尔，与社区 schema 逐项对齐 | **✓ 离线** |
| 「不蓄满能否开火」与 `Min.ProjType ≠ 0` 6/6 相关 | **✓ 离线**（强相关，非因果） |
| `ChargeTime` 是蓄力时长（秒） | **✓ 实机**（ARC-3 1.1→0.05，按下几乎立刻放电） |
| `Min.ProjType` 填值可让"必须蓄满"的枪提早开火 | **⚠ 未试** |
| 倍率区对实际弹丸生效 | **⚠ 未试** |
| 伤害随蓄力在 `DamageMin`→`DamageOver` 间变化（Railgun 1.0→2.5 · Epoch 1.0→2.0） | **✓ 离线**（结构+数值；实机幅度未量化） |
| Railgun 过蓄自毁 = 爆炸 type 326（行 209，0.4-2-3 m）→ 伤害类型 362 → damage 行 350 = **300/300、AP 3、爆破 20、硬直 5、推力 40**（**与 wiki 逐项吻合**） | **✓ 离线** |
| 爆炸行 `+0x4` 是「伤害类型 id」而非行号 | **✓ 离线**（wiki 对照逼出，见 §6.5.2 的坑） |
| Railgun 过蓄不再自伤 | **⚠ 待 run 2**（伤害类型 362→32） |
| Epoch 过蓄自毁：`ExplodeType=321` → 伤害类型 68 → **800/800、3-4-5 m**，但 `ExplodesOnOvercharged=0` | **⚠ 未证**（布尔与现象不一致） |
| Railgun 过蓄触发但**不再伤己** | **✓ 实机**（run 2：爆闪照旧、不掉血） |
| 「安全/不安全」= `WeaponDataComponentData +0x90/+0x94` 里的 FireMode 值（5=安全 / 6=不安全） | **⚠ 待 run 3**（推断来自"Epoch 只有 6 且能过蓄"） |
| 能否切换 = `function_info` 是否绑定 `WeaponFunctionType Firemode(3)`（Railgun 绑在 `+0xB8`） | **✓ 离线**（4 把蓄力枪对照，只有 Railgun 绑定） |
| 齐射"打几发"由枪管数决定，且枪管数不在数据表里 | **✓ 实机 + 离线**（单管 AR-23 = 1 发） |

---

## 8 下一步

1. ~~收 run 1（ARC-3 时间）~~ → **✓ 已收**。
2. ~~收 run 2（Railgun 过蓄不自伤）~~ → **✓ 已收**（爆闪照旧、不掉血）。
3. 把短蓄力推广：Accelerator `0.50`、Railgun `0.50`、Epoch `2.50` → 0.05。
4. 倍率区单独验：**Railgun `DamageOver` 2.5 → 5.0**，看蓄满伤害是否翻倍（同时验证“线性插值”）。
5. `Min.ProjType` 路线：给 ARC-3 的 Min 档填一个合法电弧弹丸类型，看能否提早开火。
6. **射击模式的所有后续**（加全自动 / 齐射 / 全射、射速切换、安全模式）见
   [WEAPON-FIRE-MODES](WEAPON-FIRE-MODES-26088801.md) §5–§6。
