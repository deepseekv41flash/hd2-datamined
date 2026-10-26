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

### 2.2 两个战备共用同一个呼叫码（2026-10-25，✓✓ 实机：按栏位顺序先到先得）

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

**✓✓ 实机（2026-10-25 23:5x）**：MG-43 哨戒（→→↑）与 `ORBITAL. PRECISION STRIKE`（→→↑）**同时带进任务**，
用户报「**按栏位顺序先到先得**」⇒ 同码解析 = **按配装栏里靠前的那一发**，不是随机、也不是报错。

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

## 3.8 哨戒炮的「弹药 / 转动 / 行为」一览（离线，本 build）

| 哨戒 | 本体实体 | behaviour | 弹容量 `+0x88` | 初始备匣 `+0x8C` | 补给量 `+0x90` | 膛内 `+0x9C` | 转速 俯/水 | 俯仰限 | 水平限 |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| A/MG-43 机枪 | `0x37CDE43876BA26BB` | **313** | 175 | 0 | 6 | 1 | 50 / 80 | −60…90 | ±180 |
| A/G-16 加特林 | `0xEF85D6CF58E31D70` | 214 | 500 | 0 | 6 | 1 | 50 / 80 | −60…90 | ±180 |
| A/M-12 迫击炮 | `0x51A0812E3BCE2D74` | 320 | 36 | 0 | 6 | 1 | 55 / 55 | 35…89 | ±180 |
| A/M-23 EMS 迫击炮 | `0xB2053A1838092F8B` | 324 | 16 | 0 | 6 | 1 | 55 / 55 | 35…89 | ±180 |
| 毒气迫击炮 | `0x299C0D3DFD2F0994` | 321 | 16 | 0 | 6 | 1 | 55 / 55 | 35…89 | ±180 |
| A/MLS-4X 火箭 | `0x37079568DC86E9C6` | 611 | 16 | 1 | 6 | 0 | 40 / 40 | −45…90 | ±180 |
| A/AC-8 自动炮 | `0x54D86057F5DACFB9` | 5 | 24 | 0 | 6 | 1 | 20 / 20 | −60…70 | ±180 |
| 火焰哨戒 | `0x820CC3BAFE962858` | 208 | 600 | 0 | 6 | 0 | 140 / 140 | −45…90 | ±180 |
| A/LAS-98 激光 | `0x56070F36CFFFA8A8` | 309 | **无弹匣组件**（能量武器）| — | — | — | 50 / 80 | −60…90 | ±180 |

- 弹容量/备匣/补给/膛内都在 `WeaponMagazineComponentData`（`0xFB8D88A3`）里，与 wiki 的
  `magazine_capacity / chambered / magazines_refill` 逐值对上（MG-43：175 / 1 / 6）✓。
- 转速与限位在 `TurretComponentData`（`0x1EBA7593`）`+0x08/+0x0C` 与 `+0x14…+0x20` ✓（wiki `turn_speed_*`、`vertical_limit_*` 同值）。
- **每个哨戒的 behaviour 都不同**（313 / 214 / 320 / 324 / 321 / 611 / 5 / 208 / 309），都是 AI 行为；
  玩家要自己开就得改 **658**（我们已在运输机炮塔 / 地堡炮塔 / 火箭炮塔上验过）。

### 3.8.1 哨戒炮算不算「mount」？（2026-10-25，✓ 离线判定）

| 问题 | 答案 | 依据 |
|---|---|---|
| 它能被**装到载具槽位**里吗？ | **按五件套判据：能** | 28 组件里齐了 `Unit` + `Turret` + `Wieldable` + `WeaponWielder` + `ProjectileWeapon`（外加 `WeaponData` / `WeaponMagazine` / `Health`）——这正是我们装 40mm 站 / 运输机炮塔 / 地堡炮塔 / 光明族炮头时要求的组合 |
| 它**自己是 mount 宿主**吗？ | **不是** | 28 组件里**没有** `MountComponentData` ⇒ 它没有挂载槽，只能"被装"，不能"装别人" |
| 原版有没有把哨戒当挂载件用过？ | **没有** | 165 条 `MountComponentData` 记录里**一个哨戒都没有**（离线普查）；⇒ 这是新实验 |
| 阵营要改吗？ | **不用** | `Faction +0 = 1`（超级地球）✓ |
| 行为要改吗？ | **要** | `Behavior +0` = 313 等 AI 行为 ⇒ 改 **658** 才是玩家武器行为 |
| 包怎么来？ | `LoadoutPackage +8 = 0x154BD6143819DF7D` | 与战备行 129 的 `+0xA8` 同一个包；可走 `+0xA8` 声明或 §3.8.2 的补丁 |
| 壳是什么形态？ | **自身**（`Unit +0` = 自己）| 装到车顶会显示成"落地形态"（机枪哨戒=三脚架），不是车顶炮塔形态 ⇒ 位置能对，**转动/炮口锚点要看骨骼是否支持** |

**一个顺带的好问题**：哨戒本体带着 `HellpodPayload`（`+0x04` 寿命 150 s）—— 如果把它装到载具上，
**它会不会 150 s 后自己消失？** 这正是 §2 那个字段的第二处用途，一轮就能测出来（而且现在我们能随意改这个值）。

### 3.8.2 装到载具上的配方（沿用挂载线，✓ 已装上待验）

```bash
# ① 挂载：把 TD-110 槽 2 换成 A/MG-43 哨戒本体
python tools/mount_table.py swap --entity 0xB0C9FAF4AF8903F9 --slot 2     --item 0x37CDE43876BA26BB --out ent.plain
# ② 行为：313 → 658（AI 放手）；阵营已是 1，不用动
python tools/entity_field_set.py set --plain ent.plain --block 0xBA9B803D     --key 0x37CDE43876BA26BB --field 0 --type u32 --value 658 --out ent2.plain
# ③ 包：战备行 +0xA8 写 0x154BD6143819DF7D（或按 RESOURCE-RESIDENCY 用补丁塞进常驻包）
python tools/plain_edit.py --plain strat.dl_bin --out strat2.dl_bin --set 0x7084=u64:0x154BD6143819DF7D
```

**本轮已装（2026-10-25 23:40，⚠ 待实机）**

| 文件 | sha256 | 改动 |
|---|---|---|
| `generated_entities.dl_bin` | **`4803871a669ca6b0`** | TD-110 槽 2：`5D142C3A73EBC634`（火箭炮塔）→ **`37CDE43876BA26BB`（MG-43 哨戒）**；`Behavior 313 → 658` |
| `generated_stratagem_settings.dl_bin` | **`61001ad1868d292f`** | 行 57 `+0xA8` = `154BD6143819DF7D`（哨戒包，61 资源：18 texture/15 animation/7 particles/6 material/5 mesh/4 physics/2 bones/2 state_machine）|

门禁：`mount_table swap` G1–G10 全过（全表只有 125 行 2 槽变了）、`entity_field_set` G1–G8 全过、
`plain_edit` G1–G6 全过；实体锚点 `8E49771B181FFAA1`、战备 Murmur `0x04BBE33EF809862A` 均保持。

**这一局要看的四件事**（按信息量排序）：

1. 车顶**出不出** MG-43 哨戒（出 = 挂载件判据成立；三脚架形态是预期，位置歪也正常）；
2. 驾驶位**能不能操作**（准星/开火，即 `Behavior 658` 是否把它变成玩家武器行为）；
3. 炮管**跟不跟瞄准转**（转动依赖壳的骨骼；MG-43 哨戒 `Turret` 限位 ±180/−60…90，数据侧没问题）；
4. **会不会 150 s 后自己消失** —— 它本体带 `HellpodPayload`（`+0x04` = 150 s），
   如果连挂载件也吃这个寿命，那这个字段就是"载具外来件的定时消失"开关，改它即可（§2）。

回滚：`install --sealed D:\mod\out\sentry-life\generated_entities.life30.sealed.dl_bin`（`03f80e9d121f2953`）
＋`...generated_stratagem_settings.code_dup.sealed.dl_bin`（`a94c95226cda89fb`）。

**⚠ 实机读数（2026-10-25 23:4x）**：TD-110 槽 2 装 MG-43 哨戒 —— **车顶看不到**（用户判断：穿模进车体里了，
因为哨戒壳是「落地三脚架」形态、原点在底座），但**驾驶位可以正常操作**。
⇒ 两条结论：**① 哨戒作为挂载件成立**（引擎生成了它、可开火/瞄准）；
**② 「壳形态」决定外观是否可用**（与 15.1 的判据一致），要车顶炮塔外观还得挑车顶形态的壳。

### 3.8.3 换到 M-102 Gunner FRV（炮手位，长炮管便于观察）（2026-10-25 23:5x，⚠ 待实机）

| 文件 | sha256 | 改动 |
|---|---|---|
| `generated_entities.dl_bin` | **`02b740fef30a7f7a`** | ① TD-110 槽 2 回原版烟幕 `3A061009AA31E9CB`；② **M-102 两条挂载记录（行 19 `CC21C7FFD3EBEFB9` 与行 119 `E9CD1D0D118886AF`）槽 0 = `54D86057F5DACFB9`（A/AC-8 自动炮哨戒）**；③ AC-8 `Behavior 5 → 658` |
| `generated_stratagem_settings.dl_bin` | **`081e7879cb6575e2`** | 行 57 `+0xA8` = `54DC633A67BAA93D`（AC-8 包，43 资源）· 行 59 `+0xA8` = `418322D5FF8B13BC`（AC-8 壳的 bones/mesh/physics/state_machine 所在包）|

AC-8 关键字段：`Faction 1`（不用改）· `Behavior 5→658` · `Unit +0 = CBFE1FC7158347F3`（壳**不是自己**）·
`LoadoutPackage = 54DC633A67BAA93D` · 弹容 24 · 弹丸 122 · 转速 20/20 · 俯仰 −60…70 · 水平 ±180。

**⚠ 实机读数（2026-10-25 23:5x）**：FRV 炮手位装 AC-8 —— ①**模型陷进车里** ②**是"未展开"形态**
③**开火点在炮管上方空中**。原因（离线证据）：

| 现象 | 原因 |
|---|---|
| 未展开 | AC-8 的壳是 **`aa_turret`**（`content/fac_helldivers/hellpod/aa_turret/aa_turret`，id `CBFE1FC7158347F3`，bones/mesh/state_machine **同 id**）+ **8 段 animation** ⇒ 这是**空投舱炮塔**，落地后由**状态机**切到展开姿态；**挂载路径不跑部署流程** ⇒ 永远停在默认（折叠）状态。MG-43 同理（`turret_machinegun_gpmg`，2 个 state_machine + 14 段动画）|
| 陷进车里 | 该壳的原点在**地面/舱底座**，而炮手位 node 期望"手持武器"的原点（握把/枢轴）⇒ 整体下沉（折叠姿态更低，观感更差）|
| 开火点在空中 | 开火/特效按**枪口骨骼**算；折叠状态下骨骼链不在展开位置 ⇒ 悬空。与光明族炮头当年"光束从错处出"同型 |

**修法（按成本）**：

1. **借车顶形态壳**（已装，见下）：把 AC-8 的 `Unit +0` 换成 **40mm 站壳 `9872EEB31A5F88FD`**（或 Barrager 车顶炮塔 `5D142C3A73EBC634`）。
   车顶壳没有折叠状态、原点在车顶枢轴 ⇒ 外观/炮口/转动一次到位；**火力仍是 AC-8 的**（24 发、20°/s、−60…70）。
   ⚠ 副作用：借壳是**件级**的，AC-8 **哨戒战备**那台落地炮也会跟着变成 40mm 站外观。
2. 直接用本来就是车顶形态的武器站（火箭炮塔 / 40mm 站），把 AC-8 的数值搬过去。
3. ✗ 只调 `MountInfo` offset：能抬起来，但折叠姿态与空中开火点治不了。
4. ✗ 改 `state_machine` 初始状态：资产级、且挂载路径可能仍强制默认态。

**state_machine 在哪**：它是**包里的资源**（不是 `.dl_bin` 表）——`type=state_machine`，
`file_id` 与壳 id 相同；AC-8 = `CBFE1FC7158347F3` 在包 `54dc633a67baa93d`（副本 `418322d5ff8b13bc`），
大小 **3,372 B**、`gpu=0/stream=0`（纯 toc）；MG-43 = `37CDE43876BA26BB` 在 `fc5b6bff0db90aab`/`154bd6143819df7d`；
而 40mm 车顶站的 `9872EEB31A5F88FD` 在**共享基础包 `f6fb08cc02d24255`** 里（这也解释了它“在车上零预热、没有折叠态”）。
物理位置在 `data/bundles.NN.nxa`，按包 id 取即可：
`python -m srkit extract --id CBFE1FC7158347F3 --type state_machine --package 54dc633a67baa93d -o out "<game>/data"`
（⚠ 包名必须**小写**）。离线看结构：开头是 `(offset,count)` 段表 —— (1,6)(80,7)(2944,3)(2972,5)(2996,0)(0,4)(3360,4)(3368,0)，
之后全是数字/哈希，**没有 ASCII 状态名**、也不含那 8 个动画 file_id ⇒ 状态名是另一套哈希，
要“把默认态改成展开”得先解出状态表语义（资产级、未解、风险高）。

**借壳版已装**：`generated_entities.dl_bin` = **`ef27eaf4e5310ca8`**（在 `02b740fef30a7f7a` 基础上只改 AC-8 `Unit +0` → `9872EEB31A5F88FD`）。

判读：炮手位出不出「自动炮哨戒」的模型（长炮管）；能不能瞄准/开火；炮管跟不跟瞄准转；
会不会 150 s（`HellpodPayload`）自己消失。若模型仍陷进车里，就说明**原点/挂点**对不上——
下一步可走「借车顶形态壳」（`Unit +0` 换成 40mm 站或火箭炮塔那种车顶壳）或调 `MountInfo` 的 offset。

### 3.8.4 ✓✓ 实机：改 `state_machine` 的默认态，把"未展开"的哨戒修好（2026-10-26 00:0x）

**结论**：空投舱炮塔类壳的折叠/展开由 **`state_machine` 资源的 `layer.DefaultState`** 决定；
把它改成"展开"那一档，挂到载具上时**直接以展开形态出场**——AC-8 挂 M-102 炮手位实测：
**模型展开、原点正确、开火点在炮管上、开火动画正常**（用户原话：展开本来就有一个往上伸的动作，现在全对）。

**✓✓ 实机那一套（AC-8，2026-10-26 00:0x）**

| 文件 | 值 | 用途 |
|---|---|---|
| `data/9ba626afa44a3aa3.patch_7`（3,568 B） | entry `state_machine CBFE1FC7158347F3`，`0x74: 3→2` | 让 AC-8 以展开形态出场 |
| `generated_entities.dl_bin` | **`02b740fef30a7f7a`** | FRV 炮手位（行 19/119 槽 0）= AC-8 **自己的 `aa_turret` 壳**；`Behavior 5→658`；TD-110 槽 2 回原版烟幕 |
| `generated_stratagem_settings.dl_bin` | `081e7879cb6575e2` | 行 57/59 声明 AC-8 的两个包 |

⇒ 上一版"借 40mm 壳"只是绕过；**正解是改状态机默认态**——外观、原点、炮口一次到位，且不用改壳（各哨戒外观/数值保持原生）。

**格式（来自 [xypwn/filediver](https://github.com/xypwn/filediver) 的 `stingray/state_machine`，BSD-3）**

```
头 15×u32: unk00 | 组数 | 组表偏移 | 事件哈希数 | 事件偏移 | 变量数 | 变量映射偏移
           | 骨骼透明数 | 骨骼透明偏移 | unk0 数量/偏移 | unk1 数量/偏移 | unk2 数量/偏移
组表 @组表偏移: count(u32) + offsets[]
每层 @组表偏移+off: Magic(u32) | ★DefaultState(u32) | Count(u32) | Offsets[Count]
每个 state: 名字(Hash64) 类型(0=Clip 1=Empty 2=Blend 3=Time 5=Ragdoll)
            动画哈希表+权重 | Loop | Additive | 过渡表 Link{Index,BlendTime,Type,Beat}
            | EmitEndEvent | EndTransitionTime | …
过渡类型: Immediate / WaitEnd / SyncBeatClosestImmediate / WaitUntilBeat / Sync% / SyncInverse%
```

**改法**（一层一个 u32，layer0 在文件偏移 **`0x74`**；各 SM 的偏移不同，用 `--show` 读）：

```bash
python tools/state_machine_edit.py --show --layer 0 sm.bin           # 看层/状态/默认
python tools/state_machine_edit.py --decode --names <hashlist>.csv sm.bin   # 事件表/过渡/部署完成态
python tools/state_machine_edit.py --set 0=2 --out sm_new.bin sm.bin # ③→②（折叠→展开）
# 打成补丁（资源层）：entry type = A486D4045106165C(state_machine)，id = 该 SM 的 file_id
python tools/resource_patch.py build spec.json -o out --index 7
cp out/9ba626afa44a3aa3.patch_7* "<game>/data/"
```

#### 3.8.4.1 ✓ 离线：layer0 四个状态的真实语义（`--decode` 解出，2026-10-26 10:2x）

`state_machine` 的 `AnimationEvent = {事件哈希 u32, Link 索引 i32}`，`Link = {目标态, BlendTime, 类型, Beat}`；
事件的哈希能在 `hashlist-normalized.csv` 里**直接查出名字**。AC-8（`CBFE1FC7158347F3`）layer0 全解：

| state | 名字哈希 | clip | loop | `EmitEndEvent` | 事件→过渡 | 语义 |
|---|---|---|---|---:|---|---|
| 0 | `0x79DE1870039A1A7E` | `3168C572…` | 0 | `DeployDone` endT=0.20 | DeployDone→**s2**、PackageRetract→s1、PackageDeploy→s0 | **部署过渡（播完就"展开完成"）** |
| 1 | `0xD23167BF92D249B8` | `314AE842…` | 0 | — | PackageDeploy→s0、PackageRetract→s1 | **收起后停驻** |
| 2 | `0x823905BD6B62BA3E` | `314AE842…` | 1 | — | PackageRetract→s1、PackageDeploy→s0 | **部署完成 = 展开** |
| 3 | `0x330CA356421F7ADA` | `3168C572…` | 1 | — | PackageDeploy→s0、PackageRetract→s1 | **待部署 = 折叠**（原默认） |

事件表：`0x3D0B77D2=DeployDone · 0x27A2636E=RetractDone · 0x72C4271D=PackageDeploy ·
0x6F8B215F=PackageRetract · 0xF5EACFD8=Fire · 0xA4DD22E8=FireDone · 0xE62AFEFC=未命名`。

⇒ **可复用的判据**：**部署过渡态（loop=0、带 `EmitEndEvent`）的 `EmitEndEvent` 在该 state 的
事件表里查到的那条 Link 指向的 state = "部署完成态"（= 展开）**。
AC-8 上这条规则给出的正是 state2 —— 与我们实机验证的改法完全一致。

**状态名是全局共享词汇**（同一 name 在不同壳里复用，绑的 clip 各自不同）：

| 状态名 | 角色 | 出现在 |
|---|---|---|
| `0x79DE1870039A1A7E` | 部署过渡 | **全部 7 个 SM** + 人操阵地 |
| `0xD23167BF92D249B8` | 收起 | 全部 7 个 SM + 人操阵地 |
| `0x330CA356421F7ADA` | **待部署（折叠）** | AC-8 / 火箭 / 火焰 / 激光 / 人操阵地 |
| `0x823905BD6B62BA3E` | **部署完成（展开）** | AC-8 / 火箭 / 火焰 / 激光 / 人操阵地 |
| `0xE954AED4871D630A` | 模板 B 的 idle（loop=1，默认） | MG-43 / 加特林 / 迫击炮 |
| `0x69484BEF5AC55426` | 模板 B 的"部署后"（loop=1） | 仅迫击炮 |

#### 3.8.4.2 九个哨戒 = **七份 SM、两套模板**（不是同一份文件）

`Unit +0` 读出的壳 id 就是 SM 的 `file_id`（`srkit list --type state_machine` 全库 2,099 条 / 448 个去重 id，
按 id 取即可；同一 id 的多份副本**逐字节相同**，实测 MG-43/加特林/迫击炮/火箭 4 组副本 sha256 一致）。

| 哨戒 | 本体实体 | 壳 / SM file_id | SM 名 | 大小 | 层 | layer0 状态 | 默认 | 部署完成态 | 模板 |
|---|---|---|---|---|---:|---:|---:|---|---|
| A/MG-43 | `37CDE43876BA26BB` | 同左 | `…/turret_machinegun_gpmg` | 4,012 | 7 | 3 | s0 `E954AED4` | （无独立态，见下） | **B** |
| A/G-16 加特林 | `EF85D6CF58E31D70` | `61D9DDA22A59E9BC` | `…/hellpod/turret/turret` | 5,724 | 8 | 3 | s0 `E954AED4` | 同上 | **B** |
| A/M-12 迫击炮 | `51A0812E3BCE2D74` | 同左 | `ar_turret/mortar_turret` | 4,276 | 7 | 4 | s0 `E954AED4` | **s3 `69484BEF`**（loop=1） | **B** |
| A/M-23 EMS / 毒气 | `B2053A18…` / `299C0D3D…` | **共用** `51A0812E3BCE2D74` | 同上 | 4,276 | 7 | 4 | 同上 | 同上 | **B** |
| A/MLS-4X 火箭 | `37079568DC86E9C6` | 同左 | `et_turret/rocket_turret` | 4,364 | 8 | 4 | s1 `330CA356` | **s3 `823905BD`** | **A** |
| A/AC-8 自动炮 | `54D86057F5DACFB9` | `CBFE1FC7158347F3` | `…/hellpod/aa_turret/aa_turret` | 3,372 | 6 | 4 | s3 `330CA356` | **s2 `823905BD`** | **A** |
| 火焰哨戒 | `820CC3BAFE962858` | 同左 | （无名） | 2,100 | 4 | 4 | s1 `330CA356` | **s3 `823905BD`** | **A** |
| A/LAS-98 激光 | `56070F36CFFFA8A8` | 同左 | （无名） | 2,140 | 4 | 4 | s3 `330CA356` | **s1 `823905BD`** | **A** |
| （参照）人操阵地 | — | `0E977C49DB7604F9` | `…/hellpod/manned_turret` | 4,820 | 6 | 4 | s1 `330CA356` | s2 `823905BD` | **A** |

**同构性结论（回答"能不能照抄"）**：

* **不同构**：7 份 SM 是不同文件，层数 4–8、layer0 状态数 3–4、状态名集合都不一样；
* **但同模板内部完全同构**：模板 A（AC-8/火箭/火焰/激光/人操阵地）四个状态的名字**一模一样**，
  只有 clip、loop 标志和索引不同 ⇒ **改法照抄，只需换索引**（这就是"同构"的实用定义）；
* 模板 B（MG-43/加特林/迫击炮）是另一套三/四态结构，默认态也是 `E954AED4`，
  **没有 `330CA356`/`823905BD` 这对折叠/展开态** ⇒ 不能照抄（见下 ⚠）。

每份 SM 各自的包：`LoadoutPackage +8` 就是它自己的包（MG-43 `154BD6143819DF7D`、加特林 `992D325D88DE5FBF`、
迫击炮 `8C5A99A9A40D5B8D`、EMS `4666692B63185121`、毒气 `71D9EA5D656B09B8`、火箭 `11BBDF8CE39E5FC5`、
AC-8 `54DC633A67BAA93D`、火焰 `1577E917AD1F287D`、激光 `36313BF684C1FD79`）；
另有一份公共包 `fc5b6bff0db90aab` 存了 MG-43/加特林/迫击炮/火箭 4 份副本（字节相同）。

#### 3.8.4.3 已打补丁：模板 A 的另外三个

| 文件 | 大小 | entry | 改动 | 状态 |
|---|---:|---|---|---|
| `data/9ba626afa44a3aa3.patch_8` | 4,528 B | `state_machine 820CC3BAFE962858`（火焰） | layer0 `1 → 3`（`330CA356` → `823905BD`） | ⚠ 待实机 |
| 同上 | | `state_machine 56070F36CFFFA8A8`（激光） | layer0 `3 → 1` | ⚠ 待实机 |
| `data/f6fb08cc02d24255.patch_1` 里附带的 `state_machine 37079568DC86E9C6`（火箭） | 41 条整包 | layer0 `1 → 0`（折叠 → **部署态本身**，见 §3.8.4.4） | ⚠ 待实机 |

> 火箭那份 SM 现在**只存在于资源层补丁**里（patch_8 已把它去掉），这样"整包驻留"这条路线才是唯一来源。

**当前验证配置**（`D:\mod\out\sm-verify\` + `D:\mod\out\rocket-res-patch\`，已装，盘上回读逐字节一致）：
**火箭哨戒包的资源走「资源层驻留」（`data/f6fb08cc02d24255.patch_1`），战备表 `+0xA8` 全清零** ——
刻意不用声明口，给 [资源层驻留](../engine/RESOURCE-RESIDENCY-26088801.md) 的 P4 补一个"载具挂载件"案例。

| 文件 | sha256 | 改动 |
|---|---|---|
| `generated_entities.dl_bin` | **`2a5ce9ba6b699792`** | FRV 炮手位（行 19/119 槽 0）= **A/MLS-4X 火箭哨戒** `37079568DC86E9C6`（顶掉 AC-8）；`Behavior 611→658` |
| `generated_stratagem_settings.dl_bin` | `6c0ab66b281c2178` | 行 57（增援信标）/ 59（SOS）的 `+0xA8` **清零** ⇒ 战备表里**没有任何包被声明** |
| `data/f6fb08cc02d24255.patch_1`（+`.gpu_resources` / `.stream`） | **`eb2bfca7c5408a47`**（toc）/ `9c63665fe8e4c6eb`（gpu）/ `56e9e6715ec76329`（stream） | **火箭哨戒包整包 41 条资源**驻留进共享基础包（toc 1.26 MB + gpu 4.37 MB + stream 2.29 MB）；其中 `state_machine` 是 **`layer0 default=3`（展开态）+ `layer5 default=1`（空态，关掉自转）** 那版 |
| ~~`data/f6fb08cc02d24255.patch_2`~~（+`.gpu_resources`） | ~~`52dca8710dde0d37`~~ | **已回退删除**（原为 `unit` 节点 3 的 z +2.0 m，见 §3.8.4.6；因 §3.8.4.9 的动画线索先撤下来做对照）|

回滚到 AC-8 版：把 `D:\mod\out\frv-ac8\ent.sealed.dl_bin`（`02b740fef30a7f7a`）
与 `…\strat.sealed.dl_bin`（`081e7879cb6575e2`）拷回 `data/game/`，并删掉
`data/f6fb08cc02d24255.patch_1*` 三件（`patch_7/8` 保持不动）。

#### 3.8.4.4 「伸出来」那一步：抬升在部署 clip 里，展开态只负责保留（2026-10-26 10:4x）

**✓✓ 实机读数（第一版：默认态 = 展开态 `823905BD`）**

| 项 | 结果 |
|---|---|
| 模型 / 材质 / 贴图 / 动画 | **全部正常**（不是紫问号、不是白模）|
| 需不需要 `+0xA8` 声明 | **不需要**（战备表全零，纯靠 `f6fb08cc02d24255.patch_1` 41 条资源）|
| 姿态 | **是展开状态**（模板 A 的改法对火箭也成立）|
| 位置 | **整体缩在车体里** —— 用户判断"少了个伸出来的动作" |

**壳的骨骼构成**（`srkit extract --type bones --decoded`，✓ 离线）——关键在有没有升降类骨骼：

| 壳 | 骨骼数 | 升降/展开机构相关骨骼 |
|---|---:|---|
| 火箭 `37079568DC86E9C6` | 10 | `traverse` · **`elevator_01`** · **`elevator_02`** · `boss` |
| 火焰 `820CC3BAFE962858` | 10 | `boss` · `traverse` · **`elevator_01`** · **`elevator_02`** |
| 迫击炮 `51A0812E3BCE2D74` | 19 | **`base_elevation_arm`** · `base_elevation_offseter` · **`elevator_slider`** · `elevator_rotator` |
| A/AC-8 `CBFE1FC7158347F3` | 16 | `elevator`（单根）+ `hinge` + `barrels_extension_01/02` |
| A/LAS-98 `56070F36CFFFA8A8` | 6 | 无（只有 `root/rotator/gunhousing/sensorpod`）|
| A/MG-43 `37CDE43876BA26BB` | 11 | 无 |
| A/G-16 `61D9DDA22A59E9BC` | 27 | `c_elevator`（碰撞体）|

**推理链**（✓ 离线推 + 一条实机反证）：

1. 火箭的"伸出"只能发生在**部署过渡 clip**（`86A54B9AA49F833A`，loop=0，`DeployDone`/0.20 s）里，
   或者展开态 clip（`3FCF5875B0663A62`）里；
2. **实机反证**：直接从展开态出生 ⇒ **没有伸出、整体偏低** ⇒ 抬升**不在**展开态 clip 里；
3. 正常部署流程是 `部署态 →(clip 播完 DeployDone)→ 展开态`，落地后是抬起来的
   ⇒ 抬升在**部署 clip** 里，且引擎**跨状态保留了没被后一 clip 动画的骨骼姿态**（部件级分层）；
4. 从展开态出生 = 跳过那唯一一次抬升 ⇒ 升降骨骼停在 bind（下位），整体沉进车体。
   `AC-8` 之所以没这问题：它的展开态 clip 自己就把 `elevator/hinge` 摆到位了。

**改法（本局已装，⚠ 待实机）**：把默认态设成**部署态本身**（火箭 layer0 `3 → 0`）——
出生时播一次完整部署（就是"伸出来"），`DeployDone` 之后自然进展开态，抬升姿态被保留。

```bash
python tools/state_machine_edit.py --set 0=0 --out sm_rocket_s0.bin sm.bin     # 展开态 → 部署态
python tools/whole_package_patch.py build --package 11bbdf8ce39e5fc5 \
    --host f6fb08cc02d24255 --index 1 \
    --edit state_machine:0x37079568DC86E9C6=sm_rocket_s0.bin --install
```

**若这版还不行**，下一步候选（按成本）：

1. **把部署态的 `DeployDone→展开态` 过渡切断**（把那条 Link 的目标改成自身），让它停在部署 clip 末帧
   —— 需要给 `state_machine_edit.py` 加"改 Link"能力；
2. **整层**：给火箭加一层只驱动 `elevator_01/02` 的动画（把部署 clip 里那两段曲线搬出来），
   或找已有层里"抬起位"的状态（rocket 有 8 层：layer1/2 单态 Time loop、layer5/6 Clip loop）；
3. 换壳 / 换挂点（`Unit +0` 借 40mm 站壳）—— 用过，属绕过；
4. **直接抬壳**（改 `unit` 节点位移，§3.8.4.6）—— 本轮已走这条（+2.0 m）。

#### 3.8.4.5 为什么 AC-8 一次就对、火箭却沉？——看"展开态 clip"是不是全身姿态（2026-10-26 11:0x）

`srkit` 对 `animation` 没有解码器，所以补了 [`tools/animation_probe.py`](../../tools/animation_probe.py)：
按 filediver 的 `stingray/animation` 格式读头 + 条目流，输出**长度**与**每个骨骼有没有关键帧**
（条目里骨骼是 10 bit 索引，直接映射到 `bones` 资源的顺序）。

**AC-8（`CBFE1FC7158347F3`，16 骨）** —— 展开态 clip 就是全身姿态：

| clip | 长度 | 用在 | 有键骨骼（数量） |
|---|---:|---|---|
| `314AE842A9346C76` | 0.98 s | **展开态 s2** / 收起 s1 | **14/16 全有键**：`rotator×9` `gunhousing×11` `hinge×19` `barrels_01×2` `barrels_02×18` `root×13` `attach_mag×11` **`elevator×21`** `sensorpod×1` … |
| `3168C5722055589E` | 0.98 s | **部署态 s0** / 折叠 s3 | 13/16：`rotator×9` `gunhousing×11` `hinge×21` `barrels_02×27` `root×13` **`elevator×22`** … |

⇒ AC-8 **根本没有"单独的伸出步骤"可缺**：它的展开态 clip 自己就是 0.98 s 全身姿态，`elevator` 有 21 个键。
把它设成默认态，整机（含升降）一次摆到位——这就是"位置正确"的原因（✓✓ 实机）。
用户记得的"往上伸的动作"是**部署 clip**（`3168C572`，同样 22 个 `elevator` 键），挂载路径并不会播它。

**火箭（`37079568DC86E9C6`，10 骨）** —— 展开态 clip 是**空壳**：

| clip | 长度 | 用在 | 有键骨骼 |
|---|---:|---|---|
| `3FCF5875B0663A62` | **0.17 s** | **展开态 s3** | **0 个**（整个文件只有 1 条 terminator）|
| `72E968DE308896C3` | 0.08 s | 折叠态 s1 | **0 个** |
| `86A54B9AA49F833A` | 0.98 s | **部署态 s0** | `elevator_01×30` `elevator_02×1` `boss×20` `sensor×9` ← **抬升在这里** |
| `9EAFCC13AEDC8BCF` | 1.00 s | 收起态 s2 | `elevator_01×20` `elevator_02×6` `boss×21` `sensor×23` |
| `1D39879F1BE5A80C` | **23.33 s** | layer5 | `traverse×84` `elevator_01×76` `elevator_02×26` `covers×1` |

⇒ 火箭的展开态/折叠态都是**空 clip**（不摆任何骨骼）⇒ 站上去时升降骨骼停在 bind（下位）⇒ 缩在车体里。
AC-8 与火箭用的是**同一套状态名**，但**绑的 clip 质量完全不同**——这就是"同构的状态机、不同构的姿态数据"。

**四个模板 A 壳的对照（✓ 离线判据，可预测实机）**

| 壳 | 展开态 clip | 有键骨骼 | 预测 |
|---|---|---|---|
| A/AC-8 | `314AE842` 0.98 s | 14/16（含 `elevator`）| **一次就对**（✓✓ 已证）|
| 火箭 | `3FCF5875` 0.17 s | **0** | 沉（✓✓ 已证）；改默认态为部署态 **✗ 实机无效**（模型"压根没动"）→ 最终用 §3.8.4.6 的**壳位移**解决 |
| 火焰 | `7A43988B` 1.00 s | **只有 `sensor×15`** | ⚠ **大概率同样沉**（它的 `elevator_01×30` 在部署 clip `0E24AEFE` 里）|
| A/LAS-98 | `88F2CCF2` 0.08 s | **0** | 没有升降骨骼（只有 `root/rotator/gunhousing/sensorpod`）⇒ 沉不沉取决于 bind，⚠ 未知 |

**判据（可复用）**：把某个哨戒挂上载具前，先跑

```bash
python tools/animation_probe.py <展开态 clip> --bones bones_<壳 id>.json --keyed
# 全骨骼有键 ⇒ 直接把默认态设成展开态
# 空/只有少数骨骼 ⇒ 默认态设成**部署态**（让部署 clip 抬一次），或按 §3.8.4.4 后备选处理
```

#### 3.8.4.6 挂载槽没有位移字段 ⇒ 抬升只能改"壳"：`unit` 节点位移（2026-10-26 11:1x，✓✓ 实机）

**为什么不能直接改挂载位置**：`MountInfo` 一条只有 **24 B** ——
`{ item u64 @0 | anchor_a u32 @8 | MountSide u32 @12 | anchor_c u32 @16 | byte20 | byte21 | pad }`，
**没有任何 offset/position 字段**。所以"把件往上抬 2 m"只能改**壳自己**。

**`unit` 资源里有一套节点变换表**（`section_offsets.transform_info` 指过去）：

```
transform 段 = count u32 | 12 B | 每节点 { rot 9×f32, position 3×f32, scale 3×f32, pad } (64 B)
              | 矩阵 count × 64 B（列主序，translation 在 [12..14]）
              | 每节点 { increment u16, parent u16 } | 每节点 name_hash u32
```

**火箭壳（`37079568DC86E9C6`）的节点图**（64 节点，全部 rotation=单位阵 ⇒ 局部 Z 就是"上"）：

| 节点 | 父 | 名字 | 作用 |
|---:|---:|---|---|
| 0 | 0 | `StingrayEntityRoot` | 实体根（原点）|
| 1 | 0 | `FbxAxisSystem_ConvertNode` | FBX 轴转换 |
| **3** | 1 | （无名字，hash `3819713832`）| **内容容器：下面四棵子树全挂它** |
| 4 / 9 / 51 / 58 | 3 | `shadow_mesh` / `skeleton` / `collision` / `game_mesh` | 阴影 / 骨骼 / 碰撞 / 网格 |
| 10→11→14→15 | 9 | `boss`→`traverse`→`elevator_01`→`elevator_02` | 座圈 / 回转 / 升降 |
| 16,33,45… | 15 | `covers` / `laser` / `muzzle_02..04` / `sensor` | **枪口也在这一支里** |
| 5-8, 59-63 | 4 / 58 | `g_turret*`（z=0.968）| 各级 LOD 网格 |

⇒ 把 **节点 3 的 `position.z` 加 2.0**，`position` 与矩阵 `tz` 一起改，整个可见体（含骨骼、碰撞、
**muzzle**）整体上移 2 m。骨骼动画只动 `boss/traverse/elevator` 的局部变换，不会覆盖这条位移。

**工具**：[`tools/unit_offset.py`](../../tools/unit_offset.py)（`srkit` 的 transform 段是"只读视图"、
编码时原样拷贝，所以本工具做**等长二进制改写**，不重编、不碰 gpu）：

```bash
python tools/unit_offset.py show  --unit 0x37079568DC86E9C6 --package 11bbdf8ce39e5fc5   # 列节点
python tools/unit_offset.py shift --unit 0x37079568DC86E9C6 --package 11bbdf8ce39e5fc5     --host f6fb08cc02d24255 --index 2 --node 3 --dz 2.0     --out D:/mod/out/unit-offset --install
```

门禁：**G1** 段与解码 JSON 对得上（采样 position）· **G2** 等长且只有目标 float 变（本轮只变 **2 字节**）·
**G3** 读回目标节点位移正确、其余节点未变 · **G4** 补丁条目 type/id 对、gpu 与源同尺寸 ·
**G5** sha256。产物再经 `srkit extract --decoded` 复核：节点 3 = `[0,0,2.0]`，节点 63 仍是 `0.968` ✓。

**本轮补丁**：`data/f6fb08cc02d24255.patch_2`（21,584 B + gpu 2,955,506 B，sha256 `52dca8710dde0d37`）
—— 只含 **1 条** `unit 37079568DC86E9C6`，叠在整包补丁 `patch_1` 之上（**同宿主同 id，高号胜**）。

**✓✓ 实机（2026-10-26 11:0x）**：模型整体上移约 2 m、离开车体；**弹道仍然从枪管出来**
（说明开火点取的是 `muzzle` 骨骼，它在这一支子树里，跟着一起上移）。
⇒ 这是"挂载件位置不对"的**兜底解法**：不动挂载槽、不动状态机，只平移壳的内容容器节点。
（⚠ 后来 §3.8.4.9 查明：只要**动画所在的包被加载**，火箭哨戒本来就在正确高度，**不需要**这条位移；
位移更适合"包已加载但原点就是不对"的壳。）

抬过头/抬不够只需换 `--dz` 重建同一条补丁（几秒钟）；回滚 = 删 `patch_2` 两件。

#### 3.8.4.7 没人操作时自己左右转 = layer5 的 23 s 扫视 clip（2026-10-26 11:1x，⚠ 待实机）

**现象**：位置修好后（§3.8.4.6 ✓✓），玩家不操作时炮塔自己左右转；不是 AI 抢控制权（`Behavior` 已是 658）。

**诊断方法：逐层对照 AC-8**（同一套状态名 + 同一台车 + 同一个座位，AC-8 不转）——

| 层 | 火箭默认态 | 绑的 clip | 这个 clip 动了哪些骨骼 | AC-8 同层默认 |
|---:|---|---|---|---|
| L0 | s3 展开态 | `3FCF5875` 0.17 s | 无（空 clip）| s2 展开态 |
| L1 | s0 `Time` loop | `5A5489E3` 1.00 s | `traverse×15`（偏航）| s0 `Time` loop `F470E562`（`rotator×15`）|
| L2 | s0 `Time` loop | `991F5044` 1.00 s | `elevator_01×7` | s0 `Time` loop（`gunhousing/hinge/barrels`）|
| **L5** | **s0 `Clip` loop，23.33 s** | **`1D39879F`** | **`traverse×84`** `elevator_01×76` `elevator_02×26` `covers×1` | **`Empty`（`default=1`）** |
| L6 | s0 `Clip` loop 1.00 s | `DE7DF3B6` | `sensor×15`（雷达盘） | AC-8 没有第 6 层 |

⇒ **自转来自 L5**：一个 23.33 s、`traverse` 84 个关键帧的"扫视"循环。
AC-8 之所以不转，是它**同一层的默认态是空态（`Empty`）**——这也是我们给它改 layer0 时顺手留下的对照。
L1/L2 是 `Time` 类型（时间驱动、默认冻结），AC-8 也有同样两层且不转 ⇒ 不是它们。

**改法（本局已装）**：火箭 `layer5.DefaultState` `0 → 1`（选中 `Empty`），并顺手把 `layer0` 回到 `3`（展开态，
和 AC-8 对齐；此前试过 `0`=部署态，实机"压根没动"，无效）。

```bash
python tools/state_machine_edit.py --set 0=3 --set 5=1 --out sm_rocket.bin sm.bin
python tools/whole_package_patch.py build --package 11bbdf8ce39e5fc5     --host f6fb08cc02d24255 --index 1     --edit state_machine:0x37079568DC86E9C6=sm_rocket.bin --install
```

**产物**：`data/f6fb08cc02d24255.patch_1` 重建，toc sha256 **`eb2bfca7c5408a47`**（其余 40 条资源不变）；
`patch_2`（壳 +2.0 m）不动。

**还想调的**：若连 `sensor` 雷达盘的转动也不要，把 `layer6` 默认态也设成 `1`（空态）——⚠ 未试；
层号-N 的对应关系用 `state_machine_edit.py --show` 一看就有。

**推广**：这类"挂着不动/乱动"的问题，**先拿同族里行为正确的那台（这里是 AC-8）做逐层默认态对照**，
差异那一层就是答案——比逐层试三个索引快得多。

#### 3.8.4.8 普查：34 个「能被装」的炮塔壳，只有 AC-8 是自带姿态（2026-10-26 11:2x）

**方法**（[`tools/turret_shell_survey.py`](../../tools/turret_shell_survey.py)）：
① 从 `refs/entity-components.json` 取「`Turret` + `Wieldable` + `WeaponWielder` + `Unit` + `WeaponData`」的实体（只认 `ProjectileWeapon` 会漏掉火焰的 `SprayWeapon` 和激光的 `BeamWeapon`）；
② 读 `Unit +0` 得壳 id（按壳去重）；③ 壳 id 在 `state_machine` 全库清单里找同 id 的 SM → 取所在包；
④ 解出**展开态 clip**（状态名 `0x823905BD…`），用 `animation_probe` 数它**打到了几根骨骼**，与骨架总数比。

**判据**：`A` = 有键 ≥60% 且（壳里有升降骨骼的话）升降也被打到；`B` = 半身 / 升降没打到；`C` = 空 clip（0 键）；`C0` = 空 clip 但壳里没有升降机构；`E` = 模板 B（状态机族不同，另算）；`D` = 没有部署机构（静态站 / 车顶站）。

| 类 | 名称 | 壳 id | 展开态 clip | 有键/骨架 | 升降键到没到 | 结论 |
|---|---|---|---|---|---:|---|
| A 全身姿态（自带，不用调） | A/AC-8 Autocannon Sentry; 未知 | `0xCBFE1FC7158347F3` | `0x314AE842A9346C76` | 14/16 | 是 | **自带姿态，挂上就用** |
| B 半身/升降没被打到（要调） | 未知 | `0x73681FFD58FA1A90` | `0xE0F4D80B2A9F57F4` | 1/8 | 否 | 升降没打到 ⇒ 要调 |
| B 半身/升降没被打到（要调） | A/FLAM-40 Flame Sentry | `0x820CC3BAFE962858` | `0x7A43988B623CBEC1` | 1/10 | 否 | 升降没打到 ⇒ 要调 |
| C 空 clip（要调位置） | A/MLS-4X Rocket Sentry | `0x37079568DC86E9C6` | `0x3FCF5875B0663A62` | 0/10 | 否 | 空 clip ⇒ 要调（+dz） |
| C0 空 clip 但无升降机构（bind 或许就行，未验） | A/LAS-98 Laser Sentry | `0x56070F36CFFFA8A8` | `0x88F2CCF215A33E3B` | 0/6 | 无此机构 | 空 clip 但无升降 ⇒ bind 也许就行（未验） |
| E 模板B（族不同，未验） | A/MG-43 Machine Gun Sentry; Gatling Sentry | `0x37CDE43876BA26BB` | — | — | 无此机构 | 模板 B，未验 |
| E 模板B（族不同，未验） | A/GM-17 Gas Mortar Sentry; A/M-12 Mortar Sentr | `0x51A0812E3BCE2D74` | — | — | 无此机构 | 模板 B，未验 |
| E 模板B（族不同，未验） | A/G-16 Gatling Sentry; 未知 | `0x61D9DDA22A59E9BC` | — | — | 无此机构 | 模板 B，未验 |

**读数**：**34 个壳里只有 1 个 A —— 就是 AC-8**（`✓✓` 实机）。其余哨戒要么升降没被打到（火焰），
要么展开态是空 clip（火箭、激光），要么根本是另一套状态机（MG-43 / 加特林 / 迫击炮）。

**D 类 26 个（没有部署机构）** —— 不用改状态机、也不用调位置，挂上就是它的常态：
`40mm 炮塔站` `9872EEB31A5F88FD`（FRV 原生件，`✓✓`）、`Ballistic Missile` `5D142C3A73EBC634`（TD-110 上位置正确、能转，`✓` 旧档）、`AA Emplacement` `49674794A165EDA8`、`Bunker Turret` `9926876B…` / `CD28A27A…`、`Cannon Turret` `4E342031…` / `CECD6979…`、`SAM Launcher` `A1BDB3A1…`、`Automaton Mortar Emplacement` `6293D7AB…`，以及敌机炮塔（Fusion Repeater / Gazer / Vox Engine / Factory Strider / War Strider / gunship turret 等）与 6 个没有 SM 的静态壳。

⚠ 阵营要单独看：`AA Emplacement` / `Ballistic Missile` / `Bunker Turret` 是 **Faction 8（机器人）**、`Cannon Turret` 是 4、`SAM Launcher` 是 1；要让玩家操作还得 `Faction=1` + `Behavior=658`。

**怎么再跑一遍**（34 个壳约 3 分钟）：

```bash
python tools/turret_shell_survey.py survey --out D:/mod/out/shell-survey \
    --json D:/mod/out/shell-survey/survey.json
```

#### 3.8.4.9 ✓✓ 实机：动画没播的根因 = **包没被加载**（不是状态机、也不是位置）（2026-10-26 11:3x）

**实机观察（用户，关键）**

1. 盘上是"不做位移"的那一版时，**呼叫一次原版 A/MLS-4X 火箭哨戒**，原版那台伸出之后
   **FRV 炮手位上那台也跟着往上抬**了；
2. 更进一步：**只要把火箭哨戒战备带在身上（不必叫出来）**，FRV 炮手位上那台就**不再卡进车体**、
   高度正常 —— 也就是说**不需要 `unit` 位移补丁**。

⇒ 结论：挂载件的状态机一直是对的，缺的只是**这段动画所在的包没被加载**。
"带着战备"之所以有效，是因为战备行原生就声明了这个包（`+0xA8` / `+0xF8`），包一加载，动画就能播。

**推论（用户提出，最省事的解释）**：那台挂载件的状态机**一直停在"要播部署动画"的位置**，
只是**动画 clip 的数据没被加载**（所以此前"压根没动"）；原版哨戒一出生，把同一套动画资源带进内存，
挂载件那边的状态就能播了 ⇒ 抬起来。

**为什么"资源在补丁里"却不等于"动画可用"**：`.patch_N` 只保证**按 `file_id` 可解析**（§3.8.4.6 已验证
mesh/material/texture 都行）；但**动画播放器/包级注册**可能仍以**整个包被加载**为前提——
也就是仍然要走 `+0xA8` 声明那条路（`[资源层驻留](../engine/RESOURCE-RESIDENCY-26088801.md)` §7 的边界：
补丁解决"资源在不在"，不解决"包在不在"）。`AC-8` 当初动画正常，正是因为它是**带 `+0xA8` 声明**挂上去的。

**对照测试矩阵（用户将做，单变量）**

| # | 配置 | 预期 | 说明 |
|---|---|---|---|
| A | 无位移 + **不叫**原版 | 不抬（沉/原样） | 复现"压根没动" |
| B | 无位移 + **叫**原版 | 跟着抬 | 已观察到，等于"动画随包载入"|
| C | **`+0xA8` 声明包**（已备好，未装） | **出生就抬** | 若 B 成立，C 应当不需要"外援" |

**盘上当前状态（C3：包走声明口、修正走补丁；2026-10-26 11:3x 已装）**

| 项 | 值 |
|---|---|
| `data/9ba626afa44a3aa3.patch_9`（4,560 B） | 只含 1 条 `state_machine 37079568DC86E9C6`：`layer0=3`（展开态）+ `layer5=1`（空态，关自转）|
| `generated_stratagem_settings.dl_bin` | `dae271681b372bbb`，行 57 `+0xA8` = **`11BBDF8CE39E5FC5`（声明火箭哨戒包）**，行 59 = 0 |
| `generated_entities.dl_bin` | `2a5ce9ba6b699792`（FRV 炮手位 = 火箭哨戒，`Behavior 658`）|
| ~~`f6fb08cc02d24255.patch_1`~~ | **已删除**（原 41 条整包驻留，1.26 MB toc + 4.37 MB gpu + 2.29 MB stream ≈ **7.9 MB**）|
| 补丁序号 | `9ba…patch_0..9` 连续；`f6fb…patch_0`（Warp 包，另一条实验）不动 |

⇒ 这就是 AC-8 当初的形态：**声明口负责让包（连带动画）被加载，补丁只负责改资源**。

**✓✓ 实机（C3）**：不叫原版、不靠肉身带战备，炮手位上那台**位置正确、不卡车体、不自转** —— 「包走 `+0xA8` 声明 + 修正走补丁」这套配方成立。

**E-R（`✓✓` 实机）**：把同一 41 条整包改走**注册表包**（`9ba626afa44a3aa3.patch_10`，7.6 MB）、战备表**零声明**、`patch_9` 保留补位 —— **结果与 C3 一样（位置正确、不卡车体、不自转）**。
⇒ 关键校正：**动画可以用补丁**，但**宿主必须是注册表包**；挂共享基础包时只有动画不播（P4 与 E-R 的补丁 toc 逐字节相同，唯一差别是宿主）。详见 [资源层驻留 §7.1](../engine/RESOURCE-RESIDENCY-26088801.md)。

**已备好、未安装的 C 变体**：`D:/mod/out/sm-verify/strat_declare_rocket.sealed.dl_bin`
（sha256 `dae271681b372bbb`，行 57 `+0xA8` = `11BBDF8CE39E5FC5`，行 59 仍为 0）。
装它：拷成 `data/game/generated_stratagem_settings.dl_bin` 即可（其余不动）。

#### 3.8.4.10 缺的就是这一条：火箭壳的 11 条 clip 清单与所在包（✓ 离线）

**"伸出"那条 = `0x86A54B9AA49F833A`**（layer0 的**部署态 s0** 绑的就是它）：0.98 s，
关键帧 `elevator_01×30`、`elevator_02×1`、`boss×20`、`sensor×9` —— 升降 + 座圈一起抬，就是"伸出来"。

整个壳的 11 条动画（`animation_probe` 数出来的打到哪些骨骼）：

| clip | 时长 | 谁用 | 打了哪些骨骼 | 作用 |
|---|---:|---|---|---|
| **`86A54B9AA49F833A`** | 0.98 s | **layer0 部署态 s0** | `elevator_01×30` `elevator_02×1` `boss×20` `sensor×9` | **伸出 / 抬升** |
| `9EAFCC13AEDC8BCF` | 1.00 s | layer0 收起态 s2 | `elevator_01×20` `elevator_02×6` `boss×21` `sensor×23` | 收回 |
| `72E968DE308896C3` | 0.08 s | layer0 折叠态 s1 | **无**（空壳） | 占位 |
| `3FCF5875B0663A62` | 0.17 s | layer0 展开态 s3 | **无**（空壳） | 占位 |
| `1D39879F1BE5A80C` | 23.33 s | layer5（已改空态） | `traverse×84` `elevator_01×76` `elevator_02×26` `covers×1` | **扫视循环（自转来源）** |
| `5A5489E30FF77626` | 1.00 s | layer1 `Time` | `traverse×15` | 偏航微动 |
| `991F5044858FC88B` | 1.00 s | layer2 `Time` | `elevator_01×7` | 升降微动 |
| `DA842CCEBCBC1FDE` | 0.15 s | layer3 开火 | `traverse×4` `elevator_01×2` `elevator_02×5` `covers×1` | 后坐 |
| `4725638CB8084FA4` | 2.00 s | layer4 装填 | `elevator_01×54` `elevator_02×18` `reload_cylinders×29` … | 装填 |
| `65D13D727736FC23` | 0.50 s | layer7 弹头 | `elevator_01×15` … | 弹头巢装填 |
| `DE7DF3B6B4CCBE3A` | 1.00 s | layer6 | `sensor×15` | 雷达盘转动 |

**它们只存在于 2 个包**（`srkit list --id` 全库扫，每条约 2 处、字节相同）：

| 包 | 是什么 | 覆盖 |
|---|---|---|
| `11bbdf8ce39e5fc5` | **火箭哨戒自己的 `LoadoutPackage`**（41 条资源）| 这 11 条全有 ⇒ **"带着战备"加载的就是它** |
| `fc5b6bff0db90aab` | **共享·空投舱炮塔包**（3,737 条：839 animation / 463 unit / 46 state_machine …）| 火箭 11/11、MG-43 9/9、加特林 12/12、迫击炮 8/8；**不含**火焰 / 激光 / AC-8 的动画（各在自己的包里）|

⇒ 所以"缺的动画"不是丢了一个文件，而是**读取它的包没在**：
我们 `f6fb08cc02d24255.patch_1` 里明明放了**同样 11 条**（字节相同），但动画播放器不认补丁里的副本
—— 这与 [资源层驻留](../engine/RESOURCE-RESIDENCY-26088801.md) §7 的边界一致，并且**把边界细化了一步**：
`.patch_N` 能让 **mesh / material / texture** 被解析，但**动画子系统要求包级加载**。

**判读要点**：A 不抬、B 抬 ⇒ 结论 = 缺的不是状态机也不是位移，而是**动画资源/包的加载时机**；
之后正式配方应改成"`+0xA8` 声明包（或别的让包真加载的手段）"，`unit` 位移只作为备选兜底。
若 A 也抬了，则说明另有触发源（例如战备投放是**全局广播事件**），要回到事件层查。

**模板 B 的待办（⚠ 未验，别照抄）**：MG-43/加特林默认 `E954AED4`（loop=1），部署过渡 `79DE1870`
播完**没有**回指状态（事件表里没有 `Deployed` 那条 Link），所以它停在部署 clip 的末帧；
迫击炮则显式走 `Deployed → s3（69484BEF，loop=1）`。
若模板 B 也停在"折叠"，可试：**MG-43 默认 `0→1`、加特林 `0→1`、迫击炮 `0→3`**（建议单开 `patch_9`，
一局验一件）。⚠ 这两个状态 loop=0，出场会先播一遍"伸展"再定住，观感可能与模板 A 不同。

**剩下的**：
① 模板 B 三个（上面 ⚠）；
② `EmitEndEvent` 里 `0xE62AFEFC` 仍未解析（没有语料命中）；
③ 部署流程（战备投放）也会发 `PackageDeploy` ⇒ 改默认态后，**战备投放**的同一型哨戒可能先以展开形态出现
再播一遍伸展动画（无害但可能有一瞬抖动，未专门验）。

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
