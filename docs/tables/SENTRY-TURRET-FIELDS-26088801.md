# 哨戒炮 / 炮塔类战备的字段图（build `26088801`）

> **一句话**：哨戒炮"部署后自动消失"的寿命 = **`HellpodPayloadComponentData +0x04`（f32，秒）**。
> `A/MG-43 Machine Gun Sentry` = **150 s**；把这一个 f32 改成 600，它就能站 10 分钟。
>
> 三源交叉：①本仓库数据（17 个哨戒/阵地全表）②**SHODAN Stat Editor v4.1.0 Offline** 的
> `unit_lifetime` = `'Time deployed (s)'`，写的正是 `HellpodPayloadComponentData` 行 `+4`
> （`stat_editor.lua` L15460–15465）③wiki 页面 `Lifetime = 150 s`，模块数据里
> `remove_time = 2.5` 对应同一个组件的 `+0x00`。
>
> 状态：字段定位 **✓ 离线（三源）**；改值 **✓ 实机**（`150 → 30`，用户实测「约 30 s 自己消失」，见 §4.2）。

---

## 0 三态

| 结论 | 态 | 证据 |
|---|---|---|
| 寿命 = `HellpodPayloadComponentData +0x04`（f32） | **✓ 离线（三源一致）** | 本 build 数据 MG-43 = 150.0；SHODAN 源码写 `pat + 4`、标签 `Time deployed (s)`；wiki 页面 150 s |
| `HellpodPayload +0x00` = wiki 的 `remove_time` | **✓ 离线（值全表对上）** | 哨戒 2.5 / 机枪哨戒 2.5 / 加特林 3.5 / 地雷 3.5 —— 与 wiki 模块 `remove_time` 逐一相同 |
| 寿命只对"会自己撤走"的东西非 0 | **✓ 离线** | 哨戒 150–180、特斯拉塔 150、护盾中继站 40；**HMG/反坦克阵地 = 0（人不走它就不走）**；地雷 = 0 |
| 改这一格能改变存活时长 | **✓ 实机（2026-10-25）** | `150 → 30` 后用户实测「约 30 s 自己消失」；600 s 版未测（留着备用）|
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

**“箭头”这列是什么**：它是**这发战备的呼叫码（call-in code）长度** —— 就是你在战备栏里按的箭头上/右/下/左序列。

- 数据位置：`StratagemInfo` 行 **`+0x40`**（u64，payload 相对偏移）= 箭头数组的地址，**`+0x48`**（u32）= 箭头个数；
- 数组每项一个 u32：**1 = ↑、2 = →、3 = ↓、4 = ←**；
- 逐项解码与 wiki 的 `stratcode` **完全一致**（4 件抽样）：

| 战备 | 我们的数组 | 解码 | wiki `stratcode` |
|---|---|---|---|
| `SENTRYS. MACHINEGUN`（A/MG-43） | `[3,1,2,2,1]` | ↓↑→→↑ | Down, Up, Right, Right, Up ✓ |
| `SENTRYS. ROCKET`（A/MLS-4X） | `[3,1,2,2,4]` | ↓↑→→← | Down, Up, Right, Right, Left ✓ |
| `SENTRIES. LASER CANNON SENTRY` | `[3,1,2,3,1,2]` | ↓↑→↓↑→ | Down, Up, Right, Down, Up, Right ✓ |
| `EMPLACEMENTS. HEAVY MACHINEGUN EMPLACEMENT` | `[3,1,4,2,2,4]` | ↓↑←→→← | Down, Up, Left, Right, Right, Left ✓ |

### 2.1 呼叫码能不能自己改（2026-10-25 晚）

**能，而且这是纯数据**。三个旋钮都在 `StratagemInfo` 行里：

| 旋钮 | 位置 | 说明 |
|---|---|---|
| 箭头内容 | 数组（`body + [+0x40]`，每项 u32） | 1=↑ 2=→ 3=↓ 4=← |
| 箭头数量 | `+0x48`（u32） | 1..9（SHODAN 的 `MAX = 9`）|
| 数组地址 | `+0x40`（u64，**payload 相对**） | 想让码更长时，把新数组写到空位再改这里 |

**本 build 的排布**：每个块的 payload 是「行数组 + 一个字符串/数组 blob」，各战备的箭头数组**在 blob 里连续排布**。
例：MG-43 哨戒的数组在 `0x11FE0`，占 5×4 B，**紧跟其后还有 2 个零字**（`0x11FF4`、`0x11FF8`），再往后就是别的数据。
⇒ 实践结论：

- **等长改**（换个序列）：直接写 5 个 u32，最稳（本轮就是这条）；
- **变短**：写前面几项 + 把 `+0x48` 改小，残留的箭头字没人读；
- **变长 ≤ +2**：MG-43 这一行后面恰好有空位，可以先占零字（别的行不一定有，改前先 dump 一眼邻居）；
- **更长 / 邻居被占**：必须把新数组写到块 payload 尾部（或别处空位）再改 `+0x40` —— 这需要**给中间块长 payload**。

> **“给中间块长 payload”我们已经有现成能力了**（2026-10-25 修正）：
> `tools/passive_bonus_edit.py` 做的就是**整容器重排 + 尾字校正**（它的注释原话：
> “`plain_edit.py` 只会在文件尾追加，改不了这种结构”），用在护甲被动叠行上，并且
> [ARMOR-KIT-WEIGHTS §9.5](ARMOR-KIT-WEIGHTS-26088801.md) **✓✓ 实机**证过：往 pm 数组加一行 ⇒
> **中间块 payload 变长、后续块偏移全部平移、文件 +24 B**，引擎照常解析（盔甲等级 150 → 250，恰好 = 求和）。
> ⇒ 呼叫码要变长，把那段重排逻辑抽成通用工具（`--block N --append hex:…`）即可；
> 注意本表（战备设置）用的是 24 B 头 `'LDLD'|ver|type|payload|wide|extra`（payload 尺寸在 `head+12`），
> 和实体库的 28 B 头变体不同。

**✓✓ 实机（2026-10-25）**：MG-43 哨戒 `[3,1,2,2,1] ↓↑→→↑` → `[1,1,3,3,1] ↑↑↓↓↑`
（`6c334081925df084`）后，用户报「**战备栏箭头串变成 ↑↑↓↓↑，按它能叫出来**」
⇒ **呼叫码是纯数据可改，且 HUD 直接读这张表的数组**。

**加长测试（⚠ 待实机）**：10 个 ↓（`[3]×10`，40 B）—— 用新工具
[`tools/block_payload_append.py`](../../tools/block_payload_append.py) 做**整容器重排**：
新数组追加到该块 payload 末尾（`payload 4860 → 4900`），`+0x40 = 4860`、`+0x48 = 10`，
后面所有块平移 40 B、末块再吃 8 B 尾字，Murmur 拉回 `0x04BBE33EF809862A`。
产物：`generated_stratagem_settings.code10.sealed.dl_bin`（`f02d51612437ccc8`；明文 `0220411ba395355a`，82,520 B）。
门禁 G1/G1b/G2/G2b/G3/G4/G5/G6 全 PASS（邻居 code 复查：加特林 4、迫击炮 5、激光 6 未变）。

**✓✓ 实机（2026-10-25 23:3x）**：10 个 ↓ 的版本**HUD 照常显示 10 个箭头、也能正常叫出来**
⇒ 呼叫码长度上限 **≥10**，SHODAN 的 `MAX=9` 只是它自己的 UI 限制；重排在战备表上也成立。

### 2.2 两个战备共用同一个呼叫码（2026-10-25，⚠ 待实机）

**先看原版数据**：153 行里**本来就存在 9 组同码**（多数是"同一发战备在不同池里"）：

| 码 | 重名的两行 |
|---|---|
| `CONSUMABLES. RESUPPLY` = `PRESIDENT REWARDS. AMMO CACHE` | 真·不同战备 |
| `EAGLE. AIR SUPPORT` = `EAGLE. (NOT USED) ADDITIONAL STRAFING RUNS` | 真·不同战备 |
| JUMPPACK / EXTRACTION / RAISE FLAG / EXTRACTION BEACON / REINFORCEMENT BEACON / COMBAT WALKER / MACHINEGUN | 同族/任务池副本 |

⇒ 数据层**允许**同码；真正的问号是「**两条都在配装里时按这个码叫，会叫出谁**」。

**本轮测试件**：把 MG-43 哨戒的码改回 3 个箭头、内容 = `ORBITAL. PRECISION STRIKE` 的 `[2,2,1] →→↑`
（复用上一轮追加在 payload 尾部的数组，`+0x48 = 3`）：

| 文件 | sha256 | 内容 |
|---|---|---|
| `generated_stratagem_settings.code_dup.sealed.dl_bin` | **`a94c95226cda89fb`** | MG-43 = →→↑（与 Precision Strike 同码）|

判读（同时带两发进任务）：

| 现象 | 结论 |
|---|---|
| 战备栏两发都显示 →→↑，按码叫出**其中一发**（另一发仍可用/或不可用） | 引擎按"第一个匹配"解析 ⇒ 记录谁优先（很可能是配装栏里靠前的那发）|
| 按码**叫不出任何一发** | 同码冲突被拒 ⇒ 记档 |
| **两发同时下来** | 码→多发的映射 ⇒ 记档（少见）|
| 把两发在配装栏里**换位置**再叫 → 谁出来跟着变 | 确认"先到先得"是按栏位顺序 |

判读：战备栏里 MG-43 图标下的箭头串**变了** ⇒ 这串数据就是 HUD 的来源；按 **↑↑↓↓↑** 能叫出来 ⇒ 完全通了；
箭头串没变、但按 ↑↑↓↓↑ 能叫 ⇒ HUD 另有来源（下一步查 UI/armory 资源）；两者都不变 ⇒ 叫码在别处（再查 `StratagemType` 资源）。

> SHODAN 也是这么读的（`MOD.code`：`+64` 数组、`+72` 个数，箭头值 1..4 同义），它的“Call-in code”
> 滑杆把这些箭头换算成一个五进制数（↑=1 … ←=4）好让你输入。**改它 = 改这发战备的呼叫序列**（离线可行，⚠ 未实机）。

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

| 文件 | 大小 | sha256 | 值 |
|---|---:|---|---:|
| `D:\mod\out\sentry-life\generated_entities.life30.sealed.dl_bin` | 47,259,736 | **`03f80e9d121f2953`** | **30 s**（本轮，快读数）|
| `D:\mod\out\sentry-life\generated_entities.life600.sealed.dl_bin` | 47,259,736 | `0a9d2542e9a6531a` | 600 s（备用，一小时不用等）|

**✓ 实机读数（2026-10-25）**：用户报「**约 30 s 自己消失**」⇒ 寿命字段成立，单位 = 秒，起点基本在部署/落地那一侧。

改动：**MG-43 哨戒炮 `HellpodPayload +0x04`：150 → 30**（其余一字未动；基址是上一轮投送舱 rig 的实体文件，
火箭炮塔 / rack 29 那套都还在）。30 s 比 150 s 短 5 倍，落地后**半分钟内就能读数**，不用等。

判读：叫一台 MG-43 哨戒炮，**别打爆、也别打空** ——
- 约 **30 s** 自己消失 ⇒ 字段成立，且寿命单位就是秒、基本从"落地/部署"起算；
- 照旧 **150 s** 才消失 ⇒ 这个 f32 没被读（回到 §5 的第二处怀疑：`Turret` 或行为脚本）；
- **秒级差异**（比如 30 s 后还在、40 s 才走）⇒ 成立但起点含投放延迟（倒计时 3 s + pod 下落），顺手记下偏移量；
- 根本没出现/召唤失败 ⇒ 先查是不是又装回了旧实体文件。

---

## 5 还没解 / 别踩

| 项 | 说明 |
|---|---|
| `HellpodPayload +0x08` | 1267/1268/1270/2424/2529/2537 —— 像"投放模板"枚举，同值组行为一致，但**没有差分证据** |
| `Health +0x000` = 400 vs wiki 200 | 两个来源打架；⚠ 要区分"含护甲的最大值"与"可显示 HP" |
| `Turret +0x2C/+0x30/+0x44/+0x48` | 看着是哈希/枚举（非浮点），未命名 |
| wiki 模块代差 | Laser Sentry 的 cooldown/calltime 与本 build 不同；**别照抄 wiki 数值当本 build 真值** |
| 寿命是不是"从落地起算" | 本字段只证明"值 150 = 页面寿命"，**起点**（投放/落地/首次开火）未验 ⚠ |
