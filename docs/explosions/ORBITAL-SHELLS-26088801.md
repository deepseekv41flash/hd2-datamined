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
- 每轮是否重复同一清单 **✓✓ 实机（2026-10-31 实机二，§8.10）**：`nb=7` + 7 种弹头，
  用户确认「全部弹种都出现，且每轮都是这个顺序」⇒ **清单每轮重复、按发序消耗**。

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

修法（已执行，**两条都实机验证 ✓✓**，2026-10-31）：

- **整包驻留**：`python tools/whole_package_patch.py build --package 1e6c958b95568dd7 --host f6fb08cc02d24255 --index 5 --install`
  （与 89 万能槽 Nova+Warp 同一配方，见 [RESOURCE-RESIDENCY](../engine/RESOURCE-RESIDENCY-26088801.md)）
  → **EMS 蓝色电磁爆炸特效出现 ✓✓**（此前"有伤害无视觉"根因确认 = 资产包未驻留）。
- 把 120mm LoadoutPackage `+0x10` 换成真实存在的 EMS bank `0x19F0EA7F8790BF4C`
  （产物 `out/audiobank/`，装盘 md5 `3982ff23`，只改 8 B）→ **所有声音均正常 ✓✓**（EMS 有专属音，
  120mm 原 bank 也没被顶掉）⇒ `LoadoutPackageComponentData +0x10` = **该呼叫要加载的 wwise bank 声明**，
  且 bank 加载是**叠加**的（`+0x08` 资产包内自带的 bank 不受影响）。

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

### 8.10 2026-10-31 实机二：7 发 7 弹种（逐发不同弹头）**✓✓**

**配置**（`out/thmixed/step1.plain` → 装盘 md5 `9b944279`，内容哈希锚点 `0x8E49771B181FFAA1` 未变）：

- `BombardmentComponentData` row19：`+0x04=7`、`+0x18=5`、`+0x24=10.0`、
  **`+0x40=(197,76,82,238,200,251,160,0)`**（无任何 `_Cheap` 槽）；
- `LoadoutPackageComponentData`：`+0x08` 不变、`+0x10` 仍是 delta 的悬空 bank `0xA00E6327E3747A50`
  （音效实验留到下一轮，保持单变量）；
- 资源驻留 `data/f6fb08cc02d24255.patch_5…10` 六个整包：
  EMS `1e6c958b95568dd7`、380mm `fe3ef44300e4a1e2`、Napalm `96cedf4706334c5f`、
  Gas `6369816737a36a40`、Smoke `bf35e874ac3a3b5a`、Airburst `f51342b25542a582`
  （含各自 `.gpu_resources` / `.stream`）。

**实机结果**：

| 观察项 | 结果 |
|---|---|
| 7 种弹头是否都出现 | **全部出现** |
| 每发顺序 = `+0x40` 槽序 | **是**：120mm HE → EMS → 380mm → Napalm → Gas → Smoke → Airburst |
| 每轮是否重复同一串 | **是**（「每轮都是这个顺序」） |
| 每轮发数 = `+0x04` | ✓ 7 发（`+0x18=5` 轮，理论共 35 发） |
| 是否崩溃 | 无 |

⇒ **结论**：`+0x40` = 「**每轮按发序使用的弹种清单，每轮重复**」。清单 ≤ 8 槽；官方行 `nb=7` 正好用满 7 槽。
§8.6 的「每轮重复」由 ⚠ 升为 ✓✓；仅剩 `nb > 8`（加特林 60 发 / 4 槽）的循环规则未证 ⚠。

**可复现配方（纯数据 + 资源驻留）**：

1. `BombardmentComponentData` 行：`+0x04` = 每轮发数 N（≤8）、`+0x40` = N 个 `ProjectileType`（弹种见 §8.4）、
   `+0x18` = 轮数、`+0x24` = 散布半径；
2. 每个新弹种的**资产包**整包驻留到常驻宿主（包 id = 该战备实体 `LoadoutPackageComponentData +0x08`）：
   ```bash
   python tools/whole_package_patch.py build --package <donor 包 id> \
       --host f6fb08cc02d24255 --out D:/mod/out/res-<id> --install
   ```
3. 音效 bank 靠 `LoadoutPackage +0x10` 声明，而**每行只有一个 bank 名额** ⇒ 多弹种混音是当前已知限制（⚠ 待解）。

**回滚**：实体表还原 `D:/mod/backups/spray-capsule/generated_entities.vanilla.dl_bin`；
删除 `data/f6fb08cc02d24255.patch_5…10` 及其 `.gpu_resources` / `.stream` 伴生文件。

### 8.11 非圆形散布（Orbital Walking Barrage）：`+0x60`（行走速度）+ `+0x24`（圆斑半径）（✓ 离线两样本 + **✓✓ 实机 E1/E2/E4 + ✓ 实机 E3b/F1**）

**结论**：圆斑半径仍是 `+0x24`（`area_size`）；「边走边打」的形状由 **`+0x60`（f32，行走速度）** 控制：

- `+0x60 = 0` ⇒ 原地圆形散布（24 行里 21 行如此；**✓✓ 实机 E2**：把 walking 的 3.0 改 0 后「全打一点」）
- `+0x60 > 0` ⇒ 行走投送：弹着中心沿一个方向连续移动，
  **每轮推进 = `+0x60 × [(每轮发数−1)×+0x08 + +0x1C]`**（模型 B，**✓✓ 实机 F1**：预测 9 m / 目测 9 m；
  E1 预测 18 vs 目测 ~20 ✓）。

#### 8.11.1 证据（✓ 可复算）

1. **只差 2 格**：380mm（row9）与 walking（row21）同为 3 发/轮 × 5 轮、弹种清单完全相同
   `[82,270,270]`、`+0x08/+0x1C` 相同，192 B 行内**只有两个 dword 不同**：
   `+0x24` 36 → **25**；`+0x60` 0 → **3.0**。其余 46 格逐字节相同 ⇒ 形状没有第二个数据开关。
2. **全表扫描**：24 行里 `+0x60` 非零只有 3 行 —— walking = **3.0**、
   **`ORBITAL. WALKING BARRAGE SMOKE`（row22，未发布战备 id **64**）= 15.0**、
   世界事件「火山」（row7，`[321]` = `World_VolcanoStrike`）= 0.1；其余 21 行全 0。
3. **两个 walking 变体独立佐证**：walking HE（3.0）与 walking smoke（15.0）都非零、数值不同
   ⇒ `+0x60` 是**可调步进**而不是布尔开关。
4. **HD2Runtime 也没暴露它**：`StratagemAuthoringCapabilities` 里 walking 与 380mm 的 78 个字段
   完全同构（只有战备名前缀不同），没有任何形状/方向项 ⇒ 这解释了为什么此前只解到圆形部分。
5. **方向不在行里**：380mm vs walking 46 格全同，没有方向/角度字段
   ⇒ 行走方向应由运行时决定（信标/投送者朝向，或投送资源）⚠ 未证。

#### 8.11.2 顺带发现：未发布战备 `ORBITAL. WALKING BARRAGE SMOKE`（id 64）

对 `generated_stratagem_settings.dl_bin` 的 payload 指针（`+0x98/+0xA0`）反查，row22 的宿主是：

| 项 | 值 |
|---|---|
| 内部名 | **`ORBITAL. WALKING BARRAGE SMOKE`** |
| 战备 id | **64**（`+0x00`），`+0x3C` = 5（Orbital） |
| 面板 | 冷却 **120 s** · 呼叫 **3 s** · 无限次 |
| 弹幕行 | row22：**1 发/轮 × 6 轮**、area **5**、`+0x60 = 15.0`、弹种 **251**（smoke 弹丸） |
| wiki | **无条目**（未发布） |

⇒ 它是第二个 walking 样本，而且**表里齐全**：可用 `+0xC8` 额外战备技术链到常规战备上实机调用
（同 [RECON-SHODAN-EXTRA-STRATAGEM](../cases/RECON-SHODAN-EXTRA-STRATAGEM-26088801.md)），
直接观察 `+0x60 = 15.0` 的「行走烟幕」行为。

#### 8.11.3 待实机（单变量；每次只改一个 f32 + 保哈希，成本极低）

| 实验 | 改动 | 预期 / 判定 | 状态 |
|---|---|---|---|
| **E1** | 380mm `+0x60` 0 → 3.0（其余不动） | 380mm 落点开始「走」⇒ `+0x60` = 模式开关 + 速度 | **✓✓ 实机（§8.11.4）** |
| **E2** | walking `+0x60` 3.0 → 0（其余不动） | walking 退回原地圆斑（E1 的反证） | **✓✓ 实机（§8.11.5）** |
| **E3** | walking `+0x60` 3.0 → 10.0 | 每轮推进距离按比例变大 ⇒ 线性验证 | ⚠ 未做（可选，= F2） |
| **E3b** | 380mm `+0x1C` 3.0 → 6.0（其余保持 E1 配置） | 推进距离随轮间隔变 ⇒ 验证「推进 = 速度×轮周期」 | **✓ 实机：20 → 36 m/轮（§8.11.5）** |
| **E4** | walking `+0x24` 25 → 2 | 横向散布收窄 ⇒ `area_size` 对 walking 同样生效 | **✓✓ 实机（§8.11.5，紧贴一点）** |
| **E5** | `+0xC8` 链出 id 64（walking smoke） | 直接看 `+0x60 = 15.0` 的行走烟幕形态（顺带验证未发布战备可调用） | ⚠ 未做（可选） |
| **F1** | 380mm `+0x1C` 6 → **0**（其余保持本版） | 完全不走 ⇒ 轮周期是 `+0x1C` 的纯函数（模型 A）；仍走一小段 ⇒ 轮周期含 `+0x08` 项（模型 B/C） | **✓ 实机：仍走但不远 ⇒ A 被否（§8.11.6）** |
| **F2** | 380mm `+0x60` 3 → **6**（`+0x1C`=3） | 每轮推进是否翻倍（≈36–40 m）⇒ 核对 `+0x60` 线性 | ⚠ 未做（可选） |

#### 8.11.4 实机 E1（2026-10-31）：`+0x60` = 行走速度 ✓✓

**配置**（`out/walk380/`，装盘 md5 `b03a8825`，从**原版明文**构建，只动 380mm row9 两格）：

| 字段 | 原值 | 改后 | 角色 |
|---|---|---|---|
| `+0x60` | 0 | **3.0** | **E1 唯一未知变量** |
| `+0x24` | 36 | **2.0** | 观察辅助（该字段 36→2 此前已实机验证，不算新变量） |
| `+0x04` / `+0x18` / `+0x40` | 3 / 5 / `[82,270,270]` | 不变 | — |

**实机结果**：

- **逐轮向同一方向推进** ✓（不是一团）；共 **6 轮**（基础 5 + 弹幕「+1 轮」升级，与旧记录一致）；
- **5 个间隔共推进约 100 m** ⇒ **约 20 m/轮**。

**定量对账（速度模型）**：轮周期 = `(3−1)×+0x08(1.5 s) + +0x1C(3.0 s)` = **6.0 s**
⇒ 3.0 m/s × 6 s = **18 m/轮**，5 个间隔 ≈ **90 m**，与目测 ~100 m 在误差内吻合。

**交叉验证（未实机，仅数据）**：未发布的 `ORBITAL. WALKING BARRAGE SMOKE`（row22）
`+0x60 = 15.0`、1 发/轮、`+0x08 = 1`、`+0x1C = 1` ⇒ 轮周期 ≈ 1 s ⇒ **15 m/轮**，5 个间隔 ≈ 75 m ——
形态应是「一条 75 m 左右、由 6 团烟组成的直线烟墙」；可用 E5 链出来验证。

⇒ 至此**非圆形散布的完整字段组**：`+0x60`（速度，0=圆形）、`+0x24`（围绕移动中心的圆斑半径）、
`+0x08`/`+0x1C`（轮内发间隔 / 轮间隔，决定每轮推进量与节奏）、**方向 = 运行时决定**（行里无角度字段）。

#### 8.11.5 实机 E2 / E3b / E4（2026-10-31 晚）

**配置**（`out/walk_multi/`，装盘 md5 `3ebd5454`，原版明文构建；同一局各叫一次）：

| 战备 | 改动 | 相对上一版 |
|---|---|---|
| walking（row21） | `+0x60` 3.0 → **0**、`+0x24` 25 → **2** | 双变量（E2 + E4） |
| 380mm（row9） | `+0x1C` 3.0 → **6.0** | 相对 E1 只动这一格（E3b 单变量） |

**结果**：

| 实验 | 现象 | 判定 |
|---|---|---|
| **E2** | walking **完全不移动**：6 轮 × 3 发全部砸在同一个 ~2 m 小点 | **✓✓** `+0x60` 是**唯一**行走开关（E1 ↔ E2 互为反证） |
| **E4** | 同上，小团非常紧（半径 2 m） | **✓✓** `+0x24` 对 walking 同样生效 |
| **E3b** | 380mm **每轮推进 36 m**（E1 同 `+0x60=3.0`、`+0x1C=3.0` 时 ≈20 m/轮） | **✓** 推进随轮间隔增大；定量模型见下 |

**定量拟合**（观测点：`+0x1C=3 → ≈20 m/轮`；`+0x1C=6 → 36 m/轮`；`+0x60` 固定 3.0）：

| 候选模型 | `+0x1C=3` 预测 | `+0x1C=6` 预测 | 与实测（≈20 / 36） |
|---|---:|---:|---|
| **A：每轮推进 = `2 × +0x60 × +0x1C`** | 18 | **36** | E1 −2（估读）、E3b **0** ✓ 更优 |
| B：每轮推进 = `+0x60 × [(nb−1)×+0x08 + +0x1C]` | 18 | 27 | E3b −9 ✗ |

⇒ 当时倾向**模型 A**，但「×2」来源未解；**该倾向已被 F1 否掉**（`+0x1C`=0 仍走一小段 ⇒ 轮周期含 `+0x08` 项），
最终定稿为**模型 B**（见 §8.11.6）。
**定系数还需两个点**：

- **F1（关键）**：380mm `+0x1C` 6 → **0** ⇒ 若完全不走 = 轮周期是 `+0x1C` 的纯函数（A 成立）；
  若仍每轮走 ~13–20 m = 轮周期还含 `+0x08` 项（B 成立）。
- **F2**：380mm `+0x60` 3 → 6（`+0x1C`=3）⇒ 每轮推进是否翻倍（≈36–40 m），核对 `+0x60` 线性。

**顺带修正 §8.11.4 的 smoke 预测**：按最终模型 B，未发布 `ORBITAL. WALKING BARRAGE SMOKE`
（row22：`+0x60=15`、nb=1、`+0x08=1`、`+0x1C=1`）每轮推进 = `15×[(1−1)×1+1]` = **15 m/轮**，
5 个间隔共 ≈ **75 m** 直线烟墙（与 §8.11.4 的初版预测一致）；仍待 E5 实机。

#### 8.11.6 实机 F1（2026-10-31 晚，`+0x1C`=0）：模型 A 被否 ✓

**配置**（`out/walkF1/`，md5 `7f8086ca`，原版明文）：380mm `+0x1C` 6.0 → **0**、
`+0x60`=3.0、`+0x24`=2.0、每轮 3 发、5 轮（+升级）、弹种不变。

**结果：仍走，但走得不远。**

**判读**：

- **模型 A（每轮推进 = `2×+0x60×+0x1C`）被否**：它在 `+0x1C=0` 时预测**完全不走**，实测仍走一小段。
- ⇒ 轮周期里**必然含 `+0x08` 项**（与「每轮 3 发、发间隔 1.5 s」一致），推进发生在整个轮周期内。
- 剩余两个候选（`+0x60`=3.0）：

| 模型 | 每轮推进（`+0x1C`=0） | 5 个间隔总长 | 对 E1 / E3b 的预测（实测 ≈20 / 36） |
|---|---:|---:|---|
| **B**：`+0x60 × [(nb−1)×+0x08 + +0x1C]` = 3.0×3 | **9 m** | ≈45 m | 18 / 27（残差 −2 / **+9**） |
| **C**：`+0x60 × [nb×+0x08 + +0x1C]` = 3.0×4.5 | 13.5 m | ≈67 m | 22.5 / 31.5（残差 **−2.5** / +4.5） |

⇒ **收口（✓✓）**：F1 目测**每轮 ≈ 9 m**，与 **B 的精确预测 9.0 m**（`3.0×(3+0)`）一致 ⇒ **模型 B 成立、C 被否**
（C 会预测 13.5 m）。三点对账：F1 9/9 ✓、E1 18/~20 ✓、E3b 27/36（⚠ 差 +9 m，记为估读/待将来复核）。

**定稿公式**：

```
每轮推进（米） = +0x60 × [ (每轮发数 − 1) × +0x08 + +0x1C ]
整条线长度     ≈ 每轮推进 × (轮数 − 1) + 首轮圆斑直径
```

（`+0x60`=行走速度 m/s、`+0x08`=轮内发间隔 s、`+0x1C`=轮间隔 s、`+0x24`=每轮圆斑半径 m；方向由运行时决定。）

## 9 `generated_modifier_settings` =「modifier → 目标实体 + delta 补丁」注册表（2026-10-31 新解）

> **一句话**：`entity_deltas` 里那些"只被 `modifier_settings` 引用一次"的 AddPath **不是孤儿** ——
> 这张表就是它们的调用点：每行 = `{modifier id, 目标实体数组, delta AddPath}`，目标实体恰恰是**战备的载荷实体**。
> 于是「未发布升级」有了统一的枚举入口：本 build 共 **15 行**，其中 **11 行是弹幕变体**（含 §7 的 120mm EMS）。

### 9.1 表结构（✓ 离线，本 build）

`generated_modifier_settings.dl_bin` 只有 **1,764 B**：`u32 行数 = 15`，之后 15 个 `LDLD` 容器（24 B 头）：

```
LDLD | ver=1 | type=0xDCEA3AEF | payload 长度 | 1 | 0 | 0 | payload…
```

payload = `u32 modifier_id + u32(=1)` + 若干 `(u64 数组偏移, u64 个数)` 引用数组；**常见 3 组**：

| 组 | 内容 | 证据 |
|---|---|---|
| 1 | 固定（偏移 `0x18`，1 项） | 15 行全部同形；语义 ⚠ |
| 2 | **目标实体数组**（1～8 项） | 取值与 `generated_stratagem_settings +0x98` 的载荷实体数组**精确重合**（如 `0x2D3BD00B1ED411B1` = 120mm 弹幕载荷）|
| 3 | **delta AddPath 数组**（1 项） | 每个值都在 `ComponentEntityDeltaStorage` 的 hashmap 里，`ref_scan.py delta-show` 可解 |

15 行里 **11 行**的目标是 5 条轨道弹幕（120mm/加特林/纳帕姆/380mm/行走）的载荷实体、补丁打在 comp 196
`BombardmentComponentData`；另 **4 行**是别的类型（哨戒炮 / 轨道激光 / 未知，组件 227/257/311，⚠ 未解）。

### 9.2 `effect 1426 / 1427` 的 hash 要分两层看（✓ + ⚠）

社区工具的 `[effect 1426/1427]` 是 **GWE 目录 id**，它的 `values` 是 `(32 位值, 序号)`：

| 项 | effect 1426 | effect 1427 |
|---|---|---|
| GWE values | `0x8DFA4622`, 4 | `0x166D0C91`, 0 |
| 该 32 位值在 55 张明文表里 | **0 命中** | **0 命中** |
| 数据层 AddPath（delta 键） | `0xAE4D54F6CB8CC350`（§7 已解） | **`0xDB465C00E23CDD50`（本节新定位）** |
| modifier 行 / 目标 | #6（id `0xCDD51BC6`）→ **120mm 弹幕**载荷 `0x2D3BD00B1ED411B1` | #2（id `0x4DD68526`）→ **加特林弹幕**载荷 `0x2F257B91037AC421` |
| 判据 | delta 内容 = EMS/HE 混编（已知） | 目标 = 加特林 + **唯一带火焰模板的弹种**（§9.3）|

⇒ `0x8DFA4622 / 0x166D0C91` 是**显示名 locid**（本 build 的字符串里没有这两条 ⇒ 未发布），**不是** delta 键；
所以 `delta-show 0x166D0C91` 必然报「没有这个 AddPath」；真正能查的是数据层的 64 位 IdString。
（同批的 `1428 = 0x0C064A00` 在 55 表同样 0 命中，⚠ 未定位。）

### 9.3 `effect 1427` =「轨道燃烧加特林」：modifier #2 的 delta（✓ 离线）

```text
$ python tools/ref_scan.py delta-show 0xDB465C00E23CDD50
AddPath 0xDB465C00E23CDD50 的 delta 补丁：
  comp  196 ?   +64   size 32  hex 4a000000 02010000 02010000 02010000 00000000 …
  comp  196 ?   +36   size 4   hex 0000e040  u32 1088421888
  comp  196 ?   +4    size 4   hex 3c000000  u32 60
```

| 写入 | 值 | 含义 |
|---|---|---|
| `+0x40` | `(74, 258, 258, 258)` | 弹种清单（§8 已证：第 i 槽 = 每轮第 i 发，多出的发按清单循环）|
| `+0x24` | f32 `7.0` | 与原行 row12 相同（不变） |
| `+0x04` | `60` | 与原行相同（不变） |

**为什么是"燃烧"**：弹种 **74** = 射弹行 40，`calibre=23`、速度 1050、质量 400（与原版加特林弹 79 同弹道），
但 `+0x90` 命中爆炸 = **108**：半径 `2.5 / 5 / 6.5`（与 `Cannon_23mm` 的爆炸 375 同尺寸）、
**`FireTemplate = 2`（≠0 ⇒ 带火焰模板）**、伤害类型 `0x17A`（375 是 `0x179`，同族不同变体）。
对照**原版**加特林行（§8.3 row12）：`[79, 43, 43, 43]`、`nb=60`、`ns=4`、`area=7`，其中 79 的爆炸 375
**无**火模板、43 = 无爆炸 ⇒ 原版是纯动能加特林。

⇒ 本变体**只换弹种清单**（60 发/轮、4 轮、散布 7 全不变），把会爆的那一发换成**燃烧 23mm 弹**：
这就是「轨道燃烧加特林」的效果体。同族 258 = 无爆炸变体（爆炸 0），负责其余三发的"省事"弹。
⚠ `nb=60 > 8` 的消费规则已实机证为**按发循环**（§9.10，2026-11-01：燃烧弹远多于 4 发）⇒
**每 4 发 1 发燃烧弹，整条 4 轮共 60 发燃烧弹**，60 发里其余 45 发是 258（无爆炸）。

### 9.4 顺带解出的同族变体：本 build 的 11 条弹幕变体（✓ 离线）

| # | modifier id | 目标战备（载荷实体） | delta AddPath | 补丁内容 | 解读 |
|---:|---|---|---|---|---|
| 0 | `0x1DA06C9E` | 纳帕姆(109) **+** 加特林(4) | `0x98BE8240B2D75239` | `+0x24=100.0`、`+0x1C=1.0` | 双目标：大散布/短轮间隔变体 ⚠ |
| 1 | `0x818CC7AE` | 纳帕姆(109) + `0xB5972922B4ECA89B`（**悬空**：非实体非 delta） | `0x5D8DCF5BD8C6B394` | `+0x24=10.0`、`+0x1C=1.0` | 小散布变体 ⚠ |
| **2** | **`0x4DD68526`** | **加特林(4)** `0x2F257B91037AC421` | **`0xDB465C00E23CDD50`** | `+0x40=(74,258,258,258)` | **燃烧加特林（effect 1427）** |
| 5 | `0x90E8CA22` | 纳帕姆(109) | `0x8D49E41FDFCF6784` | `+0x40=(238,242,242,200)`、`+0x04=8`、`+0x18=6` | 纳帕姆+毒气变体（`200=Orbital_Gas`）**✓✓ 实机（2026-11-01）：8 发/轮 × 6 轮、第 4 槽绿雾正常** |
| 6 | `0xCDD51BC6` | 120mm(139) `0x2D3BD00B1ED411B1` | `0xAE4D54F6CB8CC350` | 见 §7/§8.7 | **120mm HE/EMS（effect 1426）** |
| 7 | `0x01137871` | 380mm(128) | `0x9EF9B0DF05BC5F67` | `+0x40=(82,270,270,238)`、`+0x04=5`、`+0x18=7` | 380mm 混装燃烧弹变体 **✓✓ 实机（2026-11-01）：5 发/轮 × 8 轮（7+升级 1）、每第 4 发燃烧弹** |
| 10 | `0x5418C098` | 380mm(128) | `0xFC165F5604FD3911` | `+0x40=(101,101,101)` | 380mm 迷你核弹变体（101=`SEAF_Gun_Mini_Nuke`，cal 360、爆炸 288）**✓✓ 实机（2026-11-01）** |
| 11 | `0x7CFB6A7E` | 加特林(4) | `0xF1B196470BF9B2C1` | `+0x40=(67,67,67,67)` | 核弹加特林变体（67=`Nuke`，cal 1000、爆炸 92）。**发数/轮数没改**：`+0x04` 仍 **60**、`+0x18` 仍 **4**、`+0x24` 仍 7.0 ⇒ 每轮 60 发；因为 4 槽**全是同一个值 67**，无论"循环清单"还是"末槽填充"（§9.10），**60 发都会是核弹**（这个结论对循环规则不敏感）；4 轮共 240 发 |
| 12 | `0x443645E5` | walking(21) | `0xAB3E0830D9A27376` | `+0x04=3`、`+0x18=12` | 12 轮行走变体 **✓✓ 实机（2026-11-01）：3 发/轮 × 13 轮（12+升级 1）** |
| 13 | `0x3F0B8BBC` | walking(21) | `0x308EB83C11A21F95` | `+0x04=6`、`+0x18=5`、`+0x60=1.0` | 6 发/轮慢走变体 |
| 14 | `0x2A83FD6B` | walking(21) | `0x08D58CB1BF65F7A9` | `+0x40=(251,197,139,139)`、`+0x04=4`、`+0x18=5`、`+0x60=2.25`、换包 | 行走烟幕变体（delta 键 = 未发布战备 id 64 的载荷实体）|

另 4 行非弹幕（组件已定名：**227** `HealthComponentData` / **257** `ExplosiveComponentData` /
**311** `OrbitalAbilityComponentData`，见 §9.12）：#3 `0xD295BD78`（200 B，7 组引用，comp227 `+0=20`）、
#4 `0x24CFC5BA`（7～8 个哨戒炮载荷，comp227 `+0=600`）、#8 `0x8C65F7AC`（轨道激光载荷，comp311
`+0x1CC=35 / +0x1D4=20 / +0x1D8=100`）、#9 `0xC0C3FDB3`（**雪球** `0xCCFAE6D4A601C741`，
comp257 `+0x24` 爆炸类型 **73 `Snowball_Stun` → 176 `HighExplosive`**，见 §9.12）。

### 9.5 状态与未定（诚实标注）

- **✓** 表结构、目标实体映射（与战备 `+0x98` payload 精确重合）、delta 内容、火焰模板判定都可复算。
- **✓✓** 激活通道已定证（§9.15）：这 15 行**不是舰船升级**，而是**行星级「实验性战备变体」修饰符**，
  由 **GWE `effectType=94`** 激活（`values[0]` = modifier id）；抓包目录里只出现 **3 条**
  （#6 120mm HE/EMS = effect 1345、#2 燃烧加特林 = 1346、#14 行走烟幕 = 1350），其余 12 条服务器未提供；
  `[effect 1426/1427/1428]` 是另一回事（type32 临时配发**未发布新战备**，战备 hash 本地 0 命中）。
- **✓** 非弹幕 4 行的组件 **227 `HealthComponentData` / 257 `ExplosiveComponentData` /
  311 `OrbitalAbilityComponentData`** 已定名（§9.12）；`Explosive +0x24` = 爆炸类型 id 已由
  HD2Runtime 链式证据 + 本 build owner 反查双重确认（§9.12 #9）。

### 9.6 复现命令（✓ 只读）

```bash
python tools/modifier_scan.py                                  # 15 行全解：目标战备 → delta → 字段值（弹种带 FIRE 标注）
python tools/ref_scan.py delta-show 0xDB465C00E23CDD50         # 燃烧加特林变体
python tools/ref_scan.py delta-show 0xAE4D54F6CB8CC350         # 120mm EMS 变体（§7）
python tools/ref_scan.py delta-show 0x00000000166D0C91         # ✗ 查不到：32 位是 locid，不是 delta 键
```

### 9.7 装盘包：手工应用「燃烧加特林」变体（✓ 离线装盘 + 回读一致，待实机）

**改动**（`out/gatling-fire/step1.plain`，保哈希编辑）：`BombardmentComponentData` 行 12（键
`0x2F257B91037AC421` = Orbital Gatling Barrage 载荷实体）的弹种清单 4 个槽：

| 字段 | 原版 | 变体 |
|---|---|---|
| `+0x40` | 79 | **74**（23mm，命中爆炸 108 = 带 `FireTemplate=2`） |
| `+0x44` | 43 | **258**（同族无爆炸、带跳弹音） |
| `+0x48` | 43 | **258** |
| `+0x4C` | 43 | **258** |

delta 里的 `+0x04=60` / `+0x24=7.0` 与原行**同值**（no-op），字节未动；发数、轮数、散布不变，只换弹种。
⇒ 按 4 槽**循环**（`nb=60>8` 规则已由 §9.10 实机确认）：每 4 发里 1 发燃烧弹、其余 3 发无爆炸弹；
整条弹幕 60 发燃烧（这一点又被用户 2026-11-01 的实测「燃烧远多于 4 发」直接印证）。

**门禁与产物**：

| 项 | 值 |
|---|---|
| 编辑门禁 | G1/G2/G3（`0x8E49771B181FFAA1` 不变）/G4/G6/G7/G8/G9 全 PASS；diff 仅 4 槽 + 末块尺寸字段 + 校正字 |
| 明文 | 47,259,408 B，md5 `29c079e7522f51d204e877a5832d4700` |
| 封包 | 47,259,456 B，md5 `1498b3c827e1e7875d28ffa11e9f2002`，sha256 `9f46d7fdfe9ffe28` |
| 装盘 | `dlbin_deploy.py install`，回读明文 md5 与 step1.plain **逐字节一致**；账本原版备份 sha256 `4121f332a6d16307`（`D:\mod\backups\dlbin-deploy\game\generated_entities.dl_bin`）|
| 资源 | **不需要额外驻留**：弹种 74/258 与 79/43 的行内资源字段完全相同（只差爆炸 / 音效 / 2 字节标志），爆炸 108 的粒子 file_id 与 375 **同值**（`0x4f069f48ce3cdb45`）⇒ 粒子资源原版就已驻留 |

**实机观察清单**（单变量；进游戏前先完全退出重启）：

1. 带 **Orbital Gatling Barrage（轨道加特林火力网）**，任意任务叫一发；
2. 看落点：是否出现**小火苗/燃烧地面**（每 4 发 1 发），敌人是否被点燃；
3. 异常项：崩溃、灰块、无伤害、声音错乱；
4. 判读：有火焰+点燃 → effect 1427 效果体 `✓✓`；有伤害无火焰 → 火焰特效资源未驻留（FireTemplate）；
   崩溃/无效 → ✗ 回滚。

**回滚**：

```bash
python /d/mod/tools/dlbin_deploy.py restore --file generated_entities.dl_bin
# 或：cp "/d/mod/backups/spray-capsule/generated_entities.vanilla.dl_bin" \
#        "/d/SteamLibrary/steamapps/common/Helldivers 2/data/game/generated_entities.dl_bin"
```

**实机结果（2026-10-31 23:5x，用户回报）**：Orbital Gatling Barrage **有点燃效果** ⇒
effect 1427（燃烧加特林）效果体 **`✓✓` 实机确认**（弹种 74 的 `FireTemplate=2` 在游戏内生效；
不需要任何资源驻留）。三态：从 ⚠ 升为 **✓✓**。

### 9.8 下一轮装盘：Napalm 毒气弹 + 380mm 迷你核弹（✓ 离线装盘，待实机）

两个变体各改一条弹幕行，**互不影响、同一局可同测**：

| 变体 | 行（键） | 改动 | 效果 |
|---|---|---|---|
| 纳帕姆+毒气（modifier #5，delta `0x8D49E41FDFCF6784`） | Napalm row14（`0xA16AB4FF66AE6970`） | `+0x04` 5→**8**、`+0x18` 5→**6**、`+0x4C` 0→**200** | 8 发/轮 × 6 轮，弹种 `(238,242,242,`**`200`**`)` = 纳帕姆主/Cheap/Cheap + **毒气弹**（`Orbital_Gas`）|
| 迷你核弹（modifier #10，delta `0xFC165F5604FD3911`） | 380mm row9（`0xEF66B417EDC3B1D6`） | `+0x40/44/48` 82,270,270→**101,101,101** | 3 发/轮 × 5 轮，弹种 = **SEAF 迷你核弹**（proj 101，cal 360，命中爆炸 288：半径 17/25/45、震屏 250）|

**资源驻留（必须，否则有伤害无特效）**：两条变体都用了原战备资产包里没有的粒子/音效，按 §8.8/§8.10 的
整包驻留配方各打一份（宿主 `f6fb08cc02d24255`）：

| 补丁（该宿主的第 N 槽） | 源包 | 条目 | 尺寸（toc/gpu/stream） | 补的资源 |
|---|---|---|---|---|
| `f6fb08cc02d24255.patch_0` | `6369816737a36a40`（毒气打击包） | 7 | 939,072 / 512 / 276,926 B | 毒气爆炸粒子 `0xAF8AE08BBFF2BFFE` + bank |
| `f6fb08cc02d24255.patch_1` | `184c510a7a3678f9`（核爆包） | 79 | 2,061,184 / 47,783,128 / 12,757,904 B | 核爆爆炸粒子 `0x4152B17F76EAE64F`（爆炸 288）+ 音效 |
| `f6fb08cc02d24255.patch_2` | `0296cbe5005ea13f`（SEAF 炮弹包） | 143 | 1,415,808 / 20,288,242 / 33,550,886 B | 迷你核弹弹种 101 的飞行粒子 `0x547CBE12…` / `0xBD56B584…` / `0x9FB12721…` |

> ⚠ **番号是「每个宿主包各自从 0 连续」**，不是全局序号 —— 见下方修正记录。

**修正记录（2026-11-01）：上一测两个症状的根因 = 补丁序号跳号**

上一版把两份驻留补丁命名成 `f6fb08cc02d24255.patch_2` / `patch_3`（当时盘上 `patch_0/1` 属于**另一个宿主**
`9ba626afa44a3aa3`，我按"全局序号"理解去接号）。实测规则是**每个宿主包自己的槽位从 0 连续**：
该宿主缺 0/1 ⇒ **引擎合并链在 0 就断**，两份补丁**静默不生效**（文件在磁盘上、大小/md5 都对，但引擎当没看见）：

- 毒气弹：爆炸 82 的粒子没驻留 ⇒ 绿雾不出现，画面里只剩纳帕姆的火焰 ⇒「特效变成燃烧弹的」；
- 380mm 迷你核弹：爆炸 288 的粒子没驻留 + 弹种 101 的飞行粒子缺失 ⇒ 看起来「呼叫后没反应」。

修法：重命名为 `patch_0` / `patch_1`（+ 追加 `patch_2` 补弹种 101 的飞行粒子）。`patch_compose.py scan` 复核：

```
9ba626afa44a3aa3: 槽位 [0, 1]     空洞 无
f6fb08cc02d24255: 槽位 [0, 1, 2]  空洞 无
```

顺带记两条纪律：**① 装完必须跑 `python tools/patch_compose.py scan --data <game>/data` 验"空洞 无"；
② `whole_package_patch.py --index` 只在"续同一宿主已有链"时手填，新宿主必须用默认值（从 0 起）。**

**产物与门禁**：

| 项 | 值 |
|---|---|
| 编辑门禁 | G1/G2/G3（`0x8E49771B181FFAA1`）/G4（6 处）/G6/G7/G8/G9 全 PASS |
| 明文 | 47,259,408 B，md5 `d69fcd381246ddcc2a7bac7d049e8f88` |
| 封包 | 47,259,456 B，sha256 `3a6b4f10ef1db435` |
| 装盘 | 回读明文与 step1.plain 逐字节一致；盘上补丁 5 组（宿主 `9ba626…` 的 patch_0/1 原存 + 宿主 `f6fb08cc02d24255` 的 patch_0/1/2 本轮） |
| 基线自检 | `game_baseline check`：仅 entities 1 个文件变动 |

**实机观察清单**（完全退出游戏再启动；一局内依次叫两条战备）：

1. **Napalm Barrage（轨道纳帕姆火力网）**：观察 8 发/轮 × 6 轮、其中是否出现**绿色毒气云**（每轮第 4 发）；
2. **380mm HE Barrage（轨道380毫米高爆火力网）**：观察是否变成 **3 发迷你核弹**（大半径爆炸、强震屏）；
3. 异常项：崩溃、灰块、无伤害、声音错乱；
4. 判读：毒气云可见/有毒气伤害 → 变体生效；核爆视觉+大范围伤害 → 变体生效。

**实机结果（2026-11-01，用户回报）**：**两项都正常** —— 纳帕姆 8 发/轮 × 6 轮、每轮第 4 发绿雾；
380mm 3 发/轮 × 5 轮迷你核弹、爆炸正常。两条变体三态升 **`✓✓`**。

**关于 380mm「扩散很大」**：散布**没有改**。`+0x24 area_size` 仍是原版 **36.0 m**，
`+0x04=3` / `+0x18=5` / `+0x2C=3000`（投送高度）全部未动 —— 本次只写了 `+0x40/44/48` 三个弹种槽。
观感变大来自**弹头本身的爆炸半径**：

| 量 | 原版（爆炸 301 `OrbitalBarrage`） | 迷你核弹（爆炸 288） | 倍数 |
|---|---:|---:|---:|
| 伤害内径 / 外径 | 4 / 12 m | **17 / 25 m** | ≈2.1× |
| 冲击波（视觉）半径 | 18 m | **45 m** | 2.5× |
| 屏震半径 | 95 | **250** | 2.6× |

⇒ 15 发 × 45 m 冲击波叠在 36 m 落点散布里，看起来"整片区域都在炸"。

**但「散布变大」还有一个真实来源：弹种 101 的弹道参数与 380mm HE 完全不同**（✓ 离线，逐字段 diff）：

| 字段 | 380mm HE 主弹 **82** | 迷你核弹 **101** | 判读 |
|---|---:|---:|---|
| `+0x18` 口径 | 406 | **360** | 口径变小（碰撞体/穿透相关）|
| `+0x20` 初速 | 400 | **300** | 慢 25%，落点时间/曲率不同 |
| `+0x24` 质量 | 30,000 | **70,000** | 更重 |
| **`+0x28` 阻力 drag** | **0** | **0.5** | **有空气阻力**（380mm 是无阻力直线）|
| **`+0x2C` 重力 gravity** | **1** | **10** | **重力×10**，下坠快得多 |
| `+0x30` 仿真步 | 1 | **3** | 子步加密（高速弹防穿透地形）|
| `+0x58` 推进粒子长度 | 0.01 | **0.1** | 尾焰更长 |
| `+0x90` 命中爆炸 | 301 | 288 | 见上表 |
| `+0xAC/0xB0` SurfaceImpactType | 0 / 0 | 0x11 / 4 | **地表撞击效果类型不同**（弹坑/特效）|
| `+0xC4/0xC8` 跳弹散布 V/H | 12 / 45 | **0 / 0** | 核弹不跳弹 |
| `+0xE8` 命中效果伤害类型 | 3 | 2 | — |

⇒ 用户假设成立：**投射物本身的 `drag=0.5` / `gravity=10` / 初速 300 / 质量 70k / 3 子步** 都会改变弹道，
落点相对瞄准点的分布与 380mm 不同 ⇒ 观感上的"扩散"是「**弹道差异 + 爆炸半径 2.5×**」叠加，
不再是单纯 36 m 的散布。

**验证/调味实验（单变量）**：把弹种 101 的射弹行改成"弹道归一到 82"（`+0x20` 400、`+0x24`
30000、`+0x28` 0、`+0x2C` 1、`+0x30` 1，口径先不动），弹种仍是 101、爆炸仍是 288：
若实机"扩散"回到接近原版落点分布 ⇒ 确认是弹道参数贡献；若不变 ⇒ 只剩爆炸半径的观感。
（弹种 101 全表只有本变体用，改这一行全局影响面为零。）

**「弹道归一版」装盘（2026-11-01，✓ 离线装盘已完成，待实机）**：

| 文件 | 改动 | 门禁/哈希 | 产物 |
|---|---|---|---|
| `generated_entities.dl_bin` | 只留 380mm 一行：row9 `+0x40/44/48` = **(101,101,101)**；纳帕姆行**回原版**（5/5、`(238,242,242,0)`），本轮不测毒气 | G1–G9 全 PASS；锚点 `0x8E49771B181FFAA1` 保持 | 明文 md5 `a8644807…`，封包 sha256 `c9d95f1e…` |
| `generated_projectile_settings.dl_bin` | 射弹 **101**（row 158）弹道归一到 82：`+0x20` 300→**400**、`+0x24` 70000→**30000**、`+0x28` 0.5→**0**、`+0x2C` 10→**1**、`+0x30` 3→**1**；口径 360 与爆炸 288 **不动** | `plain_edit` G1–G6 全 PASS；内容哈希 `0x113A5833529A71B5` 保持 | 明文 md5 `6af65513…`，封包 sha256 `6e947fea…` |

- 两文件装盘后**回读明文与产物逐字节一致**；盘面自检 = 仅 entities + projectile 两个文件改动，补丁仍 5 组；
- ⚠ 这是本轮第一次动**射弹表**（此前只动实体表），`dlbin_deploy` 已接管该文件并在覆盖前另存
  `generated_projectile_settings.dl_bin.630dd11206fb8934.replaced`（当前 build 原版）；
- **实机判读**：380mm 叫一发，看落点分布 —— 明显回收到接近原版 36 m 散布 ⇒ 弹道参数贡献确认；
  仍很大 ⇒ 扩散观感主要来自爆炸 288（半径 45 m 冲击波）。

**实机结果（2026-11-01，用户回报）：扩散明显变小 ⇒ 弹道参数是主因，✓✓**

弹种 101 归一到 82 的弹道（初速 400 / 质量 30000 / drag 0 / gravity 1 / 子步 1）后，
落点分布回收到接近原版 380mm 的水平 ⇒ 上一版「扩散很大」**主因是弹种 101 自带的 SEAF 地面炮弹道**
（`drag=0.5`、`gravity=10`、初速 300、质量 70k、3 子步），爆炸 288 的 45 m 冲击波只是次要观感因素。
⇒ 官方 delta（只换 `+0x40` 弹种）**会连带继承整套弹道参数**，这一层在官方内容里没有额外调校。

> **通用教训（跨弹幕混装）**：`+0x40` 换的不只是"弹头外观/伤害"，而是**整套射弹行**（弹道、drag、gravity、
> 撞击类型、跳弹、爆炸…）。把 A 战备的弹种塞进 B 战备时，弹道表现会跟着 A 走 ⇒
> 想要"只换伤害/爆炸、保持原弹道"就必须像本实验一样把射弹行参数归一。

若想要紧凑版：把 `+0x24` 调小（如 20）或换小爆炸行即可，但那就不再是官方 delta 了。

**回滚**（本轮全部撤掉）：

```bash
python /d/mod/tools/dlbin_deploy.py restore --file generated_entities.dl_bin
python /d/mod/tools/dlbin_deploy.py restore --file generated_projectile_settings.dl_bin
rm "/d/SteamLibrary/steamapps/common/Helldivers 2/data/f6fb08cc02d24255.patch_"{0,1,2}{,.gpu_resources,.stream}
```

### 9.9 核弹（弹种 67 / 爆炸 92）是「数值爆炸、无表现」的空壳（✓ 离线）

查 §9.4 第 11 行（核弹加特林）时顺手核实：

| 项 | 值 | 判读 |
|---|---|---|
| 弹种 67 | `ProjectileType_Nuke`：cal **1000**、speed 300、mass **1e6**、命中爆炸 **92** | 弹道/伤害齐全 |
| 弹种 67 的显示资源 | 复用通用炮弹 mesh `0x2F394D3F3119A005` + 通用推进粒子 `0x0534FF3653CC0CEE` | **弹体可见**（不是白模） |
| **爆炸 92** | `ExplosionType_Nuke`（`DamageInfoType_Explosion_Hellbomb`）、半径 **40 / 75 / 125**、屏震 **1000**、`FireTemplate=0`、`StatusEffectTemplate=0` | 数值完整 |
| 爆炸 92 的 **`+0x38` 粒子** | **0（无任何粒子引用）** | **没有视觉** |
| 爆炸 92 的唯一使用者 | 射弹行 344（弹种 67）——全射弹表唯一 | 改动面很小 |

⇒ 把这套弹种塞进任何可用弹幕（如 §9.4 第 11 行「核弹加特林」），实机预期是
**有伤害、有 1000 屏震、有音效，但没有爆炸视觉**。这与之前记录的
**135 CLAN STATION Nuke「投出后什么都不发生」** 是**两个不同层的坑**：
135 是**载荷实体悬空**（`0x3FED8E4A3B242F02` 在实体表 0 引用；补 121 的载荷后仍 `Stratagem Failed`），
而 92 是**爆炸表现层没做**（即便调用链修好，落地也只有无形爆炸）。

> 注意：「粒子=0」本身不等于半成品——本 build 424 条爆炸里有 **78 条**粒子=0（很多是纯伤害的小爆炸）；
> 但核弹这种 **40 m 半径 + 屏震 1000 却没有粒子**，属于明显未完成表现。

**若要让核弹有视觉**（下一步可选）：把爆炸 92 的 `+0x38` 借一个现成粒子并配套驻留，候选：
120mm `OrbitalStrike`（213）的 `0x36B23284931C9124`、380mm `OrbitalBarrage`（301）的 `0x5743ACE6015929E2`；
92 只被射弹 67 引用 ⇒ 全局影响面为零。

### 9.10 `nb > 8` 时弹种清单怎么消费：**A（按发循环）✓✓ 实机确认**（2026-11-01）

**结构硬约束**：`BombardmentComponentData` 行固定 **192 B**，`+0x40` 是 typelib 里声明的
**固定 8 槽 `ProjectileType[8]`（32 B）**——24 行全部同构，**不存在"长度 60 的数组"**（行里也放不下）。
所以加特林 `nb=60` 必然是**复用**这 ≤8 个槽位。两个候选：

| 候选规则 | 60 发（清单 `(74,258,258,258)`）的结果 |
|---|---|
| **A 按发循环清单**（每 4 发一轮回） | 15 发燃烧弹 + 45 发无爆炸弹（整条 4 轮共 60 发燃烧） |
| **B 走完用最后一个非零槽填充** | 只有每轮第 1 发燃烧（整条 4 轮共 **4 发**），其余全是 258 |

**实机判定（2026-11-01，用户回报）**：燃烧加特林实测「**燃烧弹远多于 4 发**」⇒
B（总计只有 4 发燃烧）被排除 ⇒ **A 成立 `✓✓`**（计数级证据；B 的数差 15 倍，肉眼可判）。

补充边界：`nb=7`（120mm 7 发 7 弹种）此前已证「槽序=发序、每轮重复」`✓✓`（§8.10），
与本结论拼起来就是：**清单 ≤8 槽，按发序循环，每轮从头重复**。

**若要精确复核团数**（可选）：把加特林清单改成 `(200,238,238,0,…)`（200=毒气、238=纳帕姆主弹），
`nb=60` / `ns=4` 不动，数每轮绿雾：A ⇒ 约 **20 团/轮**（60÷3）；B ⇒ 只有 **1 团/轮**。

### 9.11 下一轮装盘：380mm 纳帕姆混装（#7）+ walking 12 轮（#12）（✓ 离线装盘，待实机）

上一轮（弹道归一版）已收口回滚：盘面基线自检 **0 文件改动**、补丁回到 2 组（宿主 `9ba626…` 的 patch_0/1）。

⚠ **回滚坑（2026-11-01，已踩过）**：`dlbin_deploy restore --file generated_projectile_settings.dl_bin`
恢复的是**账本里的旧 build 原版**（sha256 `424f8898…`），而本 build 26251122 的 vanilla 是 `630dd112…`
⇒ 恢复后基线会报不一致。正确做法：把覆盖时另存的
`backups/dlbin-deploy/game/generated_projectile_settings.dl_bin.630dd11206fb8934.replaced` 拷回，
再跑 `game_baseline check` 确认 **0 改动**。（实体表没有这个问题：账本原版就是本 build 的 `4121f332…`。）

**本轮两条变体（两条不同弹幕行，可同局测）**：

| 变体 | 行 / 键 | 改动 | 效果 |
|---|---|---|---|
| **#7 380mm 纳帕姆混装** | 380mm row9（`0xEF66B417EDC3B1D6`） | `+0x04` 3→**5**、`+0x18` 5→**7**、`+0x4C` 0→**238** | 5 发/轮 × 7 轮；弹种 `(82,270,270,238)` 按发循环 ⇒ 每 5 发 = 380mm 主弹 → cheap → cheap → **纳帕姆燃烧弹** → 380mm 主弹 |
| **#12 walking 12 轮** | walking row21（`0xCB7F154719F331EC`） | `+0x18` 5→**12** | 3 发/轮 × **12 轮**（行走距离按 §8.11.6 公式线性变长）|

**资源驻留（只为 #7 的 238 提供火焰视觉）**：纳帕姆资产包 `96cedf4706334c5f`（17 条 / 1.3 MB，含
爆炸 63 的粒子 `0xA3F78867A59662C4`）→ 宿主 `f6fb08cc02d24255.patch_0`（`patch_compose scan` 复核
`槽位 [0] 空洞 无`）。

**产物与门禁**：

| 项 | 值 |
|---|---|
| 编辑门禁 | G1/G2/G3（锚点 `0x8E49771B181FFAA1` 保持）/G4（4 处）/G6/G7/G8/G9 全 PASS |
| 明文 md5 | `f7ae0e3bc3bd4ccb676a822bd18e48a6`（回读逐字节一致）|
| 封包 sha256 | `ece0cd7505ebdde3…` |
| 盘面自检 | 仅 entities 1 个文件改动 + 3 组补丁（2 原有 + 本轮纳帕姆驻留）|

**为什么这轮不测 #13**：#13（`+0x04` 6、`+0x60` 1.0）与 #12 打的是**同一条 walking row21**，
同局无法单变量区分 ⇒ 等本轮测完再单独装 #13。

**实机观察清单**（完全退出游戏再启动；一局内依次叫两条）：

1. **380mm HE Barrage**：是否 5 发/轮、共 7 轮；每第 4 发是否为**纳帕姆燃烧弹**（火球/点燃）；
2. **Orbital Walking Barrage**：是否 3 发/轮 × **12 轮**（比原版 5 轮明显更长，行走总距离更长）；
3. 异常项：崩溃、灰块、无伤害、声音/特效错乱。

**实机结果（2026-11-01，用户回报）：两项都 ✓✓**

| 变体 | 实测 | 备注 |
|---|---|---|
| #7 380mm 纳帕姆混装 | **5 发/轮 × 8 轮**，每第 4 发是燃烧弹 ✓ | 轮数 = delta 的 7 + **舰船升级 +1**（与 §9.11 的 +1 轮同源）|
| #12 walking 12 轮 | **3 发/轮 × 13 轮** ✓ | 轮数 = delta 的 12 + **升级 +1** |

⇒ 两条变体三态升 `✓✓`；同时确认「升级 +1 轮」是**在数据值之上叠加**的（7→8、12→13）。

**回滚**（本轮全部撤掉）：

```bash
python /d/mod/tools/dlbin_deploy.py restore --file generated_entities.dl_bin
rm "/d/SteamLibrary/steamapps/common/Helldivers 2/data/f6fb08cc02d24255.patch_0"{,.gpu_resources,.stream}
```

### 9.12 四条非弹幕 modifier 解出来了：哨戒炮血量 / 轨道激光强化 / 爆炸物换爆炸（✓ 离线）

方法：先按 §7.4 的同构映射把实体块 0 的 u16 组件索引全解出来（253/253 个匹配），再按 modifier 的
目标实体反读组件行。新增组件名：

| u16 | 组件 | 说明 |
|---|---|---|
| **227** | `HealthComponentData` | stride 22,096 B（内部含身体部位表）；**`+0x0` = 最大生命**（507 行分布 + 已知单位交叉验证：Marauder 125 / Gazer 900 / GATER 12,000 / 玩家级单位 100）|
| **257** | `ExplosiveComponentData` | stride 360 B |
| **311** | `OrbitalAbilityComponentData` | stride 568 B；全表仅 **3 行**（Orbital Laser 等）|

**#4 `0x24CFC5BA`（72 B 行）：哨戒炮/固定武器血量 → 600**

- 目标 8 件（首发一代哨戒炮套装）：Machine Gun / Gatling / Autocannon / Mortar / Laser / Flame / Tesla /
  一个未知可持炮塔 `0x7368FFD…`（组件含 Turret+Wieldable+WeaponData，**没有 Health 行**）；
  注意**不含**后来加的 Rocket / EMS 迫击炮 / Gas 迫击炮哨戒炮 ⇒ 这批内容属于早期设计；
- delta：`HealthComponentData +0x0` = **600**；现状 6 件是 400、Tesla 本来 600
  ⇒ 若生效 = **哨戒炮血量 400→600（+50%）**，Tesla 不变。

**#3 `0xD295BD78`（200 B 行）：三组子 modifier 的"血量套装"**

结构 = 1 个描述数组 + 3 组 (目标, delta)：

| 子 modifier | 目标 | delta | 写入 |
|---|---|---|---|
| 1 | 未知可持炮塔 / Autocannon / Flame | `0x88A3AF6389DB2176` | `Health +0x0` = **1200** |
| 2 | Laser / Gatling / Tesla | `0x06B4CD02F74344AA` | `Health +0x0` = **20** |
| 3 | Machine Gun | 同上 | `Health +0x0` = **20** |

⇒ 一部分哨戒炮 1200 血、另一部分 20 血。这种"一高一低"的组合不像普通升级，更像**任务/事件/测试用**的
修饰符（⚠ 语义未定；也可能对应某个未发布玩法）。

**#8 `0x8C65F7AC`（72 B 行）：轨道激光的 `OrbitalAbility` 三字段**

- 目标：Orbital Laser 载荷 `0xEC3575E7A93793BB`（`OrbitalAbilityComponentData` row0）；
- 写入：`+0x1CC` f32 **25 → 35**、`+0x1D4` f32 **10 → 20**、`+0x1D8` f32 **50 → 100**；
- 同组件 row1（`0xAC129AA2DB5EABC9`，另一条轨道能力）的值是 (2, 90, 30)，说明该组件是"每条轨道能力一组参数"；
- 语义候选（⚠ 未证）：`+0x1CC` ≈ 持续/时长相关（+40%），`+0x1D4/+0x1D8` 各 **×2**（次数/伤害类）。
  直观读法："轨道激光强化"。

**#9 `0xC0C3FDB3`（72 B 行）：雪球（Snowball）的爆炸从 `Snowball_Stun` 换成 `HighExplosive`**

- 目标 `0xCCFAE6D4A601C741`：**dev 资源路径 `wable/snowball/snowball`**，kind=`interactable`，
  交互类型 `InteractType_PickupSnowball`、冲击类型 `SurfaceImpactType_projectile_snowball`；
  组件 16 个 = Unit / **Interactable** / **Equipment** / **Wieldable** / **WeaponData** / **Throwable** /
  **Sticky** / **Explosive** / LoadoutPackage / Attachable / Trample / Ability / CollisionEvent /
  PhysicsImpactEffect / Tag / WeaponCustomization ⇒ **可拾取、可手持、可投掷、可粘附、会爆的雪球**
  （节庆活动「Festival of Reckoning」里能捡起来互相砸的雪球，线上已发布内容）。
  它没有本地化名/百科词条（`name_status=unknown-no-entry`），所以战备表查不到——**不是战备载荷**；
- delta：`ExplosiveComponentData +0x24`（十进制 36）**73 → 176**。**该字段 = 爆炸类型 id**
  （`generated_explosion_settings` 的 `+0x0` type；HD2Runtime 的链式证据：`ExplosiveComponentData +36
  → explosion_settings recordType`，例：TED-63 是 80→360、TM-1 是 117→201）；
  - **73 = `ExplosionType_Snowball_Stun`**：半径 **1/1/1 m**，伤害行 293 =
    `DamageInfoType_Explosion_Projectile_Snowball` = **0/0 伤害、AP6、stagger 11、状态 38（StunSmall）**，
    shake 1.1 ⇒ 现版本雪球**只晕不伤**；
  - **176 = `ExplosionType_HighExplosive`**：本 build **唯一 owner 是 G-12 高爆手雷**
    （实体 `0x6B11FC757618C57E`，dev `G-12 High Explosive`，同字段 +0x24=176）；半径 **2.5/7/9 m**，
    伤害行 367 = `DamageInfoType_Explosion_HandGrenade_HighExplosive` = **800/800 伤害、AP4、
    拆 30、stagger 30、push 40**，shake 70；
- ⇒ **#9 的语义 =「雪球变高爆手雷」**：雪球砸出去按 G-12 的爆炸结算（会炸死人）。战场用法上属于
  **活动/事件侧 modifier**，不是舰船升级；
- **接线状态**：`0xC0C3FDB3` 在全部 54 张明文表里**只出现 1 次**（它自己这行）；把 15 条 modifier id
  全扫一遍也是同样结果（u32/u64 均无外部引用）⇒ 数据侧没有购买/解锁/战备/事件表引用，属于
  **预置但未接线的变体（未发布）**；雪球本体则是已发布内容；
- 证据：`ExplosionType_Snowball_Stun` / `ExplosionType_HighExplosive` / `InteractType_PickupSnowball`
  可在 `refs/dl-type-names.txt` 逐字检索；owner 关系由 `ExplosiveComponentData` 行反查（本 build
  72 行里 +0x24=73 只有雪球、=176 只有 G-12）⇒ **✓ 离线**；实机验证建议做"反向题"：
  把 G-12 的 `+0x24` 从 176 改成 73，手雷应只剩 1 m 眩晕、0 伤害（一轮即可证字段语义）。

### 9.13 「Napalm + Gatling」两条 modifier 的语义：改的是**散布半径与轮间隔**（✓ 读数，语义 ⚠）

| modifier | 目标 | delta | 写入 | 基线 → 新值 |
|---|---|---|---|---|
| **#0** `0x1DA06C9E` | 纳帕姆(109) **+ 加特林(4)** | `0x98BE8240B2D75239` | `Bombardment +0x24`（area_size） | 纳帕姆 **25 → 100 m**；加特林 **7 → 100 m** |
| #0 | 同上 | 同上 | `+0x1C`（轮间隔 f32） | 纳帕姆 **2.0 → 1.0 s**；加特林 **0.0 → 1.0 s** |
| **#1** `0x818CC7AE` | 纳帕姆(109) + 悬空目标 | `0x5D8DCF5BD8C6B394` | `+0x24` / `+0x1C` | 纳帕姆 **25 → 10 m**、2.0 → **1.0 s** |

- **#0 = 超宽散布档**：两条弹幕同时变成 **100 m 半径**的大范围覆盖、轮间隔压到 **1 s**；
- **#1 = 紧凑散布档**：纳帕姆 **10 m** 半径、轮间隔 1 s；第二目标 `0xB5972922B4ECA89B` 在实体表与战备表
  都不存在（**悬空**，疑似被删的第三条弹幕）；
- 两条都**不改弹种 / 发数 / 轮数**，只改「散布半径 + 轮间隔」⇒ 之前觉得"语义怪"是因为它根本不是弹种变体，
  而是**散布/节奏档位**；
- 可能来源（⚠ 未证）：①未发布的"弹幕散布"升级/模块；②任务或星球事件用的修饰符（把两条件弹幕拉宽/收紧）。
  判定方法：实机装 #0（只写这两行两格）——若纳帕姆与加特林同时变成"超大范围 + 快速轮"，即确认档位语义。

### 9.14 `OrbitalAbilityComponentData` 字段含义（2026-11-01，跨源核对 ✓/⚠）

本地可用的三个来源里，`filediver`（`D:\mod\filediver-dl-type-names.txt`）只给**类型名哈希**、不给成员名；
本地 `recon/shodan-stat-editor` / `repos/shodan-stat-editor` 里 grep `OrbitalAbility` **0 命中**（SHODAN 不暴露该组件）。
真正能定名的是 **HD2Runtime 仓库**：

| 来源 | 内容 |
|---|---|
| `refs/hd2runtime-repo/docs/releases/0.21.0.md` | 「Orbital Laser 的 **duration / movement speed / search radius / 0.1 s tick interval** 是四个独立 owned 的 `OrbitalAbility` 标量」 |
| `refs/hd2runtime-repo/domains/catalog.lua`（由 `schemas/sdk.json` 生成） | `orbital_laser.interval` = `OrbitalAbilityComponentData` **offset 480 = 0x1E0**，f32，expected **0.1** |
| `refs/hd2runtime-repo/docs/live-validation.md` | Orbital Laser 实体 `0xEC3575E7A93793BB` = `OrbitalAbilityComponentData index 308 / record 0`；关联 `DamageSettings type 513 / group 1 / row 504`（standard 60 / durable 60） |
| `refs/hd2runtime-repo/schemas/current.lua` | 该 SDK build 的几何：`OrbitalAbilityComponentData` stride 552、index 308、records 3（与本 build 的 stride 568 / 蓝图索引 311 差一代 ⚠） |

**本 build 实测（Orbital Laser row0）与名称推定**：

| 行内偏移 | 本 build 值 | HD2Runtime 四个标量 | 推定字段名 | 依据 |
|---|---:|---|---|---|
| **`+0x1CC`** | **25.0** | duration | **持续时间（s）** | 25 s 量级合理；modifier #8 改 25→35（+40%）|
| `+0x1D0` | 1.0 | （未列） | ⚠ 未定（可能是 tick 倍率/缩放）| — |
| **`+0x1D4`** | **10.0** | movement speed | **移动/扫射速度（m/s）** | 10 m/s 的量级 |
| **`+0x1D8`** | **50.0** | search radius | **搜索半径（m）** | 50 m 量级，光束寻敌范围 |
| `+0x1DC` | 525（u32） | （未列） | ⚠ 未定 | — |
| **`+0x1E0`** | **0.1** | tick interval | **脉冲间隔（s）** | **offset 480 与 HD2Runtime 完全对上** ⇒ 布局同源 ✓ |

⇒ **modifier #8 的语义**（✓ 数值 / ⚠ 字段名按 HD2Runtime 四标量顺序推定）：
**轨道激光强化——持续 25 → 35 s（+40%）、扫射速度 10 → 20（×2）、搜索半径 50 → 100 m（×2）**，
而 0.1 s 的脉冲间隔（`+0x1E0`）**未动**。

跨 build 提醒：HD2Runtime 那份 schema 是旧一代 SDK build（stride 552 vs 本 build 568、蓝图 index 308 vs 311），
但 **`+0x1E0 = 0.1` 的 offset 精确重合**，说明这段标量布局一致；另外三个按"四标量 + 数值量级"推定，若要铁证需实机测
（持续 35 s / 扫射更快 / 索敌更远任一明显出现即坐实）。

### 9.15 激活通道定证：这些是**行星级 GWE 修饰符**，不是舰船升级（✓✓ 抓包+本地表+字符串三方）

此前只确认"delta 只被本表引用"（未接线签名），不知道谁触发。2026-11-01 把 GWE 抓包
（`D:\mod\out\gwe\*GalacticWarEffects*.json`，310/312 条）与 `refs/strings-en-26088801.json` 对表：

- **`effectType=94`**（目录里共 3 条）的 `values[0]` 就是**本表行首 u32（modifier id）**，3/3 逐字命中；
- 3 条官方卡名/描述都能在本地字符串表解出（`nameHash → strings-en`），且描述与 delta 内容逐条吻合：

| GWE effect | modifier id | 本表行 | 官方名（英文串解出） | 描述要点 | 与 delta 对照 |
|---:|---|---|---|---|---|
| **1345** | `0xCDD51BC6` | #6 | **ORBITAL 120MM HE/EMS BARRAGE** | additional HE rounds, EMS rounds, tighter radius | `+0x40=(76,197,139,139,197,139,139)`、`+0x04=7`、`+0x18=5`、`+0x24=10`（散布收紧）✓ |
| **1346** | `0x4DD68526` | #2 | **INCENDIARY GATLING BARRAGE** | incendiary rounds instead of HE | `+0x40=(74,258,258,258)`、60 发/轮（74=燃烧）✓ |
| **1350** | `0x2A83FD6B` | #14 | **SMOKE-ENHANCED WALKING BARRAGE** | smoke rounds mixed into salvos | `+0x40=(251,197,139,139)` + 换包 ✓ |

- 机制 = 与 type71（presence）同一条路：`Status.planetActiveEffects[] += {"index": 星球, "galacticEffectId": 1345}`；
  服务器只给"哪颗星球开哪个变体"，引擎按 id 到本地本表查行 → 套用 `delta AddPath`。
  **激活源不在本地表**，所以"本地 54 表里 0 引用"是正常的、不是否证。
- 三条**当前都不在线**：68 份 `801_Status` 抓包（最新 2026-11-01 17:25）均无 1345/1346/1350。
- 其余 12 个 modifier id 在 310/312 条目录的 `values` 里 **0 命中** ⇒ 服务器尚未提供（未发布/未排期），
  目前只能像我们这样离线改数据表来跑（`strings` 里 "experimentally modified" 也**只有这 3 条**，
  全 build 24,834 条英文串里没有第 4 条 ⇒ 其余 12 条连文案都没写）。
- 区分（常见混淆）：社区清单的 `[effect 1426/1427/1428]` 是 **type32 临时配发战备**（`values[0]` = 战备 hash
  `0x8DFA4622 / 0x166D0C91 / 0x0C064A00`，本 build 表里 0 命中 ⇒ 新战备未发布），卡名 `WEAPONS EXPERIMENTATION`、
  描述模板 `The #V_ONE stratagem is available to all Helldivers.` —— 和 type94 的"改现有战备行为"是两条线。
- 旁证：`refs/strings-en-26088801.json` 里 `763846539 = "Make Snowball"` 正好命中 §9.12 #9 雪球实体的
  `InteractableComponentData +0x3C`（交互提示文案）⇒ 雪球身份再确认。
- 待实机（⚠）：走代理把 `{"index": 目标星球, "galacticEffectId": 1346}` 塞进 Status → 进图打
  Orbital Gatling Barrage 应变成燃烧弹（同一 delta 离线改表已 ✓✓，2026-11-01）。
