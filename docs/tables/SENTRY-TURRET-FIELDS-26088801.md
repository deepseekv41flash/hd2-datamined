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
# ③ 包：战备行 +0xA8 写 0x154BD6143819DF7D（或按 LIMITED-CROSS-PACKAGE §6.9 用补丁塞进常驻包）
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

#### 3.8.4.3 已打补丁：模板 A 的另外三个（⚠ 待实机）

| 文件 | 大小 | entry | 改动 |
|---|---:|---|---|
| `data/9ba626afa44a3aa3.patch_8` | 8,976 B | `state_machine 37079568DC86E9C6`（火箭） | layer0 `1 → 3`（`330CA356` → `823905BD`） |
| 同上 | | `state_machine 820CC3BAFE962858`（火焰） | layer0 `1 → 3` |
| 同上 | | `state_machine 56070F36CFFFA8A8`（激光） | layer0 `3 → 1` |

产物 `D:\mod\out\sm-patch8\`（spec.json + 3 个载荷），补丁序号 `patch_0..8` 连续。

**本局验证配置**（`D:\mod\out\sm-verify\`，已装，盘上回读逐字节一致）：

| 文件 | sha256 | 改动 |
|---|---|---|
| `generated_entities.dl_bin` | **`2a5ce9ba6b699792`** | FRV 炮手位（行 19/119 槽 0）= **A/MLS-4X 火箭哨戒** `37079568DC86E9C6`（顶掉 AC-8）；`Behavior 611→658` |
| `generated_stratagem_settings.dl_bin` | `0958505e34d4e14b` | 行 57/59 `+0xA8` = `11BBDF8CE39E5FC5`（火箭哨戒包） |

⇒ 一局：**火箭哨戒在炮手位上应该像 AC-8 那样"出场即展开、原点/炮口都对"**。
回滚到 AC-8 版：把 `D:\mod\out\frv-ac8\ent.sealed.dl_bin`（`02b740fef30a7f7a`）
与 `…\strat.sealed.dl_bin`（`081e7879cb6575e2`）拷回 `data/game/` 即可（`patch_7/8` 保持不动）。

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
