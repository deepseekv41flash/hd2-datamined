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

> ⚠ **本节是火箭/AC-8 时期的历史配置**。盘上现在跑的是 **MG-43 模板 B**（`f6fb08cc02d24255.patch_1`
> 已被重建为 MG-43 整包 61 条），**当前配置见 §3.8.4.12**。

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

#### 3.8.4.9 ✓✓ 实机（三轮复测后）：火箭"卡车体 + 自转"都是一个原因 —— `layer5` 的 23 s 扫视 clip

**最终结论**（2026-10-26 12:0x，E-S 收口）：

| 变量 | 观测 |
|---|---|
| `layer5` = **扫视 clip（23.33 s，`traverse` 84 键 / `elevator_01` 76 键 / `elevator_02` 26 键）** | 整机被摆到**收拢位**（沉进车体 ~2 m）＋ 没人操作时**自己左右转** |
| `layer5` = **空态（`DefaultState=1`）** ＋ `layer0=3`（展开态） | **位置正确、不卡车体、不自转** |

⇒ 修法就是**改 `layer5` 的默认态**：

```bash
python tools/state_machine_edit.py --set 0=3 --set 5=1 --out sm_rocket.bin sm.bin
```

**三条被否证的弯路**（都记录在案）：

| 曾经的推断 | 怎么被否掉的 |
|---|---|
| "默认态改成**部署态**（`layer0=0`）就会播一次伸出" | ⚠ 实机"压根没动"（当时 `layer5` 还在扫视，把它按住了）|
| "动画没加载，必须**带战备/声明包**（`+0xA8`）才播" | `✗` **E-R**（注册表宿主、零声明）正常，**E-S**（共享基础包宿主、零声明）也正常 |
| "换宿主包能修好" | `✗` **E-S**：同一份字节（toc `eb2bfca7c5408a47`）换回共享基础包宿主，照样正常 |

> 教训：P4 那次"沉"同时动了 `layer5`、宿主、声明三件事，逐个拆开花了四轮。

**当前盘上（火焰版，2026-10-26 12:1x 已装）**：
`f6fb08cc02d24255.patch_1` = **火焰哨戒包 32 条整包**（toc `e726fef4570074d6` / gpu `a7da4fb6d73d2b80` / stream `1ec72c7554c99aaf`），
内含改好的 `state_machine 820CC3BAFE962858`（`layer0=3` 展开态、`layer3=1` 空态）；
`9ba626afa44a3aa3.patch_0..9`（`patch_8` 里的火焰 SM 与整包内那条同字节）；
战备表零声明 `6c0ab66b281c2178`；
`generated_entities.dl_bin` = **`bdd110d62a2387b8`**（sealed）—— M-102 炮手位 = **A/FLAM-40 火焰哨戒**，`Behavior 208→658`。

#### 3.8.4.12 模板 B（MG-43 / 加特林 / 迫击炮）：光关"扫视层"不够，`layer0` 必须钉到**部署过渡态**（2026-10-26 13:1x，✓✓ 实机 13:2x）

**✓✓ 结果（2026-10-26 13:2x 局）**：`layer0 0→1` + `layer5 0→1` 装上后，A/MG-43 哨戒在 M-102 炮手位
**出场就展开**（`layer0` 停在部署过渡末帧这一行为被实机证实）。
⇒ 模板 B 的判据闭环：**"`loop=0` 且无出口的状态，引擎会把末帧保持住"** ——这是本条最重要的新事实，
它让"没有展开态的状态机"也能被挂载（之前只有"有展开态"的那几种能用）。

**第一轮实机否证**（2026-10-26 13:0x）：只把 `layer5` 关掉、`layer0` 留在原版 `0`（`E954AED4`），
MG-43 挂上炮手位后 **模型出现、但未展开**（既不沉也不自转）。
⇒ 「模板 B 的 bind 位就是展开位，所以 `layer0` 不用动」这个类比**是错的**。

**为什么**：把 `layer0` 三个状态连起来读（`--decode`）就清楚了——

| state | 名字 | loop | 绑的 clip | 语义 |
|---:|---|---:|---|---|
| s0 | `E954AED4`（idle） | 1 | `385AC26B` 0.17 s，**0 根骨骼（空 clip）** | **部署前 idle**：空 clip ⇒ 显示 bind 位 = **折叠** |
| s1 | `79DE1870`（部署过渡） | **0** | `31170087` 0.98 s（`root×14` `rotator×14` `gunhousing×15` `sensorpod×9`） | **这一段就是"从折叠到展开"的全过程** |
| s2 | `D23167BF`（收起） | 0 | `F990C128` 2.48 s（`root×34` `rotator×16` `gunhousing×21` `sensorpod×23`） | 收起 |

s0 的出口只有 `0x72C4271D PackageDeploy`→s1、`0x6F8B215F PackageRetract`→s2；
而 **s1 自己没有任何"再往前走"的过渡**（只在 retract 时去 s2）⇒ 原版一旦部署完成，
`layer0` 就**永久停在 s1 的末帧**。⇒ **模板 B 的展开姿势 = 部署过渡 clip 的末帧**
（引擎对 `loop=0` 且无出口的状态，就是把最后一帧保持住）。
这也解释了为什么模板 B **没有"展开态"这一档**——它不需要。

⇒ **模板 B 的修法 = `layer0.DefaultState 0→1`（钉到部署过渡态）+ 关掉扫视层 `layer5`。**
副作用反而是加分项：出生时真的播一次 0.98 s 的展开动画；s1 的 `EmitEndEvent=0x247452BF Deployed`
会把 `layer3/layer4`（`rotator`/`gunhousing` 的部署后循环）拉起来——与原版部署完成后完全一样。

**已装（第三轮，`⚠` 单变量：撤掉 11 MB 整包，只留 4 KB 同包）**：

| 文件 | sha256 | 内容 |
|---|---|---|
| `data/154bd6143819df7d.patch_0`（+ 空伴生） | `795d39714763f22d` | **同包补丁**：只有 `state_machine 37CDE43876BA26BB`（4,012 B）。同包 `patch_N` 是合并进那个包本身 ⇒ 同 id 必然覆盖 |
| ~~`data/f6fb08cc02d24255.patch_1`~~（+gpu/stream） | ~~`bfe487b98f4b6c11`~~ | **第二轮用的整包补丁，已撤到 `D:\mod\out\backup\mg43-patch1-v2\`**（先备份、未删）。撤它 = 单变量测"非启动包的补丁会不会被合并" |
| `data/game/generated_entities.dl_bin` | `d7c9838e7c01cad6` | M-102 炮手位（行 19/119 槽 0）= **A/MG-43 机枪哨戒** `37CDE43876BA26BB`，`Behavior 313→658` |
| `data/game/generated_stratagem_settings.dl_bin` | `6c0ab66b281c2178` | 零声明（未动） |

SM 字节级：`layer0.DefaultState @0x74 0→1`、`layer5.DefaultState @0xB4C 0→1`，其余 4,010 B 不变（`cmp` 只 2 处差异）。

> **第二轮为什么装两份**：MG-43 这个件**自己声明了包** `154bd6143819df7d`（`mount_table` 的 `declared=` 字段），
> 原包照常加载 ⇒ 同一份 SM 有"原包"和"补丁"两个提供者，谁赢当时没有实验数据；
> 第一轮"未展开"因此有两种解释（①改法错 ②改动没生效）。两份字节相同 ⇒ 无论谁赢结果一致，
> **第二轮实机"展开了"，先把姿势闭环了**。

**第三轮结果（2026-10-26 13:3x）：✗ 否证 —— 变成紫色问号（占位模型）**

撤掉 11 MB 整包、只留 4 KB 同包补丁后，炮手位上是**紫色问号**（引擎"资源缺失"占位），
不是"折叠"也不是"自转"。这个结果比预期更有信息量，一次答了两件事：

| 结论 | 依据 |
|---|---|
| **挂载路径不会去加载挂件自己声明的包** | 若 `154bd6143819df7d` 被加载，unit/mesh/贴图都在，至少能看见折叠的哨戒；现在连模型都没有 ⇒ 那个包**从头到尾就没被加载过** |
| **前两轮的模型 100% 来自 `f6fb08cc02d24255.patch_1`（整包驻留）** | 撤掉它 ⇒ 无模型；装回它 ⇒ 有模型（字节级回滚，`bfe487b98f4b6c11` 与"展开了"那局逐字节相同） |
| **`declared=` 字段只是"战备行的包声明"，不等于"这个件会把自己的包拉起来"** | `mount_table` 的 `declared=0x154BD6143819DF7D` 读的是该件的**战备行** `+0xA8`；只有**调用那条战备**时才会用到它 |
| **配方 D（同包 `patch_N`）对挂载件无效** | 包都不加载 ⇒ 它的 `patch_N` 也无从合并（那份 4 KB 补丁自始至终是空转） |

⇒ **挂载外来件必须走整包驻留**（[资源层驻留](../engine/RESOURCE-RESIDENCY-26088801.md) 配方 C）。
这不是"优化没做成"，而是把"为什么本来就要驻留"这条因果链彻底钉死了。

**另一个新事实（`✓` 离线）**：巨型共享包 `fc5b6bff0db90aab`（3,737 条 / toc 92 MB / gpu 525 MB / stream 930 MB，
含 46 个 `state_machine`、463 个 `unit`）里**有各哨戒壳的 `bones` + `state_machine`，但没有任何哨戒的 `unit`**
⇒ 姿态数据本来就在常驻包里，**缺的永远是 `unit`（以及它引用的 mesh/材质/贴图）**，所以驻留省不掉。

**四、候选件怎么挑（`✓` 离线，以后照抄）**：一个壳往往对应**多个件变体**（G-16 有 6 个），
只有**战备表真的引用**的那个才是"游戏里能拿到的那台"——
在 `generated_stratagem_settings.dl_bin` 明文里搜 item id（u64 LE），命中者入选：

| 件 | Behavior | 战备表命中 |
|---|---:|---|
| `0x37CDE43876BA26BB`（MG-43） | 313 | ✓ `@0x11ff8` |
| `0xEF85D6CF58E31D70`（G-16） | 214 | ✓ `@0x12080` |
| `0x04C99523A808EF90` / `0x57F27CBD5B71B0CB` / `0x68A34D32A1025F04` / `0x7FF0FD4572F5996F` / `0x87F46B6D12BB016A` | 680/687/214/603/685 | ✗ 未命中（变体/未启用） |


**三台模板 B 的逐台配方**（同一套判据；另两台已量好、**未安装**）：

| 哨戒 | SM | 层数 | 有没有独立"展开态" | `layer0` 设几 | 扫视层（要关） | 其余 |
|---|---|---:|---|---|---|---|
| A/MG-43 机枪哨戒 | `37CDE43876BA26BB` | 7 | **没有**（3 态） | **1**（部署过渡） | **L5** `1383C954` 21.33 s（`rotator×83` `gunhousing×65`） | L6 = 雷达 `14D268AC`（`sensorpod×15`），默认 0，无害 |
| A/G-16 加特林哨戒 | `61D9DDA22A59E9BC` | 8 | **没有**（3 态，s1 的 `EmitEndEvent=0x247452BF`） | **1** | **L6** `3CEBEDCD`（state 名同为 `0x9EA750D5873EB183`） | L7 = 雷达 `5547DDA5`；L1 有 5 态（部署/开火/装填），默认 4=`Empty` |
| A/M-12/EMS/毒气迫击炮 | `51A0812E3BCE2D74` | 7 | **有**：s3 `69484BEF`（loop=1，clip `746AA4BC` **0 骨骼**） | **3** | **L5** `732657A5` 21.67 s（`base_elevation_arm×100` `traverse×76` `elevator_rotator×65`） | L1/L3 = `Time` 循环（`traverse`/`elevation`），默认已是 `Empty` |

**判据固化**（以后任何新哨戒壳照这个走，不用再猜）：
1. `--decode` 找 **state 名 `0x9EA750D5873EB183`** 的那一层 ⇒ 那是**部署前 idle / 扫视层**，把它的 `DefaultState` 改成同层那个 `Empty`（`0x86342D70`）的索引；
2. 看 `layer0` 里有没有 **`loop=1` 且被 `EmitEndEvent` 指到**的"展开态"：
   有 ⇒ `layer0` 设成它（火箭/火焰/迫击炮/AC-8）；**没有** ⇒ 设成**部署过渡态**（模板 B）；
3. 顺手用 `animation_probe --matrix` 复核：部署过渡 clip 应该同时打 `root/rotator/gunhousing`（或 `elevator_*`）——
   如果它一根骨骼都不打，那就是真·占位，得另找。

#### 3.8.4.13 第三台：A/G-16 加特林（2026-10-26 13:4x，✓✓ 实机）

**✓✓ 结果（2026-10-26 13:4x 局）**：四条全过 —— 炮手位**出加特林**、**出场即展开**、**能瞄准/开火**、**不自转**。
两个附带结论也钉死了：
1. **46 条驻留足够**：件列表里那 6 个"变体包"（`fc5b6bff0db90aab` / `992d325d88de5fbf` / `86565de78333128f`
   / `3b2c86dd5b316eb2` / `09985dc611a3a8b6` / `4ff64273030e87d6`）是同一套 shell 的冗余副本，
   只要驻留其中一个就够，**不会在我们之后加载把 SM 盖回去**；
2. **"钉部署过渡态"对 8 层机器同样成立**（模板 B 判据跨层数有效）。

按上面三条判据一条命令量完，**与 MG-43 同型（模板 B、无展开态）**：

| 项 | 值 |
|---|---|
| SM | `61D9DDA22A59E9BC`（5,724 B，8 层）|
| 改动 | `layer0.DefaultState 0→1`（部署过渡 s1 `79DE1870`，`EmitEndEvent=0x247452BF`）+ `layer6.DefaultState 0→1`（关扫视层，state 名同为 `0x9EA750D5873EB183`，clip `3CEBEDCD`）|
| 字节级 | 5,724 B 里只变 2 处（`@0x7C`、`@0x10B4`）|
| 件 | **`0xEF85D6CF58E31D70`**（战备表 `@0x12080` 引用的那个 Gatling Sentry；其他 5 个变体战备表里没有）|
| 五件套 | Turret ✓ Wieldable ✓ WeaponWielder ✓ ProjectileWeapon ✓（另有 AI 索敌三件套——MG-43 也有，被 `Behavior 658` 压住）|
| unit | `content/fac_helldivers/hellpod/turret/turret`（10,928 B + gpu 3.3 MB），bones=6 |
| Behavior | `214 → 658`（块 `0xBA9B803D` 行 629）|

**已装**：

| 文件 | sha256 | 内容 |
|---|---|---|
| `data/f6fb08cc02d24255.patch_2`（+gpu/stream） | `1939a1ddcbad2d2c` / `59cb602b1a977645` / `79ed8ffdfbdf6ee8` | **G-16 包 `4ff64273030e87d6` 整包 46 条**驻留（toc 1.52 MB + gpu 5.63 MB + stream 2.05 MB），SM 为上面那版 |
| `data/game/generated_entities.dl_bin` | `548af458629a2263` | M-102 炮手位（行 19 槽 0）= **Gatling Sentry** `0xEF85D6CF58E31D70`；`Behavior 214→658`。行 119（另一台 FRV 变体）仍是 AC-8，未动 |
| `data/f6fb08cc02d24255.patch_1`（MG-43 驻留 11 MB） | `bfe487b98f4b6c11` | **保留**：不是还要 MG-43，而是补丁序号必须连续（`patch_0,1,2`），删了 `patch_1` 会让 `patch_2` 被静默忽略 |

#### 3.8.4.14 第四台：A/M-12 迫击炮（2026-10-26 14:0x，✓✓ 实机，含特效）

**✓✓ 结果**：本体出场、**展开态正确**（`layer0=3` 这条"有展开态但 clip 为空 ⇒ 靠 bind 位"的判断成立）、
不自转、能瞄准开火。**唯一遗留 = 开火后的灰色方块占位体**（见 §3.8.4.15，已按特效资源补 `patch_4`）。

**这台不是模板 B，而是"模板 A 的形状"**（有独立展开态）——正好用来交叉验证判据第 2 条：

| 项 | 值 |
|---|---|
| SM | `51A0812E3BCE2D74`（4,276 B，7 层；gas / EMS / M-12 三个变体**共用同一份 SM**）|
| `layer0` | **`0 → 3`**，落到 `0x69484BEF5AC55426`（部署完成态，`loop=1`，clip `746AA4BC` **0 骨骼** ⇒ 靠 bind 位）|
| 扫视层 | **`layer5 0→1`**（`732657A5` 21.67 s：`base_elevation_arm×100` `traverse×76` `elevator_rotator×65`）|
| 字节级 | 4,276 B 只变 2 处（`@0x74`、`@0xB8C`）|
| 件 | `0x51A0812E3BCE2D74`（战备表 `@0x12100`；另两个变体 gas `@0x121e8` / EMS `@0x121a8` 也都在表里）|
| unit | `ar_turret/mortar_turret`（17,040 B + gpu 2.83 MB），7 个 mesh、8 根骨骼 |
| 射界 | pitch **35…89**（只能打高抛）、yaw ±180 —— `Turret` 行 55 |
| Behavior | `320 → 658`（块 `0xBA9B803D` 行 620）|

**已装**：

| 文件 | sha256 | 内容 |
|---|---|---|
| `data/f6fb08cc02d24255.patch_3`（+gpu/stream） | `46eb123a9deff307` / `219015704b647a5f` / `9003e7fa4d448aaf` | 迫击炮包 `a5a7e8288c7a478c` **整包 226 条**驻留（toc 1.26 MB + **gpu 12.7 MB** + **stream 53.6 MB**，三变体共用 ⇒ 是目前最重的补丁） |
| `data/game/generated_entities.dl_bin` | `215fbc1ae138a596` | M-102 炮手位（行 19 槽 0）= **Mortar Sentry** `0x51A0812E3BCE2D74`；`Behavior 320→658` |

> 注意：迫击炮包里有 **3 个 `state_machine`**（`4B33E6DB` gas / `51A0812E` M-12 / `9A61CD93` EMS），
> 列补丁条目时别按"第一个 state_machine"取（第一次就取错到 `4B33E6DB`），要**按 id 选**。

**这一局要看的**：
1. 出不出迫击炮（unit `ar_turret/mortar_turret`，7 个 mesh）；
2. **是不是展开态**——这是本批第一台"有独立展开态但 clip 为空"的壳，若**折叠/沉**，
   说明它的 bind 位是收拢位（火焰 §3.8.4.11 里留的同一个备份手：改成 `layer0=0`，让部署 clip 末帧定格）；
3. 不自转（`layer5` 关对了）；4. 能瞄准开火（pitch 只能 35…89，打高抛是正常的）。

#### 3.8.4.15 开火后的"灰色半透明方块" = 特效资源缺失的占位体（2026-10-26 14:0x，✓✓ 已修）

**现象**：迫击炮装好后本体/展开/瞄准/开火都正常，但**每次开火后炮位附近出现灰色半透明方块**。

**判读**：那是引擎画不出某个特效资源时的**占位图元**（和"紫色问号"是同一族现象，只是一个作用在模型、一个作用在特效）。
不是伤害/弹道问题，也不是状态机问题——**纯粹是资源没被解析到**。

**根因**（和 §3.8.4.12 的紫问号同一条链，只是层次更深一层）：

| 层 | 状态 |
|---|---|
| 模型（unit/mesh/材质/贴图） | 靠**整包驻留**补上了（`patch_3` = 包 `a5a7e8288c7a478c` 226 条）|
| **特效（particle / 它引用的 material+texture）** | **没有**：这些引用由实体的 `EffectReferenceComponentData` / `HitEffectComponentData` 持有，而它们指向的粒子**散落在多个包里**，挂载路径一个都不加载 |
| 结果 | 引擎解析不到 ⇒ 在特效的生成点画占位方块（灰色半透明）|

**离线证据**（`✓`）：把两个包的粒子 id 集合对出来，**完全不重叠**：

| 包 | 粒子数 | 说明 |
|---|---:|---|
| `a5a7e8288c7a478c`（我们驻留的） | 22 | 与另一包**零交集** |
| `8c5a99a9a40d5b8d`（M-12 件声明 `declared=` 的） | 10 | 其中 5 个 id 能在 `generated_entities` 明文里搜到 ⇒ 确实被实体引用 |

**为什么 MG-43 / G-16 没暴露**：它们各自包里带的 7 个粒子里，恰好包含几个**跨包共用**的通用特效
（例如 `0x68AC97CEA9D1E961`、`0xABE4078E2C548590` 这两个 id 在 MG-43 包里也有）⇒ 它们的开火特效被"顺带"补上了。
迫击炮用的是**自己变体独有**的粒子/材质，所以缺。

**已装（`⚠` 待验证）**：`data/f6fb08cc02d24255.patch_4` = 包 `8c5a99a9a40d5b8d` **整包 33 条**
（toc `22e76e7ba8667fa0` 4.59 MB / gpu `bf64a29695e62891` 4.24 MB / stream `9b6db0e41bd23218` 2.80 MB）——
10 particles + 8 animation + 6 texture + 3 material + 1 mesh + 1 bones + 1 SM + 1 physics。
选择依据：M-12 件 ***自己声明*的那个包**，且它的 SM/动画与 M-12 壳一一对应。

> ⚠ **装它的时候踩了"高号胜"的反噬（已修）**：这个包里**也有一份同 id 的原版 SM `51A0812E`**，
> 而 `patch_4` 序号高于 `patch_3` ⇒ 第一版 `patch_4`（toc `540867ad03ed00ac`）一装上去，
> 迫击炮就从展开态退回**折叠态**（特效补丁本身没问题，是它顺带把 SM 顶回原版了）。
> 修法：重建 `patch_4` 时**把改后的 SM 一起塞进去**（`--edit state_machine:51A0812E=<mortar-sm.bin>`），
> 现在 `patch_3`（entry 50）和 `patch_4`（entry 11）里那份 SM **逐字节都是改后版本**。
> 规则记进 [资源层驻留](../engine/RESOURCE-RESIDENCY-26088801.md) §8 第 9 条：
> **每一份驻留补丁都必须自带它覆盖到的所有改后字节。**

**如果还冒方块**，下一步（按成本）：
1. 再补另两个 M-12 同壳变体包（`4666692b63185121` / `71d9ea5d656b09b8`，各 ~7 MB，粒子集不同）；
2. 精确定位：读该实体的 `EffectReferenceComponentData` / `HitEffectComponentData` **组件行**，把里面引用的粒子 id 全列出来，
   再按 id 反查"在哪个包"逐个补（需要一个"组件行 → 引用 id 列表"的小工具，现在还没有）；
3. 兜底：把 item `LoadoutPackageComponentData` 列的 8 个包全驻留（迫击炮约 150 MB 起，不推荐）。

**结论（给成品 mod 的教训）**：**"模型对 ≠ 特效对"**。挂载外来件时，除了模型资源，
还要保证**它开火/命中特效引用的粒子 + 粒子引用的材质贴图**也在常驻包里；
以后做 `sentry_mount.py` 时，这一步要作为独立门禁（而不是等实机看到方块再补）。

#### 3.8.4.16 第五台：A/LAS-98 激光（2026-10-26 14:1x，⚠ 待实机）

**这是九台里最省的一台**：`layer0` 只需一次 `3→1`，没有扫视层要关，也没有"展开态没 clip"的坑。

| 层 | 默认态 | 说明 |
|---|---:|---|
| **L0** | **3 → 1** | s3 `330CA356`（折叠）/ **s1 `823905BD`（展开，clip `88F2CCF2` 0 骨骼 ⇒ bind 位）**；s0 `79DE1870`（部署过渡，`EmitEndEvent=0x3D0B77D2 DeployDone` → s1）链路完整 |
| L1 | 0 | 单态 `Time` 循环（`71134B79`），前后都有，无需动 |
| L2 | 0 | 单态 `Time` 循环（`1ACD80C0`），同上 |
| L3 | 1 | **默认就是部署后那一档**（`5547DDA5`，clip `B172C4EC`）；`PackageDeploy/Retract` 时才临时去 `Empty` ⇒ 不用动 |

**判据第 2 条在这里再验一次**：激光**有**独立展开态，选它（`1`），不是选折叠（`3`）。

**一个巧合值得记**：盘上 `9ba626afa44a3aa3.patch_8` 里那份激光 SM 是**上一轮凭猜测**写的 `layer0 3→1`，
这次按判据独立算出来**逐字节相同**（`cmp` 通过）⇒ 两处提供者（启动包补丁 / 驻留补丁）内容一致，
不会重演 §3.8.4.15 那个"高号把改后版本顶回原版"的事故。

**已装**：

| 文件 | sha256 | 内容 |
|---|---|---|
| `data/f6fb08cc02d24255.patch_5`（+gpu/stream） | `9a62e0792d66cb2b` / `efb14d71075da49e` / `f8424ed97ea3bd11` | 激光包 `36313bf684c1fd79` **整包 42 条**驻留（toc 5.77 MB + gpu 5.79 MB + stream 3.32 MB：11 texture / 8 particles / 8 material / 7 animation / 1 unit / 1 bones / 1 physics / 1 SM + wwise）|
| `data/game/generated_entities.dl_bin` | `ef5b304848305174` | M-102 炮手位（行 19 槽 0）= **Laser Sentry** `0x56070F36CFFFA8A8`；`Behavior 309→658` |
| `9ba626afa44a3aa3.patch_8`（启动包，原有） | 不动 | 里面那份激光 SM 与 `patch_5` 的逐字节相同，留着无妨 |

> 激光是**唯一一个 `pkg=` 只有一个包**的哨戒（`36313bf684c1fd79`）——没有变体副本、没有共享包依赖，
> 所以它是"最小驻留"的样板：**驻留一个包 = 全部齐活**（8 个 particle 也在里面，理论上不会重演灰色方块）。
> 五件套里 `ProjectileWeapon=False`（它是 `BeamWeapon`，见 §3 的判据说明），但 `Turret/Wieldable/WeaponWielder` 齐 ⇒ 可挂。

**这一局要看的**：① 出不出激光哨戒；② 展开态；③ 不自转；④ 能瞄准开火（**光束特效正不正常**——重点看有没有灰方块/缺光束）。

#### 3.8.4.17 人操工事（E/MG-101 HMG、E/AT-12 AT）：**不是同一类挂载件**（2026-10-26 14:2x，⚠ HMG 待实机）

十二个哨戒都是"AI 炮塔"，而这两台是**玩家手动操作**的工事。组件层一看就不是一类（`refs/entity-components.json`，`✓` 离线）：

| 组件 | 哨戒（MG-43） | **工事（HMG-101 / AT-12）** | 含义 |
|---|:--:|:--:|---|
| `TurretComponentData` | ✅ | **❌ 没有** | 炮塔轴（yaw/pitch + 限位）—— 车位的瞄准逻辑靠它驱动 |
| `Wieldable` / `WeaponWielder` / `WeaponData` / `ProjectileWeapon` | ✅ | ✅ | 可被"持握者"操作 ⇒ 挂载槽要的就是这几件 |
| `SeatCollectionComponentData` | ❌ | **✅** | **自己带一个座位**（玩家按 E 坐进去操作）|
| `InteractableComponentData` | ❌ | **✅** | 交互提示 |
| `SensorEye` / `Detector` | ✅ | ❌ | AI 索敌（所以它们"没有 AIBEH"）|
| `Behavior` | ✅ | ✅ | 工事的是"玩家操作"行为（HMG=314、AT=**2**），不是 AI 行为 |
| unit dev 路径 | `…/turret_machinegun_gpmg` | **`…/hellpod/manned_turret/manned_turret`** | "**人操**炮塔" |

⇒ **两类件的控制模型不同**：
- **哨戒** = "可被挂的炮"：本身没有座位，挂到车上后由**车位的 Turret 逻辑**接管瞄准（所以我们只要 `Behavior 658` + 展开即可）；
- **工事** = "自带座位的固定武器"：瞄准轴来自**它自己的 `SeatCollection`**，玩家坐进去才转。

**对"能不能装到载具上"的离线预测**：**能挂上**（`Wieldable`/`WeaponWielder`/`WeaponData`/`ProjectileWeapon` 齐全，挂载槽不检查 `Turret`），
**但枪身大概率不跟车位准星转**（缺 `Turret` 轴），甚至可能因 `SeatCollection` 与车位冲突而无法操作。只能实机判。

**HMG 工事（已装，`⚠` 待实机）**：

| 项 | 值 |
|---|---|
| SM | `0E977C49DB7604F9`（4,820 B，**6 层**）|
| 改动 | **`layer0.DefaultState 1 → 2`**：s1 `330CA356`（折叠，clip `1D22F5E3`）→ **s2 `823905BD`（展开，clip `C1B7AE53`）**；s0 部署过渡的 `EmitEndEvent=DeployDone` → s2，链路完整。4,820 B 只变 **1 字节** |
| 其余层 | L1 = 单态 `Time` 循环；L2 默认 `Empty`（s3 是 8-clip 的 `Blend`，事件触发）；L3/L4 默认 `Empty`（s0 是叠加的开火 clip）⇒ 都无需动 |
| 件 | **`0x0E977C49DB7604F9`**（战备表 `@0x480c`；另一变体 `0xA970CBA66FBEAA11` 表里没有）|
| 五件套读数 | `Turret=False` `Wieldable=True` `WeaponWielder=True` `ProjectileWeapon=True` `Faction=inherit` **`AI大脑=False`** |
| 驻留 | `data/f6fb08cc02d24255.patch_6` = 包 `68e80476c1c602f5` 整包 40 条（toc `4b4392b53d66fca2` 3.30 MB / gpu `4610b3aa33def739` 2.76 MB / stream `fa3b4b7390d81234` 1.79 MB）|
| entities | `d65b396dca9d96ef` —— 行 19 槽 0 = HMG Emplacement，`Behavior 314→658` |

**AT-12（已量未装）**：SM `2B11C9E4980EC479`（6,076 B）、包 `5a0f047f2695b403`（49 条，toc 3.58 MB / gpu 5.04 MB / stream 1.05 MB）、
件 `0x2B11C9E4980EC479`（战备表 `@0x4c04`）、`Behavior = 2`。等 HMG 的结论再决定要不要上。

**这一局要看的（四档判读）**：
1. **根本不出现** ⇒ 挂载槽不接受无 `Turret` 的件（`Turret` 是隐藏必要条件）；
2. **出现、展开、但枪身不转** ⇒ 证实"`Turret` = 车位瞄准轴"，工事只能当**固定炮**；
3. **出现、能转能打** ⇒ `Turret` 不是必要条件，之前"五件套"判据太严（好消息：工事也能上）；
4. **出现但无法操作（开不了火/抢不到控制权）** ⇒ `SeatCollection` 与车位冲突，得改它的座位/交互组件。

**它到底算哪一类？（2026-10-26 14:3x，`✓` 离线：三类对照）**

| 组件 | AI 炮塔（MG-43） | **人操工事（HMG/AT）** | 载具（FRV） |
|---|:--:|:--:|:--:|
| `TurretComponentData` | ✅ | ❌ | ❌ |
| `SeatCollectionComponentData` | ❌ | ✅（kind=**interactable**）| ✅（kind=**vehicle**）|
| `MountComponentData`（能当**宿主**）| ❌ | ❌ | ✅ |
| `VehicleComponentData` / `VehicleMotion` / `VehicleElectrics` / `VehicleCollisionDamage` | ❌ | ❌ | ✅ 四个全有 |
| `UnitCustomization` / `Buoyancy` / `GroundCheck` / `Trample` | ❌ | ❌ | ✅ |
| `RotationSoundPlayer`（有转动部件）| ❌ | **✅** | ❌ |
| `SensorEye` / `Detector`（AI 索敌）| ✅ | ❌ | ❌ |

⇒ **它是第三类**：既不是 AI 炮塔（无 `Turret`、无索敌、`AI大脑=False`），也不是载具（`Vehicle*` 四件套和 `MountComponentData` 一个都没有）。
唯一像载具的地方就是**一个可交互座位**（`SeatCollection` + `Interactable`）。它自带 `RotationSoundPlayer` ⇒ **确实有可转部件**，
但那个转动不是 `TurretComponentData` 给的，而是**座位上玩家的瞄准驱动骨骼**（同一套"人操"逻辑）。

**能不能往它身上挂别的东西？`✗` 数据层不行**，两条理由（第三条已作废，见下方更正）：
1. **不在 Mount 哈希图里**（`mount_table.py show --entity 0x0E977C49DB7604F9` ⇒ "没有挂载记录"；全表 165 条记录，56 条 SeatCollection 里有它、Mount 里没有）；
2. 载具的挂载能力是和 `VehicleComponentData` 那一套绑在一起的，工事整套都没有（`Vehicle*` 四件套 + `MountComponentData` 全缺）。

> **⚠ 更正（2026-10-26 14:3x）**：先前写的"它只有 5 根骨骼、没有挂点所以挂不上去"**是错的**，两处都错：
> ① 它的骨架其实是 **28 根**（`bones 0E977C49DB7604F9`：`traverse`、`weapon_pitch`、`weapon_swivel`、`weapon_hinge`、
> `r_barrel`/`l_barrel`（双枪管）、`attach_gunner`、`IK_left_turret`/`IK_right_turret`、脚蹬/弹药箱/抛壳盖…）；
> ② **挂载槽的锚点是"件侧"的**：`anchor_c = 600573527` 正好是原版 MG-206 的 `gun` 骨骼哈希
> （比对了 MG-206 的 12 根骨骼）。我们把槽里的件换成 MG-43/G-16/迫击炮/激光时**没改锚点**（仍是 MG-206 的 `gun`），
> 五台却全部正常 ⇒ **锚点不是"能不能用"的硬条件**，更不能拿它当"宿主没挂点"的证据。
> 结论部分不受影响（"不能当宿主"仍成立），但**理由只剩上面两条**。

**它的骨架完全能转——缺的只是"驱动者"（`✓` 离线，2026-10-26 14:3x）**：
`traverse`（yaw 轴，`551832871`）、`weapon_pitch`（pitch 轴，`4098057313`）、双 `r_barrel`/`l_barrel`、
`attach_gunner`（炮手锚点）、`IK_left_turret`/`IK_right_turret`（与 MG-206 同名同哈希 ⇒ 玩家手部 IK 同约定）。
⇒ 它"人操能转"靠的是**座位上玩家的瞄准驱动这些骨骼**（外加 `RotationSoundPlayer`），
而不是 `TurretComponentData`。所以挂到车上能否转，取决于**车位的 aim 声明能不能指到这几根骨骼**——这正好接上下面那张座位表的差异。

**座位记录：结构完全一样，内容差 4 组字段（2026-10-26 14:3x，`✓` 离线）**

`SeatCollectionComponentData` 只有一张表、行宽固定 **424 B**，工事和载具用的是同一套 schema：

| 行内偏移 | 字段 | 说明 |
|---|---|---|
| `+0` | `transition_id` u32 | 进座过渡动画 id |
| `+8 … +264` | 16 个乘客槽 × 16 B | `{u32 a, u32 b, u64 entity}`（预置乘员/座位占用）|
| `+264 … +272` | `flags` 8 B | 行为位图 |
| `+296` / `+300` | u32 ×2 | 未解 |
| `+308 … +396` | **`aim` 22 × u32** | 瞄准相关（见下）|
| `+396 … +418` | `tail_flags` 22 B | 未解 |

逐条对比（`mount_table.py seats` + 自定义 dump）：

| 记录 | kind | transition | flags | `aim` 非零 | 乘客槽 |
|---|---|---:|---|---:|---|
| `M-102 Gunner FRV`（row 8/46） | `vehicle` | 26 | `01111101` | **4** | 0 |
| `M-103 Supply FRV`（row 48） | `vehicle` | 27 | `01111101` | **4** | 0 |
| `M-104 Incinerator FRV`（row 47） | `vehicle` | 28 | `01111101` | **4** | 0 |
| `manned_turret`（row 39–42） | `interactable` | 32 | `00111000` | 0 | 0 |
| `HMG Emplacement`（row 37/38） | `interactable` | 32 | `00011000` | 0 | 0 |
| `Anti-Tank Emplacement`（row 33） | `interactable` | **1** | `00001000` | 0 | 0 |
| 对照 `Scout Strider`（row 5） | `vehicle` | 20 | `01011000` | 0 | 1（Trooper）|

**四条硬结论**：
1. **schema 相同、行宽相同、字段位置相同** ⇒ 工事的座位不是"另一种结构"，只是同一种结构的另一种填法；
2. `kind` 字段不同（`vehicle` vs `interactable`）——这决定了**进车**还是**按 E 坐上去**；
3. `transition_id` 是**每个座位自己的**入座过渡动画（三台 FRV 26/27/28 各不相同，HMG=32、AT-12=1）；
4. **`aim` 22×u32：全表 56 行里只有那 4 条 FRV 座位非零（恰好 4 个值），工事全零**，
   且三台 FRV 型号的 4 个值**完全相同**（`0xC734BAB7` / `0x04A36AB4` / `0x7CFDDD00` / `0x46868CEE`）
   ⇒ 这是**宿主侧**的引用，不是"挂件侧"的。
   已排除两种解释：**不是 FRV 骨架节点哈希**（FRV `unit` 193 个节点里没有），**也不是原版 MG-206 的骨骼哈希**（12 根里没有）
   ⇒ 更像瞄准/相机类预设的 u32 名字哈希（`⚠` 含义待定）。

⇒ 所以"工事在车上能不能转"的答案落在第 4 条上：**它的座位不声明任何 `aim`**，
车位的 4 个 aim 引用是给 FRV 自己那套炮手武器的；工事挂上去后**既没有 `TurretComponentData`，也没有座位 aim 指到它的 `traverse`/`weapon_pitch`**
⇒ 结构上预期**不转**（但仍可能出模型、能开火）。

**由此得到的下一步（若 HMG 实机"不转"）**：走**座位表**路线而不是挂载表——
把车位那一行的 `SeatCollection` 改成 `manned_turret` 那种（表里 row 39–42 就是它的四条记录，`kind=interactable`），
让车位的瞄准改由"人操"模式驱动；或者试着把 `aim` 的 4 个槽换成工事骨架上的轴骨骼
（`traverse = 551832871`、`weapon_pitch = 4098057313`、`attach_gunner = 3603131125`）——前提是先解出 `aim` 字段真正的语义。


**✓✓ 实机（2026-10-26 14:4x，HMG 工事挂 FRV 炮手位）——结论比预期好得多**

| 观察 | 结果 |
|---|---|
| 能不能挂上 | **能**（出现、展开、能开火）|
| 坐在 **FRV 座位**上 | **水平（yaw）可控**；**俯仰（pitch）不可控**（枪口停在最高仰角）|
| 坐在 **工事自己的座位**上 | **和原版一样，两轴都正常** |

⇒ 这条线的实用结论：**工事**这一类也能上载具，且 yaw + 开火可用；只剩 pitch。

**为什么 yaw 通、pitch 不通（`✓` 离线，16 条 clip 逐层对完）**

| clip | 时长 | 谁在用 | `traverse`（yaw） | `weapon_pitch`（pitch）| 双手 IK |
|---|---:|---|---:|---:|---:|
| **`23C3D282`** | 1.00 s | **layer1 s0（`Time` 循环，唯一默认开启）** | **×15** | **×2（≈常量）** | ×24/×28 |
| `E648BB4C` | 0.57 s | layer2 s0（需事件） | — | **×17** | ×35 |
| `9B7CE3BA` | 0.42 s | layer2 s1（需事件） | — | **×16** | ×30 |
| `BE2CDFA6` | 0.23 s | layer3/4 s0（开火叠加） | — | ×5 | — |
| `1D22F5E3` / `1E21164C` | 0.98 s | layer0 s0/s1 与 s3（部署/收起） | — | ×17 | — |

- **唯一常开的那层（layer1）对 yaw 打了 15 个关键帧，对 pitch 只打 2 个关键帧 ⇒ pitch 被钉成一个常量**（就是"无人时抬到最高"的静止姿势）。这与你观察到的现象完全一致；
- 真正会动 pitch 的两条 clip（`×17` / `×16`，还带双手 IK ⇒ 明显是"双手抓住炮身瞄准"）在 **layer2**，而 **layer2 默认态是 `Empty`**，要进它必须触发事件 **`0x9E1081DA`（抓握）/ `0xBCED2F48`（松开）**——这两个事件只在**玩家坐进工事自己的座位**时才会发；
- 所以：坐自己座位 → layer2 拉起"抓握瞄准"链 → 两轴正常；坐 FRV 座位 → layer2 永远是 `Empty`，只剩 layer1 的常量 pitch。
- 补一条：它**没有 `TurretComponentData`**，所以引擎那套"炮塔轴"（哨戒的 pitch/yaw 都由它驱动）根本不参与——这解释了两类件在车上的差异。

**已装诊断实验（`⚠` 待实机）**：把 layer1 的 clip 从 `23C3D282` **改指向 0 骨骼占位 `C1B7AE53`**（`patch_6` 重建，toc `7fe8761f13510fe2`；SM 里共两处改动：`layer0 1→2` + 这 8 字节）。
三档判读：

| 观察 | 结论与下一步 |
|---|---|
| **pitch 变成水平固定**（不再朝天） | layer1 就是"钉子" ✓ ⇒ 至少得到"水平固定 + yaw 可动"的可用形态；要真可控需给它补 `TurretComponentData` 或接 aim |
| **pitch 跟着准星动了** | 意外之喜：说明有别的驱动源一直压着，直接解决 |
| **连 yaw 也没了** | layer1 同时是 yaw 的来源 ⇒ 回滚，改走 `TurretComponentData` 补行 或 座位 aim 接线 |

> 另外否掉一条看似可行的路：`TurretComponentData` 行末尾 `+0x48`（哨戒多为 `551832871`）**不是骨骼哈希**——
> 没有 `traverse` 骨骼的 MG-43 也是这个值（而 `551832871` 正是"traverse"的哈希）⇒ 它是某个 u32 角色/参数 id。
> 所以"直接抄一条 turret 行给它"并不能保证引擎知道去转哪根骨骼。

**✗ 实机否证（2026-10-26 14:4x）：layer1 不能动——它是 yaw 的方向基准**

把 layer1 的 clip 换成 0 骨骼占位后：**yaw 变成反方向**，而且**连"坐工事自己座位"也一样反了**（回归！），pitch 依旧不可控。
⇒ layer1 的 `traverse` 关键帧不只是"静止姿势"，**它承载了 yaw 的基准/方向**；删掉它 ⇒ 基准丢失 ⇒ 反向。
⇒ **已回滚**到只改 `layer0 1→2` 的那版（`patch_6` toc 回到 `4b4392b5…` 派生版，SM 与 `hmg-emplace-sm.bin` 逐字节相同）。
⇒ 结论：HMG 工事的"pitch 不动"**不是 layer1 造成的**，而是**它压根没有引擎级的炮塔轴**（无 `TurretComponentData`），
而它自己的 pitch 动画链（layer2 的抓握/瞄准）又只由"坐进它自己的座位"触发。这条路到此为止（除非补 turret 组件，语义未解）。

#### 3.8.4.18 第二台工事：E/AT-12 Anti-Tank（2026-10-26 15:0x，✓✓ 实机：两轴全通）

AT-12 的层结构比 HMG **更有利**：它的**两轴都在"默认开启"的参数层里**，不像 HMG 把 pitch 藏在需要事件触发的 layer2。

| 层 | 默认态 | 绑的 clip | 打到的骨骼 | 作用 |
|---|---|---:|---|---|
| L0 | **6 → 3** | s3 = `823905BD`（展开）`27811FE8` **0.33 s / 0 骨骼** | — | 展开态靠 bind 位；s0 部署过渡 `79A49CDE` 的 `EmitEndEvent=DeployDone` → **s3** |
| **L1** | 0（`Time` 循环） | `7F6D09AE` 1.00 s | **`traverse×15`** | **yaw 驱动（常开）** |
| **L2** | 0（`Time` 循环） | `4D7C0C93` 1.00 s | **`elevation×7`** | **pitch 驱动（常开）← 与 HMG 的关键差别** |
| L3 | 1 | `EAC0C1E3` 0.17 s | `elevation×1` `barrels×2` | 小动作/音效 |
| L4 | 0（`Empty`） | s1 `59A31B6F` 叠加 | `traverse×18` `elevation×6` + **IK 手脚 ×20–26** | "坐下"叠加（需事件）|
| L5 | 1（`Empty`） | s0 = `Blend` 5 条 | — | 混合树（默认空）|
| L6 | 0（`Empty`） | s1 `90BEEF8F` 0.82 s / s2 `6DBC9C1A` 0.63 s | 手柄/瞄准镜 IK | 上/下车动画（需事件）|

⇒ **离线预测：AT-12 挂到 FRV 炮手位后，yaw 和 pitch 都应该能动**（两轴都在常开参数层，
而 HMG 之所以 pitch 死，正是因为它的 pitch 在"要事件才进"的层里）。这也与你说的"AT-12 没有'没人就抬到最高'"吻合。

**已装（`⚠` 待实机）**：

| 文件 | sha256 | 内容 |
|---|---|---|
| `data/f6fb08cc02d24255.patch_7`（+gpu/stream） | `5747c1c158736bb7` / `afd9553d753f4640` / `bacb3ba4e03b98c6` | AT-12 包 `5a0f047f2695b403` **整包 49 条**驻留（toc 3.58 MB / gpu 5.04 MB / stream 1.05 MB；**单包**，无变体副本）|
| `data/game/generated_entities.dl_bin` | `3dda2be1a87f9022` | 行 19 槽 0 = **Anti-Tank Emplacement** `0x2B11C9E4980EC479`；`Behavior 2→658` |
| SM | 6,076 B | `layer0.DefaultState 6 → 3`（只变 1 字节）|

**这一局要看的**：① 出模型、展开；② **yaw 能否跟随**（方向对不对）；③ **pitch 能否跟随**（这是本局核心）；
④ 开火/装填（它的 L3 s2 `B127A357` 是装填动画：`shell/loader/feed/claw`）。
若 pitch 也不行，那就把"`Traverse`/`Elevation` 参数层由谁喂"作为下一个问题（需要知道这两个 `Time` 层绑的是哪两个 SM 变量）。

**✓✓ 实机（2026-10-26 15:0x，AT-12 挂 M-102 FRV 炮手位）**：**yaw 和 pitch 都能跟随，其它也全正常**（出模型、展开、开火）。
这是**第一台在载具上完整可用的人操工事**（两轴都可控），也是"人操工事"这一类能上载具的直接证据。

⇒ 两台工事的差别，现在可以精确到"层"上：

| | HMG-101 | **AT-12** |
|---|---|---|
| yaw 驱动层 | L1 `Time` `23C3D282`：`traverse×15` ✅ | L1 `Time` `7F6D09AE`：`traverse×15` ✅ |
| **pitch 驱动层** | **没有**：pitch 只在 L1 里打了 **2 个关键帧（常量）**，真正会动的两条（`E648BB4C` pitch×17 / `9B7CE3BA` pitch×16 + 双手 IK）在 **L2 的 `Clip` 状态**，要事件 `0x9E1081DA`/`0xBCED2F48` 才进 ❌ | **L2 `Time` `4D7C0C93`：`elevation×7`，默认开启** ✅ |
| L2 的 `Blend` 状态 | `EE10B788`：**8 条 clip 全是 0.067 s / 0 骨骼的空 clip** ⇒ 参数化瞄准只剩个壳，里面没内容 | L5 `Blend`（5 条，默认 `Empty`）|
| 实机结果 | yaw ✅ / **pitch 死（停在最高仰角）** / 开火 ✅ | **yaw ✅ / pitch ✅ / 开火 ✅** |

**⇒ 人操工事的挂载判据（以后照这个查，不用实机试）**：
1. 找出 `traverse`（yaw）与 `elevation`（pitch）**各自的驱动层**；
2. **只有当某一轴由「默认开启的 `Time` / `Blend` 层 + 有键 clip」驱动时，这一轴在载具上才可控**；
3. 若某一轴只存在于**事件门后的 `Clip` 状态**（例如 HMG 的抓握瞄准链，事件只在玩家坐进它自己的座位时才发），
   那这一轴在载具上**必然死**，除非另外给它补 `TurretComponentData`（`+0x48` 语义未解，见 §3.8.4.17）；
4. 顺带记一个"空壳"陷阱：HMG 的 `Blend` 状态有 8 个 anim 槽看着像 8 向瞄准混合树，
   实际 8 条全是 0.067 s / 0 骨骼的空 clip ⇒ **不能靠"有 Blend 层"就断定它是参数化瞄准**，必须检出 clip 的时长与打点。

**本线成果总表（截至 2026-10-26 15:0x，全部实测）**：

| 件 | 类别 | 状态 | 备注 |
|---|---|---|---|
| A/AC-8 自动炮哨戒 | AI 炮塔（模板 A）| ✓✓ | `layer0=3` |
| A/MLS-4X 火箭哨戒 | 模板 A | ✓✓ | `layer0=3` + 关 `layer5` 扫视层 |
| A/FLAM-40 火焰哨戒 | 模板 A | ✓✓ | `layer0=3` |
| A/LAS-98 激光哨戒 | 模板 A（C0）| ✓✓ | `layer0 3→1` |
| A/MG-43 机枪哨戒 | 模板 B | ✓✓ | `layer0 1`（部署过渡末帧定格）+ 关 `layer5` |
| A/G-16 加特林哨戒 | 模板 B（8 层）| ✓✓ | 同上，扫视层在 `layer6` |
| A/M-12 迫击炮哨戒 | 模板 A 形状 | ✓✓ | `layer0=3`；另补 M-12 声明包修掉灰色方块 |
| **E/MG-101 HMG 工事** | 人操工事 | ⚠ **yaw+开火可用，pitch 死** | 无 `Turret`，pitch 只在事件门后 |
| **E/AT-12 反坦克工事** | 人操工事 | **✓✓ 两轴全通** | 两轴都是常开 `Time` 参数层 |
| A/ARC-3 特斯拉塔 | 电弧武器（无 `Turret`）| **✓ 可用但效果不好** | 能挂车、展开对、能放电弧；仰角小时会电到车自己 |

#### 3.8.4.19 A/ARC-3 特斯拉塔：敌我开关不在 AIBEH（也不在 `SensorEye+0x20`）；已能挂车但**效果不好**（2026-10-26 15:1x）

**件与组件**（`0x74599E56F72F9D7E`，包 `8abffb1f5544121b`）：`ArcWeaponComponentData` + `SensorEye` + `Detector` + `Targeting` + `Behavior` +
`Wieldable`/`WeaponWielder`/`WeaponData`/`WeaponMagazine`；**没有 `TurretComponentData`**（塔不转，符合原版）、**没有 `ProjectileWeapon`**（电弧武器）。

**结论先说**：**"敌友不分"不在 Behavior（即我们常说的 AIBEH）里，而在 `SensorEyeComponentData+0x20` 这个"敌对阵营掩码"上。**

| 实体 | `SensorEye+0x20` | 语义 |
|---|---:|---|
| 玩家哨戒（MG-43 / 迫击炮 / 火箭 / 火焰 / 激光）| **1** | 只打"与超级地球敌对"的 ⇒ 敌人 |
| 敌方炮塔（AA Emplacement / Ballistic Missile / Gazer）| **2** | 只打"与敌方敌对"的 ⇒ 玩家 |
| **A/ARC-3 特斯拉塔（玩家方）** | **3** | **敌对双方都打 ⇒ 无差别电击**（`1\|2`）|
| 敌方 AA 工事 `0xAEAEF7A1851E6C9D` | 3 | 同样双方都打（面杀伤武器）|
| Hulk Fusion Repeater（手持）| 1 | 同上表 bit 语义 |

**Behavior（AIBEH）的取值是"性格/动作 profile"，不是敌我开关**——同一批实体里它从 2 到 661 都有：

| 实体 | `Behavior+0` |
|---|---:|
| 特斯拉塔 | **661** |
| 玩家哨戒（原版）| 313 / 214 / 320 / 309 |
| 车载武器（我们统一设的）| 658 |
| 敌方 AA / Gazer / 导弹工事 | 78 / 306 / 658 |

我们前几轮把哨戒的 `Behavior` 改成 658 **只是让车位的玩家能接管**，从没改变过它们"打谁"——这本身就是"AIBEH 管动作、不管敌我"的旁证。

**行内其它字段的归属（顺带解出来，`✓`）**：

| 位置 | 含义 | 证据 |
|---|---|---|
| `Targeting+0x1C` | **瞄准/转动所用的骨骼哈希** | MG-43 = `1176554573` = 它的 `gunhousing` 骨骼 |
| `SensorEye+0x14` | **"眼睛"骨骼哈希** | MG-43 = `633953555` = 它的 `laser` 骨骼 |
| `Targeting+0x00/+0x10/+0x14` | 索敌距离 25 / 视场 90° / 半角 180° | 特斯拉与哨戒一致 |
| `Detector+0x14` | 特斯拉=1、哨戒=0（多数 0，Gazer=1）——语义未定 | — |

**已装（`⚠` 待实机）**：`SensorEye+0x20` **3 → 1**（特斯拉塔行），
`generated_entities.dl_bin` = `aad22c9392411142`（`entity_field_set` 全门禁通过、锚点哈希 `8E49771B181FFAA1` 保持、字段读回 = 1）。
FRV 炮手位仍是 **AT-12**（未动）。

**这一局怎么验**：正常任务里叫一次 A/ARC-3 特斯拉塔，**自己站在它 25 m 范围内**（或让队友/npc 靠近）：
- 不再电你 ⇒ 掩码语义成立（`3` = 打双方，`1` = 只打敌人）；
- 照旧电 ⇒ 掩码不是那个开关，下一步往 `Detector+0x14` 或 `ArcWeapon` 行上找。

**能不能"通过改 AIBEH 控制它"**：**控制不了"打谁"**（那是掩码）；但**能控制"它是否自己行动"**——
`Behavior` 设成 658 就能像哨戒那样被车位玩家接管（它没有 `Turret` 所以不能转，但电弧是面杀伤，不需要转）。

**实机（2026-10-26 15:0x）：掩码 3→1 仍然电自己人** ⇒ `SensorEye+0x20` **不是**那个开关（或不是唯一的开关）。
按指示回到原版掩码（`3`），改走"挂车 + `Behavior 658`"这条路。

**已装（特斯拉塔挂 M-102 FRV 炮手位，`⚠` 待实机）**：

| 项 | 值 |
|---|---|
| SM | `74599E56F72F9D7E`（2,012 B，2 层）：**`layer0.DefaultState 1 → 3`**（折叠 `330CA356` → **展开 `823905BD`，`loop=1`**），只变 1 字节 |
| 展开 clip | `FFD9A888` 0.98 s / `loop=1`：**满骨骼动画**（`traverse×15` `pole×15` `surge_breaker_switch_01..03` ×31–33、`zapper_prong_*`、全部 `flaps_*_prong_*_tip` ×25–32）⇒ 待机电弧那套，不是空 clip |
| L1 | 默认 0（`Clip`，另一条展开用的 `FFD9A888`）；s1 `F5EACFD8` = 开火叠加，默认不参与 ⇒ 不动 |
| 驻留 | `data/f6fb08cc02d24255.patch_8` = 包 `8abffb1f5544121b` 整包 38 条（toc `f1bdd85b69d21f94` 1.87 MB / gpu `e80e64b0b9cc6a7a` 3.55 MB / stream `1cb638234fe5bbea` 0.51 MB；材料×14 / 粒子×7 / 动画×5 / 贴图×4）|
| entities | `9c202bfd534268d4` —— 行 19 槽 0 = **Tesla Tower** `0x74599E56F72F9D7E`；`Behavior 661 → 658`；**`SensorEye+0x20` 已回原版 `3`** |

**这一局要看的**：
1. 车上**出不出**特斯拉塔（它 `Turret=False`、`ProjectileWeapon=False`，是拿 `ArcWeapon` 的件 ⇒ 又一次验"五件套"的边界）；
2. 展开形态对不对（依赖上面那条满骨骼 clip）；
3. **能不能开火**（`Behavior 658` 是否让它被炮手位接管）；
4. 会不会**电到车上的人**（掩码是原版 `3`，预期会——这局主要看"能不能用"，不是"安不安全"）。

**实机结果（2026-10-26 15:1x）：✓ 可用，但效果不好**

| 项 | 结果 |
|---|---|
| 车上出件 | ✅ 出（`Turret=False` + `ProjectileWeapon=False` 也照样能挂 ⇒ **五件套边界再次放宽**，与激光的 `BeamWeapon` 同类结论）|
| 展开形态 | ✅ **正确**（依赖 `FFD9A888` 那条满骨骼 clip）|
| 开火 | ✅ 能正常发射电弧（`Behavior 658` 让它被炮手位接管）|
| **问题** | ⚠ **仰角小时电弧会打到 FRV 自己身上**（自伤）|

⇒ **官方评价：可用，但是效果不好。** 原因很清楚：塔本身**没有 `Turret`（不能俯仰/抬高避开车身）**，
电弧以 `zapper_prong_*` 为源、索敌半径 25 m，仰角压低时源点离车体太近，电弧链把车自己算进目标里了。
另外掩码仍是原版 `3`（双方都打）⇒ **它对车、对友军都不会挑**。

**若要改善（按成本，均未验证）**：
1. **把塔垫高**：`unit_offset.py shift --dz +X`（`unit` 节点位移，我们已在火箭哨戒上验过 ✓✓）——抬高源点、拉开与车体的距离；
2. **缩小电弧射程**：`Targeting+0x00`（现 25 m）/ `SensorEye+0x00`（25）两处一起改小 ⇒ 车体落在范围外；
3. **换瞄准骨骼/加 `Turret`**：让它能抬高——代价大（要给件补 `TurretComponentData`，`+0x48` 语义未解）。
4. 至于"打友军"：`SensorEye+0x20` 已实机否证不是那个开关，下一条候选是 `Detector+0x14`（特斯拉=1、哨戒=0）与 `ArcWeaponComponentData` 行。

#### 3.8.4.20 非武器类战备：E/FX-12 护盾继电器 与 MS-11 Solo Silo（2026-10-26 15:3x，⚠ FX-12 已装待验）

这两件都不是炮塔，判据也要换：**它们的武器组件一个都没有**（`Wieldable` / `WeaponWielder` / `Turret` / `ProjectileWeapon` 全缺），
所以"炮手位能不能操作"根本不适用——要验的是"**挂上去之后被动/装置逻辑还跑不跑**"。

| 件 | id | 组件要点 | 包 |
|---|---|---|---|
| **E/FX-12 护盾继电器** | `0xED13DDC480EC6910` | `ShieldComponentData` + `Ability` + `Animation` + `Destructible` + `HellpodPayload`；**无武器组件、连 `Behavior` 都没有** | `fe0db34ac2b9ac61`（32 条，SM = `gy_shield/energy_shield`）|
| **MS-11 Solo Silo** | `0xD24156BD98FFF3FE`（变体 `0xDDDB2910FF2B24E9`）| `GuidanceTarget` + `SeekingMissile` + `SensorEye` + `Explosive` + `Ability`；无武器组件 | `0971e953fcbdd346`（含 SM）|
| **Solo Silo 标记器** | `0xFC13460592CA79AA`（support weapon，`Wieldable=1`）| `LaserDesignatorComponentData` + **`WeaponLinkerComponentData`** + `AbilityWeapon` + `Equipment` | `18235e0c9ec0e636`（**3,522 条 animation** 的共享玩家包，本来就常驻）|

**问题 1：FX-12 的护盾数据在哪？→ 实体组件 `ShieldComponentData`，没有独立护盾表（`✓`）**

`data/game` 下 **55 张表里没有任何 shield 表**；护盾参数在 `generated_entities.dl_bin` 的
块 **`ShieldComponentData`（`0x5154DB66`，行宽 344 B）**，按实体键取行。全表 **15 个实体**持有它
（背包护盾、护盾继电器、敌人护盾模块都在同一块里）。

FX-12 那一行的非零字段（`✓` 逐字节扫出）：

| 偏移 | 值 | 猜测 |
|---|---|---|
| `+0x00` | **15.0** | 护盾半径（背包护盾那行是 `1.3`，正好对应它的小球形罩）|
| `+0x4C` | **4000.0** | 护盾总耐久 |
| `+0x54` | 1 (u32) | 开关/模式 |
| `+0x58` / `+0x5C` | 0.01 / **45.0** | 未定 / 角度或延迟 |
| `+0x60` / `+0x64` | **400.0** / **900.0** | 未定 / 可能是持续时间 |
| `+0x70` 1.0 / `+0xB0` 2.0 / `+0xE4` 0.65 / `+0xF0` 0.75 / `+0x104` 0.5 / `+0x118` 0.25 | 一组曲线系数（衰减/再生）|
| `+0xCC` | `1176554573` = `gunhousing`（u32 哈希）| 某个"附着骨骼"，语义未定 |
| `+0xFC`/`+0x110`/`+0x124` | `3881139314`（重复三次）| 同一 u32 哈希（材质/曲线/音效？）|

⇒ 要改护盾（半径/耐久/持续）**直接改这一行**，不涉及任何表。

**问题 2：MS-11 与标记器的联动字段在明文表里吗？→ 字段在，"配对"不在（`✓`）**

两边组件都在实体表里：标记器有 `LaserDesignatorComponentData`（**+0x00 = 750**，指示距离 750 m）
与 `WeaponLinkerComponentData`（12 B = `{1, 0x06212002, 2087}`；全表仅 3 个实体持有，另两个是 `{0,…}` / `{2,0,0}`）；
发射井有 `GuidanceTargetComponentData`（+0x0C=100、+0x10=2、+0x14/0x18=1、+0x20=0.95、+0x24=1.75）与 `SeekingMissileComponentData`。

**但找不到任何"标记器 ↔ 发射井"的静态交叉引用**：
1. `generated_stratagem_settings` 明文里**搜不到这两件的任何一个 id**；
2. 两件的组件行之间**没有任何共享哈希**（比对过 750 / `0x06212002` / 2087 与发射井的 `3167719909` 等）；
3. `WeaponLinker` 第三个字段只有标记器是 `2087`，另两个持有者为 0 ⇒ 更像"指示器自己的配置"，不是指向发射井。

⇒ **耦合是运行时的"当前指示目标"**：标记器写一个"已指示"状态，任何带 `GuidanceTarget`+`SeekingMissile` 的弹药去追它。
这解释了为什么没有静态字段——它本来就是**一对多**（一个指示器能给多种制导弹药指路）。

**已装（`⚠` 待实机）：E/FX-12 护盾继电器挂 M-102 FRV 炮手位**

| 项 | 值 |
|---|---|
| SM | `ED13DDC480EC6910`（2,028 B，2 层）：**`layer1.DefaultState 0 → 2`**（s0 待机循环 → **s2 激活循环** `6E1E248B`）；`layer0` 不动（s0/s1 用同一条 pod clip）|
| 驻留 | `data/f6fb08cc02d24255.patch_9` = 包 `fe0db34ac2b9ac61` 整包 32 条（toc `6b7989a2476e861e` / gpu `d253bf15914fca23` / stream `0b7d89cd13cf1dda`）|
| entities | `bea0e90d0ac8bcc3` —— 行 19 槽 0 = **Shield Generator Relay**；**`Behavior` 组件根本不存在，无需改** |
| 五件套 | `Turret=False` **`Wieldable=False` `WeaponWielder=False` `ProjectileWeapon=False`** —— 这是**第一件完全没有任何武器组件的挂载件** |

**这一局要看的**：
1. 车上**出不出**继电器模型（`Wieldable=False` 会不会让挂载槽直接拒绝？本局最大未知）；
2. 激活外观对不对（`layer1 → s2` 是否就是"开着转"那一态）；
3. **护盾泡出不出现、挡不挡伤害**（`ShieldComponentData` 自驱动，半径 15 m 会罩住车）；
4. 会不会**跟着车跑**。

**实机（2026-10-26 15:3x）**：✅ 车上出继电器、✅ **护盾泡出现**、✅ **跟着车跑**、⚠ **模型看起来还是"未展开"**。
⇒ "非武器件能不能挂"这条**已经答了：能**（`Wieldable=False` 也不影响挂载槽接受它，护盾逻辑照跑）。

**护盾字段逐个对号（`✓✓` 用两个已知背包当锚点）**

社区元数据（`refs/HD2Runtime-ModBuilder/…/BackpackAuthoringCapabilities.json`）里带着**语义字段名 + 默认值**，
拿 `SH-32 护盾背包` 的两个已知默认值当锚点，与 15 行护盾数据一一对上，映射就定了：

| 偏移 | 语义（社区字段名）| FX-12 实测 | SH-32 背包 | 另一背包 |
|---|---|---:|---:|---:|
| `+0x00` | `shield.radius`（m）| **15** | 1.3 | — |
| `+0x4C` | `shield.durability`（HP）| **4000** | **150** | **1000** |
| `+0x58` | `shield.recharge_delay`（s）| **0.01** | **60** | **3** |
| `+0x5C` | `shield.broken_recharge_delay`（s）| **45** | **12** | **6** |
| `+0x60` | `shield.recharge_rate`（HP/s）| **400** | **150** | **300** |
| `+0x64` | 未知（FX-12 900 / 背包 150）| 900 | 150 | 200 |
| `+0x70` | 标志位（全表恒 1）| 1 | 1 | 1 |
| `+0xE4` / `+0xF0` / `+0x104` / `+0x118` | 一组系数 | 0.65 / 0.75 / 0.5 / 0.25 | — | 0.5 / 0.75 / 0.5 / 0.25 |

（加粗那四列的对应关系是"元数据默认值 ↔ 表内字节"严丝合缝，所以映射可信。）

**"持续时间"不在护盾里**：`ShieldComponentData` **没有 duration 字段**——
FX-12 的存活时长来自实体的 `HellpodPayloadComponentData+0x04`：**FX-12 = 40 s**（哨戒那批是 150 s，见 §2）。
⇒ 想调"护盾能罩多久"：改 **`HellpodPayload+0x04`**；想调"多硬/回多快"：改上表 `+0x4C` / `+0x58` / `+0x5C` / `+0x60`；想调"多大"：改 `+0x00`。

**"未展开"的追查（`⚠` 待验 v2）**：FX-12 的 SM 里
`layer1 s0`（默认，`7BB7A52E` 1.38 s，只键 `top_rotator`/`fan_rotator`）→`s1`（同 clip 播一次）→`EmitEndEvent 44E27DCA`→
`s2`（`6E1E248B` 1.00 s，**额外键 `piston_tip_1..6` 各 32 帧** = 六个活塞伸出）。
v1 我们是**直接默认到 s2**（跳过了 s1），实机看起来仍像未展开。
**v2 已装**：`layer1.DefaultState 0 → 1`（走原版链：播一次 → 自动进 s2），`patch_9` 重建（toc 变了、gpu/stream 不变）。
若 v2 仍折叠，说明"展开"不在这个 SM 里（而在他掉落时生成的 `energy_shield` 子实体/pod），下一手改看 `layer0` 或那条子实体。

**附带发现**：社区元数据里还提到 **`ShieldHitFilterComponentData`**（护盾命中过滤器，独立组件）——
以后若要做"护盾只挡敌人子弹"这类效果，开关可能在它身上（`⚠` 未验）。

**调参实验（2026-10-26 15:4x，`⚠` 待实机）：验证"破盾后能不能恢复"**

原版 `+0x5C`（破盾后回充延迟 **45 s**）比它自己的 `HellpodPayload+0x04`（寿命 **40 s**）还长
⇒ **原版根本不可能出现"破盾后再回"**（物件先消失了）。这是一条结构死区，值得单独验。

按这个思路把四个字段一起改（`generated_entities.dl_bin` = **`1b4759c0984f34e2`**）：

| 字段 | 原值 | 新值 | 目的 |
|---|---:|---:|---|
| `HellpodPayload+0x04` | 40 | **180** | 让寿命长过回充延迟，留出时间窗（同时验证这个字段到底是不是寿命）|
| `ShieldComponentData+0x4C`（durability）| 4000 | **400** | 打破得快一点（10× 更容易破）|
| `ShieldComponentData+0x60`（recharge_rate）| 400 | **0** | **隔离"持续回充"** —— 这样"回来"只能来自"破盾后恢复"机制 |
| `ShieldComponentData+0x5C`（broken_recharge_delay）| 45 | **5** | 破盾后 5 s 触发 |

**判读表**：

| 观察 | 结论 |
|---|---|
| 破盾后约 **5 s 泡泡整块回来** | "破盾后恢复"是独立机制，`+0x5C` 就是它的延迟，且不受 `+0x60=0` 影响 |
| 破盾后 **完全不回来** | 引擎不接受这套参数（或恢复仍依赖 `+0x60>0`），原版死区是设计使然 |
| 破盾后 **缓慢回**（非整块）| `+0x5C` 只是"恢复前等待"，恢复仍走 `+0x60` ⇒ 与 `=0` 矛盾，说明速率字段读的是别处 |
| **40 s 左右继电器就消失** | `HellpodPayload+0x04` 不是寿命（字段归属错了），要另找 |
| 90 s 后还在、180 s 后消失 | `+0x04` 就是寿命 ✓（这条本身也值钱）|

**第一轮结果（`+0x60=0`，2026-10-26 15:4x）——关键发现：恢复是"两段式"**

实机：护盾被打破后，**看到了"恢复特效"**，但泡泡**随即又消失**。

⇒ 拆解成两步：
1. `+0x5C`（`broken_recharge_delay`）= **"破盾恢复"的触发器/延迟**：时间到就播恢复特效（所以原版 45 s 这个分支确实存在，只是永远等不到）；
2. `+0x60`（`recharge_rate`）= **供血速率**：速率 0 ⇒ 一滴血都补不回来 ⇒ 特效播完护盾仍是 0 HP ⇒ 立刻又碎。
⇒ **两段缺一不可**：`+0x5C` 决定"什么时候开始回"，`+0x60` 决定"回多快"。

**第二轮（`+0x60=1`，2026-10-26 15:5x，`⚠` 待验）**：`generated_entities.dl_bin` = **`8e95f53dbd451b9e`**
（寿命 180 / 耐久 400 / 破盾延迟 5 / 速率 **1 HP/s**）。

**判读**：
| 观察 | 结论 |
|---|---|
| 破盾 5 s 后**泡泡重新出现**（很薄），之后几乎不涨 | 两段式成立 ✓；泡泡按"HP>0"显示，不看百分比 |
| 破盾 5 s 后**一直不出现**，直到攒够某个血量 | 显示有"最低血量门槛"，值得记下来 |
| 破盾 5 s 后**还是彻底消失** | 速率 1 仍不够（可能按 tick 取整，1 HP/s 太小被舍掉）⇒ 下轮试 10~50 |
| **90 s 后继电器还在** | `HellpodPayload+0x04` = 寿命 ✓（上一轮设计的自对照）|

**第二轮结果（`+0x60=1`，2026-10-26 15:5x）——两条都成立**

- **破盾 5 s 后泡泡重新出现** ⇒ 两段式恢复成立 `✓✓`：`+0x5C` 触发、`+0x60` 供血，缺一不可；
- **90 s 后继电器还在** ⇒ `HellpodPayload+0x04` **就是寿命** `✓✓`（原版 40 s 那条自对照也解释了"原版永远等不到破盾恢复"）。

**第三轮（`+0x00` 半径 15 → 7.5，2026-10-26 16:0x，`⚠` 待验）**：`generated_entities.dl_bin` = **`cd8825d7669f481b`**
（其余三字段保持 180 / 400 / 5 / 1）。

| 观察 | 结论 |
|---|---|
| 泡泡**球体半径肉眼减半**（≈7.5 m），站的远近手感也对得上 | `+0x00` = 半径 `✓✓` |
| 视觉不变、但"挡不挡"的范围变了 | 视觉球由特效资源定尺寸，`+0x00` 只管碰撞/判定 ⇒ 两者要分开测 |
| 完全没变化 | `+0x00` 不是半径（可能是"内圈/到中心最小距离"之类），要另找 |

**第三轮结果（`+0x00` 15→7.5，2026-10-26 16:0x）：`✓✓` 泡泡球体肉眼减半** ⇒ **`+0x00` 就是半径**，可直接用来调护盾范围。

#### 3.8.4.21 护盾"形状"是资源决定的，不是字段（2026-10-26 16:1x，`✓` 离线）

问：SH-51 方向护盾是**弧面**，FX-12 / SH-32 是**完整球面**——形状是字段还是网格/材质？

**答：是资源。** `ShieldComponentData` 里**没有任何形状/类型字段**；差别在"用哪个 unit 当泡"：

| 护盾 | 罩子用的 unit 资源 | 体量 | 参数挂在哪 |
|---|---|---|---|
| **FX-12 / SH-32 / 通用 "Shield"** | **同一个共享 unit `0xFE273AD831881A39` = `SH-32 Shield Generator Sheild`** | 2,368 B / 122 KB GPU | 挂在**持有人**身上（FX-12 自己的行半径 15；SH-32 背包行半径 1.3）|
| **SH-51 方向护盾** | **`0xB56FA3F5510000AB`**（自己包里那块，无名字）| 1,680 B / **8 KB** GPU | 挂在**屏障实体自己**身上（独立 `ShieldComponentData`：耐久 1000 / 延迟 3、6 / 速率 300）|

旁证三条：
1. 共享球面 unit 在 **FX-12、SH-32、通用 Shield 三个包里各存一份**（同名同 id）⇒ 三家的泡本来就是**同一个 mesh**；
2. **弧面那行的 `+0x00` 半径 = 0**，而球面各行都是真半径（15 / 1.3 / 8 / 30 / 45 / 60）⇒ 半径字段只对球壳有意义，形状不归它管；
3. 材质/粒子也随包走（FX-12 包有 material×12、particles×4；SH-51 包 material×4、texture×3）。

**`⚠` 还没定位"谁引用这个泡 unit"**：FX-12 的 `unit`（43 节点，只有继电器本体）、`EffectReference`（3,912 B 行内没有那个 id）、`Ability`（全 12 的空壳）、
`generated_add_resource_dependencies.dl_bin`（**整表只有 228 B**，不含任何相关 id）里**都找不到** `0xFE273AD831881A39` ⇒
引用点要么在引擎代码里按约定生成，要么在战备/能力生成链上（待查）。

**因此"把球面换成弧面"的可行路径**：
1. **资源替换（最直接）**：把共享 unit `0xFE273AD831881A39` 的 mesh 换掉——但它是**多件共用**的，替换会同时影响 SH-32 等，所以只适合"就想全局改"的场合；
2. **想让 FX-12 独占弧面**：得先找到那个引用点，再把它指向一个新 unit id（自己做的弧面 mesh）——目前卡在"引用点未知"。





#### 3.8.4.22 地雷系列战备：雷是"投掷实体"，不是弹丸（2026-10-26 16:2x，`✓` 离线）

四个地雷战备件：`Anti-Personnel Minefield` `0xF00C349422E8E320`、`Anti-tank Mines` `0x25A2FD037B6ED25C`、
`Gas Mines` `0xA9982969137F3D77`、`Incendiary Mines` `0xBF32E12923A9A252`（都带 `MinefieldComponentData` + **`ThrowerComponentData`**）。

**核心答案：地雷不是 projectile，是和手雷同族的"可投掷实体"**

| 角色 | 组件 | 说明 |
|---|---|---|
| 抛洒器（战备件本体）| `ThrowerComponentData` + `MinefieldComponentData` | 负责"把雷扔出去"和"撒成一片" |
| **单颗雷**（如 `contact_mine`）| **`ThrowableComponentData` + `ExplosiveComponentData`** + LoadoutPackage / Spottable / Unit（**只有 5 个组件**）| 手雷同族；**没有 `AnimationComponent` ⇒ 地雷本身没有状态机** |

**`ThrowerComponentData+0x00` = 要扔的实体 id（u64）** `✓✓` —— 四个变体就是这么区分的：

| 战备 | `Thrower+0x00` |
|---|---|
| Anti-Personnel Minefield | `0xEE89CC10D80B6AFB` = **`contact_mine`** |
| Incendiary Mines | `0xE49A5AE078AAD407` = **`incendiary_mine`** |
| Anti-tank Mines | `0x032489CF1D439BBA` |
| Gas Mines | `0x693028644D27FFEF` |

⇒ **换雷种 = 改 `Thrower+0x00` 指向另一颗雷的实体 id**（不需要碰弹丸表）。
`✓✓` 已实机走通（AP → 毒气雷）：除实体 id 外还要抄**速度两段**、`+0x10C`、`Minefield+0x18`，并**驻留目标雷的资源包** —— 见 §3.8.4.24。

**其它字段（`✓` 四变体横比；`⚠` 语义为推断）**：`Thrower` 行 752 B、`Minefield` 行 44 B。

| 字段 | AP | AT | Gas | Incend | 推断 |
|---|---:|---:|---:|---:|---|
| `Thrower+0x08` | 0.7 | 0.7 | 0.7 | 0.7 | 抛出速度/初速系数（四件相同）|
| `Thrower+0x28` | 6 | 6 | 6 | 6 | 每批/每秒投掷数（四件相同）|
| `Thrower+0x2C` | 8 | **3** | 8 | 8 | 变体差异（AT 只 3 → 可能"每批数/散布点"）|
| `Minefield+0x08` | 0.001 | **1.0** | 0.001 | 0.001 | AT 独高 → 可能是"最小间距/触发半径" |
| `Minefield+0x0C` / `+0x10` | 0.2 / 0.25 | 0.2 / **0.2** | 0.2 / 0.25 | 0.2 / 0.25 | 散布抖动 |
| `Minefield+0x14` | 80.298 | 80.298 | 80.298 | 80.298 | **撒布覆盖半径 ≈ 80 m**（四件相同）|
| `Minefield+0x18` | 367 | 179 | 270 | 72 | 每变体一个 id（雷类型/数量表索引，语义待定）|

**地雷抛洒器的状态机：`_launcher/mine_launcher`（`0xF00C349422E8E320`，2,036 B，3 层）**

| 层 | 默认 | 状态 | 说明 |
|---|---|---|---|
| L0 | **1 = `330CA356`（折叠）** | s0 `79DE1870`（部署过渡，clip `3EB31C8D`）；s2 `D23167BF`（收起，`EmitEndEvent=0x27A2636E` → **s1**）| **没有"展开态"这一档** ⇒ 与模板 B 同型：展开靠 s0 的末帧定格 |
| L1 | 1 | 两态**共用同一条 clip** `6A52B4F8`，由事件 `0x580DF130`→s0（blend **2.0**）、`0x56ABDA23`→s1（blend **1.0**）切换 | 开/闭盖之类，慢混合 |
| L2 | 0 = **`9EA750D5` 状态**（clip `300DEE78` loop）| 收到 `PackageDeploy` → `Empty` | **和哨戒同款的"扫视层"** ⇒ 如果哪天要把抛洒器挂到车上，这一层就得关掉 |

**抛洒参数（角度/速度/数量）——有，而且四个变体一比就对上了（`✓` 离线，`⚠` 语义为推断）**

`ThrowerComponentData` 行 752 B，横向对比四个变体后，能"变化规律自洽"的字段如下：

| 字段 | AP | AT | Gas | Incend | 推断 |
|---|---:|---:|---:|---:|---|
| `+0x08` | 0.7 | 0.7 | 0.7 | 0.7 | **批间间隔 0.7 s**（恒定）|
| `+0x28` | 6 | 6 | 6 | 6 | **投掷批数 6**（恒定）|
| `+0x2C` | 8 | **3** | 8 | 8 | **每批颗数**（AT 少）|
| `+0xFC` | 400.0 | 400.0 | 400.0 | 400.0 | 抛距/力度初值（恒定）|
| **`+0x104`** | **5.0** | **7.0** | **7.0** | **5.0** | **抛出速度下限（m/s）** |
| **`+0x108`** | **15.0** | **17.0** | **15.5** | **15.0** | **抛出速度上限（m/s）** |
| **`+0x118`** | **45.0** | **45.0** | **45.0** | **45.0** | **抛射角 45°**（恒定）|
| `+0x290` | 45.0 | 45.0 | 45.0 | 45.0 | 第二处 45（可能是扇形散布半角）|
| `+0x268`/`+0x26C`/`+0x270` | 2 / 4 / 3 | 同 | 同 | 同 | 时间/超时参数（待定）|
| `+0x14C` / `+0x2C4` | 3 / 2 | 同 | 同 | 同 | 数组计数（待定）|

**两条关键旁证**：
1. `+0x104` 与 `+0x108` **成对变化**（5–15 / 7–17 / 7–15.5 / 5–15）——这种"同升同降的上下限对"几乎只可能是**速度区间**；
2. **`+0x28 × +0x2C` = 6×8 = 48**，而行尾正好是 **48 个 4 字节骨骼槽**（`+0x1A8…+0x264`，全部默认填 `1243096897` = `StingrayEntityRoot`）⇒
   **"6 批 × 每批 8 颗 = 48 个出手点"** 完全吻合（AT 是 6×3=18）。这也是"每个槽 = 一颗雷的出手骨骼"的直接证据：
   把它改成别的骨骼哈希，就能让雷从**指定骨骼**上抛出。

**换雷种实验（2026-10-26 16:2x，`⚠` 待实机）：让抛洒器扔手雷**

既然雷和手雷同属 `Throwable` 家族、而 `Thrower+0x00` 只是一个实体 id，那就应该能直接让它**扔别的投掷物**。
按这个思路把 AP 地雷阵的投掷实体换成 **G-123 Thermite**（引信长、发光、好观察）：

| 项 | 值 |
|---|---|
| 改动 | `ThrowerComponentData+0x00`：`contact_mine 0xEE89CC10D80B6AFB` → **`Thermite 0xC5C05FCB5747C799`**（`entity_field_set --type u64`，`expect-old` 校验通过）|
| Thermite 组件 | `Throwable` + `Explosive` + **`Sticky`** + `Equipment` + `Wieldable` + `CollisionEvent`/`PhysicsImpactEffect`（**没有 `Animation` ⇒ 无状态机**，与雷同型）|
| 驻留 | `data/f6fb08cc02d24255.patch_10` = 包 `dfb81f9917285965` 整包 14 条（toc `42cb6cb331c4822c` 2.56 MB / gpu `0b26a4a779c62e6c` 1.29 MB / stream `bdae403fd82b3186` 0.44 MB）。<br>该实体的资源在共享包 `fc5b6bff0db90aab` 里**也有一份完全相同的拷贝**，加这份驻留只是保证"玩家没带 Thermite 也能解析到" |
| entities | `0c2f5960168c24ae`（补丁序列 `f6fb08cc02d24255.patch_0…10` 连续）|

**这一局要看的**：
1. 抛出来的是**手雷模型**（不是地雷板）；数量按原参数就是 **6 批 × 8 颗 = 48 颗**、每 0.7 s 一批、45°、速度 5–15 m/s；
2. Thermite 带 `Sticky` ⇒ 落地可能**粘住**（地雷是不粘的）；
3. 爆炸走 Thermite 自己的 `Explosive`（不是地雷的爆炸参数）；
4. 坑：48 颗带引信+发光的粘雷同时在场，可能有**性能/连锁爆炸**问题；另外 `Equipment`/`Wieldable` 在"被抛出"语境下会不会引发异常（比如尝试把它当装备）也值得看一眼。

**如果成立，这条就通用了**：抛洒器 = "投掷任意 `Throwable` 实体"的发射器，**换一个 u64 就能换弹种**。

**第一轮：换 G-123 Thermite —— `✗` 扔出去了但引信不启动**

实机：手雷确实被抛出来（模型对），但**引信没启动**，不会爆。

⇒ 这说明"抛洒器只负责把实体扔出去，**不负责给它点引信**"。
Thermite 的引信是由**玩家投掷动作**（`Equipment`/投掷流程）启动的；被抛洒器"无主"扔出去后，没有任何东西给它起爆。
**推论（可检验）：能被抛洒器"自动激活"的实体，必须自带行为（`Behavior`/`Navigation`/`Motion`）或自带引信组件。**

**第二轮：换 G-60 Anti-Tank Seeker（2026-10-26 16:3x，`⚠` 待实机）**

选它正是因为**它自带一整套行为**（社区 Lua 时代也有人这么换成功过）：

| 项 | 值 |
|---|---|
| 件 | **`0x8E325C933E55BF62` Anti-Tank Seeker**（24 个组件）|
| 与雷/手雷的关键差别 | **`Behavior` + `Boids` + `Motion` + `Navigation` + `Rotation` + `Targeting` + `SensorEye` + `Detector`**，还有 `Animation` + **自己的状态机** ⇒ **生成即自走、自寻的**，不需要外部点引信 |
| 改动 | `Thrower+0x00`：Thermite → **`0x8E325C933E55BF62`**（`u64`，`expect-old` 通过、读回一致）|
| 驻留 | **`patch_11`** = 包 `d6d42eefe4936690` 整包 21 条（toc `58996c54548d5e19` 2.99 MB / gpu `f9c9932872a021bc` 0.54 MB / stream `ea8761507c7d52ac` 0.09 MB；含 animation×10 + state_machine×1 + mesh×1）。<br>**这份驻留是必需的**：它的行为/状态机/网格都在这个包里，而测试时玩家不会带 G-60 |
| entities | `c55510c8196aeeaa`（补丁序列 `f6fb08cc02d24255.patch_0…11` 连续）|


**第二轮结果（G-60 Anti-Tank Seeker）：`✗` 也没激活** ⇒ "自带行为就会自己跑"这条不成立（至少在这个生成路径下）。

**新证据：`ExplosiveComponentData+0x00` 是"触发类型枚举"，三种实体各不相同**

| 实体 | `Explosive+0x00` | `Explosive+0x24`（爆炸 id）| 判读 |
|---|---:|---:|---|
| `contact_mine`（原生，能正常布雷）| **2** | 367 | **地雷型**：靠近/接触即触发 |
| `incendiary_mine`（原生）| **2** | 72 | 同上 |
| `Thermite`（失败）| **3** | 201 | **引信型**：需要投掷动作点火 |
| `Lure Mine` | **4** | 117 | 诱饵雷型 |
| `Anti-Tank Seeker`（失败）| —（自导）| — | 靠 `Behavior`/`Navigation` 自行推进 |

⇒ **最可能的机制：抛洒器的"布设"只对 `+0x00 = 2`（地雷型）生效**。换成 3/4/自导型，
实体虽然被扔出来，但没有任何东西把它"装上引信/启动行为"，于是静默。

**第三轮：换 TM-1 Lure Mine（`0xA20683199DFC19E8`，2026-10-26 16:4x，`⚠` 待实机）**

Lure Mine 是**投掷物栏位的地雷**（18 组件：`Throwable`+`Explosive`+`Sticky`+`Equipment`+`Wieldable`+`Faction`+`Health`+`EffectReference`…），
比 Thermite 多了 `Faction`/`Health`/`EffectReference`（说明它是有生命值、会自我表现的地雷），但 `Explosive+0x00 = 4` **仍不是地雷型 2**。

| 项 | 值 |
|---|---|
| 改动 | `Thrower+0x00`：Seeker → **`0xA20683199DFC19E8`**（u64，读回一致）|
| 驻留 | **`patch_12`** = 包 `fae34acb79502f53` 整包 22 条（toc `21bd4c9bc44bfb05` 2.41 MB / gpu `2a622f0864b2b21e` 1.40 MB / stream `58ba2893b8478c88` 0.35 MB；含 particles×8 + state_machine×1 + mesh×1）|
| entities | `e7d700de940d0797`（补丁序列 `patch_0…12` 连续）|


**第三轮结果（TM-1 Lure Mine）：`✗` 同样一出来就失活、模型很快消失** ⇒ 与 Thermite / Seeker 同现象。

#### 3.8.4.23 社区 Lua 案例怎么解决"失活"：**靠运行时原生调用手动激活**（2026-10-26 16:5x，`✓` 已读源码）

案例：`D:\Downloads\多地雷布雷器生成热熔地雷2.4.zip`（Meltamine 2.4）。它**不是数据补丁**，而是
Lua + ffi 的运行时方案（24 个 lua 模块，含内存读取、原生调用表、遥测）。关键差异一目了然：

**它的目标实体是 `MELT='EE4C107B941AB7F4'` = `Melta Mine`（"热熔地雷"本体），而它做的是下面这条链：**

1. **捕获落点**：`world_transform(old_unit)` 读出 64 B 位姿 —— 原（毒气）雷落地时的变换；
2. **先走原生气体触发再等清理**：`gas_trigger(manager, old_gas_unit, 0)` → 轮询 `unit_alive` 直到槽位清空；
3. **原生创建**：`create(...)` 造出 Melta 实体；
4. **★ 手动激活爆炸组件**：`active(explosive_manager, entity, **1**)` —— 把 `Explosive` 的 active 置 1（这一步就是"装引信"）；
5. **★ 设归属**：`owner(explosive_manager, entity, **avatar**)` —— 否则实体"无主"，会被立刻回收；
6. **★ 原生投掷**：`throw(throwable_manager, entity, pos, {0,0,0}, avatar)` —— 用零速度在捕获位姿上走一次原生投掷流程（这才是引信/布设计时的起点）。

它用的原生函数与 RVA（来源：它的 `layout` 模块，`game.dll`/`exe` 基址 + RVA）：

| 语义 | 模块 | RVA |
|---|---|---|
| `active`（爆炸激活）| game | `0x8CE9C0` |
| `owner`（设归属）| game | `0x8CEAE0` |
| `throw`（原生投掷）| game | `0x6C6930` |
| `gas_trigger`（气体触发）| game | `0x9DE640` |
| `create`（造实体）| game | `0xFD9B10` |
| `world_transform` / `unit_alive` | exe | `0x1FD160` / `0x1FEE70` |

组件 id：`Explosive = 255`（行 40 B）、`Throwable = 259`（行 28 B）。
README 还写明**必须先装备 G-40-K 热熔地雷**——因为 `create` 需要它的模板/资源在场（就是我们说的"驻留"）。

**⇒ 由此得到本线的硬结论（`✓✓` 逻辑闭合，三轮否证 + 源码互证）：**

1. **纯数据补丁无法让布雷器"扔别的投掷物"**：数据只能改"扔哪个实体"（`Thrower+0x00`），
   但"实体被造出来后要 `active=1` + 设 owner + 走一次原生 throw"这三步**没有任何数据字段能替代**；
   缺了它们，实体就是"无主、未激活"，表现为**一出来就失活、随后被回收**（正是我们三轮看到的）。
2. **数据路线能做的，只有"在原生地雷之间互换"**（4 颗：`contact_mine` / `incendiary_mine` / AT `0x032489CF1D439BBA` / gas `0x693028644D27FFEF`）——
   因为它们本来就走布雷器自己的生成/激活路径。**→ 已按这条落地并实机验成（AP → 毒气雷，`✓✓`），见 §3.8.4.24。**
3. **想要热熔雷/手雷，就必须走运行时**（Lua + ffi，按上面 6 步）；纯数据方案在这里是死的。

**现场已恢复可用状态**：`Thrower+0x00` 已改回原生 `contact_mine`（`0xEE89CC10D80B6AFB`），
`generated_entities.dl_bin` = **`290de78e0cbceb59`** ⇒ AP 地雷阵恢复正常布雷（`patch_10/11/12` 三份驻留补丁留着不影响，只是多占内存）。
（2026-10-26 17:0x 起盘上已换成毒气雷，见 §3.8.4.24；上面这一段是当时的复原状态记录。）

**四档判读**：
1. **能布设、能触发** ⇒ `+0x00=4` 也被接受，那"2"就不是唯一门槛；
2. **布设但不触发**（与 Thermite/Seeker 同现象）⇒ 证实 `+0x00` 枚举是门槛；
3. **抛出的是诱饵雷并且有闪烁/音效** ⇒ 说明"表现"正常但"触发"没接上；
4. 若第 2 档成立，下一轮就是**决定性实验**：把 Lure Mine（或 Thermite）的 `Explosive+0x00` 从 4/3 **改成 2**，看它会不会立刻变成能踩爆的雷。
**这一局要看的**：
1. 抛出来的是**自导反坦克雷**（小飞行器形态），并且**自己飞向目标**——按原参数是 **6 批 × 8 颗 = 48 颗**、每 0.7 s 一批、45°、速度 5–15 m/s；
2. 它们会不会**互相抢目标**、绕圈、或者因为 48 个 AI 同时跑而明显掉帧；
3. 命中/爆炸是否走它自己的 `Explosive`（反坦克级，比地雷强很多）；
4. 若它能自己飞，就证明上面的推论成立：**抛洒器 = 生成器；实体能不能"活"取决于它自己带不带行为/引信。**


**想验这两个字段最省的做法（各一局、单变量）**：
- 角度：把 `+0x118` 45 → **70**，看撒布是不是变成高抛、落点更近更散；
- 速度：把 `+0x108` 15 → **40**，看雷是不是飞得明显更远。

⇒ 若要把抛洒器/地雷做成**载具挂载件**，配方与模板 B 一致：`layer0` 钉到 s0（部署过渡末帧）+ 关 `layer2` 扫视层；
但注意它**没有任何武器组件**（没有 `Wieldable`/`WeaponWielder`/`Turret`），属于"FX-12 那一类非武器件"——挂了也不会被炮手位操作，只能是"自己撒雷"的装置。

#### 3.8.4.11 火焰哨戒：同一套判据照抄（2026-10-26 12:1x，✓✓ 实机）

**火焰的 SM（`820CC3BAFE962858`，2,100 B，4 层）逐层读数**（`--decode`）：

| 层 | 默认态 | 绑的 clip | 打了哪些骨骼 | 判断 |
|---:|---|---|---|---|
| L0 | s1 `330CA356`（折叠）| `0E24AEFE` 0.98 s（**= 部署 clip 本身**）| `boss×21` `elevator_01×30` `sensor×1` | 与 AC-8 同型：折叠态复用部署 clip ⇒ 出生时**不会**自动伸出 |
| L0 | s0 `79DE1870`（部署过渡）| 同 `0E24AEFE`，`EmitEndEvent=DeployDone` → **s3** | 同上 | 部署态 |
| L0 | s3 `823905BD`（展开）| `7A43988B` 1.00 s | **只有 `sensor×15`** | 本体靠 bind 位 ⇒ **这就是要设的默认态** |
| L1 | s0 `Time` loop | `F64571A1` | `traverse×15` | 与火箭同类，火箭上没造成问题 |
| L2 | s0 `Time` loop | `9CC8B842` | `elevator_01×7` | 同上 |
| **L3** | **s1 `Empty`（默认）** | — | — | **没有"扫视"那种会压死本体的循环层** ⇒ 不像火箭需要关它 |

⇒ 按火箭的判据：**只改 L0 默认态 `1 → 3`**（展开态），L3 本来就是空态、无需处理。
（对照：火箭是 L0 `1→3` **且** L5 `0→1`。）

**已装配置**（见上表"当前盘上"）：整包走共享基础包补丁（零声明）、炮手位换成火焰、`Behavior 658`。

**⚠ 若出现"沉/低"**：说明火焰的 **bind 位就是收拢位**（和火箭不同，火箭 bind 是展开位）。
那时的下一手（按成本）：
1. `layer0` 改成 **`0`（部署态）**，让 `0E24AEFE`（`elevator_01×30`）在出生时播一次；
2. 或 `layer0` 保留 `3`，另把 `0E24AEFE` 的末帧定格（需给 `state_machine_edit.py` 加"改 Link"能力）；
3. 兜底：`unit_offset.py` 的 `--dz` 位移（已验证 +2.0 m 可用）。

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

#### 3.8.4.24 换雷种落地：AP 地雷阵 → **MD-8 毒气雷**（2026-10-26 17:1x，`✓✓` 实机）

§3.8.4.23 的结论是"纯数据只有一条活路：**在原生雷之间互换**"。这一节就是那条活路的第一份实现。

**为什么这次应该成（而前三轮不行）**：门槛不是"能不能扔出去"，而是"扔出来的东西走不走布雷器自己的激活路径"。

| 雷 | `Explosive+0x00`（触发类型）| 前三轮结果 |
|---|---:|---|
| `contact_mine`（原生）| **2** = 地雷/接触 | 正常布雷、正常触发 |
| `incendiary_mine`（原生）| **2** | 同上 |
| **`0x693028644D27FFEF` = MD-8 毒气雷** | **2** | **本轮** |
| G-123 Thermite | 3 = 引信 | ✗ 扔出来但引信不启动 |
| G-60 Anti-Tank Seeker | （自导）| ✗ 不激活 |
| TM-1 Lure Mine | 4 = 诱饵 | ✗ 一出来就失活、模型很快消失 |

⇒ 毒气雷与接触雷**同为 `2`**，且同样是"数据实体（Unit/Explosive/Throwable/LoadoutPackage/Spottable 五件套）+ 一张 mesh"，所以
它走的是和 `contact_mine` **完全相同**的生成/激活路径 —— 不需要任何运行时 `active`/`owner`/`native throw`。

**这一轮新查清的 5 件事（`✓` 离线，全部可复算）**

1. **`Minefield+0x18` = 该布雷器撒的那颗雷的爆炸 id**（3/3 对表）：

   | 战备 | `Minefield+0x18` | 对应雷的 `Explosive+0x24` |
   |---|---:|---:|
   | AP | 367 | 367（`contact_mine`）|
   | Incendiary | 72 | 72（`incendiary_mine`）|
   | Gas | 270 | 270（毒气雷）|
   | AT | 179 | ？（AT 雷没有实体行，见第 5 条）|

2. **`Thrower+0x10C` 是"留场效果"伴随字段**：`Gas = 90.0`、`Incendiary = 90.0`、`AP = 0`、`AT = 0` ——
   恰好只有那两种**会留下持续区域**的雷是 90。语义未定（⚠ 可能是持续时间/衰减系数），本轮回填成 90 与原生 Gas 对齐。

3. **四个布雷器的本体是同一个 unit**：`UnitComponentData+0x00` 在 AP 与 Gas 两行都是 `0xF00C349422E8E320`，
   而 `_launcher/mine_launcher` 的 **bones 与 state_machine 的 id 也是 `0xF00C349422E8E320`**
   ⇒ 四件战备**共用同一个发射器模型/动画/SM**，差别只在两张组件行（`Thrower` 752 B、`Minefield` 44 B）。
   这也解释了为什么 §3.8.4.22 的 SM 只有一处（`_launcher/mine_launcher`，2,036 B / 3 层）。

4. **每件的"声明包"只自带自己那颗雷的网格/物理**（`LoadoutPackage+0x08` = 包 id，本轮顺带解出）：

   | 战备 | 声明包 | 包内与雷有关的资源 |
   |---|---|---|
   | AP | `a4946425b2c70017` | `mesh` + `physics` = `0xEE89CC10D80B6AFB`（`contact_mine`）|
   | AT | `12ce4bc7cddaf51c` | `0x032489CF1D439BBA`（`les/tank_mine/tank_mine`）|
   | Gas | `ef8edb7b47d8f0b3` | `0x693028644D27FFEF` + 毒气粒子（与毒气雷包**同一份字节**）|
   | 雷本体包 | —— | 每颗雷另有自己的 `LoadoutPackage`：`contact_mine → 58bdcd1c444b0981`、`gas → 18466005ef235d2b`、`incendiary → eaada9de4cd60356` |

   ⇒ **换雷必须额外把新雷的资源包驻留**，否则用的是发射器包里"旧那颗雷"的网格。

5. **毒气雷的自有包 `18466005ef235d2b`（11 条：mesh×1 + physics×1 + material×2 + texture×4 + particles×3）就够**：
   爆炸行 **270** 的 `+0x38` 粒子 = `0x12AD853FCC69467C`，**正是这个包里的粒子** ⇒ 毒气云的表现也由这一个包覆盖。

**顺带的负结果（`✓` 否证，别照抄）**：AT 雷的投掷实体 `0x032489CF1D439BBA` 在 `generated_entities`、
`generated_entity_deltas`、以及余下 53 张表里**只出现在 AT 抛洒器自己的 `Thrower+0x00` 里**，没有任何组件行
⇒ AT 雷不是数据实体，而是"只有 mesh/physics 的资源实体"（⚠ 机制未深究，不影响本轮）。

**改动清单（6 个 u32，一次 tail 宿主写完，`entity_batch_set.py`）**

| 块 | 键 | 偏移 | 原值 → 新值 | 语义 |
|---|---|---|---|---|
| `0xA29A84D8`（Thrower）| `0xF00C349422E8E320` | `+0x00` | `0xD80B6AFB` → `0x4D27FFEF` | 投掷实体**低 32 位** |
| 同上 | 同上 | `+0x04` | `0xEE89CC10` → `0x69302864` | 投掷实体**高 32 位**（`contact_mine` → 毒气雷）|
| 同上 | 同上 | `+0x104` | `0x40A00000`(5.0) → `0x40E00000`(7.0) | 抛出速度下限 |
| 同上 | 同上 | `+0x108` | `0x41700000`(15.0) → `0x41780000`(15.5) | 抛出速度上限 |
| 同上 | 同上 | `+0x10C` | `0x00000000`(0.0) → `0x42B40000`(90.0) | 留场效果伴随字段 |
| `0x74FEF89A`（Minefield）| 同上 | `+0x18` | `0x0000016F`(367) → `0x0000010E`(270) | 该雷的爆炸 id |

结果可验证到字节：**AP 的 `Thrower` 行现在与 Gas 的 `Thrower` 行逐字节相同**，`Minefield` 行也相同
（四件本来只在 `+0x18` 上不同）。也就是说：发射器现在"以为自己是 Gas Mines"。

门禁：G1（47,259,396 → 47,259,408，+12）· G2（diff=14，越界 0）· G3（锚点 `0x8E49771B181FFAA1` 保持）·
G4（6 处读回）· G6（275 块自洽）· G7（旧值全中）· G8/G9（校正字 `@0x2D11F08`）—— 全 PASS。

**已装（`✓✓` 已实机验证）**

| 件 | 大小 | sha256（前 16） | 说明 |
|---|---:|---|---|
| `data/game/generated_entities.dl_bin` | 47,259,456 | `80053101819b77fe` | 6 处改动，明文 `out/mine-gas/ap-to-gas.plain`（48 B 密封头后一致）|
| `data/f6fb08cc02d24255.patch_13` | 58,000 | `3f6182e1e55db9dc` | **毒气雷资源包 `18466005ef235d2b` 整包驻留**（11 条：texture×4 particles×3 material×2 physics×1 unit×1）|
| `.gpu_resources` | 284,018 | `c24b3b3628ae853f` | 同上 |
| `.stream` | 1,572,928 | `822ed62ab9c09665` | 同上 |
| 回滚件 | 47,259,984 | `290de78e0cbceb59` | `out/mine-gas/backup/generated_entities.dl_bin.before-ap2gas`（= 上一轮 restore 版本）|

密封往返自检：`seal-key` → `open-key` 明文**逐字节相同**（`fc57a26333f19add`）。

**这一局怎么测（单变量）**：只带 **Anti-Personnel Minefield**（别带 Gas Mines，避免"真包被加载"混进来），
扔到平坦地、退开看：撒出来的应当是 **6 批 × 8 颗、每 0.7 s 一批、45°、速度 7–15.5 m/s**。

| 档 | 看到什么 | 结论 |
|---|---|---|
| **A** | 撒出来的是**毒气雷外形**（不是 AP 圆盘雷），敌人/自己走近 → **绿色毒气云**扩散并持续掉血 | `✓✓` 成立，配方可复用 ← **本轮命中** |
| **B** | 毒气雷外形对，但**不爆 / 没有毒气云** | 雷换了、触发链缺 → 查爆炸 270 的 status effect + patch_13 是否真的生效 |
| **C** | 撒出来还是 **AP 圆盘雷** | 实体没换 → 检查盘上是否又装了别的 entities 文件 / 补丁优先级 |
| **D** | **紫色问号 / 灰块** | 资源没解析 → patch_13 三件不齐或没被加载 |

> **`✓✓` 实机读数（2026-10-26 17:10，用户回报）**：「**撒出毒气雷外形，且有作用，和原版 MD-8 Gas Mines 一致**」
> ⇒ **档 A 命中**：投掷实体、触发（`Explosive+0x00 = 2` 接触/靠近）、毒气云表现、持续伤害**全部与原版同类战备一致**，
> 不需要任何激活步骤。**"纯数据在原生雷之间互换"由此从推论变成实机配方**，同时反证了 §3.8.4.23 的判读：
> 前三轮（Thermite / AT-Seeker / Lure）失败的**唯一**原因是触发类型不符（3 / 自驱 / 4 之于布雷器的 2），不是抛洒器不会生成、也不是资源没驻留。

**A 已成立 ⇒ 配方成立**（"把任一布雷器换成任一颗原生雷"，本轮已实机走通）：
`Thrower+0x00` 换成目标雷 id → 速度两段与 `+0x10C` 抄目标战备的原值 → `Minefield+0x18` 换成目标雷的爆炸 id →
**把目标雷的自有包做整包驻留（`patch_13` 模式）**。四颗原生雷的取值：

| 雷 | 实体 id | 爆炸 id | 自有包 |
|---|---|---:|---|
| `contact_mine` | `0xEE89CC10D80B6AFB` | 367 | `58bdcd1c444b0981` |
| `incendiary_mine` | `0xE49A5AE078AAD407` | 72 | `eaada9de4cd60356` |
| 毒气雷（MD-8）| `0x693028644D27FFEF` | 270 | `18466005ef235d2b` |
| AT 雷（MD-17）| `0x032489CF1D439BBA` | 179（`Minefield+0x18` 反推）| 待查（`12ce4bc7cddaf51c` 里只有 mesh/physics）|

**回滚**：`cp out/mine-gas/backup/generated_entities.dl_bin.before-ap2gas data/game/generated_entities.dl_bin`
＋ 删 `data/f6fb08cc02d24255.patch_13{,.gpu_resources,.stream}`。

#### 3.8.4.25 反向验证：把 AP 地雷阵换成 **AT 雷（`0x032489CF1D439BBA`）** —— "没有实体行"的雷怎么运作（2026-10-26 17:2x，`✓✓` 实机）

毒气雷那一轮（`✓✓`）说明"原生雷互换"成立。这一轮换成 **AT 雷**，因为它有一个反常事实：

**反常：AT 雷在数据里只有 mesh/physics，没有任何实体行**

| 查了什么 | 结果 |
|---|---|
| `Thrower+0x00 = 0x032489CF1D439BBA` 在 56 张表里的出现次数 | **1 次**（就只有 AT 抛洒器自己这一格）|
| `generated_entities` 全文件搜这个 8 字节 | 1 处（同上）；**没有组件行** |
| `generated_entity_deltas` | 0 处 |
| 全库资源（`srkit list --id`）| 只有 `physics` + `mesh` = `les/tank_mine/tank_mine`，**没有 `unit`** |
| 爆炸行 **179**（= AT 抛洒器 `Minefield+0x18`）| **存在**（行 261），且 `+0x38` 粒子 `0x89B5505E263B09ED` **就在 AT 抛洒器的声明包 `12ce4bc7cddaf51c` 里** |

⇒ 表现层（爆炸/粒子）是完整的，**唯独缺"实体行"**（`Unit`/`Explosive`/`Throwable` 那套）。
对照：毒气雷/接触雷的实体行齐全，且它们的**实体 id == 自己包里的 mesh id**（`0x693028644D27FFEF` / `0xEE89CC10D80B6AFB`）；
AT 雷同样是"mesh id = 投掷 id"，只是**没有实体行**。这让两个模型都有可能：

| 模型 | 预测 |
|---|---|
| **M1 资源实体**：抛洒器按"mesh/physics 资源 id"造一个裸件，实体行只是**可选**的组件附加 | 换过去就能出雷、能爆 |
| **M2 实体必需**：抛洒器要按实体行造实体，没有实体行就造不出/不能爆 | 换过去不出雷或不出伤 |

**AT 抛洒器与 AP 的三处结构性差别**（这也是为什么本轮用"整行拷贝"而不是逐字段）：

1. `UnitComponentData+0x00`（**发射器网格 id**）：AT = `0x72E79EF1017A2900`（`mine_launcher_tank_mine`），
   AP/Gas/Incendiary = `0xF00C349422E8E320`（`_launcher/mine_launcher`）⇒ **AT 用的是另一套发射器模型**（本轮保留 AP 的）；
2. `Thrower` 行里 **`+0x7C..+0xEF`（29 个字）与 `+0x150..+0x16C` 在 AT 全为 0**，AP 有值（像是出手/落地特效 id 数组）；
3. `Thrower+0x10/+0x1C/+0x2C` 与 `Minefield+0x04/+0x08/+0x10/+0x20/+0x24` 不同 —— 其中
   `+0x20 = 1`、`+0x24 = 2` **是 AT 独有**（其余三件都是 0），很可能是"资源式雷/场级起爆"的开关。

**两包共享的 9 个资源 id 逐字节相同**（5 animation + bones + state_machine + 2 particles；
`resource.json` 里的差异只是 `source.package`）⇒ **整包驻留没有遮蔽风险**（不会把 AP 发射器的那套资源顶掉）。

**本轮做法：整行拷贝**（新写的 `out/mine-gas/rowcopy.py`，同一套 tail 宿主 + G1/G2/G3/G6/G8/G9 门禁）

| 项 | 值 |
|---|---|
| 改动 | `Thrower` 行与 `Minefield` 行**整行**（752 B / 44 B）从 AT 实体 `0x25A2FD037B6ED25C` 拷到 AP 实体 `0xF00C349422E8E320` |
| 结果 | 装盘回读：AP 的两行与 AT 的两行**逐字节相同**（`✓`）|
| 明文 | `out/mine-gas/ap-to-at.plain` 47,259,408 B（+12）；密封 47,259,456 B，sha256 `066f527c7305ef7a` |
| 驻留 | **`f6fb08cc02d24255.patch_14`** = AT 声明包 `12ce4bc7cddaf51c` 整包 28 条（toc 2,702,160 `53634198541fe163` / gpu 2,847,480 `e345e744fe289f82` / stream 1,747,680 `5bd15fb57f27d17b`）|
| 保留 | AP 的发射器外形与声明包不变（只换"扔什么"）|
| 回滚件 | `out/mine-gas/backup/generated_entities.dl_bin.before-ap2at`（= 毒气雷那一版 `80053101…`）|

**这一局要看的（两件事，一场就能答）**

| 步骤 | 做法 | 看什么 |
|---|---|---|
| **对照（不改数据）** | 带 **MD-17 Anti-tank Mines** 原生战备并投下 | 发射器模型是 `mine_launcher_tank_mine`（与 AP 不同形）；**有没有撒出雷**、雷长什么样、能不能爆 |
| **实验** | 带 **Anti-Personnel Minefield**（已改成 AT 配置）并投下 | 撒出来的是不是 AT 雷（小方盘/楔形），能不能爆 |

判读：

| 档 | 结果 | 结论 |
|---|---|---|
| **A** | 两种都能出雷、都能爆 | **M1 成立**：`Thrower+0x00` 只需要"mesh/physics 资源 id"，实体行是可选附加；AT 的起爆走 `Minefield+0x18 = 179`（场级）|
| **B** | 原生 AT 自己也不出雷/不爆 | 这个 build 的 AT 战备是**数据残件**（stub）；"没有实体行"就是原因，不是我们换坏了 |
| **C** | 原生正常、我们的不出雷 | 除实体行外还差别的 → 下一个嫌疑：`UnitComponentData+0x00`（发射器网格）或 `Minefield+0x04` 那个未知 hash |

**`✓✓` 实机（2026-10-26 17:25）——档 A**：「①② 都能出雷、都能爆」⇒ 反向验证通过，机制见下。

**机理（`✓` 离线 + `✓✓` 行为侧；其中"场级起爆"这一步仍是 ⚠ 单变量未证）**

`Thrower+0x00` 读作"**要生成的资产 id**"，而不是"实体 id"。一个资产 id 下可以挂多个资源
（本 build 的雷都是 **mesh + physics** 同名同 id；发射器则还带 bones / state_machine / physics）。
实体表（`generated_entities`）的作用是**给这个资产附加组件** —— 于是同一个"扔资产"动作有了两种命运：

| 模式 | `Minefield+0x24` | 雷有实体行？ | 谁负责触发/起爆 | 实证 |
|---|---:|---|---|---|
| **实体驱动** | **0** | 有（AP 367 / 毒气 270 / 燃烧 72 三件都齐全）| **雷自己的 `Explosive`（`+0x00 = 2` 接触型）** | 毒气雷 `✓✓`；反向三轮（Thermite 3 / Seeker 自驱 / Lure 4）**扔得出来但不爆** ⇒ 这套模式下布雷器不管起爆 |
| **场级驱动** | **2**（AT 独有）| **无**（全库只有 mesh+physics）| **布雷器自己的 `Minefield` 行：`+0x18 = 爆炸 id`** | 本轮 `✓✓`（原生 AT 与"AP 整行拷贝 AT"都能炸）|

支持"场组件自己能布场+起爆"的硬证据：**13 条 `Minefield` 行的 `+0x18` 全部是合法爆炸 id**
（367 / 270 / 72 / 179 / 230 / 271），其中 **8 条压根没有 `ThrowerComponentData`**
（8 个 `0x0CEDB9E2…`/`0xC12AC9F7…` 之类的预置雷场）—— 它们只能靠 `Minefield` 自己布雷与起爆。
AT 的 `+0x20 = 1` 与那 8 条一致，`+0x24 = 2` 则在 13 条里**独此一家**。

⇒ **"AT 雷没有实体行"不是缺数据，而是另一种设计**：AT 采纳"场级布雷"，雷本体降级为纯资源道具
（只有外观 + 碰撞），触发判定与爆炸参数全在布雷器的 `Minefield` 行里。所以整行拷贝（含 `+0x24=2`）能直接生效，
而只改 `Thrower+0x00`（保留 AP 的 `+0x24=0`）则**预期不出伤** —— 这正是下一轮要钉的那一步：

**② 的实机细节（2026-10-26 17:25 追加）**：撒出的雷**外形与原生 AT 完全一致、爆炸特效也一致**
⇒ ①换 id 确实换了雷（不是回退成 AP 圆盘雷）；②爆炸走的就是**爆炸 179** 那条链
（179 的 `+0x38` 粒子 `0x89B5505E263B09ED` 在 AT 包里，由 `patch_14` 提供）。

**三条排除，把"爆炸 id 来自别处"卡死**（`✓` 离线，可复算）：

| 嫌疑 | 查法 | 结果 |
|---|---|---|
| 雷资产自带爆炸 id | 在 `tank_mine` 的 mesh（138,392 B）与 physics（7,036 B）里找 4 字节对齐的 `179` | **0 处** |
| 抛洒器 `Thrower` 行 | 752 B 里找 179 / 367 / 270 / 72 | **0 处** |
| 布雷器 `Minefield` 行 | 44 B 里找同样四个值 | **只有 `+0x18` 一处** |
| 别处的引用 | 全爆炸表 `+0x24` 有没有实体指向 179 | **没有**（见上文"无实体行"）|

⇒ ② 里那次爆炸只可能来自被整行拷过去的 **`Minefield+0x18`**。

**待验（`⚠`，一字实验，已装盘）**：把 `Minefield+0x18` 从 **179 → 367**（AP 接触雷的爆炸），其余不动。

| 结果 | 结论 |
|---|---|
| 爆炸变成 AP 那种小爆炸/换粒子 | **确认**：爆炸 id 由布雷器行提供，场级起爆闭环 |
| 依旧是大爆炸 | ✗ 爆炸来自别处（雷资产自带或硬编码）⇒ 上面的机理表要改 |

分界：明文的 `Minefield+0x18` 是这 13 行里唯一"每行都指向合法爆炸"的字段，也是 AT 与 AP 之间交换后
唯一改变的爆炸相关字段。回滚件 `out/mine-gas/backup/generated_entities.dl_bin.before-x367`（= 本轮 `✓✓` 那一版）。

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
