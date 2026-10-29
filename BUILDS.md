# 换 build：操作手册

> **本文件只讲「换 build 怎么做」**：新 build 到手跑哪几步、哪些结论能直接沿用、锚点怎么复验、基线放哪。**各 build 的验证记录不在本文件** —— 逐层记录与跨 build 对照表在 [INDEX §2 的 `builds/` 小节](INDEX.md#builds)。
>
> 当前验证 build **`26251122`** ｜ 历史基线 `25480438` → `25988413` → `26088801`。仓库不绑定某个 build（热点更新一两周一次）：**工具与方法论**文档不带 build 号，**事实类**文档文件名带 build 号（见 §2 末）。

## 1. 这份文件管什么

管**操作**（顺序与判读 §3、哪层结论能沿用 §2、锚点复验 §3.1、基线产物 §4、加新 build 改哪些文件 §5）；不管**记录与事实**（某个 build 到底改了什么 → [INDEX §2 `builds/`](INDEX.md#builds)；某条结论的证据 → 各主题文档，入口 [INDEX §1](INDEX.md#1-按问题找)）。

## 2. 哪些结论跨 build，哪些必须逐 build 复验

| 层 | 例子 | 跨 build？ |
|---|---|---|
| **结构 / 格式** | `.dl_bin` 密封盒（`明文+48 B`）、内容哈希（MurmurHash64A, seed `0xDEADBEEFABAD1DEA`）、`LDLD` 组头（数组型 `0x10\|count` 与单记录型两种）、实体块序列与 hashmap 键、`.strings` 格式与 `ThinHash`、行内「本地化 ID」机制、行命名（指针 vs 位置） | ✓ 跨 build（25988413 → 26088801 实测不变，密钥也没变） |
| **字段 / 偏移** | 「战备 `+104` 是冷却」「弹丸 `+8` 是显示名 ID」「实体 `+576` 是备选弹丸」 | ⚠ 必须逐 build 复验：类型库逐字节一致才敢直接复用，否则重跑字段定位 |
| **地址 / 常量 / 补丁码** | RVA、内存地址、注入点、patch 字节 | ✗ 基本每 build 必变，必须重新推导 |

**命名跟着效力走**：事实类 `docs/<主题>-<buildid>.md`（开头写清偏移只在该 build 实测）；方法类不带 build 号（`docs/engine/DLBIN-SEALED-BOX.md`、`docs/cases/PRIOR-ART-NAMING.md`）。

## 3. 新 build 到手后的三步（全离线，不启动游戏）

```bash
# 0) 先确认基线缓存干净 —— 否则后面两步全错（坑见 §6）
python tools/plaintext_cache_audit.py --sk <recipient.sk>  # -> refs/cache-audit.json
# 1) 当前 build 的 55 张表 + 类型库解封成明文，按 buildid 另存
python tools/build_cache.py --sk <recipient.sk>          # -> refs/dlbin/plaintext-<buildid>/
# 2) 逐表回答"变了没"：文件层 -> 封装层（比明文哈希）-> 结构层（组数/行数/步长）
python tools/build_diff.py --sk <recipient.sk>            # -> refs/build-diff.json
# 3) 用旧 build 的字典几何对照全部 55 张表（没旧明文的表也能证到"结构没变"）
python tools/build_geometry_diff.py --sk <recipient.sk>   # -> refs/build-geometry-diff.json
```

判读规则：

* `changed = 0` 且密钥仍能解 → 现有工具与文档的**结构层**结论可以直接用；
* 只要有一张表 `changed` → 那张表的行号/偏移全部作废，重跑 `tools/table_dictionary.py` 与对应的定位工具；
* `structure-same` 只证明「大小 + 组数」没变，**不能排除同尺寸下的数值改动**。

### 3.1 锚点复验（沿用旧偏移之前的最后一道闸）

沿用旧偏移之前，明文哈希必须等于**留档的锚点**：`python tools/murmur64.py <解出的明文>`。五张表的锚点与三个自检见 [WORKFLOW §2.3](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md)；这五张在 `25988413 → 26088801` 之间明文逐字节相同（`refs/build-diff.json` 里 `status` 全为 `same`），所以旧锚点可以直接沿用。
对不上就停，只有三种原因：build 不是这个 / 解到了自己部署的 mod 负载 / `--key` 用错。**其余 50 张表的 `Murmur` 锚点尚未留档**（`_index.json` 只记 sha256），它们的跨 build 复验只能走 `build_diff.py` 的明文哈希对照。

## 4. 基线产物放在哪

| 文件 | 是什么 | 属于哪个 build |
|---|---|---|
| `refs/table-geometry.json` | 55 张表的几何（明文大小 / 组数 / 行数 / 步长 / 类型） | 25988413（26088801 与 26251122 实测结构仅 2 张变，仍是有效基线） |
| `refs/build-diff.json` | 某一次「旧 → 新」的逐表 diff | 25988413 → 26088801 |
| `refs/build-geometry-diff.json` | 55 张表对旧几何的对照结果 | 26088801 |
| `refs/build-diff-26251122.json` | 26251122 的逐表 diff（文件/封装/结构三层） | 26088801 → 26251122 |
| `refs/build-geometry-diff-26251122.json` | 26251122 对旧几何：53 张结构同 / 2 张变 | 26251122 |
| `refs/dlbin/plaintext-<buildid>/` | 该 build 的解封明文（本地，不入库） | 按目录名 |

build 再多起来时，按 `refs/builds/<buildid>/` 分目录，把上述产物各存一份。

## 5. 加一个新 build 时改哪里

1. 先跑 §3 三步 + §3.1 锚点复验（产物落 `refs/`，§4），再把逐层记录写成 `docs/builds/BUILD-<buildid>-DIFF.md`：只写「相对上一个基线变了什么、哪些旧结论作废、三态小结」（样例：[BUILD-26088801-DIFF](docs/builds/BUILD-26088801-DIFF.md)）；
2. 在 [INDEX §2 `builds/`](INDEX.md#builds) 的**跨 build 对照表**加一行，再在紧跟其后的逐篇表加一行；
3. 本文件只在**操作流程**变了时才改（多一步、判读规则变了）—— 记录一律不进这里，这正是它不必每次更新都改的原因；
4. 同步「当前验证 build」：本文件顶部、[README](README.md)、[INDEX](INDEX.md) 顶部、[WORKFLOW §1.2](docs/cases/FILE-ROUTE-WORKFLOW-26088801.md) 的判据。
5. 把**工具默认路径**切到新明文：`grep -rl plaintext-<旧build> tools/*.py | xargs sed -i 's/plaintext-<旧build>/plaintext-<新build>/g'`（26251122 这次动了 29 个文件）；再用 `entity_dump.py` / `block_rows.py` 各跑一次冒烟。
6. 若 4 张以上表尺寸/内容变了，重跑 `build_geometry_diff.py` 与 `build_diff.py` 刷新 `refs/` 下的缓存，别让下个 build 拿旧缓存当基线。

## 6. ⚠ 踩过的坑：明文缓存会被我们自己的 mod 污染

`refs/dlbin/plaintext-all/` 是「某个 build 的原版明文」。只要有一次 dump 发生在**我们的 mod 已经写进 `data/game` 之后**，缓存里就会混进改过的表 —— 之后所有「这张表变了没」的判断全错，而且错得很有说服力。

**实例（2026-10-22）**：09:49 为「护甲多被动」实验生成了 mod 负载，09:52 的 dump 把**已部署的负载**当成原版存下（`customization_passive_bonuses` 4992 B，真原版 4016 B）；当天更新到 26088801 后，被误报成「这次更新改了一张表」。完整复盘与 sha256 铁证 → [BUILD-26088801-DIFF §0](docs/builds/BUILD-26088801-DIFF.md)。

1. dump 前确认 `data/game` 是原版（有 `refs/dlbin/demo/vanilla_*` 备份就逐字节比），dump 后立刻跑 `tools/plaintext_cache_audit.py`；
2. 改表实验的负载一律留在 `refs/dlbin/demo/`，**永远不要**写进缓存目录。
