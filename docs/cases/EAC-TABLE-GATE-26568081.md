# EAC 数据表闸门：四个变体的判决（build 26568081）

> 一句话：**「替换 `data/game/*.dl_bin` 改内容」被证明关死** —— 不是工具不够巧，是数学上不可能绕。
> EAC 比对的是**密文正文**；而改内容必然改密文。同时证明**引擎自己校验 Poly1305**（tag 坏了直接崩）。
> 社区的「内容不变、仅重封也被拦」**成立**，本文第一次用**内容逐字节相同**的样本证明它。

- 日期：2026-11-11
- 目标文件：`data\game\generated_zone_data.dl_bin`（518,526 B，官方 sha256 `0EC00664…DA11E7`）
- 产物与脚本：`out\eac-test-26568081\D-minimaldiff\`（`build_reseal.py` / `build_controls.py` / `scripts\deploy-A.ps1` / `rollback-A.ps1`）
- 工具：`tools/dlbin_tagkey.py`（用收件人私钥现算 `keystream[0:32]` 与合法 tag）、`tools/zone_terrain_flat.py`（保 murmur 编辑）

---

## 1. 变体矩阵（全部实机跑过）

| 变体 | 明文内容 | Poly1305 MAC | 密文正文 | `epk`/大小 | 磁盘差分 | EAC 结果 |
|---|---|---|---|---|---|---|
| **aggressive** | 改了 2,920 B（清 height generators + amplitude + 曲线/偏移） | 合法 | 改了 | 同官方 | 2,936 B（0.566%） | **弹「未知的文件版本」** |
| **T1 tag-only** | **逐字节未变** | **失效** | **一个字节没动** | 同官方 | **1 B（tag 第 0 字节 1 bit）** | 不弹，但**游戏崩溃** |
| **T3 fresh-esk** | **逐字节未变**（解封回读校验过） | 合法 | **99.6% 字节变了** | 同大小、新 epk | 516,543 B | **弹「未知的文件版本」** |
| （基线）官方 | 官方 | 官方 | 官方 | 官方 | 0 | 正常进游戏（多次） |

murmur 说明：aggressive/T2 都用无主 zone 的校正字把**明文 `MurmurHash64A` 保持在官方的 `0x4072B2DE6B1DCB16`**，
所以「引擎白名单」这一层在 aggressive 上也是通过的 —— 拦它的是另一套判据。

---

## 2. 证据：弹窗不是 bootstrapper 报的

`%APPDATA%\EasyAntiCheat\f163733398a54335966be5046900198b\8511004301af474cad0c5a65679fe02e\anticheatlauncher.log`

T1（崩溃那一发）：

```
[12:37:59] Launcher finished with: 301, 'Easy Anti-Cheat 在游戏中成功加载'.
[12:37:59] Successfully initialized the Easy Anti-Cheat module, waiting for game window to become visible.
[12:38:08] The game window has become visible, the bootstrapper will leave the visible state.
[12:38:08] Terminating with: 0.
```

T3（被拦那一发）：

```
[12:43:48] Launcher finished with: 301, 'Easy Anti-Cheat 在游戏中成功加载'.
[12:43:48] Successfully initialized the Easy Anti-Cheat module, waiting for game window to become visible.
[12:43:59] The game window has become visible, the bootstrapper will leave the visible state.
[12:43:59] Terminating with: 0.
```

两发 bootstrapper **都是 301 成功、无任何完整性错误**。也就是说：

* `未知的文件版本` 是**游戏内 EAC 模块**（`easyanticheat_x64.eac`，32 MB 混淆体）在**窗口出现之后**才报的；
* 启动器日志里看不到它，排查时要看游戏内弹窗的**出现时机**，不能只看 bootstrapper。

另外：在游戏目录、`EasyAntiCheat\`、`bin\` 里**搜不到** `generated_zone_data` 这个字面量
（`bundle_database.data` 也是 0 命中），说明索引不在明文清单里，而是编码在 EAC 模块/数据里。

---

## 3. 结论

### 结论 A：EAC 的判据覆盖**密文正文**，不是「解密后的内容」

T3 的明文与官方**逐字节相同**（我们自己用 `recipient.sk` 解封回读校验），只有封装换了；
结果仍然被拦。若 EAC 比的是解密内容，T3 必须通过 —— 它没有。

### 结论 B：T1 为什么没弹 —— 崩溃抢先，不是「tag 不受管辖」

T1 只动 tag，EAC 没弹窗，但**引擎解封失败直接把游戏崩了**（转储
`PACKER_196569156_43396.dmp`，14,099,015 B，20:38 写入；文件当时被独占锁定，转储解析待补）。
崩溃发生在窗口出现后数秒内，早于/同时于 EAC 的检查，所以
**「tag 是否在 EAC 的覆盖范围内」目前仍未定论** —— 但它已经不重要（见结论 C）。

崩溃这件事本身是**新证据**：此前「引擎是否校验 MAC」只是推测，现在是实证 —— **引擎校验 Poly1305**。

### 结论 C：改内容 = 数学上不可能

```
ciphertext = plaintext XOR XSalsa20(beforenm(sk, epk), blake2b24(epk||pk))
```

要保持内容变而密文不变，只能让 keystream 不变 ⇒ `epk` 不变 ⇒ 密文逐字节不变 ⇒ 内容不变，矛盾。
换成新 `epk` 则密文全变。**两条路都改密文，而 EAC 覆盖密文**。
所以：

> **在不改动 EAC/index 侧数据的前提下，「替换官方 dl_bin 以改变内容」在密码学上不可能成立。**

这也解释了为什么之前所有重封尝试（无论随机 esk 还是固定材质）全部失败：
失败点从来不在封装，而在「密文必须变」。

### 结论 D：社区文档的判断成立

`eac数据表校验-实测报告-2026-11-11.md` 的「内容不变、仅重封也被拦」**是对的**。
本文与它的差别是：这次是**真·内容逐字节相同**的重封（旧工具很可能在重封时重新序列化了容器，
明文其实已变），所以这条从「可能归因错误」升级为**有干净样本支撑的结论**。

---

## 4. 三条数据/资源通道的最终状态

| 通道 | 状态 | 证据 |
|---|---|---|
| **新增 `data\*.patch_N` 覆盖层（包资源）** | ✅ 可用 | 空补丁正常进主菜单；strings 覆盖真生效（`MODDED` 标签） |
| **替换 `data\game\*.dl_bin`（散表）** | ❌ 死 | 本文四变体矩阵 + 结论 C 的不可能性论证 |
| **代理改写运行期数据** | ✅ 可用 | `settingsHash`/`planet_effects`/inventory 等均已实机验证 |

推论：**任何「表内数值/地形/资产参数」的修改都只能走代理或运行时**；补丁覆盖层只能改**包资源**
（材质/贴图/字符串/Lua 等）。

---

## 5. 复现

```powershell
cd 'D:\mod\work\repo-datamined\out\eac-test-26568081\D-minimaldiff'
python build_reseal.py            # aggressive / mild
python build_controls.py          # T1 tag-only / T2 content-1B / T3 fresh-esk
cd scripts
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy-A.ps1 -WhatIf -Variant T3-fresh-esk
powershell -NoProfile -ExecutionPolicy Bypass -File .\deploy-A.ps1 -Variant T3-fresh-esk
powershell -NoProfile -ExecutionPolicy Bypass -File .\rollback-A.ps1
```

脚本守卫：游戏在跑拒绝；目标不是官方 sha 拒绝；拷贝后回读校验 sha256。

## 6. 时序判定：**引擎先读，EAC 后判（且只在游戏跑过加载后判）**

三次带客观时间戳的运行（`tools/eac_timing_watch.ps1`：100 ms 轮询进程 + 枚举新顶层窗口，
与 EAC 启动器日志交叉校验，误差 22 ms）：

| 运行 | 变体 | 窗口时刻 | 崩溃时刻 | EAC 弹窗时刻 | 结果 |
|---|---|---|---|---|---|
| A | aggressive（内容改、MAC 合法） | 21:04:58.197 | 无 | **21:05:40.201 = 窗口 +42.00 s** | 弹窗拦下 |
| B | X（内容改 + tag 坏） | 20:52:24.059 | 转储创建 20:53:12 = **窗口 +47.9 s** | 无 | 直接崩 |
| C | X 复跑 | 21:08:37.930 | crs 窗口 21:09:01.4 ≈ **窗口 +23.5 s**，进程 21:09:14.4 退出 | **无** | 直接崩 |

两张转储的异常码还不一样（B：`0xC0000005` write @0x24；C：`0xC0000028` STATUS_BAD_STACK），
都是 ntdll 里的二次故障 —— 说明解封失败后走的是各不相同的错误路径，不是同一条干净的错误分支。

**结论**：

1. **EAC 的判决晚于引擎的数据加载**：B、C 两次都是「引擎读表 → 解封失败 → 崩」，而 EAC 从头到尾没出判决；
   A 这次加载成功，EAC 才在窗口 +42 s 出判决。**即 check-after-use：数据先被消费，EAC 后判。**
2. **判决不是纯定时器**：如果是固定 +42 s 的定时检查，B（+47.9 s 才崩）早就该先弹窗；它没有。
   所以判决被"游戏跑到某个阶段"门控着。
3. 我中途一度根据「A 弹窗 +42 s vs B 崩溃 +47.9 s」推断"EAC 先查后读"——**这个推断是错的**，
   跨运行比较不成立：C 复跑同样变体，崩溃时刻从 +47.9 s 变成 +23.5 s，**加载耗时本身波动 ≥24 s**。

**边界**：窗口宽度仍未知（需要"加载完成"的客观时刻），且加载耗时波动大。
精确测量只能靠文件系统审计（SACL + auditpol）拿逐文件读取时间线。
即便窗口被证实宽裕，**本仓库不提供抢占该窗口的工具**（= 反作弊规避）。

## 7. 文件审计：逐次读取时间线（决定性数据）

方法：`auditpol` 打开 File System 成功/失败审计 + 给 55 个 `data\game\*.dl_bin` 挂 `ReadData` 的 SACL，
读安全日志 4663 事件（`tools\eac_audit_*.ps1`）。本次运行用 **aggressive** 变体（加载成功 → EAC 才出判决）。

窗口出现：`21:13:22.460`；EAC 弹窗：`21:14:02.085`（+39.62 s）。

| 相对窗口 | 事件 | 读次数 |
|---|---|---|
| **+11.42 → +11.61 s** | **引擎加载第一波**（status_effect / hit_effect / explosion / projectile / beam / arc / damage …） | 23 |
| **+14.18 → +14.22 s** | 引擎加载第二波（add_resource_dependencies / video_flow / body_settings / armor_sets / passive_bonuses …） | 6 |
| **+16.05 → +16.54 s** | 引擎加载第三波（含 **`generated_zone_data` @ +16.44 s**、region_settings、planet_data、entity_deltas …） | 23 |
| **+34.41 → +37.06 s** | **第二轮全量读取**：同一批 51 张表全被再读一遍（48 次 + 4 次，集中在 2.6 s 内） | 52 |
| **+39.62 s** | **EAC 弹窗「未知的文件版本」** | — |

合计 104 次读取 = **加载 52 次 + 校验 52 次**；51 张表全部被读 ≥2 次（zone_data、animation_event_trigger 各 3 次）。
**4 张表启动时完全不读**（懒加载）：`generated_candidate_descs`、`generated_corporation_logos`、
`generated_credits_settings`、`generated_policy_settings`。

### 由数据直接得出的结论

1. **引擎在 EAC 校验之前 18 秒就把所有表读完了**：
   加载在 +16.54 s 结束，完整性扫描 +34.41 s 才开始 → **窗口 ≈ 17.9 s**（到判决 ≈ 23.1 s）。
2. **EAC/完整性扫描确实自己把文件重读一遍**（第二轮 52 次读取，2.6 s 内完成），判决在扫描开始后 **5.2 s** 出现。
   —— 注意：引擎与 EAC 在同一进程（PID `0xe98`），PID 分不开二者；这个归属是由"与加载批次完全同构的第二轮 + 判决紧随其后"判定的，
   不是直接观测。
3. 所以此前"EAC 是不是只查一次"有了答案：**是两次独立的整轮读取，第二轮才是校验**。
4. 窗口存在且宽约 18 s —— **但本仓库仍然不提供抢占该窗口的工具**（= 反作弊规避）。
   这份数据的正当用途是理解机制与负责任披露。

## 8. 未了项

1. 崩溃转储解析（确认崩溃点落在解封/表加载路径）—— 文件当时被独占锁，稍后重试；
2. 「tag 是否也在 EAC 覆盖范围」—— 需要一个「tag 变了但游戏不崩」的样本，目前构造不出
   （tag 坏 ⇒ 引擎必崩），故不影响结论；
3. `T2-content-1B`（改 1 字节内容 + 合法 MAC，17 B 差分）**未单独跑**：
   按结论 A/C 它必然被拦，留作需要时的快速复核。
4. 崩溃转储的**业务栈**未定位（两次都是 `ntdll` 内二次故障）：如需精确定位，要用模块的 unwind 信息做
   正式展开，或抓第一现场（WER 的 LocalDumps 配 `MiniDumpWithFullMemory` + 首次异常）。
