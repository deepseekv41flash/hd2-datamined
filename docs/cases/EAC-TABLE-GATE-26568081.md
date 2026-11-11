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

## 6. 时序判定：**引擎先读，EAC 后查**（use-before-verify）

追加变体 **X**（内容改 2,920 B **且** tag 翻 1 bit，MAC 失效）：

* 内容改了 ⇒ 若 EAC 先查，必弹「未知的文件版本」；
* tag 坏了 ⇒ 若引擎先读，必崩。

实机结果：**先崩溃、没有弹窗**（转储 `PACKER_197439062_22852.dmp`，14,215,129 B，20:53 写入；
异常 `0xC0000005` write @ `0x24`，RIP 落在 `ntdll+0x1A12D` —— 崩溃处理器/二次故障，业务栈未直接可见）。

结论：**引擎在 EAC 做出判决之前就已经读取并解封了数据表**。结合 T1/T3 的弹窗都出现在窗口出现之后，
时序是：

```
启动 → 引擎读取 data\game\*.dl_bin 并解封（MAC 校验在这里） → 之后 EAC 才比对文件 → 不符则弹窗
```

即 EAC 的文件校验是 **check-after-use**：数据已经被引擎消费，才轮到它判。这是 EAC 侧的结构性弱点，
**属于应当披露、而不是利用的设计问题**；本仓库不提供抢占该窗口的工具。

## 7. 未了项

1. 崩溃转储解析（确认崩溃点落在解封/表加载路径）—— 文件当时被独占锁，稍后重试；
2. 「tag 是否也在 EAC 覆盖范围」—— 需要一个「tag 变了但游戏不崩」的样本，目前构造不出
   （tag 坏 ⇒ 引擎必崩），故不影响结论；
3. `T2-content-1B`（改 1 字节内容 + 合法 MAC，17 B 差分）**未单独跑**：
   按结论 A/C 它必然被拦，留作需要时的快速复核。
4. 崩溃转储的**业务栈**未定位（两次都是 `ntdll` 内二次故障）：如需精确定位，要用模块的 unwind 信息做
   正式展开，或抓第一现场（WER 的 LocalDumps 配 `MiniDumpWithFullMemory` + 首次异常）。
