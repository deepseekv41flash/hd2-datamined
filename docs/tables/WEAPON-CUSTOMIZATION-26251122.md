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
