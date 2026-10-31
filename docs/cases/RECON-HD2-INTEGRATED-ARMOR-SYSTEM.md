# 侦察：HD2 Integrated Armor System（第三方护甲外观系统，2026-10-31 状态）

> 来源：<https://github.com/Estecsky/HD2-Integrated-Armor-System>（284 MB 仓库，54★，建 2026-09-29，最后推送 2026-10-31T06:07Z）
> **只读侦察**：只看了仓库文件 + 客户端更新包里的字符串/配置；**未安装、未运行它的 exe**。
> 本地副本：`D:\mod\refs\third-party\hd2ias\`（README / UPDATE_HISTORY / feed / client-config / announcements + `rel/v131/app/` 客户端 4 文件）。

## 0 一句话

这不是数据表研究仓库，也没有开源代码：它是**护甲外观幻化系统**的发布仓库（RSA 签名更新 feed + 安装器/离线更新包，
客户端是闭源 .NET 8 WinUI3 程序）。对我们的价值只有四样：①`.patch_N` 部署模型在大型第三方项目里的完整用法（旁证）；
②它的**自检/基线管理**（bundle 库 sha）值得借鉴；③一批实机踩坑结论；④分发基建模板。
**没有可直接复用的数据字段 / 表结构 / dl_bin 改法。**

## 1 仓库构成（✓ 实测 GitHub API + 文件）

| 组成 | 内容 |
|---|---|
| 顶层 6 文件 | `README.md` / `UPDATE_HISTORY.txt`（11 KB，版本史）/ `feed.json` / `client-config.json` / `announcements.json` / `.gitignore` |
| `updates/` | **28 个更新包**（1.0.4 … 1.4.7；15 MB → 70 MB 级） |
| Releases | 安装器 `.exe`（V1.2.2 589 MB / V1.3.3 718 MB / **V1.6.0 271 MB**）+ 部分版本离线更新 zip |
| 客户端 | .NET 8 / WinUI3（WindowsAppSDK 1.8）+ WebView2；主 `dll` 782 KB、`exe` 290 KB（✓ 解包 1.3.1-direct：4 个文件 = 3 个 app 文件 + `update_notes.json`） |
| 当前版本 | **1.6.0**（2026-10-31 发布；`distribution: installer_only`） |

## 2 它是怎么实现的（✓ 客户端字符串 + 更新日志，未实机）

更新日志 1.4.0 明确写了「**Lua 和原生双路线**」，加上数据包：

| 层 | 组件 / 文件（均来自客户端 DLL 字符串） | 作用 |
|---|---|---|
| **原生 / ReShade addon** | `bin/HD2IndependentRig.addon64`、`HD2PreviewRuntime.addon64`、`HD2TransmogResources.addon64`、`HD2BinShadowTest.addon64`、`HD2TransmogBackend.dll` | 游戏内渲染/骨骼 hook + F4 / ReShade 面板（README 注明「MDL 作者提供的系统生效方案」） |
| **Lua 路线** | 依赖 **Bingus Shared Loader v15/v17/v18/v19**；部署 `data/9ba626afa44a3aa3.patch_0`（`boot_template.patch_0`）+ 生成 `9ba626afa44a3aa3.patch_1`；`mods/hd2ir/runtime`；`resource_shadow/` 保留副本 | 用社区 Lua 宿主做 rig/姿态 hook |
| **数据包** | 「生成 data 包 / 独立索引 / `HD2 LUA.zip`」，Arsenal 导入替换 | 把资源打成 `data/<16hex>.patch_N` |
| 自研资产格式 | `.rigbin` / `.hd2phys` / `.hd2shared` / `.hd2preview` / `.hd2pose` / `.hd2author` / `.hd2irpack.zip`；`shared_[24hex].canonical.rigbin`、`requires-shared-v2` | 独立 rig（骨架/姿态/物理）资源 |
| 基线管理 | 引用 `data/bundle_database.data`、`data/bundles.nxa`；记录 `bundle_database_sha256` / `bundle_mapping_sha256` / `managed_bundle.json` / `bundlesHash` | 部署/自检时对**盘面基线**做核对 |
| 部署校验 | 正则 `^data/[0-9a-fA-F]{16}\.patch_[0-9]+(\.stream|\.gpu_resources)?$`、`9ba626afa44a3aa3\.patch_[01]`；文案「主文件必须从 patch_0 连续编号」 | 同我们的 `.patch_N` 纪律 |
| 更新/签名 | `feed.json` = base64(JSON) + **RSA-3072 签名**（`client-config` 里 384 B modulus + `AQAB`）；`latest_sequence` 单调递增；安装器条目带 `sha256`+`bytes`；公告四语言；离线包 `update_notes.json` 带 `localized_notes` + `manual_actions` | 可抄的分发结构 |

## 3 对我们有用的（按价值排序）

### 3.1 `.patch_N` 部署模型被大型第三方逐条复现（✓ 旁证，不是新知识）

- 资产层 = `data/<16hex>.patch_N` + `.gpu_resources` / `.stream` 三件套，与我们 [RESOURCE-RESIDENCY](../engine/RESOURCE-RESIDENCY-26088801.md)、`whole_package_patch.py` 完全同构；
  「主文件从 patch_0 连续编号」= 我们的 G6 门禁。
- Lua 宿主 = `9ba626afa44a3aa3.patch_N`（我们盘上 `patch_0` 是 Bingus loader）；他们用 **patch_1** 再叠一份 → 说明多份可共存，顺序由 Arsenal 管。
  与 [LOADER-SPEC](../engine/LOADER-SPEC-25988413.md) / [LUA-API](../engine/LUA-API-25988413.md) 一致。

### 3.2 可借的「自检 / 基线」设计（⚠ 未验证其内部机制）

- 他们记录 `bundle_database.data`（本 build 186,515 B）与 `bundles.nxa` 的 sha 基线到 `managed_bundle.json`，客户端做统一自检 ——
  目的很可能是**游戏更新后识别「包/数据库变了、旧部署失效」**。
- 对我们：`dlbin_deploy` / 资源补丁工具目前只有「备份 + restore」，没有「盘面基线清单」。
  可加一份 `game-baseline.json`（build 号 + 关键文件 sha256），一键回答「这盘是不是原版 / 哪个补丁过期」。
- ⚠ 注意别误读：本仓库已证 `.dl_bin` 是松文件、**不在 `bundle_database`**（[WORKFLOW §10.3](../cases/FILE-ROUTE-WORKFLOW-26088801.md)）；
  他们的 sha 基线是**资源层/自检**用途，**不是**加载前提。

### 3.3 掉坑清单（可进我们的 prior-art / 93 条坑）

来源：`UPDATE_HISTORY.txt` 1.0.6–1.4.6 的逐版修复说明。

- 资源覆盖类 mod 互相冲突；「同套护甲只能部署一个 mod」「只保留一份 data 包 / Lua 包」「只保留一份 Bingus」。
- **跨归档重复但内容完全相同的 Unit 被误判为冲突**（去重语义问题；我们的多包同资源副本也遇过类似坑）。
- **十进制目标骨骼 ID 被再次当作名称哈希** → 骨骼匹配失败（id / hash 双形态坑，我们资源层同样适用）。
- 幻化支持包显存 2–3 GB → 1.4.0 删掉后「几乎归零」⇒ 资源包体量/常驻代价的实测旁证。
- 游戏更新 / EAC 更新会让整套系统失效（1.4.x 之前反复修，1.6.0 才恢复）⇒ 我们的补丁同样要「按 build 锁基线 + 可回滚」。

### 3.4 分发基建模板（低优先，可抄结构）

`feed.json`（schema/sequence/distribution/release_url/installer{sha256,bytes}）+ `announcements.json`（多语言）+
离线包内 `update_notes.json`（`localized_notes` + `manual_actions`）+ 安装器带 sha256。
若我们以后要把数据 mod 发给一组人，这套字段设计可直接照抄，不需要他们的客户端。

### 3.5 能力边界确认（✓ 与本仓库既有结论一致）

- 外观 / 骨骼级改动 = **运行时（Lua / 原生 addon）域**。issue #1 里另一个作者做的 **「Blink Framework」是 Bingus Lua 模块，每帧写头部骨骼旋转**；
  ⇒ 印证「armor 外观」不是 dl_bin 能做的（我们的 [ARMOR-KIT-WEIGHTS](../tables/ARMOR-KIT-WEIGHTS-26088801.md) / [ARMOR-PASSIVE-STATS](../tables/ARMOR-PASSIVE-STATS-26088801.md) 只覆盖**数值**）。
- 他们同样用 `.patch_N` 放资源包，但**没有暴露任何表偏移/字段语义** → 数据表线零可回收。

## 4 明确用不上的

- 无源码（.NET 客户端闭源 + `addon64`/`dll` 二进制）；无表结构/字段图；无 dl_bin 改法；`.hd2irpack`/`rigbin` 等私有格式无文档。
- 安装器/离线包体积巨大（70–718 MB），且 1.5+ 是「安装器 only」⇒ 不适合拿来做对照实验。

## 5 可执行跟进（我们这边）

| # | 事项 | 目的 | 优先级 |
|---:|---|---|---|
| 1 | 给 `dlbin_deploy` / `whole_package_patch` 增加「盘面基线清单」（`game-baseline.json`：build + 关键文件 sha） | 游戏更新后一键判断哪些补丁过期 | **✅ 已实现（2026-10-31）**：[`tools/game_baseline.py`](../../tools/game_baseline.py) + [GAME-BASELINE](../tools/GAME-BASELINE.md)（`snapshot`/`check`/`show`/`selftest`，带 15 项变异自检；首份基线 `baselines/game-baseline-26251122-vanilla.json`） |
| 2 | 验证 `9ba626afa44a3aa3.patch_1` 与 patch_0 共存条件（我们盘上只有 patch_0） | 以后若要在 Lua 侧叠工具（HUD/调试） | 低 |
| 3 | 若要研究外观方向：把 `.hd2irpack` / `rigbin` 当第三方「资产容器」样板（另立课题） | 外观路线可行性 | 低 |

## 6 证据与复算

- 本地：`D:\mod\refs\third-party\hd2ias\`（6 个文本文件 + `rel/v131/app/` 客户端 4 文件 + `rel/1.3.1-direct.zip`）
- 采集命令：
  ```bash
  gh api "repos/Estecsky/HD2-Integrated-Armor-System/git/trees/main?recursive=1"
  gh api "repos/Estecsky/HD2-Integrated-Armor-System/contents/<path>" -H "Accept: application/vnd.github.raw" > out
  unzip -l rel/1.3.1-direct.zip
  # 客户端字符串扫描：ASCII + UTF-16LE 双份，筛 rig/bundle/lua/patch_ 关键词
  ```
- 解码 `feed.json`：`payload` = base64(JSON)，`signature` 384 B = RSA-3072；`client-config` modulus 384 B / exponent `AQAB`。
- **下载限制**：GitHub release 资产与大更新包在本机极慢（1.3.3 的 9.6 MB 离线更新包只下到 3.5 MB 即被截断，zip 不完整）⇒
  **离线更新包内部文件清单未验证** ⚠。

## 7 三态

| 项 | 判定 |
|---|---|
| 仓库性质 / 版本 / 组件清单 | **✓** |
| 三条部署路线（原生 addon / Lua / 数据包） | **✓**（客户端字符串 + 更新日志；未实机） |
| 部署格式（`patch_N` 三件套 / 连续编号 / Lua 宿主叠包） | **✓** |
| 更新包内部结构 | **⚠**（只解了 1.3.1 客户端更新包；70 MB 离线包未下完） |
| `bundle_database`/`bundles.nxa` sha 基线的具体用途 | **⚠**（推断为自检，未验证） |
| 可复用的数据字段 / 表结构 | **✗**（无） |
| 外观 = 运行时域（数据层做不到） | **✓**（与既有结论一致 + issue 旁证） |
