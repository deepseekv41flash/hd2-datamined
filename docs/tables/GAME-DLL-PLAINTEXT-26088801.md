# `game.dll` 明文数据段里有什么（build 26251122，✓ 只读侦察）

> 背景：新 build 的 `game.dll` 段表恢复正常，`.text` 仍加密（熵 8.0000），但 `.rdata`（熵 7.6659）与
> `.data`（熵 6.4258）里的**静态数据是明文**。本文盘点这两段里「有价值 / 无价值」的内容，
> 方法 = **locid 字扫描 + 邻近聚类**（本地化字符串的 32 位 id 在数据段里成片出现），
> 工具：`tools/gamedll_data_survey.py`（数据簇）、`tools/opmod_scan.py`（Operation Modifiers）。
> 单条 Operation Modifiers 的结论见 [OPERATION-MODIFIERS-26088801](OPERATION-MODIFIERS-26088801.md)。

## 1. 扫描结果总览

`.rdata` + `.data` 里共 **13,067** 个「locid 字」，聚成 **60 个 ≥3 命中的数据簇**（73 个总簇）。
按内容归类如下（按对玩法/未发布内容的价值排序）：

| 价值 | 数据簇（文件偏移，段） | 规模 | 是什么 | 状态 |
|---|---|---|---|---|
| **高** | `0x2CB61D0` 起（`.data`） | 单条 ~0x100 B | **OperationSettings 定义**（抓包里的 `operationSettingsId` 之一 = `0x8C136427` = 2350081063），含 3 个 locid（PEACEKEEPING OPERATION + 2 段描述）与 ~20 组 `{u32 hash, f32 1.0}` 权重 | ⚠ 结构未证（下一项） |
| **高** | `0x208A440`（`.rdata`） | 143 locid 命中 | **舰船升级模块的名称/描述**：`ORDERS / PLATOON ORDERS / MAJOR ORDERS / AUTOMATED HELLPOD LOADING / PRE-FILLED HELLPODS / EXPANDED ARMORY / ENHANCED COOLING SYSTEM / EXPANDED CREW / IMPROVED GUIDANCE SENSORS …` | ⚠ 未跟本地 `generated_stratagem_upgrade_settings` 对表（可能是未发布模块的来源） |
| **中** | `0x2CA36B8`（`.data`） | 570 locid | 设置菜单文案（GAMEPLAY/DISPLAY/GRAPHICS/AUDIO/HUD/ACCESSIBILITY/…、按键提示） | 低游戏价值 |
| **中** | `0x2C9F630`（`.data`） | 219 locid | 设置项描述（Motion Sensor Sensitivity/Acceleration/…、Deadzone 等） | 低游戏价值 |
| **中** | `0x20AA41C / 0x208E410 / 0x20A5480 / 0x20BC430 / 0x20774D0 / 0x209C42C / 0x2085474 / 0x2097740 / 0x20AF414 / 0x20C5650 / 0x20B7950 / 0x2080820 / 0x207C47C / 0x2093434 / 0x20A1414 …`（`.rdata`，约 15 簇） | 每簇 230–465 locid | **Operation/战役类型定义族**：`OPERATION IMPACT`、`Completing this Operation contributes to …`、`#PERCENTAGE% HELD / LIBERATED`、`CITY OPERATION`、`MEGAFACTORY OPERATION`、`PEACEKEEPING OPERATION` | ⚠ 待解（结构与 `operationSettingsId`、难度、modifier 数量的关系） |
| 低 | `0x2060060 / 0x206E780`（`.rdata`） | 各 ~2,097 locid | **舰船命名用词表**（Adjudicator/Steward/Agent/Soul/Arbiter/Wings/Harbinger/Halo/Dawn/… + of Benevolence/of Courage/…） | 纯命名表 |
| 低 | `0x1FF1400`（`.rdata`） | 193 locid | 语音字幕（`{0.00->0.98}Package inbound…` 等） | 纯字幕 |
| 低 | 其余小簇 | 3–150 locid | 零散 UI 文案/提示 | — |

## 2. 两个高价值线索

### 2.1 OperationSettings 记录（`operationSettingsId` 在本地有定义）

抓包的 8 个 `operationSettingsId` 里 **只有 1 个能在本地命中**：

```
2350081063 = 0x8C136427  →  game.dll 文件偏移 0x2CB61D0（.data）
```

该记录前 ~0x30 B（小端）：

| 偏移 | 值 | 猜测 |
|---:|---|---|
| `+0x00` | `0x8C136427` | **operationSettingsId**（与 API 字段一致）|
| `+0x04` | `1` | ⚠ |
| `+0x08` | `2` | ⚠ 可能是 modifier 数量/单局数 |
| `+0x0C` | `1` | ⚠ |
| `+0x10` | `10` | ⚠（难度上限？）|
| `+0x14..+0x1C` | 0 | — |
| `+0x20` | `1.0f` | ⚠ |
| `+0x24` | locid `0x0CDF8AC5` = **PEACEKEEPING OPERATION** | 名称 |
| `+0x28` | locid `0x0D314823` = “Our enemies have forced co…” | 描述 |
| `+0x2C` | locid `0x0C5E0839` = “Tactically eliminate all o…” | 描述（第二条？）|
| `+0x30` 起 | ~20 组 `{u32 hash, f32 1.0}` | 权重/任务类型表（⚠ 未证）|

其余 7 个 id（`0x20126884 / 0x922F6304 / 0xA6B6B774 / 0xA7508E58 / 0xBE6CA1E1 / 0xE0791AF3 / 0xE6709132`）
**本地 0 命中** ⇒ 它们大概率是服务端侧定义（或客户端只在 Create 请求里原样回传、不做本地解析）。
> 备注：`0xA6B6B774` / `0xBE6CA1E1` 正是 2026-10-27 防守伪造实验里观察到的 `operationSettingsId` 变化值，
> 说明它确实是服务器下发的操作配置 token。

### 2.2 舰船升级模块的硬编码名/描述

`0x208A440` 簇里是一组「分组名 + 模块名 + 描述」：

```
ORDERS / PLATOON ORDERS / MAJOR ORDERS
AUTOMATED HELLPOD LOADING   – Reduces cooldown for Hellpod stratagems …
PRE-FILLED HELLPODS         – Reduces cooldown for Hellpod stratagems …
EXPANDED ARMORY             – Allows 1 additional use per mission …
ENHANCED COOLING SYSTEM     – Reduces cooldown for Strike stratagems …
EXPANDED CREW               – Reduces cooldown for Strike stratagems …
IMPROVED GUIDANCE SENSORS   – …
```

这些名称与本地 `generated_stratagem_upgrade_settings` 里的舰船模块同族；**值得做一次对表**：
**哪些模块名只出现在 game.dll、不在本 build 的模块表里**（= 未发布/预留模块，如之前社区清单里那些
"barrage spread reduced / +1 salvo" 条目）。

## 3. 结论

1. 明文数据段**没有**超出已解范围的“第二套玩法表”：玩法数值仍全在 `generated_*.dl_bin`（已有明文缓存）；
2. 额外能挖的只有三类硬编码静态定义：**OperationSettings / Operation 类型定义族**、**舰船升级模块名**、
   **Operation Modifiers**（已解出 13 条）；其余是 UI 文案、舰船命名词表、语音字幕；
3. 代码段（`.text`）仍加密 ⇒ 这些表**如何被选择/使用**依然拿不到（需运行时内存 dump）。

## 4. 下一步（建议）

1. **解码 OperationSettings 簇**：先定记录边界/步长（约 15 个 `.rdata` 簇 + `.data` 的 0x2CB61D0 记录），
   把 `operationSettingsId` ↔ 名称 ↔ 描述 ↔ `{hash,1.0}` 权重表连起来；若其中有“modifier 数量/池”字段，
   任务级 modifier 的选择逻辑就能从**数据侧**反推（不需要碰加密代码）；
2. **舰船模块对表**：game.dll 模块名 ↔ `generated_stratagem_upgrade_settings`，列未发布模块清单；
3. 收工：`stop.ps1` 停代理回纯转发。

### 4.1 这些表能改吗？——壳的实测边界与三道关卡（2026-11-07 补）

> 背景：这些表（Booster `0x2CB4840`、Operation 目录 `0x2077570`、舰船模块 `0x208A454`…）都在
> `game.dll` 里，而 `game.dll` 是**带壳**的。本节给出壳的实数边界，以及"改它"要过哪几道门。

**壳的实测**（本机 `data/game/game.dll`，49,075,800 B，sha256 前缀 `61dcfcd201dacbf3`，PE32+ / 7 段）：

| 段 | 原始大小 | 熵 | 64 KB 分块判据 | 判定 |
|---|---:|---:|---|---|
| `.text` | 0x1F98000 | **8.0000** | 506/506 块 > 7.95 | **整段密文**（入口点 RVA `0x1F10CEC` 处字节随机，无函数序言）|
| `.rdata` | 0x51B200 | 7.6659 | 50 块密文 / 10 块明文 | **半明半密** |
| **`.data`** | 0x82AA00 | 6.4258 | 14 块密文 / 28 块明文 | **以明文为主 ← 我们的表都在这里** |
| `.pdata` | 0x1B7000 | 7.9999 | 28/28 块 > 7.95 | 密文（异常表本应低熵 ~4）|
| `_RDATA` | 0x3000 | 7.9836 | — | 密文 |
| `.rsrc` / `.reloc` | — | 2.7295 / 5.4958 | — | 明文 |
| **文件尾覆盖层** | **10,328 B** | 7.6232 | — | **Authenticode 证书表**（数据目录 `dir[4]` rva `0x2ECAE00` / size `0x2858` = 10,328，与尾长**精确相等**）|

⇒ 壳的形态是"**代码 + 异常表 + 一部分 `.rdata` 加密，静态数据表留明文**"，与 §1 的观察一致。
（另：可选头校验和字段非 0，`0x02ED103A`；用户态 DLL 的校验和正常不被校验。）

**三道关卡**：

| 关卡 | 现状 | 对"改表"的影响 |
|---|---|---|
| ① 壳的解密链 | `.text`/`.pdata` 在盘上是密文，运行期由加载侧解密 | **不影响**：我们只改明文 `.data`，密文段原样不动，解密链路照跑 |
| ② Authenticode 签名 | 文件带证书表（10,328 B）| 改**任一字节**签名即失效；是否被拦取决于加载路径与 EAC（自 build 25988413 起 GameGuard → **Easy Anti-Cheat (EOS)**，内核驱动 `EasyAntiCheat_EOSSys`）|
| ③ 字段是否真被消费 | 记录只有 `itemId / +0x04 / +0x08 f32 / +0x0C / locids`，语义靠对表推断 | **离线不可证**：读这些字段的代码在熵 8.0 的加密段里 |

**旁证（重要对照）**：`dl_bin` 的内容哈希闸门 —— 引擎会比对 `MurmurHash64A(明文)` 与**内置预期值**，
说明 `game.dll` 里确实存着一张期望哈希表（在哪一段不可读）。我们这条线一直是**保哈希**绕开它，
从来没有去改那张表。

**结论**：`game.dll` 的这几张表 —— **读**完全可行（已验证 Booster 30/20 条、Operation 12 条、舰船模块 44 条）；
**写**在字节层面可行（表在明文段、不碰壳），但"会不会被接受""改了有没有效果"两问都**离线不可证**，
且踩在 EAC 上。⇒ **默认不碰**，把它当字典用；可调参数一律走 `generated_*.dl_bin`（爆炸/伤害/状态/实体/战备行都已验证可改）。

**若一定要验"游戏是否读盘上这个文件"**（最小风险序列，仍非零风险）：

1. 备份原 dll（49,075,800 B，sha256 前缀 `61dcfcd201dacbf3`）；
2. **零行为 canary**：把某条 Booster 的**名称/描述 locid** 改成另一个**已存在**的 locid（只改显示文案，
   不动任何数值与状态槽），进游戏看该 Booster 的 UI 文案是否变化；
   - 文案变了 ⇒ 游戏确实读我们改的文件，且这张表是 UI 数据源；
   - 没变 / 报错 / 被踢 ⇒ 存在完整性校验，路线到此为止；
3. canary 通过后再做**强度差分**（例：`SAMPLE EXTRICATOR` 的 `+0x08` 10.0 → 50.0），用行为回答
   "`+0x08` 是行为参数还是显示参数"。

⚠ 风险声明：这是篡改受签名保护的游戏可执行模块，在 EAC 下**有封号风险**；本仓库至今**没有任何一次**
`game.dll` 上机改动记录（所有成功改动都在 `dl_bin` + 代理侧）。

## 5. 复现

```bash
python tools/gamedll_data_survey.py --json out/gamedll-clusters.json   # 数据簇摘要（locid 字扫描）
python tools/opmod_scan.py --csv out/opmod.csv --json out/opmod.json   # 13 条 Operation Modifiers
```

段表 / 熵 / 签名目录自查（只读）：

```python
import struct, math, pathlib
from collections import Counter
b = pathlib.Path(r"D:/SteamLibrary/steamapps/common/Helldivers 2/data/game/game.dll").read_bytes()
ent = lambda d: -sum((v/len(d))*math.log2(v/len(d)) for v in Counter(d).values()) if d else 0
e = struct.unpack_from('<I', b, 0x3C)[0]; opt = e + 24; sec = opt + 240
for i in range(7):
    o = sec + i*40
    nm = b[o:o+8].rstrip(b'\x00').decode('latin1')
    vs, va, rs, rp = struct.unpack_from('<IIII', b, o+8)
    print(f"{nm:8} raw=0x{rs:08X} 熵={ent(b[rp:rp+rs]):.4f}")
```


证据等级：数据簇/偏移/样例文案 = ✓ 离线（可复算）；簇身份猜测 = ⚠ 推断；
OperationSettings 字段语义 = ⚠ 未证；代码引用关系 = ✗ 不可读（`.text` 加密）。
