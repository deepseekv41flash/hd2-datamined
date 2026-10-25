# 侦察 + 实现：战备表的「额外战备」`+0xC8`（把未发布战备带进任务）

> **一句话**：SHODAN-Stat-Editor v4.1.0 的「额外自选战备」= 往 `StratagemInfo +0xC8`（`additional_stratagem`）
> 写**另一条战备的 id**；带上宿主战备时，引擎把这条额外战备一起给你，**不占 4 个配装位**，而且会顺着
> extras 一路跟（**成环 → 任务开始崩溃**）。这是**纯数据表**字段（file route），不是运行时补丁。
> 我们已离线做出补丁（`M-104 Incinerator FRV` = 战备 id **138**），**尚未装盘**（等实机判定未发布战备是否被拒）。
>
> 样本：SHODAN-Stat-Editor-Offline **v4.1.0**（GitHub release，zip sha256 `3174425d3939bec3…`）
> 抽出位置：`D:/mod/recon/shodan-stat-editor/v4.1.0/`（**只读**：未运行 exe、未改 `data/`）

---

## 1 结论先看

| 问题 | 结论 | 态 |
|---|---|---|
| 额外战备写的是哪个字段 | `StratagemInfo +0xC8`（=200）u32，值 = 目标战备的 `+0` id；0 = 无 | **✓ 离线**（源码 + 本 build 数据双向对上） |
| 它占配装位吗 | **不占**（作者注释：`It doesn't take a loadout slot, but the HUD's stratagem list can fill up`） | ✓ 源码注释 |
| 引擎真的用它吗（我们的 build） | **是**：全部 Eagle 行 `+0xC8 = 51`（`EAGLE. REARM`）—— 原版就在用这条链 | **✓ 离线**（153 行逐行读） |
| 能附带未发布战备吗 | **机制上能**（值是任意战备 id），但**未发布战备会不会被任务开始校验拒绝**：**未证** | ⚠ 待实机 |
| M-104 Incinerator FRV 在本 build 里存在吗 | **存在**：战备 id **138**、key `0xA9A97CD7`、实体 `0x2d85bfe3d8717fe5`（`frv_flamer`） | **✓ 离线** |
| 是 A 档（dl_bin）还是 C 档 | **A · dl_bin 等价**（只写一个 u32 + 保内容哈希） | ✓ 离线门禁 G1–G7 |

## 2 第三方 mod 的机制（源码级）

`app/stat_editor.lua`（1.23 MB，源码随包发布；md5 `70caf0ff…`）：

```lua
-- Extra stratagem (issue #64): StratagemInfo +200 additional_stratagem, a stratagem type (+0) given along when
-- this one is in your loadout (the Eagles' is Eagle Rearm, so they are offered as extras only). The choices:
-- every stratagem the game has (mission and President's reward ones too: the Dark Fluid and Medic backpacks
-- work, tested), by name; 0: none. A choice that leads back to the stratagem is refused.
function MOD.extra.row(entry, def)
    local row = add_row(entry, 'Extra stratagem', 'extra', 'Extra stratagem (choice)', 'u32',
                        { part('extra', def.kind, def.off + 200, 'u32', 100000) }, 0, 100000, 1, 10)
```

配套逻辑：
- **环检测**：`MOD.extra.refused()` 顺着 `+200` 链走，回到自己就拒绝 —— 注释写明
  「the game follows extras with no end, **and crashes as the mission starts**; tested」。
- **选择范围**：所有战备（含任务用、总统奖励用）；作者实测 Dark Fluid / Medic 背包可用。
- **UI**：每行一个「Extra stratagem」选择器（0 = 无）。

同一版本里另外两处和战备行有关（顺带记下）：
- `StratagemInfo +260`（`+0x104`）= 车辆种类位：`0x100000` 外骨骼 / `0x200000` FRV / `0x400000` 坦克；
  「一套配装每种车只带一台」就是这几位，清掉即可多带（该开关注明在内存里改）。
- `StratagemInfo +368`（`+0x170`）bit `0x02` = 战备球弹跳（与我们 VPM 侦察的结论一致）。

## 3 本 build（26088801）数据核对

`generated_stratagem_settings.dl_bin`：12 组 / **153 行 × 400 B**（组内 16 B 头 + 行 + 组尾 blob）。

| 项 | 值 |
|---|---|
| `+0x00` | 条目 id（1 基连续，1..153） |
| **`+0xC8`** | **额外战备 id**（Eagle 全家 = 51 = `EAGLE. REARM`；其余 142 行为 0） |
| `+0x104` | 车辆种类位（M-102 `0x200820` / M-103 `0x204020` / **M-104 `0x200060`** / 坦克 `0x401820`） |
| `+0x170` | 低字节标志位（`0x02` = 战备球弹跳） |

**目标：M-104 Incinerator FRV**

| 项 | 值 | 来源 |
|---|---|---|
| 战备 id | **138** | 本表 `+0x00`（行 #142，组 11） |
| 物品 key | `0xA9A97CD7` | 本表 `+0x04`；**全明文表里只出现这一处**（= 它自己的 key） |
| 载荷实体 | `0x2d85bfe3d8717fe5` | 行 `+0x98` 指向的 8 字节数组（= 资源 `.../vehicles/frv/frv_flamer`） |
| 实体存在性 | `generated_entities.dl_bin` 里该 hash **39 处引用** | mmap 扫 47 MB 明文 |
| 第三方 mod 的编号 | `strat = 135`（它自己的 game.dll 战备表序号，**不是** `+0` id）、`key = 0xA9A97CD7` ✓、`record = 0xDA0600D7`（运行时物品注册表用，明文表里 0 命中） | `settings.UNLOCKS` |

⚠ 注意「**解锁未发布物品**」是另一条路：SSEO 的 `settings.UNLOCKS` 在**运行时**往物品注册表插行
（`registry()` / `add_row` / `api.write`），README 也写明「unlocking unused items need the running game」⇒ 那是 **L4**。
本页的**额外战备**是**纯数据**：只写 `+0xC8`。

## 4 我们的实现（已做，未装盘）

工具：`tools/stratagem_extra.py`（列表 / 查找 / 写入 / 环检测 / 封包）

```bash
python tools/stratagem_extra.py --show                 # 153 行：id / 名字 / 当前额外战备
python tools/stratagem_extra.py --find FRV             # id 108 / 26 / 138
python tools/stratagem_extra.py --host 121 --extra 138 --out out/stratagem-extra/strat-m104.plain --seal
```

产物：`out/stratagem-extra/strat-m104.dl_bin`（82,440 B，sha256 `ac7c2e53a1d2e23c…`）

| 门禁 | 结果 |
|---|---|
| G1 长度 = 原长 + 对齐 + 8 | PASS（82,384 → 82,392 明文；封包 +48） |
| G2 差异 ⊆ 声明字段 ∪ 尺寸 ∪ 校正字 | PASS（diff=2） |
| G3 重算 Murmur64A == 原值 | PASS（`0x04BBE33EF809862A`） |
| G4 目标字段读回 | PASS（`138`） |
| G5 其余字节未动 | PASS |
| G6 容器自洽、无尾部残留 | PASS |
| **G7 环检测** | PASS（另测 `--host 51 --extra 31` 正确拒绝） |

改动内容：`ORBITAL. PRECISION STRIKE`（id **121**）`+0xC8: 0 → 138`。

**装盘（等你说）**：
```bash
python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin     --sealed out/stratagem-extra/strat-m104.dl_bin
# 回滚
python tools/dlbin_deploy.py restore --file generated_stratagem_settings.dl_bin
```

## 5 试验设计（一局判三件事）

1. 配装：带 **Orbital Precision Strike**（+ 任意 3 个）进任务；
2. 看战备条：是否出现第 5 个图标（M-104），图标/名字是否正常（未发布会显示什么？）；
3. 按呼叫码叫车：
   - 车出来了 ⇒ **未发布战备可用，A 档闭环**（数据就能带未发布战备）；
   - 图标在但叫不出来 / 报不可用 ⇒ 任务开始有解锁校验，需要运行时（**C 档**：解锁那一步）；
   - 完全没有图标 ⇒ `+0xC8` 对未发布目标被过滤（要换宿主或换目标再试），仍属数据侧可查。

## 6 风险与已知

| 风险 | 说明 |
|---|---|
| **环路崩溃** | 引擎顺着 extras 无限跟，成环在任务开始崩（作者实测）。工具 G7 已挡 |
| **HUD 挤满** | 额外战备不占配装位，但 HUD 战备条会变长（作者注释） |
| 未发布战备的解锁校验 | 未知；本页 §5 就是判它的 |
| 与 4 槽上限的关系 | 4 个自选位不变；额外的是「跟着来」的第 5、6… 条 |
| 联机 | 只改本机数据；队友看不到你的额外战备（他们各自的表） |

## 7 三态

| 结论 | 态 |
|---|---|
| 额外战备 = `StratagemInfo +0xC8`（另一条战备的 `+0` id），不占配装位 | **✓ 离线**（源码注释 + 本 build Eagle 全部 = 51） |
| 引擎会在配装里跟随 extras 链（成环崩溃） | **✓ 离线**（源码注释，作者实测；本 build 原版 Eagle 链在用） |
| M-104 = 战备 id 138 / key `0xA9A97CD7` / 实体 `frv_flamer` 在本 build 完整存在 | **✓ 离线**（表 + 实体表双向） |
| 写 `+0xC8` 一个 u32 即可、保内容哈希 | **✓ 离线**（G1–G7 全 PASS） |
| 未发布战备能作为额外战备进任务并呼叫 | **⚠ 待实机** |
| 「解锁未发布物品」（让它在军械库可选）可以离线做 | **✗ 不能**（SSEO 走运行时物品注册表，L4） |
