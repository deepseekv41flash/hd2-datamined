# 武器配件在明文表上吗？—— build 26251122 实测（三层模型复核）

> 起因（2026-10-30）：用户问「武器配件相关字段在明文表上吗？之前 memmod 时期做过但没做出来」。
> 旧文档：`HD2SDK-CommunityEdition/docs/attachment-layers.md`（2026-10-08，三层模型 L0/L1/L2）＋
> `las22-unlock-analysis.md`（LAS-22 解锁路线）。本篇是**在新 build 上的复核**，结论一句话：

**L0（出生默认挂载）✓✓ 在明文表上，已完整解出、可直接改文件；L1（可选/解锁清单）⚠ 明文里有候选表但未解；L2（玩家当前选择）✗ 仍不在明文。**

---

## 1. 三层在新 build 的位置

| 层 | 旧文档（memmod 期） | 本 build 26251122 实测 |
|---|---|---|
| **L0 出生默认挂载** | 运行期 4872 B 记录，Suzuka 用**内存写 8 B** | **✓✓ 明文表**：`WeaponCustomizationComponentData`，块 `0xEBA8F3D0`，在 **`generated_entities.dl_bin`** |
| **L1 可选配件/解锁清单** | 运行期登记表（184 B 记录 + 24 B 映射 + 管理槽 512×148 + 进度组 112 B/行），LAS-22 用 6 个硬编码 RVA 改 | **⚠ 未定**：明文里有 `generated_weapon_customization_settings.dl_bin`（30,824 B，9 个结构化块），是否就是 L1 的数据源**待验证** |
| **L2 玩家当前选择/预设** | 三方都没找到 owner | **✗ 仍不在明文**（推测在档案/服务端） |

> 旧文档 §6 明确记过：第三方把 L0 标为 `not proven current player selection`、受控实验得
> `NO_OWNER_IN_BOUNDED_SCOPE`。**「改 L0 到底会不会改出生挂载」这一环，当年我们也没有实机验证过。**

---

## 2. L0 表结构（离线实测）

| 项 | 值 |
|---|---|
| 块类型 id | `0xEBA8F3D0`（`typelib.type_id_of("WeaponCustomizationComponentData")`） |
| 位置 | `generated_entities.dl_bin`，275 块中的 1 块，`payload = 966,056 B` |
| 组成 | `ComponentIndexData` **6,272 B**（**392 个 16 B 槽**：`u64 实体键 + u32 行号 + u32 0`）＋ `WeaponCustomizationComponent` **959,784 B** |
| 行 | **196 行 × 4,872 B**（`959784 / 4872 = 197`，实占 196 行） |
| 行内布局 | `+0x00` 起最多 **10 个 entry**，每个 `8 B = (u32 slot, u32 optionId)`；**`slot == 0` 为终止符** |

slot 枚举（与旧文档一致）：`1=Underbarrel 2=Optics 3=PaintScheme 4=Muzzle 5=Magazine 6=AmmoType 7=AmmoTypeAlternate 8=Internals 9=Triggers`

### 普查结果（`refs/weapon-customization-l0-26251122.json`）

| 指标 | 值 |
|---|---|
| 行总数 | 196（有名 166 / 无名 30） |
| **非空 L0** | **116 行**；空 80 行 |
| slot 出现次数 | 1:61、2:91、3:58、4:49、5:30、6:26、7:4、8:11、9:11 |
| kind 分布 | primary_weapon 59、support_weapon 45、sidearm 28、unit 20、interactable 7、throwable 6 |

optionId → 名字的翻译用第三方目录 `refs/hd2runtime-repo/research/weapon-attachments-F5FEE03DCFDB.json`
（241 条，含 `debugName`、`slots`、`addPath`）—— **100% 对得上**，例如：

| 武器（行） | L0 |
|---|---|
| Evictor（28） | `2:REFLEX SIGHT` → `3:Default` |
| Punisher Plasma（34） | `2:HOLOGRAPHIC SIGHT` → `3:Default` |
| Slugger（31） | `2:TUBE REDDOT 1,5x` → `3:Default` |
| Trenchgun 系（35） | `1:Trenchgun Bayonet` → `2:No Optics` → `4:No Muzzle` → `3:Default` |
| Knight（19） | `5:Extended 弹匣` → `6:FULL METAL JACKET` → `4:No Muzzle` → `2:REFLEX SIGHT` → `3:Default` |
| **Flamethrower / Crisper / Sterilizer** | **空**（支持武器没有配件面） |

---

## 3. 与旧文档的逐字节吻合（这是最硬的证据）

旧文档记 Suzuka 那 8 字节写的目标是 `stride=4872 index=113 offset=16`，且原文 `original` 前 16 B =
`01000000 452f0571 | 03000000 3de6fb80`（= `(slot1, Bayonet)` + `(slot3, Default 涂装)`，然后终止符）。

本 build 明文实测：

| 行 | 名字 | 键 | L0 |
|---|---|---|---|
| **114** | **Constitution** | `0x7B75E5132FFD4CA6` | `(1, 0x71052F45 Bayonet)` → `(3, 0x80FBE63D Default)` → **`+0x10` 为 `(0,0)` 终止符** |
| 113 | Amendment | `0x0F83639AB8C86165` | `(1, Bayonet)` → `(2, 0xE8C28B34 COMBAT SCOPE 4x)` → `(3, Default)` |

⇒ **Constitution 的 L0 与 Suzuka payload 的 `original` 逐字节一致**，`+0x10` 那一格正是它写瞄具的位置。
⇒ 顺带发现：**Amendment 这一行在官方数据里本来就带 4x 战斗瞄具**（= 官方自己用同一个机制做过"预装瞄具"的武器）。

---

## 4. 实验 J（设计好、未装盘）：文件路线复刻 Suzuka

当年这事要内存写 8 字节 + 6112 B 签名扫描；现在**只要改明文**。

| 项 | 值 |
|---|---|
| 目标 | `generated_entities.dl_bin` → 块 `0xEBA8F3D0` → Constitution 行（键 `0x7B75E5132FFD4CA6`） |
| 改动 | `+0x10` 的 8 B：`(0,0)` → **`(2, 0x4672A011)` = HOLOGRAPHIC SIGHT**（或 `0x67E0A480` = SNIPER SCOPE 10x） |
| 小端值 | `value = (optionId << 32) | slot` = `0x4672A01100000002` |
| 命令 | `python tools/entity_field_set.py set --block 0xEBA8F3D0 --key 0x7B75E5132FFD4CA6 --field 0x10 --type u64 --value 0x4672A01100000002 --expect-old 0 --out out/…plain`，再 `dlbin_seal.py seal-key` + 覆盖 `data/game/generated_entities.dl_bin` |
| 判据 | 军械库预览 / 进游戏看 **Constitution 上有没有全息镜**；同时全表 diff 确认其它行一字节未动 |
| 判读 | 有镜子 ⇒ **L0 就是出生挂载来源**（旧文档那个未验证的环被补上，以后所有配件改动都能走文件）<br>没镜子 ⇒ L0 只是"资源默认定义"、被 L2/服务端覆盖 ⇒ 与第三方结论一致，路线改走 L1 |

### 已装盘（2026-10-30 20:4x，单变量）：先撤胶囊，再只写这 8 字节

| 项 | 状态 |
|---|---|
| `spray_capsule_radius` | **已撤回原版**（`+0x10 = 0.0`，实体表恢复到与明文缓存**逐字节一致**） |
| Constitution 行 `+0x10` | `00 00 00 00 00 00 00 00` → **`02 00 00 00 11 a0 72 46`**（`(slot 2, 0x4672A011 HOLOGRAPHIC SIGHT)`） |
| 哈希 | G1/G2/G3/G4/G6/G7/G8 全 PASS；与原版明文差异 **6 字节**（5 字节字段 + 1 字节末块尺寸） |
| 封包/装盘 | `recipient.pk` 合法 MAC，47,259,456 B；`recipient.sk` 解封回读与目标明文逐字节一致 |
| 装盘后 L0 实读 | `(1, Bayonet)` → `(3, Default)` → **`(2, HOLOGRAPHIC SIGHT)`** → 终止符 |

⚠ 注意 entry **顺序不是按 slot 排序**：新项被追加在 `+0x10`（原终止符位），所以顺序是 1、3、2。
Suzuka 当年也是这么写的（写 offset 16），引擎应按 slot 查表、不依赖顺序 —— 若实验失败需回来怀疑这一点。

判读：

| 现象 | 结论 |
|---|---|
| Constitution 上**出现全息镜**（军械库预览/进游戏模型） | ✅ **L0 = 出生挂载来源**，旧文档 §6 那个未验证环补上；以后配件改动全走文件 |
| **毫无变化** | L0 只是"资源默认定义"、被 L2/服务端覆盖 ⇒ 与第三方 `NO_OWNER_IN_BOUNDED_SCOPE` 一致 ⇒ 转攻 L1 |
| 军械库改装页把"全息镜"显示为**已选** | 比只看模型更强的证据（UI 也读 L0） |
| 其它枪外观也变了 / 崩 | 写错行 ⇒ 立刻回滚 |

回滚：`cp "D:/mod/backups/spray-capsule/generated_entities.vanilla.dl_bin" "…/data/game/generated_entities.dl_bin"`

> 注：粒子的 F 档（65 m 远射喷火器）仍在装盘状态，与配件实验互不影响。

---

## 5. L1 的下一步（离线、零风险）

`generated_weapon_customization_settings.dl_bin`（9 块、30,824 B，块类型 `0x1E604234`，行结构是
`{u64, u32×5, u64×2, struct16, struct16, u32}` 这种复合体，**不是**平坦数组）。
下一步：把 9 个块逐字段解出来，与第三方 `attachment-unlock-lists-F5FEE03DCFDB.json`
（52 把武器的可选清单）对照 —— 若能对上，**L1 也能文件化**，LAS-22 那条当年没做出来的路线就有了替代方案。

---

## 6. 实机结果（2026-10-30 21:0x）：**L0 不驱动出生挂载 = ✗ 否证**

玩家实机：**毫无变化**（Constitution 没有出现全息镜，改装页也没把全息镜显示为已选）。

⇒ **L0（`WeaponCustomizationComponentData`）只是"资源默认定义"，不是出生挂载来源** ——
与第三方 `meaning: 'not proven current player selection'` / `NO_OWNER_IN_BOUNDED_SCOPE` / `selectedAttachmentOwnersProven: 0` **完全一致**。
⇒ 已回滚到原版实体表（与明文缓存逐字节一致，`Constitution +0x10 = 00…`、`FLAM-40 +0x10 = 0.0`）。

---

## 7. L1 在明文表里吗？—— **一半在，一半不在**（2026-10-30 实测）

用第三方解锁清单（52 把武器 / 1,322 条 option）当指纹，扫全部 55 张明文表：

### 7.1 ✓ **配件定义在明文**

| 证据 | 结果 |
|---|---|
| 204 个去重 optionId 的落点 | **`generated_weapon_customization_settings.dl_bin` 命中 204/204（各出现 1 次）**；`generated_entities.dl_bin` 命中 60 个（那是 L0 默认项） |
| 文件结构 | 9 个块，块类型 `0x1E604234`，**正好按 9 个槽位分组** |
| 分组实测 | 块0=`AmmoType`(+Alt) 84 项、块3=`Magazine` 45、块4=`Muzzle` 33、块5=`Optics` 9、块6=`PaintScheme` 12、块7=`Triggers` 3、块8=`Underbarrel` 12、块2=`Internals` 3、块1=混合 3 |
| 记录里能读到 | `optionId` + 3 个 id + **`addPath`（u64，与第三方字段逐字节一致，如全息镜 `0xE478A2FB566C818A`）** |

⇒ **"有哪些配件、各能装哪个槽、是什么效果资源"= 明文可改。**

### 7.2 ✗ **每把枪能选哪些（绑定/解锁）不在明文**

| 证据 | 结果 |
|---|---|
| 204 个 optionId 出现次数 | **每个只出现 1 次**（纯定义）；没有任何"同一 optionId 在多把枪下重复引用"的结构 |
| 武器 resource id 附近 | 52 把枪的 resource id 在 entities 里都能找到，但**其后没有 optionId 数组** |
| `node` id（1,322 个，解锁图的节点） | 全表扫描：entities 命中 **1** 个、customization_settings 命中 **1** 个 ⇒ **解锁图不在明文** |
| `generated_stratagem_upgrade_settings.dl_bin`（唯一像"进度"的表） | **0 个 optionId** |
| 第三方来源 | `mode: "snapshot"`、`writes: 0` —— 他们也是**从内存快照**抓的解锁清单，不是从表里读的 |

⇒ 当年 LAS-22「做不出来」的根因在此：**绑定层不在 55 张 dl_bin 里**，它在运行期/资源侧。

### 7.3 三层最终判定

| 层 | 在明文？ | 结论 |
|---|---|---|
| **配件定义**（204 个附件的名字/槽位/效果资源） | **✓** | 可改，但改了也没有"能被选中"的入口 |
| **L0 出生默认挂载** | **✓**（表在明文） | **✗ 改了不生效**（实测） |
| **L1 绑定/解锁清单** | **✗** | 运行期/资源侧，纯 dl_bin 路线打不通 |
| **L2 玩家当前选择** | **✗** | 同上 |

---

## 8. 能做什么 / 不能做什么（这条线的边界结论）

| 想做 | 判定 |
|---|---|
| 改某个附件的**外观/效果定义**（名称、槽位、addPath 指向的效果 delta） | ✓ 文件可做（`weapon_customization_settings`） |
| 让某把枪**默认挂着**某配件 | ✗ 实测无效（L0 不驱动） |
| 让某把枪**可选**新配件（含 LAS-22 解锁） | ✗ 数据表做不到（绑定不在明文）；只能走资源/运行期 |
| 查"某配件能装哪些槽 / 效果是什么" | ✓ 离线可查（本表 + 第三方 241 条目录） |

**建议**：这条线在"改表"层面收口。若将来还想做配件解锁，唯一剩下的方向是**资源侧**（武器资源里的 customization 定义）——成本高、且当年 memmod 已经证明要用运行期定位。

---

## 9. 支援武器假设与实验 K（2026-10-30 21:1x 已装盘）

### 9.1 观察：支援武器的 L0 里**本来就有瞄具**

45 个 `support_weapon` 行里 **28 行 L0 非空**，而且几乎都是光学槽：

| 武器（行） | L0 |
|---|---|
| **RS-422 Railgun（181，键 `0x2E9D0BDC48B09E60`）** | `2: Railgun Scope`（`0x5A3E7EBC`） |
| Autocannon(157) / Commando(173) / Recoilless(182) / Airburst(155) / Meltagun(160) / Expendable Napalm(163) / Laser Cannon(172) | `2: Support Scope`（`0xDD0F1240`） |
| Spear(164) | `2: FAF SPEAR SCOPE` |
| Speargun(169) | `2: TUBE REDDOT 1,5x` |
| Stalwart(127) / Heavy Machine Gun(171) | `2: REFLEX SIGHT MKII` |

### 9.2 为什么值得单独测：支援武器**没有改装页**

主武器/副武器有军械库改装 UI（⇒ 存在 L2「玩家当前选择」层，可能覆盖 L0）。
**支援武器根本没有那个页面** ⇒ 没有 L2 可覆盖 ⇒ 若 L0 在任何地方生效，就该在支援武器上生效。
这也给实验 J 的失败提供了另一种解释：**Constitution 的 L0 可能被它自己的 L2 覆盖了**。

### 9.3 实验 K（单变量，已装盘）

| 项 | 值 |
|---|---|
| 目标 | 块 `0xEBA8F3D0` 行 181（键 `0x2E9D0BDC48B09E60`），`+0x0` 的 8 B |
| 改动 | `(slot 2, 0x5A3E7EBC Railgun Scope)` → **`(slot 2, 0x67E0A480 SNIPER SCOPE 10x)`** |
| 门禁 | G1/G2/G3/G4/G6/G7/G8 全 PASS；与原版明文差异 **5 字节** |
| 封包/装盘 | 合法 MAC 47,259,456 B；`recipient.sk` 解封回读 = 目标明文逐字节一致 |
| 装盘后实读 | Railgun 行 `entry[0] = (2, 0x67E0A480)`、`entry[1] = 终止符` |

判读：

| 现象 | 结论 |
|---|---|
| Railgun 上变成 **10x 大镜子**（军械库预览/进游戏） | ✅ **L0 对支援武器生效** ⇒ 支援武器配件可改；且 J 的失败原因是主武器被 L2 覆盖 |
| 还是原来的 Railgun Scope | L0 连支援武器都不用 ⇒ L0 彻底是"资源默认"死数据 ⇒ 数据表路线收口 |
| 瞄具消失 / 枪变灰方块 | 10x 镜的资源不在这个包里 ⇒ 需要**供体包驻留**（同 §5.6.9 粒子那条 Reinforce 配方） |
| 崩 / 枪不出现 | 写错行或 slot 冲突 ⇒ 回滚 |

回滚：`cp "D:/mod/backups/spray-capsule/generated_entities.vanilla.dl_bin" "…/data/game/generated_entities.dl_bin"`

> 注：粒子 F 档（65 m 远射喷火器）仍在装盘，与本次配件实验不相干。

### 9.4 实验 K 实机结果（✓✓ 部分成功）：**参数层生效，模型层没有**

玩家实机（截图 2026-10-30 21:0x）：**菜单里出现了 10x 瞄具才有的 50m / 100m / 200m 零位档位**，
但枪身上**没有模型**。

| 层 | 结果 |
|---|---|
| **参数/逻辑层**（倍率、零位档位、准星、`WeaponDataComponentData` 的 ergonomics/stat delta） | **✓✓ 生效** —— 零位档位实测出现 |
| **视觉模型层**（optics unit 网格） | **✗ 没有** |

⇒ **支援武器可以用 L0 换瞄具的全部"手感/参数"**，这是本轮最大收获；
而支援武器**没有 L1（没有改装页）**，所以 L0 成了它的唯一入口 —— 这解释了为什么它生效而主武器（Constitution）不生效。

### 9.5 模型为什么缺（离线排查，2026-10-30 21:1x）

| 检查 | 结果 |
|---|---|
| 10x 的 `addPath` = `0x19FC5C5B031A4AF2` | 只出现在 `weapon_customization_settings`（定义）与 **`generated_entity_deltas.dl_bin`**（delta 体）各 1 次 |
| `entity_deltas` 结构 | 1 块，类型 `0x683E604F`，payload 352,317 B，typelib stride **80**，实占 4,403 行（**复合结构，不是定长行**，按 80 B 硬切对不上 addPath 偏移） |
| 武器行内是否直接引用 scope/optic 命名的资源 | **0 处**（用 322,711 条资源索引反查 8 把枪的整行 u64，名字含 scope/optic/sight 的命中 0） |
| `WeaponCustomizationComponentData +0x78`（第三方称 "optics unit"） | **196 行全为 0** ⇒ 本 build 该偏移不是 optics unit |
| `+0x80` 实际是什么 | 解析出 `gazine/railgun_magazine`、`on_clip/autocannon_clip`、`FAF-14 Spear Ammo` ⇒ **弹匣模型** |

⇒ 两条解释，都指向"模型不该出现"：

1. **模型焊在武器网格里**（最可能）：支援武器的瞄具是武器 unit 的一部分，换 optics 只换参数不换网格；
2. 或者 optics unit 由 `entity_deltas` 在运行期下发、但该 unit 的**资源包没驻留**（需要 Reinforce `+0xA8` 供体包）。

要区分这两条，得先解 `entity_deltas` 拿到 optics unit 的资源 id（工作量中等），再决定要不要包驻留。

### 9.6 能力边界（支援武器配件）

| 想改 | 能做吗 |
|---|---|
| 支援武器的**倍率 / 零位档位 / 准星参数 / ergonomics·后坐力 delta** | **✓✓ 文件可做**（L0 换 optionId，已实测） |
| 支援武器的**瞄具模型外观** | **✗ 未成**（见 §9.5） |
| 主武器/副武器的配件（含默认挂载） | **✗**（L0 被 L2 覆盖，实验 J 已否证） |
| 主武器/副武器"可选择新配件" | **✗**（L1 绑定不在明文） |

### 9.7 用资源索引直接找到 10x 镜的资源包（绕开 entity_deltas）✅ 比路线 A 更快

放弃解 `entity_deltas`（5 列列存：A 列 1024×16 = `{addPath, 0..571 索引}` 哈希图，B/C/D/E 列语义未定），
改用**资源索引按名字反查**（`tools/res_index.py`，322,711 条目 / 3,425 包）：

| 附件 | mesh/bones 资源 id | 所在包 |
|---|---|---|
| **10x Sniper Scope** | **`0x6D54652EE217D712`** | `52ebdf76131c8f38`、`a37891d879cb3b1d`、`2404fa21fe49c32d`、`ea6967f8565a2d76`、`e0807831d6f456c8` |
| 4x Combat Scope | `0x44A2A59CA08AC865` | 多个 |
| 2x Support Scope | `0x2457B559AA341CC1` | 多个 |
| 2x Tube Red Dot | `0x129E5FB1B13C2018` | 多个 |

包 `52ebdf76131c8f38` 是 10x 镜的**完整自洽资产集**（8 条，无外部依赖）：

| 类型 | id |
|---|---|
| bones + mesh | `0x6D54652EE217D712`（10x Sniper Scope） |
| material | `0x20CAB97A40D12B05`、`0xC9EF8AD9A2BBAE84` |
| texture | `0x11D16B39328ABF82`、`0x9879FE7F28234491`、`0xA77FE193C439C83F`、`0xE703C134E7BADA38` |

⇒ **模型缺失的原因是"包没驻留"**，不是"模型不存在"：Railgun 自己的包里没有这份 scope 资产。

### 9.8 实验 L（✓ 已装盘 2026-10-30 21:4x）：Reinforce 行声明供体包

用已验证的跨包加载机制（`+0xA8` = toc 包 id，见 `docs/engine/LIMITED-CROSS-PACKAGE-LOADING-26088801.md`）：

| 项 | 值 |
|---|---|
| 表 | `generated_stratagem_settings.dl_bin` |
| 目标行 | `MISSIONS. REINFORCEMENT BEACON`（组5 行20，type 0x7F） |
| 改动 | `+0xA8`：`0x0` → **`0x52EBDF76131C8F38`**（原值为 0，空字段，不会破坏原有加载） |
| 门禁 | G1–G7 全 PASS；与原版明文差 15 字节（目标行 + 校正字） |
| 封包/装盘 | 合法 MAC，82,424 B；`recipient.sk` 解封回读 = 目标明文逐字节一致 |

判读：

| 现象 | 结论 |
|---|---|
| 叫一次增援后 Railgun **长出 10x 镜模型** | ✅ 打通：支援武器配件"参数 + 模型"全链可改；配方 = L0 换 optionId + Reinforce 声明供体包 |
| 模型还是没有 | 跨包加载对"武器配件资源"无效（只对枪体/粒子这类生效）⇒ 改走"把 scope 资产打进 Railgun 自己的包"（路线 B'：`7f37db9b767844c2` 打 patch_0，8 条资源 + gpu） |
| 增援本身出问题（增援舱灰方块等） | `+0xA8` 被别的系统占用 ⇒ 立刻回滚战备表 |

回滚战备表：重新 seal `refs/dlbin/plaintext-26251122/generated_stratagem_settings.dl_bin` 并覆盖 `data/game/` 即可。

### 9.9 实机确认（✓✓ 2026-10-30 21:2x）：Railgun **长出 10x 镜模型**

玩家实机：换上 10x 后 Railgun **有模型了**。⇒ **支援武器配件「参数 + 模型」全链可改**：
`L0 换 optionId`（参数/倍率/零位/准星/后坐力） + `资源驻留`（模型）。

### 9.10 换成不依赖战备的驻留方式（✓ 已装盘）：补丁路线

`docs/engine/RESOURCE-RESIDENCY-26088801.md` 的结论是「**声明口管包在不在，补丁管资源在不在**」。
我们先用的是声明口（`+0xA8`），现在换成补丁路线，**战备表已回原版**：

| 项 | 值 |
|---|---|
| 宿主包 | **`f6fb08cc02d24255`**（共享基础包，782 资源，必然常驻；该宿主此前没有补丁，用 `patch_0`） |
| 条目 | **8 条**：`bones 0x6D54652EE217D712`、`mesh(unit) 0x6D54652EE217D712`（gpu 501 KiB）、`material 0x20CAB97A40D12B05`、`material 0xC9EF8AD9A2BBAE84`、`texture 0x11D16B39328ABF82`（gpu+stream 1.33 MiB）、`texture 0x9879FE7F28234491`、`texture 0xA77FE193C439C83F`、`texture 0xE703C134E7BADA38` |
| 体积 | toc 8,032 B ＋ gpu 1,390,536 B ＋ stream 1,398,128 B |
| 安装 | `data/f6fb08cc02d24255.patch_0{,.gpu_resources,.stream}` |
| 门禁 | `resource_patch.py list` 回读 8 条类型/id 全对；战备表解封回读 = 原版明文逐字节一致 |

⇒ 这条路线**不用叫增援**，也不需要任何战备行声明；资源按 `file_id` 进全局索引，任一已加载包里有就能解析。

### 9.11 副武器（实验 M，✓ 已装盘）：P-2 Peacemaker 加反射镜

副武器同样**没有独立的自定义入口**（用户判断），所以用与支援武器相同的办法试探：

| 项 | 值 |
|---|---|
| 行 | 49（键 `0x05E4E5C2DB6E44A2`），`+0x18` |
| 改动 | `(2, 0x7766DA38 No Optics)` → **`(2, 0x469F34D9 PISTOL REFLEX SIGHT)`** |
| 门禁 | G1/G2/G3/G4/G6/G7/G8 全 PASS；链式写（在 Railgun 改动之上再跑一遍，哈希仍回到锚点） |
| 装盘后实读 | Peacemaker L0 = `(4,No Muzzle) (6,AMMO) (5,Magazine) (2,PISTOL REFLEX SIGHT) (1,Laser Sight Flashlight)` |

判读：

| 现象 | 结论 |
|---|---|
| Peacemaker 上**出现反射镜** | ✅ 副武器与支援武器同机制 ⇒ 副武器配件全链可改 |
| 只有参数层变（如准星/手感变）无模型 | 模型资源未驻留 ⇒ 给该附件包再加一份驻留补丁 |
| **毫无变化** | 副武器有 L2（玩家选择）覆盖 L0 ⇒ 与主武器同类，只有支援武器这条路可走 |

### 9.12 副武器确认（✓✓ 实机 2026-10-30 21:3x）：Peacemaker 长出反射镜

⇒ **副武器与支援武器同机制**：没有独立自定义层（或 L0 就是它的入口），L0 换 optionId 直接生效（参数 + 模型）。
⇒ 至此三期结论：**支援武器 ✓✓ / 副武器 ✓✓ / 主武器 ✗（实验 J）**。

### 9.13 实验 N（✓ 已装盘）：主武器**替换**已有配件（在它自己的解锁清单范围内）

思路（用户提出）：主武器没法"新增"配件（L1 绑定不在明文），但也许可以"**替换**"——
关键差别在于：**新选项必须在该枪自己的解锁清单里**，否则大概率被校验挡掉（这也许正是实验 J 失败的另一种解释）。

用第三方解锁清单与 L0 做交叉，**全库只有一把**满足「L0 已有光学槽 **且** 清单里还有别的光学选项」：

| 项 | 值 |
|---|---|
| 武器 | **LAS-13 Trident**（行 124，键 `0x3C86E871923F3970`），`PRIMARY` |
| 现状 | `+0x08` = `(slot 2, 0x661DF57B TUBE REDDOT 1,5x)` |
| 其清单可选光学 | HOLOGRAPHIC SIGHT / Iron Sights / TUBE REDDOT 2x / REFLEX SIGHT MKII |
| 改动 | `+0x08` → **`(slot 2, 0x4672A011 HOLOGRAPHIC SIGHT)`** |
| 门禁 | G1/G2/G3/G4/G6/G7/G8 全 PASS；链式写，哈希回锚点 |
| 装盘后实读 | `(4,No Muzzle)(2,HOLOGRAPHIC SIGHT)(3,Default)(1,Underbarrel)` |

判读：

| 现象 | 结论 |
|---|---|
| Trident 上**出现全息镜**（参数+模型） | ✅ **主武器也能"替换"**，条件 = 目标选项在该枪解锁清单内 ⇒ 主武器 per-weapon 改装配方成立 |
| 只有参数变、无模型 | 校验过了但资源没驻留 ⇒ 给该附件加驻留补丁（同 §9.10） |
| **毫无变化** | L0 对主武器根本不被读取（校验不是原因）⇒ per-weapon 路线死；改走"**option 定义重定向**"（全局：把 `weapon_customization_settings` 里 A 的记录改成 B 的 addPath，则所有能选 A 的枪都变 B） |

---

## 10. 投送舱塞主武器（实验 O，✓ 已装盘）—— 「玩到拿不到的武器」路线

用户提出：主武器是**可拾取的**，理论上投送舱也能吐；若能成，就能绕过解锁直接玩到未发布武器（如 LAS-22）。

### 10.1 先确认了一件关键事：舱槽吃的是**武器自己的实体键**

| 证据 | 值 |
|---|---|
| rack 47（MG-43 舱）槽 0 的 Item | `0x11C27D3BABB38956` |
| 该键在武器定制表里的身份 | **row 177 `Machine Gun`** —— 就是 MG-43 自己的武器实体键 |

⇒ 舱槽 `Item` 与 `WeaponCustomizationComponentData` 的哈希图键是**同一套实体键**。
⇒ 所以「把某把主武器塞进舱」= 把它的实体键写进任一 `RackAttach.Item`。

### 10.2 装盘内容（实验 O）

| 项 | 值 |
|---|---|
| 舱 | rack 47（MG-43 舱，原 `spawn=1`、authored 2 槽、两个真挂点 `0x76C6D1E3` / `0x7FE13CFF`） |
| 槽 0 | `0x11C27D3BABB38956 MG-43` → **`0x3C86E871923F3970 LAS-13 Trident`**（node/offset/side 全不动） |
| 槽 1 | 保留 MG-43 作对照 |
| `+0x22C` spawn | `1` → **`2`**（两槽都生成） |
| 门禁 | G1–G7 全 PASS；差异 10 字节；解封回读与目标明文逐字节一致 |
| 装盘后实读 | 槽0=Trident、槽1=MG-43、spawn=2、random=0 |

判读：

| 现象 | 结论 |
|---|---|
| 舱里落地**两件**：Trident + MG-43，且 Trident **可拾取、可开火** | ✅ 投送舱 = 通用武器载体 ⇒ **未发布武器可直接玩**（下一步把 LAS-22 Shear 塞进去） |
| 只出 MG-43 | 主武器实体不能当舱载荷（缺 world-item 组件）⇒ 换对象（载具级实体、或先补组件） |
| 出灰方块 / 崩 | 载荷资源未驻留 ⇒ 加驻留补丁（同 §9.10 的 8 条资源做法） |
| 舱空了 | `+556`/挂点组合不合法 ⇒ 先回滚 spawn=1 用单槽 Trident 再试 |

### 10.3 未发布武器：LAS-22 Shear **实体确实存在**

| 项 | 值 |
|---|---|
| 实体键 | **`0x7E3145A5BAA4B948`**（名字 `Shear`，`loadout_type = 1` 可装备） |
| 说明 | 它在实体表里存在、只是**不在任何解锁清单**里 ⇒ 「投送舱」正是绕过解锁的入口 |

⇒ 若实验 O 成立，下一步 = 把 `0x7E3145A5BAA4B948` 写进舱槽 + 给它做资源驻留补丁（模型/材质/贴图），
即可在任务里捡到未发布的 LAS-22 Shear。
