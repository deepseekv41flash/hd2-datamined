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

⚠ 与 2026-10-30 已装的 `spray_capsule_radius` 改动**共用同一张表**（`generated_entities.dl_bin`）：
装实验 J 时会与胶囊改动**同时生效**，若要保持单变量，需要决定是否先把胶囊改动撤回。

---

## 5. L1 的下一步（离线、零风险）

`generated_weapon_customization_settings.dl_bin`（9 块、30,824 B，块类型 `0x1E604234`，行结构是
`{u64, u32×5, u64×2, struct16, struct16, u32}` 这种复合体，**不是**平坦数组）。
下一步：把 9 个块逐字段解出来，与第三方 `attachment-unlock-lists-F5FEE03DCFDB.json`
（52 把武器的可选清单）对照 —— 若能对上，**L1 也能文件化**，LAS-22 那条当年没做出来的路线就有了替代方案。
