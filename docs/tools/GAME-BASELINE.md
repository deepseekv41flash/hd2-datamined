# GAME-BASELINE：盘面基线（`game-baseline.json`）自检

> 工具 **`tools/game_baseline.py`** · 基线示例 **[`baselines/game-baseline-26251122-vanilla.json`](../../baselines/game-baseline-26251122-vanilla.json)**
> 思路借自第三方大型外观系统 HD2IAS 的「记录 bundle 库 sha 基线 + 每次启动自检」
> （见 [RECON-HD2-INTEGRATED-ARMOR-SYSTEM](../cases/RECON-HD2-INTEGRATED-ARMOR-SYSTEM.md) §3.2），
> 这里是数据表路线用的通用版。

## 0 一句话

把「盘面现在是什么状态」变成一份可 diff 的 JSON：**哪个表被改过、哪个 `patch_N` 是谁的、游戏有没有更新**。
四个子命令：`snapshot`（记录）/ `check`（核对）/ `show`（摘要）/ `selftest`（变异自检）。

```bash
python tools/game_baseline.py snapshot --out baselines/game-baseline-26251122-vanilla.json \
    --build 26251122 --label vanilla --no-patches \
    --override game/generated_entities.dl_bin=D:/mod/backups/<原版实体表>.dl_bin

python tools/game_baseline.py check --baseline baselines/game-baseline-26251122-vanilla.json
python tools/game_baseline.py check --baseline <baseline> \
    --artifact game/generated_entities.dl_bin=out/thmixed/generated_entities.dl_bin
```

## 1 它记录什么（`HD2GameBaseline/1`）

| 类别 | 文件 | 方式 |
|---|---|---|
| **数据/引擎文件** | `data/game/*`（57 个：50+ 张 `*.dl_bin` + `dl_library.dl_typelib` + `game.dll`） | 全量 sha256 + size |
| **关键数据文件** | `data/bundle_database.data`、`data/bundles.nxa`、`data/bundles.region_hints` | 全量 sha256 + size |
| **补丁** | 全部 `*.patch_*`（主文件 + `.gpu_resources` / `.stream` 伴生） | 按 `<host>.patch_<N>` 分组，逐件 sha256 |
| **大归档/安装物** | `bundles.00..29.nxa`（单个数百 MB）、data 根的 `<16hex>` / `<16hex>.stream` 安装 blob | **只记 size**（不读 20 GB） |
| **构建指纹** | `game/game.dll` + `game/dl_library.dl_typelib` 的 sha256 | 判「是不是同一个 build」 |

基线 JSON 只有哈希与尺寸，**不含任何游戏资产**，可以进仓库/分享。

## 2 三个使用场景

### 2.1 装盘前后：证明「盘上装的正是我的产物」
```bash
python tools/game_baseline.py check --baseline baselines/game-baseline-26251122-vanilla.json \
    --artifact game/generated_entities.dl_bin=out/ems120/generated_entities.dl_bin
# ✓ 构建相同 → 「~ game/generated_entities.dl_bin 45.1 MiB 4121f332… → 4d0174f4…」
# 产物断言 … ✓ 盘上文件 == 产物
```

### 2.2 游戏更新后：判断哪些补丁过期
先 `snapshot` 新基线（`--build <新号>`），再拿旧基线 `check`：
- **构建指纹变** ⇒ 不是同一 build ⇒ 先按 [BUILDS.md §3](../../BUILDS.md) 三步复验；
- `bundles.NN.nxa` 尺寸变 ⇒ 包体更新过；
- `game/*.dl_bin` 被改且不是你的补丁 ⇒ 官方改表了（对照 [BUILD-26251122-DIFF](../builds/BUILD-26251122-DIFF.md) 一类文档）。

### 2.3 回滚验证
```bash
cp /d/mod/backups/spray-capsule/generated_entities.vanilla.dl_bin "<game>/data/game/generated_entities.dl_bin"
# 删掉 patch_* 后
python tools/game_baseline.py check --baseline baselines/game-baseline-26251122-vanilla.json
# ✓ 盘面与基线完全一致（无漂移），exit 0
```

## 3 判读表

| 现象 | 含义 | 动作 |
|---|---|---|
| `✗ 构建不同` | 游戏更新了 / 基线不是这版 | **先**按 [BUILDS.md §3](../../BUILDS.md) 三步复验并重建基线，别继续套旧补丁 |
| 只有 `game/*.dl_bin` 改动 | 数据表补丁（我们这条路线） | 正常；用 `--artifact` 核对是不是自己的产物 |
| 多出 `*.patch_*` | 已部署的资源补丁 | 按组名 `<host>.patch_<N>` 对账；删除时连 `.gpu_resources`/`.stream` 一起 |
| `bundles.NN.nxa` 尺寸变 | 游戏内容/打包更新 | 资源补丁可能过期，重打 |
| 归档缺失 / 新增 | 安装不完整 / 换了盘 | Steam 校验完整性后重建基线 |
| 退出码 | `0` 干净 · `1` 漂移 · `2` 用法/IO 错误 | CI 或脚本可直接用 |

## 4 当前基线（build `26251122`）

- 文件：`baselines/game-baseline-26251122-vanilla.json`
- 规模：**60 个全量哈希（111.8 MiB）+ 60 项尺寸清单 + 0 个补丁组**（vanilla 期望无补丁）
- 构建指纹：`dl_library.dl_typelib = 4d4db6e7a057b9e5…` · `game.dll = 61dcfcd201dacbf3…`
- 生成方式：采集时盘上已有实验补丁，因此用 `--override game/generated_entities.dl_bin=<原版备份>` 把实体表换回原版哈希、
  并 `--no-patches` 表示「vanilla 期望没有补丁」。
- 2026-10-31 实测（盘上装的是「7 发 7 弹种」实验 + 6 个资源驻留包）：
  - `✓ 构建相同`；`改动 1`（`game/generated_entities.dl_bin` 4121f332… → 4d0174f4…）；`60 项归档尺寸全部一致`；
  - `补丁 21 组`（`f6fb08cc02d24255.patch_0…10` + 其它实验残留）、产物断言 ✓、exit 1 —— 与预期完全一致。

## 5 边界与已知限制

- 大归档**只比 size**（换 build 时够用、也快；同尺寸更新会漏）——需要强校验时单独 `sha256sum`。
- 只扫 `data/` 根 + `game/` 一层（游戏 data 目录只有 `game/` 一个子目录）。
- 补丁按 `<16hex>.patch_<N>` 分组；命名不符的文件进尺寸清单，不会漏报、但不会分组。
- **不记录 mtime**：内容一致即判「相同」（故意如此，换备份不算漂移）。
- `--override` 是给「从已知好备份重建基线」用的；它只替换 `files` 里那一条，不校验其它字段。

## 6 自检（变异测试，15 项）

```bash
python tools/game_baseline.py selftest
# 临时夹具：造盘 → snapshot → 分别变异
#  PASS 未变异 → exit 0 / 改表 → 1 / 缺文件 → 1 / 多补丁 → 1 / 归档尺寸变 → 1 / 构建指纹变 → 1
#  PASS 产物断言：一致 → 0 / 不一致 → 1 --no-patches 基线 + 盘上有补丁 → 1
# 自检：15 PASS / 0 FAIL
```

## 7 与其它工具的关系

| 场景 | 配合 |
|---|---|
| 数据表装盘 | 手动 `cp` 密封文件后 `check --artifact`（同 [FILE-ROUTE-WORKFLOW](../cases/FILE-ROUTE-WORKFLOW-26088801.md) 的 8 步链） |
| 资源补丁装盘 | `whole_package_patch.py build --install` 之后 `check` 看补丁组是否按预期多出 |
| 换 build | `snapshot` 新基线 + [BUILDS.md](../../BUILDS.md) 三步 + [INDEX §2 builds](../../INDEX.md#builds) 登记 |
| 回滚 | 恢复备份 → `check` 应回到 `0` |
