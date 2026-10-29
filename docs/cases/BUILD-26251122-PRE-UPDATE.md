# 升级前准备：26088801 → 26251122（2026-10-29）

> 目标：把盘面还原成**纯原版 26088801**，把一切可回滚的东西连同**明文表快照**一起留档，
> 以便新 build 落地后做**逐表 diff** 并快速恢复工具链。
> 执行读数时刻：**2026-10-29 18:05–18:20**（下文所有"当前"均指这个时刻）。

## 1 卸载了什么（`✓ 离线`，已回读核对）

| 类别 | 数量 | 处置 | 回读证据 |
|---|---|---|---|
| 盘内 `.patch_N` 补丁文件 | **107 个**（36 条 patch + 伴随 gpu/stream，9 个宿主包） | 全部删除 | `data/` 下 `.patch_` 计数 **0** |
| 我们改过的 `generated_*.dl_bin` | **7 张** | 全部 `dlbin_deploy restore` | entities `cac4a228`、stratagem `7072cfe2`、damage `f425756e`、explosion `3f2d30a6`、projectile `424f8898`、armor_sets `4739b50c`、passive_bonuses `2bc5967a` |
| Lua 型 loader + 14 个 Lua mod | —— | **随 patch 一起消失**（loader 与 mod 都在 `9ba626afa44a3aa3.patch_*` 里） | `BingusSharedLoader.log` 里 14 个 `mods/...` 全靠 boot 包补丁加载 |
| `bin/` 下的 `preloader.dll` / `runtime.dll` / `crs-*` / `plugins/*` | 未删 | **判定为引擎文件**，不是 loader | 10/20 的 25480438 全量备份里**没有** `preloader.dll`/`runtime.dll`，而 loader 10/19 已在运行 ⇒ 二者属 25988 引擎换代后的新引擎文件；`crs-*`、`libcurl` 在旧备份里就有 |

卸载后盘面：`buildid 26088801`、`data/game/*.dl_bin` **55 张**、`data/bundles*.nxa` **31 个**、`.patch_` **0 个**。

## 2 备份与快照（642 MB）

目录：`D:\mod\backups\pre-update-26251122-20261029\`

| 子目录 / 文件 | 内容 |
|---|---|
| `patches/` | **107 个**原补丁文件（含第三方 APC 模组 7 组 + 我们全部实验补丁） |
| `loader/` | `preloader.dll`、`runtime.dll`、`crs-client.dll`、`crs-handler.exe`、`libcurl.dll`、`plugins/`、`BingusSharedLoader.log` |
| `plaintext-26088801/` | **56 个**明文表（旧 build 的 diff 基线） |
| `meta/fingerprint-26088801-vanilla.json` | exe/runtime/plugins 全 sha、31 个 bundle 的 size+头尾 1 MiB sha、**55 张表的全 sha**、buildid |
| `meta/manifest-backup-files.sha256` | 115 个备份文件 sha |
| `meta/manifest-plaintext-26088801.sha256` | 56 个明文 sha |
| `meta/ledger.json` + `dlbin-status-before-uninstall.txt` | 卸载前的部署账本 |
| `meta/steamdb-26251122-patch-notes.txt` | SteamDB 抓页正文（见 §3） |

## 3 新 build 26251122 的官方变更（来自本地 SteamDB 抓页）

**Devoid of Liberty: 7.2.2**，2026-10-29，**Build 26251122**；depot：553851/553852/553853/553854（+ DLC depot 1999180）。

| 类别 | 变更 |
|---|---|
| 战备 · **AMW-20 APEX** | 口径 60 → **20**；军械库正确显示"反坦克"穿甲；拆除强度 → **30**；远距离伤害衰减变缓 |
| 战备 · **LAS-44 NOVA** | 只修正军械库穿甲显示（"反坦克"） |
| 战备 · **SG-22 BUSHWACKER**（修正上一版算错） | 伤害 405 → **486**；耐久伤害 108 → **135** |
| 修复 | PC/Xbox 渲染器偶发崩溃；启动偶发崩溃 |
| 其它 | 移除两首音乐（不影响玩法） |
| 已知问题 | （空） |

**对工具链的预判**：本次没有任何载具/实体相关条目 ⇒ `generated_entities.dl_bin` **很可能整表不变**，
我们关于 TD-220/Maelstrom/GATER 的结论大概率仍成立；变化应集中在
`weapon_*` / `stratagem_*` / `projectile_settings` / `damage_settings` 这几张表。
但**一切以新明文逐表 sha 对比为准**，不做断言。

## 4 更新后必做（按顺序）

1. **确认 buildid**：`appmanifest_553850.acf` 的 `buildid` == `26251122`；记进下方表格。
2. **纯净启动一次**（不带任何补丁）确认游戏能进，排除 loader 残留。
3. **重新 dump 明文表** → `refs/dlbin/plaintext-26251122/`（55 张 + typelib）。
4. **typelib 对照**：与 `plaintext-26088801/dl_library.dl_typelib` 做 sha 比较 —— 相同则全部字段/枚举偏移结论继续有效，不同则先重跑 `typelib.py index`。
5. **逐表 sha diff**：用 `meta/fingerprint-26088801-vanilla.json` 的 `tables` 段做基线，产出 `BUILD-DIFF-26251122.md`（每张表的 变/不变 + 行数 + 关键行）。
6. **实体表专项复核**（若 entities 有变化）：TD-220 `0x16474112801385B6`（SeatCollection `+0x00`、Mount 槽）、Maelstrom `0xB0C9FAF4AF8903F9`、GATER 两变体 `0x0801B6B3C5D12EBC` / `0x423FF97D57AB04F5` 是否仍在、`TransitionId` 枚举值个数是否仍为 46。
7. **工具自检**：`python tools/check_links.py`、`dlbin_deploy.py status`、`entity_dump.py`、`resource_patch.py list` 各跑一次。
8. 以上全过之后，才讨论把 mod 装回（且要按新 build 重封包，旧 `.patch_N` 与旧封包**一律不要直接复用**）。

## 5 恢复/回滚（要回到 26088801 的 mod 状态时）

```bash
# 1) 补丁文件
cp /d/mod/backups/pre-update-26251122-20261029/patches/* "/d/SteamLibrary/steamapps/common/Helldivers 2/data/"
# 2) 表：按 meta/ledger.json 里记录的 installed_from 与 sha 回装（示例：entities + stratagem）
cd /d/mod && python tools/dlbin_deploy.py install --file generated_entities.dl_bin --sealed out/apc-recon/gater-host.dl_bin
python tools/dlbin_deploy.py install --file generated_stratagem_settings.dl_bin --sealed out/apc-recon/gater-host-strat.dl_bin
```

> ⚠ 回滚只对**同一 build（26088801）**有意义；升级到 26251122 之后，旧封包/旧补丁不可用，
> 需要按新明文重新生成（流程见 §4）。

## 6 结论（这一轮停止点）

- GATER 换壳投送线**暂停**在：`✗ 否证` 了血量、碰撞免疫、尺寸缩放、运输机血量四条；
  `⚠ 未证` 的最后两个嫌疑是**壳状态机**（已装过"换成坦克 SM"但**未取得实机判读**就被这次升级打断）
  与**挂载物/托架**（`nomount` 版本已备好但未上机）。
- 相关产物都在盘上：`out/apc-recon/gater-host*.dl_bin|plain`、`out/gater-sm/0dff5200594e867f.patch_0*`，
  升级后若要继续，先按新 build 重建这三样。
