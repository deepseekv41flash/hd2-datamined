# RECON：`LAS22FileTool 1.0.0` —— 用两张 dl_bin 让未发布 LAS-22 Shear「上线」

> 2026-11-05 只读分析。原包 `D:\Downloads\LAS22FileTool-1.0.0.zip`（单 exe 7,678,976 B），
> 输出在 `D:\Downloads\LAS22FileTool-1.0.0_files\`：
> `generated_entities.dl_bin`（47,259,472 B）+ `generated_weapon_customization_settings.dl_bin`（30,880 B），
> 两者都是 **sealed**（可用 `refs/dlbin/keys/recipient.sk` 解封）。
> 结论：**机制完全解开，且两个输出明文都能被我们逐字节复现**。

## 0. 一句话

它不改内存、不写 game.dll、不需要 Lua 加载器：**只改两张 dl_bin**，用「**借用已注册的模板键 + 重指向附件资产 + 重指向默认选项**」
把已注册的 LAS-5 Scythe 身份借给未发布的 LAS-22 Shear —— 军械库里的「LAS-5 Scythe」入口从此加载 Shear 的实体/数据，
长柄镰自己变得不可见；再把 4 个已注册激光配件的 `AddPath` 指到 LAS-22 专属的「charge」资产，
菜单仍显示原配件名，装上却是切变的散热器/枪口。

## 1. 工具形态与行为（从产物反推）

| 事实 | 证据 |
|---|---|
| exe 是 PE32+ GUI，主体在 `.rsrc`（7.47 MB，高熵；`.text` 仅 143 KB） | 全文件熵 7.993；ASCII/UTF-16 都搜不到 `LAS`/`generated`/`.dl_bin` 等字符串 ⇒ 打包/加密的 loader + 大块资源 |
| **它读的是本机当前已装的 sealed 表** | entities 输出明文 = **本机已装的 LAS-17 三档测试盘**（`tmp/heat/clean-3band.plain`，含 L1=Gas/L2=Stim 两个状态字节）+ 5 处新改动；若是内嵌整份文件，base 应是原版 |
| 流程：解封 → 按固定偏移打补丁 → 重算内容哈希 → 重新封装 → 写 `_files/` | 两输出的 Murmur 锚点与基座一致（entities `0x8E49771B181FFAA1`、wcust `0x2959F01202679FE6`）；两者各 +8 B 尾部校正字，且各自末块/末组 payload 尺寸字段 +8 |
| 不写游戏目录 | 只产出 `_files/` 两个文件（安装与否由用户决定） |

## 2. 机制：身份互换 + 资产重指向

### 2.1 为什么能「注册」未发布武器

- 游戏注册表（184 B 记录 / item id 键）在 **game.dll loader data**，dl_bin 改不到（Lua 版 mod 就是内存改它）。
- 但 `LAS-22 Shear` 的档案里写着 `key = 0x7DE53646, template_key = 0xE673DCC8`，
  而 `0xE673DCC8` 正是 **LAS-5 Scythe**（已注册）的键
  （见 [UNRELEASED-INVENTORY §](/d/mod/work/repo-datamined/docs/tables/UNRELEASED-INVENTORY-26088801.md) 行 159）。
- ⇒ 把两张 `LoadoutEntryComponentData` 行的键**互换**：
  `0xE673DCC8`（Scythe，已注册）现在指向 **Shear 的实体行**，`0x7DE53646`（Shear，未注册）给了 Scythe 行。
  军械库按已注册键解析时，拿到的就是 Shear 的数据 ⇒ **LAS-22 显示并可装备**；Scythe 因为拿着未注册键而隐藏。

### 2.2 修「装上去长什么样、给什么配件」

- Shear 行原来的默认配件是 LAS-22 专属的 charge 分支（`Laser. Charge Standard`、`Laser Heatsink (Charge).*`），
  这些 option 不在解锁清单里 ⇒ 默认装配会落空。工具把它们改成 **LAS-5 的已注册选项**
  （`Laser. Standard Prism`、`Laser Heatsink. Medium Standard`）。
- 再把 **这 4 个已注册选项的 `AddPath`（asset/效果包）** 指向 LAS-22 专属 charge 资产：
  于是菜单里仍是原名字/原解锁状态，实际装上去的是切变的电荷散热器与枪口
  （等价于把 LAS-5 的 4 个配件"换皮"成 LAS-22 的）。
- `+0x12FC`（`WeaponCustomizationComponentData.UnknownThinHash2`，即 Lua 分析里的「Shear upgrade key」`0xD62DC83D`）
  换成 Scythe 的 `0x56219B65` ⇒ **进度/升级元数据继承长柄镰**（与 Lua 版 README 说法一致）。

## 3. 逐字段清单（共 9 处值 + 2 处容器尺寸）

### 3.1 `generated_entities.dl_bin`（基座=本机已装 LAS-17 三档盘；明文 +28 B）

| 绝对偏移 | 结构 | 原值 → 新值 | 含义 |
|---|---|---|---|
| `0x0B30B4` | `LoadoutEntryComponentData` 行 127（实体 `0x27EE1ED8F6FB6356` LAS-5 Scythe）`+0x0` | `0xE673DCC8` → `0x7DE53646` | 把已注册键让给 Shear |
| `0x0B30D4` | `LoadoutEntryComponentData` 行 128（实体 `0x7E3145A5BAA4B948` LAS-22 Shear）`+0x0` | `0x7DE53646` → `0xE673DCC8` | Shear 拿到已注册模板键 |
| `0x1B265F8` | `WeaponCustomizationComponentData` 行 121（Shear）`+0x04` `DefaultCustomizations[0].Customization` | `0xD65DC159`（'Laser. Charge Standard'）→ `0xE917F79B`（'Laser. Standard Prism'） | 默认枪口改已注册选项 |
| `0x1B26610` | 同组件行 `+0x1C` `DefaultCustomizations[3].Customization` | `0x5672E4B7`（'Laser Heatsink (Charge). Standard Heatsink'）→ `0xF3D0DF39`（'Laser Heatsink. Medium Standard'） | 默认弹匣改已注册选项 |
| `0x1B278F0` | 同组件行 `+0x12FC` `UnknownThinHash2` | `0xD62DC83D`（Shear upgrade key）→ `0x56219B65`（Scythe 的） | 进度元数据继承长柄镰 |
| `0x2D11CC8` | 末块 payload 尺寸 | `560+20` → `560+28` | 尾部 +8 B 校正字 |

### 3.2 `generated_weapon_customization_settings.dl_bin`（基座=原版；明文 +8 B）

| 绝对偏移 | 组/item | 字段 | 原值 → 新值 | 新值去向 |
|---|---|---|---|---|
| `0x004010` | 组 3 item 41 `0xF3D0DF39` 'Laser Heatsink. Medium Standard' | `AddPath` (u64) | `0xB61B1340B74AAA5C` → `0xB889C472C393E06B` | **'Laser Heatsink (Charge). Standard Heatsink'** 的资产 |
| `0x004068` | 组 3 item 42 `0xF9D96D40` '…Improved Heatcapacity' | `AddPath` | `0x55E9F7BC3BFA32FA` → `0x7DCA2947CCDA8F56` | **'…(Charge). Extended Heatsink'** |
| `0x0040C0` | 组 3 item 43 `0x87770B73` '…Improved Cooldown' | `AddPath` | `0x86BCCD5B35E0EEA5` → `0xB4E981030087D094` | **'…(Charge). Rapid Heatsink'** |
| `0x005874` | 组 4 item 31 `0xE917F79B` 'Laser. Standard Prism' | `AddPath` | `0xCEBD25F8778BFDEE` → `0x7DC6DDA584CC5223` | **'Laser. Charge Standard'** 的枪口资产 |
| `0x006FE8` | 末组 payload 尺寸 | | `2164` → `2172` | 尾部 +8 B 校正字 |

## 4. 复现（字节级）

用 `tools/murmur64.padding_word_for_hash` 把上面 9 处值 + 2 处尺寸写进对应基座，末尾追加 8 B 校正字：

| 文件 | 基座 | 复现明文 sha256(前16) | 工具输出明文 sha256(前16) | 结果 |
|---|---|---|---|---|
| generated_entities | 本机 LAS-17 三档盘 | `7079ee2ed4f7ec76` | `7079ee2ed4f7ec76` | **逐字节相同** ✓ |
| generated_weapon_customization_settings | 本机原版 | `019d43023c6603a5` | `019d43023c6603a5` | **逐字节相同** ✓ |

⇒ 工具的做法 = 与我们的「tail 宿主保哈希」完全同一套数学；其 sealed 包只是随机 ephemeral，与内容无关。
（本机安装前先 `python tools/dlbin_deploy.py install --file ... --sealed <工具输出>` 即可用；账本/备份由 deploy 工具管理。）

## 5. 与 Lua 版 LAS-22 解锁 mod 的关系

| | Lua v1.0.2（`LAS22-Shear-Unlock-Customization`） | 本文件版 |
|---|---|---|
| 载体 | 两个 Lua 资源 + Bingus Shared Loader | 两张 dl_bin（sealed） |
| 注册 | 内存里**新建** 184 B 注册记录 + 24 B 映射 + count++（2928→2929），克隆 LAS-16 模板 | **不新建**，把已注册的模板键（LAS-5 Scythe）让给 Shear |
| 代价 | 需要加载器；构建更新后可能失效 | **LAS-5 Scythe 从军械库消失**；菜单里配件名仍是长柄镰的 |
| 附件 | 嫁接 7 条附件记录/映射 | 4 个已注册配件的 `AddPath` 换皮成 charge 资产 |
| 进度 | 继承长柄镰（README 明说） | `+0x12FC` 换成长柄镰 upgrade key |
| 联机/更新 | 加载器全局生效 | 只替换本机两张表，需与生成时同 base |

## 6. 复刻/改进建议

- 复刻：按 §4 的 9+2 处字段写我们的 `entity_fields_batch` 风格脚本即可（注意 entities 的基座要**用当前已装表**，否则容器尺寸/尾字会不同）。
- 若想**不牺牲 LAS-5**：可改用「把 Shear 的组件行数据写进 Scythe 行 / 或者给 Shear 行补 Spottable+EntityBind 后用投送舱路线」
  （见 [WEAPON-CUSTOMIZATION §10](WEAPON-CUSTOMIZATION-26251122.md)），但那需要更多表/资源驻留，不如这个方案省事。
- 数据来源已记录：`las22-unlock-analysis.json`（Lua 版逐层分析）；
  `UNRELEASED-INVENTORY` 行 159（`key=0x7DE53646, template_key=0xE673DCC8`）；
  `WEAPON-CUSTOMIZATION-26251122.md` §10.4（三条 charge 散热器的 optionId/addPath 与"谁在用"）。

---

## 7. 复盘：这个案例解开了我们哪些卡点（2026-11-05 追加）

> 所有数字都现场重读过表；**没实机的一律标"待实机"**。

### 7.1 直接确证（离线可复查）

| # | 之前的卡点 | 本案给出的答案 | 证据 |
|---|---|---|---|
| 1 | 「LAS-22 为什么不显示」只知道"不在解锁清单、解锁图不在明文"（WEAPON-CUSTOMIZATION §7.2） | 根因精确到一个 u32：`LoadoutEntryComponentData +0x0`（后端目录 id）不指向它。实体/组件/名字/百科条目本来都在 | `0x7DE53646` 全库仅 1 处（就是该行）；`0xE673DCC8` 全库 2 处（entities 行 127 + `policy_settings`） |
| 2 | `WeaponCustomizationComponentData +0x12FC` = `UnknownThinHash2`（filediver 注释 "No clue"） | = **配件解锁/升级组键**（每把可改装武器一个）。196 个键里 56 非零、55 个不同值；Scythe `0x56219B65`、Shear `0xD62DC83D` | 两个互不相干的 mod 都只改这一处来继承进度/解锁树；两键在 55 张明文表里各只出现 1 次（=字段自身）⇒ 组内容在资源/运行期，**指针在明文、可改** |
| 3 | 「注册/上架」能不能纯数据做 | 不能新增，但**可以借位**：目录 id ↔ 实体行是查表关系，交换 id = 交换身份 | Scythe 行 127、Shear 行 128，各自 id 唯一 |
| 4 | 每把枪「能改哪些槽」在哪层 | **在明文行内**：`CustomizationSlots`（+0x50，10×u32）。Scythe 与 Shear 都是 `(2,1,4,5,3)`，工具没动它 | 直接读表 |
| 5 | `DefaultCustomizations` 的 10 组怎么读 | **entry 顺序无关，`slot` 字段才是指针**：Scythe 顺序 `5,4,2,1,3`、Shear `4,2,1,5,3`；工具改的是 slot=4（枪口）/ slot=5（弹匣） | 直接读表；改后装配仍成立 |
| 6 | 4 个「换皮」到底换成了什么 | LAS-22 专属 charge 分支的资产（三条散热器 + charge 枪口） | 见 §7.2 反查表 |
| 7 | `LoadoutEntry +0x0` 是"唯一物品 id"吗 | **不是**：199 行里 7 组 id 重复（4 把支援武器共用 `0x00DAE676`、GL-28 武器+背包共用 `0x1E86BFC1`）⇒ 更像"目录/发放 id" | 全表复读 |

### 7.2 9 处写值的来源复核

L1 表（`generated_weapon_customization_settings`）里按工具的 4 个 patch 偏移反查 item：

| 原 option | 旧 AddPath | 新 AddPath | 新 AddPath 属于 |
|---|---|---|---|
| `0xF3D0DF39` Heatsink Medium Standard | `0xB61B1340B74AAA5C` | `0xB889C472C393E06B` | `0x5672E4B7` Charge Standard |
| `0xF9D96D40` …Improved Heatcapacity | `0x55E9F7BC3BFA32FA` | `0x7DCA2947CCDA8F56` | `0x3D0687C6` Charge Extended |
| `0x87770B73` …Improved Cooldown | `0x86BCCD5B35E0EEA5` | `0xB4E981030087D094` | `0x53120A73` Charge Rapid |
| `0xE917F79B` Laser. Standard Prism | `0xCEBD25F8778BFDEE` | `0x7DC6DDA584CC5223` | `0xD65DC159` Laser. Charge Standard |

⇒ 四条新 AddPath 都能在 L1 表里反查到归属；L0 那两处（slot 4/5）确实落在 Shear 行的对应 slot 上。

### 7.3 两条被判死的旧结论有了复活路线（待实机）

| 旧结论 | 新路线 | 代价/前提 |
|---|---|---|
| WEAPON-CUSTOMIZATION §8「让某把枪可选新配件 ✗（绑定/解锁图不在明文）」 | 仍不能"新增"，但能**借**：① 默认项改成宿主已解锁的选项；② 这些选项的 `AddPath` 换成目标配件资产（换皮）；③（未测）改 `+0x12FC` 借另一把枪的解锁树 | 要一把已解锁的同族宿主；换皮是**全局**的（§7.5） |
| §12.7「未发布副武器 P-41 ✗（补 Interactable 两次卡死；副武器不可拾取）」 | **军械库路线不需要拾取**：P-41 有 LoadoutEntry 行（row 161，id `0xC9F609BA`，slotType 3），与 P-2 Peacemaker（id `0xA7977F98`，slotType 3）互换 id 即可在配装界面直接装备 | 牺牲 P-2；未测 |
| §11「LAS-22 上线 = 舱 + 17.6 MB 整包驻留 + 5 个 patch」 | 军械库装备路径按需流式加载（§11.2 已记）；文件版只改 2 张表 ⇒ 若实机成立，**驻留补丁只对投送舱路线必需** | 待实机；包 `487bcf38276eb725` 仍要能按需取到 |

### 7.4 两条要修正/收回的说法

1. 初稿 §0 说"军械库里的『LAS-5 Scythe』入口从此加载 Shear 的数据"——**入口名很可能直接变 LAS-22 Shear**：
   名字不是行内字段，是实体 `EncyclopediaEntryComponentData+0`（ENTITY-LOCID §5），查名字走实体键。
   而 "LAS-22"/"Shear" 两条文本本 build 都有（Lua 版分析已验）⇒ 借位后条目应显示 **LAS-22 Shear**。待实机。
2. 但**配件标签仍可能缺文本**：Lua 版专门补了 `0x37709874`（Shear muzzle label，base 全库没有这条字符串），
   文件版没补 ⇒ charge 枪口那一项可能显示空/占位名。这是纯观感问题，不影响机制。

### 7.5 副作用：4 个换皮选项是**共享行**

| 被改的选项 | 谁把它当 L0 默认 | 后果 |
|---|---|---|
| `0xF3D0DF39` Heatsink Medium Standard | 只有 Scythe | 随 Scythe 一起隐藏 |
| `0xE917F79B` Laser. Standard Prism | Scythe + **`0x2C66C201B2543D2C`**（Guard Dog Rover 的激光武器，BACKPACK-DOGS §2） | Rover 的默认枪口也指到 charge 枪口资产（Rover 没有 L1/L2，L0 是唯一入口）⇒ **实机要顺手看一眼 Rover 的枪口/特效** |
| `0xF9D96D40` / `0x87770B73` | 0 把武器的默认项（只是可选） | 影响面取决于激光家族的 L1 清单（不在明文） |

### 7.6 新线索：`generated_policy_settings.dl_bin` 里有一张武器清单

- 480 B / 1 块 / **14 行 × 32 B**（`refs/table-geometry.json`）；旧 build 字典的成员名 = `PolicySetting` + **`PolicyUnlockedWeaponList`**（TABLE-DICTIONARY §PolicySettings）。
- 尾部数组里出现两个 LoadoutEntry 目录 id：**`0xE673DCC8`（LAS-5 Scythe）** 与 **`0x951D05B0`（LAS-7 Dagger）**。
- ⇒ 如果运行时按这张表"发放/解锁"，那"注册"和"发放"是两层：**把 `0x7DE53646` 加进清单**可能是不牺牲宿主的解锁路线。
- 结构还没解（行内是 u32 + 3×hash 的记录 + 尾部 offset/count 数组），列为下一步离线任务。

### 7.7 仍未解（本案没碰到的）

- 注册表本体（2928 × 184 B 记录 + 24 B 映射，在 game.dll loader data）不可写；借位以"宿主消失"为代价。
- 块 0 组件净增（HEAT §21）仍无解 —— 但**不再挡 LAS-22**：借位后玩到的是真实体（自带 `TargetingComponent`、`overheat_ability 2877`），不需要移植。
- `+0x12FC` 指向的解锁树内容、L2 玩家选择、"解锁图"本体仍不在明文。
- 前提：宿主 id `0xE673DCC8` 必须在本机注册表里且账号拥有 —— 文件版不做任何授予，
  所有权/启用状态是跟着 **id** 走的（Lua 版改的是记录里的 `+0x14` 状态，取值 ∈ {0,1,2,4}）。

## 8. 下一步（单变量）

| # | 实验 | 一次回答 | 风险 |
|---|---|---|---|
| 1 | 装文件版（entities + wcust 两张），进游戏 | ① 军械库条目名是 Shear 还是 Scythe ② 是否拥有/可装备 ③ 装上后散热器/枪口是不是 charge 资产 ④ LAS-5 是否消失 ⑤ Rover 枪口有无异常 | 低（两张表，deploy 账本可回滚）；会覆盖当前 LAS-17 三档盘 |
| 2 | 若 1 成立：军械库改 Scythe 的配件选择，再看 LAS-22 出生装配 | L2 是否按注册 id 覆盖 L0（把"三层模型"最后一格钉死） | 低 |
| 3 | P-41 ↔ P-2 目录 id 互换 | "军械库借位"对副武器是否通用（§12.7 那条线复活） | 中（会改副武器池） |
| 4 | 离线先做：解 `policy_settings` 14 行 + 试写"给清单加一行" | 能否不牺牲宿主地解锁（以及"注册 vs 发放"两层） | 离线零风险 |
