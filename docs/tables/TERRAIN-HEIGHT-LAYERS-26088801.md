# 地形高度层与 `zone_data` height generators（build `26088801`）

> **一句话**：行星地形起伏不是一个字段，而是**至少两层**：`region_settings` 段 0 的区域高度参数
> （实测有效）＋ **`zone_data` 的 `HeightGenerators`（+0x080）**——每个 zone 1～3 个噪声生成器，
> 参数名已用哈希爆破解出 `noise_scale` / `power` / `amplitude`。城市 zone 完全没有生成器，这正是
> 城市地形平坦的原因。

## 0. 三态

| 结论 | 态 | 证据 |
|---|---|---|
| `region_settings` 的 `terrain_height_range` 等在任务生成时被读取 | **✓ 实机**（定性）| v1 装盘（46 行 65→2）后用户回报「变平了一点，但还有山」|
| `zone_data` 每个 zone 有 1～3 个 `HeightGenerators`（+0x080），元素 = `ShaderProperties`(24 B) | **✓ 离线** | 30 个 zone 有生成器、58 个没有；结构偏移与 typelib/filediver 一致 |
| 生成器参数名 `noise_scale`(0x53D111F6) / `power`(0x21E1CDE6) / `amplitude`(0xE0EC70A9) | **✓ 离线**（哈希爆破，32-bit = MurmurHash64A 高 32 位）| 词表 11k 命中 3/6；值域与语义吻合（见 §2）|
| 城市 zone 无 height generator ⇒ 城市天然平坦 | **✓ 离线** | zone 10/15/20/25（被 `region_shared_city` 引用）`0x080` 数组 count=0 |
| `amplitude` 就是高度倍率 | **⚠ 待实机** | v3 装盘：131 处 amplitude → 0.01 |
| 还剩哪些高度层 | **? 未定** | stamp 侧（`FlatteningIntensity` / `FlattenTerrain`）、`HeightModificationCurve`（±14）|

## 1. 数据结构

`generated_zone_data.dl_bin`（518,478 B 明文）容器形状与其它表不同：

```
u32 3 | u32 88 | 88 × [ "LDLD" | ver | type=ZoneSettings | payload_size | wide | extra | payload ] | 段1 | 段2
             ↑ 88 = zone 数，块序号 = ZoneId；payload = 912 B 记录 + 该 zone 的组尾数组/字符串
```

`ZoneSettings`（912 B）里的生成器数组（filediver `rawZoneSettings` 权威顺序）：

| offset | 字段 | 本 build 实测 |
|---|---|---|
| `+0x000` | `ZoneTags` | 1～3 个 u8 |
| `+0x010` | `stamp_groups` | 印章组（地形拼块）|
| `+0x020` / `0x030` / `0x040` / `0x050` / `0x060` / `0x070` | `color_variation` / `ShaderProperties1` / `fog_volumes` / `minimap_viz` / `material` / `ShaderProperties2` | 6 条 |
| **`+0x080`** | **`height_generators`** | **1～3 个；00/02 段全 build 只有 2 个 shader hash** |

嵌套布局（全部在本仓库实测过）：

```
DLArray            = { offset i64, count u64 }                     (16 B)
ShaderProperties   = { shader u64, settings DLArray }               (24 B)
ShaderSetting      = { name ThinHash u32, value f32, Vec4, count u32 } (28 B)
```

## 2. 参数名（哈希爆破）与值域

名字哈希 = **MurmurHash64A(name, seed 0) 的高 32 位**（`tools/namehash.py`，与 Stingray 一致）。

| hash | 名字 | 实测值域 | 解读 |
|---|---|---|---|
| `0x53D111F6` | **`noise_scale`** | 25～375 | 噪声特征尺度 |
| `0x21E1CDE6` | **`power`** | 1.0～3.0 | 指数/锐度 |
| `0xE0EC70A9` | **`amplitude`** | 0.1～3.5 | 高度倍率（待实机确认）|
| `0x8A8534A7` | ? | −0.2～−0.5 | 未爆（偏置？）|
| `0xA751D97B` / `0xC1A65F78` | ? | 0 / 0.35 | 只出现在第二个 shader |

两个 `height_generators` 用的 shader hash：`0x7EDBF2FA87BE099E`（绝大多数 zone）、
`0x8C85E17EC008DD66`（zone 80，6 条 settings）。两者名字未爆。

## 3. 典型 zone 读数（`noise_scale`, `power`, `amplitude`）

| zone | 使用者 | 生成器参数 |
|---:|---|---|
| 4 | sandy / arctic | (125, 1, 1.0) (25, 1, 1.1) |
| 6 | sandy | (300, 1, 1.45) (150, 1, 1.75) |
| 32 | arctic_mountains | (350, 1, 1.4) (100, 1, 1.45) (48, 3, 3.0) |
| 35 | **arctic_mountains_and_dunes** | (140, 1, **0.1**) (75, 1, **0.25**) |
| 52 | sandy_acid_lakes | (96, 1.5, 1.5) (192, 1.5, 1.5) (32, 1.5, 1.5) |
| 67 / 68 | moor | (150, 1, 1.5) / (150, 1, 1.2) |
| 81 / 86 | swamp | (45, 1, 0.5) / (30, 1, 0.5) |
| **10/15/20/25** | **`region_shared_city`** | **（没有生成器）** |

「城市没有生成器」是最强的一条旁证：城市地面平坦不是靠参数小，而是**根本没有生成层**。

## 4. 改法与产物

```
python tools/zone_terrain_flat.py --plain <zone_data 明文> --amplitude 0.01 \
    --out out/terrain/zone_flat_amp001.plain.dl_bin \
    --seal refs/dlbin/keys/recipient.pk --sealed out/terrain/zone_flat_amp001.sealed.dl_bin \
    --secret refs/dlbin/keys/recipient.sk
```

- 改 **131 个 amplitude**（57 个 zone × 1～3 个生成器），全部 → `0.01`；
- 保 `MurmurHash64A`（本表原值 `0x99ED02D57714BBAD`）：校正字借 **无主 zone**（zone 0，不被任何
  region 子区域引用）payload 起点的 8 字节对齐字；
- 封装用 recipient 公钥，装盘回读逐字节一致；
- 装盘/回滚：`tools/deploy_region_flat.py --target generated_zone_data.dl_bin ...`
  备份名 `generated_zone_data.dl_bin.bak-terrain-zone-amp001`。

## 5. 实验日志（地形压平）

| 版本 | 改动 | 结果 |
|---|---|---|
| v1 | 46 个被引用 region 行 `terrain_height_range` 65→2、宏观/zone/随机归零 | 「变平了一点，但还有山」→ 区域层有效但只是其中一层 |
| v2 | 全 74 行 + 四档权重 0/0/0/2 + 子区域 HeightGroup 全 Bottom_Flat | 「沙漠还是有沙丘」→ 剩余起伏来自 zone 生成层 |
| v3 | zone `height_generators` 的 `amplitude` 131 处 → 0.01（**已装盘**）| **待实机** |

## 6. 未解

1. `amplitude` 究竟是高度倍率还是层权重——v3 实机判定；
2. `0x8A8534A7`（−0.2～−0.5）与第二个 shader 的 `0xA751D97B` / `0xC1A65F78` 的名字；
3. 两个 height generator shader 的名字（64-bit 爆破未命中）；
4. stamp 侧是否还叠地形：`StampWeights.HeightWeight`(Vec4)、`StampCircle/Rectangle.FlatteningIntensity/FlattenTerrain`；
5. `HeightModificationCurve`（0x0F0，±14）的实际作用。

## 7. 来源

- 结构/字段顺序：游戏 typelib（`ZoneSettings` size64=912，100 成员）+ filediver `datalibrary/zone_settings.go`；
- 参数名：本仓库 `tools/namehash.py` 哈希爆破（写入 `out/_scratch/crack_shader_settings.py`）；
- 实例数据：`refs/dlbin/plaintext-26251122/generated_zone_data.dl_bin`。
