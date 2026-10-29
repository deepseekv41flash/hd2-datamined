# 改盘上数据的 mod：从「想改一个数值」到「实机确认」的完整工作流（build `26088801`）

> **build `26088801` 实测**（2026-10-23）｜路线：**改数据文件**（不碰进程内存、不需要 Lua/FFI/注入/DLL）。
>
> **2026-10-29 复验（build `26251122`）**：密钥、类型库、实体库与本文结构层结论**全部不变**；
> 55 张表只有 4 张变化（APEX 口径/拆除、战备名字表、删两条音乐）—— 见 [BUILD-26251122-DIFF](../builds/BUILD-26251122-DIFF.md)。
> 文内凡写 `26088801` 处均为**当时实测记录**；偏移与锚点判据请以本 build 的明文与锚点为准。
> 状态：**✓✓ 端到端全链路**（Eagle 双行：面板 7→2 秒、任务内回收 150→3 秒多）；工具层为 2026-10-23 的只读审计，未改任何源码。
> **一句话**：一条能复现的改表链 = 取明文 → 定位字段 → 尾宿主保哈希写入 → 过七道门禁 → 重封 → 往返 → 备份安装 → 盘上回读 → 分级实机验证；**少一次读数，就只能记 `⚠`，不能记 `✓`**。
> 相关：[DLBIN-SEALED-BOX.md](../engine/DLBIN-SEALED-BOX.md)（密封盒 / 哈希 / 校正字原语）· [STRATAGEM-FIELDS-26088801.md](../tables/STRATAGEM-FIELDS-26088801.md)（战备字段图与面板公式）· [ENTITY-TABLE-25988413.md](../tables/ENTITY-TABLE-25988413.md)（实体库 275 块）· [BUILDS.md](../../BUILDS.md)（换 build 先跑哪三步）· [SKILL.md](../../skills/hd2-file-route-mod/SKILL.md)（可执行形态）

---

## 0. 验证状态（先看这张，别把未验证当结论）

三态口径：`✓ 实机` = 进游戏看过，且**账本 `installed_from` + 盘上回读值 + 进程状态**三项齐全；`✓ 离线` = 只读解析 / 离线复跑，不启动游戏（比实机弱一档）；`✗ 否证` = 试过、不通，写清失败形态；`⚠ 未证` = 有推理或部分证据，没上机 / 没分辨。**没有第五种。**

| 结论 | 状态 | 证据 |
|---|---|---|
| `.dl_bin` 明文 = 密文 − 48 B；封包 = 明文 + 48 B | **✓ 实机** | 55 张表 + 类型库解封；四份部署备份 47,259,444 / 96,652 / 68,204 / 82,432 B 均 = 明文 + 48 |
| 引擎内容哈希 = `MurmurHash64A(明文)`，seed `0xDEADBEEFABAD1DEA` | **✓ 实机** | 改内容不改哈希 → `0xC000000D`；保哈希后正常进游戏 |
| 校正字可代数反解，尾部 8 B 宿主可保哈希 | **✓ 实机** | 战备表 / 实体表；Eagle +8 B、只有 5 字节差异、哈希仍 `04BBE33EF809862A` |
| 校正字落进记录行首 → 崩 | **✓ 实机（崩溃）** | 3 次同签名 `0xc0000005 @ game.dll+0x1083a45`，寿命 26–29 秒 |
| 一次封装同时改 Eagle 两行 | **✓ 实机** | 面板 7→2 秒；任务内回收 150→3 秒多；账本 + 回读 + 进程正常（§11） |
| 路线级门禁 G1..G7 | **✓ 实机 / ✓ 离线** | Eagle 输出 7 PASS；工具审计另离线复现若干缺陷（§10.2） |
| 自动备份 / `install` / `restore` 账本 | **⚠ 工具未随仓库发布** | 私有 `dlbin_deploy.py`；账本 4 个受管文件（§9.4），部署三步是它的最小等价物（§7.3） |
| `dlbin_deploy.py` 会校验补丁内容 | **⚠ 未证（风险）** | 它只比 sha256；装错文件会崩在引擎里（§7.6） |
| Eagle 面板「冷却」公式 | **⚠ 未证** | 15→7、4→2 两点符合 `floor(base/2)`，不符合已验证的 `×0.90×0.95`（§8.1） |
| Eagle 回收时间的升级系数 | **✓ 实机** | 基值 100 → 回收 **68 秒** ⇒ ×0.8×0.9×0.95 = **×0.684**（§11.10） |
| Eagle 面板冷却公式 | **✓ 实机** | 基值 80 → 面板 **38 秒**，排除 `floor(base/2)`；真因子 ×0.5×0.95（§11.10） |
| `+0x60` 语义 | **⚠ 未证** | `EAGLE. REARM` = 15.0，`EAGLE. AIRSTRIKE` = 0.0；没做过改动实验 |
| 20 张零空位表用 tail 宿主 | **⚠ 未证** | 只在战备表 / 实体表实机；其余逐表未验（§9.5 / §10.3） |
| `damage_settings` 改伤害 | **✓ 实机** | 面板「伤害」直接跟着变（改成 1 → **001**）。`DamageInfo` 76 B / 8 成员**行内**零 padding，但宿主可以放**文件尾**（tail +8）或借别的无主行 → [DAMAGE-SETTINGS §5](../tables/DAMAGE-SETTINGS-26088801.md#5-宿主策略)。**零 padding 是「行内」事实，不是「文件内」事实** |
| 加行新增可见战备 / 解锁未发布物品 | **✗ 否证**（军械库）；**战备例外 ✓ 实机** | 加行进不了军械库；但**未发布战备**可用 `+0xC8`「额外战备」直接带进任务（7 条实机，见 [UNRELEASED-STRATAGEMS](../tables/UNRELEASED-STRATAGEMS-26088801.md)）|
| 给武器新增独立弹种行 | **✗ 否证** | 四个变体全 `0xC000000D`；只能改现有行（§10.3） |
| 用 `.patch_N` 覆盖 `data/game/*.dl_bin` | **✗ 否证** | 不在 `bundle_database.data`，引擎按路径直读加密松文件（§10.3） |

---

## 1. 适用范围与前置条件

### 1.1 这条路线改的是哪一层

| 层 | 内容 | 载体 | 本路线 |
|---|---|---|---|
| 层 2 · 定义 | 这条**叫什么、什么数值** | `generated_*_settings.dl_bin`（战备 / 爆炸 / 弹丸 / 实体…） | ✓ 可改，本文全篇 |
| 层 1 · 成员资格 | 面板上**有哪几条** | **不在 55 张明文表里**（后端目录 / 组件挂接） | ✗ 改不到；加行也不显示 |
| 字符串 | 任意自定义文本 | `.strings` 语料（bundle 资源） | ✗ 需另一条路线 |
| 表内引用 | 让 A 指向 B（爆炸 type / 包 id / 实体哈希数组） | 表内字段 | ✓ 可改，但目标必须已存在 |
| 资源内容 | 模型 / 贴图 / 粒子本体 | 资源包 | ✗ **本路线**改不了；但有**补丁路线**（`.patch_N` 把资源塞进常驻包，✓✓ 实机，见 [资源层驻留](../engine/RESOURCE-RESIDENCY-26088801.md)） |
| 进程内存 / 原生代码 | 运行时数值、DLL | — | ✗ 已全部否证（§10.4） |

**一句话**：这条路能改「定义」和「表内引用」，改不了「谁能出现」「文本从哪来」「资源长什么样」。想把未发布物品变出来、想写全新描述，都不在这条路上。

> ⚠ **2026-10-25 晚补充**：「资源长什么样」这一格现在有解了，但**不在这条路线上** —— `data/<包名>.patch_N` 可以**新增/替换资源**（含整包搬迁），粒子 79 KB 顶掉 68 MB 包、整包 50/51 条搬进共享基础包与注册表包都 ✓✓ 实机。详见 [资源层驻留](../engine/RESOURCE-RESIDENCY-26088801.md)。


> ⚠ **2026-10-25 修正（重要）**：**战备**这一族有例外 —— 未发布战备可以用 `+0xC8`「额外战备」在**任务里**拿到（7 条实机：M-104 FRV / 额外扫射 / A2A 导弹 / 烟幕行走弹幕 / 纸屑 / 飞鹰掠过 / 照明弹，见 [UNRELEASED-STRATAGEMS](../tables/UNRELEASED-STRATAGEMS-26088801.md)）。**军械库仍然不显示**（那条边界的原意没变）；武器/护甲等其它族也仍然不行。

### 1.2 三个硬前置

| 前置 | 判据 | 不满足时 |
|---|---|---|
| **build 对得上** | 明文哈希等于 §2.3 的锚点；`build_cache.py` 的 `_index.json` 里 `buildid` 是 `26088801` | 停。偏移全部作废，先跑 [BUILDS.md](../../BUILDS.md) §3 的三步，再重跑全表字典 |
| **自备密钥材料** | 解封要 `recipient.sk`；重封要 `recipient.pk` | 只能读、不能封。**本仓库不提供任何密钥**；`pairs` 产出的 `streams/*.xor` 与 `report.json` 里的 epk/tag 属等价密钥材料，绝不入仓 |
| **干净基线 + 已备份 + 游戏已关** | `data/game` 是原版；每张要动的表都有 sha256 备份；游戏进程不在 | 缓存会被自己的 mod 污染（§2.4）；运行中替换可能读到半份文件；没备份不能回滚 |

其他环境要求：Python 3.11+；只有 `dlbin_seal.py` 的 key 子命令要 **PyNaCl**；实体表约 47 MB，备份与明文缓存要留出 ~100 MB；Windows 路径含空格，命令里全部加引号；本文的命令行是 **bash**（Git Bash / WSL），PowerShell 等价见 §7.8。

### 1.2.1 取密钥：本仓库不能 bootstrap（先把这一条读掉）

| 事实 | 说明 |
|---|---|
| 必须是**游戏内置的那一对** | 引擎用它自己的 `recipient.sk` 解封。自己用 `nacl` 生成一对能让本文所有命令跑通，**产物游戏解不开**（`seal-key` 成功、进游戏失败） |
| 有 sk 就能算出 pk | `python -c "from nacl.public import PrivateKey;print(PrivateKey(open('recipient.sk','rb').read()).public_key.encode().hex())"` —— 不必两个文件都齐 |
| 本仓库不提供、也不该提供 | 密钥 = 能伪造「通过内容校验」的数据文件的能力 |

两条已知来源与各自的代价：

| 来源 | 前置 | 代价 / 边界 |
|---|---|---|
| 旧 build 全量内存转储 + **本仓库给出的 RVA 与 XOR 常数** | 一份 10 GB 级 dump（build `25480438`） | **唯一需要的外部实物就是这份 dump**：模块 `helldivers2.exe`、公钥 RVA `0x16532B0`、私钥 RVA `0x1653160`、四段 qword 各 XOR `0xEB63463F0C116E2C`、seek 工具 `tools/dump_read_rva.py`、以及三重验证判据，**全部在 [DLBIN-SEALED-BOX §10](../engine/DLBIN-SEALED-BOX.md) 里**。dump 本身不入库（体积 + 含密钥） |
| `tools/dlbin_keyhunt.py` | 无 | 研究工具，仓库里**没有成功记录**，别当可行路径 |

> 曾经还有第三条：借第三方 mod 里烘焙的固定 ephemeral 密封材料。**已弃用（2026-10-23）**——
> 它被 `max_len` 卡死在 **65,504 B**，我们的目标表全都超限（战备表 82,392 B、护甲 453,204 B）；
> 且须先持有那份 mod。相关提取工具与文档里的材料数值已一并移除
> （理由见 [DLBIN-SEALED-BOX §7](../engine/DLBIN-SEALED-BOX.md)）。

**结论（说清楚边界，别让人误以为无解）**：

- **能自己解**：只要有一份 build `25480438` 的全量转储，RVA、XOR 常数、seek 工具与三重验证判据**都在本仓库**，
  照 §10 走一遍就能在本机重新得到那一对 —— 这正是本仓库不放密钥副本的原因（可复现，没必要存）。
- **不能凭空解**：没有那份 dump，也没有别人给的一对，就**无法从零 bootstrap**；此时只能读
  （解封之外的解析、定位、预演，见 §2.6），不能封、不能部署。这是前置条件，不是可以扫过去的障碍。
- ⚠ **只有当前 build 的 dump** 时，RVA 不适用（手册给的属于 `25480438`），得自己重新定位；
  仓库里唯一的自动找法是 `tools/dlbin_keyhunt.py`，**它没有成功记录**。

### 1.3 不要碰的清单

| 不要碰 | 原因 | 替代 |
|---|---|---|
| 记录行**开头 8 B**（`+0` type / `+4` name_id） | 校正字写进去 = 把主键与名字 ID 改成随机值 → `0xc0000005 @ game.dll+0x1083a45`，三次同签名 | 尾部宿主（§4.5） |
| `+0` 条目 ID | 连续 1 基主键；重复必崩，复制行沿用原 ID 也崩 | 新行取 `max+1`；能不加行就不加 |
| 五个本地化 ID（`+0x28/+0x2C/+0x30/+0x34/+0x38`） | 条目身份；改了面板名字/描述会跟着变，且只能借**现有**字符串 | 真要改名，只改前两格并确认引用存在 |
| `LDLD` 头 `+16` 的 `wide` | 块头宿主的前提是 `wide` 仍为 1；无约束反解会破坏它 | 用 tail；非用 L1 就做受约束反解 |
| 正在运行的游戏目录 | 表在启动时读入，文件可能被占用 / 替换到一半 | 先关游戏，再装（§7.1） |
| `SSEO` / 护甲多被动管理的同一张表 | 两个 writer 争基线，Restore 可能把改动版当原版（§7.7） | 一张表只让一个 writer 管 |
| `--host-mode row` | 工具帮助自己写着「实机已验证会崩」 | 默认 `tail`，别传这个开关 |
| `.patch_N` 覆盖 `data/game/*.dl_bin` | 松文件不在 `bundle_database.data`，补丁层看不到它 | 只能替换文件本身（本路线） |
| 20 张「零空位」表直接套 tail | 只有战备（`+8`）/ 实体（`+12`）实机验证过宿主被接受；其余逐表未验 | 先在单表上做一次进游戏测试 |
| 任何密钥、`streams/*.xor`、含 epk/tag 的 `report.json` | 泄露 = 别人能伪造通过校验的数据文件 | 本地保存；文档只写「自备」 |
| 多人游戏 / 分发改过的游戏数据 | 改的是全局数据文件，会影响他人体验，也违反服务条款 | 单人 / 私人环境自用 |

### 1.4 工具可用性（先认清哪些在仓库里）

| 工具 | 作用 | 仓库状态 | 依赖 |
|---|---|---|---|
| `murmur64.py` | 算 `MurmurHash64A`；库函数 `padding_word_for_hash` 解校正字 | ✓ 已发布 | 标准库 |
| `table_dictionary.py` | 全表字典：组 / 行 / stride / 字段树 | ✓ 已发布 | PyNaCl + `typelib.py` |
| `plain_edit.py` | 任意 `LDLD` 容器按绝对偏移写，tail 宿主 + 6 门禁 | ✓ 已发布 | 标准库 |
| `stratagem_tune.py` | 按内部名 / type 改战备行，`--edit` 一次改多行，tail 宿主 + 7/8 门禁 | ✓ 已发布 | 标准库 + typelib |
| `dlbin_seal.py` | 解封 / 重封 / 结构解析 / 往返自检 | ✓ 已发布 | PyNaCl |
| `build_cache.py` | 把 55 张表 + typelib 解成按 build 存放的明文缓存 | ✓ 已发布 | PyNaCl |
| `build_diff.py` / `build_geometry_diff.py` | 换 build 后逐表回答「改了什么」 | ✓ 已发布 | PyNaCl |
| `expl_set.py` / `proj_copy_row.py` / `entities_modeb.py` | 爆炸行 / 弹丸整行 / 实体武器格 | ✓ 已发布 | 标准库 |
| `ent_set.py` | 实体表按绝对偏移写（非标准容器） | ✗ **私有，未随仓库发布** | 标准库 |
| `dlbin_deploy.py` | 自动备份 / `install` / `restore` / 账本 | ✗ **私有，未随仓库发布** | 标准库 |
| `check_links.py` | 文档链接自检 | ✓ 已发布 | 标准库 |

> 私有工具不影响方法论：`ent_set` 的判据与 §4.7 相同；`dlbin_deploy` 的五条不变量在 §7.3 里退化为最小三步，自动版多出来的是账本与安全闸。**本文的命令只用仓库里存在的工具 + 标准 shell**，私有工具只在说明「自动版长什么样」时点名。

### 1.5 八步速查

| 步 | 动作 | 命令（占位符） | 硬判据（不过就停） |
|---:|---|---|---|
| 1 | 建基线 / 取明文 | `build_cache.py --sk <sk> --game "<游戏>"` 或 `dlbin_seal.py open-key` | 明文哈希 = §2.3 锚点；`blocks` 能解析 |
| 2 | 定位字段 | `table_dictionary.py` + 内部名 / 绝对偏移 + 跨行统计 | 有**可证伪预测**，不是「看起来像」 |
| 3 | 写入 + 保哈希 | `stratagem_tune.py` / `plain_edit.py`（实体另说） | 输出长度 = 原长 + pad + 8（战备 `+8` / 实体 `+12`） |
| 4 | 读门禁 | 看工具 stdout 的 G1..G7 | 该工具的门禁**全 PASS**，diff 字节数 = 预期 |
| 5 | 重封 | `dlbin_seal.py seal-key --key <pk>` | 封包 = 明文 + 48 B |
| 6 | 往返 | `open-key` 解回 + `cmp` | 解回**逐字节相同**，哈希仍等于锚点 |
| 7 | 部署 | 备份 → 替换 → **盘上回读**（§7） | 从**游戏目录那份**解回的值 = 目标值 |
| 8 | 实机 + 记账 | 面板 / 任务内计时 / 日志 | 先算预测，再看读数；账本留档 |

全链只需 Python 3.11+ 标准库；第 5 步与第 1 步的解封需要 **PyNaCl**。

---

## 2. 取明文：两条路与三个自检

### 2.1 路线 A · 缓存明文（整包，推荐）

```bash
python tools/build_cache.py --sk <recipient.sk> \
    --game "D:/SteamLibrary/steamapps/common/Helldivers 2"
# 默认输出：refs/dlbin/plaintext-<buildid>/   （55 张表 + dl_library.dl_typelib）
# manifest 不用给：--appmanifest 的默认值就是 D:\SteamLibrary\steamapps\appmanifest_553850.acf
# （在 steamapps/ 下，不在 common/Helldivers 2/ 下；照抄一个不存在的路径会在第 1 步 FileNotFoundError）
```

适合：第一次上手、换 build、要跨表统计、要跑 `table_dictionary.py`。产出目录里 `_index.json` 记 `buildid`、每张表的 `plain_bytes` / `sealed_bytes` / `sha256`；先看它，再抽样算两个哈希。

```bash
python tools/murmur64.py refs/dlbin/plaintext-26088801/generated_stratagem_settings.dl_bin
python tools/dlbin_seal.py blocks refs/dlbin/plaintext-26088801/generated_stratagem_settings.dl_bin
```

### 2.2 路线 B · 现场解封（单张，快）

```bash
# 明文
python tools/dlbin_seal.py open-key --key <recipient.sk> \
    "<游戏>/data/game/generated_stratagem_settings.dl_bin" \
    --out <work>/generated_stratagem_settings.dl_bin

# 类型库也必须解到同一目录：stratagem_tune.py 靠它取 stride，找不到就退出
python tools/dlbin_seal.py open-key --key <recipient.sk> \
    "<游戏>/data/game/dl_library.dl_typelib" \
    --out <work>/dl_library.dl_typelib

python tools/dlbin_seal.py blocks <work>/generated_stratagem_settings.dl_bin   # 12 组、末组 6,420 B
python tools/murmur64.py   <work>/generated_stratagem_settings.dl_bin          # 04BBE33EF809862A
```

适合：只改一张表、已经知道偏移、不想解 56 个文件。**代价**：每次都要自己确认「解的是原版、不是上一轮的 mod 负载」。

| | 路线 A 缓存 | 路线 B 现场 |
|---|---|---|
| 输入 | `recipient.sk` + 游戏目录 + manifest | `recipient.sk` + 单个密文 |
| 产出 | 55 张表 + typelib | 1 张表 + typelib |
| 强项 | 跨表统计、字典、build 对比 | 快、路径短 |
| 风险 | 缓存被已部署的 mod 污染（§2.4） | 解到的是改过的文件；漏解 typelib |
| 必做 | 抽样哈希 = 锚点 | 每张都哈希 = 锚点 |

### 2.3 三个自检与五张表的锚点

拿到明文，先做这三件事，缺一不可：

1. **长度**：密文长度 − 48 = 明文长度（单张解封时最直观）；
2. **结构**：`dlbin_seal.py blocks` 能逐组解析，组数 / 末组 payload 符合预期；
3. **哈希**：`murmur64.py` 等于 §2.3 的锚点。

| 表 | 明文 B | 封包 B | 组 / 行 / stride | 明文 `Murmur64A`（锚点） |
|---|---:|---:|---|---|
| `generated_stratagem_settings` | 82,384 | 82,432 | 12 组 / 153 行 / 400 B | `04BBE33EF809862A` |
| `generated_explosion_settings` | 68,156 | 68,204 | 1 组 / 424 行 / 152 B | `2ABCD21D2536373D` |
| `generated_projectile_settings` | 96,604 | 96,652 | 1 组 / 355 行 / 272 B | `946A4FE5FAAAE076` |
| `generated_entities` | 47,259,396 | 47,259,444 | 275 个 `LDLD` 块 | `8E49771B181FFAA1` |
| `generated_damage_settings` | 50,336 | 50,384 | 2 组 / 661 行 / 76 B | `D03587CCBD2FECFC` |

**哈希对不上时不要往下走**。三种常见原因：build 不是 `26088801`；解到了已部署的 mod 负载；`--key` 用错 / stream 不对。`open-key` 用错密钥会直接抛 `CryptoError`；`unseal` 用错 stream 只打一行 `WARNING: plaintext does not parse (wrong stream?)` 然后**照样写文件并返回 0** —— 所以永远以哈希为准，不以退出码为准。

### 2.4 明文缓存污染：一次真实的误报

| 时间 | 发生了什么 | 结果 |
|---|---|---|
| 09:49 | 备份原版、生成 mod 负载 | 原版 4,016 B 的表还在 |
| 09:52 | 全表 dump | 把**已部署的 4,992 B 负载**当成原版存进缓存 |
| 13:2x | 游戏更新 | 被误报成「这次更新改了一张表」 |
| 事后 | 核对两个 build 的原始文件 | 逐字节相同，根本没变 |

规则：**dump 前确认 `data/game` 是原版**（没装过自己的 mod，或先 `restore`）；每次换 build 重跑 `build_cache.py`；不要拿「上次的缓存」当基线。详见 [BUILDS.md](../../BUILDS.md) §6 与 [BUILD-26088801-DIFF.md](../builds/BUILD-26088801-DIFF.md)。

### 2.5 「原版判定」：哈希 == 锚点识别不了保哈希的 mod

| 判据 | 能识别 | 识别不了 |
|---|---|---|
| 明文 `Murmur` == 锚点 | build 不对 / `--key` 用错 / 解错了文件 | **这一份是不是原版** —— 保哈希改过的明文，哈希**仍然等于**锚点（这正是本路线成立的原理） |
| 封包字节数 | 装过没有：战备表原版 82,432 B，装过 §11 的负载是 82,440 B | 装的是哪一份 |
| 与备份逐字节比对 | 一切改动 | 没有备份就没得比 |

本文写作时本机就是活反例：账本里 `installed_sha256 = 32294d8d…`、封包 82,440 B（§11.6），而盘上那份的明文哈希按机制仍等于 `04BBE33EF809862A`。**所以「哈希对上了」只证明「解的是这一版游戏的这张表」，不证明「盘上是原版」。**

判「原版」只有两条路：① 从没装过 mod 的干净基线；② 有一份装前封包备份（`build_cache.py` 的 `_index.json` 里每张表都记了 `sealed_bytes`，与盘上文件逐张对一遍，比只对哈希更早发现问题）。**没有原版备份，就没有可核对的原版清单**——这是这条路线唯一无法事后补救的东西。

### 2.6 无密钥预演：不需要 sk/pk 也能跑通的那一段

| 资产 | 内容 | 怎么用 |
|---|---|---|
| `tables/` 三张明文样本 | projectile 96,604 B / damage 50,336 B / weapon_customization 30,824 B | 直接喂 `plain_edit.py`：tail 宿主 + 完整 G1–G6，真跑不是假想 |
| [refs/table-geometry.json](../../refs/table-geometry.json) | 55 张表的 plain / groups / count / stride（build `25988413`） | 无 sk 就能查 stride 与行数 |
| [refs/exports/stratagem_settings.csv](../../refs/exports/stratagem_settings.csv) · [.md](../../refs/exports/stratagem_settings.md) | 153 行的 group / row / 内部名 / `+104` 冷却…（生成于 2026-10-22，文件本身**没标 build**；这 55 张表在两 build 间逐字节相同，见 [BUILD-26088801-DIFF](../builds/BUILD-26088801-DIFF.md)） | 把「想改哪一条」落到具体组行 |

实测（2026-10-23 本仓库内复跑，**✓ 离线**）：

```bash
python tools/murmur64.py tables/generated_projectile_settings.dl_bin      # 946A4FE5FAAAE076 = 锚点
python tools/plain_edit.py --plain tables/generated_projectile_settings.dl_bin \
    --out /tmp/probe.plain.dl_bin --set 0xBC=u32:12345
```

输出：`96,604 → 96,616`（对齐 4 + 宿主 8）、`G1..G6` 全 PASS、`diff=3`、哈希仍 `946A4FE5FAAAE076`。**这一段不需要任何密钥**，练的正好是最容易错的几件事：绝对偏移怎么算（单组表 `44 + i×stride + 字段`）、值语法、tail 的 `pad+8`、门禁读法。

边界：预演**不能**替代真表 —— 它不能封、不能部署、不能进游戏；`tables/` 里没有战备表（`stratagem_tune.py` 只认 stride 400 + typelib，跑不了）。

---

## 3. 定位字段：三条手段与一张选表

### 3.1 先看懂容器几何（`LDLD`）

```
文件   = u32 group_count │ 组 × { "LDLD" + 组头(24 B) + payload }
组头   = magic(4) ‖ version(4) ‖ type_id(4) ‖ payload_size(4) ‖ wide(4) ‖ extra(4)
payload = 描述符 16 B（u64 marker=0x10 ‖ u64 count）‖ 行 × stride ‖ 尾部变长块（可能没有）
行起点 = payload + 16          （不是 payload + 44）
```

- 单组表的**文件绝对偏移** = 4（组数）+ 24（组头）+ 16（描述符）= 44；多组表每组各自从 `payload + 16` 起。早期文档把「爆炸行基址 44」写成 payload 相对偏移，差了 28 B —— 写工具时用错基准就是改错字段。
- 行数来自描述符里的 `count`，**不要**用 `payload // stride` 反推（有尾块的表会算错）。
- `LDLD` 容器在本 build 有**三种形态**（55 张表里 43 张是标准 counted-LDLD，12 张不是）：
  - **标准**：首 `u32` = 组数、块链正好结束在文件尾 —— 43 张，`plain_edit.py` 可写；
  - **块前带 4 B 标签**：`generated_entities`（275 个 `LDLD` 块、块头实际 28 B）、`generated_entity_deltas`；
  - **首 `u32` 不是组数**：`stamp_settings`（文件直接以 `LDLD` 开头）、`zone_data`（`u32=3` 但块链从 `0x8` 起）、`resource_swap`（24 B、无 `LDLD`）。
  另有 7 张是 counted 形态但块链后带尾部数据，`plain_edit.py` 报「尾部残留」拒写：`destruction`（131,328 B）、`galactic_presence`（1,096）、`modifier`（120）、`planet_data`（3,504）、`planet_region`（2,952）、`region_settings`（15,719）、`route_settings`（24）。实体库的特例写法见 §4.7。

### 3.2 手段一 · typelib stride 扫描（结构）

```bash
python tools/table_dictionary.py --sk <recipient.sk> \
    --game "D:/SteamLibrary/steamapps/common/Helldivers 2" \
    --names refs/dl-type-names.txt \
    --json <work>/dict.json --md <work>/DICT.md
```

关键接口：`Dictionary.element_of(type_id) → (element_type_id, stride)`。容器类型若只包一个成员、且该成员记录更大，就返回成员类型与它的记录大小。`--names` 可选；不给时类型名全是 `0xXXXXXXXX`（类型库的字符串表是空的，名字得靠外部清单反查）。

**⚠ 已发布字典 MD 的一个已知缺陷**（2026-10-23 离线复现，尚未修）：`sample_rows()` 只对旧 layout 名（`array` / `array+tail` / `hashmap+rows`）补 `+16` 描述符偏移，而 `geometry()` 现在返回 `rows` / `rows+blob`，于是 `TABLE-DICTIONARY-25988413.md` 的「row 0, both readings」列整体错位：**标号 `N` 显示的是真实偏移 `N−16` 的字节**。例：第 3004 行标号 `8` 显示 `0x0000000D`（其实是组头 count=13）；第 3019 行标号 `96` 显示 `0xFFFFFFFF`（其实是 `row0+0x50` 的无限次数）。只影响人读报告，不影响任何写入路径。修法：把 `rows` / `rows+blob` 加进判定元组并重新生成；在那之前，**用 `--json` 的几何 + 直接读字节**，不要照 MD 的样本列抄偏移。

另两个使用注意：`table_dictionary.py` 的 MD 标题与 JSON `build` 字段硬编码 `25988413`，在 `26088801` 上重跑仍打旧标签；`--sk` 会把短密钥补零、长密钥截断，不校验长度。build 号以 `build_cache.py` 的 `_index.json` 和哈希锚点为准。

### 3.3 手段二 · 按内部名找行（身份）

战备行 `+0x10` 是一个 `u64` 字符串偏移（相对 payload 起点），指向尾部字符串块里的**内部名**，如 `ORBITAL. LASER`、`EAGLE. AIRSTRIKE`。面板显示名不在表里。

```bash
# 精确名优先；没命中才退化为子串
python tools/stratagem_tune.py --plain <work>/generated_stratagem_settings.dl_bin \
    --name "EAGLE. REARM" --set cooldown=5 --out <work>/probe.plain.dl_bin
```

规则与边界：

- `--name "Orbital Laser"` **命中 0 行** —— 表里是 `ORBITAL. LASER`（点号 + 空格），不是面板写法。用 wiki / `refs/table-row-names.json` / `stratagem_join.py` 把显示名换成内部名。
- 精确名优先，否则子串；`EAGLE` 会命中多行 → 工具拒绝，必须写全。
- `row_name` 遇到非 ASCII 返回空串，该行永远匹配不到；当前战备名全 ASCII，换语言/换表会静默失效。

### 3.4 手段三 · 已知绝对偏移（快，但只对当前 build）

```
绝对偏移 = 组起始 + 24（LDLD 头） + 16（描述符） + i × stride + 字段偏移
        = payload + 16 + i × stride + 字段偏移
```

例：`EAGLE. REARM` 是组 2 行 8，行首 `0x2D70`；冷却字段 `+0x68` ⇒ `0x2D70 + 0x68 = 0x2DD8`。

换成一条你没动过的战备（真实需求：把 `ORBITAL. 380MM HE BARRAGE` 的 240 s 冷却改成 60 s），是同一套走位，只是多两步换算：

| 步 | 做法 | 这一步的实例 |
|---:|---|---|
| 1 | **值 → 行**：在 [refs/exports/stratagem_settings.csv](../../refs/exports/stratagem_settings.csv) 里搜面板名 | `380MM` ⇒ `group=6, row=6`（`+0` = `0x80`） |
| 2 | **行 → 行首**：**不是** `44 + 6×400`（那是单组表算式）。多组表要用 `dlbin_seal.py blocks` 打印的**该组 `payload_off`**：`行首 = payload_off + 16 + row×stride` | 战备表 12 组，各组 `payload_off` 不同 |
| 3 | **行首 → 字段** | `+ 0x68`（冷却） |
| 4 | **写 + 预测**：`f32:60`，面板预测 `60 × 0.90 × 0.95 ≈ 51.3` | 先写下 51.3，再去读面板（⚠ 这一行没实测过，别当结论） |

**多组表的 `payload_off` 必须现查**：把单组表的常数 `44` 套到组 6 会整体算错，而且错得很像「字段没生效」。

```bash
python tools/plain_edit.py --plain <work>/generated_stratagem_settings.dl_bin \
    --out <work>/onefield.plain.dl_bin --set 0x2DD8=f32:5.0
```

前提：明文哈希 = 锚点；行数 / stride 未变；你改的是**字段**不是身份槽。写完必须 G4 回读；如果行被加/删过，所有绝对偏移作废，回到 3.2/3.3 重算。

### 3.5 该改哪张表：先按语义选表，再谈偏移

| 你想改 | 先看哪张表 | 入口 | 状态 |
|---|---|---|---|
| 战备冷却 / 呼叫时间 / 使用次数 | `generated_stratagem_settings` | `+0x68` / `+0x54` / `+0x50` | ✓ 实机 |
| Eagle 回收时间 | `generated_stratagem_settings`，`EAGLE. REARM` 独立行 | `+0x68`（同一字段、两种语义） | ✓ 字段实机；系数 ⚠ |
| 爆炸伤害 / 半径 / 破片 / 粒子 | `generated_explosion_settings` | `+0x04` / `+0x10..+0x18` / `+0x50/+0x54` / `+0x38/+0xA8` | ✓ 多数实机；详见 [EXPLOSION-VISUAL](../explosions/EXPLOSION-VISUAL-26088801.md) |
| 弹丸换**爆炸效果** | `generated_projectile_settings` | `+0x90` / `+0x9C`（十进制 `+144` / `+156`）= 命中 / 到期**爆炸 type 引用** | ✓✓ 实机 |
| 弹丸换**弹头**（整行搬运） | `generated_projectile_settings` | **整行 272 B** 从供体行拷来（`proj_copy_row.py`），**不改** `+0x90/+0x9C` | ✓✓ 实机 |
| 弹幕轮数 / 散布 | `generated_entities`，`Bombardment` 组件 | `+0x18` 轮数 / `+0x24` 散布（f32 米） | ✓ 实机 **@`25988413`**（5→1 落 2 组；36.0→2.0） |
| 武器装填时可移动 | `generated_entities`，`WeaponReloadComponentData` | 80 B 行：`ManualClearing` / `ReloadAllowMove` / `Duration` | ✓ 实机 **@`25988413`**（MG-43 的 `ReloadAllowMove` 0→1） |
| 爆炸外观 | 爆炸表 + 弹丸表 + 战备表 | 整行克隆 + 爆炸 type + `+0xA8` 包 | ✓✓ 实机 |
| 新可见战备 / 解锁未发布物品（**军械库**） | **不在 55 张表** | — | ✗ 否证（需运行时登记表） |
| **未发布战备进任务**（不经军械库） | `generated_stratagem_settings +0xC8` | 宿主战备「附赠」另一条战备 id，不占配装位 | **✓ 实机**（7 条，见 [UNRELEASED](../tables/UNRELEASED-STRATAGEMS-26088801.md)）|
| 自定义名称 / 描述文本 | `.strings` 语料 | — | ✗ 另一条路线 |
| 战备攻击参数（`num_bombs` / `num_salvos` / `area_size` / `fire_height`） | **不在明文表** | bundle 里的战备攻击定义 | ✗ 全扫空 |
| 伤害 / 穿甲（`DamageInfo`） | `damage_settings` | 76 B / 8 成员，**行内**零 padding；宿主用 tail（或借无主行）（[DAMAGE-SETTINGS §5](../tables/DAMAGE-SETTINGS-26088801.md#5-宿主策略)） | **✓ 实机**（面板可见） |

> 选表的第一原则：**面板上不显示的数，不要先假定它不在表里，也不要假定它在战备行里**。轮数与散布最终都在实体表，`+0x3C` 只是投放方式枚举 —— 见 §3.6 的反面教材。
>
> 实体表那几行偏移是在 `25988413` 上实测的；`26088801` 的 55 张表逐字节未变（[BUILD-26088801-DIFF.md](../builds/BUILD-26088801-DIFF.md)），所以可沿用，但仍以本 build 的哈希锚点与 §2.3 自检为准。

### 3.6 定案仪式：跨行统计 + 单变量实机

| 证据源 | 能给什么 | 不能给什么 |
|---|---|---|
| `table_dictionary.py` 的字段树 | 偏移、宽度、嵌套 | **语义**（类型库没有名字） |
| wiki 数据模块 / 本地 SQLite | 字段语义、参考数值 | 不保证与本 build 同步 |
| 外部 SDK（[HD2Runtime by SkyeShade](https://github.com/SkyeShade/HD2Runtime)、SSEO） | 现成字段名与用法 | 版本可能落后；引用需显式署名 |
| 跨行统计 | 相关性、候选字段 | 因果；可能被「投放方式」这类枚举骗 |
| **单变量实机** | **唯一能定案的证据** | 要花一次启动；要算对面板公式 |

**四步定案，缺一不可**：

1. 找一个**只与你的假设自洽**的分布（例：全部弹幕行的 `+0x3C` 都是 5）；
2. **写下一个具体预测**（例：把 `+0x54` 改成 12.0，面板应显示 `12.0 + 2.45 − 1.0 = 13.45`）；
3. 只改**一个**字段，上机读**另一个**可读数；
4. 命中 ⇒ 字段语义 + 加成模型同时坐实；不中 ⇒ 假设错，**不是「没生效」**。

反面教材（都是真花过时间的）：

| 案例 | 当时怎么想 | 实际 | 教训 |
|---|---|---|---|
| `+0x3C` | 弹幕行全是 5 ⇒ 以为它是「轮数」 | 它是**投放方式枚举**（Eagle=0 / 单发=1 / 武器=2 / 弹幕=5） | 跨行分布只能提候选，不能定语义 |
| `+0x54` | 只看 380mm 的 6.0 vs 面板 7.45 ⇒ 判「不是呼叫时间」 | 单看表值并不分层：153 行里 **111 行非零**，值就是各自的呼叫基础秒（3 / 5 / 120…）；分层的是**「面板 − 表值」这个差值**（ORBITAL 实测 `12.0 → 面板 13.45`，即 `+2.45−1.0`；EAGLE `0 → 4.10`），预测 13.45 实测 13.45 | 单样本对不上就否定字段，是误判 |
| `EAGLE.REARM +0x68` | 150.0 与 wiki 的 150 s 同值 ⇒ 判「回收时间」 | 改 5 后任务内 3 秒多；字段语义 ✓，升级系数 ⚠ | 同值只能提假设，改完读到才算 |

---

## 4. 写入与保内容哈希

### 4.1 两层封装：密封盒 + 内容哈希

```
磁盘文件 = epk(32) ‖ tag(16) ‖ ciphertext        总长 = 明文 + 48
ciphertext = plaintext XOR keystream[32:]        （libsodium crypto_box_seal 形态）
```

| 事实 | 状态 | 后果 |
|---|---|---|
| 每个 `generated_*.dl_bin` 比明文长 48 B | ✓ 实机 | 长度可直接当自检 |
| 封装只需公钥 `recipient.pk`，ephemeral 自己随机 | ✓ 实机 | 长度**没有上限**（不是 65,504） |
| 每次封装的 epk / tag 都不同 | ✓ 实机 | 不能拿封包哈希比内容；要比就比明文哈希 |
| 引擎加载时重算 `MurmurHash64A(明文)` 与 `game.dll` 里的期望值比对 | ✓ 实机 | 封装正确但内容对不上 → `0xC000000D` |

**门槛从来不是「能不能封」，而是「改完哈希必须回到原值」**：期望值是原版明文的哈希，不能重算一个新哈希写进去。

### 4.2 内容哈希闸门

```
算法：MurmurHash64A
seed = 0xDEADBEEFABAD1DEA
乘数 = 0xC6A4A7935BD1E995
终局 = h ^= h >> 47; h *= M; h ^= h >> 47
```

第一次改雾色表（内容改了、哈希没保）启动即崩 `0xC000000D`；用**完全相同的原版明文**重新封装不崩 ⇒ 崩在第二层内容校验，不是封装、不是 tag。**那次为什么保不住哈希**：组头 `+16` 在 `0x14` 不 8 对齐，行内也没找到可用空位，而 tail 自造宿主当时没在这张表上验证过 ⇒ 只能改内容、保不住哈希，崩是必然。**但「这张表永远不能保哈希」不是结论**：`generated_weather_color_set_settings` 是 1 组、块链正好结束在文件尾、明文 25,916 B（`%8 = 4`），`plain_edit` 的 tail 宿主（pad 4 + 8 = `+12`）在结构上完全可用，只是**没在它上面进过游戏（⚠ 未证）**。详见 [DLBIN-SEALED-BOX.md](../engine/DLBIN-SEALED-BOX.md) 与 §9.5。

### 4.3 校正字：为什么能反解，约束是什么

Murmur64A 的块函数对单个 8 B 字是可逆的（乘数有模 `2^64` 逆元，xor-shift 也可逆），所以给定目标哈希，可以**代数反解**某一个 8 字节对齐字的取值，不用爆破：

```python
from murmur64 import padding_word_for_hash
word = padding_word_for_hash(data, word_offset, wanted_hash)
```

两个硬约束：

1. `word_offset % 8 == 0` —— 哈希按 8 B 一块吃，校正字必须落在对齐的字上；
2. `0 <= word_offset <= len(data)//8*8 - 8` —— 必须**完整落在数据内**；越界或落在尾部残字上，求解器直接 `ValueError`。

**关键设计**：在明文末尾追加 8 个零字节，就凭空造出一个 8 对齐、语义为空的字；解出校正字写进去，整块哈希回到原值。代价只是明文 +8 B，而 `payload_size` 也要 +8 让容器接受这段尾巴。

> `murmur64.py` 的命令行只打印哈希，**不能**直接求校正字；求解器只以库函数形式暴露。单看 `--help` 容易误判它「只能算哈希」。

### 4.4 尾部宿主（tail）六步

以战备表为例（明文 82,384 B，已 8 对齐）：

1. **对齐**：把明文补到 8 的倍数（`plain_edit` 自动做；`stratagem_tune` 要求输入本来就对齐，否则拒绝）；
2. **追加**：在末尾追加 8 个零字节；
3. **改尺寸**：找到最后一个 `LDLD` 块，把块头 `+12` 的 `payload_size` 加 **`pad+8`**（战备表已 8 对齐，pad=0：字段在文件偏移 `0x128B0`，6,420 → 6,428；实体表明文 `%8 = 4`，pad=4 ⇒ `+12`，见 §4.7）；
4. **解字**：以原哈希为目标，在**对齐后的**末尾偏移（= 追加区起点，8 对齐）解 8 B 校正字；
5. **写入**：把校正字写到追加区；
6. **复算**：`murmur64(new) == murmur64(old)`，且容器能重新解析、末尾无残留。

Eagle 实例的追加区是 `0x141D0–0x141D7`，校正字 `53 92 A9 E4 EE 8D 69 2E`（文件顺序）；`0x141D0 % 8 == 0`。

### 4.5 为什么校正字绝不能放进记录行

| 变体 | 长度 | 行数 | 校正字落在哪 | 结果 |
|---|---|---|---|---|
| 复制一行 `(NOT USED)` | +400 | 11→12 | `(NOT USED)` 行开头 | ✗ 崩 |
| 只把 380mm 的 `+0` 改成别人占用过的值 | 不变 | 不变 | 同上 | ✗ 崩（同签名） |
| 等长改冷却 240→60 | 不变 | 不变 | 同上 | ✗ 崩（同签名） |
| 只加 8 字节尾巴 | +8 | 不变 | 追加的尾巴 | ✓ 通过 |

三次崩溃签名逐字相同：`0xc0000005 @ game.dll+0x1083a45`，会话寿命 26–29 秒。根因：记录行开头 8 B 正是 `+0` 的条目 ID 与 `+4` 的名字 ID；校正字是 64 位随机数，写进去就是把主键与名字 ID 一起改掉。

**一条值得背下来的话**：「这一行面板不渲染」**≠**「引擎不读它的字段」。`(NOT USED)` 行的显示名是死引用、不会被画出来，但它的 `+0` 照样参与读表建索引 —— 渲染与建 map 是两条独立路径。

宿主选择顺序：

| 优先级 | 宿主 | 条件 | 证据 |
|---:|---|---|---|
| 1 | **tail**：末组 `payload_size += pad+8`、文件尾追加 `pad+8` B | 末块必须结束在文件尾 | ✓ 实机（战备 pad=0 → `+8` / 实体 pad=4 → `+12`，两次都盘上回读） |
| 2 | 块头保留区（L1）：`LDLD` 头 `+16` 的 8 B | 绝对偏移 8 对齐，且 `wide` 必须仍是 1 ⇒ 受约束反解 | ⚠ 未上机 |
| 3 | 行内非主键空位 | 必须先证明那个字没人读 | ⚠ 爆炸表 `+0x34` 已实机；其它表逐个证明 |
| 4 | 行首 8 B | —— | ✗ 已崩三次 |
| 5 | 零空位表自造 tail | 逐表未验 | ⚠ 只有战备 / 实体实机 |

### 4.6 写入工具与值语法

| 场景 | 工具 | 寻址 | 门禁 | 注意 |
|---|---|---|---|---|
| 战备行（400 B） | `stratagem_tune.py` | 内部名 / `+0` type | G1–G8（6 项独立） | `--edit` 可重复；tail 默认；只认 `uses` / `callin` / `cooldown` |
| 标准 counted `LDLD`（**43/55 张**：块链正好到文件尾） | `plain_edit.py` | 文件绝对偏移 | G1–G6（5 项独立） | 单次写 >16 B 要 `--allow-wide`；**不保护身份字段**；其余 12 张见 §3.1（7 张报「尾部残留」） |
| `generated_entities` | `ent_set.py`（私有）或自写 | 绝对偏移 | G1–G5 | 非标准容器；`plain_edit` 会拒绝 |
| 爆炸行 | `expl_set.py` | type + 行内偏移 | G1–G6 | 已发布；半径 / 破片 |
| 弹丸整行搬运 | `proj_copy_row.py` | 行号 / type | G1–G5 | 已发布；换弹头 |
| 实体武器格 | `entities_modeb.py` | 单元格 | ✓✓ 实机 | 可选弹种 / 双弹药池 |

**值必须带类型前缀**，这是用一次「整行被抹掉」换来的：

| 写法 | 实际字节 | 说明 |
|---|---|---|
| `u32:158` | `9E 00 00 00` | 十进制 158，小端 u32 ✅ |
| `f32:12.5` | `00 00 48 41` | IEEE-754 小端 ✅ |
| `hex:11223344` | `11 22 33 44` | 按文件顺序 ✅ |
| `4:11223344` | `11 22 33 44` | 宽度 4、**十六进制文本**语义；不是十进制 |
| `4:99` | `00 00 00 99` | 同上 ⇒ 想写 99 必须用 `u32:99` |
| `4:0x11223344` | — | ⚠ 已知 bug：`ValueError: non-hexadecimal number`；用 `hex:` 或去掉 `0x` |
| `158`（裸整数） | 旧版：158 个零字节 | 把整行抹掉；当前 `plain_edit` 已拒绝无冒号的值 |

那次事故的细节：`--set 0x979c=158` 被旧解析器当成「宽度 158 字节、内容全 0」，整行被抹掉；更糟的是 G4 用**同一套解析逻辑**回读，于是「自己骗自己」通过了。这就是 G4 的固有上限（§5.3）。

### 4.7 实体库特例：`generated_entities`

```
u32 type_tag ‖ "LDLD" ‖ ver ‖ type_id ‖ payload_size ‖ wide ‖ extra ‖ payload
```

- 首 `u32` 是块类型标签，**不是组数**；实际 275 个 `LDLD` 块，块头实际 28 B；
- `plain_edit.py` 按「首 u32 = 组数」解析，会直接拒绝（实测 `@0x2d370` 报「第 1 块头不是 LDLD」）；
- 正确写法：扫 `LDLD` 魔数、按 `payload` 跳，跳过 payload 内的伪魔数；末块必须结束在文件尾（本 build：末块标签 `@0x2D11CB8`（`LDLD` 魔数在 `0x2D11CBC`）、payload 560、`+24+560` 结束于 `0x2D11F04` = 文件长，与 `ent_set.py` 的 `at+24+payload` 口径一致），才能用 tail 宿主；
- 这张表的明文 47,259,396 B，`%8 = 4` ⇒ tail 实际是 **4 B 对齐 + 8 B 校正字 = `+12`**（产物 `47,259,408 B`，末块 `payload_size` 560 → 572），并且已做**盘上回读**，不是「数学上可行」；
- 47 MB 的哈希求解是纯 Python 全表扫，单次数秒到十几秒；不要用「反复试盐」的块头路线，成本不可接受；
- **不要给武器新增独立弹种行**：四个变体（新行 A/B 池、整行克隆、按 wiki 真值、删条目重排）全部 `0xC000000D`；只改现有行（SG-8 实验）没问题。

### 4.8 一次封装改完所有改动

`stratagem_tune.py --edit` 与 `plain_edit.py --set` 都支持一次写多处；哈希锚点仍是**进入这次运行前的明文**。正确做法：把所有目标字段放进**同一次**运行、同一次封装、同一次部署。

> 旧版文档写「`--edit` 串两次会失效」——**这条已被离线否证**：对同一明文连做两次「追加 8 B + 解校正字」，两次后哈希仍等于原值（82,384 → 82,392 → 82,400）。真实代价只是每轮 payload +8 B、第二轮的 G2/G4 基准变成上一轮产物，容易误判「相对原版改了什么」。所以不是「不能」，是「不要」：一次改完。

---

## 5. 门禁 G1..G7：每一道在防什么

### 5.1 路线级七道

下面的 G1..G7 是**路线级**定义；各工具的实现编号并不统一（§5.2）。**引用时必须点名工具** —— 同一串 G 编号在不同工具里指的不是同一件事（尤其 G5 / G6），不点名工具的「G1..G7 全过」没有可核对的内容。

| 门禁 | 检查什么 | 为什么需要这一道 | 典型失败 |
|---|---|---|---|
| **G1 长度** | `len(edited) == len(original) + pad + 8` | 容器偏移全靠长度；少加/多加会让后续块与行错位 | 忘 pad、`payload_size` 没同步、把 +8 当成 +16 |
| **G2 差异集合** | 所有不同字节 ⊆ 声明偏移 ∪ 末块 `payload_size` 字段 ∪ 校正字 8 B | **最有价值的一道**：抓「顺手改到别处」——hex 块覆盖、写错偏移、宿主冲突 | 同一段既写 `hex:` 又写块内字段，两块互相覆盖 |
| **G3 哈希** | `MurmurHash64A(edited) == MurmurHash64A(original)` | 引擎的内容哈希闸门；不过就 `0xC000000D` | 校正字位置错、写到宿主之外、seed 假设错 |
| **G4 回读** | 每个声明字段按同一解析逻辑读回 == 目标值 | 抓偏移 / 宽度 / 端序错误 | 裸整数被当字节宽度；f32 与 u32 混写 |
| **G5 其余字节** | 除目标记录 / 字段外一字节未动 | 抓容器重建时丢字节 / 重排 | 重建时把尾块截掉；复制行时多写 |
| **G6 容器自洽** | 重新解析块链：组数、`LDLD` 魔数、`payload_size`、末尾无残留 | 抓「文件加了 8 B、但 `payload_size` 没加」 | 只 append 不改尺寸字段；尾块残留 |
| **G7 身份字段** | `+0` type 与五个 locid 槽（`+0x28..+0x38`）未变 | 抓撞主键 / 改条目身份；重复 `+0` 必崩 | 校正字落行首；复制行沿用原 ID |

### 5.2 各工具的真实编号（不要张冠李戴）

| 路线级 | `plain_edit.py` | `stratagem_tune.py` | `ent_set.py`（私有） |
|---|---|---|---|
| G1 | G1 | G1 | G1 |
| G2 | G2 | G2 | G2 |
| G3 | G3 | G3 | G3 |
| G4 | G4 | G4 | G4 |
| G5 | G5（**条件与 G2 相同**，不是独立检查） | G5（记录级：其它记录未动） | G5（弱：只验「块连续到新文件尾」） |
| G6 | G6（唯一真正重新解析容器的） | G6 是**记录级**（「目标行其余字段未变」），**不等于路线级 G6** | G5 兼作弱解析 |
| G7 | 无 | G7（`--set-type` 时降级为 G7'） | 无 |
| 额外 | — | G8 只是「报告是否制造重复 key」，恒 PASS，**不是门禁** | — |
| 独立检查数 | **5** | **6** | **5** |

所以：

- `plain_edit` 没有「7/7」，它只有 6 道，其中 G5 还是 G2 的重复；
- `stratagem_tune` **默认输出 7 行**（G1–G7）；只有 `--set-type` 时打印 **8 行**（G7 降级为 G7'，多一行恒真的 G8「报告重复 key」——那是记录，不是门禁）。G5 与 G2 记录级重叠，真正独立的是 6 项；
- 它的 G6 是「目标行其余字段未变」，**记录级**；路线级的 G6（容器重解析）它**没有**，靠 `dlbin_seal.py blocks` 兜底；
- `ent_set` 只有 5 行，且 G5 很弱；
- 说「7 道全过」时，只有 `stratagem_tune` 的 stdout 会出现 7 个 PASS；它的独立检查仍是 6 项，`plain_edit` 是 6 行 / 5 项，`ent_set` 是 5 行。

### 5.3 门禁的四个局限

1. **G3 是「相对不变」，不是「等于引擎期望值」**。`h0 = murmur64(原始明文)`，不是与 `game.dll` 里烘焙的常量比对。实体库的引擎期望值 `8E49771B181FFAA1` 只存在于文档 / 记忆里，这 7 个工具都没有断言它。因此 G3 的强度上限 = `murmur64.py` 的算法正确性；一旦引擎换 seed，全部门禁会静默通过、实机拒绝。
2. **G4 验证的是「按我的理解写对了」，不是「引擎按它的理解读对了」**。它和写入用同一套解析逻辑；158 字节零写入能过 G4 就是证明。字段语义只能靠 §3.6 的单变量实机。
3. **G2 的允许集合是调用者声明的**。`ent_set` 不校验目标落在哪个块 / 哪一行：只要差异 ⊆ 你声明的偏移，写进块头甚至 `payload_size` 都会放行。G2 抓的是「未声明的写入」，不是「有害的写入」。
4. **G6 只有 `plain_edit` 真正做**。`stratagem_tune` 改完只改末组 `payload_size`，不重新解析块链；结构断层要靠 `dlbin_seal.py blocks` 兜底。`ent_set` 的 G5 只验「末块结束在新文件尾」，是容器自洽的弱版本。

### 5.4 门禁之外还必须做的三件事

| 动作 | 证明什么 | 不能证明什么 |
|---|---|---|
| 明文哈希 = §2.3 锚点 | build / 文件 / 密钥没搞错 | 字段语义 |
| 封装往返逐字节一致 | keystream 对称、封装没丢字节 | MAC 有效、引擎接受（§6.3） |
| **盘上回读**（§7.4） | 装进去的那份就是你以为的那份 | 引擎读得懂（还要进游戏） |

**门禁全绿 ≠ 功能生效**。项目里真出过「全绿而效果为零」的事故；也出过「实验作废」——部署的根本不是那个变体（§8.5）。门禁只证明「我按自己声明的改了」，后者只能靠第 8 步。

---

## 6. 封装（`seal-key`）与解封往返

### 6.1 重新封装

```bash
python tools/dlbin_seal.py seal-key --key <recipient.pk> \
    <work>/stratagem_eagle_cd4_rearm5.plain.dl_bin \
    --out <work>/stratagem_eagle_cd4_rearm5.dl_bin

ls -l <work>/stratagem_eagle_cd4_rearm5.dl_bin    # 必须 = 明文 + 48
python tools/dlbin_seal.py inspect <work>/stratagem_eagle_cd4_rearm5.dl_bin
```

`seal-key` 走 libsodium `crypto_box_seal`：每次用**全新随机 ephemeral**，epk / tag 都变，所以同一份明文封两次得到两个不同文件 —— 这是正常的。**比内容只比明文哈希或解封后的字段，不要比封包哈希。**

> ⚠ 永远显式给 `--out`：`seal-key` 的默认输出是「去掉扩展名再加 `.dl_bin`」。输入若已经叫 `x.dl_bin`，默认输出就是 `x.dl_bin` —— 原地覆盖明文。

### 6.2 四条封装路线与 MAC 语义

| 路线 | 需要 | tag / MAC | 状态 | 用途 |
|---|---|---|---|---|
| `seal-key --key <pk>` | `recipient.pk` | 真 libsodium sealed box（真 epk + 真 Poly1305 tag） | **✓ 实机** | 常规封装；无长度上限 |
| `seal-material --material <dir>` | `epk.bin` + `poly.bin` + `keystream.bin` | `Poly1305(cipher, poly_key)`，**真 MAC** | **✓ 离线**（本轮未单独上机） | 第三方材料 / 互操作 |
| `seal --stream <S> --tag copy` | keystream + 旧封包 | **照搬旧 tag**，明文一改就失效 | **⚠ 未证** | 只在「引擎不校验 MAC」时可能成立，未验证 |
| `seal --stream <S> --tag zero` | keystream | 全零 tag，显然无效 | **⚠ 未证** | 诊断 |

关键事实：

- **tag 密钥 = `keystream[0:32]`**。一对已知明文/密文只能求出该文件的 `keystream[32:]`；`[0:32]` 永远求不出 ⇒ 拿旧 tag 重算密文会在打开时失败。
- 所以「没有 `recipient.pk` 就只能解、不能封」不是工具限制，是密码学限制。`recipient.pk` 是公钥，但它等价于**封装能力**（pk + 任意明文 ⇒ 引擎接受的封包）⇒ **需自备、不建议扩散**；`recipient.sk` 是私钥，只喂 `open-key` / `table_dictionary`。
- **65,504 B 不是格式上限**，只是「借用别人固定流」时的长度限制。拿到 `recipient.pk` 后 `seal-key` 用全新随机 ephemeral，82,432 B 往返一致、长度不限。
- `dlbin_seal.py selftest` 的字节级往返把**原 tag 原样搬回**，只能证明 keystream 对称，**永远不能证明 MAC 有效** —— 「封包往返一致」≠「引擎接受」。

### 6.3 解封往返校验

```bash
python tools/dlbin_seal.py open-key --key <recipient.sk> \
    <work>/stratagem_eagle_cd4_rearm5.dl_bin \
    --out <work>/roundtrip.plain

cmp <work>/roundtrip.plain <work>/stratagem_eagle_cd4_rearm5.plain.dl_bin \
  && echo "往返一致"
python tools/murmur64.py <work>/roundtrip.plain     # 必须 = 原始锚点
```

| 检查 | 判据 | 失败说明 |
|---|---|---|
| 封包长度 | `len(sealed) == len(plain) + 48` | 头/尾丢了，或封的不是这份明文 |
| 解回内容 | `cmp` 逐字节相同 | keystream / 材料不对 |
| 解回哈希 | = §2.3 锚点 | 明文本身不是原版，或解错了 |
| 字段回读 | 目标字段 = 新值 | 写到别处 / 解析错 |
| 结构 | `blocks` 能重新解析 | `payload_size` / 组链坏了 |

往返只证明「加解密对称、封装没丢字节」；**MAC 有效性与引擎接受都还没证**，后者必须靠第 7、8 步。

### 6.4 封装的六个坑

| 坑 | 现象 | 规避 |
|---|---|---|
| 默认输出覆盖明文 | 输入 `x.dl_bin`，默认输出也是 `x.dl_bin` | 永远 `--out` 到不同路径 |
| `--tag` 默认 `copy` 又必须给 `--from-blob` | 默认参数组合本身不完整，不能直接跑 | `seal-key` 或 `seal-material` |
| `unseal` 用错 stream 只警告、exit 0 | 垃圾明文被当成功产物写盘 | 以哈希为准，不以退出码为准 |
| keystream 是 per-file 的 | 换表 / 换 build 必须重新取；`seal` 只按长度校验，不告诉你流属于哪张表 | 每张表单独 `pairs` / 单独 `seal-key` |
| `pairs` 的 `streams/*.xor` + `report.json` 是密钥材料 | 泄露 = 可伪造 | 与私钥同级；绝不入仓 |
| `selftest` 把流目录写死在 `<root>/streams` | `pairs --out` 换目录后 selftest 找不到流 | 用默认目录，或手动指定 |

---

## 7. 部署与盘上回读

### 7.1 先关游戏

表在**启动时**读入；游戏运行时替换文件可能被占用，或读到一半的副本。部署前确认进程不在；部署后从游戏目录回读，再启动。

### 7.2 自动部署器的不变量（参考实现）

私有工作区里的 `dlbin_deploy.py`（**不随本仓库发布**）把五件事固定下来；这五条就是「自动备份 + install」的全部实质：

| 不变量 | 做法 | 防什么 |
|---|---|---|
| 备份先于写入 | 第一次 `install` 前 `cp` 到备份根，立刻 sha256 复核 | 改坏后无原版可回 |
| 安装安全闸 | `live` 必须等于账本里的 `backup_sha256` 或 `installed_sha256`，否则拒绝 | 踩掉游戏更新 / 别人的改动 |
| 原子替换 | 先写 `<name>.deploying` → 校验 sha256 → `os.replace` → 再校验 | 拷到一半崩溃留下半份文件 |
| 账本原子写 | 先写**同目录的 `ledger.tmp`**（`p.with_suffix(".tmp")` 会把 `.json` 换掉，不是 `ledger.json.tmp`），再 `os.replace` | 账本写坏，回滚失去依据 |
| restore 校验备份 | 回滚前校验备份哈希，回滚后复核 sha256；**无账本时直接覆盖**，不检查盘上第三方状态 | 备份不对拒绝；无账本时防不了第三方改动 |

```bash
# 有部署器时（路径按你的私有工作区替换）
python <private>/dlbin_deploy.py status
python <private>/dlbin_deploy.py backup  --file generated_stratagem_settings.dl_bin
python <private>/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin \
    --sealed <work>/stratagem_eagle_cd4_rearm5.dl_bin
python <private>/dlbin_deploy.py restore --file generated_stratagem_settings.dl_bin
```

`status` 的四态：**未接管**（无账本）/ **已装 `<from>`** / **已是原版** / **⚠ 盘上被改过**（既非原版也非我们装的）。这四个状态是判断「现在到底装了什么」的最快入口。

### 7.3 没有部署器时的最小三步（本仓库可执行）

> 下面是 **bash**（Git Bash / WSL）写法；PowerShell 逐条等价见 §7.8。

```bash
set -euo pipefail
GAME="D:/SteamLibrary/steamapps/common/Helldivers 2/data/game"
NAME="generated_stratagem_settings.dl_bin"
WORK="<work>"
mkdir -p "$WORK/backup"

# ① 备份（第一次装之前做一次；之后不要覆盖）
[ -f "$WORK/backup/$NAME" ] || cp "$GAME/$NAME" "$WORK/backup/$NAME"
sha256sum "$WORK/backup/$NAME"          # 记下来；Windows 可用 certutil -hashfile

# ② 安装：先写临时文件，校验，再 rename（同卷 rename 是原子的）
cp "$WORK/stratagem_eagle_cd4_rearm5.dl_bin" "$GAME/$NAME.deploying"
sha256sum "$GAME/$NAME.deploying"       # 必须 = 产物 sha256
mv -f "$GAME/$NAME.deploying" "$GAME/$NAME"

# ③ 盘上回读：从游戏目录那份解回来，不从自己的产物读
python tools/dlbin_seal.py open-key --key <recipient.sk> \
    "$GAME/$NAME" --out "$WORK/readback.plain"
python tools/murmur64.py "$WORK/readback.plain"   # 必须 = 锚点
```

字段级回读（比只看哈希更强）：

```bash
python - <<'PY'
import struct
p = open(r"<work>/readback.plain", "rb").read()
# 0x2608 = 0x25A0（组2 行3 = EAGLE. AIRSTRIKE 行首）+ 0x68（冷却）
# 0x2DD8 = 0x2D70（组2 行8 = EAGLE. REARM 行首）    + 0x68
print("AIRSTRIKE +0x68", struct.unpack_from("<f", p, 0x2608)[0])   # 期望 4.0
print("REARM     +0x68", struct.unpack_from("<f", p, 0x2DD8)[0])   # 期望 5.0
PY
```

### 7.4 为什么盘上回读不能省

| 只做到哪一步 | 漏掉什么 | 真实事故 |
|---|---|---|
| 相信自己的产物 | 游戏目录里可能根本不是这份 | 轮数实验部署的是**另一个 probe**，事后账本对不上，整次实验作废（§8.5） |
| 只做封装往返 | 往返证明的是「产物没坏」，不是「游戏目录里是产物」 | 换包 / 拷错路径 / 游戏更新覆盖，任何一步都能让盘上文件变回原版 |
| 从自己的产物回读 | 不证明 install 成功 | 读到的是「我封的」，不是「盘上装的」 |
| 从游戏目录回读 + 哈希 | 证明装进去的字节对 | 仍不证明引擎接受（要进游戏） |

**判据顺序**：`installed_from`（装的是哪份）→ 盘上明文哈希（字节对不对）→ 字段回读（目标字段对不对）→ 进游戏（引擎认不认）。

### 7.5 账本：至少记这七项

| 字段 | 例子 | 为什么必须 |
|---|---|---|
| `build` | `26088801` | 备份 / 安装跨 build 会静默失效；账本不记 build 就没有 staleness 判断 |
| `backup_sha256` | 装前那份的 sha256 | 回滚时验证「备份还是原版」 |
| `installed_sha256` | 装进去那份的 sha256 | 判断盘上是不是我们装的 |
| `installed_from` | `tmp/out/stratagem_eagle_cd4_rearm5.dl_bin` | 「已上机」三件套的第一件 |
| `installed_at` | `2026-10-23T15:06:46` | 与游戏日志 / 崩溃时间对齐 |
| 明文哈希 + 目标字段旧/新值 | `04BBE33EF809862A` / `4.0`、`5.0` | 不依赖封包哈希；换密钥也能复核 |
| 实机读数 | 面板 7→2；回收 150→3 秒多 | 把「改了」升级成「等于预测」 |

### 7.6 部署器只保护「文件身份」，不保护「内容合法」

`install` 只比 sha256、只检查文件存在；它**不**检查：

- 这份 sealed 能不能用 `recipient.sk` 解开；
- 明文是否过内容哈希门禁（G3）；
- `LDLD` 块链是否自洽（G6）。

所以传错文件（甚至传明文）会照装，崩在引擎里。**部署前必须已经走完 §5 门禁与 §6 往返**；部署器不是第二道内容门禁。

### 7.7 两个 writer 争同一张表：基线所有权冲突

| 场景 | 会发生什么 | 处理 |
|---|---|---|
| `SSEO` 与我们交替改同一张表 | `install.lua` 只认自己写过的哈希；当前哈希不在清单里时，它把当前文件当 `original` 存起来并删掉旧 `original` ⇒ Restore 还原出的是**改动版** | 一张表只让一个 writer 管；或把 SSEO 的改动收编成一个补丁 |
| 护甲多被动 mod | 它内嵌 `ORIGINAL_PLAINTEXT`、应用时整体重建覆盖盘上任何第三方改动；取消选择写回 `ORIGINAL_SEALED` | 不要在它管理的表上叠我们的写入；冲突在文件内容层，写运行时加载器救不了 |
| 两个手写脚本 | 后装的覆盖前装的；账本只记最后一次 | 统一走一个部署器 / 一个账本 |

详见 [COMMUNITY-MODS-COMPAT-26088801.md](COMMUNITY-MODS-COMPAT-26088801.md)。

### 7.8 Windows 上怎么跑（PowerShell 等价）

本文的部署段是 bash。用 PowerShell 时逐条换：

| bash | PowerShell |
|---|---|
| `cp a b` / `mv -f a b` | `Copy-Item a b -Force` / `Move-Item a b -Force` |
| `sha256sum f` | `(Get-FileHash f -Algorithm SHA256).Hash.ToLower()` |
| `cmp a b && echo 一致` | `fc.exe /b a b`，或比两个 `(Get-FileHash …).Hash` 是否相等 |
| `python - <<'PY' … PY` | 把那段存成 `readback.py`，再 `python readback.py` |
| `set -euo pipefail` | `$ErrorActionPreference = 'Stop'` |

- `Get-FileHash` 输出**大写**十六进制，账本与本文都是小写，比较前统一大小写。
- **只在 Git Bash / WSL 里照抄 bash 段**：PowerShell 里 `[ -f ]`、`set -euo`、heredoc 都不存在，第一条就报错。
- 工具输出编码：`plain_edit.py` 会自己 `reconfigure(utf-8)`，但 `check_links.py` / `build_cache.py` / `dlbin_seal.py` / `murmur64.py` / `table_dictionary.py` **不会**，在 UTF-8 的 Git Bash 里看到的是 cp936 乱码（实测 `check_links.py` 打「ɨ�� 48 �� Markdown…」）。加 `PYTHONIOENCODING=utf-8` 前缀即可读：`PYTHONIOENCODING=utf-8 python tools/check_links.py`。

---

## 8. 实机验证的三级

**先写预测，再看读数。**「变了」不是结果，「等于我算的那个数」才是。三级证据的强度差一个量级：

| 级 | 证据形态 | 强度 | 真实例子 | 能证明 | 不能证明 |
|---|---|---|---|---|---|
| 1 | **面板可见** | 强 | Eagle 冷却 7→2 秒；使用次数 3；呼叫 4.10 秒 | 引擎运行时读了这个字段 | 面板公式 / 任务内行为 |
| 2 | **任务内计时 / 计数 / 视觉** | 中 | 回收 150→3 秒多；轮数 5→1 落 2 组；散布 36→2 m | 运行时行为真的变了 | 精确系数 / 其他玩家看到的数 |
| 3 | **只能靠日志 / 转储** | 弱 | 三次 `0xc0000005 @ game.dll+0x1083a45`，26–29 秒 | 引擎拒绝了 / 代码路径走到了 | 字段语义 / 正面生效 |

### 8.1 一级 · 面板可见（强）

Eagle 双行改动的面板读数：

| 观察项 | 改前 | 改后 | 判读 |
|---|---:|---:|---|
| 面板「冷却时间」 | 7 秒 | **2 秒** | ✓ `+0x68` 是运行时活字段 |
| 面板「使用次数」 | — | 3 | = vanilla 2 + Expanded Weapons Bay +1；未改动，符合预期 |
| 面板「呼叫时间」 | — | 4.10 秒 | = `+0x54`(0) + 鹰式交付延迟 4.10；未改动，符合预期 |

**本轮的公式当时没解**：通用模型「冷却 = 基础值 × 各升级」按 ×0.90×0.95 算得 15→12.8、4→3.4，与面板的 7、2 对不上；观察到的两点都符合 `floor(base/2)`，但分母无来源。
所以当时这一级只打「字段活」的 ✓、公式打 ⚠。**后续已由 §11.10 解开**：真因子是 ×0.5（Liquid-Ventilated Cockpit）× 0.95（Morale），"÷2" 只是巧合。

面板数还会因玩家升级档不同而不同；判断「生效」必须换回「基础值 × 该玩家升级」，否则会把「生效」误判成「没生效」。

### 8.2 二级 · 任务内计时 / 计数 / 视觉（中）

| 实验 | 预测 | 实测 | 判读 |
|---|---|---|---|
| `EAGLE. REARM +0x68` 150→5 | 3.6–5 秒（`5×0.8=4` 到 `5×0.8×0.9=3.6`） | **3 秒多** | ✓ 字段是回收时间；系数后由 §11.10 定为 **×0.684** |
| 弹幕轮数 `Bombardment +0x18` 5→1 | 1 + 弹幕升级 +1 = 2 组 | **2 组** | ✓ 轮数在实体表，不在战备行 |
| 散布 `Bombardment +0x24` 36.0→2.0 | 弹壳落点集中在小范围 | **全砸在一个小点附近** | ✓ 散布是 f32 米 |

面板上**不显示**的数（轮数 / 散布 / 弹间隔 / 后坐）只能进任务数或计时；它们同样吃升级（轮数 `+1`），换算错了会把「生效」看成「没变」。

### 8.3 三级 · 只能靠日志 / 转储（弱）

| 例子 | 日志 / 现象 | 它能说明什么 | 它不能说明什么 |
|---|---|---|---|
| 校正字落行首的三次崩溃 | `0xc0000005 @ game.dll+0x1083a45`，寿命 26–29 秒，三次同签名 | 引擎在读表阶段拒绝了这份数据 | 具体哪个字段错（只能靠变体对照定位到「行首 8 B」） |
| 资源缺包的爆炸 | 灰色半透明方块 | 代码路径走到了、粒子 id 被用了，但资源不在已加载包里 | 「没生效」—— 它其实是缺包，是免费探针 |
| immediate GUI | 日志计到 3,600 次绘制，屏幕什么都不画 | 代码跑了、调用成功了 | 「可见」—— `is_visible=true` 也不是可见性判据 |

**判据本身不可能失败的测试不是判据。** 第一版外部读内存的判据只看「句柄能不能创建」，而反作弊故意让创建成功 ⇒ 那个判据永远打印 `READABLE`，什么也证明不了（细节见 [MEMORY-ACCESS](../boundaries/MEMORY-ACCESS-25988413.md) §12），修正后必须真的读到一个字节才算数。日志同理：只打印「我调用了」的日志证明不了任何结果。

### 8.4 判读规则

| 规则 | 说明 |
|---|---|
| 先预测后实测 | 预测值写进表里，能被别人复核；只写「变了」等于没验证 |
| 面板 = 基础值 × 该玩家升级 | 冷却两个升级已观察为相乘（×0.90、×0.95）；呼叫 = 基础 + 交付延迟 − 升级；轮数 = 基础 + 升级 |
| 不同玩家不同读数 | 升级档不同，看到的数本来不同；比较必须在同一档位 |
| 面板不显示 ≠ 没生效 | 轮数 / 散布 / 间隔根本不在面板上；进任务 |
| 一次只改一个变量 | 多字段同改无法归因；要改多行就分别记录每行的旧值/新值 |
| 先排除四种非引擎原因 | 面板不显示 / 吃升级 / 部署的不是那个变体 / 缓存被污染 |

### 8.5 「已上机」三件套与作废实验

说「已上机」必须同时给出：

1. **账本 `installed_from`**（装的是哪份产物）；
2. **盘上回读值**（从游戏目录解回来的字段 / 哈希）；
3. **进程 / 转储状态**（正常启动、面板可读、无新崩溃签名）。

缺一条只能写 **`⚠` 已部署未验证**，不能拿它去否定一个正确的假设。

真实反例：按 `+0x3C` 做「改成 2 轮」的实验没见效，事后核对账本发现部署的是**另一个 probe** ⇒ 整次实验作废，**既不能证明也不能反证** `+0x3C` 是轮数。后来轮数在实体表 `Bombardment +0x18` 找到（5→1 落 2 组），才把这条补上。

正例：雾色表改内容后 `0xC000000D`，用**完全相同的原版明文**重新封装不崩 ⇒ 隔离出「崩在内容哈希，不在封装/tag」。这类「只改一个变量」的对照实验才是可引用的证据。

---

## 9. 记账与回滚

### 9.1 记账的五类信息

| 记什么 | 例子 | 不记的后果 |
|---|---|---|
| build + 文件 | `26088801` / `generated_stratagem_settings.dl_bin` | 换 build 后不知道备份是哪版 |
| 备份 / 安装 sha256 | 两份 sha256 | 回滚时无法判断盘上是原版还是改动版 |
| 产物 + 时间 | `tmp/out/stratagem_eagle_cd4_rearm5.dl_bin` / `2026-10-23T15:06:46` | 「已上机」无法复核 |
| 明文哈希 + 字段旧/新值 | `04BBE33EF809862A`；`15.0→4.0`、`150.0→5.0` | 只比封包哈希会误判 |
| 实机读数 + 进程状态 | 面板 7→2；回收 150→3 秒多；正常启动 | 只有「改了」，没有「生效」 |

### 9.2 账本 schema（推荐）

```json
{
  "generated_stratagem_settings.dl_bin": {
    "build": "26088801",
    "backup_sha256": "<装前那份的 sha256>",
    "installed_sha256": "<装进去那份的 sha256>",
    "installed_from": "tmp/out/stratagem_eagle_cd4_rearm5.dl_bin",
    "installed_at": "2026-10-23T15:06:46",
    "plaintext_sha256": "da7f0cb7f9dcfc428ee48419ec97b98c130e442d6eea84e4b43df483cc9356c9",
    "plaintext_murmur64": "04BBE33EF809862A",
    "diff_bytes": 5,
    "readings": { "panel_cooldown_s": [7, 2], "mission_rearm_s": [150, "3.x"] },
    "restored_at": null
  }
}
```

### 9.3 回滚

```bash
# 有部署器
python <private>/dlbin_deploy.py restore --file generated_stratagem_settings.dl_bin

# 没有部署器：从备份拷回，再核哈希
cp "$WORK/backup/$NAME" "$GAME/$NAME"
sha256sum "$GAME/$NAME"                  # 必须 = backup_sha256
python tools/dlbin_seal.py open-key --key <recipient.sk> \
    "$GAME/$NAME" --out "$WORK/restored.plain"
python tools/murmur64.py "$WORK/restored.plain"   # 必须 = 原版锚点
```

回滚后账本改成 `installed_sha = backup_sha`、`installed_from = "(restored)"`、`restored_at = <时间>`；不要删记录，保留「装过什么、什么时候回滚」。

### 9.4 当前账本（只读核对，2026-10-23）

| 文件 | 状态 | `installed_from` | `installed_at` | `restored_at` | 备份 B |
|---|---|---|---|---|---:|
| `generated_entities.dl_bin` | 已 restore | `(restored)` | `2026-10-23T14:17:55` | `2026-10-23T14:49:41` | 47,259,444 |
| `generated_projectile_settings.dl_bin` | 已 restore | `(restored)` | `2026-10-23T13:35:25` | `2026-10-23T14:10:42` | 96,652 |
| `generated_explosion_settings.dl_bin` | 已 restore | `(restored)` | `2026-10-23T13:40:52` | `2026-10-23T14:10:42` | 68,204 |
| `generated_stratagem_settings.dl_bin` | 已装 | `tmp\out\stratagem_eagle_cd4_rearm5.dl_bin` | `2026-10-23T15:06:46` | — | 82,432 |

四份备份尺寸都 = 明文 + 48，反证「封包 = 明文 + 48」这条结构事实。

### 9.5 多表回滚与「零空位」表

- **一次改动跨 N 张表 ⇒ N 条账本、N 次回滚**。只回滚其中一张会留下悬空引用：例如爆炸外观三步链（爆炸行克隆 → 弹丸 `+0x90` 指向克隆行 → 战备 `+0xA8` 指向包），只回滚战备表，弹丸仍指向一个已不存在的克隆行；只回滚爆炸表，战备仍声明一个空包 ⇒ 灰块 / 空效果。
- 回滚顺序建议按依赖反序（先回引用方，再回被引用方），或一次性全回；每一步都核哈希。
- **零空位表**：55 张表里 20 张在 L1/L2 都没有可用空位；`planet_override`（35,474 B）/ `planet_color_set`（1,964 B）/ `weather_color_set`（25,916 B）连 L3 也是 0。tail 自造宿主（战备 `+8` / 实体 `+12`）只在战备 / 实体上实机通过，**逐表未验证**；不要因为「战备能加 8」就假定这 20 张都能。

### 9.6 备份跨 build 的陷阱

备份是**一次性快照**（除非 `--force` 重做）。游戏更新后：

- `live` 变了，`install` 会拒绝覆盖（这是对的，防踩更新）；
- 但「原版备份」仍是**旧 build**；此时 `restore` 会把旧 build 的表装回去，可能直接崩；
- 账本里没有 build 号，也没有 staleness 检测。

规则：**游戏更新后先重新建基线**（`build_cache.py` + `build_diff.py`），确认新 build 的锚点，再决定旧备份还能不能用；不要把旧 build 的 `restore` 当成万能回滚。

---

## 10. 坑清单

**状态列读法**：`✓ 实机` = 进游戏/真实事故里确认；`✓ 离线` = 离线复现或只读源码确认；`✗ 否证` = 这条做法/假设被证伪；`⚠ 未证` = 只知道风险或只做了部分验证。序号连续，便于引用。

### 10.1 十六条主坑（每条都真花过时间）

| # | 症状 | 根因 | 修法 | 状态 |
|---:|---|---|---|---|
| 1 | 启动即崩 `0xc0000005 @ game.dll+0x1083a45`，寿命 26–29 秒 | 校正字写进记录行，把 `+0` 主键与 `+4` 名字 ID 改成随机值 | 只用 tail 宿主；行内宿主必须避开行首 | **✓ 实机** |
| 2 | 整行被抹成 158 个零字节 | `--set 0x979c=158` 被当成「宽度 158 字节」，G4 用同一解析逻辑自证 | 值必须写 `u32:` / `f32:` / `hex:` | **✓ 实机** |
| 3 | `--name "Orbital Laser"` 命中 0 行 | 表里存内部名 `ORBITAL. LASER`，不是面板显示名 | 用内部名；精确优先、否则子串 | **✓ 实机** |
| 4 | 改了「轮数」不生效 | `+0x3C` 是投放方式枚举；轮数在实体 `Bombardment +0x18` | 换表改；先看 [STRATAGEM-FIELDS](../tables/STRATAGEM-FIELDS-26088801.md) | **⚠ 未证** |
| 5 | 明明改了，面板数不对 | 面板 = 基础值 × 该玩家升级（冷却 ×0.90×0.95） | 先换算再判；Eagle 面板另有未解系数 | **✓ 实机** |
| 6 | 面板上看不到变化 | 该字段面板不显示（轮数 / 散布 / 间隔） | 进任务数 / 计时；同样吃升级 | **✓ 实机** |
| 7 | 一次 `--set` 里既有整块 `hex:` 又有块内字段 ⇒ 门禁拒写 | 两块互相覆盖 | 先改好字段，合成一个 hex 块一次写入 | **✓ 离线** |
| 8 | 「已验证生效」结论被推翻 | 部署的不是那个变体（账本指向另一个 probe） | 三件套：账本 + 盘上回读 + 进程状态 | **✓ 实机** |
| 9 | 游戏更新被误报「改了一张表」 | 明文缓存被自己的 mod 负载污染 | dump 前确认 `data/game` 原版；每 build 重跑 `build_cache.py` | **✓ 实机** |
| 10 | 加一行就崩 | `+0` 是连续 1 基主键，复制行沿用原 ID ⇒ 重复键 | 新行 `+0` 取 `max+1`；能不加就不加 | **✓ 实机** |
| 11 | 只改粒子 id，特效不出现 | 引擎要整行一致（克隆），且包要加载 | 整行克隆 + `+0xA8` 指包 | **✗ 否证** |
| 12 | 换了粒子却看到灰色方块 | 代码路径跑了，资源不在任何已加载包 | 灰块 = 缺包，不是「没生效」；这是免费探针 | **✓ 实机** |
| 13 | 工具在 Windows 控制台打印时崩 | 默认 GBK 没有 `⚠`/`✗` | `sys.stdout.reconfigure(encoding="utf-8")`；已内置 | **✓ 离线** |
| 14 | `stratagem_tune.py` 直接退出：找不到 typelib | 它要求 `dl_library.dl_typelib` 与 `--plain` 同目录 | 用 `build_cache.py` 的输出目录，或把 typelib 解到同目录 | **✓ 离线** |
| 15 | 同一份明文封两次，文件哈希不一样 | `seal-key` 每次新随机 ephemeral（epk/tag 都变） | 比内容用明文哈希 / 解封字段，不比封包哈希 | **✓ 实机** |
| 16 | 部署后游戏报 `0xC000000D` | 封装正确但内容哈希没还原 | 回第 4 步保哈希；不是封装问题 | **✓ 实机** |

### 10.2 工具层扩展坑（2026-10-23 只读审计）

| # | 工具 | 坑 | 规避 | 状态 |
|---:|---|---|---|---|
| 17 | `plain_edit` | 文档承诺的 `4:0x11223344` 实测 `ValueError`（`0x` 被交给 `fromhex`） | 用 `hex:11223344` 或 `4:11223344` | **✓ 离线** |
| 18 | `plain_edit` | `4:99` 写出 `00 00 00 99`（十六进制文本语义），和 `u32:99` 的 `63 00 00 00` 不同 | 数值一律用 `u32:` / `f32:` | **✓ 离线** |
| 19 | `plain_edit` | 没有身份字段门禁，可合法改坏 `+0` / locid | 自己按 G7 核 `+0` 与 `+0x28..+0x38` | **⚠ 未证** |
| 20 | `plain_edit` | 不拦 `--out == --plain`，会原地覆盖原始明文 | 输出永远另起路径 | **⚠ 未证** |
| 21 | `ent_set` | 没有 16 B 宽度上限，`hex:` 可一次写任意长；也不校验目标落在哪个块/行 | 偏移从字典算；大块写入前先人工复核 | **⚠ 未证** |
| 22 | `ent_set` | `blocks_of` 只按 `LDLD` + payload 跳，payload 内伪魔数可能被当块；47 MB 多次全表扫很慢 | 依赖「末块到文件尾」断言；一次批量写 | **⚠ 未证** |
| 23 | `stratagem_tune` | `--host-mode row` 仍可达，帮助文本自述「实机已验证会崩」 | 永不传这个开关；默认 `tail` | **✓ 实机** |
| 24 | `stratagem_tune` | 改完不重新解析块链，只改末组 `payload_size` | 之后跑 `dlbin_seal.py blocks` 兜底 | **⚠ 未证** |
| 25 | `stratagem_tune` | 用 `max(g['at'])` 当末组，但没断言它确实是文件最后一个块 | 跑 `blocks` 确认末块结束 = 文件长 | **⚠ 未证** |
| 26 | `stratagem_tune` | 要求明文长度 8 对齐；只认 stride 400 的组 | 先 pad；换 build 先重跑字典确认 stride | **⚠ 未证** |
| 27 | `stratagem_tune` | `row_name` 非 ASCII 返回空串，该行永远匹配不到 | 用 `--type` 或绝对偏移 | **⚠ 未证** |
| 28 | `stratagem_tune` | docstring 与代码脱节（写「G1 长度不变」「行宿主」「G7 三槽」） | 以 `--help` 和源码为准 | **⚠ 未证** |
| 29 | `stratagem_tune` | 旧文档说「`--edit` 串两次会失效」 | **否证**：两次后哈希仍等于原值（82,384→82,392→82,400）；只是基准会漂、payload 每轮 +8 | **✗ 否证** |
| 30 | `murmur64` | seed 硬编码，没有任何一处把 seed 与 build 绑定；传错文件只安静地给另一个哈希 | 每次先对锚点；换 build 重验算法/seed | **⚠ 未证** |
| 31 | `murmur64` | CLI 只能算哈希不能解字；47 MB 全表扫数秒 | 解字 import `padding_word_for_hash`；批量合并写入 | **⚠ 未证** |
| 32 | `table_dictionary` | `sample_rows()` 漏了 `rows`/`rows+blob` 的 `+16`，已发布 MD 的样本列整体错位 | 用 `--json` 几何 + 直接读字节；修复后重生成 MD | **✓ 离线** |
| 33 | `table_dictionary` | MD/JSON 的 build 硬编码 `25988413`；短密钥补零、长密钥截断；无 `--names` 时名字全空 | build 以 `_index.json` 为准；校验密钥长度；提供 names | **⚠ 未证** |
| 34 | `dlbin_seal` | `selftest` 把原 tag 原样搬回，不能证明 MAC 有效 | 用 `seal-key` / `seal-material`；别把「往返一致」当「引擎接受」 | **⚠ 未证** |
| 35 | `dlbin_seal` | `unseal` 用错 stream 只警告，仍写文件并返回 0 | 以哈希为准 | **⚠ 未证** |
| 36 | `dlbin_seal` | `--tag copy` 在明文改过时是失效 tag；`--tag zero` 显然无效 | 只在「引擎不校验 MAC」的未验证前提下考虑；优先 `seal-key` | **⚠ 未证** |
| 37 | `dlbin_seal` | `seal-key` 默认输出去扩展名再加 `.dl_bin`，输入 `x.dl_bin` 会原地覆盖 | 永远 `--out` | **⚠ 未证** |
| 38 | `dlbin_seal` | `--tag` 默认 `copy`，而 `copy` 又必须给 `--from-blob`：默认组合本身不完整 | 显式给全参数，或走 `seal-key` | **⚠ 未证** |
| 39 | `dlbin_seal` | `streams/*.xor` 与 `report.json` 的 epk/tag 是密钥材料；keystream 是 per-file 的 | 与私钥同级保存；换表/换 build 重新取 | **⚠ 未证** |
| 40 | `dlbin_seal` | `selftest` 把流目录写死在 `<root>/streams` | `pairs` 用默认输出目录 | **⚠ 未证** |
| 41 | `dlbin_deploy` | `install` 不校验「能否解密 / 明文哈希 / LDLD 自洽」，传错文件照装 | 部署前走完 §5/§6 | **⚠ 未证** |
| 42 | `dlbin_deploy` | 备份是一次性快照；游戏更新后 restore 旧 build 备份可能崩 | 更新后重建基线；显式 `--force` 重做备份 | **⚠ 未证** |
| 43 | `dlbin_deploy` | 游戏目录与备份根硬编码，没有 `--backup-root` | `--game-data` 指定游戏目录；备份根改源码/自建脚本 | **⚠ 未证** |
| 44 | `dlbin_deploy` | 账本以文件名为键、不记 build；同名跨 build 互相覆盖 | 自己账本加 `build` 字段 | **⚠ 未证** |
| 45 | `dlbin_deploy` | 无账本时 `restore` 不做第三方检查；也不检测游戏进程状态 | 第一次先 `backup`；回滚靠人 | **⚠ 未证** |

### 10.3 语义 / 定位 / 验证扩展坑

| # | 坑 | 事实 | 规避 / 证据 | 状态 |
|---:|---|---|---|---|
| 46 | Eagle 设「无限」 | `+0x50` 直接进 float32 运算，`0xFFFFFFFE`/`0xFFFFFFFF`/`0xFFFFFFFD` 全回绕成 0 | 鹰式不能设无限；非鹰式先特判 sentinel | **✗ 否证** |
| 47 | float32 显示门槛 | `4,294,967,167` 显示 `4,294,967,040`；`4,294,967,168` → 0；≥2²⁴ 时「+1」被舍掉 | 实用上限 2²⁴−1；要「+1」升级就别逼近 2³² | **✓ 实机** |
| 48 | 「这一行不渲染」当成「没人读」 | `(NOT USED)` 行不画面板，但 `+0` 照样参与建索引 | 渲染与建 map 是两条路径 | **✓ 实机** |
| 49 | 单样本否定字段 | 只看 380mm 的 `+84`=6.0 vs 面板 7.45，误判「不是呼叫时间」 | 全表 68 条分层 + 预测 13.45 双命中才定案 | **✓ 实机** |
| 50 | 战备攻击参数找错表 | `num_bombs`/`num_salvos`/`area_size`/`fire_height` 在 400 B 行里四种宽度全 0 命中 | 在 bundle 的战备攻击定义里，不在明文表 | **✗ 否证** |
| 51 | 散布不在战备表 | `Bombardment +0x24`（f32 米）36.0→2.0，弹壳集中 | 早期「不在任何明文表」的结论是被否证的 | **✓ 实机** |
| 52 | 每轮弹数 / 弹间隔 | Napalm 每轮 5、其余 3，但扫遍 400 B 没有「Napalm=5 其它=3」 | 跟弹丸/爆炸数据放一起 | **✗ 否证** |
| 53 | 战备→弹丸数值外键 | 四种编码形式全不命中；`+0x98` 指向 8 B 实体哈希数组，不是弹丸 id | 靠运行时资源名语义跳转 | **✗ 否证** |
| 54 | 加行 ≠ 新增可见条目 | 复制 380mm 到 ID 154 能进游戏，但面板仍只有一条 | 成员资格在 55 张表外 | **✗ 否证** |
| 55 | 雾色表「改内容又保哈希」 | 1 个组；组头 `+16` 在 `0x14` 不 8 对齐，那次行内也没找到可用空位 | 「那次崩」已证（✗）；**tail 自造宿主（pad 4 + 8 = `+12`）在这张表上还没验过，所以「这张表能不能保哈希」仍是 ⚠** | **⚠ 未证** |
| 56 | 「audit 报 0 个校正字」= 真没空隙 | 是类型不在类型库、布局未知；不是 padding 为零 | 先把类型补进字典再判断 | **✗ 否证** |
| 57 | 65,504 B 是格式上限 | 只是「借用别人固定流」的限制；`recipient.pk` + 随机 ephemeral 后长度不限 | 82,432 B 往返一致 | **✗ 否证** |
| 58 | Poly1305 tag 可从明密文对反推 | 一对只给出 `keystream[32:]`；`[0:32]` 永远求不出 | 必须 pk 或 seal-material | **✗ 否证** |
| 59 | 类型名可读 | LTLD v4 有 1,208 类型 / 7,349 成员，但字符串表 0 B | 靠外部类型名清单按哈希反查 | **✗ 否证** |
| 60 | 改 locid 能写任意文本 | 表里只有 32 位本地化 ID；写新文本要动 `.strings` | 只能借现有字符串 | **✗ 否证** |
| 61 | 20 张零空位表都能 tail +8 | 只有战备 / 实体实机；其余逐表未验 | 单表先做一次进游戏测试 | **⚠ 未证** |
| 62 | 块头 L1 可无约束反解 | `wide` 必须仍为 1，需受约束反解 | 优先 tail；L1 未上机 | **⚠ 未证** |
| 63 | 「改了却不生效」的四种非引擎原因 | 面板不显示 / 吃升级 / 部署的不是那个变体 / 缓存污染 | 按这四项先排除，再怀疑字段 | **✓ 实机** |
| 64 | `SSEO` 与我们交替改同一张表 | `install.lua` 只认自己写过的哈希，会把我们的改动当原版存起来 | 一张表一个 writer，或收编成一个补丁 | **✓ 离线** |
| 65 | 护甲多被动 mod 的基线所有权 | 内嵌 `ORIGINAL_PLAINTEXT`，应用时整体重建覆盖盘上改动 | 不要在它管理的表上叠加 | **✓ 离线** |
| 66 | 用 `.patch_N` 覆盖数据表 | `data/game/*.dl_bin` 不在 `bundle_database.data`，是加密松文件 | 只能替换文件本身 | **✗ 否证** |
| 67 | 「只有 5 种资源有 codec ⇒ 只能改 5 类」 | `.patch_N` 替换只需原始字节，引擎按类型选加载器；physics 裸 float32 已证可改 | 不要从 codec 数量推能力边界 | **✗ 否证** |
| 68 | `LoadoutEntry.selectable` 解锁未发布物品 | 发布数据里没有这个组件；可见性由「实体是否挂 LoadoutEntry」+ 后端 id/DLC 决定 | 不是离线可翻的字节；**但战备另有 `+0xC8` 旁路**（不进军械库、直接进任务） | **✗ 否证**（军械库）|
| 69 | 给武器新增独立弹种行 | 四个变体全 `0xC000000D` | 只能改现有行 | **✗ 否证** |
| 70 | EAC 是移除 LuaJIT 的原因 | EAC 是独立进程，改不了引擎的 Lua 实现 | 同一意图、两个改动；别因果误判 | **✗ 否证** |
| 71 | 不存在「声明式包依赖」 | 包头 56 B = 哈希 / 哈希 / 包大小，不是依赖表；三个资产包在 55 张明文表里全表 0 命中；bundle 不是加载单位 | 唯一声明口是 `+0xA8`（以及武器 `+0xF8`）；见 [EXPLOSION-VISUAL](../explosions/EXPLOSION-VISUAL-26088801.md) §7 | **✗ 否证** |
| 72 | `+0xA8` 是唯一包声明口 | 克隆但 `+0xA8` 原值 → 灰块；克隆 + 火粒子包 → 火球；回滚 → 火球消失；自有信号弹 / 下落轨迹正常 | 换外观必须改 `+0xA8` 并确保包已加载 | **✓ 实机** |
| 73 | 火光「归弹丸 / 实体管」 | 曾只改一个字段就下结论；后来证明火光就是爆炸行 `+0x38`，且要整行一致 + 包加载 | 别单字段下结论；见 [EXPLOSION-VISUAL](../explosions/EXPLOSION-VISUAL-26088801.md) 引言 | **✗ 否证** |
| 74 | 资源副本数当「能不能画」的判据 | 同 file_id 平均 5 份（62,915 唯一 id ↔ 322,711 条目）；爆炸 343 的粒子 28 份、380mm 1 份；28 份的照样不画 | 判据是 `+0xA8` 声明的包加载了没有，不是副本数 | **✗ 否证** |
| 75 | 旧 ffi 探针「失败」 | 它检测到 no jit / no ffi 后惰性返回：无崩溃、无报错、无数据 —— 它成功地什么也没做 | 能力缺失必须打一行日志再退出，禁止静默 return | **✗ 否证** |
| 76 | `package.path` 里的 `bin\lua\` 默认不存在 | 写入报 `No such file or directory`；根目录可写且能 require；手工建目录后 `?.lua` 与 `?\init.lua` 都命中 | 部署器先创建目录 | **✓ 实机** |
| 77 | repack 丢容器头 56 B | 新建容器只塞条目会丢「头里的 unknown / 偏移 16 起的 56 B / 每条目 blob 偏移提示」；`Package.parse` 读入再 `to_bytes` 才 IDENTICAL | 改写已有补丁必须「原容器进、原容器出」 | **✗ 否证** |
| 78 | 判据假阳性 | 第一版判据只看「句柄是否创建成功」，而这个判据本身不可能失败 | 判据必须能失败：换成「真的读到一个字节」；教训是方法论级的，细节回指 [MEMORY-ACCESS](../boundaries/MEMORY-ACCESS-25988413.md) §12 | **✗ 否证** |

### 10.4 路线边界（实测于 `25988413`；`26088801` 换了 `helldivers2.exe` / `game.dll`，引擎级结论未在本 build 复验）

| # | 坑 / 否证 | 事实 | 证据 | 状态 |
|---:|---|---|---|---|
| 79 | 进程内 `ffi` 读表 | `_VERSION == Lua 5.1`，`type(ffi) == nil`，`jit`/`bit` 同为 nil | [PROBE-AUTHORING](../engine/PROBE-AUTHORING-25988413.md) | **✗ 否证** |
| 80 | `package.loadlib` 自备 DLL | 自备 DLL 被签名闸门拒绝（不存在 / 未签名 / 签名不在名单，三种都不放行） | [MEMORY-ACCESS](../boundaries/MEMORY-ACCESS-25988413.md) §12 | **✗ 否证** |
| 81 | 自签证书 + 装进系统根存储 | 签名校验变成「有效」也照样不放行；外部小组独立复现 | 同上 §12g | **✗ 否证** |
| 82 | 走引擎插件目录 | 闸门 2 认「名字 + 内容」：同名不同内容不映射且 1 s 终止 | 同上 §12h | **✗ 否证** |
| 83 | 外部进程读内存 / 全量转储 | 反作弊在句柄创建时就把读取权限剥掉；多种替代读法全被拒 | 同上 §1/§2/§8 | **✗ 否证** |
| 84 | 虚拟机 + 宿主读客户机内存 | 反作弊的虚拟机检测挡住（伪装后仍被硬件指纹挡住） | [VM-DUMP](../boundaries/VM-DUMP-25988413.md) | **✗ 否证** |
| 85 | 问引擎「有什么」 | `ResourcePackage` 只有 6 个键不可枚举；`PluginManager` 只列 3 个引擎插件 | [LOADER-SPEC](../engine/LOADER-SPEC-25988413.md) §3 | **✗ 否证** |
| 86 | 载荷请求资源包 | Lua 侧 `stingray.ResourcePackage` 只有 6 个键（load / unload / has_loaded / flush / __index / _name），不能枚举也不能任意预载；跨包驻留只能由 **HD2Runtime by SkyeShade** 走 `game.dll` 的 `RefcountedPackageSystem`（见 §13） | 同上 §3 | **✗ 否证** |
| 87 | 猜 GUI 绑定签名 | `Gui.resolution` 是 `(viewport, window)`，把 Gui 当 Viewport 传 = 原生 AV；immediate 模式调用全成功但屏幕不画 | [GUI-HUD](../engine/GUI-HUD-25988413.md) | **✗ 否证** |
| 88 | 「未发布物品一律不可用」（旧能力边界） | **要分族**：**战备** ✓（`+0xC8` 附赠，7 条实机、含未发布的 M-104）；**武器 / 护甲 / 其它物品** ✗（军械库成员资格在表外，需运行时登记表） | [UNRELEASED-STRATAGEMS](../tables/UNRELEASED-STRATAGEMS-26088801.md) | **✓ 实机** |
| 88 | `pcall` 成功 = 调用成功 | `loadlib`/`loadstring` 失败返回 `nil,message`，只取第一个返回值会记成 `ok=true` | [PROBE-AUTHORING](../engine/PROBE-AUTHORING-25988413.md) §7 | **✗ 否证** |
| 89 | 沿用 LuaJIT 的 `\x` 转义 | stock 5.1 静默丢掉反斜杠，`"\x41"` 变 `"x41"`，载荷照常加载但字节不同 | [LUA51-TOOLING](../engine/LUA51-TOOLING-25988413.md) §3 | **✗ 否证** |
| 90 | `patch_N` 序号可留空洞 | 只留 `patch_3` 时探针报 0/0/6 全 absent；连续态 3/3/3 | [LOADER-SPEC](../engine/LOADER-SPEC-25988413.md)（单次观察） | **⚠ 未证** |
| 91 | `set_resource_override` 缺参当神谕 | 0 参直接 AV，无 minidump；自引用覆盖可把游戏挂死 | [STINGRAY-API](../engine/STINGRAY-API-25988413.md) | **✗ 否证** |
| 92 | 文档索引当穷举 | STINGRAY-API 索引只开了 16 个子表；`stingray` 下实际 125 个命名空间 / 2,483 个成员 | 同上「索引修正」 | **✗ 否证** |

### 10.5 统计

共 **92** 条：`✓ 实机` 19 条、`✓ 离线` 8 条、`✗ 否证` 36 条、`⚠ 未证` 29 条。其中 **16 条主坑** 是这条工作流最常踩的；扩展坑里 **29 条**是工具行为，**33 条**是语义 / 验证 / 资源，**14 条**是路线边界。数字只用于说明覆盖度，不用于给结论加权 —— 一条 `✗` 的否证，价值往往高于十条 `✓`。

---

## 11. 完整实例：一次封装同时改两行（`EAGLE. AIRSTRIKE` + `EAGLE. REARM`）

### 11.1 为什么这是两条独立记录

`EAGLE. REARM` **不是**写在 8 条鹰式空袭行里的字段，它是战备表里**独立的一行**：

| 条目 | 位置 | `+0` type | `+0x50` uses | `+0x54` callin | `+0x60` 未知 | `+0x68` cooldown |
|---|---|---:|---:|---:|---:|---:|
| `EAGLE. AIRSTRIKE` | 组 2 行 3（行首 `0x25A0`） | `0x12` | 2 | 0.0 | 0.0 | **15.0** |
| `EAGLE. REARM` | 组 2 行 8（行首 `0x2D70`） | `0x33`（51） | `0xFFFFFFFF` | 0.0 | 15.0 | **150.0** |

判定依据：`EAGLE. REARM` 的 `+0x68 = 150.0` 与 wiki 的「鹰式回收 150 s / Pit Crew −20% = 120 s / Advanced Crew −10% = 108 s」同构（`150×0.8` 与 `150×0.8×0.9`），与已验证的「冷却升级相乘」模型一致 ⇒ 同一字段、两种语义，随行的用途而变。

> **[STRATAGEM-FIELDS](../tables/STRATAGEM-FIELDS-26088801.md) 现已同步**：那份文档原写着「回收机制在哪个字段未知」，写在本节实验之前；现已在它的 §5.4 / §5.4.4 / §9 里同步为「`EAGLE. REARM` 独立一行、`+0x68` = 回收时间」，并补入 §11.10 的两个系数结论。

> 字段名 `uses_per_rearm` / `rearm_time` 来自 **HD2Runtime by SkyeShade**（其许可证要求引用时显式署名）；本节的数值与实机读数来自本仓库。

### 11.2 先写预测

| 目标 | 预测 | 依据 |
|---|---|---|
| `EAGLE. AIRSTRIKE +0x68` 15→4 | 面板冷却应下降；**具体值故意不预测**（当时公式未解） | 已验证 `+0x68` 是冷却活字段；公式后由 §11.10 解开 |
| `EAGLE. REARM +0x68` 150→5 | 任务内回收 **3.6–5 秒** | `5×0.8=4` 到 `5×0.8×0.9=3.6` |

### 11.3 命令

```bash
python tools/stratagem_tune.py \
    --plain <work>/generated_stratagem_settings.dl_bin \
    --edit "EAGLE. AIRSTRIKE::cooldown=4" \
    --edit "EAGLE. REARM::cooldown=5" \
    --out   <work>/stratagem_eagle_cd4_rearm5.plain.dl_bin
```

一次运行、一次哈希求解、一次封装。**不要**先改一行跑一次，再改另一行跑一次（基准会漂，payload 每轮 +8）。

### 11.4 门禁输出

```
明文 82,384 B  组 12  行 153
目标：组2 行3 type=0x12 'EAGLE. AIRSTRIKE'
目标：组2 行8 type=0x33 'EAGLE. REARM'
宿主：最后一组 payload 末尾追加 8 字节零区 @ 82384（不碰任何记录）
原始哈希 0x04BBE33EF809862A
  EAGLE. AIRSTRIKE  cooldown +104: 15.0 -> 4.0
  EAGLE. REARM  cooldown +104: 150.0 -> 5.0
  PASS  G1 长度  82,384 -> 82,392
  PASS  G2 差异 ⊆ 目标行 ∪ 校正字 (+尺寸字段)  diff=5  目标行 2
  PASS  G3 重算哈希 == 原始哈希  0x04BBE33EF809862A
  PASS  G4 目标字段读回  [('EAGLE. AIRSTRIKE', 'cooldown', 4.0), ('EAGLE. REARM', 'cooldown', 5.0)]
  PASS  G5 其它记录一字节未动  越界改动 []
  PASS  G6 目标行其余字段未变  越界改动的偏移 []
  PASS  G7 身份字段未变  offsets=(0, 40, 44, 48, 52, 56)
```

> 只省略了最后的输出路径提示；数值、顺序、措辞逐字保留。工具打印的是十进制 `+104`，即本文的 `+0x68`。这是**默认模式**（没给 `--set-type`）的 7 行；`--set-type` 时会多一行恒真的 G8「报告重复 key」，那是记录、不是门禁（§5.2）。

### 11.5 字节差异：整份明文只差 5 字节

| 文件偏移 | 旧 | 新 | 属于 | 说明 |
|---:|---:|---:|---|---|
| `0x260A` | `70` | `80` | `EAGLE. AIRSTRIKE +0x68` 高两字节 | f32 `15.0 → 4.0`（低两字节 `00 00` 没变） |
| `0x260B` | `41` | `40` | 同上 | 同上 |
| `0x2DDA` | `16` | `A0` | `EAGLE. REARM +0x68` 高两字节 | f32 `150.0 → 5.0` |
| `0x2DDB` | `43` | `40` | 同上 | 同上 |
| `0x128B0` | `14` | `1C` | 末组 `payload_size` 低字节 | `6,420 → 6,428`（tail 宿主 +8） |
| `0x141D0–0x141D7` | — | `53 92 A9 E4 EE 8D 69 2E` | 追加的 8 B | **校正字**（`0x141D0 % 8 == 0`） |

注意：差异计数是 **5**，不是 13 —— 四个字段字节 + 一个尺寸字节；追加的 8 B 不参与「与原文件逐字节比较」，它们是新长度的一部分。

### 11.6 封装与往返

| 项 | 值 |
|---|---|
| 明文长度 | 82,392 B |
| 明文 `Murmur64A` | `04BBE33EF809862A`（= 原版锚点） |
| 明文 sha256 | `da7f0cb7f9dcfc428ee48419ec97b98c130e442d6eea84e4b43df483cc9356c9` |
| 封包长度 | 82,440 B（+48） |
| 封包 sha256 | `32294d8dbfb3c8a3c3d68cfc3ad608d9547ca7172701218f38237db6cb7041f5` |
| 解回 `_roundtrip.plain` | 与产物 sha256 **相同** |
| 部署器留档 `_installed.plain` | 与产物 sha256 **相同** |

封包哈希只对「这一次封装」有意义（每次新 ephemeral）；跨运行要比的是明文哈希。

**离线复跑核对**（2026-10-23 15:26，本次编写时重跑）：

| 项 | 已部署产物 | 本次复跑 |
|---|---|---|
| 明文长度 | 82,392 B | 82,392 B |
| 明文 sha256 | `da7f0cb7…` | `da7f0cb7…` |
| 明文 Murmur | `04BBE33EF809862A` | `04BBE33EF809862A` |
| 差异字节 | 5 | 5 |
| 门禁 | 7 PASS | 7 PASS |

⇒ 同一条命令、同一份原版明文，产出**逐字节相同**；这不是「看起来一样」，是 sha256 相同。

### 11.7 部署与盘上回读

| 项 | 值 |
|---|---|
| 账本 `installed_from` | `tmp\out\stratagem_eagle_cd4_rearm5.dl_bin` |
| 账本 `installed_at` | `2026-10-23T15:06:46` |
| 盘上回读留档 | `_installed.plain`，sha256 与产物相同 |
| 字段回读 | `0x2608 = 4.0`；`0x2DD8 = 5.0` |
| 明文哈希 | `04BBE33EF809862A` |

> 本文未重新进游戏、也未重读游戏目录；上表引用 2026-10-23 15:06 的部署记录与留档文件。三件套在**当时**齐全。

### 11.8 实机结果

| 观察项 | 改前 | 改后 | 判读 |
|---|---:|---:|---|
| 面板「冷却时间」 | 7 秒 | **2 秒** | ✓ `+0x68` 是运行时活字段（公式后由 §11.10 解开） |
| 面板「使用次数」 | — | 3 | = vanilla 2 + Expanded Weapons Bay +1；未改动，符合预期 |
| 面板「呼叫时间」 | — | 4.10 秒 | = `+0x54`(0) + 鹰式交付延迟 4.10；未改动，符合预期 |
| 任务内回收 | 150 秒 | **3 秒多** | ✓ `+0x68` 在 REARM 行上就是回收时间；系数后由 §11.10 定为 ×0.684 |
| 进程 | — | 正常进游戏、面板可读 | 进程存活；无新崩溃签名 |

### 11.9 三项证据（为什么这一条能打 `✓`）

1. **账本**：`installed_from = tmp\out\stratagem_eagle_cd4_rearm5.dl_bin`，`installed_at = 2026-10-23T15:06:46`；
2. **盘上回读**：`_installed.plain` 与产物逐字节相同（sha256 `da7f0cb7…`），两个字段回读 `4.0` / `5.0`，明文哈希仍 `04BBE33EF809862A`；
3. **进程状态**：正常启动、面板可读、无新崩溃签名。

### 11.10 收口：两个 ⚠ 都解开了（同日第二 / 第三轮）

第一轮留下两个 ⚠。收口的办法**不是再多测几个点，而是选一个能把两种假设分开的基值**。

**① Eagle 面板冷却公式**（第一轮只有 base 15→7、base 4→2，两个模型都吻合）

| 模型 | 公式 | base 15 | base 4 | **base 80（判决点）** |
|---|---|---|---|---|
| **A** | `round(+0x68 × 0.475)` = ×0.5 ×0.95 | 7.125 → **7** ✓ | 1.9 → **2** ✓ | 38.0 → **38** |
| B | `floor(+0x68 / 2)` | 7.5 → **7** ✓ | 2 → **2** ✓ | 40 |

第二轮：把 `EAGLE. 500KG BOMB` 的 `+0x68` 写 **80**（同时给 110mm / Cluster 也写 80 做冗余探针，拥有其中任意一把就能读）。
面板「冷却时间」= **38 秒** ⇒ **模型 A 成立**。

⇒ 那个 "÷2" 是巧合。真正的因子是 **×0.5（Liquid-Ventilated Cockpit，Eagle 冷却 −50%）× 0.95（Morale Augmentation，全体 −5%）**。
base 80 之所以能判决，是因为 80 × 0.475 = **38.0 恰好整数**，两个模型给出不同整数（38 vs 40）。

**② 回收时间的升级系数**（第一轮 base 5 → "3 秒多"，三种假设都落在区间内）

第三轮：把 `EAGLE. REARM +0x68` 从 5 拉到 **100**：

| 假设 | 系数 | 预测 |
|---|---|---|
| 只有 Pit Crew Hazard Pay | ×0.8 | 80 秒 |
| ＋ Advanced Crew Training | ×0.72 | 72 秒 |
| **＋ Morale Augmentation** | **×0.684** | **68 秒** |

任务内回收 = **68 秒** ⇒ **三个升级全相乘**：`×0.8 × 0.9 × 0.95 = ×0.684`。
回验 base 5：5 × 0.684 = 3.42 → "3 秒多" ✓ 一致。

⇒ **面板冷却与回收时间用同一套「相乘」模型，只是升级集合不同**：冷却吃 ×0.5 与 ×0.95；回收吃 ×0.8、×0.9、×0.95。

**③ 副产品：投递延迟是「逐战备」而不是「逐类」**

同一次截图顺带看到 `EAGLE. 500KG BOMB` 面板「呼叫时间」= **3.45 秒**，而 `EAGLE. AIRSTRIKE` 是 **4.10 秒**，
两行的 `+0x54` 都是 0 ⇒ 延迟**不随"鹰式一类"取常数**，而是逐战备取值。把 4.10 当成鹰式常数会算错。

⚠ 仍开：取整规则（68.4→68 与 3.42→3 在 floor / round 下同值）。分辨配方：把基值取到 x.5 附近，
如 `REARM +0x68 = 125` → 85.5（floor 得 85 / round 得 86）。

**收口后状态**：鹰式这条线只剩 `+0x60`（REARM 行 15.0 / 空袭行 0.0）语义未解 —— 面板不可见、价值低，留作 ⚠。

## 12. 未决（按价值排序）

1. ~~鹰式面板冷却公式~~ **已解开**（§11.10）：`round(+0x68 × 0.5 × 0.95)`，base 80 → 面板 38 秒判决。
2. ~~回收时间的升级系数~~ **已解开**（§11.10）：`×0.8 × 0.9 × 0.95 = ×0.684`，base 100 → 68 秒判决。
3. **`+0x60` 语义**：`EAGLE. REARM` = 15.0、`EAGLE. AIRSTRIKE` = 0.0；没有改动实验。先做单行改值，观察面板/任务内是否有可读变化。
4. **20 张零空位表的 tail +8**：逐表进游戏测试；优先 `planet_override` / `planet_color_set` / `weather_color_set`（连 L3 都是 0）。
5. **块头 L1 宿主**：`wide` 必须保持 1 的受约束反解；目前只有设计，没有实机。
6. ~~**`damage_settings` 的宿主方案**~~ **已解**：`DamageInfo` 的零 padding 只是**行内**，推不出「文件内没有宿主」；宿主走「别的无主行的空状态槽」，或者 tail 追加 8 B，见 [DAMAGE-SETTINGS §5](../tables/DAMAGE-SETTINGS-26088801.md#5-宿主策略)。剩下的只是**实机复核**，不是方法缺口。
7. **给武器新增独立弹种行**：四个变体全 `0xC000000D`，根因未定位；在根因清楚前只改现有行。
8. **`table_dictionary.sample_rows` 修复**：把 `rows` / `rows+blob` 加进判定元组，重新生成 `TABLE-DICTIONARY-25988413.md`；否则样本列一直错位。
9. **`stratagem_tune` 补容器重解析**：对齐 `plain_edit` 的 G6，避免只改 `payload_size` 不验块链。
10. **部署器内容预检**：`install` 前增加「能否解密 + 明文哈希门禁 + `LDLD` 自洽」三项；账本加 `build` 与备份 staleness。
11. **seed / build 绑定**：`murmur64` 的 seed 硬编码，工具链没有任何一处把它与 build 号绑定；换 seed 时全部门禁会静默通过。
12. **更多表的锚点**：目前只记录了 5 张表的明文 `Murmur64A`；建议另行留档全表 55 张的锚点（`_index.json` 目前只有 sha256，没有 Murmur），换 build 时逐表比对。

---

## 13. 追溯与许可

本文引用的以下事实来自 **[HD2Runtime by SkyeShade](https://github.com/SkyeShade/HD2Runtime)**：

- `+0x50` 作为「每次回收次数」（`uses_per_rearm`）的语义；
- 鹰式 `uses_per_rearm` / `rearm_time` 两个字段名；
- 「爆炸行带粒子与音效成员」这条结构结论；
- 「跨包驻留由 `game.dll` 的 `RefcountedPackageSystem` 完成」这条结论。

其许可证在 MIT 之外有自定义条款：**引用其偏移 / 字段名 / 清单需显式署名**。本文的实测、失败读数与否定证据是本仓库自己的。

wiki（helldivers.wiki.gg）只用于交叉核对字段语义与参考数值，未复制其数据表；外部 SDK / 社区 mod 的引用只用于定位线索，结论以本 build 的实机 / 离线证据为准。

**密钥材料一律自备**：需使用者自备 `recipient.pk` / `recipient.sk`，本仓库不提供；`pairs` 产出的 `streams/*.xor`、含 epk/tag 的 `report.json` 与私钥同级，绝不入仓。本文不包含游戏资产、mod 补丁二进制、47 MB 实体库或全量 dump；出现的尺寸 / 哈希只用于验证解析与回滚。

---

## 14. 变更记录

| 日期 | 改了什么 |
|---|---|
| 2026-10-23 | 首版：八步流程、四张表锚点、宿主选择的三次崩溃、EAGLE 双行案例、16 条坑 |
| 2026-10-23 | 本版：按「适用范围 → 取明文 → 定位 → 保哈希 → 门禁 → 封装 → 部署 → 验证 → 记账 → 坑 → 实例」重排；补 2026-10-23 工具只读审计（29 条）、语义 / 资源扩展坑（33 条）、路线边界（14 条）；修正 Eagle 校正字偏移为 `0x141D0`；否证「`--edit` 串两次会失效」；补部署三件套 / 盘上回读 / 多 writer 冲突；明确 `dlbin_deploy.py` / `ent_set.py` 未随仓库发布 |
| 2026-10-23 | 复核修订：删掉会照抄必崩的 `--appmanifest` 路径；新增 §1.2.1（取密钥来源与本仓库不能凭空 bootstrap）、§2.5（哈希 == 锚点识别不了保哈希的 mod）、§2.6（无密钥预演）、§7.8（PowerShell 等价）；§3.1 改为「LDLD 三种形态 / 43 张可写」，§4.6 点名 7 张「尾部残留」表；§4.7 末块算术与 `+12` 落实机；§5.2 门禁改为「默认 7 行 / `--set-type` 8 行」并点明 `stratagem_tune` 的 G6 是记录级；§9.4 补 `installed_at` / `restored_at`；§10.3 #55 从 `✗` 降为 `⚠`；§10.4 去掉可照做的操作细节并标 `25988413`；§3.5 拆开「换爆炸」与「换弹头」；`+0x54` 的分层口径改为「111 行非零 + 差值分层」 |
| 2026-10-23 | **架构定型：本文件与 `docs/` 成为唯一知识库，技能只留方法论**。① 删除 `tools/extract_seal_material.py`（借第三方 mod 固定 ephemeral 的方案已弃用，`max_len` 卡 65,504 B）并移除 `DLBIN-SEALED-BOX` §7 里印着的 `epk` / `poly` 十六进制（`poly` = Poly1305 密钥，属密钥材料）；② §1.2.1 由「三条来源」改为「两条」，并写明**一份旧 build 转储即可自解**；③ 删除 `refs/filediver-strings.go`（BSD-3 源码拷贝、全仓 0 引用、能力已由 `stratagem_display_names.py` 独立重实现）；④ 技能 `SKILL.md` 由 499 行重写为 213 行的纯方法论 + 知识库索引 |
| 2026-10-23 | **伤害表打开**（`26088801`）：`damage_settings` 的四处「零 padding 无宿主」改成「行内零 padding、宿主在别的行」（§0 / §3.5 / §12 #6）；§2.3 加第 5 张锚点 `D03587CCBD2FECFC`；新增 [DAMAGE-SETTINGS](../tables/DAMAGE-SETTINGS-26088801.md)（字段图 / 5 张引用表 / 共享行 / 宿主策略） |
