# EXO 机甲臂件变体：社区编号「MK2 / MK3」到底是什么（build `26088801`）

> **问题**：memmod 时代提到「EXO-49 的加农炮有一个 MK2 变体，是未发布内容」——它是什么、和原版差在哪？
> **结论**：加农炮这一支**没有**「MK2」这个名字；社区编号里的第三个变体叫 **MK3 = `0x3E3A31261A124454`（右臂、200 发）**，
> 它在数据上只改**两个字段**（弹匣 100→200、默认射速档 175→300 rpm）。
> 而引擎类型名里真正带 `_MK2` 的是**导弹**（`ProjectileType_Missile_Combat_Walker_MK2`），对应爱国者导弹巢的孪生体 `0x821D035AA47E3E75`。
>
> **状态**：全部 **✓ 离线**（逐组件逐字段比对）；两者都**没有被任何挂载记录引用** ⇒ 当前 build 里属于未使用/未发布件（⚠ 是否有 AI/BOSS 生成表引用未逐一排除）。

---

## 1 来源：第三方 `ExoLoadout v0.8.1`

| 项 | 值 |
|---|---|
| 文件 | `D:\Downloads\ExoLoadout-v0.8.1.zip`（19,125 B，sha256 `556ce922e3a603ba…`） |
| 形态 | Bingus Shared Loader 的 **纯 Lua addon**：`Addon/9ba626afa44a3aa3.patch_0`（59,072 B） |
| 载荷 | 单个 lua 资源 `0x9ECD04291C6E37CE`（58,877 B），`python -m srkit extract --id … --decoded` 取出 `script.lua`（1,440 行） |
| 干什么 | 运行时改 `MountComponentData` 的手臂槽（`SLOT_NO = {L=0, R=1}`），让玩家在**携带的两台机甲之间**互换同侧臂件 |

它自带的臂件字典（`script.lua` 第 209–227 行）：

```lua
local EXTRA_ARMS = {
  emancipator = { R = { '3E3A31261A124454' } },   -- MK3(右) 200发
}
local ARM_NAME = {
  ['824B7E0C4C879EB5'] = '火箭发射器',
  ['08F6089289C83D22'] = '加特林',
  ['E5F64DCC3BFE9DD1'] = '机炮（左）',
  ['FF9878576A4C543B'] = '机炮（右）100发',
  ['3E3A31261A124454'] = '机炮（右）200发',
  ['65489809A8181B96'] = '护盾',
  ['DF51FE8D62F294BE'] = '霰弹枪',
  ['0736BEE2D6328726'] = '喷火器',
  ['17C5D12D8D5DEE2C'] = '反坦克炮',
}
```

同一段上方的注释写明社区编号口径：**「手臂 / MK2 / MK3 依次为 右 / 左 / 右」** ——
也就是说 `MK2` = 原版**左臂**机炮（`E5F64DCC3BFE9DD1`），`MK3` = 补进来的**右臂 200 发**件。

---

## 2 三个件的数据（**✓ 离线**，`generated_entities.dl_bin`）

| | 右臂（原版） | 左臂（= 社区 MK2） | 右臂 200 发（= 社区 MK3） |
|---|---|---|---|
| 实体键 | `0xFF9878576A4C543B` | `0xE5F64DCC3BFE9DD1` | **`0x3E3A31261A124454`** |
| 资源名 | `walker_autocannon_right` | `_walker_autocannon_left` | `walker_autocannon_right` |
| 组件数 | 12 | 12 | 12（同一套） |
| **`WeaponMagazine +0x88` 弹匣** | **100** | 100 | **200** |
| **`ProjectileWeapon +0x08` 默认射速** | **175 rpm** | 175 rpm | **300 rpm** |
| `ProjectileWeapon +0`（弹丸 id） | 265 = `30mm APHE Cannon` | 265 | 265（**同一个弹丸**） |
| 模型 | Unit `+0 = FF9878576A4C543B` | Unit `+0 = E5F64DCC3BFE9DD1` | **Unit `+0 = FF9878576A4C543B`**（复用右臂 unit） |

**200 发件 vs 原版右臂的完整差异 = 2 个字段**（12 个组件逐 4 字节比完）：

| 组件 | 偏移 | 原版 → 变体 | 语义 |
|---|---:|---|---|
| `WeaponMagazineComponentData` | `+0x88` | 100 → **200** | 每匣弹数（[WEAPON-AMMO-RESERVE §8](WEAPON-AMMO-RESERVE-26088801.md) 已定名 `capacity`） |
| `ProjectileWeaponComponentData` | `+0x08` | 175.0 → **300.0** | `rounds_per_minute` 的**默认档**（[WEAPON-FIRE-MODES §1.2](WEAPON-FIRE-MODES-26088801.md)：`+4/+8/+12` 三档，`+8` 为默认） |

其余（`WeaponData` 伤害/散布/后坐、`Magazine` 其它字段、`Animation`/`Attach`/`Behavior`/`Gore`/`Health`/`Visibility`/`Wieldable`/`Ability`）**逐字节相同**。
⇒ **同一个模型、同一门炮，只改「弹匣容量」和「射速」** —— 社区说的「不是换皮，是有实战意义的选择」在数据上成立，且**射速也被改了**（mod 文档没提这一点）。

**左臂（MK2）vs 右臂（原版）**：除 `Behavior +0`（自己的键）与 `Unit +0/+4`（自己的 unit 资源）外**逐字节相同** ⇒ 左/mk2 只是"同一门炮的另一侧"，没有任何数值差异。

---

## 3 未使用性（引用普查）

| 检查 | 结果 |
|---|---|
| `MountComponentData` 全表 328 槽 × 134 条记录里出现 `0x3E3A31261A124454`？ | **0 次**（无任何载具/机甲挂它） |
| 其它 55 张明文设置表里出现该键？ | **0 次**（只有实体库内部各组件表把它当作自己的键） |
| 结论 | 它是**在实体库里、但没人挂**的件 ⇒ 未发布/未使用（⚠ AI/关卡生成表若在 bundle 里，本普查覆盖不到） |

---

## 4 附：真正叫「MK2」的是**导弹**，不是机炮

引擎类型名里 `_MK2` 只出现在**导弹**家族（`dl-type-names.json`）：

| 类型名 | id |
|---|---|
| `ProjectileType_Missile_Combat_Walker` / **`_MK2`** | `0x3A750C02` / **`0xC2D1A0EB`** |
| `ExplosionType_Combat_Walker_Missile` / **`_MK2`** | `0x874F5C12` / **`0x957578FB`** |
| `DamageInfoType_Projectile_Missile_Combat_Walker` / **`_MK2`** | `0x5C35644C` / **`0x02390E35`** |
| `DamageInfoType_Explosion_Projectile_Missile_CombatWalker` / **`_MK2`** | `0xEB34A4ED` / **`0x8A39B756`** |

数据里对应的就是爱国者导弹巢的**孪生实体** `0x821D035AA47E3E75`（Unit `+0` 指向原版 `0x824B7E0C4C879EB5` ⇒ 同模型，同样没有挂载记录引用）：

| 项 | 原版导弹 `0x824B7E0C4C879EB5` | MK2 孪生 `0x821D035AA47E3E75` |
|---|---|---|
| `ProjectileWeapon +0x00` 弹丸 | **130**（SHODAN 名表：`70mm Laser-Guided Missile`） | **354**（`70mm Laser-Guided Missile Mk2`） |
| 弹丸行 `+60` 伤害行 | 249 → **damage 1250**、durable 1250、AP (6,6,5,0)、demo 30、stagger 40、push 25 | 250 → **damage 600**、durable 600、AP (5,5,3,0)、demo **40**、stagger **50**、push 25 |
| 弹丸行 `+144` 命中爆炸 | 418 | 303 |
| 爆炸行 `+4` 伤害行 | 406 → damage 400、AP (3,0,0,0) | 407 → damage 400、AP (**5**,0,0,0) |
| `ProjectileWeapon +0x28/+0x2C` | 两个 effect 哈希 | 变了 |
| `ProjectileWeapon +0x30` | f32 **10.0** | **0.0** |
| `ProjectileWeapon +0x08`（rpm 默认档） | 同值 | 同值（导弹这一支没改射速） |

其余组件（`WeaponData`/`Magazine`/`Unit`/…）**逐字节相同**。
⇒ MK2 导弹的改法是：**直击伤害砍半（1250→600）、直击穿甲降一档（6→5），但爆炸穿甲升两档（3→5）、拆解/硬直提高（30→40 / 40→50）**
—— 更像「早期平衡稿」，不是纯强化。

---

## 5 想实测怎么办

两个变体都不需要额外资源包（Unit 指向原版 unit，包就是本机甲/本臂那一包），所以**一条挂载槽写入**即可：

```bash
# 200 发机炮 → EXO-49 右臂（行 108 槽 1）
python tools/mount_table.py swap --entity 0xC2D449ECF7FACAB1 --slot 1 \
    --item 0x3E3A31261A124454 --out out/exo49-ac200/plain --dry-run   # 先看判据与射界
# MK2 导弹 → 爱国者左臂（行 17 槽 0）
python tools/mount_table.py swap --entity 0x79E4B3D2DA5E45E3 --slot 0 \
    --item 0x821D035AA47E3E75 --out out/exo45-mk2-missile/plain --dry-run
```

---

## 6 三态

| 主张 | 态 |
|---|---|
| 社区 `EXTRA_ARMS` 里的 `0x3E3A31261A124454` 在本 build 实体库中存在，12 组件与原版右臂同构 | **✓ 离线** |
| 它与原版右臂只差 `Magazine +0x88`（100→200）与 `ProjectileWeapon +0x08`（175→300 rpm） | **✓ 离线** |
| 它复用原版右臂的 unit 资源（同模型） | **✓ 离线**（`UnitComponentData +0` 相同） |
| 左臂与右臂机炮除自身键/unit 外完全相同 | **✓ 离线** |
| 爱国者导弹 MK2 孪生体的差异（伤害/AP/爆炸 如上表） | **✓ 离线** |
| 两者都未被挂载记录引用 ⇒ 未发布/未使用 | **✓ 离线**（挂载表 0 命中；⚠ AI/关卡生成表未覆盖） |
| 装进游戏后表现（弹匣 200、射速更快、MK2 导弹手感） | **⚠ 未证** |

---

## 7 溯源

- 第三方 mod：`D:\mod\recon\exoloadout-26088801\`（`Addon/9ba626afa44a3aa3.patch_0` + 解包出的 `script.lua`）
- 表几何与字段语义：[WEAPON-AMMO-RESERVE §8](WEAPON-AMMO-RESERVE-26088801.md)（`Magazine +0x88`）· [WEAPON-FIRE-MODES §1.2](WEAPON-FIRE-MODES-26088801.md)（`ProjectileWeapon +4/+8/+12` = rpm）· [EXPLOSION-PROJECTILE §2](../explosions/EXPLOSION-PROJECTILE-25988413.md)（弹丸行 `+60`/`+144`）· [DAMAGE-SETTINGS §2](DAMAGE-SETTINGS-26088801.md)（伤害行 76 B 字段图）
- 弹丸记录名表：本地第三方 `SHODAN Stat Editor v4.1.0`（`MOD.round_names`，按记录 id 给名）

---

## 8 实机装配（2026-10-25，**⚠ 待验**）：爱国者双外来臂 = MK2 导弹 + 200 发机炮

### 8.1 盘上内容

| 文件 | 大小 | sha256 | 改动 |
|---|---:|---|---|
| `D:\mod\out\exo45-arms-v2\generated_entities.exo45-mk2-ac200.dl_bin` | 47,259,592 | `7e75675de840f83f` | EXO-45 行 17：**slot0（左臂）→ `0x821D035AA47E3E75`**（导弹 MK2 孪生）、**slot1（右臂）→ `0x3E3A31261A124454`**（机炮 200 发） |
| `D:\mod\out\exo45-arms-v2\generated_stratagem_settings.exo49pkg.sealed.dl_bin` | 82,440 | `2dc6179e8a3f71ef` | 只改 1 处：爱国者 **live 行 143 `+0xA8` = `0xE72D3E9B05C3DB0B`**（解放者/EXO-49 包）；`SOS Beacon` 行归零（不再借行） |

门禁：换件两次 G1–G10 全过（`changed=[(17,0,…)]`、`changed=[(17,1,…)]`）；`plain_edit` G1–G6 全过（diff 9 B）；
封箱后 `open-key` 回读逐字节一致；两个文件 Murmur64A 各自保持原值。

### 8.2 为什么只需要声明 **一个** 包

| 件 | `UnitComponentData +0`（模型来源） | 包 | 是否需额外驻留 |
|---|---|---|---|
| 200 发机炮 `0x3E3A31261A124454` | `0xFF9878576A4C543B`（EXO-49 右臂原版） | `e72d3e9b05c3db0b` | **要** → 用爱国者 live 行声明 |
| 导弹 MK2 孪生 `0x821D035AA47E3E75` | `0x824B7E0C4C879EB5`（爱国者自己的导弹巢） | `22749a294788af66` | **不要**（本体自带） |

⇒ 对比上一轮（盾 + 伐木者炮）需要两个外来包、要借 `SOS Beacon` 一行；这一轮两个件里只有一个外来包，**完全自足**（只动爱国者自己那一行）。

### 8.3 进游戏看什么

| 观察点 | 期望 |
|---|---|
| 左臂模型 | 与**原版导弹巢完全一样**（同一 unit 资源） |
| 左臂手感 | 直击**变弱**（1250→600，AP 6→5），但**爆炸穿甲更强**（3→5）、拆解/硬直更高（30→40 / 40→50） |
| 右臂模型 | 与 EXO-49 右臂机炮一样（同一 unit 资源），**紫问号** = EXO-49 包没驻留 |
| 右臂 HUD 弹数 | **200**（原版 100；该件 `chambered = 0`，所以不减一） |
| 右臂射速 | 300 rpm（原版 175） |
| 本体 | 正常（`+0xA8` 是纯增量声明，见 [EXO45-ARM-SWAP §8.3](../cases/EXO45-ARM-SWAP-26088801.md)） |

回滚：`python tools/dlbin_deploy.py restore --file generated_entities.dl_bin` 与
`python tools/dlbin_deploy.py restore --file generated_stratagem_settings.dl_bin`；
回上一版（盾 + 伐木者炮）：`install --sealed D:\mod\out\exo45-arms\generated_entities.exo45-arms.dl_bin` +
`install --sealed D:\mod\out\exo45-arms\generated_stratagem_settings.minimal-borrow.sealed.dl_bin`。
