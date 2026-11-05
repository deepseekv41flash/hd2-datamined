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
