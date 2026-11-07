# Booster 线收口（build `26251122` / 表 `26088801`）

> **一句话**：Booster 的定义不在 `generated_*.dl_bin`，而在 `game.dll` 的 21 行硬编码表
> （`0x2CB4840`，步长 `0x38`）；每行 = `itemId` + **granted StratagemType（`+0x04`）** +
> **调谐标量（`+0x08`，f32）** + 10 个 locid。**表里没有指针**——标量由代码消费，最终**落到**
> 明文表的字段（`AvatarComponentData` 等）或整行（爆炸/状态/实体/战备）。
> 数据侧能做的三件事：**解锁**（代理注入 `cat 5`）、**改已定位的落点**、**等效替代**；
> **不能**新增 Booster、改 `+0x04` 映射、改 `+0x08` 标量（那要动 `game.dll`，见 §5）。

## 0. 三态

| 结论 | 态 | 依据 |
|---|---|---|
| Booster 定义在 `game.dll` 硬编码表，不在任何 `generated_*` 表 | **✓ 离线** | 55 张明文表对 20 个 itemId **0 命中**；表本体可直读 |
| `+0x08` 是**标量**，不是指针/索引 | **✓ 自证 + 结构** | 整行无 64 位槽；值域含 0.05/0.15/0.35 等分数；`FLEXIBLE 0.75 ↔ wiki 2:00→1:30` 逐值吻合 |
| `+0x04` = granted `StratagemType`（0 = 无） | **✓ 自证** | 全表仅 `SURPLUS EAT` 非零 = `15` = 那条战备复制体的 stratagem id |
| 20 条本地定义 / 目录 30 条 / 10 条本地无定义 | **✓ 离线** | 目录 `cat 5` 30 条，表覆盖 20 条，剩 10 条全 `game.dll` 0 命中 |
| 5 条落点在明文表且已闭合 | **✓✓** | Firebomb `83` / Stun `335` / Concealed `401`(中置信) / ARP 实体 / Surplus EAT 战备 15 |
| 其余 15 条的数值落点 | **✗/⚠ 未定位** | 见 §2 表末列；多数是代码常量或运行期状态，不在已映射的明文表里 |

## 1. 定义源与两张清单

```
game.dll @ 0x2CB4840, stride 0x38, 21 行（idx0 = NO BOOSTER）
  +0x00 u32  itemId（= 目录 cat 5 的 mixId）
  +0x04 u32  granted StratagemType（0 = 无；全表只有 SURPLUS EAT = 15）
  +0x08 f32  tuning scalar
  +0x0C u32  恒 1
  +0x10..  10 × u32 locid（名称/标题/描述…）
```

| 清单 | 数量 | 说明 |
|---|---:|---|
| 本地定义（`game.dll`） | **20** | 实际可用的 Booster |
| 服务端目录（`/api/Progression/items` 的 `progressionCategory=5`） | **30** | 代理注入可解锁，但本地无定义的 10 条效果/名字会异常 |
| 本地无定义的 10 条 | — | `196883860 767342143 1046516979 1175500164 1195476753 1607993656 2031253145 2262930209 3126789594 3224102862` |

机器可读表：[`refs/boosters-26088801.json`](../refs/boosters-26088801.json)。

## 2. 全表（20 条 + 落点/证据）

| # | Booster | itemId | +0x04 | +0x08 | 数据侧落点 | 证据 |
|---:|---|---:|---:|---:|---|---|
| 0 | NO BOOSTER | `2747100039` | 0 | 1 | — | 占位 |
| 1 | VITALITY ENHANCEMENT | `1110686504` | 0 | 0.9 | 代码：受击伤害入口 ×(scalar) | ⚠ 第三方旧 build 语义（wiki 标 90%，本仓库未自核） |
| 2 | STAMINA ENHANCEMENT | `684729784` | 0 | 1.3 | `AvatarComponentData +0x34..+0x5C`（时长/消耗） | ✓ 字段已定位；÷vs× 方向 ⚠ 单源 |
| 3 | MUSCLE ENHANCEMENT | `2776452811` | 0 | 0.35 | 未定位（avatar 表无通用地形减速倍率） | ✗ 落点未定位 |
| 4 | UAV RECON BOOSTER | `4136928865` | 0 | 1.5 | 未定位（雷达扫描，客户端） | ✗ 落点未定位 |
| 5 | INCREASED REINFORCEMENT BUDGET | `4066886572` | 0 | 1 | 未定位（每玩家增援数） | ✗ 落点未定位 |
| 6 | FLEXIBLE REINFORCEMENT BUDGET | `4273318008` | 0 | 0.75 | 未定位（回援冷却） | ✓✓ 语义已自核：wiki 2:00→1:30 = ×0.75 |
| 7 | HELLPOD SPACE OPTIMIZATION | `1908198785` | 0 | 1.5 | 未定位（出舱满补给） | ✗ 落点未定位 |
| 8 | LOCALIZATION CONFUSION | `876985512` | 0 | 0.9 | 未定位（生成率） | ✗ 落点未定位 |
| 9 | EXPERT EXTRACTION PILOT | `3504405746` | 0 | 0.7 | 候选：战备行「Extraction」的 `+0x84` 呼叫延迟 | ⚠ 候选未证 |
| 10 | MOTIVATIONAL SHOCKS | `2709264466` | 0 | 0.5 | 候选：StatusEffect `8 Slowed`（`+0x20` = 0, 0.4, 4.0）/ `68 FlamerSlowed` | ⚠ 候选未证 |
| 11 | EXPERIMENTAL INFUSION | `3912131454` | 0 | 1 | 代码选 StatusEffect **29**（替代 25） | ✓ 本 build status 29 存在（tick 0，参数 0/0.25/0） |
| 12 | FIREBOMB HELLPODS | `3102833400` | 0 | 1 | **爆炸 83 → 伤害行 438**（Fire 20） | ✓✓ 本仓库 + wiki 逐字段 |
| 13 | SAMPLE SCANNER | `336215081` | 0 | 0.15 | 未定位（样本掉落概率阈值） | ✗ 落点未定位 |
| 14 | DEAD SPRINT | `2239116615` | 0 | 0.05 | 未定位（血量地板；状态 id 未定） | ✗ 落点未定位 |
| 15 | ARMED RESUPPLY PODS | `3793458484` | 0 | 0 | **实体 `0x73681FFD58FA1A90`**（代码生成炮塔） | ✓ 本仓库双源（同族对照 + 包邻接） |
| 16 | SAMPLE EXTRICATOR | `796779894` | 0 | 10 | 未定位（样本掉落上限） | ✗ 落点未定位 |
| 17 | STUN PODS | `1151328602` | 0 | 1 | **爆炸 335 → 伤害行 439**（Stun Massive 100） | ✓✓ 本仓库 + wiki 逐字段 |
| 18 | CONCEALED INSERTION | `1602836857` | 0 | 1 | **爆炸 401 → 伤害行 0**（半径 5/5/0，纯烟雾） | ⚠ 中置信（无 wiki 数值；旧号 400 不采纳） |
| 19 | INTEGRATED EXTINGUISHERS | `3545987157` | 0 | 0.5 | 未定位（燃烧衰减 ×1/(1-v)；候选 StatusEffect 5 `Fire`） | ⚠ 候选未证 |
| 20 | SURPLUS EAT ALLOCATION | `1213901450` | **15** | 1 | **战备 15** `TEAM WEAPONS. EXPENDABLE ANTI-TANK (Booster)` | ✓✓ 本仓库（两条独立行 + `max_uses=2`） |

## 3. 机制四形态（决定"能不能在数据侧改"）

| 形态 | 判定 | 本表里的 Booster | 数据侧可改? |
|---|---|---|---|
| **A. 标量 × 明文字段** | 代码读字段基值，再乘/除标量 | 1 2 3 4 6 8 9 10 19（9 条）| **字段可改、Booster 的倍率不可改**；改字段 = 等效替代 |
| **B. 标量作阈值/计数** | `random < v` / `count < int(v)` / 血量地板 | 5 13 14 16（4 条）| 只能改被比较的那个量，改不了阈值 |
| **C. 无标量：代码按字面 type 选明文整行** | 硬编码字面量 | 11 12 17 18（4 条）| **能改整行**（爆炸/伤害/状态）← 已闭环 |
| **D. 数据引用** | 数据里直接给 | 15 20（2 条）| **能改目标**（实体/战备）← 已闭环 |

⇒ 数据侧真正"能改到 Booster 本体效果"的只有 **C + D 共 6 条**（11/12/15/17/18/20）；
A/B 两类只能改它们读的基值（等效替代），改不了 Booster 自己的倍率。

## 4. 已闭合的 5 条特例（细节不在此重复）

| Booster | 结论 | 文档 |
|---|---|---|
| SURPLUS EAT ALLOCATION | 发的是**专用战备复制体**（id 15，`max_uses=2`），不污染原版 EAT-17（id 151） | [GAME-DLL-CATALOGS §5.5](GAME-DLL-CATALOGS-26088801.md) |
| ARMED RESUPPLY PODS | 无战备复制体；代码在补给舱落点生成独立炮塔实体 `0x73681FFD58FA1A90`（140 发 / 640 rpm / AIBEH 214 / 无装填） | [GAME-DLL-CATALOGS §5.6](GAME-DLL-CATALOGS-26088801.md) |
| FIREBOMB / STUN / CONCEALED | 爆炸 `83` / `335` / `401`，伤害行 `438` / `439` / `0`；三条都是弹丸表 0 引用的代码触发行 | [POD-IMPACT-EXPLOSIONS](../explosions/POD-IMPACT-EXPLOSIONS-26088801.md) |
| 标量与耐力那条映射 | `+0x08` 是标量；耐力基线在 `AvatarComponentData +0x34..+0x5C`；`1.3` 的方向仍未证 | [BOOSTER-MAPPING](BOOSTER-MAPPING-26088801.md) |

## 5. 能力边界

| 想做什么 | 能不能 | 怎么做 / 为什么不能 |
|---|---|---|
| 解锁某条 Booster（含目录里 10 条无定义的）| **✓** | 代理注入 `cat 5` 一行 inventory（已实机） |
| 改 Firebomb / Stun / Concealed 的伤害·半径·状态 | **✓** | 改爆炸行 + 伤害行（保内容哈希） |
| 改 ARP 炮塔的弹量/射速/索敌/寿命/AIBEH | **✓（⚠ 未实机）** | 改实体 `0x73681FFD58FA1A90` 的组件行 |
| 改 Surplus EAT 的"给几次" | **✓** | 改战备行 15 的 `+0x058 max_uses` |
| 让任意投送舱带炮塔 / 带爆炸 | **✓（数据侧三档做法）** | 见上一轮结论：追加载荷对 / 杂交实体 / 全局 hellpod 补组件 |
| 等效替代 A 类 Booster（如耐力） | **✓** | 改 `AvatarComponentData` 的基值字段 |
| **改 Booster 的倍率本身（`+0x08`）** | **✗** | 在 `game.dll` 的明文 `.data` 段 —— 但文件带 Authenticode 签名、受 EAC 保护，且字段是否被消费离线不可证 ⇒ 默认不碰（[GAME-DLL-PLAINTEXT §4.1](GAME-DLL-PLAINTEXT-26088801.md)） |
| **新增 / 删除 Booster 行** | **✗** | 同上（要动 `game.dll`） |
| **改 `+0x04`（booster → 战备）映射** | **✗** | 同上；但可以直接改那条战备行本身（C/D 形态）绕过去 |
| 运行时读/写这些数值 | **✗** | 本代 build 无存活通道（[MEMORY-ACCESS §12f](../boundaries/MEMORY-ACCESS-25988413.md)） |

## 6. 仍未解（按"值得做"排序）

| # | 未解项 | 下一步怎么找 |
|---:|---|---|
| 1 | **A 类 9 条的标量落点**（尤其 MUSCLE 0.35、UAV 1.5、EXPERT EXTRACTION 0.7）| 先从 `generated_scenario_settings`（27 组）/`generation_settings` 里按语义找；或按 wiki 数值（30%/50%/30%）反查 f32 |
| 2 | **耐力 1.3 的方向（÷ vs ×）** | 只需**游戏内掐表**：基线 23 s，期望 29.9 / 36.6 / 17.7 s 三档（见 BOOSTER-MAPPING §3.3）|
| 3 | **Concealed Insertion = 401** 的一分钱验证 | 改 401 的半径或粒子，看落舱烟变化 |
| 4 | **DEAD SPRINT 的状态 id** | 本 build 里 status 59 每跳伤害为 0，541 属于 status 36（Arc）；需按"掉血曲线"重新定位 |
| 5 | 目录 10 条无定义 Booster 的注入表现 | 代理侧逐条注入、看客户端是否报错/空白（低优先）|
| 6 | `HELLPOD SPACE OPTIMIZATION` 的"出舱满补给"落点 | 弹药储备 + `LoadoutEntry` 两条线交叉（参考 WEAPON-AMMO-RESERVE）|

## 7. 复现

```bash
# 表本体（21 行）
python out/_scratch/boosters_closeout.py          # 生成 refs/boosters-26088801.json + 上表

# 直接读（只依赖 game.dll）
python - <<'PY'
import struct, pathlib
b = pathlib.Path(r"D:/SteamLibrary/steamapps/common/Helldivers 2/data/game/game.dll").read_bytes()
for i in range(21):
    o = 0x2CB4840 + i*0x38
    item, g4 = struct.unpack_from('<2I', b, o)
    print(i, item, g4, struct.unpack_from('<f', b, o+8)[0])
PY
```

## 8. 交叉引用

- [GAME-DLL-CATALOGS](GAME-DLL-CATALOGS-26088801.md) §5（表本体 + §5.5 EAT + §5.6 ARP + §5.7 落舱爆炸）
- [BOOSTER-MAPPING](BOOSTER-MAPPING-26088801.md)（标量语义、四种映射形态、耐力专题、旧 build 口径）
- [POD-IMPACT-EXPLOSIONS](../explosions/POD-IMPACT-EXPLOSIONS-26088801.md)（三条落舱爆炸逐字段）
- [AVATAR-HELLDIVER-FIELDS](../cases/AVATAR-HELLDIVER-FIELDS-26251122.md)（耐力等 A 类落点字段）
- [GAME-DLL-PLAINTEXT §4.1](GAME-DLL-PLAINTEXT-26088801.md)（为什么 `game.dll` 不改）
- [MEMORY-ACCESS §12f](../boundaries/MEMORY-ACCESS-25988413.md)（为什么没有运行时路线）
