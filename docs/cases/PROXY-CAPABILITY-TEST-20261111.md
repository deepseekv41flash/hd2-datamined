# 代理线全能力一次测（2026-11-11，build 26251122）

> **一句话**：一次登录覆盖 9 条代理能力 + 1 条抓包能力；服务端侧 8 项已用 curl 穿过代理**离线验证全部生效**，
> 剩下 2 项（变种、战备试用）需要客户端上报星球后才会注入，只能进游戏看。

## 0. 三态

| 能力 | 落点 | 离线验证 | 实机 |
|---|---|---|---|
| A 全局 GWE 效果 | `globalEvents[1501113].effectIds += 1346` | **✓** curl 读到 `[1346]` | ⚠ 待看 |
| B 星球级变种 | `selection.json` = 掠食变种 → `planetActiveEffects` | ✗ 需客户端上报星球 | ⚠ 待看 |
| C 战备试用 | `stratagems.json` = 1227 / 1263 | ✗ 同上 | ⚠ 待看 |
| D 解锁注入 | `runtime/inventory_*.json`（24 物品 + 140 附件 + 3 外观 + 30 战备项）| ✗ 需登录态 | ⚠ 待看 |
| E 休眠星节点 | `planet_nodes` 300 + `campaigns` + `events` + `jointOperations` | **✓** 273→274 节点、43→44 战役、2→3 事件、+1 联合作战 | ⚠ 待看 |
| F 归属翻转 | `owner {"158":1}` | **✓** 3→1 | ⚠ 待看 |
| G 攻击边 | `attacks [{124→168}]` | **✓** 新增该边 | ⚠ 待看 |
| H 分区状态 | `regions [{76, regionIndex 0}]` | **✓** 新增 (76,0) | ⚠ 待看 |
| I 生态/地形借用 | `settings_hash {"100":721718208}` | **✓** `3515299681 → 721718208` | ⚠ 待看（此前已验证过配方）|
| J 全量抓包 | `HD2_GWE_DUMP=capture-20261111` | **✓** 日志出现 `gwe-dump`，body 落盘 | — |

## 1. 目标选择（基于 2026-11-11 18:5x 的真实 Status）

| 目标 | 现状 | 用途 |
|---|---|---|
| index **300** | Status 里**不存在**（本地 planet_data 有定义） | 伪造节点 + 战役 + 防守事件 |
| index **158** | owner=3（机器人），632 玩家 | 翻成人类看颜色 |
| index **124** | owner=2（虫族），2,149 玩家，有战役 | 掠食变种（terminid 阵营匹配）|
| index **168** | owner=1（人类），无事件 | 注入攻击边 124→168 |
| index **76** | owner=1，12,163 玩家，无 planetRegions | 注入分区 0 |
| index **100** | owner=2，有战役 | 生态换 UVP ALPHA（落叶林）|

## 2. 启动方式

```
cd D:\Downloads\variant_mod
.\stop.ps1
powershell -ExecutionPolicy Bypass -File .\run-capability-test.ps1
```

启动器会把 spec 写进 `runtime\capability_test.json`，并设好
`HD2_GWE_EXTRA` / `HD2_GWE_DUMP` / `HD2_GWE_PATHS=api/`。

> 坑：`selection.json` 必须用 **UTF-8 无 BOM** 写。用 PowerShell `Set-Content -Encoding UTF8`
> 写中文会双编码，代理读出来是「鎺犻鍙樼」这种乱码，变种直接匹配不上。

## 3. 实机检查清单（一次登录按顺序看）

1. **星图**：找 index 300 的新节点（坐标 `(0.30, -0.55)`）——是否出现、是否可点；
2. **星图**：该节点上是否有防守事件倒计时（事件 id 9001）→ E 的 events 分支；
3. **星图**：158 号星是否变成人类控制色 → F；
4. **星图**：168 号星是否出现「被攻击」箭头 → G；
5. **星图**：100 号星的名字/生态是否变成 UVP ALPHA / 落叶林 → I；
6. **装备/护甲界面**：是否多出注入的武器、护甲、附件、外观 → D；
7. **战备栏**：是否出现 MG-43 / M-105 的试用（打开过星球后才有）→ C；
8. **打开 124 号星 → 进任务**：虫族是否出现掠食变种 → B；
9. **任意任务用轨道加特林**：是否变成燃烧弹 → A；
10. **进 76 号星**：是否出现分区条（分区 0）→ H。

## 4. 风险与回滚

- 星图异常 / 崩溃：`.\stop.ps1` → `.\run.ps1 -Passthrough` 即可恢复原版服务端数据；
- 注入的 300 号节点若让星图错乱，属已知风险（坐标是猜的，非真实节点位置）；
- `regions` 只补缺失条目，不覆盖线上已有分区（代码保证）。

## 5. 产物

- 启动器 `D:\Downloads\variant_mod\run-capability-test.ps1`
- spec `D:\Downloads\variant_mod\runtime\capability_test.json`
- 抓包目录 `D:\mod\out\gwe\capture-20261111\`（`status_pre/post.json`、`warinfo_pre/post.json` + 本次全部响应体）

## 6. 实机结果（2026-11-11 晚，两轮）

| 项 | 结果 | 说明 |
|---|---|---|
| A 全局燃烧加特林 | **✓ 生效** | `globalEvents[1501113].effectIds += 1346`，局内轨道加特林变燃烧弹 |
| B 星球级变种 | **✓ 生效（换通道后）** | selection 通道在 TERREK 上被阵营过滤（owner=1 vs terminid）；改用 **`planet_effects` 原始注入**后，TERREK 卡面出现 **PREDATOR STRAIN** 词条（用户截图确认）|
| C 战备试用 | **✓ 生效** | MG-43 / M-105 出现在战备栏 |
| D 解锁注入 | **✓ 生效** | `INV REWRITE +197`、`ITEMS REWRITE +3`；LAS-22 出现在物品栏 |
| F owner 翻转 | **✓ 生效** | 158 CHOEPESSA IV 3→1，星图变色 |
| I 生态借用 | **✓ 生效** | 100 TRANDOR → 落叶林 |
| E 休眠星节点 | 待复测 | 第一轮只有 Status 节点（无 warinfo planetInfo）→ 不显示；第二轮已补 `planet_infos`，待实机 |
| G 攻击箭头 | 待复测 | 第一轮只加 `planetAttacks` 不画；第二轮已补 campaign type=4 + planetEvents 9002 |
| H 分区条 | 待复测 | 76 无 warinfo 分区定义；第二轮换 16 号星（4 个分区）|

### 6.1 新结论：阵营过滤是**我们代理侧**的限制，不是客户端限制

`planet_effects` 把 terminid 的 tag(1243)+mechanic(1245) 直接挂到人类星 TERREK（owner=1）上，
客户端照样渲染出 PREDATOR STRAIN 卡面。说明 `selection.json` 那条「按 owner 过滤」只是我们为了避免
跨阵营出错加的保护，客户端并不拒绝「人类星 + 虫族变种」。代价是语义上不合理（人类星为何有虫族变种），
但作为注入通道它更通用。

对应代码：`war_proxy.py` 的 `_gwe_apply_extra()` 新增 `planet_effects` 键（`DSH-PLANET-EFFECTS-V1`）。
