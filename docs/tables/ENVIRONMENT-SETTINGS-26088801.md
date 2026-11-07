# `environment_settings` 全解：17 个星球生态的着色/大气预设（build `26251122`）

> **一句话**：这张表 **17 行 × 576 B**，一行 = 一个 `PlanetType` 生态（id `0..16`，
> 名字直接写在**行尾字符串**里：`forest / desert / arctic / … / rift`）。
> 内容是**着色 + 大气 + 散点引用**——**没有**任何移动/体力/伤害倍率，
> 所以 `MUSCLE ENHANCEMENT (0.35)` 的落点**不在**这里（否证一个候选，见 §6）。

## 0. 三态

| 结论 | 态 | 证据 |
|---|---|---|
| 17 行 = `PlanetType` 枚举 `0..16`，一行一个生态 | **✓ 离线（自证）** | ①`+0x00` 是 type `0x29EED886` 的枚举，17 行取值恰好 0..16 无重复；②行尾有 `forest/desert/arctic/…/rift` 与 `planet_type_<name>` 两串；③`planet_data` 438 组的 `+0x1B8`（同为 `PlanetType`）只用到其中 12 个值 |
| 颜色字段读法正确 | **✓ 离线（语义自证）** | 颜色按生态自然聚类：arctic/snowy_forest = **(1,1,1) 白**；forest 族 = 橄榄绿；desert 族 = 暖棕；rift 的 `light` = **(15,12,18) 偏蓝紫** |
| 本表不含移动/体力参数 | **✓ 离线（否证）** | 28 个成员全部落在「名称串 / 资源哈希 / 颜色 vec3 / 标志位 / 子结构」五类里，没有可解释为速度或体力倍率的标量（唯一“像数值”的 `+0x238` 是常量 1.0）|
| 5 个生态本 build 未被任何星球使用 | **✓ 离线** | `planet_data` 438 行的 `PlanetType` 只有 12 个值：`2/3/6/8/9/10/11/12/13/14/15/16`；`0 forest / 1 desert / 4 savanna / 5 rocky / 7 snowy_forest` 无引用 |

## 1. 一行（576 B）逐成员

| 偏移 | 大小 | typelib 类型 | 判定 | 证据 |
|---|---:|---|---|---|
| `+0x000` | 4 | `0x29EED886`（同 `PlanetType`）| **生态枚举 id**（0..16）| 17 行取值全不同 = 0..16 |
| `+0x008` | 8 | — | payload 相对偏移 → **生态名串**（如 `arctic`）| 17/17 解出 `forest…rift` |
| `+0x010` | 4 | — | thin hash32 ⚠ | 17 行各不同，值非小整数 |
| `+0x018` | 8 | — | 偏移 → **`planet_type_<name>` 串** | 17/17 解出，与 `+0x000` 一致 |
| `+0x020` `+0x024` `+0x05C` | 4×3 | — | thin hash32 ⚠（不是 f32：按 f32 读是 1e27 量级垃圾）| 同上 |
| `+0x028…+0x048` | 8×5 | — | **5 个 hash64 资源引用**（每行 15 种取值）| 全表只出现于本表 → 资源哈希，离线不可解析 |
| **`+0x050`** | 12 | `0x85B82A43` = vec3 | **颜色 #1**（3 种取值）| arctic 白 / desert 暖棕 / forest 橄榄 |
| **`+0x060`** | 12 | vec3 | **光照/色调 vec3**（4 种）| (48,48,48) 雪 / (15,12,7.5) 暖 / (12,18,15) 绿 / (15,12,18) 紫 |
| `+0x06C` | 12 | vec3 | **常量** `(0.15, 0.75, 1.0)`（17/17 相同）| 常量 |
| **`+0x078`** | 12 | vec3 | **颜色 #2**（3 种，值更小：0.033–0.1）| 与 #1 同步分组 |
| `+0x088` | 8 | — | hash64（3 种）| — |
| `+0x090` | 360 | `0x6D91F262` | 子结构；**每行仅 90 B 非零**，其中 rocky 与其余 16 行差 16 B ⚠ | 未解（像固定尺寸的采样/梯度表）|
| `+0x1F8` | 16 | — | 常量 `{0xFFFFFFFFFFFFFFFF, 0}` | 17/17 相同 |
| **`+0x208`** | 4 | — | **标志位 / 位掩码**：forest=1 desert=2 arctic=4 swamp=8 primordial=16 moor=32，其余 9 行 = 0 ⚠ | 取值恰为单 bit |
| `+0x210` | 8 | — | hash64（16 种）⚠ | — |
| `+0x218` | 8 | — | 偏移 → **`<variant>_default` 串**（着色预设名）| 17/17 解出；**有复用**：sandy→`desert_default`、swamp→`forest_default`、snowy_forest→`arctic_default`、superearth→`moor_default` |
| `+0x220…+0x22C` | 4×4 | — | 0 / 少量 hash32 ⚠ | — |
| `+0x230` | 8 | — | 偏移 → 空串（17/17 空）| 预留（presence 天气覆盖？空）|
| `+0x238` | 4 | — | f32 常量 `1.0` | 17/17 |

## 2. 17 行全表

| id | 生态（本表尾串）| 着色预设（`+0x218`）| flag | 颜色 #1 `+0x50` | 光照 `+0x60` | 颜色 #2 `+0x78` |
|---:|---|---|---:|---|---|---|
| 0 | `forest` | `forest_default` | 1 | (0.1486, 0.1437, 0.0637) | (12, 18, 15) | (0.085, 0.1, 0.033) |
| 1 | `desert` | `desert_default` | 2 | (0.1686, 0.1137, 0.0588) | (15, 12, 7.5) | (0.1, 0.067, 0.033) |
| 2 | `arctic` | `arctic_default` | 4 | **(1, 1, 1)** | **(48, 48, 48)** | (0.1, 0.1, 0.1) |
| 3 | `sandy` | `desert_default` | 2 | (0.1686, 0.1137, 0.0588) | (15, 12, 7.5) | (0.1, 0.067, 0.033) |
| 4 | `savanna` | `savanna_default` | 2 | (0.1686, 0.1137, 0.0588) | (15, 12, 7.5) | (0.1, 0.067, 0.033) |
| 5 | `rocky` | `rocky_default` | 2 | (0.1686, 0.1137, 0.0588) | (15, 12, 7.5) | (0.1, 0.067, 0.033) |
| 6 | `swamp` | `forest_default` | 8 | (0.1486, 0.1437, 0.0637) | (12, 18, 15) | (0.085, 0.1, 0.033) |
| 7 | `snowy_forest` | `arctic_default` | 4 | **(1, 1, 1)** | **(48, 48, 48)** | (0.1, 0.1, 0.1) |
| 8 | `primordial` | `primordial_default` | 16 | (0.1486, 0.1437, 0.0637) | (12, 18, 15) | (0.085, 0.1, 0.033) |
| 9 | `moor` | `moor_default` | 32 | (0.1486, 0.1437, 0.0637) | (12, 18, 15) | (0.085, 0.1, 0.033) |
| 10 | `superearth` | `moor_default` | 1 | (0.1486, 0.1437, 0.0637) | (12, 18, 15) | (0.085, 0.1, 0.033) |
| 11 | `bug_hiveworld` | `desert_default` | 0 | (0.1686, 0.1137, 0.0588) | (15, 12, 7.5) | (0.1, 0.067, 0.033) |
| 12 | `magma` | `desert_default` | 0 | (0.1686, 0.1137, 0.0588) | (15, 12, 7.5) | (0.1, 0.067, 0.033) |
| 13 | `oasis` | `oasis_default` | 0 | (0.1686, 0.1137, 0.0588) | (15, 12, 7.5) | (0.1, 0.067, 0.033) |
| 14 | `deciduous` | `deciduous_default` | 0 | (0.1486, 0.1437, 0.0637) | (12, 18, 15) | (0.085, 0.1, 0.033) |
| 15 | `coniferous` | `coniferous_default` | 0 | (0.1486, 0.1437, 0.0637) | (12, 18, 15) | (0.085, 0.1, 0.033) |
| 16 | `rift` | `rift_default` | 0 | (0.1486, 0.1437, 0.0637) | **(15, 12, 18)** | (0.085, 0.1, 0.033) |

机器可读：`refs/environment-settings-26251122.json`。

## 3. 与 `planet_data` 的 join

| 项 | 值 |
|---|---|
| `planet_data` 布局 | **438 组**（一星球一组，组 payload ≈ 792–904 B，行 624 B + 尾串）|
| 生态选择器 | `+0x1B8` = `PlanetType`（同枚举）|
| 本 build 实际用到的生态 | 12 个：`2 arctic`(48) `3 sandy`(101) `6 swamp`(32) `8 primordial`(88) `9 moor`(94) `10 superearth`(2) `11 bug_hiveworld`(8) `12 magma`(12) `13 oasis`(15) `14 deciduous`(25) `15 coniferous`(10) `16 rift`(3) |
| 本 build 未使用 | `0 forest` `1 desert` `4 savanna` `5 rocky` `7 snowy_forest`（表里仍有定义，属预留）|

→ 与 [PLANET-DATA-FIELDS](PLANET-DATA-FIELDS-26088801.md) §4 的 12 值分布**逐值一致**（独立复算）。

### 3.1 使用情况：本地无引用 vs 本季未上线（2026-11-07 补）

三个口径要分开（数据源：`planet_data` 438 组 + 最新 `api_WarSeason_801_Status.json` 抓包）：

| 口径 | 数量 | 生态 |
|---|---:|---|
| 有 `environment_settings` 行 | 17 | `0..16` 全部 |
| **被任一星球行引用** | **12** | 见上表 |
| **本季在线（`planetStatus` 里）** | **9** | sandy(72) moor(66) primordial(61) arctic(34) swamp(29) magma(6) bug_hiveworld(3) superearth(1) rift(1) |
| 本地无任何星球引用 | **5** | `forest` `desert` `savanna` `rocky` `snowy_forest` |
| 有星球但本季 0 颗在线 | **3** | `oasis`(15 颗全休眠) `deciduous`(25) `coniferous`(10) |

补充事实：

- 本季 `Status` 返回 **273** 颗星球（`index` 0–273），本地 **438** 行 ⇒ **165 颗休眠**（未进入本季战况）；
  休眠星球里恰含 `deciduous 25 / oasis 15 / coniferous 10` 的全部行星。
- `PlanetType` 枚举共 **18** 个值（filediver 枚举 `0..17`），而本表只有 **17 行**（`0..16`）
  ⇒ **值 `17` 既无着色定义、也无星球引用**（纯悬空枚举；本机 filediver 串表里没有 `planet_type_17` 之类名字）。
- 那 5 个无引用生态被"细分生态"取代：本 build 被引用的 setup 家族全是细分型
  （`forest_swamp / forest_primordial / forest_moor / forest_deciduous / forest_coniferous / forest_rift`、
  `desert_sandy* / desert_magma / desert_oasis*`），**没有任何行星引用过 `forest_base` / `desert_base` 这类通用 setup**。
  ⇒ 这 5 行更像"旧版通用生态的残留着色预设"，⚠ 资源包里是否还留着对应地形 setup 未验。

⇒ 想在本季看到"新生态"：只能选 `oasis / deciduous / coniferous`（它们仍有星球行与 setup 资产，改 `PlanetType` 才有意义）；
拿 `forest / desert / savanna / rocky / snowy_forest` 去指，可能只剩着色差异（⚠ 未验）。

## 4. 语义自证：颜色怎么和生态对上

| 聚类 | 成员 | 颜色特征 | 讲得通吗 |
|---|---|---|---|
| 雪 | `arctic` `snowy_forest` | 颜色 #1 = **纯白 (1,1,1)**，光照 **48**（其余生态的 2.7–4 倍）| ✓ 雪原高反照 |
| 植被 | `forest` `swamp` `primordial` `moor` `superearth` `deciduous` `coniferous` | 橄榄色，光照 **G>R>B** = (12,18,15) | ✓ 叶绿 |
| 干旱 | `desert` `sandy` `savanna` `rocky` `bug_hiveworld` `magma` `oasis` | 暖棕，光照 **R>G>B** = (15,12,7.5) | ✓ 沙尘 |
| 裂隙 | `rift` | 同植被底色，但光照 **B 最高** = (15,12,18) | ✓ 紫色虚空 |

⇒ 这套字段读法**不是猜的**：三条颜色向量与生态名字的对应关系自洽，且与 `PlanetType`
的生态名（`arctic`/`desert`/`forest`…）交叉成立。

## 5. 对 Booster 线的结论（否证一条候选）

`MUSCLE ENHANCEMENT` 的 `+0x08 = 0.35` 语义是"地形减速 ×(1−0.35)"，曾把本表当候选落点。
本表 28 个成员里**没有**速度/体力类标量（唯二像数值的是两个常量：`+0x6C` = (0.15,0.75,1.0)、
`+0x238` = 1.0）⇒ **否证**。地形减速更可能在实体侧（`AvatarComponentData` 的
`SteepSlopeMovement.*` 只有陡坡，不含泥/雪/沙）或关卡生成/表面材质侧，仍未定位。
详见 [BOOSTER-COMPLETE](BOOSTER-COMPLETE-26088801.md) §6 未解项 1。

## 6. 本地 vs API：星球环境与天气都存在本地

| 数据 | 在哪 | 说明 |
|---|---|---|
| 生态（env 着色预设）| **本地** `environment_settings` | 17 行，本表；由 `planet_data.PlanetType` 选 |
| 星球本体 / 生态 / setup / 调色板 / region | **本地** `planet_data`（438 组）+ `region_settings` / `zone_data` / `planet_region_settings` / `location_groups` | 关卡生成参数全在本地 |
| 天气定义 | **本地** `weather_settings`（184 组 × 648 B）| 含 6 条 `galactic_presence_overrides/weather_settings/*` 的 presence 覆盖 |
| 星球当前状态（归属 / 解放度 / 战役 / 事件）| **API** | `GET /api/WarSeason/801/Status` 等；`planetIndex / race / campaignId / planetEventId` 都是服务端字段 |
| "这条 presence 现在是激活的" | **API / 运行时战况板** | 本地 `galactic_presence_settings` 有 137 行定义，但**哪条激活**不在本地表（详见 [PLANET-TABLES](PLANET-TABLES-26088801.md) §3.5）|

⇒ 所以：**你看得到的"这颗星是什么地貌/什么天气"来自本地表**（离线可改，改 `PlanetType` 等于整套换生态）；
**"这颗星现在属于谁、有没有事件、presence 开没开"来自 API**（服务端/代理层，改本地表无效）。

## 7. 复现

```bash
# 17 行 + 名字 + 颜色
python - <<'PY'
import struct, pathlib
b = pathlib.Path(r"D:/mod/refs/dlbin/plaintext-26251122/generated_environment_settings.dl_bin").read_bytes()
n = struct.unpack_from("<I", b, 0)[0]; off = 4
for _ in range(n):
    ver, tid, psz, wide = struct.unpack_from("<4I", b, off+4)
    o = off + 24
    def s(rel):
        e = b.find(b"\x00", o+rel, o+psz); return b[o+rel:e].decode("latin1")
    print(struct.unpack_from("<I", b, o)[0], s(struct.unpack_from("<Q", b, o+8)[0]),
          s(struct.unpack_from("<Q", b, o+0x18)[0]), s(struct.unpack_from("<Q", b, o+0x218)[0]),
          [round(x,4) for x in struct.unpack_from("<3f", b, o+0x50)])
    off = o + psz
PY
```

## 8. 交叉引用

- [PLANET-DATA-FIELDS](PLANET-DATA-FIELDS-26088801.md)（`+0x1B8 PlanetType`、12 值分布、setup 家族）
- [PLANET-TABLES](PLANET-TABLES-26088801.md)（presence 唯一钩子 = 天气；API/本地边界）
- [BOOSTER-COMPLETE](BOOSTER-COMPLETE-26088801.md)（MUSCLE 落点仍未定位）
