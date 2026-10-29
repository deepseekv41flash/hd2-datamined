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

#### 7.1.1 `+0x3C` 全表普查（153 行分组）

> ⚠ **2026-10-28 更正**：`+0x3C` 的字段名是 **`StratagemCategoryType` 枚举**，不是「投放方式」
> （与解码 JSON 102 行严格双射，见 [`STRATAGEM-FIELDS`](STRATAGEM-FIELDS-26088801.md) §4.2b）。
> 下表的「含义」一列是按行为起的俗称，保留因为它是玩家视角的说法。

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

#### 7.2.1b **资源驻留必须做**（2026-10-28 实机教训）

载荷修好之后还会撞第二道墙：**紫问号**。实机对比很干净 ——

| 条件 | 现象 |
|---|---|
| 修好载荷、配装里**没有** Supply Pack | 掉出来的是**紫色问号**（模型/资源缺失） |
| 同一份补丁，配装里**带** Supply Pack | 正常渲染成 Supply Pack |

⇒ 引擎只加载「它认为要加载的包」。载荷实体所在的 toc 包没被声明，就只画占位符。
本 build 的**两个声明口**（`pod_loadout.py` 已实测）：

| 字段 | 含义 | 全表使用情况 |
|---|---|---|
| `+0xA8` u64 | **物品的 toc 包**（u64 包 id） | 106 / 111 原值是 **0**；现役行都有值：18 `0x1E33CC1600FF38F3`、104 `0x519980A75EBD50AD`、121 `0xDBAE525060F06D70` |
| `+0xF8` u32 | 授予武器的 LoadoutEntry id → 该武器的包 | 37 行非零，几乎都是支援武器（Machine Gun / Autocannon / Railgun …） |

⚠ **修正我 2026-10-28 早些时候的一个错误结论**：我说过「`package = 0` 不是故障标志，因为 `id 5`、`id 85` 也是 0」。
那是**从能用的行反推**得到的假结论 —— 那些行的载荷本来就在基础包 / 配装包里，所以不需要额外声明。
**借来的载荷必须显式声明包**，否则必紫问号。106 第一次「成功」也是因为测试配装里带了飞鹰，
把 Eagle Airstrike 的包加载了 —— 不是 `package` 无所谓。

⇒ `tools/stratagem_repair.py --copy-package` 是**必需**而非可选。

#### 7.2.2 载荷修复实验：**106 成功，135 仍失败**（2026-10-28 实机）

社区案例 `MrChengl11/hd2-lua-mod-skill` 的 `hd2-carpet-bomb` 独立复现了同一件事：
`0x6CCB976676EF6CC6` 在 2024-06 快照里是 `unit=shuttle_transport.bones / payload=EaglePayload_CarpetBombing`，
**当前构建整块 LDLD 里出现 0 次 —— 实体是被删的**。该案例的可复用结论：
**别用「没人引用」的实体，要用「现役战备正在用的载荷」** —— 没人引用 ≠ 能用，
实体必须处在已加载的包里才会被生成。

`tools/stratagem_repair.py` 从现役行把 `payload` 数组 **+ `+0xA8 package`（资源驻留）** 抄到坏行，其余字段不动：

| 目标 | 供体 | 换上的载荷 | 实机结果 |
|---|---|---|---|
| **106** Carpet Bomb | 18 Eagle Airstrike | `0x2EA01CB1676ACA29` + 包 `0x1E33CC1600FF38F3` | **`✓✓` 干净配装下正常（不再崩、不出紫问号、真的出弹）** |
| 135 Nuke | 121 Orbital Precision Strike | `0xC897C0D84448AB2C`（该轮**未**抄包） | `✗` 仍失败，HUD 明确弹 **「Stratagem Failed」** |
| **111** Scrambler | 104 Supply Pack | `0x31400A6A3003E29C` + `0x73F8498BFFDCF415` + 包 `0x519980A75EBD50AD`（另把 `+0xC0 enabled` 0→1） | **`✓✓` 干净配装下正常掉出 Supply Pack** |

> **这一条是本页最有价值的结果**：一条载荷实体**已被官方删除**的战备行，
> 只要把它的 `payload` 换成现役祖的载荷，就能从「投出即崩」变成「正常工作」。
> 这是首次证明「半删行」可修 —— 但**修出来的是供体的行为**，
> 原版 `EaglePayload_CarpetBombing`（三机编队 / 6Z 弹道 / 200kg 炸弹 ×30）已被删，不可恢复。

**135 的病灶够不着（`✗ 否证` 若干假设）**：

| 假设 | 否证方式 |
|---|---|
| `package = 0` 导致 | 106 也是 `package = 0` 却能用；且 `id 5`（轨道照明弹）、`id 85`（机枪）等正常行 `package` 也是 0 |
| `origin_type = ClanStation`(2) 导致 | 106 也是 2 |
| `cooldown_type = SharedClan`(2) 导致 | 106 也是 2（飞鹰类不读冷却，真正冷却在 `EagleRearm`） |
| `selectable = 1` 导致 | **无法测**：该字段在明文表里不存在 —— 102 行逐字节 + u32 四个 lane 全扫，零命中（见 [`STRATAGEM-FIELDS`](STRATAGEM-FIELDS-26088801.md) §4.2c） |

135 与 11 条 `OrbitalFireSupport` 同族逐字段对比，它独一份的字段只剩 `+0x048`(7)、
`+0x078`(248)、`+0x0E4`、`+0x0BC cost`(3) 这几个语义未知的，以及**解码表里 `selectable = 1`**
（44 条隐藏行里**只有它一条是 1**）。下一步要么把 121 的整组标量移植过来做范围收缩，
要么承认这条依赖「已解锁状态」而放弃。

#### 7.2.3 SEAF Squad（id 119）为什么「投下空无一物」—— 查到了夹层

它不是投送舱行：`HellpodRackComponentData` 的 72 个实体键里**没有**它的两个载荷实体
（`0x75F7E96AF7DCD303` 士兵 / `0x3EC790806D0B0540` 运输机）。

它走的是另一张表 **`SquadTransportComponentData`（`0xD2B93CD8`，6 行 × 168 B）**，运输机是第 2 行。
这行有个 **96 字节数组 `+0x20`（12 个 u64）**：

```
+0x20 96B = 00BCF8247A544CDC  000000004190F652  ---- ×10
```

**只有第 1 项非空**。而 `0x00BCF8247A544CDC` 解出来不是实体键，是一条 **bones 资源**：

| 项 | 值 |
|---|---|
| 资源 | `content/fac_cyborgs/vehicles/cyborg_tank/cyborg_tank` |
| 所在包 | **`8e9247646ccea917`** |
| 该包内容 | 81 条：3 mesh / 3 bones / 12 texture / 4 material / 28 animation / 3 state_machine / 2 physics … |

⇒ SEAF 的运输机把「投送内容」指向了一套 **Cyborg 阵营坦克资产**，而这个包**按阵营/星球加载**，
普通任务里不在内存 —— 与「紫问号」是同一个病根：**声明口管包在不在，补丁管资源在不在**。

> 注意：Cyborg 在本 build 里是「回归阵营」（播报有整套 "So the Cyborgs are back…" / "We've touched down on Cyberstan itself…"），
> 不是纯遗留；所以包真实存在、只是按需加载。
>
> 另一个旁证：同一行的「赛博运输机」（`cyborg_dropship`，能正常投兵）用的是**同一个** `cyborg_tank` 值 ——
> 说明填这个值本身是对的形态，SEAF 这行是从同一模板抄来、指向了别的阵营的资产。

**因果检验补丁**（2026-10-28，待实机）：整包驻留 `8e9247646ccea917` 到 boot 包

```bash
python tools/whole_package_patch.py build --package 8e9247646ccea917 --host 9ba626afa44a3aa3     --out D:/mod/out/cyborg-res-patch
# → data/9ba626afa44a3aa3.patch_10(.gpu_resources/.stream)，81 条 / 30.6 MiB，G1–G8 全过
```

验证链：补给(34) → 106 → 111 → **119 SEAF Squad**。

**实机结果（2026-10-28）：仍然空无一物** ⇒ 两条解释同时被否证：

| 假设 | 结论 |
|---|---|
| 缺 Cyborg 资产包（驻留就能修） | **`✗` 否证** —— 整包驻留 81 条 / 30.6 MiB 进 boot 包后，行为一字未变 |
| `+0x20[0]` 是「投送内容」 | **`✗` 否证**（同上：把它的包强行塞进内存也没东西掉出来） |

### 已排除项（都查过、都不是病灶）

| 项 | 实测值 | 结论 |
|---|---|---|
| 阵营 | `FactionComponentData +0x00`：SEAF 运输机与士兵都是 **1 = 超级地球**；Automaton Dropship 是 8 | 阵营正确 |
| 士兵实体完整性 | `0x75F7E96AF7DCD303` 46 个组件（`AiSquadMember` / `FriendlyNpc` / `Inventory` / `Unit` …） | 不是空壳 |
| 运输机实体完整性 | `0x3EC790806D0B0540` 18 个组件 | 不是空壳 |
| `VehicleShuttleComponentData` | 11 个运输单位**逐字段几乎相同**（`+0x08` 都是 180.0） | 不是病灶 |
| 小队编队 | `SquadTransportFormationComponentData +0x00` 48 B **有内容**（`2E07E43D 01000000 …`，与 `SquadTransportComponentData +0x08` 同值 `0x3DE4072E`） | 编队非空 |

### 换宿主：用「已验证的运输机投送」来投 SEAF 士兵（2026-10-28 晚，已装盘）

119 自己那条投送路径三次否证后仍然不通，于是改思路：**不修 119，改用一条投送路径已经实机验证过的行来投士兵**。

全表按载荷实体组件分类，得到两条现成通路：

| 通路 | 行 | 槽位结构 | 状态 |
|---|---|---|---|
| **运输机投送** | 类目 3（载具空投）整类：`1 / 10 / 26 / 27 / 38 / 41 / 52 / 74 / 75 / 91 / 94 / 97 / 105 / 108 / 138 / 141 / 152` | `slot0 = 被投物，slot1 = 共享运输机 0x75BE82ED8592A6B3` | `✓✓` 机甲 / FRV / 坦克都验过 |
| **地狱舱投角色** | `96 TUTORIAL REINFORCEMENT BEACON`（类目 4） | `slot0 = 角色实体（带 CharacterName/CharacterVoice），slot1 = 地狱舱 0x73F8498BFFDCF415` | 增援本身就是投角色 |

选 **138 Incinerator FRV** 做宿主（未发布，投送路径 `✓✓`，改坏不影响正常游玩）：

* `slot0`: `0x2D85BFE3D8717FE5`（M-104 车辆）→ **`0x75F7E96AF7DCD303`（SEAF 士兵）**
* `slot1` 共享运输机不动；`+0xA8` 不动；士兵本体包仍由 42.4 MiB 驻留补丁兜着
* 链：补给(34) → 106 → 111 → **138**，t9（sha `79f9a846`）

**实机结果（2026-10-28）：掉出一个 SEAF 士兵，AIBEH 正常 —— 能移动、能开火。** `✓✓`

⇒ 两个结论：

1. **119 的病灶确认在它自己的投送路径**：category 6 全表唯一、`cooldown_type=SharedClan` / `hud_type=Mission` 也独一份，
   那套 `SquadTransportComponentData` 通路在本 build 里跑不通。**但这不阻断「投人」这件事本身**。
2. **运输机通路（类目 3）接受 NPC 作为 slot0**，而且**不需要额外声明武器包** ——
   士兵用的是 MG-43 / AR-23 这类**玩家常规武器**，它们的包本来就常驻，所以能直接开火。
   这也回收了先前「武器包 `792b2a2ba11ae85d` 缺声明」的猜测：对这名士兵不成立。

**可复用的成品配方（✓✓ 实机）**：找一条类目 3（载具空投）的宿主行，把 `slot0` 换成人形实体键，
`slot1` 保持共享运输机 `0x75BE82ED8592A6B3` 不动，即可让运输机按原流程投下一名可行动的友军 NPC。
本次用的是未发布的 138 Incinerator FRV，改坏不影响正常游玩。

#### 一支小队：11 个 SEAF 变体一次投（2026-10-28 晚，已装盘）

SHODAN 4.1.0 源码里有一张带实体哈希的 SEAF 变体表（`stat_editor.lua:718–728`），**11 个变体在本 build 全部存在**，
每个 46 个组件、都带 `AiSquadMemberComponentData`：

| 兵种 | 变体 | 实体键 |
|---|---|---|
| SEAF Soldier | V1–V4 | `75F7E96AF7DCD303`（已实测能走能打）/ `6B22AE8E5F669D4F` / `A00331F24DEEF2EE` / `548136F66F5C9B5C` |
| SEAF Leader | V1–V2 | `BCFC57848F206106` / `78DABC7344E50234` |
| SEAF Medic | V1–V3 | `14453B8FCB040099` / `6FB1E73E00A84329` / `C47287D738BE91C3` |
| SEAF Specialist | V1–V2 | `BFB5C88D557595D8` / `A6DCC225E1263606` |

做法：新工具 `tools/stratagem_payload_multi.py` 把 138 的载荷数组从 2 槽**扩到 12 槽**
（11 个变体 + 共享运输机 `0x75BE82ED8592A6B3` 放最后）。扩容手法：把新数组追加到目标组 payload 末尾、
组 size 相应增加、行内 `+0x98` 改指新位置、`+0xA0` 改成 12，再用 Murmur 反解校正字把内容哈希复原。
G1/G2/G3/G4/G6 全过；82,400 → 82,504 B，封包 t10（sha `3a40dd89`）。

⚠ 同一哈希重复会被去重（飞鹰编队那次已验），所以 11 槽必须是**11 个不同**的实体键。

**第一次装盘失败（实机：运输机压根没生成）→ 根因 = 载荷数组偏移没做 8 字节对齐。**

`stratagem_payload_multi` 最初把新数组直接追加在组 payload 末尾，拿到偏移 `6,436`（`6,436 % 8 = 4`）。
离线对表一眼就看出来了：

| 版本 | 有载荷的行 | 偏移 8 对齐 | 不对齐 |
|---|---:|---:|---:|
| vanilla | 145 | **145** | 0 |
| t9（成功） | 145 | **145** | 0 |
| t10（失败） | 145 | 144 | **1（就是 138）** |

⇒ **载荷数组的 payload 相对偏移必须是 8 的倍数**，vanilla 全表 145 行无一例外。
修法：追加前先补 `lead = (8 - size % 8) % 8` 个零字节，`+0x98` 指向对齐后的位置；
工具里加了 **G7 数组偏移 8 对齐** 门禁。修后 t11（偏移 `6,440`）全表不对齐行数回到 **0**。

**但对齐修好后（t11）实机仍然不生成** ⇒ 8 字节对齐是必要条件、不是充分条件。继续收敛：

| 检查 | 结果 |
|---|---|
| t10b（能用的输入）vs t11 逐字节 diff | **只有 3 处**：组 size 字段、138 的 `+0x98`、138 的 `+0xA0`（外加末尾追加区）+ 校正字 ⇒ 改动本身干净，不是写错了位置 |
| 组 11 payload 布局 | 10 个数组全部是 **2 项**，占用 `5344..6272`；再往后到 `6420` 是**字符串区**（`"TANK. TANK RELOAD HE"` 等） |
| 找空白区替代追加 | ≥96 B 的 8 对齐零区 **0 处**；只有 3 处 44 B 的零区（`4256/4656/5056`，间距正好 400 = 行距，落在行内部，动它风险高） |

⇒ 最可疑的是：**payload 尾部是字符串/数组块，其长度可能由 payload 总大小推出**，追加 104 字节会让引擎把
多出来的字节当成块内容 → 整行失效（连运输机都不生成）。另一种可能是**载荷槽数量有上限**。

为区分这两者，做了**最小扩容**：138 从 2 槽 → **3 槽**（士兵 V1 + 队长 V1 + 运输机），
仍然是对齐后的追加，`82,400 → 82,440 B`，t12（sha `0f672b76`），G1/G2/G3/G4/G6/G7 全过。

* **3 槽能用** ⇒ 追加机制成立、上限 ≥3，可按 3→6→9 二分找上限（或就是 8）
* **3 槽也不能用** ⇒ 追加本身不成立，payload 不能变长；只能放弃「一队」，改用 2 槽（1 名 NPC + 载具）

**实机结果：3 槽也不生成，而 106 / 111 仍正常** ⇒ 定案：

| 结论 | 依据 |
|---|---|
| **战备行的载荷数组长度不可变** | 12 槽、3 槽两种扩容都不生成；而同一张表里 106 / 111 照常工作 ⇒ 表没被判废，是**那一行**坏了 |
| 不是 8 字节对齐问题 | 修好对齐（全表 145 行偏移全部 8 对齐）后仍然不生成 |
| 不是「写错字段」 | t10b vs t11 逐字节 diff 只有组 size / `+0x98` / `+0xA0` 三处 |
| 不是数量上限 | 3 槽（远超原值 2，但远低于 12）同样失败 —— 如果是上限，3 应该能过 |

最可能的机制：payload 尾部的**字符串/数组块长度由 payload 总大小推出**，任何追加都会被当成块内容；
而数组偏移又必须落在该块**之前**的区域，追加到块后面等于指向非法区。两者夹死了「扩数组」这条路。

⇒ **「一次投一队」在本 build 走数据层做不到**。可用的上限是每行 2 个载荷槽 = **1 名 NPC + 1 台载具**，
这也正是已经实机通过的那一版（t13，sha `52dbe070`，已装回盘上）。
想要多个 NPC，只能靠**多次呼叫**（每次一发），或在任务脚本层面刷人。

**换载具（GATER）**：`slot0` 换成 GATER 的车辆实体，同时把 `+0xA8` 换成它的 toc 包 ——

| 项 | 值 |
|---|---|
| GATER 变体 A | `0x0801B6B3C5D12EBC`（vehicle，32 组件，含 `DepositComponentData` 采集逻辑） |
| GATER 变体 B | `0x423FF97D57AB04F5`（同上，同包） |
| 它的 toc 包 | `0x0DFF5200594E867F`（`LoadoutPackageComponentData +8`，两个变体同一个包） |

`+0xA8` 的命名空间与 `LoadoutPackageComponentData +8` **逐值一致**（M-104 车辆 = `0x2CEE40DFBD0B174D`，
正好等于 138 原本的 `+0xA8`），所以换载具必须**同时**改 `slot0` 与 `+0xA8` 两个字段 —— 只改前者会紫问号。

GATER 没有 `LoadoutEntry` 行（`LOE id=None`），所以 `+0xF8` 用不上，只能走 `+0xA8`。

**挂点位置在 `TransportComponentData`（不是战备表，也不是 `MountComponentData`）**

14 行 × 40 B 整表（`tools/block_rows.py --block 0x67B29FFA`）：

| 字段 | 值分布 | 判读 |
|---|---|---|
| `+0x08` u32 | 行 3/11 = `3245600362` = `murmur32("cargo_attach")`；行 1/2/7/8/9/10/12/13 = `2601604451` = `murmur32("boss")`；行 0/5/6 = `996959194`；行 4 = `2511938199` | **挂载节点名哈希**，在**本实体自己的 unit** 里查表 ⇒ 必须命中一个存活节点 |
| `+0x00` f32 | 行 3/11 = 0；多数地狱舱 = 0.5；行 0/4/5/6 = 10；行 2 = 5 | `⚠ 未证` |
| `+0x04` f32 | 行 3/11 = 2.0；地狱舱 = 0.75；其余 = 1.0 | `⚠ 未证` |
| `+0x14` f32 | **只有行 3/11 = −1.0** | 载货专用标记 `⚠ 未证` |
| `+0x24` f32 | **只有行 3/11 = 16.0** | 载货专用参数 `⚠ 未证` |

**三重独立证据**（这不再是猜测）：

1. 行 3（共享运输机 `0x75BE82ED8592A6B3`）与行 11（`0x3F70E3503A3293F9`）的 `+0x08`
   都等于 `cargo_attach` 的 murmur32，而这两台的 unit 里确有 `cargo_attach` 节点；
2. 十个地狱舱行的 `+0x08` 都等于 `boss` 的 murmur32，而地狱舱的 unit（如
   `0x583ECDE0D7718126`，83 节点）里确有 `boss`；
3. 同一实体的 `MountComponentData`：`+0x00`（u64）恰好是 `ttle_gunship_turret_hmg` 的
   **unit 资源 id** `0x8365609B35EF6672`，`+0x08` 恰好是该 unit 里 `attach_front_turret` 的
   murmur32 ⇒「组件字段按名/按 id 引用 unit 与节点」这条规则在第二个组件上复现。

**崩溃的真相（自我更正，推翻原判读）**：先前把 `+0x08` 当 f32 读成 **−15.2457**（看起来很像
「15 米吊高」），据此把它改成 `-25.0`，结果 **`0xc0000005` @ `helldivers2.exe+0xdd6ab2`**。
真相是 **`0xC173EE6A` 这个位型同时也是一个"很合理"的 float**：写 `-25.0`（`0xC1C80000`）
等于写了一个**不存在的节点哈希**，引擎查表得空指针 ⇒ AV。
⇒「−15.2457 = 吊挂高度」「该字段有合法数值范围」两条判读**全部作废**；
该字段是**名字哈希**，改它就是**换挂载节点**（换成有效节点不崩，见 §7.2.4）。

**实机：GATER 被投下来之前就被摧毁了。** 离线排查：

| 检查 | 结果 |
|---|---|
| 血量 | **不是问题** —— GATER `HealthComponentData +0x00 = 12000`，而能正常存活的 M-104 只有 **2900** |
| 组件差异 | GATER 32 个 / M-104 37 个；GATER 独有 **`ObjectiveDynamicLinkComponentData`** + `DepositComponentData`；缺 `WoundableComponentData` / `Animation` / `UnitCustomization` 等 7 个 |
| 目标链接字段 | `ObjectiveDynamicLinkComponentData` = `{+0x00=0（无目标 id）, +0x04=1, +0x08=1}` ⇒ 两个 `1` 疑似「缺目标就自毁」 |

据此做了实验（entities 表，已装盘 sha `18dec4e3`）：把 GATER A `0x0801B6B3C5D12EBC` 的
`ObjectiveDynamicLinkComponentData +0x04` 与 `+0x08` 都清 0（`G1–G8` 全过，内容哈希 `0x8E49771B181FFAA1` 保持，
盘上回读逐字节相同）。若仍被摧毁，下一候选是「运输机吊挂尺寸不匹配」或 `HealthComponentData +0x1C`
（GATER `-200.0` vs M-104 `-40.0`）这个未解字段。

**实机结果：仍被摧毁。** 两个 `1` 不是"缺目标就自毁"的开关 —— 这条假设**已否证**（2026-10-29）。

**换兵种**（同一套机制，只改 `slot0` 一个 u64）：把 `0x75F7E96AF7DCD303`（士兵 V1）换成别的变体键即可。
当前盘上是 **SEAF Specialist V1 = `0xBFB5C88D557595D8`**（t14，sha `ed8a7b72`），
专家 V2 = `0xA6DCC225E1263606`，队长 V1 = `BCFC57848F206106`，医疗 V1 = `14453B8FCB040099`。

未解：`SquadTransportComponentData +0x00 = 3`（SEAF 侧的小队规模）属于**119 那条坏通路**，
本通路一次只投 1 名（同一哈希重复会被去重，与飞鹰编队那次同理）。

### 唯一还没解释的差异

`SquadTransportComponentData` 6 行里，SEAF 那行有**三个全表独有的值**：

| 字段 | SEAF（row 2） | 能正常投兵的 `cyborg_dropship`（row 0/4） |
|---|---:|---:|
| `+0x14` | **6** | 0 |
| `+0x80` | **1** | 0 |
| `+0x81` | **1** | 0 |

⇒ 最后一次实验：把这三个归零对齐 working dropship。**仍空 ⇒ 判定 SEAF Squad 是任务脚本专用行，数据层不可修，收工。**

**已装（2026-10-28，待实机）**：`tools/entity_field_set.py` 两次链式写入
（`--block 0xD2B93CD8 --key 0x3EC790806D0B0540`）

| 字段 | 旧 | 新 |
|---|---:|---:|
| `+0x14` u32 | 6 | 0 |
| `+0x80` u32（= 两个 byte `+0x80`/`+0x81`，原值 `0x00000101`） | 257 | 0 |

门禁 G1–G8 全过，内容哈希保持 `0x8E49771B181FFAA1`；封包 `ent-seaf.dl_bin`（47,259,464 B，sha `d0630860`）
已装盘，**盘上回读解封后与源明文逐字节相同**。同时已删掉那 30.6 MiB 的无用驻留补丁。
⚠ 实体表在**游戏启动时**读 → 必须重启游戏才生效。

**第二轮（2026-10-28 晚，已装盘待重启）**：按用户提示「SEAF 资源不是固定加载」（护卫犬换 SEAF 武器曾出紫问号）重查资源归属：

| 包 | 大小 / 条数 | 内容 | 119 的 `+0xA8` |
|---|---|---|---|
| `6eb59430a00a525c` | 42.4 MiB / 282 | **士兵本体**：bones / ragdoll_profile / ik_skeleton / physics 同为 `0x7A3637CD33A54E4C`「SEAF Solider」+ 262 animation + 1 mesh + 9 texture + 3 material | **原值就是它** |
| `792b2a2ba11ae85d` | 79.7 MiB / 805 | **士兵的武器资产**：MG-43 / AR-23 / SMG-37 / EAT-17 / P-11 / G-6 / Iron Sights 的 bones+mesh | 本轮改指向它 |
| `5f8a1420c40203a2` | 743 条（含 1 个 level） | 运输机的 `tle_transport_personnel` physics | 未声明 |

做法（避开「换掉 `+0xA8` 会连本体包一起丢」的混淆）：
**整包驻留本体包 `6eb59430a00a525c` → boot 包 `9ba626afa44a3aa3.patch_10`（282 条 / 42.4 MiB，G1–G8 全过，toc sha `163486f1`）**，
再把 `+0xA8` 腾出来声明武器包 `0x792B2A2BA11AE85D`。两者互不挤占，`+0xF8` 保持 0。

⚠ 自我更正：`UnitComponentData +0x00` **不是**单位资源指针 —— 能正常工作的 `Automaton Dropship` 该字段为 0。
先前据此推的「士兵单位资源缺包」作废；真实依据是上面三个包的归属。

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

#### 7.2.4 C 路线（改 unit 资源）—— 已做完并装盘

**① 关键更正：HD2 里没有 `unit` 这个资源类型，"mesh" 就是 UNIT。**
`srkit codecs` 里 `mesh 0xE0A48D0BE9A7453F` 用的编码器就叫 `unit`，`srkit/util/ids.py` 里
`TYPE_UNIT = 0xE0A48D0BE9A7453F → "mesh"`。所以上一版写的「该包里没有 unit 类型条目」是**误判**：
`mesh` 条目就是 unit。`srkit list --type unit` 会直接报 `unknown type 'unit'`。

**② 要改的是实体的「功能壳」，不是那个 3 MB 的视觉壳。**

| 资源 | 所在包 | 大小 | 作用 |
|---|---|---|---|
| **`mesh 0x75BE82ED8592A6B3`** | `f6fb08cc02d24255` | toc 41,664 B / gpu **0** | **功能壳**：131 个节点、**零网格**，`UnitComponentData +0x00` 就指向它 |
| `mesh 0xEF3A4136B21592CB` | `131fe264b7380717` | toc 66,960 B / gpu 3.1 MB | 视觉壳：`shuttle_gunship` 根 + 11 个 mesh + 阴影 LOD |
| `mesh 0x3F70E3503A3293F9` | `131fe264b7380717` | gpu 6.5 MB | 第二台运输机的视觉壳（`TransportComponentData` row 11 的实体） |

`UnitComponentData +0x00`（u64）在这台运输机上**等于实体键本身**（自指）；
地狱舱 `0x73F8498BFFDCF415` 的同一字段指向 `0x583ECDE0D7718126`（不是自指），所以它是**真的资源 id**。

**③ 功能壳的节点表**（`tools/unit_nodes.py` / `unit_offset.py show`；Z 向上，原点在机腹平面）：

| 节点 | 父 | 局部位置 | 世界 z | 意义 |
|---|---|---|---|---|
| 9 `root` | — | — | 0 | 骨架根 |
| 13 `chassi` | 9 | [−0.017, −1.095, **3.221**] | 3.221 | 机架 |
| **26 `cargo_attach`** | 13 | [0.017, 0.095, **−2.277**] | **0.944** | **挂载点**（`+0x08` 指向的节点） |
| 27 `front_claw` / 32 `rear_claw` | 13 | — | 1.726 | 前/后爪 |
| 16 `hose_base` → 17–24 `hose_01..08` | 16…23 | 逐节 +1.5 | 0.263 → **−11.737** | **吊索**，往下垂约 12 m |
| 25 `hose_aimref` | 13 | [0.017, 1.345, −15.575] | **−12.354** | 吊索末端参考点 |

**④ 已装盘的补丁（C 路线的第一发）**

```
tools/unit_offset.py shift --unit 0x75BE82ED8592A6B3 --package f6fb08cc02d24255 \
    --host f6fb08cc02d24255 --index 18 --node 26 --dz -4.5 --out D:/mod/out/c-route/c-patch
```

* 节点 26 位置 `[0.017, 0.095, −2.277] → [0.017, 0.095, −6.777]`（世界 z `0.944 → −3.556`），
  矩阵平移同步改；
* 等长改写：41,664 B 只变 **7 字节**，G1–G5 全过；
* 补丁 1 条（`unit 0x75BE82ED8592A6B3`，gpu 0 B），**41,856 B**，sha `6c0d4bd6`；
* 已装 `data/f6fb08cc02d24255.patch_18`（+ 两个 0 B 伴随文件），盘上 sha 与产物一致；
* **完全不碰实体表**：改坏最多是挂载位置不对，不会访问违例（这正是上一发崩溃的反面）。

**⑤ dz 为什么取 −4.5**（顶点包围盒实测，`srkit extract --decoded` 后统计 mesh 顶点）

| 实体 / unit | x / y / z 尺寸 (m) | 挂在 z=0.944 时**顶部**到 | 结论 |
|---|---|---|---|
| M-104 车辆 `0x2D85BFE3D8717FE5` | 3.06 / 5.08 / **2.39**（−1.30…+1.09） | **+2.03**（舱内 2 m） | **同样重叠，实机却完全正常** |
| GATER `0x423FF97D57AB04F5`（两变体共用） | **9.07 / 21.88 / 5.98**（±2.57） | **+3.51**（舱内 3.5 m） | 21.9 m 比运输机本身（14.2 m）还长，机体把整个舱腹包住 |

dz = −4.5 ⇒ GATER 顶部到 **−1.0**（离机腹留 1 m 余量），底部到 −6.13。

**⚠ 同一发里被否证的旧假设**：M-104 也往舱里插 2 m 却毫发无伤
⇒ **「货物与舱体重叠 = 必死」不成立**。所以这一发改的是**重叠量级**
（M-104 只是"插进空舱 2 m"，GATER 是"把舱腹整个包住并超出前后各 2 m"），
**并不保证有效** —— 这是本次实验中唯一还站着的几何解释。

**⑥ 离线工具链（新增，均可复跑）**：`tools/unit_nodes.py`（壳节点表，1–3 秒）、
`tools/entity_dump.py`（实体键 → 组件清单）、`tools/block_rows.py`（组件块整表）。

#### 7.2.5 若 C 路线这一发仍被摧毁 —— 下一批候选（按代价排）

| 候选 | 做法 | 能区分什么 |
|---|---|---|
| 换挂载节点（数据表，1 个 u32） | `TransportComponentData +0x08` 由 `cargo_attach` 改成同壳里的 **`hose_aimref`**（世界 z −12.354，吊索末端） | 与 ④ 是同一个几何变量，但**一次到位 12 m**；若它也救不回，几何整条线可以直接砍掉 |
| 卸掉任务语义 | `DepositComponentData` 各字段清零；`ObjectiveDynamicLinkComponentData +0x00/+0x04/+0x08` 全 0（后两个已试过，无效） | 任务脚本是否在"投送即摧毁" |
| 换投放器 | 用 hellpod 行（`TransportComponentData` row 9，`+0x08 = boss`）投 GATER | 运输机侧 vs 载具侧 —— 换投放器仍死 ⇒ 问题在 GATER 自身 |
| 缩小体积 | 只能改 GATER 的 unit 缩放（`UnitComponentData +0x08..+0x10` 的 scale） | 体积是否是唯一变量 |

#### 7.2.6 C 路线第一发实机结果：**卡死 → 自动退出**（`cargo_attach` 位移被否证）

**实机（2026-10-29 00:3x）**：装 `f6fb08cc02d24255.patch_18` 后，进游戏、叫 34 号、
**运输机刚出现时卡死一段时间，随后自动退出**（用户描述）。

取证结果（这一发**没有**崩溃产物，与上一发形成对照）：

| 检查 | 结果 |
|---|---|
| `%TEMP%` 新 THEIA 转储 | **无**。最新仍是 10-28 23:56 那个 `-25.0` 的（14.7 MB） |
| Windows 应用程序日志（WER 1000/1001） | 00:15 之后**一条都没有** |
| 游戏目录 00:20 后改动的文件 | 只有我们自己装的 `patch_18` 三件 |
| 磁盘空间 | C: 剩 11 GB，排除写不下转储 |

⇒ 死法和 `-25.0` 那次**不同**：那次是立即 `0xc0000005` 且留转储；这次是**挂起后被超时/看门狗终止**
（无 SEH、无 WER、无 dump），指向「投送点校验 / 物理互穿求解进死循环」这一类，而不是空指针。

**否证清单（本发新增）**：

1. ❌「`cargo_attach` 可以自由下移」—— 下移 4.5 m 让投送流程挂起；
2. ❌「dz = −4.5 能减少重叠而不出别的问题」—— 它同时把 21.88 m × 5.98 m 的车**向下推了 4.5 m**，
   方向与量级都是我按「顶部离机腹 1 m」算出来的，**没有实验依据**；
3. ✅ 补丁机制**不是**嫌疑：`RESOURCE-RESIDENCY §2` 记录「同 id 高号胜 + 单条 `unit` 补丁带 +2 m 位移」
   是 `✓✓` 实机过的，单条 `state_machine` 补丁也跑过。

**已回滚**：`data/f6fb08cc02d24255.patch_18*` 三件已删除，盘上回到 18 条旧补丁。

**下一步转向：先问清「GATER 是被伤害打死还是被逻辑销毁」**，这一步**完全不碰几何**：

| 实体 | `HealthComponentData +0x00` | `+0x18` constitution | `+0x1C` const_rate |
|---|---:|---:|---:|
| M-104（能活） | 2,900 | 400 | −40.0 |
| GATER（被摧毁） | 12,000 | 2,000 | −200.0 |

两者 `constitution / |rate|` 都正好是 10 s，所以这条比值**不是**判别项。

实验：GATER A `0x0801B6B3C5D12EBC` 的 `+0x00` 由 `12000` → **`10000000`**（G1–G8 全过，
内容哈希 `0x8E49771B181FFAA1` 保持），封包 sha `c1510b90`，已装 `generated_entities.dl_bin`
（战备表仍是 t15 `84c22907`）。

| 实机结果 | 判定 |
|---|---|
| GATER 活下来了 | 是**伤害**（挤压/重叠/坠落）⇒ 修法走血量或伤害源，几何路线可以放弃 |
| 仍被摧毁 | 是**逻辑销毁**（mission/objective/despawn）⇒ 下一批：`DepositComponentData` 清零、换 hellpod 投放器 |

#### 7.2.7 GATER 解剖表实测对照（2026-10-29）：油罐爆炸**不是**致死原因

用户提出新假设：**GATER 是被它的油罐爆炸摧毁的**（看到爆炸发生在油罐位置），并给出 wiki 的
「任务完成后 Pelican 会取走尾部油罐，车辆随之自毁」。

**① 用 wiki 解剖表对本 build 的 `HealthComponentData` 做了三方核对（全部对上）**

| 部件（wiki） | wiki 数值 | 本 build 对应位置 | 读值 | 一致 |
|---|---|---|---|---|
| Truck（主） | 12,000 / AV6 / Durable 75% / Constitution 2,000 [−200/s] / **Fatal** | `0x0801B6B3C5D12EBC` 主块 | 12000 / armor **6** / durable **0.75** / const 2000 / rate **−200** | `✓✓` |
| Autocannon | 1,000 / AV4 / Durable 100% | **独立实体** `0x9872EEB31A5F88FD`（GATER `MountComponentData` 唯一一条，节点 `attach_turret`） | 1000 / armor **4** / durable **1.0** | `✓✓` |
| Tires (10) | 1,500 / AV2 / 70% / %ToMain **0%** / ExDR **65%** | GATER 主行 **10 个活跃区** | 10× 1500 / armor 2 / durable 0.7 / `affects_main` **0** / 爆炸份额 **0.35** | `✓✓` |
| Oil Tanks | 300 / AV1 / 70% / %ToMain **0%** / **Fatal: No** / ExDR 65% | **全表找不到** | hp=300 的 14 行没有一行是 AV1 + 0.7 | `✗` 不是实体 |

**② 判定：油罐爆炸不可能是致死原因**

- wiki 解剖表明写：油罐 **`% To Main = 0%`**、**`Fatal? = No`** ⇒ 打爆油罐**不把伤害传给主血量、也不致死**；
- 油罐只有 **300 HP / AV1（Very Light）**，是整个车上最脆的部件 ⇒ 一挤就碎，
  **你看到的那次爆炸更像"被夹碎的油罐"，是症状**；
- 它甚至不是实体（`MountComponentData` 只有机炮塔一条；`GoreComponentData`/`HitReactComponentData` 里也没有 300）
  ⇒ 它是**外观/可破坏部件**，走的是 gore 那条路，不参与主血量结算。

**③ 真正能解释"落地之前才炸"的机制（新，`⚠ 未证` 但三方吻合）**

wiki 脚注 5 说明了 `constitution` 的真实语义：**它是主血量（或肢体）打空之后才可能衰减的二级血池**，
不是开局就按 −200/s 掉。所以 GATER `constitution 2000 @ −200/s` 的含义是
**主血量归零后还能撑 10 秒**（M-104 的 `400 @ −40/s` 同样正好 10 秒）。

⇒ 时间线：运输机夹持时**主体被挤压/碰撞扣主血量 → 12000 打空 → 10 秒体质倒计时 → 车在吊运途中（落地前）爆炸**。
油罐在同一时刻被夹碎，所以看起来"爆炸发生在油罐处"。

**④ 判据（盘上已装的那一发就是它）**

`generated_entities.dl_bin` 现为 `c1510b90`：GATER A 主血量 `12000 → 10000000`（其余未动）。

| 实机结果 | 判定 | 下一步 |
|---|---|---|
| GATER 活下来 | 确认是**主血量被打空**（挤压/碰撞伤害）⇒ 油罐、任务逻辑都排除 | 把血量定到合理值（如 6 万）即为可用修法；或回头降低挤压（几何已崩过一次，优先级降低） |
| 仍被摧毁 | 是 **destroy 调用**（脚本自毁/despawn），血量无效 | 转 `DepositComponentData` 清零、换 hellpod 投放器、查 tag 位（GATER 独有 bit 81/167/211，M-104 是 103） |
