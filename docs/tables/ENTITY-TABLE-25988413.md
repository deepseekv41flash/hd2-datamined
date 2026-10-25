# `generated_entities.dl_bin` 可写化 —— 实体/组件表离线改写（build 25988413）

> 状态：**✓ 已实机验证**（2026-10-22）。这是本项目第一条「47 MB 实体库」级别的离线改写路线。
> 相关：`docs/engine/DLBIN-SEALED-BOX.md`（封装与内容哈希模型的由来）、`WEAPONDATA-FIELDS`（字段图，见 `D:\mod\work\share-25988413-plaintext\WEAPONDATA-FIELDS.md`）。

---

## 1. 结论

`data/game/generated_entities.dl_bin` 与 `data/game/*.dl_bin` 设置表**受同一道内容哈希闸门约束**，并且同样可以「改字节 + 校正字 + 保哈希」离线改写。

四次实机验证：

| 实验 | 改动 | 结果 |
|---|---|---|
| AR-23 解放者站姿惩罚 | `WeaponData` 行 273 `FirePreventsMovement(+387)` 0→1 | ✓ 开火时无法移动 |
| MG-43 弹链机枪装填移动 | `WeaponReload` 行 239 `ReloadAllowMove(+1)` 0→1 | ✓ 装填时可以走动 |
| AR-23 可选弹种（眩晕） | `WeaponData +184`=8 ＋ `ProjectileWeapon +576`=195 | ✓ 能切换、弹种不同；眩晕太弱（见 §7） |
| AR-23 可选弹种（燃烧） | 同上，`+576` = AR-2 Coyote 的 140 | ✓✓ **命中点燃 + 火焰特效 + 持续伤害** |
| SG-8 Punisher 独立弹药池 | `WeaponData +184`=4 ＋ `WeaponRounds +68` = 140 | ✓✓ **能切弹 + 两池独立 + B 池自带弹道（只有一颗）** |

前两次已回滚/覆盖；后两次即当前装机状态（另有 MG-43 保留）。所有部署后**明文哈希都与 game.dll 烘焙值一致**。

## 2. 闸门证据

```
data/game/game.dll（49,075,800 B）
  0x2CAF028  = 8E49771B181FFAA1   ← generated_entities.dl_bin 明文 Murmur64A
  0x2CAF328  = D03587CCBD2FECFC   ← generated_damage_settings.dl_bin
  0x2CAF338  = 946A4FE5FAAAE076   ← generated_projectile_settings.dl_bin
```

现算 entities 明文哈希 = `8E49771B181FFAA1`，逐字节吻合 → 闸门覆盖 entities ✓

（哈希算法：MurmurHash64A，seed `0xDEADBEEFABAD1DEA`，乘数 `0xC6A4A7935BD1E995`；实现见 `D:\mod\work\devkit\tools\murmur64.py`）

## 3. 文件结构

不是 toc 容器，是「块序列」：

```
u32 type_id | 'LDLD' | u32 version(=1) | u32 type_id | u32 payload | u8 wide | 7 reserved   （28 B 头）
```

- 共 **275 个块**，第一个是 `EntitySettingsHashmap`（185,172 B），第二个 `EntityNetworkDataArray`（15,072 B）
- 组件块 payload = **`[hashmap][行数组]`**：
  - hashmap：16 B/条 `{u64 资源哈希, u32 值, u32 pad}`
  - 行数组：行结构由 `dl_library.dl_typelib` 给出（成员偏移/大小/类型），字段名来自 filediver 的 Go 定义
- 键 = **Murmur64A(资源路径)**，与 `LoadoutEntry`/`Equipment` 同一命名空间

### 第一批已定位的块

| 组件 | type | 块偏移 | hashmap | 行结构 |
|---|---|---|---|---|
| `WeaponDataComponentData` | `0x88E4DBB1` | `0x0193CCE8` | 11,936 B | 1,240 B × 374 |
| `WeaponReloadComponentData` | `0x991D454E` | `0x0057E9B8` | 8,128 B | 80 B × 255 |
| `ProjectileWeaponComponentData` | `0x45171B68` | `0x02CDE0B8` | 8,896 B | 616 B × 279 |
| `EquipmentComponentData` | `0x5357A825` | `0x0191B790` | 11,232 B | 232 B × 352 |
| `LoadoutEntryComponentData` | `0x4F2CF417` | `0x000B07D8` | 6,368 B | 32 B × 199 |

### 已实测字段

`WeaponDataComponentData`（行内）：

- `+356` `Ergonomics`（人机响应，float32）
- `+387` `FirePreventsMovement`（站姿惩罚，bool）
- `+84` `Spread`（水平/垂直 mrad）、`+96` `SpreadMods`
- `+0` `RecInfo`（后坐，60 B；Drift/Climb 各 28 B）、`+60` `RecModifiers`
- `+104` `SwayMultiplier`、`+128` `ScopeSway`、`+140` `NumBurstRounds`、`+144..156` 四种 FireMode

`WeaponReloadComponentData`（行内 80 B）：

- `+0` `ManualClearing`、**`+1` `ReloadAllowMove`**、`+4` `Ability`
- `+8` `ReloadAnimEvents[4]`（48 B）、`+56` `Duration`、`+60` `HasSharedDeposit`
- `+64..76` 四条 VO ThinHash

实测对照（`ReloadAllowMove`）：MG-43=0、MG-206=0、GR-8=0、AC-8=0；M-105 Stalwart=1、AR-23=1 —— 与游戏行为完全一致。

## 4. 校正字（这文件最难的一步）

47 MB 文件里**没有**随手可用的空位：

- 各组件行内 padding 全部 < 8 字节（和 damage 表一样）
- 文件末尾余量为 0（275 块正好排到文件尾）

唯一可用的 8 字节对齐空位是 **`EntitySettingsHashmap` 的空槽**：

```
每条 32 B：{u64 资源哈希, u64 components_offset, u64 count, u32 game_object, pad[4]}
空槽：{0, 0xFFFFFFFFFFFFFFFF, 0, 0xFFFFFFFF}
entry 基址 ≡ 4 mod 8 → entry+4 恰好 8 字节对齐，覆盖「资源哈希高4B + offset低4B」
count = 0 → offset 不被解引用，只有「资源哈希高半变垃圾」这一点副作用
```

**实机两次使用均无副作用**（2157 个空槽任选其一即可）。

备选方案（**✓ 已实机**）：在文件尾追加 12 字节（4 B 对齐 + 8 B 校正字），长度 +12。散布 36.0→2.0 那次的产物就是 47,259,408 B（末块 `payload_size` 560→572），已盘上回读，见 [FILE-ROUTE-WORKFLOW §4.7](../cases/FILE-ROUTE-WORKFLOW-26088801.md)。

## 5. 标准操作流程

```
1) 取明文            python tools/dlbin_seal.py open-key <游戏文件> --key refs/dlbin/keys/recipient.sk --out x.plain
2) 算原哈希          python -c "from murmur64 import murmur64; print('%016X'%murmur64(open('x.plain','rb').read()))"
3) 改目标字节        行地址 = 块 payload 起点 + hashmap 大小 + 行号 × 行大小 + 字段偏移
4) 解校正字          padding_word_for_hash(data, 0x20, 原哈希)  → 写回 0x20（空槽）
5) 校验              重算哈希必须等于原值；文件长度不变
6) 封装              python tools/dlbin_seal.py seal-key x.plain --key refs/dlbin/keys/recipient.pk --out x.sealed
7) 部署              覆盖 data/game/generated_entities.dl_bin，回读核对哈希与目标字节
```

工具：`D:\mod\tools\entities_modeb.py`（武器行/弹丸格改写 + 门禁 + 变异测试，见 §7）、`D:\mod\tools\dmg_custom_row.py`（自制伤害行）、`D:\mod\work\share-25988413-plaintext\parse_examples.py`（块/hashmap 解析示例）、`entity_fields.py`（typelib × filediver 字段表）。

## 6. 边界与未解

- **蹲下才能装填**：`WeaponReload` / `Wieldable` 结构里**没有** crouch/stance 字段（关键词 0 命中）。⚠ 推断该约束来自装填动画/状态机（资源层），不在 entities 表；改它要动画资源，工作量太大，**暂缓**。
- **`LoadoutEntry` 的 `selectable`：✗ 已否证**（2026-10-22）。该组件行只有 32 B = `{id, type(LoadoutItemType), dlc_pack_id, equipment_tags[5]}`，**没有 selectable**；带 selectable 的 `LoadoutItem`/`LoadoutItemCategory` 在实体库与 55 张 `data/game` 表里**均 0 命中** ⇒ 「是否已发布」不是离线可翻的字节，可见性由「实体是否挂 LoadoutEntry」+ 后端 id/DLC 归属决定。详见 §8。
- ~~Halt 的两套独立弹药池未解~~ → **✓✓ 已解并实机**（`WeaponRoundsComponentData` + `fnid=4`，见 §9）。
- 每行字段名来自 filediver Go 定义，**+396 之后的 WeaponData 尾部偏移可能有 ±4 漂移**（filediver 落后于本 build），改前须用真实取值核对。
- 哈希闸门只保「内容不变性」，不保语义；写歪了引擎会读到垃圾而未必崩溃（例：把 `Disabled` 位置写坏只会行为异常）。

## 7. 可选弹种：给武器挂备用弹（引擎原生 `ProgrammableAmmo`）—— ✓✓ 已实机

### 7.1 两格（都在本文件，一次校正字搞定）

| 引用名 | 位置 | 语义 |
|---|---|---|
| `fnid` | `WeaponDataComponentData` 行 **`+184`**（`FunctionInfo.function_id`，u32） | **8 = 引擎原生 `ProgrammableAmmo`**：装上后「切弹」由引擎自己做，我们不用写任何逻辑 |
| `alt` | `ProjectileWeaponComponentData` 行 **`+576`**（u32） | 备选弹丸 **type id**（⚠ 不是行号，见下） |
| `prim` | 同行 `+0`（u32） | 主弹丸 type id（模式 A，一般不动） |

### 7.2 离线全表互证（不是猜的）

```
WeaponData   type=0x88E4DBB1 rows=374 slots=746 keys=373   # 11,936 + 1,240×374 = 475,696 = payload ✓
Projectile   type=0x45171B68 rows=279 slots=556 keys=278   #  8,896 +   616×279 = 180,760 = payload ✓
+184 分布：{0:355, 2:1, 3:5, 4:1, 6:1, 8:6, 10:1, 11:3}
相关性 (+184, 有备选弹)： (8,True)=6   (8,False)=0
```
- `8` 只有 6 把，且**只有这 6 把有备选弹** ⇒ 与 b30 运行期普查「`+0xB8==8` ⟺ 有备选射弹」逐字一致
- 这 6 把 = AC-8 / GR-8 / P-33 / P-92 Warrant / RL-77 / StA-X3（发射器族，原版就有 A/B）
- b30 普查当时看到 7 把 = 6 原生 + 我们打过补丁的主宰；**离线原版正好 6** ✓

命名钉死（名称表 = `b30-speargun-ammo-census.lua` 里 130 条 `key|name`，键是资源路径的 Murmur64A）：

```
AR-23 Liberator key=0x968211C0033DCE64 → 行 273 @0x19925FC
   Ergonomics@+356 = 65.0   FirePreventsMovement@+387 = 0   fnid@+184 = 0
```
= 先前实机改过 `+387` 的那一行 ✓（名称表 ↔ 哈希键 ↔ 离线行 ↔ 实机行 全闭死）

弹丸格是 **type id**（1..355，是价值集合，不是索引）—— 物理自证：

```
AC-8 prim 117 -> cal 20mm  820 m/s  mass 120     ← 20mm 机炮 ✓
GR-8 prim 155 -> cal 85mm  250 m/s  mass 3300    ← 85mm 火箭 ✓
（若按“行号”解释会得到 cal 5 / speed 1 m/s 的荒谬值 ⇒ 否证行号说）
```

### 7.3 实机结果

| 轮次 | 改动 | 用户观测 |
|---|---|---|
| 眩晕 | `fnid` 0→8，`alt` 0→**195**（Halt 眩晕弹：伤害行 184 = 6 伤害 / AP 2-2-2-2 / 状态 40 强度 1.0） | ✓ 能切换、弹种真的不同、伤害变了；**眩晕太小看不出来**（单颗只等于 Halt 满喷 20 颗的 1/20） |
| 燃烧 | `alt` →**140**（AR-2 Coyote：伤害行 126 = 75 伤害 / AP 3-3-3 / 状态 **5 = 燃烧** 强度 2.0） | ✓✓ **命中点燃 + 火焰特效 + 持续伤害** |

### 7.4 规则与边界

- **备选弹只贡献「伤害 + 状态」**，弹道（颗粒数/初速/质量/单位）来自**主弹行** ⇒ AR-23 切成燃烧弹仍是「1 颗粒 / 900 m/s」，只有伤害与点燃变
- HUD 的弹种图标/名称跟备选弹走（实测会显示「眩晕弹」这类标签）；动作/音效跟主弹
- **引用**别人的伤害行不产生连带（我们不写它）；**改写**共享行才会（AR-23 的伤害行 116 同时服务 AR-23A / StA-52 / M-105）
- 状态 id 对照（b3x 系列反解）：`5`=火 · `39`=眩晕 · `42/44/43/45`=毒气 · `37`=电击 · `38`=未命名

### 7.5 自制伤害行（想要自定义数值时）

```
python tools/dmg_custom_row.py --plain <vanilla damage> \
  --source-type 116 --target-type 186 --status 39 --strength 25 --host-type 296 --out x.plain
```

- 「无主行」判据：没有任何射弹引用 + 没有任何爆炸行引用（爆炸表 = stride 152 / 424 行，`+4` 是伤害行 id）
- 整行抄源行（伤害/坚固/穿甲/demo/stagger/push），只改状态；`+0` 保留目标行自己的 id
- 伤害表行内没有 8 字节空位 ⇒ **校正字写在另一条无主行的空状态槽**里（`--host-type`）
- 门禁：长度不变 / 差异 ⊆ 目标行+校正字 / 哈希不变 / 读回 / 源行未被改动

### 7.6 工具与门禁

```
python tools/entities_modeb.py show   <plain> [--weapon AR-23]
python tools/entities_modeb.py edit   <vanilla_plain> <out_plain> --weapon AR-23 --fnid 8 --alt 140 [--keep-mg43]
python tools/entities_modeb.py mutate <edited_plain>        # 变异测试：翻校正字一位，门禁必须报红
```

门禁 `G1 长度不变 / G2 差异 ⊆ 目标格+校正字 / G3 哈希回到原值 / G4 每格读回 / G5 校正字 8 对齐`；
变异测试 = 「翻一位 ⇒ 哈希必变 ⇒ FAIL；恢复 ⇒ PASS」——证明门禁不是摆设。

### 7.7 部署纪律（本轮血泪）

1. **部署前先读回已装状态**。本轮发现伤害文件里还留着旧实验（AR-23 伤害 90→900），差点把燃烧弹的结果污染成“伤害变了是因为火”。
2. 一次只改一个变量；两个文件分别门禁、分别备份。
3. 备份与回滚路径写进交付报告（`D:\mod\refs\dlbin\backup\`）。

## 8. `LoadoutEntry` / `selectable` —— ✗ 否证

```
LoadoutEntryComponentData 行（32 B × 199）：
  +0  id (u32，后端物品 ID)
  +4  type (u32，LoadoutItemType：1=主武器 2=支援 3=副武器 4=投掷 6=背包)
  +8  dlc_pack_id (u32)
  +12 equipment_tags[5] (5 × u32)
```

实测对照：AR-23 行 103 type=1 · M-105 行 134 type=2 · MG-43 行 184 type=2 · CQC-19 行 44 type=3 · G-3 Smoke 行 84 type=4 · K-9 背包 行 34 type=6 —— 全部符合枚举 ✓

**没有 `selectable`**：32 B 已被上述字段占满，一个字节不剩。带 `selectable` 的 `LoadoutItem` / `LoadoutItemCategory` 在实体库（两种哈希空间）与 55 张 `data/game` 表里 **0 命中**；`LoadoutPackageComponent` 也只有 `{bundle_tag, package, audio_resource, include_default_customizations}`。

⇒ 「显示未发布物品」**不是离线数据层的开关**：可见性由「实体是否挂 `LoadoutEntry` 组件」+「后端 id / 账号 / DLC 归属」决定。

> ⚠ 2026-10-25 补充：这句只对**军械库显示**成立。**战备**可以走 `generated_stratagem_settings +0xC8`「额外战备」**不进军械库、直接进任务**（7 条未发布战备已实机可用，见 [UNRELEASED-STRATAGEMS-26088801](UNRELEASED-STRATAGEMS-26088801.md)）。老 b18 路线能做是因为它**运行期**往登记表追加记录，正好印证数据层没有这个开关。


## 9. 独立弹药池：两套完整弹药（各带自己的弹道）—— ✓✓ 已实机

### 9.1 与 §7 的区别（两条是**不同**的机制，别混）

| | 备选弹 §7（`fnid=8`） | 独立弹药池（`fnid=4`） |
|---|---|---|
| 弹丸放哪 | `ProjectileWeaponComponentData` 行 `+576` | `WeaponRoundsComponentData` 行 `+64`/`+68`（A/B 两格） |
| 弹道（颗粒/初速/质量） | **沿用主弹**（b33 用户观测：1 颗还是 1 颗） | **B 池用自己的弹丸**（实测：霰弹枪 B 池变单颗粒） |
| 弹药池 | 与主弹共享一个 | **A/B 各自独立**：`+72` 弹匣 A/B、`+80` 备弹 A/B |
| 原版使用者 | AC-8 / GR-8 / P-33 / P-92 / RL-77 / StA-X3 | **只有 SG-20 Halt**（187 / 195） |

### 9.2 `WeaponRoundsComponentData` 几何（typelib 直接给）

```
type 0x66081072   size 4,336       block @0x005A6E50
  +0     800 B = hashmap（50 槽 × 16 B）
  +800 3,536 B = 行数组（26 行 × 136 B）
```

行结构（逐成员 + 25 行实测）：

| 行内 | 大小 | 实测解读 |
|---|---|---|
| +0 | 64 | 16 × float，全 1.0（**未解**，疑似散布/倍率数组）⚠ |
| **+64** | 8 | **弹丸 type id A / B** |
| **+72** | 8 | **两个「各自独立」的弹匣容量 A / B**（float）。★ 实机：Sweeper 切到 B 后两种模式**各显示 7 且互不影响** ✓；面板 Capacity = A+B（Halt 8+8=16 ✓） |
| **+80** | 8 | **备弹 A / B**。★ 单位随换弹方式：逐发装填=**发**（Halt 60）、整匣换弹=**匣**（AR-23 8） |
| **+88** | 4 | **初始量**（Halt 32 发 ✓ / 整匣换弹武器应为匣数） |
| +88 / +92 | 8 | 未解（霰弹族 32 / 1；P-69 Veto 6；AC-8 5）⚠ |
| +96 | 8 | 两个 float（多为 0；Veto 8.0）⚠ |
| +108 | 24 | 6 个 hash，霰弹族**共享同一组**（疑似弹种显示名）⚠ |
| +104 / +132 | 2 | u8 ⚠ |

### 9.3 全表相关性：只有 Halt 是 B≠A，也正好只有它是 `fnid=4`

```
武器                    fnid  弹丸A 弹丸B  弹匣A/B  备弹A/B
SG-20 Halt                 4    187   195     8/8     60/60   ← 唯一 B≠A
SG-8 Punisher              0    264   264     8/8     60/60   ← B 只是占位
SG-8S Slugger              0    244   244     8/8     60/60
SG-451 Cookout             0    352   352     8/8     60/60
SG-97 Sweeper              0    266     0     7/0     70/70
SG-88 Break-Action         0    220     0     2/0     40/20
DBS-2 Double Freedom       3    322     0     2/0     40/40
AC-8 Autocannon            8    117     0    10/0      0/0    ← 走 §7 那条机制
```

另：这 25 把**全部没有 magazine 行**，而 AR-23 有（行 203）⇒ 两张表看起来是互斥的两条路。

### 9.4 实验 A（实机三联验证）

```
SG-8 Punisher.fnid     @0x01973D7C   0 -> 4
SG-8 Punisher.rounds_b @0x005A72E0 264 -> 140   （AR-2 Coyote 燃烧弹）
```

用户观测（原话）：**「能切弹，两个池独立，B 池是只有一颗。」** ⇒

- `fnid=4` = 双弹药池开关 ✓
- 两池的**弹种、弹道、弹匣**各自独立 ✓（Sweeper 复测：切到 B 后两种模式各 7 发，互不影响）
- ⚠ **但备弹是共用的**（用户实测；与 Halt 原版一致）⇒ 行内 `+80` 的 A/B 两格只是同值镜像，不是两套账 ✗
- B 池弹丸**自带弹道**（霰弹枪的 B 池变成单颗粒）✓ —— 这是 `fnid=8` 做不到的

### 9.5 空位（给没有 rounds 行的武器新增时用，不用扩容）

```
hashmap 50 槽 / 25 键  → 25 个空槽 ✓
行数组  26 行 / 已用 0..24 → 空行 25 ✓
```
⇒ 新增一行 = 写 16 B 的 hashmap 条目 + 一条 136 B 的行，**文件长度不变**，哈希照旧可保。
⚠ 未试：与 `WeaponMagazineComponentData` 行并存（AR-23 属于这种）会不会打架。

### 9.6 工具

```
python tools/entities_modeb.py show <plain> --weapon "SG-8 Punisher"
python tools/entities_modeb.py edit <vanilla> <out>     --weapon AR-23 --fnid 8 --alt 140 --keep-mg43     --edit "SG-8 Punisher:fnid:4" --edit "SG-8 Punisher:rounds_b:140"
```
新增格：`rounds_a` `rounds_b`（弹丸）· `rounds_mag_a/b`（弹匣 float）· `rounds_reserve_a/b`（备弹）
多重 `--edit` 支持一次改多把武器；门禁与变异测试同 §7.6。

### 9.7 实验 B：给「整匣换弹」武器加独立池 —— ✗ 否证（三种变体都崩）

目标：让 AR-23（原版走 `WeaponMagazine` 模型）也拥有两套弹药。做法是给它**新增**一条
`WeaponRounds` 行（新键写进自然槽 + 用空行 25）+ `fnid=4`。

| 变体 | 内容 | 结果 |
|---|---|---|
| v1 | 新行：A=281 / B=140（Coyote 燃烧）· 弹匣 30 · 备弹 45 · `+108` 六个弹种 hash **清零** | ✗ **打开切弹页面时崩**（0xC000000D） |
| v2 | 整行克隆 Halt（`+108` 用原值），只改弹丸/容量 | ✗ 崩（同一位置） |
| v3 | 按 wiki 真值：弹匣 45/45 · 备弹 8/8 匣 · 初始 6 | ✗ 崩（同一位置） |
| v4 | 再**删掉 AR-23 的 magazine 条目**（整表重排 275 键），彻底换成 rounds 模型 | ✗ 崩（同一位置） |

三次崩溃的签名完全一致：`0xC000000D`、`ntdll+0x86BE7`、1 个线程、栈底是
`ExitProcess → LdrShutdownProcess → PlayFab 卸载`（= 引擎致命错误后的收尾路径，抓不到原始触发点）。

**结论**：在 build 25988413 上，「新增 rounds 行 + `fnid=4`」**不足以**让整匣换弹武器获得可用的双池 ——
崩点在**打开切弹页面**（不是加载、不是射击），说明页面需要的东西**不在 `generated_entities.dl_bin` 里**
（大概率是资源/UI 侧，只对原生双弹种武器存在）。

**安全边界（现结论）**：双池只能在**原生自带 `WeaponRounds` 行**的 25 把武器上做 ——
实验 A（SG-8 Punisher）证明这条路零结构风险 ✓✓；给别的武器**新增**行 = 未证且已三次失败 ✗。

**副产品（本轮新增且有价值）**：
1. 组件 hashmap 是**开放寻址表**：`slot = key % slots`，冲突线性探测。对 WeaponRounds(50)/WeaponMagazine(552)/WeaponData(746)/ProjectileWeapon(556) 四张表校验，**探测失败均为 0** ✓
   ⇒ 往表里加/删键时**必须**遵守这个规则（随便找空槽写 = 引擎查不到，实验静默失效）。
2. `WeaponMagazineComponentData` 几何修正：**552 槽 × 16 B + 277 行 × 160 B**（早先误记为 604/144）。
3. rounds 行字段语义经 wiki 校准：`+72` 的 A+B = 面板 Capacity、`+80` = 备弹（单位随换弹方式）、`+88` = 初始量。
4. AR-23 原版真值：**Capacity 45 · Spare Magazines 8 · Starting Magazines 6**（此前误记 30/45）。
5. 删条目要**整表重排**（直接清零会截断别人的探测链）。

### 9.8 正向配方：给「已有 rounds 行」的武器加第二弹种 —— ✓✓ 实机（SG-97 Sweeper）

这是本机制目前**唯一安全**的落地方式（前提：该武器**原生就有** `WeaponRounds` 行）。

**配方（6 格）**：

| 格 | 位置 | 改成什么 |
|---|---|---|
| `fnid` | `WeaponData` 行 `+184` | `0 → 4`（双弹药池开关） |
| `rounds_b` | `WeaponRounds` 行 `+68` | 第二弹种的**弹丸 type id** |
| `rounds_mag_b` | 行 `+76` | 第二池的**弹匣容量**（抄该武器自己的原弹匣容量） |
| `rounds_reserve_b` | 行 `+84` | 与 A 格相同（引擎实际共用备弹） |
| `rounds_flag` | 行 `+104` | `1`（声明存在第二池） |
| `+108` 六个 hash | 行内 24 B | 照抄同族**双池**武器的值（Punisher / Cookout / Halt 三家完全相同） |

**实例（SG-97 Sweeper / key `0xDCD1C835407EF7BA` / rounds 行 7）**

```
fnid             0 -> 4
rounds_b         0 -> 352      ← SG-451 Cookout 的燃烧弹（20 颗粒 · 120 m/s · 16 伤害 + 燃烧 0.6/颗）
rounds_mag_b     0 -> 7.0
rounds_reserve_b 70（本来就是 70）
rounds_flag      0 -> 1
+108 六个 hash   = 整段拷 Cookout
```

**实机结果（用户观测，原话）**：**「页面能开，能切。切到 B 后是 20 颗燃烧弹丸。备弹为 70，两种模式容量都是 7 且独立。」**

⇒ 三条结论一次拿到：
1. `fnid=4` + 原生 rounds 行 = 可用的双池（第 2 个独立样本，第一个是 Punisher）
2. **B 池的弹道是它自己的**（Sweeper 原版 7 颗粒 → B 变成 20 颗粒）
3. **弹匣 A/B 独立、备弹共用**（容量各 7，互相不影响）

**这是目前唯一能给武器「加弹种」的成品路线**；而给**整匣换弹**武器新增 rounds 行（§9.7）已四次失败、不要重试。
