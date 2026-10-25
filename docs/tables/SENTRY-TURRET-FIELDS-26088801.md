# 哨戒炮 / 炮塔类战备的字段图（build `26088801`）

> **一句话**：哨戒炮"部署后自动消失"的寿命 = **`HellpodPayloadComponentData +0x04`（f32，秒）**。
> `A/MG-43 Machine Gun Sentry` = **150 s**；把这一个 f32 改成 600，它就能站 10 分钟。
>
> 三源交叉：①本仓库数据（17 个哨戒/阵地全表）②**SHODAN Stat Editor v4.1.0 Offline** 的
> `unit_lifetime` = `'Time deployed (s)'`，写的正是 `HellpodPayloadComponentData` 行 `+4`
> （`stat_editor.lua` L15460–15465）③wiki 页面 `Lifetime = 150 s`，模块数据里
> `remove_time = 2.5` 对应同一个组件的 `+0x00`。
>
> 状态：字段定位 **✓ 离线（三源）**；改值实机 **⚠ 待验**（已装 `150 → 600` 的构建，见 §4.2）。

---

## 0 三态

| 结论 | 态 | 证据 |
|---|---|---|
| 寿命 = `HellpodPayloadComponentData +0x04`（f32） | **✓ 离线（三源一致）** | 本 build 数据 MG-43 = 150.0；SHODAN 源码写 `pat + 4`、标签 `Time deployed (s)`；wiki 页面 150 s |
| `HellpodPayload +0x00` = wiki 的 `remove_time` | **✓ 离线（值全表对上）** | 哨戒 2.5 / 机枪哨戒 2.5 / 加特林 3.5 / 地雷 3.5 —— 与 wiki 模块 `remove_time` 逐一相同 |
| 寿命只对"会自己撤走"的东西非 0 | **✓ 离线** | 哨戒 150–180、特斯拉塔 150、护盾中继站 40；**HMG/反坦克阵地 = 0（人不走它就不走）**；地雷 = 0 |
| 改这一格能在游戏里延长 | **⚠ 待验** | 已装 `0a9d2542e9a6531a`（MG-43 = 600 s） |
| `+0x08`（1267/1270/1268/2424/2529/2537）是什么 | **⚠ 未解** | 看着像"载荷/投放模板"枚举，同值的东西行为一致（1267=人操阵地、1270=地雷/加特林、2537=多数哨戒） |

---

## 1 数据落在哪：战备行 → 两个实体

以 `SENTRYS. MACHINEGUN`（战备 id 124、行 129、基址 `0x11168`）为例，`StratagemInfo` 行里的
**`+0x98` = 载荷实体数组的 payload 相对偏移，`+0xA0` = 个数**（本例 2）：

| 数组项 | 实体键 | 是什么 |
|---|---|---|
| 1 | `0x37CDE43876BA26BB` | **哨戒炮本体**（28 个组件：`Turret` / `ProjectileWeapon` / `WeaponMagazine` / `Health` / `HellpodPayload` …）|
| 2 | `0x73F8498BFFDCF415` | 送它下来的 **hellpod**（`HellpodComponentData` + `StaticPosition`）|

**寿命字段在 1 号（本体）上**，`HellpodPayloadComponentData` 行的 `+0x04`。

> 同一行还有 `+0x150` 数组（本例 2 项）：那是**字符串表**（`0x2E535952544E4553` = ASCII `SENTRYS.`），不是实体。

---

## 2 全表：17 个哨戒 / 阵地

`cooldown` = 行 `+0x68`（f32）、`calltime` = 行 `+0x54`（f32）、`箭头数` = 行 `+0x48`（u32）、
`payload` = `HellpodPayloadComponentData` 行（12 B）。

| 战备行 | 本体实体 | cooldown | calltime | 箭头 | `+0x00` remove | **`+0x04` 寿命** | `+0x08` |
|---|---|---:|---:|---:|---:|---:|---:|
| `SENTRYS. MACHINEGUN`（A/MG-43）| `0x37CDE43876BA26BB` | 90 | 3.0 | 5 | 2.5 | **150.0** | 2537 |
| `SENTRYS. GATLING`（A/G-16）| `0xEF85D6CF58E31D70` | 150 | 3.0 | 4 | 3.5 | **150.0** | 1270 |
| `SENTRYS. MORTAR`（A/M-12）| `0x51A0812E3BCE2D74` | 180 | 3.0 | 5 | 2.5 | **180.0** | 2537 |
| `SENTRYS. MORTAR STATICFIELD`（EMS）| `0xB2053A1838092F8B` | 180 | 3.0 | 5 | 2.5 | **180.0** | 2537 |
| `SENTRYS. MORTAR GAS` | `0x299C0D3DFD2F0994` | 180 | 3.0 | 5 | 2.5 | **180.0** | 2537 |
| `SENTRYS. ROCKET`（A/MLS-4X）| `0x37079568DC86E9C6` | 150 | 0.0 | 5 | 2.5 | **150.0** | 2537 |
| `SENTRYS. AUTOCANNON`（A/AC-8）| `0x54D86057F5DACFB9` | 150 | 3.0 | 6 | 2.5 | **150.0** | 1268 |
| `SENTRYS. FLAMETHROWER` | `0x820CC3BAFE962858` | 100 | 3.0 | 6 | 2.5 | **150.0** | 2537 |
| `SENTRIES. LASER CANNON SENTRY`（A/LAS-98）| `0x56070F36CFFFA8A8` | 150 | 3.0 | 6 | 2.5 | **180.0** | 2537 |
| `EMPLACEMENTS. TESLA TOWER` | `0x74599E56F72F9D7E` | 120 | 3.0 | 6 | 2.5 | **150.0** | 2529 |
| `EMPLACEMENTS. SHIELD GENERATOR RELAY` | `0xED13DDC480EC6910` | 90 | 0.0 | 6 | 2.5 | **40.0** | 2424 |
| `EMPLACEMENTS. HEAVY MACHINEGUN EMPLACEMENT` | `0x0E977C49DB7604F9` | 180 | 3.0 | 6 | 2.5 | **0.0** | 1267 |
| `EMPLACEMENTS. ANTI TANK EMPLACEMENT` | `0x2B11C9E4980EC479` | 180 | 3.0 | 6 | 2.5 | **0.0** | 1267 |
| `EMPLACEMENTS. DEFENSE WALL GRENADE LAUNCHER` | `0x0C8257D1C0255593` | 120 | 3.0 | 5 | 2.5 | **0.0** | 1267 |
| `EMPLACEMENTS. ANTI-PERSONNEL MINE DEPLOYER` | `0xF00C349422E8E320` | 120 | 3.0 | 4 | 3.5 | **0.0** | 1270 |
| `EMPLACEMENTS. INCENDIARY MINE DEPLOYER` | `0xBF32E12923A9A252` | 120 | 3.0 | 4 | 3.5 | **0.0** | 1270 |
| `EMPLACEMENTS. ANTI-TANK MINE DEPLOYER` | `0x25A2FD037B6ED25C` | 120 | 3.0 | 4 | 3.5 | **0.0** | 1270 |
| `EMPLACEMENTS. GAS MINE DEPLOYER` | `0xA9982969137F3D77` | 120 | 3.0 | 4 | 3.5 | **0.0** | 1270 |

读法：**`+0x04 > 0` 的才会自动消失**（人操阵地 / 地雷 = 0 ⇒ 只要不被摧毁、不被捡走就一直在）；
`+0x00`（2.5 / 3.5 s）与 wiki 模块的 `remove_time` 逐个相同，是"撤离/拆解时长"那一档，
**不要**把它当寿命。

### 2.1 wiki 模块数据 vs 本 build（有一处代差）

wiki `stratagemdata.json` 的 `calltime` / `cooldown` / `stratcode` 与我们**逐项对上**
（MG-43：3 s / 90 s / 5 箭头；加特林 150 s / 4 箭头；火箭 0 s；自动炮 150 s / 6 箭头）。
但 **Laser Sentry 对不上**：wiki 写 `cooldown 128 / calltime 4.75`，本 build 是 **150 / 3.0** ——
wiki 模块来自旧 build（顺带：wiki 里 sentry `health` 一律写 200，本 build 数据是 400，见 §3.7）。
**验数一律以本 build 数据为准，wiki 只当"字段名/量纲"的参照。**

---

## 3 其它炮塔字段（按组件）

### 3.1 `StratagemInfo`（战备行，400 B）

| 偏移 | 类型 | 含义 | 交叉证据 |
|---|---|---|---|
| `+0x00` | u32 | 战备 id（本 build 是 1..153 的排列） | 普查 |
| `+0x40` / `+0x48` | u64 指针 / u32 | **呼叫码箭头数组**（payload 相对） / **箭头个数** | SHODAN `MOD.code`（`+64` 数组、`+72` 个数）；MG-43 = 5 箭头 = wiki `stratcode` 5 项 ✓ |
| `+0x50` | u32 | **每局可用次数**（`0xFFFFFFFF` = ∞） | SHODAN `Uses per mission`（`+80`）|
| `+0x54` | f32 | **投放前倒计时**（秒；信标 → 投放派发） | SHODAN `Countdown before delivery`（`+84`）；wiki `calltime` ✓ |
| `+0x60` / `+0x64` | f32 | `extra_travel_time` / 载具专用（SHODAN 注释：实测两者都**不改变**任何时间）| SHODAN `MOD.callin_rows` 注释 |
| `+0x68` | f32 | **冷却（秒）** | SHODAN `Cooldown`（`+104`）；wiki `cooldown` ✓ |
| `+0x98` / `+0xA0` | u64 / u32 | **载荷实体数组**（payload 相对偏移 / 个数） | 本文 §1（2 项：本体 + hellpod）|
| `+0xC8` | u32 | **额外战备**（带上本发时附赠的另一条 id；0 = 无） | SHODAN `extra`（`+200`）；本仓库已实机 ✓✓ |

### 3.2 `HellpodPayloadComponentData`（12 B，`0xDDB5C03F`）

| 偏移 | 类型 | 含义 | 交叉证据 |
|---|---|---|---|
| `+0x00` | f32 | **remove_time**（撤离/拆解时长，2.5 / 3.5 s） | 与 wiki 模块 `remove_time` 全表一致 |
| **`+0x04`** | **f32** | **部署后寿命（秒）** | SHODAN `Time deployed (s)`；wiki 页面 150 s；§2 全表 |
| `+0x08` | u32 | ⚠ 未解（1267/1268/1270/2424/2529/2537） | 同值组行为一致 ⇒ 像"投放模板/类别" |

### 3.3 `TurretComponentData`（76 B，`0x1EBA7593`）

| 偏移 | 类型 | 含义 | MG-43 实测 | 交叉证据 |
|---|---|---|---|---|
| `+0x08` | f32 | **俯仰转速**（vertical turn speed） | 50 | wiki `turn_speed_vertical: 50` ✓ |
| `+0x0C` | f32 | **水平转速**（horizontal turn speed） | 80 | wiki `turn_speed_horizontal: 80` ✓ |
| `+0x10` | f32 | 未知（本例 1.0） | 1.0 | — |
| `+0x14` / `+0x18` | f32 | **俯仰下限 / 上限（度）** | −60 / +90 | wiki `vertical_limit_min/max: -60/90` ✓ |
| `+0x1C` / `+0x20` | f32 | **水平下限 / 上限（度）** | −180 / +180 | 与"哨戒炮可转满圈"一致 ✓ |
| `+0x24` / `+0x28` | f32 | 未知（0.1 / 0.1，可能是瞄准阻尼/插值） | — | ⚠ |
| `+0x2C` / `+0x30`、`+0x44` / `+0x48` | u32 | 非浮点（看着是哈希/枚举） | — | ⚠ |

### 3.4 `WeaponMagazineComponentData`（160 B，`0xFB8D88A3`）

| 偏移 | 含义 | MG-43 | 交叉证据 |
|---|---|---:|---|
| `+0x04` | 未知（4 个 150 连着出现） | 150 | ⚠ |
| `+0x14` | 未知 | 246 | ⚠ |
| `+0x88` | **弹匣容量** | **175** | wiki `magazine_capacity: 175` ✓ |
| `+0x8C` | 初始备弹（本行 0） | 0 | 与 `[WEAPON-AMMO-RESERVE](WEAPON-AMMO-RESERVE-26088801.md)` §8 一致 |
| `+0x90` | **备弹补给量** | **6** | wiki `magazines_refill: 6` ✓ |
| `+0x9C` | **膛内**（chambered） | 1 | wiki `chambered: 1` ✓ |

### 3.5 `ProjectileWeaponComponentData`（616 B，`0x45171B68`）

| 偏移 | 含义 | MG-43 | 交叉证据 |
|---|---|---:|---|
| `+0x00` | **弹丸类型 id** | 150 | wiki `projectile_type: Rifle_8x60mm_fmj`（wiki 给名字，不给 id）|
| `+0x04` / `+0x08` / `+0x0C` | **射速三档（rpm）** | 630 / 630 / 900 | wiki `rounds_per_minute {x:630,y:630,z:900}` **逐值对上** ✓✓ |
| `+0x10` | **射程 / distance** | 75 | wiki `distance: 75` ✓ |

> 这条同时给 `[WEAPON-FIRE-MODES](WEAPON-FIRE-MODES-26088801.md)` 里"`+4/+8/+12` = rpm 三档"
> 补上了一个 wiki 逐值验证的样本。

### 3.6 `WeaponDataComponentData`（1240 B，`0x88E4DBB1`）

| 偏移 | 含义 | MG-43 | 交叉证据 |
|---|---|---:|---|
| `+0x54` / `+0x58` | **散布 horizontal / vertical** | 10 / 10 | wiki `spread_info {10,10}` ✓ |
| `+0x164` | **人机工效 ergonomics** | 65 | wiki `ergonomics: 65` ✓ |
| `+0x174` | 很可能 = `aim_flinch_max` | 5.0 | wiki `aim_flinch_max: 5`（同名同量纲，⚠ 未做差分）|

### 3.7 `HealthComponentData`（22096 B，`0xB3915DE3`）

| 偏移 | 含义 | MG-43 | 交叉证据 |
|---|---|---:|---|
| `+0x000` | 生命值（u32） | **400** | SHODAN 把人操/哨戒的 hp 读在 Health 行"body"处；**但 wiki 写 200** ⚠ 待验（可能 wiki 旧 build，或 400 是含护甲的另一池）|
| `+0x118`（= 280） | **护甲（u32）** | **2** | wiki `armor: 2` ✓；SHODAN 对 EXO 手臂也用 `+280` 读护甲 |
| `+0x2F0`（= 752） | 分区生命（`+520+232`） | 400 | SHODAN EXO 分区血同偏移 |

---

## 4 怎么改

### 4.1 一条命令（保内容哈希）

```bash
# 寿命：把 A/MG-43 哨戒炮从 150 s 改成 600 s
python tools/entity_field_set.py set \
    --block 0xDDB5C03F --key 0x37CDE43876BA26BB \
    --field 4 --type f32 --value 600 --expect-old 150 \
    --out entities.life600.plain
python tools/dlbin_seal.py seal-key --key <recipient.pk> --out X.sealed.dl_bin entities.life600.plain
python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed X.sealed.dl_bin
```

门禁：G1 长度 / G2 差异 ⊆ 字段 ∪ 尺寸 ∪ 校正字 / G3 Murmur 锚点 `0x8E49771B181FFAA1` /
G4 读回 / G7 旧值 / G8 校正字对齐 —— 本轮全部 PASS（diff = 2 B）。

### 4.2 本轮已装（⚠ 待实机）

| 文件 | 大小 | sha256 |
|---|---:|---|
| `D:\mod\out\sentry-life\generated_entities.life600.sealed.dl_bin` | 47,259,736 | **`0a9d2542e9a6531a`** |

改动：**MG-43 哨戒炮 `HellpodPayload +0x04`：150 → 600**（其余一字未动；基址是上一轮投送舱 rig 的实体文件，
火箭炮塔 / rack 29 那套都还在）。

判读：叫一台 MG-43 哨戒炮，**别让它被打爆、也别把弹打空** —— 如果 150 s 后它没消失、而是撑到约 10 分钟，
字段成立；如果照旧 150 s 消失，说明寿命还有第二处（下一步怀疑 `TurretComponentData` 或该实体的行为脚本）。

---

## 5 还没解 / 别踩

| 项 | 说明 |
|---|---|
| `HellpodPayload +0x08` | 1267/1268/1270/2424/2529/2537 —— 像"投放模板"枚举，同值组行为一致，但**没有差分证据** |
| `Health +0x000` = 400 vs wiki 200 | 两个来源打架；⚠ 要区分"含护甲的最大值"与"可显示 HP" |
| `Turret +0x2C/+0x30/+0x44/+0x48` | 看着是哈希/枚举（非浮点），未命名 |
| wiki 模块代差 | Laser Sentry 的 cooldown/calltime 与本 build 不同；**别照抄 wiki 数值当本 build 真值** |
| 寿命是不是"从落地起算" | 本字段只证明"值 150 = 页面寿命"，**起点**（投放/落地/首次开火）未验 ⚠ |
