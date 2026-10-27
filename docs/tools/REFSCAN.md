# `ref_scan.py` —— 表行 id / 配件 delta 的引用反查

> build `26088801` 实测；只读，不碰游戏目录、不启动游戏。
> 解决的问题：**"某个 id 在整个档案里被谁引用"**，以及**"原版武器开火用的弹丸/资源到底写在哪"**。
> 起因：P-19 Redeemer 实体记录里 `ProjectileWeapon+0 = 0` 却能正常开火；靠本工具找到了真正的引用 ——
> 它在 `generated_entity_deltas.dl_bin` 的**弹种配件 delta** 里（证据链见
> [BACKPACK-DOGS §28](../tables/BACKPACK-DOGS-26088801.md)）。

## 1. 两条判据（为什么这样找）

| 判据 | 子命令 | 做法 | 适用 |
|---|---|---|---|
| **值域** | `columns` | 扫每个 4 字节槽，保留"整列都是目标表 id（外加 0）"的槽 | 找**引用面**：不需要预先知道偏移，能发现"另有一套引用写法" |
| **精确值** | `exact` | 扫全档任意对齐的 `u32 == VALUE` 窗口 | 找**具体一条引用**：随机 u32 撞上 355 分之一目标的概率是 1/4.3e9，本档 4 字节窗口约 1,180 万 ⇒ 期望误报 0.003 次，**命中即证据** |

`exact` 的命中会归因到 `(文件, 块类型, 行号, 行内偏移, 实体键)`，所以能区分：
真引用 / 哈希图里的"行号恰好等于该值" / 结构字段（settingsIndex、成员偏移）等巧合。

## 2. 子命令

```bash
# 全档扫 u32 == 296，逐处归因（--row-only 只看落在行数组里的）
python tools/ref_scan.py exact 296 [--row-only] [--max-show 200]

# 找"值域落在弹丸表 id(1..355) 里"的列：实体组件块 + 全部 generated 表
python tools/ref_scan.py columns --for-projectile [--min-hits 3]

# 打印某个实体的全部组件行（非零 u32 槽；命中目标 id 会标出来）
python tools/ref_scan.py entity 0x3575AABC5F1F9326 [--raw 64]

# entity delta 存储：几何、条目数、组件索引直方图、最常见的 (组件,偏移,宽度)
python tools/ref_scan.py delta-info

# 某个 AddPath（配件/弹种资源哈希）的 delta 打了哪些补丁
python tools/ref_scan.py delta-show 0xC756800DA816EFE1

# 列出所有配件 delta 补丁（可 join 配件总表 CSV 带名字；可按组件/成员/槽位过滤）
python tools/ref_scan.py delta-ammo --component 324 --member 0 --slot AmmoType
```

参数：`--plaintext`（明文缓存目录，默认 `D:\mod\refs\dlbin\plaintext-26088801`）、
`--names`（`dl-type-names.json`）、`--entity-names`（`entity-locid-names.json`）、
`--max-id`（目标 id 上限，默认 355 = 弹丸表行数）。

## 3. entity delta 存储（`generated_entity_deltas.dl_bin`）

全档唯一块 `0x683E604F` = `ComponentEntityDeltaStorage`（352,345 B）：

| 区 | payload 内偏移 | 条数 | 每条 | 结构 |
|---|---:|---:|---:|---|
| header | `+0` | 5 组 | 80 B | 每组 `(u64 offset, u64 count)` |
| hashmap | `+0x50` | 1024 槽（572 非空）| 16 B | `{u64 AddPath, u32 settingsIndex, u32 pad}` |
| settings | `+0x4050` | 1144 | 8 B | `{u32 componentCount, u32 firstComponent}` |
| component | `+0x6410` | 1038 | 12 B | `{u32 组件索引, u32 firstDelta, u32 deltaCount}` |
| delta | `+0x94B8` | 6119 | 12 B | `{u32 成员偏移, u32 宽度, u32 data 偏移}` |
| data | `+0x1B38C` | 240,817 B | — | 被打进去的字节本身 |

**组件索引 → 组件名（本 build 实测；换 build 必须重测）**：
`5` = `WeaponMagazineComponentData` · `114` = `WeaponReloadComponentData` ·
`119` = `WeaponRoundsComponentData` · `239` = `WeaponDataComponentData` ·
`274` = `WeaponCustomizationComponentData` · `324` = `ProjectileWeaponComponentData`。

## 4. 已用它得到的结论（本 build）

| 结论 | 命令 |
|---|---|
| `ProjectileWeapon+0` 只有 265/279 个武器非零；P-19、P-2 等 14 个为 0，其中 12 个靠 `WeaponRounds` 给弹丸，P-19/P-2 靠**弹种 delta** | `columns --for-projectile` |
| P-19 默认弹种 `PISTOL-SMG 9x20mm. FULL METAL JACKET`（AddPath `0xC756800DA816EFE1`）的 delta 把 comp 324 `+0` 写成 **296** | `delta-show 0xC756800DA816EFE1` |
| P-19 默认弹匣 `Pistol 9x20mm. Extended`（AddPath `0xC891ACF9E8DBDA97`）的 delta 写 comp 5 容量组 + comp 274 **`+0x80` = 该 AddPath** | `delta-show 0xC891ACF9E8DBDA97` |
| 全档 67 个弹种配件写 comp 324 `+0`；15 个备选弹种（slot 7）写 comp 119 `+68` | `delta-ammo --component 324 --member 0 --slot AmmoType` |
| P-2 Peacemaker 默认弹种 `HOLLOW POINT` 的 delta → comp 324 `+0 = 342`（与 P-19 不同） | `delta-show 0x70564BCA8BDD43D1` |
| 全档 `u32 == 296` 共 180 处，**只有 1 处**是弹丸引用（delta data 段 `0x027EF4`）；其余是哈希图行号/图数据/结构偏移的巧合 | `exact 296` |

## 5. 边界与坑

1. **组件块靠 typelib 拆几何**：`geometry`/`check_geometry` 不过的块会被跳过（本 build 265/275 通过），
   所以 `columns` 的"引用面"只在可拆块内完整；`exact` 不受影响（它按块边界归因，不需要行几何）。
2. **哈希图里的"行号"是巧合高发区**：`{u64 key, u32 row, u32 pad}` 里 `row == VALUE` 很常见，`exact` 会把它标成
   "非行数组区"，别当真引用。
3. **非 4 对齐命中会跨字段**：例如 `MountComponentData` 的 9 行在 `+43` 命中 296，其实是 `+40` 的 f32 尾部
   +`+44` 的 1 拼出来的巧合；`exact` 会打印对齐槽的值提示这种情形。
4. **实体 delta 的 data 段是字节流**：不是行数组，按字段/按行都扫不到，必须解 delta 三级索引。
5. **组件索引与数值都是 build 相关的**：别把本 build 的 `324`、`296` 当成跨 build 常量（社区 HD2Runtime 0.28.1
   文档里 Liberator 的 FMJ 弹丸是 `276`，本 build 是 `281`）。
6. 只读：不解封游戏目录、不写 `data/game`、不启动游戏；`--plaintext` 指向已解好的明文缓存即可。

## 6. 相关文档

* [BACKPACK-DOGS §28](../tables/BACKPACK-DOGS-26088801.md) —— 用它破的案：P-19 的原版运行逻辑 + 实机验证
* [WEAPON-CUSTOMIZATION-DECODED §7](../tables/WEAPON-CUSTOMIZATION-DECODED.md) —— 配件表 → entity delta 的落地链
* [RESDEP](RESDEP.md) —— 反过来：从一个武器/实体出发把**资源**依赖扫全（驻留计划）
