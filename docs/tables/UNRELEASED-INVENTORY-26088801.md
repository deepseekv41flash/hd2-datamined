# 未发布内容全量盘点（build 26088801）

> **只读侦察**：读本 build 已解密明文缓存 `D:/mod/refs/dlbin/plaintext-26088801/generated_*.dl_bin`、
> 本 build 的英文本地化表、SHODAN Stat Editor 4.1.0 的名称表，以及本地 wiki 镜像。未启动游戏、未改任何数据。
>
> 三态：`✓ 离线` = 本 build 数据独立证明；`✓✓ 实机` = 已在游戏里实测；`✗ 否证` = 查过不成立；`⚠ 未证` = 查过但结论不确定。
>
> **一句话结论**：把「有名字 / 有实体 / wiki 怎么记」三条判据叠起来，本 build 里**真正未发布的战备是 10 行**
> （9 行 wiki 完全不记载 + 1 行 wiki 记载但自己标 `source = N/A`），**真正未发布的装备是 5 件**。
> SHODAN 作者另外独立标了 4 件「游戏有但不提供」，与我们 4/4 全部对上。

---

## 0 结论速览

| 层 | 总数 | 未发布 | 判据 |
|---|---:|---:|---|
| 战备行（`stratagem_settings`） | 153 | **10** | 玩家向 + wiki 无记载 / wiki 标 `source = N/A` |
| 可装备实体（`generated_entities`） | 219 | **5** | 有 code + 有名字 + wiki 无任何记载 |
| 无名字行 | 153 | **8** | `name_id` 与 `upper_id` 在本 build 字符串表**都不存在** |

未发布的 10 行战备 **10/10 全部实机验证可用**（走 `+0xC8` 额外战备链；最后 3 行于 2026-10-28 一局验完，§7.1）。

---

## 1 五个数据源各自能给什么

| 源 | 文件 | 规模 | 能给 | 不能给 |
|---|---|---:|---|---|
| 本 build 战备表 | `generated_stratagem_settings.dl_bin`（经 `tools/stratagem_extra.py --show`） | 153 行 | 行 id、内部 debug 名、`name_id`/`upper_id` | 哪些行进得了军械库 |
| 本 build 本地化 | `refs/strings-en-26088801.json` | 24 834 条 | 「这一行到底有没有名字」的**硬证据** | 名字属于哪一行（要自己按 id 绑） |
| 本 build 实体表 | `refs/entity-locid-names.json` → `entity_index` | 1 939 实体（219 可装备） | 装备的 `code`+`name`+`loadout_tags`+实体 key | 是否可购买（采购在服务器侧） |
| **本地 wiki 镜像** | `refs/wiki/pages/*.wikitext`（763 页）<br>`wiki/index.json`（370 页）<br>`refs/wiki/cat_*.json` | 80 战备页 / 39 武器页 / 35 支援武器页 | ①是否有页面 ②页面 infobox 的 `source` = **wiki 自己给的「怎么获得」** | 比 build 旧约 3 周 |
| **SHODAN 4.1.0** | `stat_editor.lua` | 3 480 条 EN→ZH 名称对 + `settings.UNLOCKS` | ①中文名 ②作者标注的「游戏有、不提供」清单 | 不给行 id |

### 1.1 wiki 镜像的 `source` 字段是决定性判据

每个战备页有 `{{Infobox Stratagem | ... | source = ... }}`。把 763 页全解出来：

| Infobox | 页数 | `source` 有值 | `source = N/A` | 无 `source` 字段 |
|---|---:|---:|---:|---:|
| Stratagem | 80 | 59 | **1** | 20（任务物件 / 舰船基础项） |
| Weapon | 39 | 36 | 0 | 3 |
| Support Weapon | 35 | 35 | 0 | 0 |
| Throwable | 23 | 23 | 0 | 0 |

**全镜像只有一页写 `source = N/A`：`M-104 Incinerator FRV`** —— 页面正文也写着
"At this time, the Incinerator FRV is unavailable for use."。这正是我们自己实机测出来能带能叫、
但军械库里买不到那台车。**wiki 的 `source = N/A` = 我们的「实机可用但未发售」，两个独立来源互证。**

反例校准：同一批新内容里 `G-11 Caltrops` / `AMW-20 Apex` / `LAS-44 Nova` 的 `source` 分别写着
`Scope of Authority Premium Warbond` 第 1/2/3 页 —— 所以“wiki 有页面”**确实**能区分已发售与未发售。

---

## 2 SHODAN 名称表 → 153 行：8 个「无名行」的真相

`refs/stratagem-display-names.json` 里 8 行 `name_status = unknown`。SHODAN 4.1.0 的 zh-Hans 名称表
对这 8 行**都有条目** —— 但把行里的 `name_id` / `upper_id` 拿去本 build 的字符串表里对，**全部落空**：

| 行 id | 内部名 | SHODAN 给的英文 | `name_id` | `upper_id` | 本 build 字符串里有吗 |
|---:|---|---|---|---|---|
| 36 | `EAGLE. (NOT USED) ADDITIONAL STRAFING RUNS` | (Not Used) Additional Strafing Runs | 2283799497 → ✗ | 3236255620 → ✗ | **✗ 没有**（SHODAN 自己意译的） |
| 114 | `MISSIONS. IMMEDIATE EXTRACTION BEACON` | Immediate Extraction Beacon | 3901583393 → ✗ | 491152859 → ✗ | **✗ 没有** |
| 135 | `MISSIONS CLAN STATION. Nuke` | Nuke | 3894610137 → ✗ | 3599477113 → ✗ | ✗ 该行没有（但独立字符串 `NUKE` 存在） |
| 89 | `MISSIONS. REMOTE EXPLOSIVES` | Remote Explosives | 2294760818 → ✗ | 249660316 → ✗ | **✗ 没有** |
| 119 | `SEAF Squad` | Seaf Squad | 2400957530 → ✗ | 799126270 → ✗ | ✗ 该行没有（独立字符串 `SEAF Squad` 存在） |
| 48 | `TANK. TANK RELOAD HE` | Tank Reload HE | 2664466741 → ✗ | 1462990578 → ✗ | **✗ 没有** |
| 98 | `TANK. TANK RELOAD AT` | Tank Reload AT | 3778618418 → ✗ | 386985065 → ✗ | **✗ 没有** |
| 62 | `TANK. TANK RELOAD CANISTER` | Tank Reload Canister | 527728115 → ✗ | 861212028 → ✗ | **✗ 没有** |

**结论（`✓ 离线`）**：这 8 行的 `name_id` 和 `upper_id` 在本 build 的 24 834 条英文字符串里**一条都找不到**
—— 它们**真的没有本地化名字**，不是我们解析链漏了。SHODAN 的 8 个名字是它按 debug 名做的意译
（它自己的 `lower` 表里还有正则 `'^MISSIONS CLAN STATION%.%s*(.+)$' → '空间站任务：%1'`，就是这么拼出来的）。

**这条解释了实机现象**：id 36 带进游戏后「图标借 Eagle Strafing Run、名字空白」——因为本 build 里它压根没有名字。
而同批的 id 25/35/36/64/81 都有完整 `name_cased` + `name_upper`，带进去就正常显示。

> **判据要按两个字段算**：`name_id` **和** `upper_id` 都不在字符串表里才算「真无名」。
> 只查 `name_id` 会把 `MEDIC BACKPACK`(id 20) 这种「只有大写名」的行误判成无名 ——
> 它有 `upper_id 2927578997 → 'MEDIC BACKPACK'`，进游戏是能显示名字的。
> 同批的 id 25/35/36(Confetti)/64/81 则 `name_cased` + `name_upper` 都齐，实机也确实正常显示。

---

## 3 战备行 × wiki：玩家向未发布 10 行

判据：内部名不是 `MISSIONS.*` / `MISSIONS CLAN STATION.*` / `TANK.*` / `TUTORIAL` 前缀（那些是任务物件，本来就不发售），
且 wiki 镜像里**没有一件战备页**（`wiki/index.json` 370 页 + `cat_stratagems`/`cat_weapons` 分类成员 +
763 页正文全文搜索，三路都查）。全文命中只有两处**语料巧合**、不是条目：
`Medical Supplies` 出现在 M-103 补给 FRV 的描述句 "…replenish ammunition and medical supplies on the move" 里，
`SEAF Squad` 出现在 SEAF 部队部署机制的叙述里 —— 都是普通名词，不是战备条目。

| id | 行号 | 内部名 | 显示名（中文） | wiki | 判据 | 实测 |
|---:|---:|---|---|---|---|---|
| **36** | 24 | `EAGLE. (NOT USED) ADDITIONAL STRAFING RUNS` | （无名字） | 无 | 内部名自带 `(NOT USED)`；名字双缺 | `✓✓` 能带能叫，效果 = Eagle Strafing Run，只有 4 次、Rearm 不补 |
| **150** | 25 | `EAGLE. (NOT USED) AIR-TO-AIR MISSLES` | Eagle Air-to-Air Missiles（空对空导弹） | 无 | 内部名自带 `(NOT USED)` | `✓✓` 有名字有图标，能用；⚠ 会锁地面目标 |
| **50** | 35 | `EAGLE FLY BY` | Eagle Fly By（飞鹰掠过） | 无 | 无 wiki 页 | `✓✓` 有名字有图标，纯演出 |
| **145** | 36 | `ORBITAL CONFETTI` | Orbital Confetti（轨道彩纸礼花） | 无 | 无 wiki 页 | `✓✓` 有名字有图标，能用 |
| **64** | 81 | `ORBITAL. WALKING BARRAGE SMOKE` | Orbital Walking Barrage Smoke（移动弹幕烟雾） | 无 | 无 wiki 页 | `✓✓` 有名字有图标，能用 |
| **80** | 14 | `CONSUMABLES. HEALTH PACK RACK` | Medical Supplies（医疗补给） | 无 | 无 wiki 页 | `✓✓` 有名字有图标，可用 |
| **93** | 87 | `PRESIDENT REWARDS. HEALTH PACK RACK` | Medical Supplies（医疗补给） | 无 | 无 wiki 页 | `✓✓` 可用（与 80 同名，出现两条是预期） |
| **20** | 89 | `PRESIDENT REWARDS. MEDIC BACKPACK` | MEDIC BACKPACK（`B/MED-18` 医疗背包） | 无 | 无 wiki 页 | `✓✓` 可用 |
| **119** | 147 | `SEAF Squad` | （无名字） | 无 | 名字双缺 | `✓✓` 能带能叫，但运输机投下空无一物 |
| **138** | 142 | `VEHICLES. FAST RECON VEHICLE (Ramming Flamethrower)` | Incinerator FRV（炽灼型 FRV） | **有页** | **`source = N/A`** | `✓✓` 车辆正常投放能开；军械库无此车 |

### 3.1 两条新的机制旁证（`✓ 离线`）

本 build 的字符串表里，这几条**事件发放提示**存在，说明「未发布」里有一部分其实是**限时 / 事件赠予**，不是废弃内容：

| 字符串 | 指向 |
|---|---|
| `The Eagle Air-to-Air Missiles stratagem is temporarily available to all Helldivers.`（1495667994 / 2069818539） | id 150 是**限时开放**过的战备，配套还有 `... availability has ended.`（830957581） |
| `<i=1> Free Medical Supplies</i> stratagem on all missions.`（1483406869） | **Medical Supplies 是任务修饰符赠予**的免费战备 —— 所以 id 80/93 的「未发布」是「不常驻商店」 |
| `Helldivers will be given <i=1>#V_TWO free uses</i> of the <i=1>Resupply Stratagem</i> each mission.`（991129614） | 同一族修饰符写法（`#V_TWO` 是数值占位） |

同族还有 88 条 `... is temporarily available to all Helldivers.` + 44 条 `... availability has ended.`，
覆盖的都是**已发售**战备（Eagle Airstrike、Orbital Laser、Resupply…）—— 即「限时免费」是通用机制，
不是未发布内容的特征。所以**不能只凭这条字符串判未发布**，只能当旁证。

---

## 4 装备层：219 个可装备实体里 5 件 wiki 无记载

`generated_entities.dl_bin` 里带 `loadout_type` 的实体 219 个（primary 59 / support 46 / backpack 36 / sidearm 28 /
throwable 27 / vehicle 20 / other_item 3）。对 wiki 匹配后 35 个没页面，剔掉三类噪声后剩 **5 件**：

剔掉的是：① 支援武器/载具的**子部件**（`Autocannon Backpack`、`Spear Backpack`、`Solo Silo Targeting Remote`、
`Larva Container`、`Cargo Truck` 等 18 个）；② **无名占位**实体（名字是 `未知`，是 SEAF 的 AI 操作版副本，
SHODAN 用正则 `'^(.+) %(SEAF%)$'` 渲染它们，共 12 个）。

| 实体 | 类别 | 实体 key | loadout_tags | wiki | SHODAN `UNLOCKS` | 判定 |
|---|---|---|---|---:|---|---|
| `P-41 Ombudsman`（巡察者） | sidearm | `0xBDE1F2534280300D` | HEAVY ARMOR PENETRATING / ONE HANDED / ROUNDS RELOAD | 无 | **✓ 标了** | `✓ 离线` 未发布手枪 |
| `LAS-22 Shear`（切变） | primary_weapon | `0x7E3145A5BAA4B948` | LIGHT ARMOR PENETRATING / BEAM / HEAT | 无 | **✓ 标了** | `✓ 离线` 未发布主武器（激光连续光束） |
| `AR-23L Liberator Legacy`（解放者·传承） | primary_weapon | `0xB80951732A5F58F4` | LIGHT ARMOR PENETRATING | 无 | ✗ 没标 | `✓ 离线` 有实体有名字，wiki 零记载 |
| `SG-8F Punisher fire of liberty` | primary_weapon | `0xBCC2177439D231BE` | ROUNDS RELOAD / LIGHT ARMOR PENETRATING | 无 | ✗ 没标 | `✓ 离线` 有实体，**连 fluff 文案都有**（`Punisher fire of liberty Fluff`，1817621264） |
| `SH-20 MEDIC BACKPACK` | backpack | `0x0A55E504092B981D` | — | 无 | ✗（但名称表有 `Medic Backpack`） | `✓ 离线` 就是战备行 id 20 的载体（`B/MED-18 MEDIC BACKPACK`，1016262718） |

> **`SG-8F Punisher fire of liberty` 值得注意**：名字里有 `fire of liberty`（自由之火），且带完整 fluff 文案。
> 这是**写完了但没上线**的典型形态 —— 文案都写了，只是没进商店。

---

## 5 SHODAN `settings.UNLOCKS` 交叉验证

SHODAN 4.1.0 里有一段作者注释与表：

```lua
-- unlocks: items the game has but does not offer, by id, on / off (settings.unlock, below).
settings.UNLOCKS = {
    { id = 'incinerator', name = 'M-104 Incinerator FRV', config = 'incinerator_frv',
      strat = 135, key = 0xA9A97CD7, record = 0xDA0600D7 },
    { id = 'ombudsman', name = 'P-41 Ombudsman', config = 'unlock_ombudsman',
      model = { 0xBDE1F253, 0x4280300D }, template = { 0x05E4E5C2, 0xDB6E44A2 } },
    { id = 'caltrops', name = 'G-11 Caltrops', config = 'unlock_caltrops',
      model = { 0x2968DEBA, 0x6D6C2F09 }, template = { 0x4CE9EAB7, 0x85A79B7B } },
    { id = 'shear', name = 'LAS-22 Shear', config = 'unlock_shear',
      model = { 0x7E3145A5, 0xBAA4B948 }, key = 0x7DE53646, template_key = 0xE673DCC8, class = 1 },
}
```

把它的 `model` 高/低 32 位拼起来，和本 build 的实体 key 逐个比：

| SHODAN `UNLOCKS` | 拼出的实体 key | 本 build 实体表 | 我们的独立判据 | 吻合 |
|---|---|---|---|:--:|
| M-104 Incinerator FRV | 战备 key `0xA9A97CD7` | 车辆实体 `0x2D85BFE3D8717FE5`（strat 135） | wiki `source = N/A` + 实机可叫但买不到 | `✓` |
| **P-41 Ombudsman** | `0xBDE1F2534280300D` | **正好是** sidearm `0xBDE1F2534280300D` | wiki 零记载 | `✓` |
| G-11 Caltrops | `0x2968DEBA6D6C2F09` | **正好是** throwable `0x2968DEBA6D6C2F09` | wiki 有页，`source = Scope of Authority 第 1 页` | **已发售** |
| **LAS-22 Shear** | `0x7E3145A5BAA4B948` | **正好是** primary `0x7E3145A5BAA4B948` | wiki 零记载 | `✓` |

**4/4 实体 key 精确命中**，说明 SHODAN 的清单和我们的实体索引是同一套数据。
其中 `G-11 Caltrops` 是**已经发售**的（当前 Warbond「Scope of Authority」第 1 页），
说明 SHODAN 这张表是**累计表、不随发售删条目** —— 所以**不能直接拿它当「未发布」结论**，
要用 wiki 的 `source` 字段再过滤一次。这一步正好把我们筛到 3 件（Ombudsman / Shear / M-104）。

---

## 6 「真未发布」总表

把 §3、§4、§5 三张表并起来，去掉已发售与任务物件，本 build 的未发布内容就是这 14 项
（10 件战备 + 4 件装备；`B/MED-18` 同时占战备与背包两侧，合并成一行）：

| # | 名字 | 层 | id / key | 状态 |
|---:|---|---|---|---|
| 1 | （无名）Additional Strafing Runs | 战备 | id 36 | `✓✓` 实机可带可叫 |
| 2 | Eagle Air-to-Air Missiles | 战备 | id 150 | `✓✓` 实机可带可叫（限时开放过） |
| 3 | Eagle Fly By | 战备 | id 50 | `✓✓` 实机可带可叫 |
| 4 | Orbital Confetti | 战备 | id 145 | `✓✓` 实机可带可叫 |
| 5 | Orbital Walking Barrage Smoke | 战备 | id 64 | `✓✓` 实机可带可叫 |
| 6 | SEAF Squad | 战备 | id 119 | `✓✓` 可带可叫，**投下空无一物**（半成品） |
| 7 | Medical Supplies（`CONSUMABLES. HEALTH PACK RACK`） | 战备 | id 80 | `✓✓` 实机可用（2026-10-28） |
| 8 | Medical Supplies（`PRESIDENT REWARDS. HEALTH PACK RACK`） | 战备 | id 93 | `✓✓` 实机可用（2026-10-28） |
| 9 | `B/MED-18` MEDIC BACKPACK | 战备 + 背包实体 | id 20 / `0x0A55E504092B981D` | `✓✓` 实机可用（2026-10-28） |
| 10 | M-104 Incinerator FRV | 战备（载具） | id 138 / 车辆 `0x2D85BFE3D8717FE5` | `✓✓` 实机可带能开；wiki `source = N/A` |
| 11 | P-41 Ombudsman | 副武器 | `0xBDE1F2534280300D` | `⚠ 未证`（需要实体解锁路线，不是战备路线） |
| 12 | LAS-22 Shear | 主武器 | `0x7E3145A5BAA4B948` | `⚠ 未证` |
| 13 | AR-23L Liberator Legacy | 主武器 | `0xB80951732A5F58F4` | `⚠ 未证` |
| 14 | SG-8F Punisher fire of liberty | 主武器 | `0xBCC2177439D231BE` | `⚠ 未证` |

> 第 11–14 项走的是**装备解锁路线**（SHODAN 的做法：复制同族装备的注册表行），
> 不是「额外战备」路线；本页只做盘点，路线见
> [`RECON-SHODAN-EXTRA-STRATAGEM`](../cases/RECON-SHODAN-EXTRA-STRATAGEM-26088801.md)。

---

## 7 还没实机测过的（可上机清单）

### 7.1 未发布战备 —— 已清零（2026-10-28 一局验完 3 行）

剩下的三行于 2026-10-28 用**一条链**（`Resupply(34) → 80 → 93 → 20`）一局测完，用户回执
**「全都可以正常用」** ⇒ 三行全部 `✓✓ 实机`。结构与结果：

| id | 内部名 | 显示名 | 投放 | 次数 | 冷却 | 结果 |
|---:|---|---|---:|---:|---:|---|
| **80** | `CONSUMABLES. HEALTH PACK RACK` | Medical Supplies（医疗补给） | 2 | ∞ | 300 s | `✓✓` 有名字有图标，可用 |
| **93** | `PRESIDENT REWARDS. HEALTH PACK RACK` | Medical Supplies（与 80 同名） | 2 | 1 | 30 s | `✓✓` 可用 |
| **20** | `PRESIDENT REWARDS. MEDIC BACKPACK` | `B/MED-18` MEDIC BACKPACK | 2 | 1 | 600 s | `✓✓` 可用 |

配方（留档，实测有效）：

```bash
python tools/stratagem_extra.py --chain 34:80,93,20 --out out/stratagem-extra/medical.plain --seal
python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin     --sealed out/stratagem-extra/medical.dl_bin --accept-current
```

**由此得到一条可用的通用规律**（`✓✓ 实机`）：`+0x3C 投放方式 = 2`（投掷/空投）的未发布行
**一律能叫、且真的掉东西**；唯一失败的是 `投放方式 = 6` 的 `SEAF Squad`(119)（有呼叫流程、投下空的）。
⇒ 以后判断「这条未发布行值不值得试」，先看 `+0x3C`，命中 `2` 就基本稳。

#### 7.1.1 `+0x3C 投放方式` 全表普查（153 行按投放方式分组）

把 153 行全按 `+0x3C` 分组，再叠上「这一组里有多少条已经实机通过」，判据就变成一句话
——**只有 `6` 是坏的，`0/1/2/3/4/5` 每一组都有实机通过的成员**：

| `+0x3C` | 含义 | 行数 | 已实机通过的成员 | 未测成员 |
|---:|---|---:|---|---|
| 0 | 飞鹰空投 | 12 | 8 条已发布 + id 36 / 150 / 50 | **106（Carpet Bomb）** |
| 1 | 轨道 | 11 | 10 条已发布 + id 145 / 5 | **135（CLAN STATION Nuke）** |
| 2 | 投掷/空投 | 94 | 大量已发布 + id 80 / 93 / 20（2026-10-28） | — |
| 3 | 载具空投 | 17 | M-102/103/104、EXO×4、任务物件若干 | 任务物件 |
| 4 | 信标 | 11 | Extraction / Upload Data / ACTIVATE DRILL / CALL IN SUPER DESTROYER / Reinforce 等 7 条已发布 | **127（Reinforcement Beacon）**、**48 / 98 / 62（坦克换弹）** |
| 5 | 行走弹幕 | 6 | 5 条已发布 + id 64 | — |
| 6 | （SEAF 专用） | 1 | **无 —— id 119 是唯一失败样本**（投下空无一物） | — |
| 7 | Eagle Rearm | 1 | 已发布 | — |

⇒ 判「这条未发布行值不值得试」：先看 `+0x3C`，**是 `6` 就别试**；但 `+0x3C` 只是第一道闸 ——
还要叠上 §7.2.1 的**载荷实体存在性**（106 / 135 就是投放 0/1 正常、载荷悬空而废的）。

⚠ 链式会覆盖中间行原有的 `+0xC8`；测完记得回原版（见
[`UNRELEASED-STRATAGEMS-26088801`](UNRELEASED-STRATAGEMS-26088801.md) §5.2 的「每条宿主只挂 1 条」做法）。

### 7.2 任务物件行：106 / 135 / 127 已实机（2026-10-28，**三条全废**）

按 id：`106`（CLAN STATION 地毯轰炸）、`127`（REINFORCEMENT BEACON）、`135`（CLAN STATION Nuke）
是这批里结构最像「叫东西下来」的三条。实测结果**三种症状各不相同**：

| id | 名字 | 投放 | 实机现象 | 根因层 |
|---:|---|---:|---|---|
| **106** | Carpet Bomb | 0 飞鹰空投 | 能按，**投出瞬间崩溃** | **载荷实体悬空**（`0x6CCB976676EF6CC6` 在 `generated_entities` 里 0 次引用） |
| **135** | （无名） | 1 轨道 | 能按，**投出后什么都不会发生** | **载荷实体悬空**（`0x3FED8E4A3B242F02` 同样 0 次引用） |
| **127** | Reinforce | 4 信标 | **有图标但按不动** | 载荷**存在**（3 次引用）⇒ 缺的是**呼叫前置**（任务状态/上下文），不是载荷 |

**同样是「载荷不存在」，投放方式决定表现形式**：`0` 飞鹰空投会去起一个载机 → 解引用空指针 → **崩**；
`1` 轨道从地图外抛射、着弹才需要实体 → 没人来接 → **静默无反应**。这条是 `⚠ 未证`（机制解释，未做对照实验）。

其余 31 条任务行是终端/钻机/旗帜/摄像机一类；坦克换弹子项 `48 / 98 / 62` 无载荷数组、6 s 冷却，不建议花时间。

#### 7.2.1 新增判据：先查「载荷实体存不存在」

`+0xC8` 只能证明「带得进去」，**证明不了「叫得出来」**。离线可查的第二道闸是载荷引用：

```
战备行 +0x98 = {u64 payload 相对偏移, u32 数量} → 8 字节实体哈希数组
                                          ↓
              每个哈希在 generated_entities.dl_bin 里数 u64 小端出现次数，0 次 = 悬空
```

全表 153 行扫下来**只有 3 行悬空**：

| id | 名字 | 投放 | 悬空哈希 | 实机 |
|---:|---|---:|---|---|
| 106 | Carpet Bomb | 0 飞鹰 | `0x6CCB976676EF6CC6` | `✓✓` 崩（已测） |
| 135 | （无名） | 1 轨道 | `0x3FED8E4A3B242F02` | `✓✓` 静默（已测） |
| **111** | Scrambler | 2 投掷 | `0xA2945F73F912004D` | **`⚠` 未测 —— 可用来验证「投放方式决定表现形式」这个解释** |

对照：`18 Eagle Airstrike`（0 飞鹰，载荷 18 次引用）与 `121 Orbital Precision Strike`（1 轨道，5 次引用）
载荷都在，都正常工作 —— 所以「投放 0/1 本身不能叫」是错的，坏的是**那两行的载荷引用**。

工具：`python tools/stratagem_payload_check.py`（默认只列悬空行，`--all` 全表）。

---

## 8 判据边界

| 结论 | 强度 | 说明 |
|---|---|---|
| 153 行、219 实体、3 480 名称对 | `✓ 离线` | 直接来自本 build 明文表，可重跑复核 |
| 8 行「真无名」 | `✓ 离线` | `name_id` 与 `upper_id` 双缺失，24 834 条字符串里都没有 |
| 10 行玩家向未发布 | `✓ 离线` | wiki 页面、分类成员、763 页正文全文三路都 0 命中 |
| M-104 `source = N/A` | `✓ 离线` + `✓✓ 实机` | wiki 自己写的 + 我们实机可叫但买不到 |
| 5 件未发布装备 | `✓ 离线`（存在）+ `⚠ 未证`（是否明天就发售） | 装备存在、名字完整；「发售没发售」只有服务器商店知道 |
| 第 11–14 项能否实际拿到 | `⚠ 未证` | 本页只盘点，没试解锁 |

**已知的两个边界**：

1. **wiki 镜像比 build 旧约 3 周**（页面缓存 2026-09-30，分类成员 2026-10-22）。若某件东西在这窗口内发售，
   我们会把它误判成未发布。本 build 里最可疑的是 `AR-23L` / `SG-8F fire of liberty`（名字带 `Liberator Legacy`
   / `fire of liberty`，像自由日档期内容）。
2. **本 build 里还有一批老名字字符串**（`GL-6 Grenade Launcher`、`AT-48 Recoilless Rifle`、`RS-422 Railgun`、
   `ST-1 Stinger`、`SAR-1 Sniper Rifle`、`TS-4 Arc Thrower`、`Defense Wall`）—— 这些是**改名前的遗留**，
   不是未发布内容。它们和现名（`GL-21`/`GR-8`/`RS-422`）指同一件，判据上没有意义，已排除。

---

## 9 复现

```bash
# 全量盘点（本页所有数字）
python tools/unreleased_inventory.py --json-out out/unreleased/inventory-26088801.json
```

工具做的事：跑 `tools/stratagem_extra.py --show` 拿 153 行的表内 id → 用 `name_id`/`upper_id` 去
`refs/strings-en-26088801.json` 查名字（判「真无名」）→ 解 `refs/wiki/pages/*.wikitext` 的
`{{Infobox Stratagem|Weapon|Support Weapon|Throwable}}` 拿 `source` 字段（判「可不可获得」）→
把 `entity_index` 的 219 个可装备实体逐个对 wiki（判「装备层未发布」）→ 从 SHODAN
`stat_editor.lua` 抽 zh-Hans 名称表与 `settings.UNLOCKS`。

依赖：本 build 的明文缓存（`refs/dlbin/plaintext-26088801/`）、本地化表、wiki 镜像、
SHODAN 4.1.0 目录。全是本地文件，不联网、不启游戏。
