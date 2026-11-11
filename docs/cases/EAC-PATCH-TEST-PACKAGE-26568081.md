# EAC 覆盖范围测试包（build 26568081，实验 ③：新增 `data/*.patch_N` 会不会被 EAC 拦）

> 本文是仓库内的协议副本；实际二进制测试包在 `out/eac-test-26568081/`（`out/` 不入库）。

> **目的**：判定「新增补丁文件」在 EAC 文件索引下是**被忽略**（→ 数据/资源层路线仍可行）
> 还是被判成 `error_file_forbidden`（未知的游戏文件，→ 只剩代理/离线路线）。

## 0. 测试包内容

```
out/eac-test-26568081/
  A-empty/9ba626afa44a3aa3.patch_0 (+ .gpu_resources/.stream)   空补丁，用社区标准宿主包
  B-empty-unknown-host/0f1e2d3c4b5a6978.patch_0 (+ 两个 0 B 附流) 备用：宿主包不存在，引擎永不加载
  scripts/00-inventory.ps1              记录当前 data 下所有 patch 文件与 sha256
  scripts/10-archive-old-patches.ps1    把更新前的旧 patch 移出（备份 + manifest）
  scripts/20-deploy-empty-patch.ps1     部署空补丁（-Variant A|B，自动校验哈希）
  scripts/30-rollback.ps1               移除测试补丁（-RestoreOldPatches 可恢复旧 patch）
```

两个补丁都是 **srkit 生成的合法容器**（256 B TOC、0 条资源）；A 用社区标准宿主包
`9ba626afa44a3aa3`（引擎会合并，但 0 条=什么都不改），B 用不存在的宿主包（引擎根本不会去合并）。

## 1. 为什么先用「空补丁」

- 要判定的只是 **EAC 对"多出来的文件"的态度**，不需要它真的改任何东西；
- 空补丁把「引擎侧兼容风险」压到最低——如果它让游戏崩了，说明新 build 的 patch 容器格式变了，
  这一发就不算数，换 B 变体或等格式解明；如果游戏正常启动且没有 EAC 弹窗，结论就干净。

## 2. 执行顺序（每次启动都要「完全退出游戏」）

```powershell
cd D:\mod\work\repo-datamined\out\eac-test-26568081\scripts

# ① 记录现状
powershell -NoProfile -ExecutionPolicy Bypass -File .\00-inventory.ps1

# ② 清空旧 patch，先做一次"干净基线"启动（对照组）
powershell -NoProfile -ExecutionPolicy Bypass -File .\10-archive-old-patches.ps1
#    启动游戏 → 应正常进主菜单、无 EAC 弹窗。若这一步就崩，先解决基线，别往下做。

# ③ 部署空补丁（变体 A）
powershell -NoProfile -ExecutionPolicy Bypass -File .\20-deploy-empty-patch.ps1 -Variant A
#    启动游戏 → 观察 EAC

# ④ 回滚
powershell -NoProfile -ExecutionPolicy Bypass -File .\30-rollback.ps1 -Variant A -RestoreOldPatches
```

## 3. 判读表

| 现象 | 结论 | 下一步 |
|---|---|---|
| 正常进主菜单、无 EAC 弹窗、无崩溃 | **新增 patch 文件被 EAC 忽略** → 数据/资源层路线成立 | 立刻做第二阶段：一个**真的改了东西**的 patch（改一张贴图或一个数值），确认「加载生效 + EAC 不拦」 |
| 弹 `Easy Anti-Cheat Error！未知的游戏文件 (…patch_0)` | 新增文件被拦（`error_file_forbidden`） | 试变体 B（宿主包不存在）确认是否与宿主包有关；若 B 也被拦 → 路线关闭 |
| 弹 `未知的文件版本` 且点名 patch 文件 | 同属文件索引拦截 | 同上 |
| 游戏直接崩、**没有** EAC 弹窗 | 引擎侧不兼容（patch 容器/格式变了），与 EAC 无关 | 换变体 B；再不行说明 26568081 改了 patch 加载器，需要先解格式 |
| 进主菜单但没反应/贴图异常 | 补丁被加载了（对空补丁而言不应发生） | 记录，说明引擎扫描了它 |

## 4. 证据要留什么

- EAC 弹窗截图（若有）；
- `%APPDATA%\EasyAntiCheat\<productid>\<deploymentid>\anticheatlauncher.log` 的对应时段；
- `inventory-before.txt` / `receipt-variant-A.txt`（证明改了什么、哈希是多少）；
- 本次 EAC 模块指纹（模块换了就说明索引也可能换了）：
  `easyanticheat_x64.eac` 32,075,192 B / `.metadata` `sha1=62526a9b…`。

## 5. 已知前提（别踩）

1. **绝不要**碰 `data/game/*.dl_bin` 官方文件——那条路已在报告里实测判死；
2. 旧 patch（`9ba626afa44a3aa3.patch_0..3`，10/31–11/2 做的）**先移出**，否则变量不干净；
3. 本机当前 4 个旧 patch 在更新后仍能启动，但这不能替代对照——旧 patch 可能是"从未被加载"或
   "加载了但无副作用"，必须按 §2 的顺序做。
