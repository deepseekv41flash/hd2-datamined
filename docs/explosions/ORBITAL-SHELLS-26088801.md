# 轨道弹幕的"弹丸 → 爆炸"链，与"HE/EMS 交替"到底能不能做（build 26088801）

> 起因：社区工具里出现两条未发布候选 `轨道120mm HE/EMS火力网 [effect 1426]`、`轨道燃烧加特林 [effect 1427]`。
> 本文只记**可复算的事实**与**否证**，结论在三态里标出。

## 0 三态

| 标记 | 含义 |
|---|---|
| ✓ | 离线可复算（本 build 明文 + 社区元数据交叉） |
| ✗ | 已否证（写明证据）|
| ⚠ | 未验 |

## 1 社区元数据里那两件是什么（`✓` 阅读）

来源：`refs/helldiversdata/generated_projectile_settings.json`（246 行，社区 dump）+ `refs/hd2runtime-repo/research/`。

轨道弹丸家族的弹道参数（`calibre / mass / speed`）：

| 射弹 | cal | mass | speed | 命中爆炸 |
|---|---:|---:|---:|---|
| `Orbital_Cannon_120mm_HE` | 84 | 5000 | 400 | `OrbitalStrike` |
| `Orbital_Cannon_120mm_HE_Cheap` | 84 | 5000 | 400 | `OrbitalStrike_Cheap` |
| **`Orbital_Stunround`（EMS）** | **84** | **5000** | **400** | `OrbitalStun` |
| `Orbital_Stunround_Upgraded_MK2 / MK3` | 84 | 5000 | 400 | `OrbitalStun_MK2 / MK3` |
| `Orbital_Cannon_110mm` | 110 | 5000 | 400 | `OrbitalShot` |
| `Orbital_Cannon_380mm_HE` | 406 | 30000 | 400 | `OrbitalBarrage` |
| `Orbital_Cannon_Napalm` | 84 | 5000 | 400 | `Orbital_Napalm` |
| `Orbital_Gas`（+MK2/MK3） | 84 | 5000 | 400 | `OrbitalGas` |
| `Orbital_Smoke` | 84 | 5000 | 400 | `AirStrikeSmoke` |

⇒ **120mm HE 与 EMS 眩晕弹的弹道一模一样**（84 / 5000 / 400），只有命中爆炸不同。
"HE/EMS 火力网" = 同一门弹幕混打这两种**已存在**的弹丸，不需要新弹头数据。

## 2 本 build 里对应的行与爆炸 id（`✓`）

`ProjectileInfo` 272 B、355 行、行基址 **44**（`96604 - 44 = 355×272`）。
用社区 dump 的 **name hash**（行内 `+4/+8/+12`）对齐，命中：

| 射弹 | 行号 | `+0`=ProjectileType | `+0x90` 命中爆炸 | `+0x9C` 到期爆炸 |
|---|---:|---:|---:|---:|
| `Orbital_Cannon_120mm_HE` | **135** | **197** | **213** | 213 |
| `Orbital_Stunround`（EMS） | **148** | **76** | **188** | 0 |
| `Orbital_Cannon_380mm_HE` | 79 | — | 210 | 0 |
| `Orbital_Gas` | 151 | — | 82 | 0 |
| `Orbital_Smoke` | 10 | — | 0 | 0 |

**爆炸 213 在整张射弹表里只被 1 行引用（行 135）**；188 也只被 1 行（行 148）
⇒ 把行 135 的爆炸换成 188，只影响"120mm HE 这一发弹"，不会波及其它战备（`✓` 全表 355 行扫过）。

## 3 "逐发交替（HE/EMS 混编）"在数据层做不到（`✗` 否证）

HD2Runtime 的字段名里有 `orbital_120mm_he_barrage_attack_delivery_1/2/3_projectile`，本以为能在数据里找到三条投送。

| 查法 | 结果 |
|---|---|
| `ProjectileWeaponComponentData` 行结构（容器 `0x45171B68` → 行类型 `0x2290C42E`，**616 B / 556 行**，typelib 逐成员）| 弹丸槽**只有两个**：`+0x000`（主弹）与 `+0x240`（备弹/alt，正是当年"可编程弹药"用的那格），**没有第三、第四条** |
| 556 行武器的 `+0x000` / `+0x240` 里有没有 197（120mm HE）或 76（EMS）| **0 行** —— 战备轰炸的炮弹根本不是通过实体武器组件的数值字段发射的 |
| `AttackPatternComponentData`（`0x4CCBAD23`）| **全表只有 1 行**，且不含 197/76 |
| 其它"投送"类组件（`ObjectiveVehicleDelivery` / `ObjectiveDeliverableVehicle` / `ObjectiveCarryDelivery` / `ObjectiveShellRack` / `ObjectiveShell`）| 都是任务目标物件，与轨道弹幕无关 |

⇒ 那三条 `attack_delivery_*_projectile` **不在 dl_bin 表里**，是**资源层（unit / 投送资源的节点或事件）**里的名字 ——
这与旧结论一致：**战备 → 弹丸的关联不是数值外键，是运行时按资源名解析**（见 [STRATAGEM-REFERENCE-CHAIN](../tables/STRATAGEM-REFERENCE-CHAIN-25988413.md)）。
所以"同一条弹幕里逐发交替两种弹种"**纯数据做不到**。

## 4 纯数据能做的（`✓` 可执行）

| 方案 | 改动 | 效果 |
|---|---|---|
| **A. 120mm EMS 弹幕** | 射弹行 **135** 的 `+0x90`（命中爆炸）**213 → 188**；`+0x9C` 可选 | 120mm 弹幕全部变成 EMS 眩晕弹；因 213 独占，其它战备**零影响** |
| **B. 燃烧加特林（近似）** | 找 `ORBITAL. GATLING BARRAGE` 用的射弹行，把命中爆炸换成燃烧类（如 `EagleBomb_Napalm` 的爆炸行）| 与 A 同型：单弹种替换 |
| ~~C. 同一条弹幕 HE/EMS 交替~~ | —— | **✗ 数据层无入口**（见 §3）|

> B 需要先定位加特林弹幕的射弹行（同一套 name-hash 对齐法，`Orbital` 家族里没有 gatling 项 ⇒ 它用的是另一族射弹，待查）。

## 5 相关

- 弹丸行字段与换爆炸配方：[EXPLOSION-PROJECTILE-25988413](EXPLOSION-PROJECTILE-25988413.md)
- 爆炸表与粒子：[EXPLOSION-VISUAL-26088801](EXPLOSION-VISUAL-26088801.md)
- 战备→弹丸不是数值外键：[STRATAGEM-REFERENCE-CHAIN-25988413](../tables/STRATAGEM-REFERENCE-CHAIN-25988413.md)

## 6 「每轮三发是否一致」：逐 delivery 字段对照（✓ 离线，2026-10-31）

HD2Runtime 0.27.0 的 `StratagemAuthoringCapabilities.json` 把每条战备的 `attack_delivery_N_projectile`
**每个弹道/伤害/爆炸字段**都列成了可读值（本机缓存在 `D:/mod/hd2runtime-capabilities.json`，
SDK 校验 build `F5FEE03DCFDB` / steamBuild **25480438**，与我们 build `26251122` 差一代 —— 下表数值是
**该 SDK 版本读数**，是否随 build 变需再核；结构/字段名与我们的 `ProjectileInfo` 行 135 一致）。

`orbital_120mm_he_barrage` 共 **3 个 delivery**（这就是“每轮三发”的数据形态），26 个字段**三份全部相同**：

| 字段 | delivery 1 / 2 / 3 |
|---|---|
| `projectile.pellet_count` | 1 / 1 / 1 |
| `projectile.velocity` | 400 / 400 / 400 |
| `projectile.mass` | 5000 / 5000 / 5000 |
| `projectile.drag` | 0 / 0 / 0 |
| `projectile.gravity` | 1 / 1 / 1 |
| 直击伤害（standard / durable） | 3500 / 3500（三份相同） |
| 直击穿甲（direct / slight / large / extreme） | 7 / 7 / 6 / 6（三份相同） |
| 直击 demolition / stagger / push | 50 / 20 / 20（三份相同） |
| 命中爆炸半径（inner / outer / shockwave） | **3.3 / 10.0 / 11.0**（三份相同） |
| 爆炸伤害（standard / durable） | 1200 / 1200（三份相同） |
| 爆炸穿甲（direct / slight / large / extreme） | 5 / 0 / 0 / 0（三份相同） |
| 爆炸 demolition / stagger / push | 50 / 70 / 40（三份相同） |

⇒ **三发完全一致**：同一弹丸参数、同一命中爆炸、同一爆炸伤害。三发之间的差别只可能来自
**delivery 的时序/落点**（这些不在 HD2Runtime 暴露的字段里），与 §3 的结论一致 ——
`attack_delivery_*_projectile` 是资源层投送引用，不是 dl_bin 表里的三个弹丸外键。

顺带（同一份 JSON 的 delivery 计数，作为“每轮几发”的旁证）：

| 战备 | deliveries |
|---|---|
| `orbital_120mm_he_barrage` | **3** |
| `orbital_380mm_he_barrage` | 3 |
| `orbital_napalm_barrage` | 3 |
| `orbital_walking_barrage` | 3 |
| `orbital_gatling_barrage` | **4** |
| 单发类（precision / railcannon / gas / smoke / EMS / airburst / 全部 Eagle） | 1 |

复算命令：

```bash
python - <<'EOF2'
import json,re
d=json.load(open(r"D:/mod/hd2runtime-capabilities.json",encoding="utf-8"))
rows=d["collections"]["StratagemAuthoringCapabilities.json"]["fieldInstances_kept"]
sel=[r for r in rows if "orbital_120mm_he_barrage" in r.get("instanceKey","")]
for r in sorted(sel,key=lambda x:x["instanceKey"]):
    print(r["instanceKey"].split("orbital_120mm_he_barrage",1)[1], "=", r.get("currentDefault"))
EOF2
```

## 7 未发布的舰船升级 `Orbital 120mm EMS Barrage`（hash `0xAE4D54F6CB8CC350`）——存在，效果体已写好，但未接线

社区（Bingus 作者）指出 Hash.csv 里有一条「轨道火力网-升级」= `0xAE4D54F6CB8CC350`。**本 build 确认存在，且不是空名字占位。**

### 7.1 它是什么：`ComponentEntityDeltaStorage` 里的一条完整 addPath delta

`python tools/ref_scan.py delta-show 0xAE4D54F6CB8CC350` 直接解出 **6 处字段写入 / 2 个组件**：

| comp | 字段 | 内容 | 解读 |
|---:|---|---|---|
| **196** | `+0x40`，32 B | `76, 197, 139, 139, 197, 139, 139, 0`（u32） | 同时出现 **76 = `Orbital_Stunround`（EMS 眩晕弹丸 type）**、**197 = `Orbital_Cannon_120mm_HE`（HE 弹丸 type，见 §1）**、**139 = `ORBITAL. 120MM HE STRIKE` 战备 id** ⇒ 「把 120mm 弹幕改成打 EMS」的官方定义 |
| 196 | `+0x04` | `7` | 类/弹种槽位相关（未定名） |
| 196 | `+0x18` | `5` | 同上 |
| 196 | `+0x24` | **f32 `10.0`** | 与 120mm 命中爆炸 outer_radius 10.0 相同（§6） |
| **28** | `+0x08` | `0x25B8CFF26C7C0112` | **= 120mm 弹幕战备行 139 的 `+0xA8` 根包**（同一值） |
| 28 | `+0x10` | `0xA00E6327E3747A50` | 另一个包（疑似 EMS 弹幕载荷包） |

⇒ 这不是"名字占位"，而是**已写好数值/引用的一套升级效果**：换弹丸 type（76/197 并存说明是"改掉 120mm 的弹种"而不是新弹丸）+ 换加载包。

### 7.2 接线状态：`✗ 未接线`

对全部 55 张明文表做 u32 级搜索（`lo32 0xCB8CC350` / `hi32 0xAE4D54F6`）：

| 出现处 | 次数 | 说明 |
|---|---:|---|
| `generated_entity_deltas.dl_bin` | 1 | 就是上面那条 addPath delta 本体 |
| `generated_modifier_settings.dl_bin` | 1 | 唯一一处"数据侧引用"（块 6 payload 尾部 8 字节；未解语义，疑似修饰符→升级的引用） |
| 其余 53 张表 | 0 | **没有任何升级列表 / 解锁行引用它** |

⇒ 它**没有接到"可购买/可解锁的舰船升级"行**上，这就是它未发布的直接原因（不是数值没写完）。

### 7.3 三态判定

| 项 | 结论 |
|---|---|
| 存在性 | **✓ 存在**（addPath delta + modifier 一处引用） |
| 效果体完整度 | **✓ 完整**（弹丸 type、战备 id、半径、两个包 id 全部写实） |
| 玩家可见名字 | **⚠ 只有内部名 hash**（Hash.csv 的「轨道火力网-升级」）；未在明文定位表/字符串语料里找到对应显示名（本仓库 strings 语料 grep "120mm/EMS BARRAGE" 0 命中） |
| 可购买/可获得 | **✗**（无接线，见 7.2） |
| comp 196 / 28 的真实组件名 | **⚠ 未定**（不在 `ref_scan.py` 现知的 6 个 delta 组件映射里：5/114/119/239/274/324） |

**一句话**：它是**「写好效果、没接解锁」的半成品**，恰好证明官方确实做过"120mm 打 EMS"的方向；社区说的「SHODAN 不开放这一格」也成立 —— 它的效果不在战备行字段里，而在 `entity_deltas` 的 addPath 机制里（与武器附件同一套）。
