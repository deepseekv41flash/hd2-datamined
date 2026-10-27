# 索引

> **本仓库唯一索引入口。** [README](README.md) 只讲「这是什么、怎么上手」；所有文档都从这里进。
>
> 当前验证 build **`26088801`** ｜ 历史基线 `25480438` → `25988413`
> **事实类**文档文件名带 build 号，结论只对那个 build 成立；**方法类**不带 build 号，跨 build 有效。
> 每个 build 到底改了什么 → [§2 的 `builds/` 小节（跨 build 对照表）](#builds)；新 build 到手先跑哪三步 → **[BUILDS.md](BUILDS.md)**。
> 链接自检：`python tools/check_links.py`（0 断链才算过）。

## 0. 三十秒：我该从哪进

| 你是… | 从这进 |
|---|---|
| 想亲手改一张表 | **[改盘上数据的完整工作流](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md)** —— 主线文档，8 步链 + 锚点哈希 + 93 条坑 |
| 想让**代理**去做 | **[skills/hd2-file-route-mod](skills/hd2-file-route-mod/SKILL.md)** —— Agent Skills，只给方法论（每步的目的 / 判据 / 停的条件）+ 指回本页 |
| 想查某个字段 / 某个数 | [§1 按问题找](#1-按问题找) |
| 想按类型看全部 68 篇 | [§2 按类型浏览](#2-按类型浏览68-篇) |
| 想找某个工具 / 看它验证到哪一步 | [§3 工具清单](#3-工具清单tools) |
| 刚更新完游戏 | [BUILDS.md §3](BUILDS.md)（三步 + §3.1 锚点复验） |
| 什么都没有、只想先摸摸 | [§4 无密钥也能练](#4-无密钥也能练) |

## 1. 按问题找

### 动手改东西

| 我想改 | 读 | 关键小节 | build |
|---|---|---|---|
| 战备冷却 / 呼叫时间 / 使用次数 | [STRATAGEM-FIELDS](docs/tables/STRATAGEM-FIELDS-26088801.md) | §2 面板公式 · §5.2 鹰式次数 · §5.3 float32 边界 | `26088801` |
| **Eagle 回收时间** | [STRATAGEM-FIELDS](docs/tables/STRATAGEM-FIELDS-26088801.md) | **§5.4 `EAGLE. REARM` 独立行** | `26088801` |
| **Eagle 冷却 / 回收的升级公式** | [STRATAGEM-FIELDS](docs/tables/STRATAGEM-FIELDS-26088801.md) | **§5.4.4**（两个公式都已实机解开） | `26088801` |
| 爆炸半径 / 破片数 / 粒子 / 震屏 / 外观移植 · 状态爆 | [EXPLOSION-VISUAL](docs/explosions/EXPLOSION-VISUAL-26088801.md) | §1 字段图 · §4 无主行账本（265/424，✓ 实机用过 254）· §5 `+0xA8` 跨包加载 | `26088801` |
| **给载具换武器 / 往空槽加件** | [MOUNT-SEATS](docs/tables/MOUNT-SEATS-26088801.md) | **§2 `MountInfo` 24 B（只写 item）· §4 五件套 + 两条否决项 · §7 换件配方与 G1–G10 · §8 能力判定 · §11 M-102 枪手位 = 通用武器挂点（✓✓ MG-206 / MG-43 / AC-8〔装填需玩家背背包〕/ 手枪 P-19 全通；§11.4 声明包不被载具加载 → 整包驻留）· §11.9 规则汇总 R1–R7 · §12 E/GL-21 墙 = 挂载 GL-21 变体（同弹道/低后坐/60 发无备弹 + mount 字段解剖；§12.7 挂 Guard Dog ✓✓；§12.8 墙换 MG-43 ✓✓（装填扣备弹 = 工事座位走玩家路径）· §13 结项总表 R1–R8 + 盘面已复原（删 patch_18–33，152.2 MB））** | `26088801` |
| 换弹头（整行搬运）/ 换爆炸效果 | [EXPLOSION-PROJECTILE](docs/explosions/EXPLOSION-PROJECTILE-25988413.md) | 全文 | `25988413` |
| 武器数值 / 可选弹种 / 独立弹药池 | [ENTITY-TABLE](docs/tables/ENTITY-TABLE-25988413.md) | §9 | `25988413` |
| 武器配件与槽位 | [WEAPON-CUSTOMIZATION-DECODED](docs/tables/WEAPON-CUSTOMIZATION-DECODED.md) | 全文 | `25988413` |
| **改武器伤害 / 穿甲** | [DAMAGE-SETTINGS](docs/tables/DAMAGE-SETTINGS-26088801.md) | **§2 字段图 · §4 共享行 · §5 宿主策略**（行内零 padding 也能改） | `26088801` |
| **武器备弹 / 让背包武器自带备弹** | [WEAPON-AMMO-RESERVE](docs/tables/WEAPON-AMMO-RESERVE-26088801.md) | **§2 `Rounds +0x50/+0x54/+0x58` · §3 `Magazine +0x88/+0x8C/+0x94` · §5 四把配方** | `26088801` |
| **近炸引信（空炸 / 破片弹）** | [PROJECTILE-PROXIMITY](docs/tables/PROJECTILE-PROXIMITY-26088801.md) | **§1 引信段字段 · §3 AC-8 为什么要找备弹 289 · §4 怎么改** | `26088801` |
| 弹幕轮数 / 每轮弹数 / 散布 | [STRATAGEM-FIELDS](docs/tables/STRATAGEM-FIELDS-26088801.md) · [ENTITY-TABLE](docs/tables/ENTITY-TABLE-25988413.md) | §3 散布 · §5 弹幕组件 | `26088801` |
| **护甲三数字（rating / speed / stamina）** | [ARMOR-KIT-WEIGHTS](docs/tables/ARMOR-KIT-WEIGHTS-26088801.md) | **§2.1 完整数值模型（135/135）· §5.2 实机读数 · §1.1 class_table 三张表的 RVA 与字节** | `26088801` |
| **射击模式 / 射速** | [WEAPON-FIRE-MODES](docs/tables/WEAPON-FIRE-MODES-26088801.md) | **§2 FireMode 枚举表（已基本填满）· §3 能做/不能做的边界 · §4 五轮实验台账 · §5 配方** | `26088801` |
| **蓄力武器（charge-up）** | [CHARGE-WEAPONS](docs/tables/CHARGE-WEAPONS-26088801.md) | **§2 行内字段图（三档 ChargeStateSetting + 倍率）· §3 「要不要蓄满」= `Min.ProjType` · §6 run 1 已装盘** | `26088801` |
| **锁定 / 制导武器**（**✓ 结项**） | [LOCKON-TARGETING](docs/tables/LOCKON-TARGETING-26088801.md) | **§7.5 能力边界 + 7 轮实验台账（C 档样板来源）**：距离 ✓ 实机、锁定时间 ✓ 实机、锥角 ✗、目标集合 ✗ · §1 三张表与几何 · §4 武器→投射物→制导行映射 · §10 目标列表不在明文 | `26088801` |
| **护甲被动 / 弹容 / 装填 / 单件甲** | [ARMOR-PASSIVE-STATS](docs/tables/ARMOR-PASSIVE-STATS-26088801.md) | **§2 两层作用范围 · §4 sm 七个槽的语义 · §5 三条硬约束 · §6 已验证配方** | `26088801` |
| **只给某一件甲加效果** | [ARMOR-PASSIVE-STATS](docs/tables/ARMOR-PASSIVE-STATS-26088801.md) | **§2 单件级（改 kit 的 `+0x1C`）· §6 配方 · §2 末尾「没有空被动」的否证** | `26088801` |
| **投送舱送什么（战备空投舱换载荷）** | [POD-RACK](docs/tables/POD-RACK-26088801.md) | **§1 槽位结构 · §2 前 N 个槽才生成 · §3 换物品配方** | `26088801` |
| **换进来的物品只有紫问号 / 网格材质不加载** | [POD-RACK](docs/tables/POD-RACK-26088801.md) | **§4 两个包槽（`+0xA8` + `+0xF8`）· §5 item→包解析表** | `26088801` |
| **改了弹丸/爆炸，怎么知道漏了哪些粒子/实体/声音资源** | [RESDEP](docs/tools/RESDEP.md) | **`chain` 扫引用 · `plan` 分「同包/跨包/缺失」· `--apply` 一键装盘+整体回滚 · `VERIFY.md` 实机清单 · HIRC 事件目录** | `26088801` |
| **某个 id 在整个数据里被谁引用 / 原版武器的弹丸从哪来 / 某个弹丸 id 叫什么** | [REFSCAN](docs/tools/REFSCAN.md) | **`exact` 全档 u32 账本 · `columns` 引用面普查 · `delta-info/-show/-ammo` 解配件 delta 链（弹种槽 6 → `ProjectileWeapon+0`）· §6 wiki 镜像交叉验证（61 武器 / 59 个 id→枚举名）· 本 build 组件索引表** | `26088801` |
| **狗背包（AX 系）换枪**（**✓ 结项**） | [BACKPACK-DOGS](docs/tables/BACKPACK-DOGS-26088801.md) | **§17 收尾**：配方 = 改无人机 `Mount+0x00` 一个 u64 · 三条硬规则（资源驻留 / 载体装填 / 开火输入）· **§17.3 白名单账本** · **§27.1 副武器 P-19 实机通过 · §28 根因链（弹种 delta 写 `Proj+0=296`）· §30 载体装填机制修正：GD 装填 = 直接填弹匣、不扣备弹（墙版 GL-21 60 发/备弹 0 仍能装填；AC-8 两段装填）· §30.4.1 `WeaponRounds +92` = 单次装填量 ✓✓（改 10 后狗/玩家都一次装满）· §30.5 狗（不扣备弹）vs 玩家/工事座位（扣备弹）路径对照** | `26088801` |
| **改背包数值（跳跃冷却/跳跃高度/补给次数/护盾半径/位移距离）** | [BACKPACK-VALUES](docs/tables/BACKPACK-VALUES-26088801.md) | **§1 五个组件的字段表（偏移+语义名+现值）· §2 一条命令 · §3 第一轮已装盘** | `26088801` |
| **背包能不能"换特性"（把跳跃搬到补给包）** | [BACKPACK-LINE](docs/tables/BACKPACK-LINE-26088801.md) | **§8 收口：纯数据走不通（四轮实验 + 按 5 崩溃）· §7.4 字段类型图（typelib + HD2Runtime）** | `26088801` |
| **哨戒炮/炮塔多久自动消失、各字段含义** | [SENTRY-TURRET-FIELDS](docs/tables/SENTRY-TURRET-FIELDS-26088801.md) | **§2 寿命字段（`HellpodPayload +0x04`）· §3 逐组件字段表 · §4 一条命令** | `26088801` |
| **哨戒挂到载具上「不出模型 / 未展开 / 开火点悬空」** | [SENTRY-TURRET-FIELDS](docs/tables/SENTRY-TURRET-FIELDS-26088801.md) | **§3.8.4 改 `state_machine` 的 `layer.DefaultState`（✓✓ 实机）· §3.8.4.1 四态语义 + 部署完成态判据 · §3.8.4.2 九哨戒 = 七份 SM / 两套模板** | `26088801` |
| **炮塔/工事挂到载具：状态机改哪一层、改成几（每件/每类配方）** | [TURRET-SM-RECIPES](docs/tables/TURRET-SM-RECIPES-26088801.md) | **§1 五条判据 · §3 模板 A 逐件 · §4 模板 B 逐件 · §5 人操工事两轴判据 · §6 非武器件 · §7 一件一行总表 · §9 十一条坑** | `26088801` |
| **有限数量的跨包加载（通用产出）** | [LIMITED-CROSS-PACKAGE-LOADING](docs/engine/LIMITED-CROSS-PACKAGE-LOADING-26088801.md) | **§2 三个可编辑量 · §3 解析链 · §5 一条命令 · §6.9 指针 · §7 边界** | `26088801` |
| **声明口不够用 / 想不占口就加载一整个包的资源** | [RESOURCE-RESIDENCY](docs/engine/RESOURCE-RESIDENCY-26088801.md) | **§1 两条路线分工 · §3 P1–P4 实测 · §4 三条配方 · §5 `whole_package_patch.py` · §8 坑** | `26088801` |

### 理解原理

| 想知道 | 读 | 关键小节 |
|---|---|---|
| 密封盒 / 内容哈希 / 校正字怎么工作 | [DLBIN-SEALED-BOX](docs/engine/DLBIN-SEALED-BOX.md) | §1–§6 · §10 取密钥 · §11 实机验收 |
| `LDLD` 容器 / 组头 / 行起点怎么算 | [WORKFLOW](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) | §3 定位 · §4 保哈希 |
| 每张表的组 / 行 / 步长 / 尾块几何 | [TABLE-DICTIONARY](docs/tables/TABLE-DICTIONARY-25988413.md) | 全表字典 |
| 表里的名字从哪来（locid / `.strings`） | [LOCID-NAMES](docs/tables/LOCID-NAMES-25988413.md) · [ROW-NAMING](docs/tables/ROW-NAMING-25988413.md) · [ENTITY-LOCID](docs/tables/ENTITY-LOCID-26088801.md) | — |
| 实体库 275 个块 / 组件布局 | [ENTITY-TABLE](docs/tables/ENTITY-TABLE-25988413.md) | 全文 |
| 战备 → 弹丸 → 爆炸这条引用链 | [STRATAGEM-REFERENCE-CHAIN](docs/tables/STRATAGEM-REFERENCE-CHAIN-25988413.md) | 全文 |
| 战备表 400 B 行的完整解码 | [STRATAGEM-SETTINGS-DECODED](docs/tables/STRATAGEM-SETTINGS-DECODED.md) | 全文 |

### 密钥与前置

| 想知道 | 读 |
|---|---|
| **只有一份 dump，怎么自己解出密钥**（RVA + XOR 常数 + seek 工具 + 三重验证） | [DLBIN-SEALED-BOX §10](docs/engine/DLBIN-SEALED-BOX.md) |
| 所有密钥来源与各自代价 | [WORKFLOW §1.2.1](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) |
| 怎么判盘上是原版（「哈希 == 锚点」识别不出保哈希 mod） | [WORKFLOW §2.5](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) |
| 没有密钥能练什么 | [WORKFLOW §2.6](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) · [§4 无密钥也能练](#4-无密钥也能练) |

### 坑与边界

| 想知道 | 读 |
|---|---|
| **93 条坑**（现象 / 规则 / 三态） | [WORKFLOW §10](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) |
| 工具的行为陷阱（不报错但会让你误判） | [WORKFLOW §5.2](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) · [§3 工具清单](#3-工具清单tools) |
| 走不通的路：进程内存 / 未签名 DLL / 加载器 | [MEMORY-ACCESS](docs/boundaries/MEMORY-ACCESS-25988413.md) · [LOADER-SPEC](docs/engine/LOADER-SPEC-25988413.md) |
| 虚拟机路线为什么也不行 | [VM-DUMP](docs/boundaries/VM-DUMP-25988413.md) |
| 还缺什么实验 / 哪些字段没找到 | [WORKFLOW §12](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) |
| 四条路线横向比较（为什么选盘上数据） | [ROUTES-COMPARE](docs/builds/ROUTES-COMPARE-26088801.md) |

### 换 build 与工具

| 想知道 | 读 |
|---|---|
| 新 build 到手先跑哪三步 + 锚点怎么复验 | [BUILDS.md §3](BUILDS.md) |
| **每个 build 到底改了什么 / 哪些结论还成立** | [§2 `builds/` 跨 build 对照表](#builds) |
| 这次更新到底把 55 张表改了没 | [BUILD-26088801-DIFF](docs/builds/BUILD-26088801-DIFF.md) |
| 工具清单与各自验证状态（依赖 / 三态） | [§3 工具清单](#3-工具清单tools) |
| 游戏内探针怎么写（旧探针为什么"能加载但静默失效"） | [PROBE-AUTHORING](docs/engine/PROBE-AUTHORING-25988413.md) |
| Lua 运行时 / API 面 / `Gui.*` 绘制 | [LUA-API](docs/engine/LUA-API-25988413.md) · [STINGRAY-API](docs/engine/STINGRAY-API-25988413.md) · [GUI-HUD](docs/engine/GUI-HUD-25988413.md) |
| 数据文件路线为什么不需要执行权 | [PATCH-LOADER-DESIGN](docs/engine/PATCH-LOADER-DESIGN-26088801.md) |

### 外部参照

| 想知道 | 读 |
|---|---|
| 别人怎么把内部名接到显示名 | [PRIOR-ART-NAMING](docs/cases/PRIOR-ART-NAMING.md) |
| wiki 里的原始解码数据能补哪些字段 | [WIKI-DATA-MODULES](docs/cases/WIKI-DATA-MODULES.md) · [WIKI-LOCAL-DB](docs/cases/WIKI-LOCAL-DB.md) |
| **多个 mod 改同一份文件的不同字段，想同时用** | [MOD-MERGER](docs/cases/MOD-MERGER-26088801.md) | **§1 算法 · §2 用法 · §3 逐字节等价证明 · §4 前提与边界** | `26088801` |
| 社区包怎么做 / 能不能共存 | [CASE-STUDY](docs/cases/CASE-STUDY-20261021.md) · [COMMUNITY-MODS-COMPAT](docs/cases/COMMUNITY-MODS-COMPAT-26088801.md) · [PATCH-SALVAGE](docs/builds/PATCH-SALVAGE-25988413.md) |

## 2. 按类型浏览（68 篇）

| 类别 | 放什么 | 篇数 |
|---|---|---:|
| [`builds/`](docs/builds/) | 每个 build 的总体变化、差异、路线取舍 | 4 |
| [`engine/`](docs/engine/) | 引擎侧：格式封装、API 面、Lua 运行时、探针、加载器、**有限数量的跨包加载** | 10 |
| [`tables/`](docs/tables/) | 数据表与实体库的解码 / 改写 | 24 |
| [`explosions/`](docs/explosions/) | 爆炸与弹头（玩法层 + 外观层） | 2 |
| [`boundaries/`](docs/boundaries/) | 被挡住的路：进程内存、虚拟机 | 2 |
| [`cases/`](docs/cases/) | 案例与外部参照：社区包、贴图委托、wiki 数据、**完整工作流**、**老 mod→数据路线修复版 playbook（含两个 C 档样板）**、**第三方护甲多被动 / Sterilizer 改治疗 / P-11 Self-Heal / VanillaPlus 两件 / SHODAN 额外战备 侦察**、**网络复制层探针系列**、**实体表在线改写实机证明**、**EXO-45 换臂（memmod 复现）** | 26 |

### `builds/`

**跨 build 对照**（逐层细节在各篇正文里；本表只回答「现在该信哪一版」，操作步骤见 [BUILDS.md](BUILDS.md)）：

| build | 日期 | 状态 | 这一版是什么 / 在它上面立起了什么 | 逐层记录 |
|---|---|---|---|---|
| **26088801** | 2026-10-22 | **当前** | 7.2.1 hotfix：密钥与类型库不变、55 张表 0 变化；变的是 `exe` / `game.dll` 与 bundle 打包（5 个 ±64 KB） | [BUILD-26088801-DIFF](docs/builds/BUILD-26088801-DIFF.md) |
| 25988413 | 2026-10-20 | 历史基线 | `*-25988413.md` 的实测版本：结构层（密封盒 / 内容哈希 / 块布局 / 行命名 / locid）在此立起，玩法层（实体改写 / 可选弹种 / 独立弹药池 / 爆炸弹头线）在此实机 | [BUILD-25988413](docs/builds/BUILD-25988413.md) |
| 25480438 | 2026-10-15 | **不收录** | 只有本地备份；结论已过时会误导 | — |

**逐篇记录**：

| 文档 | 一句话 | build |
|---|---|---|
| [BUILD-25988413](docs/builds/BUILD-25988413.md) | 10-20 更新改了什么：文件身份、代码与资源层、更新后工具链还剩什么能用 | `25988413` |
| [BUILD-26088801-DIFF](docs/builds/BUILD-26088801-DIFF.md) | 7.2.1 hotfix 逐层比对：55 张表一张没变，变的是 exe/game.dll 与 bundle 打包（含一次误报复盘） | `26088801` |
| [ROUTES-COMPARE-26088801](docs/builds/ROUTES-COMPARE-26088801.md) | 战备线与护甲线谁先开：四个判据逐项对照 | `26088801` |
| [PATCH-SALVAGE-25988413](docs/builds/PATCH-SALVAGE-25988413.md) | 22 个旧补丁按资源类型清点：资产只能当原料，外观方向是新活不是抢救 | `25988413` |

### `engine/`

| 文档 | 一句话 | build |
|---|---|---|
| [DLBIN-SEALED-BOX](docs/engine/DLBIN-SEALED-BOX.md) | `.dl_bin` 封装模型：48 B 头 + `crypto_box_seal` + keystream 关系；**§10 用旧 build 转储取密钥** | `25988413` |
| [ENGINE-API-25988413](docs/engine/ENGINE-API-25988413.md) | 内存路全死之后引擎侧还能读到什么，逐条三态 | `25988413` |
| [STINGRAY-API-25988413](docs/engine/STINGRAY-API-25988413.md) | 游戏内 `pairs()` 枚举到的 446 个 Stingray 入口 | `25988413` |
| [LUA-API-25988413](docs/engine/LUA-API-25988413.md) | Lua API 全量面：125 命名空间 / 2,483 成员 | `25988413` |
| [LUA51-TOOLING-25988413](docs/engine/LUA51-TOOLING-25988413.md) | `lua51.dll` 消失后，迁到 stock Lua 5.1 要改哪些工具与判据 | `25988413` |
| [PROBE-AUTHORING-25988413](docs/engine/PROBE-AUTHORING-25988413.md) | 新 build 上怎么写探针；旧探针为什么"能加载但静默失效" | `25988413` |
| [GUI-HUD-25988413](docs/engine/GUI-HUD-25988413.md) | 纯 Lua 自绘屏幕文字：`Gui.*` 真实签名（三次崩溃换来） | `25988413` |
| [LOADER-SPEC-25988413](docs/engine/LOADER-SPEC-25988413.md) | 共享加载器必须满足什么，含 `package.loadlib` + 原生 DLL 的最终否证 | `25988413` |
| [PATCH-LOADER-DESIGN-26088801](docs/engine/PATCH-LOADER-DESIGN-26088801.md) | 数据文件路线不需要执行权：用离线合成器替掉 boot 覆盖 | `26088801` |
| ★★ [LIMITED-CROSS-PACKAGE-LOADING-26088801](docs/engine/LIMITED-CROSS-PACKAGE-LOADING-26088801.md) | **跨包加载全账**：`+0xA8`+`+0xF8` 双声明口 / 解析链 / 「行在不在**普通任务栏**」是唯一判据（教学关行 138 ✗） / `+0xC8` 额外战备链把口带进栏（✓✓） / §6.9 只留指针 → 资源层驻留已单独成文 | `26088801` |
| ★★ [RESOURCE-RESIDENCY-26088801](docs/engine/RESOURCE-RESIDENCY-26088801.md) | **资源层驻留（`.patch_N`）主档**：声明口管「包在不在」、补丁管「资源在不在」的**两条路线分工** / 机制（连续序号、file_id 全局解析、类型不挑、伴生 gpu·stream、同 id 高号胜） / **P1–P4 实测**（79 KB 顶掉 68 MB 包、整包 50/51 条、整包 41 条给载具挂载件且零声明）/ 三条配方 / `whole_package_patch.py`（G1–G8，重跑产物与盘上逐字节相同）/ 上限与坑（含 `srkit` 把 `unit` 显示成 `mesh` 的 bug） | `26088801` |

### `tables/`

| 文档 | 一句话 | build |
|---|---|---|
| ★★ [FACTION-BEHAVIOR-26088801](docs/tables/FACTION-BEHAVIOR-26088801.md) | **阵营/AI 行为/外来件/特效的全线台账**：`Faction +0` 位掩码（2=终结者 4=光明族 8=自动化 1=超级地球）· `Behavior +0`（645→658 把 AI 领走）· 挂载换件 · **§17 特效根因：粒子包写在教学关行 138 ⇒ 普通任务不读；搬到 SOS 行 59 后拖尾/命中爆炸全出（✓ 实机）** · `+0xC8` 额外战备链把声明口带进栏（✓ 实机） | `26088801` |
| ★ [EXO-ARM-VARIANTS-26088801](docs/tables/EXO-ARM-VARIANTS-26088801.md) | **机甲臂件变体普查**：社区编号 MK2/MK3 对应哪些实体键；200 发机炮件与原版只差「弹匣 100→200 + 默认射速 175→300 rpm」；真正的 `_MK2` 类型在导弹家族（伤害/AP/爆炸逐项对照） | `26088801` |
| ★ [WEAPON-FIRE-MODES-26088801](docs/tables/WEAPON-FIRE-MODES-26088801.md) | **射击模式 / 射速档位**:`FireMode` 四连槽 `+0x90…0x9C` + `function_info` 选择键（`Firemode=3` / `ROF=2`）；枚举 1 自动 / 2 半自动 / 3 连发 / **4 齐射 / 5 安全 / 6 不安全 / 7 全射**（**槽位上限 3**）；任意枪可加全自动与全射（均已实机） | `26088801` |
| ★ [PLAYBOOK-LUA-MOD-TO-DLBIN](docs/cases/PLAYBOOK-LUA-MOD-TO-DLBIN.md) | **老 mod → 数据路线等价修复版**：五步流水线（开包/读载荷/归层 L1–L4/映射/实现）+ **A/B/C 三档判定（dl_bin 等价 / 跨载体等价 / 不可实现，禁用「不可等价」）** + 载体能力表 + 跨 build 常量重取规则 + **五个样板案例（A×2 / B / C×2：代码型 P-11 Self-Heal、数据边界型 锁定锥角）** + 报告骨架；配套工具 `lua_payload_dump.py`、技能 `skills/hd2-lua-mod-to-dlbin` | 跨 build |
| ★ [RECON-VPM-BOUNCE-STICKY](docs/cases/RECON-VPM-BOUNCE-STICKY-26088801.md) | **VanillaPlus Megapack 两件侦察**：`BetterStratagemBounce` 改的是**战备表 `+0x170` 的 bit 0x02**（不是 sticky，且在本 build 会拒绝执行）；`StickyGrenadeHandles` 改的是材质 `userData`（4 B）——**已定位**到 physics 载荷内联 20 B 材质记录的数据字（G-123 `+0x15C` / G-109 `+0xCC`，全量 4,839 载荷扫完），`ThrowableComponent+0x54/+0x164` 只读 | `26088801` |
| [STICKY-COMPONENT-26088801](docs/tables/STICKY-COMPONENT-26088801.md) | **粘附组件全解**：38 槽 + 19 行 × 76 B；`+0x2C` = 粘住时的命中伤害行（飞刀 648）、`+0x3C/+0x40` = 两个 AbilityId、`+0x08` 附着旋转全表 -90°；热熔的 sticky 是最小配置 | `26088801` |
| ★ [STATUS-EFFECTS-26088801](docs/tables/STATUS-EFFECTS-26088801.md) | **状态效果表全解**：73×160 B + 名字 blob（id↔名字↔每跳伤害行全表）；全库只有 10 处能施加状态；**Thermite = id 13**（tick 行 533）却无人引用；§7 **状态爆 = 孤儿爆炸行 → 伤害行 → 状态槽**（265 条无主爆炸 + P-11 治疗爆配方，**✓ 实机**：脚下回血、>2 m 不回血） | `26088801` |
| ★★ [UNRELEASED-STRATAGEMS-26088801](docs/tables/UNRELEASED-STRATAGEMS-26088801.md) | **未发布战备候选名单**：153 行逐行分类（85 已发布 / 41 任务子项 / 9 载具 / 2 个 `(NOT USED)` / 彩蛋）；**七条已实机可用**（138 M-104 / 36 额外扫射 / 150 A2A 导弹 / 64 烟幕行走弹幕 / 145 纸屑 / 50 飞鹰掠过 / 5 照明弹），119 半成品；`--chain` 一次带 3 件的配方 + 判读表 | `26088801` |
| ★ [CHARGE-WEAPONS-26088801](docs/tables/CHARGE-WEAPONS-26088801.md) | **蓄力武器**：`WeaponChargeComponentData`（20 槽 + 11 行 × 216 B）三档状态（`ChargeTime`+`ProjType`）+ 12 倍率；**蓄满时间 ✓ 实机**（ARC-3 按下几乎立刻放电）；「不蓄满能否开火」= `Min.ProjType` 非 0（6/6）；过蓄伤害 = `DamageMin→DamageOver`（Railgun 1.0→2.5）· 过蓄自毁 = 爆炸 type 326→伤害行 362（2000 伤害 / 0.4-2-3 m） | `26088801` |
| ★ [LOCKON-TARGETING-26088801](docs/tables/LOCKON-TARGETING-26088801.md) | **锁定/制导武器（✓ 结项）**：可改 = 距离（`SensorEye.distance`）+ 锁定时间（`lock_on_target_time`，均实机）；改不动 = 锥角（四路否证）+ 可锁集合（标签位图无映射）；含 7 轮实验台账与武器→投射物→制导行映射 | `26088801` |
| ★ [ENTITIES-TABLE-LIVE-EDIT-26088801](docs/cases/ENTITIES-TABLE-LIVE-EDIT-26088801.md) | **实体表在线改写 ✓ 实机**：47 MB `generated_entities.dl_bin` 可改 + 重新封装 + 引擎接受；完整证据链（解封/锚点哈希/门禁/盘上回读/实机） | `26088801` |
| ★ [ARMOR-PASSIVE-STATS-26088801](docs/tables/ARMOR-PASSIVE-STATS-26088801.md) | **护甲被动/stat 行的文件侧能力模型**：pm vs sm 两通道、两层作用范围、7 个 stat 槽、三条硬约束、4 个已验证配方 | `26088801` |
| ★ [TABLE-DICTIONARY-25988413](docs/tables/TABLE-DICTIONARY-25988413.md) | **全表字典**：55 张表几何 + 类型库字段偏移（1,208 类型 / 7,349 成员） | `25988413` |
| ★ [ENTITY-TABLE-25988413](docs/tables/ENTITY-TABLE-25988413.md) | 47 MB 实体库离线改写：组件块、哈希闸门、校正字、可选弹种、LoadoutEntry 否证 | `25988413` |
| [ENTITY-LOCID-26088801](docs/tables/ENTITY-LOCID-26088801.md) | 实体 → 游戏内名字的唯一出处（`EncyclopediaEntry`，643 行可解） | `26088801` |
| ★ [MOUNT-SEATS-26088801](docs/tables/MOUNT-SEATS-26088801.md) | **载具挂载 / 座位两表全解**：Mount = 328 槽 + 165 × 120 B（`MountComponent` = 5 × `MountInfo`，`MountSide` 已有资源名直证）；SeatCollection = 112 槽 + 56 × 424 B（`TransitionId` + `Passenger[16]` + `ActiveAimConstraint[22]`）；**122 件挂载件分桶与 memmod 旧账逐桶吻合**（16/4/1/**11**/37/53）+ 四条旧实测交叉；`mount_table.py` 换件保哈希（G1–G10）+ 两个 sealed 工件；**§11 M-102 枪手位 = 武器挂点（✓✓ MG-206 / MG-43 实机正常；§11.4 紫问号 = 声明包不被载具加载，整包驻留 patch_30；§11.7 AC-8 ✓✓：装填需玩家背对应背包；§11.8 手枪 P-19 ✓✓；§11.9 规则汇总 R1–R7）· §12 E/GL-21 Grenadier Battlement = 墙 + 挂载的 GL-21 变体（同弹道、低后坐 25/25 vs 170/175、60 发无备弹；§12.6 独立武器但非装备表物品；§12.7 挂 Guard Dog 组件差集 = 只缺 LoadoutPackage/MeleeAttack，patch_33 实测 ✓✓：模型+开火+60 发打空能装填（GD 装填直接填弹匣，见 BACKPACK-DOGS §30）；§12.8 墙换 MG-43 ✓✓（装填扣备弹 = 工事座位走玩家路径）· §13 结项总表 R1–R8 + 盘面已复原（删 patch_18–33，152.2 MB）** | `26088801` |
| [LOCID-NAMES-25988413](docs/tables/LOCID-NAMES-25988413.md) | 32 位本地化 ID：`.strings` 全局 ID→文本表怎么打通六张表的名字 | `25988413` |
| [ROW-NAMING-25988413](docs/tables/ROW-NAMING-25988413.md) | 逐行名字的两条取法、判据、以及位置法取错过名的两张表 | `25988413` |
| ★ [WEAPON-CUSTOMIZATION-DECODED](docs/tables/WEAPON-CUSTOMIZATION-DECODED.md) | 武器配件总表：88 B 行、九类槽位枚举、252 行可读导出；**§7 配件 → entity delta 落地链（build `26088801`：`AmmoType` 写 `ProjectileWeapon+0`、`Magazine` 写 `cust+0x80`，含组件索引表与坑）** | `25988413` · §7 `26088801` |
| ★ [STRATAGEM-SETTINGS-DECODED](docs/tables/STRATAGEM-SETTINGS-DECODED.md) | 战备表 400 B 行 / 12 组解码，含三处旧结论的自我否证 | `25988413` |
| ★ [STRATAGEM-FIELDS-26088801](docs/tables/STRATAGEM-FIELDS-26088801.md) | 战备字段总表：面板公式（先预测后实测）、散布、**Eagle 回收（§5.4）**、条目 ID 重复=崩溃 | `26088801` |
| ★ [DAMAGE-SETTINGS-26088801](docs/tables/DAMAGE-SETTINGS-26088801.md) | 伤害表 76 B 行字段图：5 张引用表 / 共享伤害行 / **行内零 padding 的宿主策略** / 完整改值链 | `26088801` |
| ★★ [SENTRY-TURRET-FIELDS-26088801](docs/tables/SENTRY-TURRET-FIELDS-26088801.md) | **哨戒/阵地炮塔的字段图**：寿命 = `HellpodPayloadComponentData +0x04`（f32 秒；MG-43=150、迫击炮=180、人操阵地=0 不自毁）—— 三源交叉（本仓库数据 / SHODAN「Time deployed (s)」/ wiki）；另给 StratagemInfo、Turret（转速/俯仰·水平限位）、弹匣、射速三档、ergonomics、护甲的逐字段对照表 | `26088801` |
| ★ [POD-RACK-26088801](docs/tables/POD-RACK-26088801.md) | 投送舱换载荷：rack 568 B 行 / 槽位语义 / **`+0xA8`+`+0xF8` 双包声明** / item→包解析表 / 六轮实机 / **§8 整包补丁驻留（✓✓：一个舱三件、两个零声明）** | `26088801` |
| ★★ [TURRET-SM-RECIPES-26088801](docs/tables/TURRET-SM-RECIPES-26088801.md) | **炮塔/工事状态机配方总表（手册型）**：一个 u32 修好一件（出场即展开、不自转、能瞄准）。五条判据 = 模板 A 选展开态 / 模板 B 钉"部署过渡末帧定格" / 按 state 名 `0x9EA750D5` 关扫视层 / 人操两轴只看"是不是常开 `Time` 层 + 有键 clip" / 字节级自检；**11 件逐件配方**（AC-8·火箭·火焰·激光·迫击炮·特斯拉·MG-43·加特林·HMG-101·AT-12·FX-12）+ 一件一行总表 + 11 条已踩坑 | `26088801` |
| ★★ [BACKPACK-VALUES-26088801](docs/tables/BACKPACK-VALUES-26088801.md) | **背包自身数值的字段表 + 改法（手册型）**：`Jumppack +0x00` 起跳速度 40（`+0x9C` 悬停 = −1 无/6 s）、`Recharge +0x00` 冷却 15、`Deposit +0x00/+0x04/+0x08` 补给次数 4/4/1、`Shield +0x00/+0x4C/+0x58/+0x5C/+0x60` 半径与耐久回充、`Displacement +0x78…` 位移全套；一条命令一个字段 + 第一轮已装盘（冷却 5 s / 跳高 60 / 补给 8 次 / 护盾 2 m） | `26088801` |
| ★★ [BACKPACK-DOGS-26088801](docs/tables/BACKPACK-DOGS-26088801.md) | **AX 狗背包换枪线（✓ 结项）**：挂载句柄 = 无人机 `MountComponentData+0x00` 一个 u64；**三规则**：R1 包必须驻留否则紫问号 / R2 载体决定装填（GD·HotDog·DogBreath 有，Rover·K-9 无）/ R3 AI 只"按住"不给"松手"（ARC-3 ✗、Quasar ✓、W.A.S.P. 锁定 ✓）；**白名单** MG-43·AC-8·PLAS-1·W.A.S.P.·Quasar·炮塔 ✓✓；**副武器 P-19 ✓✓（§27.1 四狗开火、手感与玩家版一致）**，根因链见 **§28：实体记录是休眠值，弹种配件 delta 才写 `Proj+0=296`**；**§29 把 P-2 Peacemaker 挂 Guard Dog 验证第二把休眠型武器 ✓✓（正常开火 + 弹匣渲染，半自动也成立）**；**§30 载体装填机制修正 ✓✓：GD 装填 = 直接填弹匣、不检查/不扣备弹；分段次数由枪自己的单次装填量决定（AC-8 两段）；§30.4.1 `+92`=单次装填量 ✓✓（狗/玩家通用）· §30.5 狗 vs 玩家/工事装填路径对照 ✓✓**；十架无人机映射 + `BehaviorId` 账本 + 未解项 | `26088801` |
| ★ [BACKPACK-LINE-26088801](docs/tables/BACKPACK-LINE-26088801.md) | 背包族开线档：35 件全集与投放两条路线 / **§7.4 字段类型图（typelib 类型名 × HD2Runtime 语义名）** / **§8 收口：给别的背包加跳跃能力 = 纯数据走不通**（四轮实测，按 5 崩溃；`--row` 共享行技巧可给满块加组件） | `26088801` |
| ★ [WEAPON-AMMO-RESERVE-26088801](docs/tables/WEAPON-AMMO-RESERVE-26088801.md) | 三种供弹模型 / `Rounds` 与 `Magazine` **两套备弹字段** / 五把背包武器改成自带备弹（已实机）/ 清空槽位的坑 | `26088801` |
| ★ [PROJECTILE-PROXIMITY-26088801](docs/tables/PROJECTILE-PROXIMITY-26088801.md) | **近炸引信字段**（弹丸行 `+0x94` 半径 / `+0x88` 阈值角 / `+0xA0` 保险距离）；AC-8 在备弹 289 上 | `26088801` |
| [STRATAGEM-REFERENCE-CHAIN-25988413](docs/tables/STRATAGEM-REFERENCE-CHAIN-25988413.md) | 战备→弹丸→爆炸：只有弹丸↔爆炸一跳，战备→弹丸是否证 | `25988413` |

### `explosions/`

| 文档 | 一句话 | build |
|---|---|---|
| ★ [EXPLOSION-PROJECTILE-25988413](docs/explosions/EXPLOSION-PROJECTILE-25988413.md) | 玩法层：换弹头整行、改 `+144`/`+156` 换爆炸、改 `+80`/`+84` 加破片 | `25988413` |
| ★★ [EXPLOSION-VISUAL-26088801](docs/explosions/EXPLOSION-VISUAL-26088801.md) | 外观层：粒子 `+0x38`、震屏 `+0x28`、整行克隆、`+0xA8` 纯数据跨包加载 | `26088801` |

### `boundaries/`

| 文档 | 一句话 | build |
|---|---|---|
| [MEMORY-ACCESS-25988413](docs/boundaries/MEMORY-ACCESS-25988413.md) | EAC 剥掉 `PROCESS_VM_READ`、`ffi` 消失、DLL 加载两道闸门的实测 | `25988413` |
| [VM-DUMP-25988413](docs/boundaries/VM-DUMP-25988413.md) | 虚拟机路线：宿主读 guest 内存已证实，过不了 EAC 的虚拟机检测 | `25988413` |

### `cases/`

| 文档 | 一句话 | build |
|---|---|---|
| ★ [EXO45-ARM-SWAP-26088801](docs/cases/EXO45-ARM-SWAP-26088801.md) | **EXO-45 换臂（memmod 复现）**：左臂 ← 突破者盾、右臂 ← 伐木者加农炮；换件只写 `MountInfo.item`，包驻留用**两个免费常驻行**的 `+0xA8`（`Reinforce` 57/138 + `SOS Beacon` 59）—— 不用 runtime、不用携带源机甲 | `26088801` |
| ★ [FILE-ROUTE-WORKFLOW-26088801](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) | **知识库主管线**：完整 8 步链、5 张表锚点、宿主三选（含三次崩溃归因）、**93 条坑**、EAGLE 双行案例、未决清单 | `26088801`（流程跨 build） |
| [CASE-STUDY-20261021](docs/cases/CASE-STUDY-20261021.md) | 三个社区包拆出来的路：`.patch_N` 能替换任意资源类型，纯资产 mod 不需要 loader | `25988413` |
| [TEXTURE-SWAP-10X-APEX](docs/cases/TEXTURE-SWAP-10X-APEX.md) | 一次贴图替换委托：BC1 往返误差、材质槽判定、`patch_3` 部署与回滚 | 跨 build |
| [COMMUNITY-MODS-COMPAT-26088801](docs/cases/COMMUNITY-MODS-COMPAT-26088801.md) | SSEO 与护甲多被动为何不能共存：争的是同一文件的基线所有权 | `26088801` |
| [PRIOR-ART-NAMING](docs/cases/PRIOR-ART-NAMING.md) | 别人怎么把内部名接到显示名/页面（filediver / HD2Runtime / wiki），我们该借哪个 | 跨 build |
| [WIKI-DATA-MODULES](docs/cases/WIKI-DATA-MODULES.md) | wiki `Module:` 命名空间里的原始解码数据清单，能补哪些字段名 | 跨 build |
| [WIKI-LOCAL-DB](docs/cases/WIKI-LOCAL-DB.md) | 不抓 HTML：页面源码 + JSON 模块落本地 SQLite，一条命令查战备/武器全貌 | 跨 build |
| ★ [MOD-MERGER-26088801](docs/cases/MOD-MERGER-26088801.md) | **多个 mod 改同一文件不同字段怎么共存**：抽语义 / 剔哈希脚手架 / 逐字节判冲突 / 逐字节等价证明 | `26088801` |
| ★ [RECON-ARMOR-MULTI-PASSIVE](docs/cases/RECON-ARMOR-MULTI-PASSIVE.md) | **第三方「护甲多被动」只读侦察**：`passive_bonuses` 的 payload 布局（pm/sm 双数组）、**效果在 sm 行**、全表只有 7 个 stat 槽、描述隐藏=末 4 B 清零、它的堆叠配方与安全设计 | `25988413`（结构在 `26088801` 已逐字段核对一致） |
| ★ [RECON-STERILIZER-HEAL](docs/cases/RECON-STERILIZER-HEAL-26088801.md) | **第三方「Sterilizer 改治疗」只读侦察**：改的是**伤害行**的 4 组字段（状态槽 0/1 的 type+value、`element`、damage）；附带**伤害行 76 B 完整字段图**与**状态效果表解码**（73×160 B + 名字 blob → id↔名字全表） | `26088801` |
| ★★ [RECON-P11-SELF-HEAL](docs/cases/RECON-P11-SELF-HEAL-26088801.md) | **C 档样板（代码型）**：P-11 Self-Heal v1.0.4 = 运行时 `player_fired` 事件 + `Player:heal`（**一条数据都没改**，413 行源码）；「开火即回血」数据侧没有事件钩子 ⇒ **C · 不可实现**；替代 = 数据侧**治疗爆**（孤儿爆炸 254 + 治疗行 446，打脚下 2 m 内回血 ✓ 实机 / >2 m 不回血 ✓ 实机 / **顺带修部位 ✓ 实机**） | `26088801` |
| ★★ [RECON-SHODAN-EXTRA-STRATAGEM](docs/cases/RECON-SHODAN-EXTRA-STRATAGEM-26088801.md) | **额外战备 = `StratagemInfo +0xC8`**（另一条战备的 `+0` id，不占 4 个配装位，引擎跟链、成环崩）：SHODAN v4.1.0 源码级定位 + 本 build 153 行核对（Eagle 全 = 51 `EAGLE. REARM`）；**M-104 Incinerator FRV = id 138 / 实体 `frv_flamer` 本 build 完整存在**；工具 `stratagem_extra.py`（G1–G7 含环检测）；**✓ 实机**：带 Resupply 链式送 `Precision Strike → M-104`，两件都出现在战备条且可呼叫 ⇒ 未发布战备走数据路线进任务 | `26088801` |
| ★ [NETWORK-READ-QUICKREF](docs/cases/NETWORK-READ-26088801-QUICKREF.md) | **网络复制层读取一页速查**：正确调用形态、六道闸、字段字典（16 条 hash↔名字）、能力边界 | `26088801` |
| ★ [PROBE-READ-GUARDED](docs/cases/PROBE-READ-GUARDED-26088801.md) | 自建探针 run4–run8 全记录：名字形态、batched 语义、seat 70 = 被击倒、时间线纪律 | `26088801` |
| [HUDPLUS-0.5.3-LIVE-PROOF](docs/cases/HUDPLUS-0.5.3-LIVE-PROOF-26088801.md) | HUD+ 0.5.3 实机可用 + 从它反推出的正确 API 形态；含 7 个 frag 模块解码 | `26088801` |

## 3. 工具清单（`tools/`）

**82 个脚本（`tools/*.py` 实数），全部在库**（§3.5 另列「文档里提到但仓库故意没有」的，不计入这个数）。

本目录全部工具**只读 / 离线**：没有一个会读游戏进程内存、注入或改内存数值。改数据走「解封装 → 改字节 → 解校正字 → 保哈希 → 重新封装」这条资源侧路线（原理见 [DLBIN-SEALED-BOX](docs/engine/DLBIN-SEALED-BOX.md)）。
依赖列是**可选**的：核心表工具只需标准库（外加同目录的 `murmur64.py` / `dlbin_seal.py`）。凡是打了「自检」的，都能直接 `python tools/<名字> --selftest` 复跑，**不需要游戏文件**。

**按任务速查**：

| 我想… | 工具 |
|---|---|
| 把当前 build 的表解封成明文 | `build_cache.py` · `dlbin_seal.py open-key` |
| 改几个字节但保住内容哈希 | `plain_edit.py`（通用）· `stratagem_tune.py`（战备）· `expl_set.py`（爆炸）· `proj_copy_row.py`（弹丸整行）· `entities_modeb.py`（实体）· `pod_rack_swap.py` / `rack_edit.py`（投送舱槽位） |
| 查某张表的几何 / 字段偏移 | `table_dictionary.py` · `typelib.py` |
| 查某行的名字 / 本地化文本 | `table_row_names.py` · `table_locid_scan.py` · `stratagem_display_names.py` · `entity_locid_scan.py` |
| 更新后对比到底变了什么 | `build_diff.py` · `build_geometry_diff.py` |
| 打资源补丁 / 换贴图 | `resource_patch.py` · `swap_texture.py` · `export_textures.py` |
| 把一个包整包塞进常驻包（不占声明口） | `whole_package_patch.py`（`list` / `build` / `check`，见 [RESOURCE-RESIDENCY](docs/engine/RESOURCE-RESIDENCY-26088801.md)）|
| 立论或否证一次扫描 | `table_xref_scan.py` · `probe_*` · `find_bombs_salvos_pair.py` |
| 查 wiki 的原始解码数据 | `wiki_query.py` · `wiki_build_db.py` · `fetch_wiki_modules.py` |
| 算 / 解 Murmur64A | `murmur64.py`（库）· `murmur64a.py`（CLI） |
| 给载具换武器 / 改挂载槽 | `mount_table.py`（`list` / `show` / `seats` / `find` / `swap` / `verify`） |
| 离线合成一个数据 mod 补丁 | `patch_compose.py` |

### 3.1 数据表 / 封装

| 工具 | 用途 | 依赖 | 验证 |
|---|---|---|---|
| `murmur64.py` | MurmurHash64A（引擎的内容哈希闸门）+ 反解「校正字」，改完字节仍过校验 | 标准库 | ✓ 已实机（全部表工具都走它） |
| `murmur64a.py` | 同一个算法的**命令行版**：`hash` / `solve --word N --target HEX` / `selftest`（库调用请用上面的 `murmur64.py`，两者在自检里互相对表） | 标准库 | ✓ `--selftest` **7/7**（含「解自己的哈希必须解出原来的字」与跨实现对表） |
| `dlbin_seal.py` | `.dl_bin` 密封盒：解/封、配对→keystream、LDLD 结构 | PyNaCl | ✓ 已实机 |
| `dlbin_keyhunt.py` | 在 `game.dll` 里定位打开 `.dl_bin` 的 X25519 密钥（**前提：使用者自己有 dump**） | PyNaCl + cryptography | ⚠ 研究工具；仓库不含任何密钥材料 |
| `dump_read_rva.py` | **从多 GB 全量 minidump 里按 RVA 读虚拟地址**（只 seek 不整读）。旧 build 的接收方密钥就在加载后映像的固定 RVA 上，所以有 dump 就能跳过 aPLib 解包直接取 —— 配方见 [DLBIN-SEALED-BOX §10](docs/engine/DLBIN-SEALED-BOX.md) | 标准库 | ✓ 已实机（本项目这一对密钥就是这么来的，过三重验证） |
| `plain_edit.py` | **任意字节写入**任意 `LDLD` 容器明文，自动用 tail 宿主保住内容哈希；6 门禁（含「声明字段读回」与「其余字节未动」） | 标准库 + `murmur64.py` | ✓ 已实机 |
| `particle_census.py` | 列出某个包里全部 `particles` 资源（挑「供体特效」用；配合 `refs/srkit-names.json` 反查副本分布） | `srkit` + 游戏数据 | ✓ 离线 |
| `particle_strings.py` | 扫包内粒子资源的内嵌字符串 —— **用于证明「粒子无法按名字/内容识别」**（`file_id` 不是名字哈希，粒子内部无可读串） | `srkit` + 游戏数据 | ✓ 否证记录 |
| `typelib.py` | 解析 DataLibrary 类型库（LTLD v4），查表结构 | `dlbin_seal.py` | ✓ |
| `table_export.py` | 把整张表导成**人类可读**的 CSV + Markdown（名字 + 每字段 hex/f32 + 统计 + 一阶嵌套）；`LAYOUTS` 存字段名与枚举注解，`POINTERS` 存 (表, 步长) → 行内名字指针 | PyNaCl + `typelib.py` | ✓✓ 六张表整表导出（weapon_customization 252×13、stratagem 153×68），名字全部走指针 |
| `table_row_names.py` | 抽出逐行名字。**指针优先**：weapon_customization 252 / stratagem 153 / planet_override 44 / status_effect 73 / language 15 / stratagem_upgrade 1；其余表退化为位置法且必须 `串数 == 行数` | PyNaCl + `typelib.py` | ✓ 实机数据抽全（`refs/table-row-names.json`，每表标明机制） |
| `row_pointer_sweep.py` | 扫全部 55 张表找**行内名字指针**，判据是「每行解析出不同的串」，并与位置法交叉验证 | PyNaCl + `typelib.py` | ✓ 6 张表命中；weapon_customization 交叉验证 240/240 一致 |
| `probe_row_name_offsets.py` | 单表深挖指针：命中率 / 不同串数 / 串的类别（显示名 / 键 / 描述键），用来排除小整数巧合 | PyNaCl | ✓ 实机数据 |
| `stratagem_field_scan.py` | 拿系族当标签给每个 4 字节槽打分（族内纯度 + 能否分离 wiki 四色），用来判定分类字段 | PyNaCl | ✓ `+392` 5/6（唯一交集是 cell 0）；`+56`/`+60` 3/6 及以下，否证了「`+56` 的 4 个值 = wiki 四类」 |
| `stratagem_join.py` | 战备行与 HD2Runtime 目录逐名配对（同系族内模糊匹配、一对一），用冷却是否相等反向校验配对；目录快照早于补丁时按 `PATCHED` 表登记 | PyNaCl + HD2Runtime SDK zip | ✓ 21 配对：20 条精确 + 1 条已定案补丁差异（Airburst 100→90），未解释 0 |
| `settings_field_align.py` | 用连接键把 filediver 明文 dump 的字段名对齐到本表偏移（带「常量字段/常量槽」双排除） | PyNaCl + `typelib.py` + filediver JSON | ✓ 弹丸表 18 字段（`name_upper` 连接，132 对） |
| `stratagem_field_align.py` | 按 **wiki 解码值反查战备字段偏移**：拿 `Module:Decodedata-Attacks` 的 `cooldown`/`uses`/`num_bombs`/`num_salvos`/`area_size`… 逐字段与每个 4 字节槽做「无符号」和「f32」双读匹配，用值反推偏移而不是猜 `+60` 是什么 | PyNaCl + wiki 模块 | ✓ 定位 `+104`/`+80`/`+84` |
| `table_xref_scan.py` | 通用跨表引用扫描：找出源表哪个槽命中目标表某列的值（用 `distinct` 判据排除小整数巧合） | PyNaCl + `typelib.py` | ✓ 用它否证「战备行引用弹丸行」 |
| `stratagem_attack_chain.py` | 走通一条链并逐环打印证据：战备行 `+0` → StratagemType 名 → 战备道具资源的 `projectile_type` → 弹丸行 → `+144/+156` → 爆炸行 `+28` | PyNaCl + `typelib.py` + wiki 模块 + filediver dump | ✓ 26 条命中，含 Airburst 的 cone=27 |
| `probe_stratagem_projectile_link.py` | 排查战备行里弹丸类型的编码形式（`+0`/文件下标/`name_upper`/枚举下标），用于否证「战备行有指向弹丸的外键」 | PyNaCl + `typelib.py` | ✗ 四种编码全不命中 |
| `fetch_wiki_modules.py` | 按需拉取 wiki 的 `Module:Decodedata-*` 数据模块（当字段名字典用；wiki 会挡默认 UA，故不随仓库分发） | 标准库 | ✓ 12/12 可拉 |
| `probe_stratagem_fields.py` | 把两份 wiki 战备视图的全部数值字段逐一对到本表槽（含最佳槽报告，能区分「没有」和「有但值不同」） | PyNaCl | ✓ 定位 `+104`/`+80`/`+84` |
| `find_bombs_salvos_pair.py` | 战备 `num_bombs`×`num_salvos` 的**联合**反查：扫所有有序槽对、扫乘积、再按 u8/u16/u32/f32 四种宽度找标志值 | PyNaCl | ✗ 全落空（证明这两项不在战备行里） |
| `fetch_wiki_pages.py` | 用 MediaWiki API 批量缓存 wiki 页面源码，50 页一请求 + sleep；支持 `--category` 与按标题补抓 | 标准库 | ✓ 763 页（战备/武器/护甲/披风/外观/护甲被动/星球） |
| `wiki_build_db.py` | 把页面源码的模板参数 + 模块 JSON 落成 SQLite（`page`/`param`/`entity`/`stratagem`/`weapon`）；`page.kind` 由信息框模板判定 | 标准库 | ✓ 763 页 / 9,312 参数 / 235 武器行 |
| `wiki_match_tables.py` | 把表里解出的名字和 wiki 页面标题对上（精确 / 后缀 / 包含 / 模糊四条规则），输出覆盖率与未匹配清单 | 标准库 | ✓ 护甲 217/237、被动 32/33、星球 277/395；未匹配的都查过确实无页面 |
| `wiki_query.py` | 查本地库：任意页（战备/武器）全貌 + 攻击链解析 + 与解密表并排对照；支持 `--page` / `--field` / `--entity` / `--sql` | PyNaCl（仅 `--sk` 时） | ✓ 见 [WIKI-LOCAL-DB](docs/cases/WIKI-LOCAL-DB.md) |
| `build_stratagem_alias.py` | 用行内 `+24` 本地化键 → slug → HD2Runtime `uiIcon.nativeType` 建战备别名表（不依赖显示名），产出 `refs/stratagem-alias.json` | PyNaCl + HD2Runtime SDK zip | ✓ 38 条 / 0 歧义；冷却 34/35 一致 |
| `stratagem_display_names.py` | 从 `.strings` 资源解出每行的**游戏内文本**：五个槽位（`+40` 大写名 / `+44` 显示名 / `+48` 描述 / `+52` 长描述 / `+56` 状态标签），并附上匹配到的 wiki 页面标题 | PyNaCl + 由 srkit 解出的 strings 目录 | ✓ 显示名 145/153（135 直接 + 1 文本匹配 + 9 大写回退），wiki 页 115/145 |
| `table_locid_scan.py` | 扫一张表每个 4 字节槽，按 `(stride, offset)` **跨组聚合**，报告「本地化 ID 命中数 / 去重数 / 样本文本」。两种 `LDLD` 组头都认 | PyNaCl（无）+ `typelib.py` | ✓ 扫出 7 张表的名字槽（判据见 [LOCID-NAMES §1](docs/tables/LOCID-NAMES-25988413.md)） |
| `table_locid_names.py` | 按槽位表把本地化 ID 倒成文本，输出 JSON（`name` / `name_source` / 原始 ID），带「文本匹配 → 大写回退」 | PyNaCl（无）+ `typelib.py` | ✓ 六张表：弹丸 225/355、配件 234/252、护甲 389/422、被动 33/33、载具 11/12、星球 399/438 |
| `entity_locid_scan.py` | 解实体库（275 块 → `[哈希图][行数组][尾数组]`），定位本地化 ID 槽。实体名只有一处：`EncyclopediaEntryComponentData`（块 56） | PyNaCl（无）+ `typelib.py` | ✓ 643/1,939 实体有名字，205/211 条带代码条目精确命中 wiki 标题 |
| `entity_components.py` | 实体 → 组件清单（用每个组件块自己的哈希图反查，不用块 0 的 u16）；附带「谁引用了某值」的列扫描 | PyNaCl（无）+ `typelib.py` | ✓ 1,932 实体 / 272 种组件；用它查出 explosion 68 被 `Bombardment +64` 引用 |
| `ref_scan.py` | **引用反查 + 配件 delta 解码（只读）**：`exact` 扫全档 `u32 == VALUE` 并归因到（文件/块/行/槽/实体键）· `columns` 找「整列都是目标表 id」的引用面（不猜偏移）· `entity` 打单个实体全部组件行 · **`delta-info`/`delta-show`/`delta-ammo` 解 `ComponentEntityDeltaStorage` 三级索引**（配件 AddPath → 组件 → 成员偏移 → 字节），带本 build 组件索引表（[REFSCAN](docs/tools/REFSCAN.md)）| `entity_locid_scan.py`、`table_dictionary.py` | ✓ 用它破案：P-19 的 `Proj+0 = 296` 来自默认弹种 delta（[BACKPACK-DOGS §28](docs/tables/BACKPACK-DOGS-26088801.md)）；67 个弹种配件 → 各自弹丸 |
| `xcheck_projectile_names.py` | **弹丸 type id ↔ wiki 枚举名 + 批量数值交叉验证**：实体百科 `(code,name)` → wiki 页 → weapon 模块 `attacks[].name`；我们这边取默认弹种 delta / `Proj+0`；比 size/velocity/mass/penSlow 与伤害（[REFSCAN §6](docs/tools/REFSCAN.md)）| `entity_locid_scan.py` + 本地 wiki 镜像 `refs/wiki/wiki.sqlite` | ✓ 61 武器 join、弹道参数 61/61、49 个全字段一致（其余为 wiki 旧快照伤害）；`296→Pistol_9x20mm_fmj`、`342→P-2_P`、`281→Rifle_5.5x50mm_fmj` |
| `explosion_names_from_chain.py` | 爆炸行没有名字字段，改从引用链命名：投掷物 `+144/+156` → 爆炸 `+0`，输出每个爆炸行的消费方 | PyNaCl（无）+ `typelib.py` | ✓ 210 条边 / 0 悬空；103 个爆炸行有名字（97 唯一 + 6 共用） |
| `strings_inventory.py` | 清点 `.strings` 语料：语言分布（`ThinHash` 反查 15 种语言）、每个 bundle 的 distinct 英文 blob 数、ID 并集。**只读文件头 16 字节** | 标准库 | ✓ 证明英文语料是全局唯一那 18 个 blob |
| `table_dictionary.py` | **全表字典**：解封 55 张表 → 组/行数/步长/尾块 + 每个类型的字段偏移树（需自备 `recipient.sk`） | PyNaCl + `typelib.py` | ✓ 55/55 表解析（18 张几何完全闭合） |
| `build_diff.py` | 更新后逐表回答「改了什么」：文件层（size/sha256）→ 封装层（比**明文**哈希）→ 结构层。只读 | PyNaCl | ✓ 25988413→26088801：55 张表 0 变化，exe/dll 哈希变 |
| `build_geometry_diff.py` | 用旧 build 的字典几何对照当前 55 张表：多大/多组/多少行，哪张被动过一目了然 | PyNaCl | ✓ 同一次更新：identical 21 / structure-same 33 / changed 0 |
| `build_cache.py` | 把当前 build 的 55 张表 + 类型库解封成明文缓存，**按 buildid 另存**。更新后第一件事就是跑它 | PyNaCl | ✓ 26088801：56/56 解封 |
| `plaintext_cache_audit.py` | **查明文缓存有没有被我们自己的 mod 污染**：一次 dump 若发生在我们把负载写进 `data/game/` 之后，那份缓存里就混进了改过的表，之后所有「这张表变了没」的判断全错。两条独立判据（对部署前原版备份逐字节比 / 对锚点哈希）| 标准库 | ✓ 已实机（正是它抓出 2026-10-22 那次把自家 med-kit 实验负载误报成「唯一变化的表」） |
| `entities_modeb.py` | 实体表：武器单元格编辑、可选弹种（模式 A/B）、双弹药池、hashmap 维护 | `murmur64.py` | ✓✓ 已实机（主宰/惩罚者/扫荡者） |
| `proj_copy_row.py` | 整行搬运 272 B 射弹行（换弹头），带 5 道门禁 | `murmur64.py` | ✓✓ 已实机（Eruptor 弹头 → 主宰） |
| `pod_rack_swap.py` | 改 `HellpodRackComponentData` 槽位物品（投送舱换载荷），tail 宿主 + 9 道门禁 + 变异自检 | `murmur64.py`、`typelib.py` | ✓✓ 已实机（2026-10-23，六轮） |
| `rack_edit.py` | **投送舱 rack 任意槽位 + `+0x22C spawn` 一次写完**（`--slot N=item` 可重复、`--spawn N`）；补 `pod_rack_swap.py` 只能改 slot0/slot1 的空白；G1–G7 门禁 + 保 Murmur 锚点 | `murmur64.py`、`pod_rack_swap.py`、`typelib.py` | ✓ 离线（G1–G7 全过；用于 §18 的三件 rig，✓✓ 实机） |
| `mount_table.py` | **载具挂载 / 座位表**：`MountComponentData`（328 槽 + 165 × 120 B）与 `SeatCollectionComponentData`（112 槽 + 56 × 424 B）的读/查/换件；`swap` 只写 `MountInfo.item` 的 8 字节，tail 宿主保 Murmur64A，**10 道门禁**（含「全表只有目标槽变了」）；`show` 直接给出五件套 + 两条否决项的离线判据 | 标准库 + `murmur64.py`、`pod_rack_swap.py`、`typelib.py` | ✓ 离线（G1–G10 全过；sealed round-trip 逐字节相等；实机待验） |
| `pod_loadout.py` | **投送舱换载荷 + 有限数量的跨包加载的通用产出**：名字→包/LOE id→自动判单包/双包→出可装文件（不部署） | `pod_rack_swap.py`、`plain_edit.py`、`dlbin_seal.py` | ✓ 产物与实机验证件逐字节一致 |
| `strat_slot_census.py` | **战备表 153 行的装包口普查**：按 typelib 结构穷举（不是按值搜，空槽才看得见），分「两槽已满 / 仅 `+0xA8` 空 / 仅 `+0xF8` 空 / 两槽全空」四类并给出行基址 | `pod_loadout.py`、`typelib.py` | ✓ 离线：只有 `+0xA8` 命中包集合（114/114），空槽 155 个 |
| `strat_slot_fill.py` | **把包填进战备行的空槽**：名字→行（同名全改）→拒绝覆盖已占用槽→一次 tail 宿主写完→读回校验→可选封装 | `strat_slot_census.py`、`plain_edit.py`、`dlbin_seal.py` | ✓ 离线门禁通过（6 处填空槽，整份只 +8 B） |
| `entity_field_set.py` | **任意实体组件行任意字段**的通用写入（`--block`+`--key`+`--field`），tail 宿主 + 7 门禁，可链式 | `typelib.py`、`murmur64.py` | ✓✓ 已实机（AC-8 备弹 0→40/40）|
| `entity_batch_set.py` | **批量字段写入**：一次 tail 宿主写多个组件/多行/多字段（文件只 +12 B），9 道门禁 | `entity_field_set.py`、`pod_rack_swap.py` | ✓ 产物与实机验证件逐字节一致 |
| `state_machine_edit.py` | **`state_machine` 资源（不是表）的读/改**：`--show` 列层/状态/默认态，`--decode` 解出事件表、每条过渡、以及 `EmitEndEvent → 部署完成态`，`--names` 用 hashlist 反查事件名，`--set 层=索引` 写 `layer.DefaultState`；改完走 `resource_patch.py` 打成补丁 | 标准库 | ✓✓ 已实机（AC-8 哨戒挂载不展开：`0x74: 3→2` 后出场即展开，触点/开火点全对；`--set 0=2` 复现的载荷与 patch_7 逐字节相同）|
| `unit_offset.py` | **改 `unit`（壳）里某个节点的位移 → `.patch_N`**：`show` 列 64 个节点的名字/位置/父子（找"内容容器"节点），`shift --node N --dz 2.0` 做**等长二进制改写**（transform 段在 srkit 里是只读视图、编码时原样拷贝，所以不重编不碰 gpu），G1–G5 门禁 + `--install` | `srkit`、`resource_patch.py` | ✓ 离线（火箭壳节点 3 +2.0 m：只变 2 字节；`srkit extract --decoded` 复核节点 3=[0,0,2.0]）；⚠ 实机待验 |
| `animation_probe.py` | **`animation`（动画 clip）解码**（`srkit` 只有 raw fallback）：按 filediver 格式读头 + 条目流，输出**长度**与**每个骨骼有没有关键帧**（`--matrix` 出 clip×骨骼总表、`--bones` 把索引映射成骨骼名）；用于判断"某状态绑的 clip 是不是全身姿态" | 标准库 | ✓ 离线（AC-8 展开态 14/16 骨有键含 `elevator`；火箭展开态 0 骨 = 空 clip）|
| `turret_shell_survey.py` | **普查"哪些炮塔壳像 AC-8 一样自带姿态"**：取 `Turret`+`Wieldable`+`WeaponWielder`+`Unit`+`WeaponData` 的实体 → 读 `Unit +0` 得壳 → 找同 id 的 `state_machine` → 解展开态 clip → 用 `animation_probe` 数**它打到了几根骨骼**； 分 A（≥60% 且升降被打到）/B/C/C0/E（模板 B）/D（无部署机构）；`--json` 出机器可读 | `srkit`、`entity_field_set.row_of`、`typelib`、`animation_probe`、`state_machine_edit` | ✓ 离线：34 个壳里 A 类只有 AC-8（14/16）；火箭 0/10、火焰 1/10、激光 0/6 |
| `boot_manifest.py` | **枚举"必然常驻"的包**：读 `data/settings.ini` 的 `pre_boot/boot/fallback_resource` 三个包设置 → `murmur64(路径)` 得包 id → 抽 `.package` 清单（`u32 ver|u32 unk|u64 count|count×(u64 type,u64 id)`）→ 类型直方图；`--package <id>` 可看任意包组成 | `srkit` | ✓ 离线：`packages/boot` = **`9ba626afa44a3aa3`**（4,052 条，就是补丁挂的那个包）；pre_boot 2 条、fallback 25 条 |
| `armor_kit_weight.py` | **护甲三数字的唯一文件侧入口**：改某件甲 9 个部件的档位（`+16`），rating/speed/stamina 一起变；`--show` 列 135 件甲；8 道门禁 | `plain_edit.py`、`murmur64.py` | ✓ 离线（135/135 与 SDK 逐件对上），⚠ 上机待读 |
| `passive_bonus_edit.py` | **护甲被动表编辑**：给某个 perk 加 pm/sm 行（含**中间块变长后的整容器重排**），尾部校正字保内容哈希；`--show` 打全表 | `murmur64.py` | ✓✓ 已实机（Acclimated 抗性 0.5→0.0 ⇒ 火/毒不掉血；ergonomics +30 待读） |
| `entity_hashmap_insert.py` | **给实体新增一种组件**：往组件哈希图里插一条 `(键 → 行)`，可整行复制孤儿行；哈希图是 `键 % 槽数` 线性探测（§ENTITY-LOCID 10），8 道门禁 | `pod_loadout.py`、`murmur64.py` | ✓ 离线门禁全过；**但「新增组件」这条用法已实机否证**（GL-28 插弹匣行不被采纳，删联动键后崩溃）—— 只用于读写已存在组件 |
| `dlbin_merge.py` | **mod 合并器**：多个保哈希 mod 取并集、剔除脚手架、判冲突、重解一个校正字；含 `--report-only` / `--on-conflict` | `murmur64.py` | ✓✓ 已实机（第一次上机：rack 三件 rig × GL-28 弹药行 → 合并后四件照常全出） |
| `expl_set.py` | 写爆炸行字段（半径 / 破片数 `+80` / 破片射弹 `+84`），带 6 道门禁 | `murmur64.py` | ✓✓ 已实机（毒气爆炸加 30 破片） |
| **`stratagem_extra.py`** | 战备表**额外战备** `+0xC8`：`--show` 全表 153 行 / `--find` 按名找 id / 写入（tail 宿主保哈希）+ **G7 环检测** + `--seal` | `murmur64.py`、`dlbin_seal.py` | ✓ 离线（G1–G7 全 PASS；未发布目标待实机） |
| **`expl_orphans.py`** | **爆炸表孤儿普查**：重算 memmod 时代判据（无射弹行 `+0x90`/`+0x9C` 指向它）→ 424 行里 265 条无主 / 98 条伤害行独占；`--list` 全表、`--type N` 单行、`--json` 机器可读 | 标准库 | ✓ 离线（`refs/explosion-names-chain.json` 交叉验证 0 冲突） |
| `stratagem_tune.py` | 改战备表的 `+80` uses / `+84` call-in / `+104` cooldown；`--edit` 可重复，一次封装改多行。**默认 tail 宿主**保内容哈希；`--host-mode row` 已知会崩，永不传 | 标准库（`murmur64.py` + `typelib.py`） | ✓✓ 已实机：EAGLE. AIRSTRIKE `+104` 15→4 + EAGLE. REARM 150→5，整份只差 5 字节、哈希仍复原，面板 7→2 秒 / 任务内回收 150→3 秒多（`26088801`） |
| `patch_compose.py` | 数据路线 mod 的离线合成器：`scan` 查各包槽位与空洞、`merge` 求并集（同 id 不同内容=冲突，默认拒绝）+ 逐条回读验证、`install` 只写下一个连续槽位 | 标准库 + `srkit.container` | ✓ 实测把 bones/material/texture/lua 共 7 条合进一个补丁，toc 与 gpu 附流逐条一致 |
| `dmg_edit.py` / `dmg_custom_row.py` / `dmg_refs.py` | 伤害行编辑 / 自制伤害行 / 跨表引用查询 | `murmur64.py` | ✓ 离线门禁通过 |
| **`lua_payload_dump.py`** | **第三方 patch_0 的 lua 载荷抽取**：`srkit list/extract` + **LuaJIT 字节码壳解码**（`loadstring("LJ…")` → `.luac` + 字符串常量 + 关键词高亮） | `python -m srkit`（HD2SDK 检出） | ✓ 三个真实 mod 实测通过 |
| **`dmg_row_edit.py`** | **伤害行任意字段编辑**：`damage/durable/ap[4]/demo/force/impulse/element` + **4 个状态槽**（`--slot N:TYPE:VALUE`），7 道门禁 + `--seal` | `murmur64.py` `dmg_edit.py` `dlbin_seal.py` | ✓ 离线门禁通过（G1–G7 全 PASS，实机待验） |
| `name_rows.py` | 用跨 build 指纹给爆炸/射弹行恢复名字 | 标准库 | ✓ |

### 3.2 补丁 / 资源

| 工具 | 用途 | 依赖 | 验证 |
|---|---|---|---|
| `resource_patch.py` | **任意** Stingray 资源类型的 `.patch_N` 构建/查看/解包/重打 | `srkit`（构建时） | ✓ |
| `resdep.py` | **资源依赖自动追踪 + 驻留计划**：`index` 建全档 `资源 id → 宿主包` 索引（322,810 行 / 62,915 id，约 20 s）· `chain` 从武器/实体/爆炸走引用链并**全 u64 扫描**（不猜字段）· `plan` 按目标件声明包分「同包/跨包/缺失」并出 `whole_package_patch` 命令 · `sound-catalog`/`sound` 解 wwise **HIRC** 建事件目录（实测 **9,627 事件 / 420 bank**；⚠ 但表里哪个字段放事件 id 仍未定位，爆炸行 0/424 命中）。G1–G5，**缺失资源默认拒绝出计划**；`--apply` 一键装盘 + 失败整体回滚 + 自动生成 **VERIFY.md 实机验证清单** | `srkit`（`python -m srkit`） | ✓ 爆炸 213 → 粒子+震屏 9 包 0 缺失；MG-43 → 同包 7 / 跨包 11（5 包）/ 0 缺失；全量声音目录 9,627 事件 |
| `whole_package_patch.py` | **整包资源 → `<宿主包>.patch_N`**（资源层驻留）：`list` 列包内资源；`build` 解包→`--edit` 换资源（自动同步 `resource.json` 的 size/sha）→打包→复核；`check` 核对成品。G1–G8 门禁；序号默认自动取下一个连续值；`--install` 可选部署 | `srkit`（`python -m srkit`）+ `resource_patch.py` | ✓ 复现证明：重跑 P4 补丁，三件产物与盘上**逐字节相同**（toc `a3f71af78d333f02`）|
| `swap_texture.py` | 把一张 PNG 换进 `.patch_N` 里的某个贴图并重打 | Pillow | ✓ 已实机 |
| `export_textures.py` | 把 `.patch_N` 里每个贴图导出成可编辑 DDS | Pillow | ✓ |

### 3.3 Lua 侧

| 工具 | 用途 | 依赖 | 验证 |
|---|---|---|---|
| `lua51_check.py` | 用**真** Lua 5.1 解析/消毒载荷，避免方言错误烧一次启动 | lupa | ✓ 自检 |
| `luac51_disasm.py` | 反汇编标准 Lua 5.1 字节码块 | 标准库 | ✓ 自检（6 项） |
| `check_unit_snapshot.py` | 静态查「遍历 `World.units()` 快照还调 Unit getter」的崩溃写法 | 标准库 | ✓ 自检 |
| `hud_layout_check.py` | 离线算 HUD 绘制坐标（假引擎跑真 lua） | lupa | ✓ |
| `lensmask_to_reticle.py` | 「亮镜片 + 暗准心」贴图 → 自发光准心遮罩 | Pillow | ✓ |
| `grab_logs.py` | 在下次启动覆盖前把游戏日志归档 | 标准库 | ✓ |

### 3.4 反作弊 / 能力边界（**全部是否证记录，不是方法**）

这几个是「试着做 → 失败 → 把失败量出来」的工具，**没有一个成功过**，最硬的证据来自它们自己的自检：
`eac_access_test.py --selftest` 会**故意造一只被剥权的句柄**（`0x0400`，正是 EAC 还给你那种形状），要求「读一个字节必须被拒绝」，5/5 PASS。
发布它们是因为「我们试过并且失败了」比沉默有用 —— [MEMORY-ACCESS §2–§8](docs/boundaries/MEMORY-ACCESS-25988413.md) 就是这些工具的输出。

| 工具 | 它回答的问题 / 实测结果 | 依赖 | 验证 |
|---|---|---|---|
| `eac_access_test.py` | 外部进程还能读游戏吗？→ **不能**：`OpenProcess` 三档全给句柄、元数据能读，但 `ReadProcessMemory` **err=5**、`MiniDumpWriteDump` **0x80070005**。文件头留着第一版**假阳性**的教训 | 标准库 | ✓ `--selftest` **5/5**（含「剥权句柄必须被拒」的变异测试） |
| `eac_early_handle.py` | 有没有「保护生效前」的窗口？→ **没有**：进程出现后 **10.6 ms** 建的句柄**已经被剥权**（err=5），access mask 在创建时就定了 | 标准库 | ✓ `--help`；完整流程需要一次游戏启动 |
| `crash_watch.py` | 在 CRS 删掉之前抢救游戏**自己**的崩溃捕获。外部全量 dump 那条路已死 | `eac_access_test.py`（缺席时降级为「跳过预检」） | ✓ `--selftest`（造假 CRS 捕获 → 救援 → hash 校验 PASS） |
| `watched_modules.py` | 从**外部**盯一个进程的**映射文件列表**（`VirtualQueryEx` + `GetMappedFileNameW`，只读元数据、不读内容），回答「某个 DLL 到底有没有被映射进来」 | 标准库 | ✓ 实机（2026-10-22：正常态插件在第一个样本就出现 / 换供体后 23 个样本里从未出现） |
| `make_loadlib_fixtures.py` | 造 DLL 夹具，用**错误码判别**回答「游戏 Lua 能不能加载我们自己放上去的 DLL」：126 = 模块不存在 / 127 = 模块被映射但符号不在 / 577·193 = 加载器策略拒绝。只有 127 才证明 `LoadLibraryA` 真的跑过 | 标准库 | ✓✓ 已实机（两轮 5 夹具 / 7 用例；结论与两道闸门见 [MEMORY-ACCESS §12g](docs/boundaries/MEMORY-ACCESS-25988413.md)） |

### 3.5 文档提到、但本仓库**故意不含**的工具

写清楚是为了让人别照着文档找不存在的文件：

| 文档里出现 | 为什么不在 |
|---|---|
| `memscan.py` | 旧路线（LuaJIT + `ffi`）的扫描器，**弃用**：25988413 的 VM 没有 `ffi`，跑不起来；3,000+ 行里全是旧 build 的偏移知识 |
| `verify_patch_series.py` | 依赖 `patch_series_prune.py` → `hd2_archive`（不在本仓库） |
| `build_snapshot.py` | 需要本机的普查表 / 探针 / 文档作为输入，不是通用输入 |
| `package_p2p_ping.py` | 属于另一个项目（`hd2-p2p-ping`），与本仓库无关 |
| `passive_example.py` | **不是我们的工具**：[DLBIN-SEALED-BOX](docs/engine/DLBIN-SEALED-BOX.md) 引用的是某个第三方 modkit 里的文件，只作「别人怎么解这个字」的对照 |
| `extract_seal_material.py` | **已删除（2026-10-23）**：借第三方 mod 固定 ephemeral 的方案被 `max_len` 卡在 65,504 B，且产出即密钥材料 |
| `dlbin_deploy.py` / `ent_set.py` | 部署与实体写入器，**未随仓库发布**；最小等价物见 [WORKFLOW §7 / §9](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) |

> 注：少数工具相对私有工作区只改了两处——默认输出路径改成**相对路径**、个人 SDK 路径改成 `HD2SDK` 环境变量。逻辑未改。

## 4. 无密钥也能练

不需要游戏、不需要密钥就能跑通「解析 → 改字节 → 过门禁 → 核哈希」这几件事：

| 资产 | 内容 |
|---|---|
| [`tables/`](tables) | 四张很小的明文参数表（projectile 96,604 B / damage 50,336 B / weapon_customization 30,824 B / **stratagem 82,384 B**，合计 ~260 KB） |
| [`refs/table-geometry.json`](refs/table-geometry.json) | 55 张表的 stride / 行数 |
| [`refs/exports/`](refs/exports) | 战备 / 爆炸 / 弹丸等表的逐行 CSV（组 / 行 / 内部名 / 偏移值） |
| [`refs/dl-type-names.txt`](refs/dl-type-names.txt) | 类型哈希 → 名字 |
| [`refs/entity-block-types.json`](refs/entity-block-types.json) | 275 个组件块类型名 |

配方：[WORKFLOW §2.6](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) —— 用 `plain_edit.py` 真跑出完整 G1–G6（锚点 `946A4FE5FAAAE076`）。

当前 build 的可跑示例：[`examples/stratagem_extra_demo.py`](examples/stratagem_extra_demo.py)（战备表 `+0xC8` 额外战备，`--verify` 自带自检；写入用 [`tools/stratagem_extra.py`](tools/stratagem_extra.py)）。

## 5. 能力明细

| 能力 | 状态 |
|---|---|
| 解开 `data/game/*.dl_bin`（`crypto_box_seal` 形态）并还原明文 | ✓ 工具可跑（需自备密钥，见 [DLBIN-SEALED-BOX §10](docs/engine/DLBIN-SEALED-BOX.md)） |
| 还原**内容哈希闸门**（MurmurHash64A + 校正字），改完字节仍过校验 | ✓ 已实机 |
| `generated_entities`：组件块布局 / hashmap / 行结构 | ✓ 已实机 |
| 武器数值：人机、站姿惩罚、散布、后坐、装填可移动 | ✓ 已实机 |
| **可选弹种**：`fnid=8` + 备选弹丸（伤害 + 状态切换） | ✓ 已实机（眩晕 / 燃烧） |
| **独立弹药池**：`fnid=4` + `WeaponRounds` 两套弹丸 | ✓✓ 已实机（仅限原生有该行的 25 把） |
| **爆炸/弹头**：换弹头整行 · 换爆炸（`+144`/`+156`）· 加破片（`+80`/`+84`） | ✓✓ 已实机 |
| **爆炸视觉 + 跨包加载**：整行克隆供体爆炸 · `+0xA8` 任意外观可移植 | ✓✓ 已实机（`26088801`） |
| 战备：呼叫 / 冷却 / 散布 / 使用次数 / 弹幕轮数与每轮弹数 / **Eagle 回收时间与两套升级公式** | ✓✓ 已实机（`26088801`） |
| 全表字典：55 张表几何 + 1,208 类型字段偏移 | ✓ 离线可复现 |
| **改现有伤害行的数值**（标准 / 耐久 / 穿甲 / 状态强度） | ✓✓ 实机（`26088801`：`116 +4` 改成 1 → 面板「伤害」直接显示 **001**，AR-23 / AR-23A / StA-52 / M-105 同时变；`25988413`：90→900 → AR-23 与 M-105 同时变高伤）—— 见 [DAMAGE-SETTINGS](docs/tables/DAMAGE-SETTINGS-26088801.md) |
| **复用无主行「自制」一条伤害行**（整行改写 + 借另一条无主行付哈希） | ✓ 离线门禁通过（`dmg_custom_row.py`）；**⚠ 未实机** |
| **投送舱换载荷**：改 rack 槽位决定空投舱送什么 | **✓✓ 实机**（`26088801`：rack 29 → GL-21+B-1 / GL-28 双件 / Nova+Warp 双件；**四件版 Nova+Warp+GL-28+GL-28 背包（`+556`=4）四件全出**）—— 见 [POD-RACK](docs/tables/POD-RACK-26088801.md) |
| **武器自带备弹**：把背包供弹武器改成自带备弹、不需要背包 | **✓✓ 实机**（两套模型：`Rounds` 用 `+0x50/+0x54/+0x58`（AC-8），`Magazine` 用 `+0x88/+0x8C/+0x94`（GR-8 / Spear / RL-77 / W.A.S.P. 四把一次全绿）；rack `+556` 2→1 → 只出武器）—— 见 [WEAPON-AMMO-RESERVE](docs/tables/WEAPON-AMMO-RESERVE-26088801.md) |
| **背包供弹武器（第四种模型）怎么办** | ✓✓ **连背包一起投送**（GL-28 + 它的背包同包，`+556`=4 四件全出、能开火）；**改弹药模型/插新组件都走不通**：插弹匣行不被采纳、删联动弹药键直接崩溃（与「给 AR-23 强塞双弹池」同类）—— 见 [WEAPON-AMMO-RESERVE §4b](docs/tables/WEAPON-AMMO-RESERVE-26088801.md) |
| **跨包加载**：`+0xA8`（物品包）+ `+0xF8`（武器的 LoadoutEntry）双声明口；口不够时接 `+0xC8` 额外战备链（不占位）；**或走补丁把资源/整包塞进常驻包（不受口上限）** | **✓✓ 实机**（只换 `+0xA8` → 谁出模型跟着换；`+0xC8` 链带进 4 条战备；补丁：79 KB 顶掉 68 MB 包、整包 50/51 条进**共享基础包**与注册表包、舱里三件零声明全出；挂载件整包 41 条零声明 ⚠ 待实机）—— 声明口见 [LIMITED-CROSS-PACKAGE-LOADING](docs/engine/LIMITED-CROSS-PACKAGE-LOADING-26088801.md)，补丁见 [RESOURCE-RESIDENCY](docs/engine/RESOURCE-RESIDENCY-26088801.md) |
| **空声明槽普查**：153 行战备里 **133 行没填满**，空槽存量 **155 个**（两槽全空 22 行 / 仅 `+0xA8` 空 17 行 / 仅 `+0xF8` 空 94 行）⇒ `strat_slot_fill.py` 按名字填空槽 | **✓✓ 实机**（R3：把 Warp 的包填进 `Reinforce` 的 `+0xA8` ⇒ **关卡加载即驻留**，不叫、不带、不死；投送舱里两件不同包的物品同时正常，**三个包并存**）。`+0xF8` 另有否证（R1：不授予武器的战备上不读它）—— 见 [LIMITED-CROSS-PACKAGE-LOADING](docs/engine/LIMITED-CROSS-PACKAGE-LOADING-26088801.md) §6.6 |
| 解锁未发布物品（`LoadoutEntry.selectable`） | ✗ 已否证（发布数据里没有这个开关） |

## 6. 已验证的核心结论

> 这些**在 `25988413` 上做的实机 / 离线验证**；结构层部分（密封盒、闸门算法、块布局、行命名、本地化 ID）在 `26088801` 上已复验仍成立。
> **每个具体偏移都必须按 [BUILDS.md §3](BUILDS.md) 在你自己的 build 上重验一遍。**

1. **闸门**：`data/game/*.dl_bin` 的明文被 `game.dll` 里烘焙的 MurmurHash64A 校验（seed `0xDEADBEEFABAD1DEA`），不匹配就 `0xC000000D`。**解法**：改完字节后在一个语义惰性的 8 字节对齐字里解出「校正字」，让哈希回到原值 —— 长度不变、校验通过。
2. **实体库不是 toc，是块序列**：`u32 type ｜ LDLD ｜ ver ｜ type ｜ payload ｜ …`（28 B 头）；组件块 payload = `[hashmap][行数组]`；hashmap 键 = `Murmur64A(资源路径)`。
3. **可选弹种两格**：`WeaponData +184`（`function_id`，**8 = 原生 ProgrammableAmmo**）＋ `ProjectileWeapon +576`（**备选弹丸 type id**）。备选弹**只贡献伤害 + 状态**，弹道来自主弹行。
4. **独立弹药池**：`WeaponRoundsComponentData`，行内 `+64` 两个弹丸 id / `+72` 两个弹匣容量 / `+80` 两个备弹。全表 25 把里只有 SG-20 Halt 是 B≠A，也正好只有它是 `fnid=4`。正向配方与边界见 [ENTITY-TABLE §9](docs/tables/ENTITY-TABLE-25988413.md)。
5. **未发布物品**：`LoadoutEntryComponentData` 只有 `{id, type, dlc_pack_id, equipment_tags[5]}` 32 字节，**没有 selectable**；带 selectable 的结构在发布数据里 0 命中 ⇒ 不是离线可翻的开关。
6. **战备面板的两套升级公式**（`26088801` 实测，判决点设计见 [STRATAGEM-FIELDS §5.4.4](docs/tables/STRATAGEM-FIELDS-26088801.md)）：
   - 冷却 `= round(+0x68 × 0.5 × 0.95)`（Eagle 额外吃 Liquid-Ventilated Cockpit；全体吃 Morale Augmentation）
   - Eagle 回收 `= EAGLE. REARM +0x68 × 0.8 × 0.9 × 0.95 = ×0.684`
   - 方法要点：**选一个让两种假设给出不同整数的基值**（80 → 38/40；100 → 80/72/68），比多测几个小值有效得多。
7. **投送舱载荷**（`26088801` 实测，见 [POD-RACK](docs/tables/POD-RACK-26088801.md)）：舱里送什么 = `HellpodRackComponentData` 某条 rack 的**前 `spawn_payload_size` 个槽**的 `Item`（u64 物品实体键）；
   物品的**网格/材质**由战备行的两个声明口决定 —— `+0xA8`（物品的 toc 包）+ `+0xF8`（授予武器的 `LoadoutEntry` id，其包为第二槽）。
   引擎同时还会加载**原版物品自己的包**，这就是原版 Apex 舱能用两个包的原因。改数据即可，重启不还原。

## 7. 三态标记与自检

| 标记 | 含义 |
|---|---|
| `✓ 实机` | 进游戏看过，且「账本 + 盘上回读 + 进程状态」三件套齐全 |
| `✓ 离线` | 只读解析 / 离线复跑，不启动游戏 |
| `✗ 否证` | 试过、不通，写清失败形态 |
| `⚠ 未证` | 有推理或部分证据，没上机 / 没分辨 —— **不许**当结论用 |

- **改完文档**：`python tools/check_links.py`（0 断链才算过；`../` 层数写错会逃出仓库根，检查器**静默跳过**）。
- **加新文档**：在 §2 对应目录表里加一行；若它回答了某个「我想…」，同时在 §1 加一行。
- **换 build**：更新本文顶部的「当前验证 build」，并按 [BUILDS.md §3](BUILDS.md) 复验锚点（§3.1）。
