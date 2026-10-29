# `SquadTransportComponentData` 全解：谁在用、每个字段是什么 —— build `26251122`

> **一句话**：它**不是** SEAF 小队运输机独有的表 —— 6 个实体在用它（2 架 `Dropship`、1 艘 `Warp Ship`、
> 1 个 SEAF 运输穿梭机、2 台 `Factory Strider`）。它定义的是「**这个载体怎么把一小队单位放出来**」：
> 走哪个节点（`+0x08` 是节点名的 murmur32）、放几组、每组引用什么资源。
>
> 相邻两张表别混：
> - `TransportComponentData`（`0x67B29FFA`，40 B 行，**14 宿主**）= 通用**载货**（carries 任意实体，含 NPC）；
> - `SquadTransportFormationComponentData`（`0x498CE7C7`，48 B 行，**90 宿主**）= **成员侧**编队参数。
>
> 相关：[POD-RACK-SLOTS](POD-RACK-SLOTS-26251122.md)（投送舱那条完全不同的路）·
> [UNRELEASED-INVENTORY](UNRELEASED-INVENTORY-26088801.md) §7.2.3（119 SEAF Squad 的否证台账）

---

## 0. 验证状态（三态口径见 [INDEX §7](../../INDEX.md#7-三态标记与自检)）

| 结论 | 状态 | 证据 |
|---|---|---|
| `SquadTransportComponentData` = `0xD2B93CD8`，块 @`0x1FC358`，哈希图 192 B（12 槽）+ **6 行 × 168 B** @`0x1FC434` | **✓ 离线** | typelib 成员 + 块几何现算 |
| 宿主 **6 个**（2 Dropship / 1 Warp Ship / 1 SEAF 穿梭机 / 2 Factory Strider）⇒ **不是独有表** | **✓ 离线** | §1 宿主表（实体组件索引 + 名字） |
| 行内 `+0x08` = **节点名的 murmur32**：4 行 `0x3DE4072E`=**"Dropship"**、2 行 `0xC170DF27`=**"Spawner"** | **✓ 离线（名字表直证）** | SDK `hashlists/hashlist-all.txt` 反查命中；与 `TransportComponentData +0x08 = murmur32("cargo_attach")` 同一类字段 |
| `+0x20` = **6 × 16 B 条目**（u64 + u32/f32），只有第 0 条有值 | **✓ 离线** | typelib：成员 96 B = 6 × 类型 `0x1CF4C4AA`（16 B：u64 + u32） |
| 第 0 条的 u64 = **资源 file_id `0x00BCF8247A544CDC`** → `content/fac_cyborgs/vehicles/cyborg_tank/cyborg_tank` | **✓ 离线** | `entity-resource-names.json` 直查；`resource_index` 里也有这个 file_id |
| `+0x14`（枚举）/ `+0x00` / `+0x04` / `+0x0C` / `+0x84` 的语义 | **⚠ 推断** | 只有互异值与宿主对照，没有差分实验（见 §2 备注） |
| 把 `+0x14` / `+0x80` / `+0x81` 归零后 119 SEAF Squad 仍投空 | **✓ 实机（2026-10-28，否证）** | UNRELEASED-INVENTORY §7.2.3：三值归零装盘后仍空 |
| 载体行与正常 Dropship 的差异 **共 5 处**（不是 3 处）：`+0x00`、`+0x0C`、`+0x14`、`+0x80`、`+0x81` | **✓ 离线（逐字段 diff）** | §7.1：旧台账漏了 `+0x00`(3 vs 6) 与 `+0x0C`(0.45 vs 0.20)，这两处**从未被测试** |
| 11 名 SEAF 成员的编队行自成一档：`+0x18 = 0`（**无挂点**），而 53 行「能被投下」的单位写的是 `Spawner` | **✓ 离线** | §7.2（90 行模式分组） |

---

## 1. 六个宿主（这就是「谁在用」）

| row | 实体键 | 名字 | 组件数 | `+0x08` 节点 | 备注 |
|---:|---|---|---:|---|---|
| 0 | `0xDB90077E76FAA025` | **Dropship** | 29 | `Dropship` | 空投小队的主力形态 |
| 4 | `0x98152772A72F7838` | **Dropship** | 29 | `Dropship` | 与 row 0 逐字段相同（两份变体） |
| 2 | `0x3EC790806D0B0540` | *（无名字）* | 18 | `Dropship` | **SEAF 那条**；全表**唯一带 `VehicleShuttleComponentData`**，即「小队运输穿梭机」 |
| 3 | `0x74E2285C01DA4F71` | **Warp Ship** | 28 | `Dropship` | 光明族运输；`+0x11=1`、`+0x84` 掩码含 512 |
| 1 | `0xD37E8D120D2836E3` | **Factory Strider** | 50 | `Spawner` | **体内放兵**（不是空投）；还带 `AiSpawnerComponentData` + `SquadTransportFormationComponentData` |
| 5 | `0x30F2DEE2333F227A` | **Factory Strider** | 49 | `Spawner` | 同上（两档变体） |

⇒ 同一张表覆盖**两种投放形态**：`Dropship`（从外部空投）与 `Spawner`（从载体内部释放）。

---

## 2. 字段表（几何来自 typelib，取值来自 6 行实测）

| 偏移 | 尺寸 | typelib 成员 | 6 行观察值 | 判定 |
|---|---|---|---|---|
| `+0x00` | u32 | `[0]` | `1`（Strider）/`3`（SEAF）/`5`（Warp）/`6`（Dropship） | ⚠ 小整数，像「组数/规模枚举」 |
| `+0x04` | u32 | `[1]` | `2` / `3` / `4` | ⚠ 小整数，成对出现（与 `+0x00` 一起看） |
| **`+0x08`** | u32 | `[2]` | `0x3DE4072E`="Dropship" ×4 · `0xC170DF27`="Spawner" ×2 | ✓ **节点名 murmur32**（名字表直证） |
| `+0x0C` | f32 | `[3]` | `0.20`（5 行）· `0.45`（SEAF 行） | ⚠ 浮点参数（间距/延迟/半径？SEAF 与其它不同） |
| `+0x10` | u8 | `[4]` | 全 `1` | ⚠ bool |
| `+0x11` | u8 | `[5]` | Warp Ship=`1`，其余 `0` | ⚠ bool |
| `+0x14` | u32（枚举 `0x451716DE`，**类型不在 typelib**） | `[6]` | `0` / `5`（Strider）/ `6`（**SEAF 独有**） | ⚠ 枚举；UNRELEASED §7.2.3 的「三独有值」之一 |
| `+0x18` | u8 | `[7]` | 全 `1` | ⚠ bool |
| **`+0x20`** | **96 B** = **6 × (u64 + u32)** | `[8]`（元素类型 `0x1CF4C4AA`，stride 16） | 只第 0 条非零：u64=`0x00BCF8247A544CDC`，u32 读作 f32 = `18.12`（两架 Dropship + SEAF 行）· `0`（Warp Ship、两台 Strider） | ✓ u64 = **资源 file_id**（`/cyborg_tank/cyborg_tank`）；u32 ⚠ |
| `+0x80` | u8 | `[9]` | **仅 SEAF 行 = `1`**（按 u32 读作 `0x00000101`） | ✓ 观察（独有） |
| `+0x81` | u8 | `[10]` | **仅 SEAF 行 = `1`** | ✓ 观察（独有） |
| `+0x84` | 32 B（类型 `0x346D1AF4` **不在 typelib**） | `[11]` | 前三个 u32 = `4` / `8` / `16`；Warp Ship = `4` / `8` / `512` | ⚠ 看着像位掩码（bit2 / bit3 / bit4，Warp bit9） |

逐行取值（判读用）：

| row | 宿主 | `+00` | `+04` | `+08` | `+0C` | `+10` | `+11` | `+14` | 槽[0].u64 | 槽[0] f32 | `+80` | `+81` | `+84` |
|---:|---|---:|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| 0 | Dropship | 6 | 2 | Dropship | 0.20 | 1 | 0 | 0 | `0x00BCF8247A544CDC` | 18.120 | 0 | 0 | 4,8,16 |
| 1 | Factory Strider | 1 | 4 | Spawner | 0.20 | 1 | 0 | 5 | `0` | 0 | 0 | 0 | 4,8,16 |
| 2 | **SEAF 穿梭机** | **3** | 2 | Dropship | **0.45** | 1 | 0 | **6** | `0x00BCF8247A544CDC` | 18.120 | **1** | **1** | 4,8,16 |
| 3 | Warp Ship | 5 | 3 | Dropship | 0.20 | 1 | **1** | 0 | `0x00BCF8247A544CDC` | 0.000 | 0 | 0 | 4,8,**512** |
| 4 | Dropship | 6 | 2 | Dropship | 0.20 | 1 | 0 | 0 | `0x00BCF8247A544CDC` | 18.120 | 0 | 0 | 4,8,16 |
| 5 | Factory Strider | 1 | 4 | Spawner | 0.20 | 1 | 0 | 5 | `0` | 0 | 0 | 0 | 4,8,16 |

> ⚠ **别把 `+0x20` 读成「12 个 u64」**：typelib 明写 96 B = 6 × 16 B（u64 + u32）。
> 早前按 12 个 u64 读，会把每条的第二半（u32/f32）错当成一条新条目。

---

## 3. 和另外两张「运输」表的边界

| 表 | 类型 | 行 | 宿主 | 管什么 |
|---|---|---:|---:|---|
| **`SquadTransportComponentData`** | `0xD2B93CD8` | 168 B | **6** | 载体侧：**把一小队单位放出来**（节点 + 组数 + 资源引用） |
| `SquadTransportFormationComponentData` | `0x498CE7C7` | 48 B | **90** | 成员侧：**编队参数**（谁站哪）。`+0x00` 90 行全是 `0x3DE4072E`="Dropship"，`+0x14` 是 `AttachTank`/`AttachSpawner`，`+0x18` 是 `Spawner`（都是 murmur32 名字哈希） |
| `TransportComponentData` | `0x67B29FFA` | 40 B | 14 | 通用**载货**（`+0x08` = `cargo_attach` 节点名哈希），能载任意实体 |

> 判据：`SquadTransport*` 是「**投人**」（带编队/成员语义）；`TransportComponentData` 是「**载货**」（载具/箱子/NPC 都行）。

---

## 4. 与本项目已有结论的关系

- **119 SEAF Squad 的「投空」不是这张表的参数问题**（§0 最后一行，✓ 实机否证）：
  把三处 SEAF 独有值（`+0x14`、`+0x80`、`+0x81`）归零对齐能正常投兵的 dropship 之后，**仍然投空**。
- **投 SEAF 士兵的正确通路已经换掉了**：改用投送舱（`HellpodRackComponentData`），
  一舱 8 个，见 [POD-RACK-SLOTS](POD-RACK-SLOTS-26251122.md)（✓✓ 实机，武器/AI 正常）。
- 本表剩下的价值：`Factory Strider` 用 `Spawner` 节点从体内放兵 —— 如果以后要让某个载体「体内放出 NPC」，
  这就是现成的模板（`+0x08` 写 `Spawner` 的 murmur32 = `0xC170DF27`）。

---

---

## 7. 119 SEAF Squad 的两张表「正常吗」—— 逐字段比对（2026-10-29）

结论先说：**结构都正常，但都不是「能正常投兵」的模板值**。载体行有 **5 处**与工作模板不同（旧台账只记了 3 处），
成员行则是一套**只在 11 个 SEAF 士兵身上出现的独立模板**。

### 7.1 载体侧：`SquadTransportComponentData` 第 2 行 vs 两架能正常投兵的 Dropship

| 偏移 | Dropship（row 0 / 4） | **SEAF 穿梭机（row 2）** | 判定 |
|---|---|---|---|
| `+0x00` | 6 | **3** | **SEAF 独有 · 从未对齐过** |
| `+0x04` | 2 | 2 | 同 |
| `+0x08` | `Dropship` | `Dropship` | 同（节点名哈希一致） |
| `+0x0C` | 0.20 | **0.45** | **SEAF 独有 · 从未对齐过** |
| `+0x10` / `+0x11` / `+0x18` | 1 / 0 / 1 | 1 / 0 / 1 | 同 |
| `+0x14` | 0 | **6** | SEAF 独有（2026-10-28 已归零试过） |
| `+0x20` | `[0]` 缺省条目（资源 + 18.12） | 同 | 同 |
| `+0x80` / `+0x81` | 0 / 0 | **1 / 1** | SEAF 独有（同日已归零试过） |
| `+0x84` | 4,8,16 掩码 | 4,8,16 | 同 |

> ⚠ **旧台账记「三个独有值」，实际是五个**：`+0x14`、`+0x80`、`+0x81` 之外还有 `+0x00` 与 `+0x0C`。
> 2026-10-28 那次归零实验只动了前三个 ⇒ **「对齐后仍投空」这个否证只覆盖了 3/5 的差异**，
> 剩下的 `+0x00`（3 vs 6）与 `+0x0C`（0.45 vs 0.20）**从未被测试过**。

### 7.2 成员侧：`SquadTransportFormationComponentData`（48 B）—— SEAF 是一套独立模板

全表 90 行按字节模式分组，11 名 SEAF 士兵（`0x75F7E96AF7DCD303` 等）**11 行完全相同**，
并且自成一档（该档 11 行全是 SEAF）：

| 字段 | SEAF 11 名（独立档） | 主体档 53 行（Voteless / Marauder / Trooper / MG Raider…，**能正常被投下**） | 判定 |
|---|---|---|---|
| `+0x00` | `Dropship` | `Dropship` | 同 |
| `+0x04` | 1 | 1 | 同 |
| `+0x08` | 1 | 1 | 同 |
| `+0x0C` | 1 | 2 | **不同** |
| `+0x10` | **6** | **1** | **不同** |
| `+0x14` | 0 | 0 | 同 |
| **`+0x18`** | **0（没有挂点）** | **`Spawner`（节点名哈希 `0xC170DF27`）** | **不同 ← 最可疑** |
| `+0x1C` / `+0x20` | 1 / 1 | 1 / 1 | 同 |
| `+0x24` | 1 | 2 | **不同** |
| `+0x28` | 1 | 5 | **不同** |

其它档位（作对照）：坦克 4 行 `+0x14=AttachTank`；Factory Strider / Vox Engine 3 行 `+0x14=AttachSpawner`；
Hulk 8 行 `+0x10=3`；Scout Strider 2 行 `+0x10=2`。

⇒ **成员侧从来没有被检查过**：旧台账（[UNRELEASED-INVENTORY](UNRELEASED-INVENTORY-26088801.md) §7.2.3）
只验了载体行。SEAF 成员现在 `+0x18 = 0`（**没有挂点哈希**），而 53 行「能被投下来」的单位写的都是 `Spawner`。
这与「士兵实体/编队有内容」的旧判据并不冲突 —— 旧判据只看了 `+0x00`（`Dropship`）那一格。

### 7.3 由此得到两个尚未做过的单变量实验

| # | 改什么 | 与谁对齐 | 预期 |
|---|---|---|---|
| M1 | 11 名 SEAF 成员的 `SquadTransportFormationComponentData +0x18`：`0 → 0xC170DF27`（"Spawner"） | 53 行正常档 | 若「投下来」需要成员侧挂点，这一发就能让 119 吐出士兵 |
| M2 | 载体行 `+0x00`：`3 → 6`、`+0x0C`：`0.45 → 0.20` | 两架 Dropship | 若组数/间距是门槛，这一发能过 |

两个都属**数据层可写**（`entity_field_set.py` 支持按组件类型 + 行键写字段），门禁与之前一致。
⚠ 但 2026-10-28 的三值归零已实机否证过「只靠载体参数」这条路，所以 **M1 的优先级高于 M2**。

## 5. 复现

```bash
# 表几何 + 6 行逐字段转储
python out/pod-census/squad_transport_dump.py

# u32 值 → SDK 名字哈希反查（Dropship / Spawner / AttachTank / AttachSpawner 就是这么命中的）
python out/pod-census/squad_transport_names.py
```

## 6. 溯源与许可

- SDK 名字哈希表：`C:\Users\Admin\HD2SDK-CommunityEdition\hashlists\hashlist-all.txt`（只取 `0x` 前缀行，
  十进制行会造成小整数假命中）。
- 资源路径：`D:\mod\entity-resource-names.json`（file_id → 资源路径），`D:\mod\cache\resource_index.pkl`。
- 本仓库：`tools/typelib.py`（几何现算）、`refs/entity-components.json`（谁挂了哪个组件）、
  [UNRELEASED-INVENTORY](UNRELEASED-INVENTORY-26088801.md) §7.2.3（119 的否证与三独有值）。
