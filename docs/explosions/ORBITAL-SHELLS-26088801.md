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

## 3 "逐发交替（HE/EMS 混编）"在数据层做不到（~~`✗` 否证~~ → **2026-10-31 更正：做得到 `✓`，入口见 §8**）

HD2Runtime 的字段名里有 `orbital_120mm_he_barrage_attack_delivery_1/2/3_projectile`，本以为能在数据里找到三条投送。

| 查法 | 结果 |
|---|---|
| `ProjectileWeaponComponentData` 行结构（容器 `0x45171B68` → 行类型 `0x2290C42E`，**616 B / 556 行**，typelib 逐成员）| 弹丸槽**只有两个**：`+0x000`（主弹）与 `+0x240`（备弹/alt，正是当年"可编程弹药"用的那格），**没有第三、第四条** |
| 556 行武器的 `+0x000` / `+0x240` 里有没有 197（120mm HE）或 76（EMS）| **0 行** —— 战备轰炸的炮弹根本不是通过实体武器组件的数值字段发射的 |
| `AttackPatternComponentData`（`0x4CCBAD23`）| **全表只有 1 行**，且不含 197/76 |
| 其它"投送"类组件（`ObjectiveVehicleDelivery` / `ObjectiveDeliverableVehicle` / `ObjectiveCarryDelivery` / `ObjectiveShellRack` / `ObjectiveShell`）| 都是任务目标物件，与轨道弹幕无关 |

⇒ 那三条 `attack_delivery_*_projectile` **不在 dl_bin 表里**，是**资源层（unit / 投送资源的节点或事件）**里的名字 ——
这与旧结论一致：**战备 → 弹丸的关联不是数值外键，是运行时按资源名解析**（见 [STRATAGEM-REFERENCE-CHAIN](../tables/STRATAGEM-REFERENCE-CHAIN-25988413.md)）。
所以当时判"同一条弹幕里逐发交替两种弹种**纯数据做不到**"。

> **2026-10-31 更正（推翻本节 ✗）**：入口不在武器/投送组件，而在 **`BombardmentComponentData +0x40` = 8 槽
> `ProjectileType` 弹种清单**（第 i 槽 = 每轮第 i 发弹种）+ `+0x04` 每轮发数 —— 完整解码见 **§8**。
> 两个反证：①本 build **原版** 120mm 弹幕自己就是逐发混编（第 1 发 `..._120mm_HE`、第 2/3 发 `..._120mm_HE_Cheap`）；
> ②官方未发布 EMS 升级（§7）写的就是"首发 EMS + 其余 6 发 HE"的逐发混编。
> 当年找不到的原因：只在**武器组件 / 投送组件**里找"多弹丸槽"，而弹种清单是**实体组件里的 typed reference 数组**；
> 另 HD2Runtime 自己也没证明 shell/volley 语义，`delivery:N` 只是把 `+0x40` 的非零槽顺序编号。

## 4 纯数据能做的（`✓` 可执行）

| 方案 | 改动 | 效果 |
|---|---|---|
| **A. 120mm EMS 弹幕** | 射弹行 **135** 的 `+0x90`（命中爆炸）**213 → 188**；`+0x9C` 可选 | 120mm 弹幕全部变成 EMS 眩晕弹；因 213 独占，其它战备**零影响** |
| **B. 燃烧加特林（近似）** | 找 `ORBITAL. GATLING BARRAGE` 用的射弹行，把命中爆炸换成燃烧类（如 `EagleBomb_Napalm` 的爆炸行）| 与 A 同型：单弹种替换 |
| **C. 同一条弹幕 HE/EMS 交替** | 改 `BombardmentComponentData` 第 19 行 `+0x40` 弹种清单（8 槽）+ `+0x04` 每轮发数 | **✓ 可行**（2026-10-31 实机：每轮 7 发、首发 EMS；§8）|

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

⇒ **当时的结论**：三发在"26 个暴露字段"上完全一致，差别只可能来自 **delivery 的时序/落点**（这些不在 HD2Runtime 暴露的字段里），与 §3 的结论一致 ——
`attack_delivery_*_projectile` 是资源层投送引用，不是 dl_bin 表里的三个弹丸外键。

> **2026-10-31 更正（§8 定因）：数值部分仍然成立，但"同一命中爆炸"是错的。**
> - 26 个暴露字段（弹道/直击伤害/穿甲/爆炸半径/爆炸伤害）**确实三份相同** ✓；
> - 但三发**不是同一条弹丸行**：第 1 发 = 射弹行 **135**（`Orbital_Cannon_120mm_HE`，命中爆炸 **213 = `OrbitalStrike`**）；
>   第 2/3 发 = 射弹行 **136**（`Orbital_Cannon_120mm_HE_Cheap`，命中爆炸 **177 = `OrbitalStrike_Cheap`**）；
> - 两条爆炸行的伤害行（457）、半径 3.3/10/11、震屏 60、音效事件**全部相同**，只有 `+0x38` **粒子资源**（与 surface impact）不同
>   ⇒ 三发差别除了时序/落点，还有**爆炸粒子（视觉）**：第 1 发正常、第 2/3 发省粒子。
> - 为什么 §6 没看出来：HD2Runtime 暴露的 26 个字段**不含粒子**；且其 `OrbitalBarrageProof/README.md` 自己写明
>   *"Native delivery arrays remain unchanged because scalar shell/volley semantics are not proven"* ——
>   它把 `+0x40` 的非零槽按顺序编成 `delivery:N`，`delivery:1` 与 `delivery:2/3` 指向的其实是**两条不同射弹行**，
>   只是这两行在它暴露的字段上恰好等值。
> ⇒ 正确表述：**三发"数值"完全一致；"弹种/爆炸行/视觉"不一致**；并且**每发弹种可以单独改**（`+0x40`，见 §8）。

顺带（同一份 JSON 的 delivery 计数，作为“每轮几发”的旁证）：

> ⚠ 更正：这里的 `deliveries` 数 = **`+0x40` 非零槽数**，**不等于每轮发数**。120mm 是 3 槽/每轮 3 发（巧合相等）；
> 加特林是 **4 槽**但 `+0x04`（每轮发数）= **60**。见 §8。

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
| **196 = `BombardmentComponentData`**（块 `0xCDBC43D8`，24 行 × 192 B） | `+0x40`，32 B | `76, 197, 139, 139, 197, 139, 139, 0`（u32） | **8 槽 `ProjectileType` 数组 = 每发弹种清单**（§8 已全解）：**76 = `Orbital_Stunround`（EMS 眩晕弹）**、**197 = `Orbital_Cannon_120mm_HE`（射弹行 135）**、**139 = 它的 `_Cheap` 克隆（射弹行 136，只换省粒子爆炸，见 §8.5）** ⇒ 官方定义是「**首发 EMS + 其余 6 发 HE**」的混合弹幕，不是整条变 EMS（§8.7 更正） |
| 196 | `+0x04` | `7` | 类/弹种槽位相关（未定名） |
| 196 | `+0x18` | `5` | 同上 |
| 196 | `+0x24` | **f32 `10.0`** | 与 120mm 命中爆炸 outer_radius 10.0 相同（§6） |
| **28 = `LoadoutPackageComponentData`**（块 `0x7A858691`） | `+0x08` | `0x25B8CFF26C7C0112` | **= 120mm 弹幕战备行 139 的 `+0xA8` 根包**（同一值） |
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
| comp 196 / 28 的真实组件名 | **✓ 已解**：196 = `BombardmentComponentData`、28 = `LoadoutPackageComponentData` —— 解法见 7.4 |

**一句话**：它是**「写好效果、没接解锁」的半成品**，恰好证明官方确实做过"120mm 打 EMS"的方向；社区说的「SHODAN 不开放这一格」也成立 —— 它的效果不在战备行字段里，而在 `entity_deltas` 的 addPath 机制里（与武器附件同一套）。

### 7.4 comp 196 / 28 的组件名怎么解出来的（✓ 离线，2026-10-31）

delta 存储的「组件索引」与 **实体表块 0 尾部 u16 组件清单**是**同一套编号**（值空间 0..324），于是用
[WEAPON-CUSTOMIZATION-26251122](../tables/WEAPON-CUSTOMIZATION-26251122.md) §12.6 的映射方法反查即可
（组件块键集合 == u16 值出现过的实体集合，272/272 精确同构）：

| 组件索引 | 组件名 | 对照 |
|---:|---|---|
| 5 | `WeaponMagazineComponentData` | 与 `ref_scan.py` 已知表一致 |
| 119 | `WeaponRoundsComponentData` | 同上 |
| 239 | `WeaponDataComponentData` | 同上 |
| 274 | `WeaponCustomizationComponentData` | 同上 |
| 324 | `ProjectileWeaponComponentData` | 同上 |
| **196** | **`BombardmentComponentData`** | **与社区图里的 type hash `0x0CDBC43D8` 完全一致**；块 `0xCDBC43D8`、24 行 × 192 B |
| **28** | **`LoadoutPackageComponentData`** | 与包里写 `+0x08/+0x10` 两个包 id 的语义吻合 |

**顺带锁定 120mm HE 弹幕行**：`BombardmentComponentData` 第 **19** 行 —— `+0x04=3`（= `num_bombs`，每轮 3 发）、`+0x18=5`（= `num_salvos`，5 轮）、
`+0x24=27.0`（= `area_size`），`+0x40`（32 B = 8×u32 的 `ProjectileType` 弹种清单）当前 = **`(197, 139, 139, 0, …)`**
= **1 发正常 120mm HE（射弹行 135）+ 2 发 `_Cheap` 克隆（射弹行 136）**（§8.4/§8.5）。
EMS 升级 delta 把这一格改成 **`(76, 197, 139, 139, 197, 139, 139, 0)`** —— 即 **7 发里只有第 1 发是 EMS，其余 6 发全是 HE 族**：
官方写的是「**EMS 起手 + HE 收尾**」的混合弹幕，不是整条变 EMS（§8.7 有更正与实证）。

⇒ 至此这条升级的**完整作用链**清楚了：改 `BombardmentComponentData` 第 19 行（弹幕定义，`+0x40` 弹种清单）
+ 换 `LoadoutPackageComponentData`（`+0x08` 根包 / `+0x10` 第二个包）。缺的只是解锁接线与显示名。

## 8 `BombardmentComponentData` 行字段全解：`+0x04` 发数 / `+0x18` 轮数 / `+0x24` 面积 / `+0x2C` 高度 / `+0x40` 弹种清单（✓✓ 实机 + ✓ 离线，2026-10-31）

> **一句话**：`+0x40` 是 **8 槽 `ProjectileType` 枚举数组** —— 第 i 槽 = 每轮第 i 发弹的**弹种**；
> 每个值 = `generated_projectile_settings.dl_bin`（射弹表 355 行 × 272 B）里某条射弹行的 `+0x00`。
> `+0x04` = **每轮发数**（wiki 名 `num_bombs`，实机 3→7 已验证）、`+0x18` = **轮数**（`num_salvos`）。

### 8.1 三层独立证据

1. **typelib 结构**（`python tools/typelib.py show <typelib> 0x0CDBC43D8`）：块 = 哈希图 + 行数组；行类型
   `0x0793349E`，192 B / 32 成员，其中 **`+64` 起 32 B** 是一个数组成员（成员类型 `0xA2B5F333`）
   ⇒ `+0x40` 是 **8 个 u32 槽**（不是"3 个 u32"，也不是包 id / 战备 id）。
2. **HD2Runtime 0.27.0 研究档**（`refs/hd2runtime-repo/research/offensive-stratagem-runtime-F5FEE03DCFDB.json`）：
   每个 `BombardmentComponentData` 给出
   `"typedReferences":[{"path":[64],"referenceClass":"ProjectileType","values":[…]}]`；
   其写入门禁 `domains/stratagem_writes.lua:177-180` 逐槽核对
   `b.u32(component.bytes, 64+(index-1)*4)==value` ⇒ 官方核对脚本也按"第 i 槽 = i 号弹种"读。
3. **wiki 战备 JSON 四字段对齐**（本地 `refs/wiki/wiki.sqlite` 的 `stratagem` 表，`json` 列里
   `num_bombs / num_salvos / area_size / fire_height`）：把 10 条轨道战备的四个数与块内 24 行的
   `+0x04 / +0x18 / +0x24 / +0x2C` 对照，**10/10 精确相等**（§8.3 表）；另外 `+0x2C` 全表都是 3000
   （= 轨道炮的投送高度）。

### 8.2 字段表（`BombardmentComponentData` 行，192 B，24 行）

| 偏移 | 类型 | 名字 | 120mm 行（row19）值 | 状态 |
|---|---|---|---|---|
| `+0x04` | u32 | **`num_bombs` = 每轮发数** | **3** | ✓✓ 实机（3→7 后每轮 7 发） |
| `+0x18` | u32 | **`num_salvos` = 轮数** | **5** | ✓ 与 wiki 10/10 对齐 |
| `+0x24` | f32 | **`area_size` = 散布半径（m）** | **27.0** | ✓ 同上 |
| `+0x2C` | f32 | **`fire_height` = 投送高度** | **3000.0** | ✓ 同上 |
| `+0x40` | u32×8 | **`ProjectileType[8]` = 弹种清单** | **`(197,139,139,0,0,0,0,0)`** | ✓✓ 实机（槽 0 改 76 → 首发变 EMS） |
| `+0x08` / `+0x1C` | f32 | 未定名 | 0.75 / 2.0 | ⚠ 数值形态像"轮内发间隔 / 轮间隔"（380mm 1.5/3.0、加特林 0.045/1.275），未实机证 |
| `+0x00` / `+0x0C` / `+0x10` / `+0x14` / `+0x20` / `+0x28` / `+0x30`… | u32/f32 | 未解 | 多数 0 | ⚠ |

### 8.3 十条轨道战备的弹幕定义（本 build，逐行对照）

| 战备 | row | 组件实体键 | nb | ns | area | fh | `+0x40` 弹种清单 |
|---|---:|---|---:|---:|---:|---:|---|
| Orbital Precision Strike | 16 | `0xC897C0D84448AB2C` | 1 | 1 | 1 | 3000 | `[102]` |
| Orbital Gatling Barrage | 12 | `0x2F257B91037AC421` | 60 | 4 | 7 | 3000 | `[79,43,43,43]` |
| Orbital Gas Strike | 11 | `0x05F3C83A91075766` | 1 | 1 | 1 | 3000 | `[200]` |
| **Orbital 120mm HE Barrage** | **19** | `0x2D3BD00B1ED411B1` | **3** | **5** | **27** | 3000 | **`[197,139,139]`** |
| Orbital Airburst Strike | 17 | `0x75B131DC1DDC02D5` | 1 | 4 | 2 | 3000 | `[160]` |
| Orbital Smoke Strike | 18 | `0xDA76A06325E692C9` | 1 | 6 | 15 | 3000 | `[251]` |
| Orbital EMS Strike | 20 | `0x55F3747B8C27AEF6` | 1 | 1 | 1 | 3000 | `[76]` |
| Orbital 380mm HE Barrage | 9 | `0xEF66B417EDC3B1D6` | 3 | 5 | 36 | 3000 | `[82,270,270]` |
| Orbital Walking Barrage | 21 | `0xCB7F154719F331EC` | 3 | 5 | 25 | 3000 | `[82,270,270]` |
| Orbital Napalm Barrage | 14 | `0xA16AB4FF66AE6970` | 5 | 5 | 25 | 3000 | `[238,242,242]` |

识别方法：`BombardmentComponentData` 的哈希图键 = 宿主实体键；拿实体键去对 HD2Runtime 研究档的
`historicalIdentity.payloads`（120mm = `0x2D3BD00B1ED411B1`，与 row19 精确一致），再用
`nativeGraph` 的 `recordType → row` 交叉把 SDK 弹种号换算成本 build 弹种号（见 §8.4）。

### 8.4 弹种 id 解码表（本 build；值 → 射弹行 → 身份）

| 值 | 射弹行 | 身份（社区名） | 命中爆炸（本 build） | 依据 |
|---:|---:|---|---|---|
| **76** | 148 | `Orbital_Stunround`（EMS 眩晕弹） | 188 = `OrbitalStun` | 粒子 `0x424630BFE2FF5E99` 精确对齐 |
| **197** | 135 | `Orbital_Cannon_120mm_HE` | 213 = `OrbitalStrike` | 粒子 `0x36B23284931C9124` 精确对齐 |
| **139** | 136 | `Orbital_Cannon_120mm_HE_Cheap` | 177 = `OrbitalStrike_Cheap` | 粒子 `0x31798A36AF6C43DE` 精确对齐 |
| **82** | 138 | `Orbital_Cannon_380mm_HE`（主） | 301 = `OrbitalBarrage` 族 | 与 270 成对、爆炸族唯一主弹 |
| **270** | 143 | `Orbital_Cannon_380mm_HE_Cheap` | 94 = `OrbitalBarrage_Cheap` | 唯一 Cheap 粒子 |
| **238** | 140 | `Orbital_Cannon_Napalm`（主） | 63 = `Orbital_Napalm` 族 | 与 242 成对（主/Cheap 同名同粒子，按首发为主推定） |
| **242** | 141 | `Orbital_Cannon_Napalm_Cheap` | 74 同上 | 同上 |
| **79** | 37 | `Cannon_Eagle_23mm`（加特林弹，带爆炸） | 375 = `Cannon_23mm` 族 | — |
| **43** | 43 | 同族 `no_explosion` 变体（命中爆炸 0） | 0 | — |
| **200** | 151 | `Orbital_Gas` | 82 = `OrbitalGas` | 唯一 |
| **160** | 172 | Airburst 弹丸（wiki `S_P15`） | 0（爆炸不挂在弹丸上） | ⚠ 名字推定 |
| **251** | 152 | Smoke 弹丸 | 75 | ⚠ 名字推定 |
| **102** | 213 | Precision Strike 弹丸 | 0 | — |

解码方法（可复算）：① 用**爆炸行的粒子 file_id** 把本 build 爆炸 type ↔ 社区
`generated_explosion_settings.json` 的名字对齐（如 213↔`OrbitalStrike`、177↔`OrbitalStrike_Cheap`）；
② 射弹行 `+0x90`（命中爆炸）/`+0x9C`（到期爆炸）指向爆炸 type，于是射弹行 → 爆炸名 →
社区 `generated_projectile_settings.json` 里 `explosion_type_on_impact` 反查射弹名。
120mm 两行因此**唯一命中**：197=`..._120mm_HE`、139=`..._120mm_HE_Cheap`（无歧义）。

### 8.5 `_Cheap` 到底是什么：只换粒子，不换伤害

- 社区 JSON 里 `120mm_HE` 与 `120mm_HE_Cheap` 的全部字段只有一处不同：`explosion_type_on_impact`
  （`OrbitalStrike` / `OrbitalStrike_Cheap`）。
- 落到本 build 的两条爆炸行（type 213 / 177）逐 dword 对照：**伤害行（457）、半径 3.3/10/11、
  震屏 60、`+0x40` 全部相同**；只有 **`+0x38` 粒子 file_id**（`0x36B23284931C9124` / `0x31798A36AF6C43DE`）
  与粒子列表偏移（`+0x28/+0x48`）不同 ⇒ **Cheap = 换一套更省的粒子**，性能优化，不是削弱。
- 因此 **120mm HE 弹幕每轮 3 发 = 1 发正常爆炸 + 2 发省粒子爆炸**（写死在行里，不是随机）。

### 8.6 位置语义 / 循环规则

- **第 i 槽 = 每轮第 i 发**（1 基）；`0` = 槽位空（清单结束）。实机：槽 0 由 197 改 76 后，**每轮首发**变 EMS。
- 清单 ≤ 8 槽，而行里存在 `nb > 8` 的弹幕（加特林 nb=60 只有 4 个非零槽；row7 nb=64 只有 1 个）
  ⇒ 多出来的发是**按清单循环**（或取末槽）⚠ **循环规则未实机证**。
- 每轮是否重复同一清单 ⚠：按 `nb=7 / ns=5` 的官方 delta，如果每轮都套清单，应看到 **~5 次 EMS 首发**
  （2026-10-31 实机未记录次数，待补）。

### 8.7 官方未发布升级 `Orbital 120mm EMS Barrage` 的重新解读（**更正 §7.1**）

delta 写的是 `+0x04=7` + `+0x40=(76,197,139,139,197,139,139,0)` ⇒ **7 发混合弹幕：首发 EMS 眩晕，
其余 6 发全是 HE 族**（HE + 2×Cheap，重复两遍），并把 `+0x24` 27→10 收紧散布。
即官方做的是「**EMS 起手 + HE 覆盖**」的混合弹幕，**不是**"整条弹幕变 EMS"。
⇒ 要真正的全 EMS 弹幕：把 8 槽都填 76（`[76]*8`）即可，弹种层面没有别的门。

### 8.8 2026-10-31 实机记录与"特效缺失"根因

实机（装入 §7 的 6 处 delta 写入手工版）：**每轮 7 发 ✓**、**首发 EMS ✓**、**EMS 爆炸特效缺失 ✗**。

根因（离线定位，✓ 可复算）：

1. `LoadoutPackageComponentData` 行 32 B：`+0x08` = **资产包**、`+0x10` = **wwise bank**（音效库）。
   120mm 实体 `0x2D3BD00B1ED411B1`（row249）：`+0x08 = 0x25B8CFF26C7C0112`（14 项：粒子
   `0x0534FF36…`、`0x36B23284…`、`0x31798A36…`、`0x61A844A0…`、`0x68358A1C…` + texture/material + bank）；
   `+0x10 = 0x218D61959F181C48`（wwise bank，Airburst 也在用）。
2. EMS 打击实体 `0x55F3747B8C27AEF6`（row250）的资产包是 **`0x1E6C958B95568DD7`**：7 项，含
   **粒子 `0x424630BFE2FF5E99`（= `OrbitalStun` 的爆炸粒子）** + bank `0x19F0EA7F8790BF4C` + 2 个 wwise_stream。
   ⇒ **EMS 的爆炸粒子只在 EMS 打击自己的资产包里，120mm 的呼叫根本不会加载它** ⇒ 有伤害/无视觉。
3. delta 想换的 `+0x10 = 0xA00E6327E3747A50` 在资源索引（`D:/mod/index/all_entries.json` 322,711 条 /
   3,425 包）里 **查不到** —— 本 build 没有这个 bank ⇒ 即使照抄 delta 也没有 EMS 音效（悬空引用）。
   真正存在的是 `0x19F0EA7F8790BF4C`。

修法（下一步实验，纯数据/资源层，不碰实体行以外）：

- **整包驻留**：`python tools/whole_package_patch.py build --package 1e6c958b95568dd7 --host f6fb08cc02d24255 --index <下一个空位> --out D:/mod/out/ems120-res-patch`
  （与 89 万能槽 Nova+Warp 同一配方，见 [RESOURCE-RESIDENCY](../engine/RESOURCE-RESIDENCY-26088801.md)）；
- 可选把 120mm LoadoutPackage `+0x10` 换成真实存在的 EMS bank `0x19F0EA7F8790BF4C`（补音效）。

### 8.9 复算命令

```bash
# ① 整块 24 行（含 +0x40 清单）
python tools/block_rows.py --block 0xCDBC43D8 --width 48

# ② 行 → 赛博战备：HD2Runtime 研究档
python - <<'EOF2'
import json
d=json.load(open(r"D:/mod/refs/hd2runtime-repo/research/offensive-stratagem-runtime-F5FEE03DCFDB.json",encoding="utf-8"))
for s in d["stratagems"]:
    print(s["name"], s["historicalIdentity"]["payloads"], s["rootProjectiles"])
EOF2

# ③ wiki 四字段（num_bombs / num_salvos / area_size / fire_height）
python - <<'EOF2'
import sqlite3,json
con=sqlite3.connect(r"D:/mod/refs/wiki/wiki.sqlite")
for k,j in con.execute("select key,json from stratagem"):
    d=json.loads(j)
    if d.get("num_bombs"): print(k,d["num_bombs"],d["num_salvos"],d["area_size"],d["fire_height"])
EOF2

# ④ 弹种号 → 射弹行：扫描 projectile 明文 +0x00（行基址 44，stride 272）
```
