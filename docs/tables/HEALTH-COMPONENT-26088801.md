# HealthComponentData 字段表（build 26088801）

> **一句话**：`HealthComponentData` 是**主血量块 + 1 个默认区 + 38 个伤害区槽**的结构，
> 每行 **22,096 B**、伤害区从 `+520` 起、每槽 **552 B**。武器/载具/敌人/哨戒/可部署物**共用这一套 schema**。
>
> 三态：`✓✓` 实机验证过（HD2Runtime 的 live evidence）· `✓ 离线` 本 build 数据复核 · `⚠ 未证` 只有名字没验证。

## 1 几何

| 项 | 值 | 证据 |
|---|---|---|
| 类型哈希 | `0xB3915DE3` | `✓ 离线`（typelib + 本 build 明文） |
| 行大小 | **22,096 B** | `✓ 离线` |
| 行数 | 506 行（keyed 哈希图） | `✓ 离线` |
| 伤害区槽 | **38 个**，从 `+520` 起，每槽 **552 B** | `✓ 离线`（与 HD2Runtime 文档一致） |
| 区是否启用 | 区 `+96` 非 0 | `✓ 离线`（SHODAN 用同一判据） |

## 2 主块字段

| 偏移 | 类型 | 名字 | 含义 | 证据 |
|---:|---|---|---|---|
| `+0x000` | u32 | `health` | **主血量池** | `✓✓` 实机（敌人实测改过，载具 gameplay-proven） |
| `+0x004` | f32 | `regeneration` | **每秒回血** | `✓ 离线`（SHODAN `h+4`） |
| `+0x018` | u32 | **`constitution`** | **体质**（成员名 `constitution`，len 12） | `✓ 离线`（HD2Runtime schema + 本 build 复核） |
| `+0x01C` | f32 | **`constitution_rate`** | **体质速率**（成员名，len 23） | `✓ 离线` |
| `+0x030` | u32 | `KillScore` | 击杀计分（敌人用） | `✓ 离线`（HD2Runtime `events.md`） |
| `+0x10C` (268) | f32 | `durable_resistance` | **默认区耐伤比例 0–1**（1 = 只吃 durability 伤害） | `✓ 离线` |
| `+0x118` (280) | u32 | `armor` | **默认区护甲 0–10** | `✓✓` 实机（载具区护甲 gameplay-proven） |
| `+0x120` (288) | u32 | `max_armor` | 护甲上限（HD2Runtime `0.28.1` 报告用过） | `✓ 离线` |
| `+0x55E0` (21984) | u32 | `death` | 摧毁它的破坏等级（与 `destruction` 表联查） | `✓ 离线`（SHODAN `KINDS[TYPES.destruction].DEATH`） |

## 3 伤害区（38 槽 × 552 B，起点 `+520`）

| 偏移 | 类型 | 名字 | 含义 | 证据 |
|---:|---|---|---|---|
| `+0x060` (96) | u32 | — | **区是否启用**（非 0 = 有实体） | `✓ 离线` |
| `+0x0CC` (204) | f32 | `durable_resistance` | 该区耐伤比例 0–1 | `✓ 离线` |
| `+0x0D8` (216) | u32 | `armor` | **该区护甲** | `✓✓` 实机（敌人区护甲 live-proven） |
| `+0x0E0` (224) | u32 | `max_armor` | 该区护甲上限 | `✓ 离线`（HD2Runtime `0.28.1`） |
| `+0x0E8` (232) | u32 | `health` | **该区血量**（`-1` = 用主血量池） | `✓✓` 实机 |
| `+0x0EC` (236) | ? | `constitution` | 区体质（类型未定，按 f32 读恒 0） | `⚠ 未证` |
| `+0x0F8` (248) | f32 | `affects_main_health` | **该区伤害分摊到主血量的比例 0–1** | `✓✓` 实机（载具区） |
| `+0x144` (324) | f32 | `explosive_damage_percentage` | 该区爆炸伤害份额；**未设时是 `FLT_MAX` 哨兵** | `✓ 离线`（哨兵值实测见 §4） |

> HD2Runtime 的两条读法约定（`✓`）：**wiki 的「爆炸伤害减免 25%」= 原生爆炸份额 0.75**；
> **「Durable 75%」= durable share 0.75**。哨兵：区血 `-1` = 用主池；爆炸份额未设 = 走另一个区。

## 4 本 build 实测校验（拿真实行读出来的值）

| 实体 | health | regen | constitution | const_rate | durable | armor | maxArmor | 活跃区 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M-104 FRV（车） | 2900 | 0.00 | **400** | **-40.0** | 0.85 | 3 | 0 | 29 |
| **GATER A** | **12000** | 0.00 | **2000** | **-200.0** | 0.75 | **6** | 0 | 10 |
| 共享运输机 | 2500 | 0.00 | 0 | 0.0 | 0.00 | 3 | 4 | 4 |
| SEAF 专家 | 150 | 0.00 | 75 | -1.5 | 0.00 | 0 | 0 | 6 |

`+0x30 KillScore` 在这四个上都 = 0（它们不是敌人）；`+0x55E0 death` 也都 = 0。
区 0 的爆炸份额读出 `3.4028235e38` = **`FLT_MAX` 哨兵** ⇒ 该区未设爆炸份额（与 HD2Runtime 的说明一致）。

## 5 对 GATER「落地前被摧毁」的意义

**血量、体质、护甲三项都不支持「太脆」这个解释**：

| 量 | GATER | M-104（同路径投送、能存活） | 倍数 |
|---|---:|---:|---:|
| 主血量 | 12000 | 2900 | **4.1×** |
| 体质 `constitution` | 2000 | 400 | **5×** |
| 默认区护甲 | 6 | 3 | 2× |
| 耐伤比例 | 0.75 | 0.85 | 略低 |

⇒ 要把 GATER 弄成「落地前被摧毁」，靠这几项是解释不了的，得往**非血量机制**找：
`ObjectiveDynamicLinkComponentData`（已试：把 `+0x04`/`+0x08` 清 0，见
[UNRELEASED-INVENTORY](UNRELEASED-INVENTORY-26088801.md) §7.2.3）、吊挂尺寸、或区结构差异
（GATER 只有 10 个活跃区 vs M-104 的 29 个）。

## 6 证据来源

| 来源 | 给了什么 |
|---|---|
| **HD2Runtime** `docs/enemy-authoring.md` / `vehicle-authoring.md` | **带偏移的 schema 表**（`+0` / `+24` / `+28` / 区 `+216/+232/+248/+204/+236/+324`），以及 live-proven / gameplay-proven 的等级 |
| **SHODAN Stat Editor** `stat_editor.lua`（`body_rows` 等） | 偏移与标签互证：`+0` health、`+4` regen、`+268` durable、`+280` armor、区 `+96` 启用判据、区 `+204/+216/+232`、`DEATH = 21984` |
| HD2Runtime `docs/events.md` | `+0x30` = `KillScore` |
| **本 build 明文** | 几何（22,096 / 38×552 / 506 行）+ 上表全部实测值 |
| 本地 wiki 镜像 | **没有**组件级字段（wiki 只到玩家可见的「Durable %」「爆炸减免」），只能当语义佐证 |
| 网上（`shalzuth/HelldiversData`） | `data/components/HealthComponentData.json` 只给结构（`hashmap` + `HealthComponent` 数组），**没有字段名**；`data/` 下只有 `components / entities / enums / settings / translations`，无 `types/` |

## 7 未解

* 区 `+236 constitution` 的类型（按 f32 读恒 0，可能是 u8/u16）
* `+0x120 max_armor` 只在运输机上非 0，含义待验证
* `+0x55E0 death` 全部为 0，说明这批实体没用到「按破坏等级判定死亡」这条路径
