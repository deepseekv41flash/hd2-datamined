# `weapon_customization_settings` 解码（build 25988413）

> 这张表是**武器配件总表**：252 行 = 弹种 82 + 弹匣 57 + 枪口 37 + 瞄具 22 + 下挂 20 +
> 备选弹种 15 + 涂装 12 + 内部件 4 + 扳机 3。
> 整表可读导出：`refs/exports/weapon_customization_settings.csv`（252 行 × 13 字段，含行名）。

## 1. 行结构（88 B，逐字段已对上）

字段名与偏移来自 **xypwn/filediver** 的 `datalibrary/weapon_customization.go`
（`rawWeaponCustomizableItem`），我们把它的 88 字节结构与本机数据逐项对齐过：

| 偏移 | 字段 | 类型 | 本机观测 |
|---:|---|---|---|
| **`+0`** | **`DebugNameOffset`** | **u64 指针** | **就是每行自带的名字指针**：252/252 行解析出显示名，248 个不同值。早先以为它"只是碰巧"，已否证 |
| `+8` | `ID` | ThinHash (u32) | **252 个不同值** ⇒ 每件配件的唯一 id |
| `+12` | `NameUpper` | u32 | 158 个不同值（大写名哈希）|
| `+16` | `NameCased` | u32 | 158 个不同值（原样名哈希）|
| `+20` | `Description` | u32 | 158 个不同值（描述哈希）|
| `+24` | `Fluff` | u32 | **恒为 0**（本表没填）|
| `+28` | *(padding)* | 4 B | |
| `+32` | `AddPath` | Hash (u64) | 249 个不同值（模型/挂点资源）|
| `+40` | `Icon` | Hash (u64) | 252 行**全 0**（图标另有来源）|
| `+48` | `SlotsOffset` | u64 | → 槽位枚举数组 |
| `+56` | `SlotsCount` | u64 | 每件 1 个槽位（个别多项）|
| `+64` | `UIWidgetColorsOffset` | u64 | → `CApiVector3` 数组 |
| `+72` | `UIWidgetColorsCount` | u64 | |
| `+80` | `SortGroups` | u32 | **4 个不同值**，见下 |
| `+84` | *(padding)* | 4 B | |

## 2. 那两个枚举

`WeaponCustomizationSlot`（`+48/+56` 指向的数组，元素为 u32）：

| 值 | 名称 | 本表件数 |
|---:|---|---:|
| 0 | None | 0 |
| 1 | **Underbarrel** | 20 |
| 2 | **Optics** | 22 |
| 3 | **PaintScheme** | 12 |
| 4 | **Muzzle** | 37 |
| 5 | **Magazine** | 57 |
| 6 | **AmmoType** | 82 |
| 7 | **AmmoTypeAlt** | 15 |
| 8 | **Internals** | 4 |
| 9 | **Triggers** | 3 |

`WeaponCustomizationSortGroups`（`+80`）：

| 值 | 名称 | 本表件数 |
|---:|---|---:|
| 0 | None | 240 |
| 1 | Paint_Default | 1 |
| 2 | Paint_Solid | 7 |
| 3 | Paint_Camo | 4 |

## 3. 上一版猜错了什么

之前推测 `+8/+12/+16/+20` 是"按弹种分组的一组 4 个 id"。**不对**——它们是
`ID`、`NameUpper`、`NameCased`、`Description`：一个唯一 id 加三个**名字/描述的 32 位哈希**。
真正的分组列是 `+48/+56`（槽位枚举）和 `+80`（排序组）。这也是"158 个不同值"的来源：
252 件配件里有 158 个不同的（名字, 描述）组合。

## 4. 交叉验证（不是推论，是计数）

1. **弹种行全部落在 AmmoType**：82 条 `AmmoType` 里包含全部 `PISTOL-SMG` / `RIFLE` / `SHOTGUN`
   弹药名；反查"名字像弹药但槽位不是 AmmoType"的行 = **0 条**。
2. **涂装行全部落在 Paint_* 排序组**：`Forest Solid` / `Arctic Camo` / `Desert Solid` 等 12 条
   `PaintScheme` 行的 `SortGroups` 只在 1/2/3。
3. **`Fluff` 恒 0、`Icon` 恒 0** 与 filediver 结构里这两个字段"本表没填"的预期一致。

## 5. 复现

```bash
# 整表导出（需要你自己的 recipient.sk，仓库不含密钥）
python tools/table_export.py --table weapon_customization_settings \
    --sk <你的>/recipient.sk --out out/wc
# 产 out/wc.csv（含 slots / sort_group 两列）与 out/wc.md（字段图例 + 前 15 行）
```

`tools/table_export.py` 里的 `LAYOUTS` 就是这张表的注解：字段名、两个枚举、槽位数组位置。
换别的表时把注解补进 `LAYOUTS` 即可复用同一套导出。

## 6. 出处

* 结构与字段名：**xypwn/filediver**，`datalibrary/weapon_customization.go`、
  `datalibrary/enum/weaponcustomizationslot.go`、`.../weaponcustomizationsortgroups.go`（MIT）。
* 本表数据、偏移核对、槽位解码：本项目（`tools/table_export.py` + 密钥解封）。
* 行名来自**每行自带的 `+0` 指针**（`DebugNameOffset`），不是尾部的平行数组：指针名与位置名
  在 8 个组上 240/240 一致，而位置法在第 9 组（12 个染料，块里混着颜色二进制）会吐出碎片。
  抽取方式见 `tools/table_row_names.py`、`tools/probe_row_name_offsets.py` 与字典文档 §0.5。

## 7. 选项怎么"落地"：entity delta 链（build `26088801` 实测）

> 上面 §1–§6 是 `25988413` 的表结构。本节是**动作侧**：配件选中之后，游戏到底改了哪个组件、改成什么 ——
> 这部分不在本表里，在 `generated_entity_deltas.dl_bin`（`ComponentEntityDeltaStorage`，块类型 `0x683E604F`）。

### 7.1 链

```
实体 WeaponCustomizationComponentData 的默认 (slot, optionId) 对
  -> 本表（weapon_customization_settings）按 +8 ID 找到配件行，取 +32 AddPath（u64 资源哈希）
  -> generated_entity_deltas.dl_bin 的 hashmap 按 AddPath 找到 settingsIndex
  -> settings/component/delta 三级索引 -> (组件索引, 成员偏移, 宽度, data 偏移)
  -> 建造武器时把 data 里的字节打进该组件记录
```

### 7.2 delta 存储结构（本 build，`python tools/ref_scan.py delta-info` 可复现）

| 区 | payload 内偏移 | 条数 | 每条 | 结构 |
|---|---:|---:|---:|---|
| header | `+0` | 5 组 | 80 B | 每组 `(u64 offset, u64 count)` |
| hashmap | `+0x50` | 1024 槽（572 非空）| 16 B | `{u64 AddPath, u32 settingsIndex, u32 pad}` |
| settings | `+0x4050` | 1144 | 8 B | `{u32 componentCount, u32 firstComponent}` |
| component | `+0x6410` | 1038 | 12 B | `{u32 组件索引, u32 firstDelta, u32 deltaCount}` |
| delta | `+0x94B8` | 6119 | 12 B | `{u32 成员偏移, u32 宽度, u32 data 偏移}` |
| data | `+0x1B38C` | 240,817 B | — | 被打进去的字节本身 |

### 7.3 组件索引表（本 build 实测；换 build 必须重测）

| 索引 | 组件 | 本 build 见到的补丁 |
|---:|---|---|
| `5` | `WeaponMagazineComponentData` | 弹匣容量/初始/补给/备弹（`+136/+140/+144/+148`）|
| `114` | `WeaponReloadComponentData` | 装填常量与动画资源哈希 |
| `119` | `WeaponRoundsComponentData` | 弹药池 A/B 弹丸（`+64/+68`，slot 7 备选弹种走这里，15 条）|
| `239` | `WeaponDataComponentData` | 射速/后坐/散布等（`+964…`）|
| `274` | `WeaponCustomizationComponentData` | **`+0x80` 宽 8 = 当前弹匣/挂件 AddPath** |
| `324` | `ProjectileWeaponComponentData` | **`+0` 宽 4 = 弹丸 type id**（slot 6 弹种，67 条）|

### 7.4 两个实测例子（P-19 Redeemer）

| 配件槽 | 选中的配件 | AddPath | delta 干了什么 |
|---|---|---|---|
| slot 6 `AmmoType` | `PISTOL-SMG 9x20mm. FULL METAL JACKET` | `0xC756800DA816EFE1` | comp 324 `+0 = 296`（弹丸）|
| slot 5 `Magazine` | `Pistol 9x20mm. Extended` | `0xC891ACF9E8DBDA97` | comp 5 `+136=31 /+140=4 /+144=6 /+148=6`；comp 274 `+0x80 = 0xC891ACF9E8DBDA97` |

这解释了为什么 P-19 实体记录里 `ProjectileWeapon+0 = 0`、`WeaponCustomization+0x80 = 0` 却仍能正常开火：
**两个值都是休眠值，建造时被 delta 覆盖**。完整证据链与实机验证见
[BACKPACK-DOGS §28](BACKPACK-DOGS-26088801.md)。

### 7.5 复现

```bash
python tools/ref_scan.py delta-info
python tools/ref_scan.py delta-show 0xC756800DA816EFE1
python tools/ref_scan.py delta-ammo --component 324 --member 0 --slot AmmoType
```

### 7.6 坑

1. **组件索引是 build 相关的**。社区 HD2Runtime 0.28.1 文档里的索引（如 `[113] WeaponReload`）与本 build（`114`）不同 ⇒ 别跨 build 抄。
2. **delta 里的数值也会漂**。例：`RIFLE 5,5x50mm. FULL METAL JACKET` 在 HD2Runtime 0.28.1 文档里是弹丸 `276`，本 build 是 `281` ⇒ 以本档解出来的为准。
3. **data 段是字节流，不是行数组**：按字段扫实体记录 / 按行扫表都找不到它，必须解 delta。
4. `⚠` 引擎侧"无人机挂载为什么不跑 delta 链"还没证到代码；目前证据是行为侧（记录 = 0 不开火、= 296 开火且手感一致）+ 数据侧（delta 链就写这两个值）。

